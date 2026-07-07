"""Invoice recovery engine — automated reminder sequences for overdue invoices."""

REMINDER_SEQUENCE = [
    {"step": 1, "day": 0,  "channel": "email", "name": "Friendly reminder — day of"},
    {"step": 2, "day": 3,  "channel": "email", "name": "Second reminder"},
    {"step": 3, "day": 7,  "channel": "email", "name": "Urgency — one week late"},
    {"step": 4, "day": 14, "channel": "email", "name": "Two weeks — escalation"},
    {"step": 5, "day": 21, "channel": "email", "name": "Final notice before collections"},
    {"step": 6, "day": 30, "channel": "email", "name": "Account suspension warning"},
]

DEFAULT_TEMPLATES = {
    1: {
        "subject": "Friendly reminder — invoice {{invoice_id}} is due",
        "body": """<p>Hi {{customer_name}},</p>
<p>Just a friendly reminder that invoice <strong>{{invoice_id}}</strong> for <strong>${{amount}}</strong> is now due.</p>
<p>You can pay securely online here:</p>
<p><a href="{{payment_link}}" style="display:inline-block;padding:12px 24px;background:#4F46E5;color:white;text-decoration:none;border-radius:6px;">
  Pay Invoice Now
</a></p>
<p>If you've already sent payment, thank you — please disregard this message.</p>
<p>— {{business_name}}</p>""",
    },
    3: {
        "subject": "Invoice {{invoice_id}} is now 7 days past due",
        "body": """<p>Hi {{customer_name}},</p>
<p>Invoice <strong>{{invoice_id}}</strong> for <strong>${{amount}}</strong> is now 7 days past due. We haven't received payment yet.</p>
<p>To avoid any service interruption, please submit payment as soon as possible:</p>
<p><a href="{{payment_link}}" style="display:inline-block;padding:12px 24px;background:#F59E0B;color:white;text-decoration:none;border-radius:6px;">
  Pay Now — ${{amount}}
</a></p>
<p>If there's an issue or you need to discuss payment terms, just reply to this email.</p>
<p>— {{business_name}}</p>""",
    },
    5: {
        "subject": "Final notice — invoice {{invoice_id}} is 21 days past due",
        "body": """<p>Hi {{customer_name}},</p>
<p>This is our final attempt to reach you about invoice <strong>{{invoice_id}}</strong> (${{amount}}), now <strong>21 days past due</strong>.</p>
<p>If payment is not received within 7 days, your account may be referred to collections.</p>
<p><a href="{{payment_link}}" style="display:inline-block;padding:12px 24px;background:#DC2626;color:white;text-decoration:none;border-radius:6px;">
  Pay Immediately
</a></p>
<p>We'd prefer to resolve this directly. Please reach out if you need help.</p>
<p>— {{business_name}}</p>""",
    },
}
