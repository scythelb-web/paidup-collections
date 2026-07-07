"""Dashboard routes for PaidUp Collections."""
from fastapi import APIRouter, Request
from fastapi.responses import RedirectResponse

from app.database import get_db
from app.routers.auth import get_current_user

router = APIRouter(tags=["dashboard"])


@router.get("/dashboard")
async def dashboard(request: Request):
    user = get_current_user(request)
    if not user:
        return RedirectResponse("/auth/login", status_code=303)

    with get_db() as db:
        # Active overdue invoices
        active_count = db.execute(
            "SELECT COUNT(*) as count FROM overdue_invoices WHERE user_id = ? AND status = 'pending'",
            (user["id"],),
        ).fetchone()["count"]

        # Total overdue amount
        active_amount = db.execute(
            "SELECT COALESCE(SUM(amount), 0) as total FROM overdue_invoices WHERE user_id = ? AND status = 'pending'",
            (user["id"],),
        ).fetchone()["total"]

        # Recovered this month
        from datetime import datetime, timezone
        month = datetime.now(timezone.utc).strftime("%Y-%m")
        stats = db.execute(
            """SELECT total_overdue, total_recovered, total_amount_overdue, total_amount_recovered
               FROM recovery_stats WHERE user_id = ? AND month = ?""",
            (user["id"], month),
        ).fetchone()

        # All-time stats
        all_time = db.execute(
            """SELECT COALESCE(SUM(total_overdue), 0) as overdue,
                      COALESCE(SUM(total_recovered), 0) as recovered,
                      COALESCE(SUM(total_amount_overdue), 0) as amount_overdue,
                      COALESCE(SUM(total_amount_recovered), 0) as amount_recovered
               FROM recovery_stats WHERE user_id = ?""",
            (user["id"],),
        ).fetchone()

        # Aging breakdown
        aging = db.execute(
            """SELECT
                 CASE
                   WHEN days_overdue <= 7 THEN '1-7 days'
                   WHEN days_overdue <= 14 THEN '8-14 days'
                   WHEN days_overdue <= 30 THEN '15-30 days'
                   ELSE '30+ days'
                 END as bucket,
                 COUNT(*) as count,
                 SUM(amount) as total
               FROM overdue_invoices
               WHERE user_id = ? AND status = 'pending'
               GROUP BY bucket
               ORDER BY bucket""",
            (user["id"],),
        ).fetchall()

        # Recent activity
        recent = db.execute(
            """SELECT oi.*, rl.sent_at as last_contact
               FROM overdue_invoices oi
               LEFT JOIN reminder_log rl ON rl.overdue_invoice_id = oi.id
               WHERE oi.user_id = ?
               ORDER BY oi.created_at DESC LIMIT 10""",
            (user["id"],),
        ).fetchall()

    recovery_rate = round(
        all_time["recovered"] / max(all_time["overdue"], 1) * 100, 1
    )

    data = {
        "request": request,
        "user": user,
        "active_count": active_count,
        "active_amount": active_amount / 100,
        "month_stats": dict(stats) if stats else {
            "total_overdue": 0, "total_recovered": 0,
            "total_amount_overdue": 0, "total_amount_recovered": 0,
        },
        "all_time": dict(all_time),
        "recovery_rate": recovery_rate,
        "aging": [dict(r) for r in aging],
        "recent": [dict(r) for r in recent],
    }

    return request.app.state.templates.TemplateResponse("dashboard.html", data)
