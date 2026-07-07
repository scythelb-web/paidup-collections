import os
from dotenv import load_dotenv

load_dotenv()

SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret-change-in-production")
STRIPE_SECRET_KEY = os.getenv("STRIPE_SECRET_KEY", "")
SENDGRID_API_KEY = os.getenv("SENDGRID_API_KEY", "")
BASE_URL = os.getenv("BASE_URL", "http://localhost:8000")
ADMIN_EMAIL = os.getenv("ADMIN_EMAIL", "admin@paidup.io")

PRICING = {
    "starter": {"price": 29, "invoices": 50, "label": "Starter"},
    "growth": {"price": 79, "invoices": 500, "label": "Growth"},
    "scale": {"price": 199, "invoices": 5000, "label": "Scale"},
}
