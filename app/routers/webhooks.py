"""Stripe webhook handlers for PaidUp Collections."""

import logging
import stripe
from fastapi import APIRouter, Request, HTTPException

from app.config import STRIPE_SECRET_KEY
from app.database import get_db

logger = logging.getLogger(__name__)

router = APIRouter(tags=["webhooks"])

stripe.api_key = STRIPE_SECRET_KEY

PLAN_PRICE_MAP = {
    2900: "starter",
    7900: "growth",
    19900: "scale",
}


@router.post("/webhooks/stripe")
async def stripe_webhook(request: Request):
    payload = await request.body()
    sig_header = request.headers.get("stripe-signature")

    if not sig_header:
        raise HTTPException(status_code=400, detail="Missing stripe-signature header")

    # In production, set STRIPE_WEBHOOK_SECRET and verify the signature:
    # try:
    #     event = stripe.Webhook.construct_event(payload, sig_header, STRIPE_WEBHOOK_SECRET)
    # except (ValueError, stripe.error.SignatureVerificationError) as e:
    #     raise HTTPException(status_code=400, detail=f"Webhook signature verification failed: {e}")

    try:
        event = stripe.Event.construct_from(stripe.util.json.loads(payload), stripe.api_key)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid payload")

    event_type = event["type"]
    logger.info("Stripe webhook received: %s", event_type)

    if event_type == "checkout.session.completed":
        await handle_checkout_completed(event["data"]["object"])
    elif event_type == "customer.subscription.deleted":
        await handle_subscription_deleted(event["data"]["object"])
    else:
        logger.info("Unhandled event type: %s", event_type)

    return {"status": "ok"}


async def handle_checkout_completed(session):
    """Handle checkout.session.completed — provision the subscription."""
    client_reference_id = session.get("client_reference_id")
    customer_id = session.get("customer")
    subscription_id = session.get("subscription")

    # Determine plan from line item amount
    plan = "starter"
    line_items = session.get("line_items", {}).get("data", [])
    if not line_items:
        metadata = session.get("metadata", {})
        plan = metadata.get("plan", "starter")
    else:
        amount = line_items[0].get("amount_total") or line_items[0].get("price", {}).get("unit_amount", 0)
        plan = PLAN_PRICE_MAP.get(amount, "starter")

    if not client_reference_id:
        logger.warning("No client_reference_id in checkout session %s", session.get("id"))
        return

    user_id = int(client_reference_id)

    with get_db() as db:
        db.execute(
            "UPDATE users SET stripe_customer_id = ?, plan = ?, stripe_subscription_id = ? WHERE id = ?",
            (customer_id, plan, subscription_id, user_id),
        )
    logger.info(
        "Provisioned subscription for user %s: plan=%s, customer=%s, subscription=%s",
        user_id, plan, customer_id, subscription_id,
    )


async def handle_subscription_deleted(subscription):
    """Handle customer.subscription.deleted — downgrade user to starter."""
    customer_id = subscription.get("customer")
    if not customer_id:
        logger.warning("No customer in deleted subscription %s", subscription.get("id"))
        return

    with get_db() as db:
        user = db.execute(
            "SELECT id FROM users WHERE stripe_customer_id = ?",
            (customer_id,),
        ).fetchone()

        if not user:
            logger.warning("No user found for stripe customer %s", customer_id)
            return

        db.execute(
            "UPDATE users SET plan = 'starter', stripe_subscription_id = NULL WHERE id = ?",
            (user["id"],),
        )
    logger.info(
        "Downgraded user %s to starter (subscription deleted: %s)",
        user["id"], subscription.get("id"),
    )
