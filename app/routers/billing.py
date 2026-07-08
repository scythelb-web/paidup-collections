"""Stripe Checkout billing routes for PaidUp Collections."""

import logging
import stripe
from fastapi import APIRouter, Request
from fastapi.responses import RedirectResponse, JSONResponse

from app.config import STRIPE_SECRET_KEY, BASE_URL, PRICING
from app.database import get_db
from app.routers.auth import get_current_user

logger = logging.getLogger(__name__)

router = APIRouter(tags=["billing"])

stripe.api_key = STRIPE_SECRET_KEY

PRICE_IDS = {
    "starter": "price_1Tr3DdIh3bqeW0wSOO3oAwPG",
    "growth": "price_1Tr3DvIh3bqeW0wSn4ePM15a",
    "scale": "price_1Tr3EBIh3bqeW0wS8FwMqNPA",
}


@router.get("/pricing")
async def pricing_page(request: Request):
    return request.app.state.templates.TemplateResponse(
        "pricing.html", {"request": request, "pricing": PRICING}
    )


@router.post("/create-checkout-session")
async def create_checkout_session(request: Request):
    user = get_current_user(request)
    if not user:
        return JSONResponse({"error": "Unauthorized"}, status_code=401)

    body = await request.json()
    plan = body.get("plan", "starter")

    if plan not in PRICE_IDS:
        return JSONResponse({"error": "Invalid plan"}, status_code=400)

    try:
        with get_db() as db:
            checkout_session = stripe.checkout.Session.create(
                customer_email=user["email"],
                client_reference_id=str(user["id"]),
                line_items=[
                    {
                        "price": PRICE_IDS[plan],
                        "quantity": 1,
                    }
                ],
                mode="subscription",
                success_url=f"{BASE_URL}/billing/success?session_id={{CHECKOUT_SESSION_ID}}",
                cancel_url=f"{BASE_URL}/pricing",
                metadata={"user_id": str(user["id"]), "plan": plan},
            )
            return JSONResponse({"url": checkout_session.url})
    except stripe.error.StripeError as e:
        logger.error("Stripe error creating checkout session: %s", e)
        return JSONResponse({"error": "Payment service unavailable"}, status_code=503)


@router.get("/billing/success")
async def billing_success(request: Request):
    user = get_current_user(request)
    if not user:
        return RedirectResponse("/auth/login", status_code=303)

    return request.app.state.templates.TemplateResponse(
        "pricing.html",
        {"request": request, "pricing": PRICING, "success": True},
    )
