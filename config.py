# config.py
import os

BOT_TOKEN = os.environ.get("BOT_TOKEN", "8911011039:AAH0Jl6JkCM1h50l2mOJ1-uQxguCF2DKm9Q")
ADMIN_CHAT_ID = int(os.environ.get("ADMIN_CHAT_ID", 123456789))
CHANNEL_ID = os.environ.get("CHANNEL_ID", -1001234567890)   # sirf zip upload ke liye rakha

QR_IMAGE_PATH = "qr.png"
UPI_ID = "yourupi@upi"
VIDEOS_PER_PAGE = 5

# ── Editable links (admin panel se change ho sakte hain) ──
HELP_DM_LINK   = "https://t.me/Premiumselee"
DEMO_GROUP_LINK = "https://t.me/+3CIhP6FePCJlOTNl"
PREMIUM_CHANNEL_LINK = "https://t.me/+BffX1nv6dsZkZjk1"

# ── Plans ──
PLANS = {
    "50":  {"label": "50 Links",  "price": 100, "links": 50,  "days": 30},
    "100": {"label": "100 Links", "price": 150, "links": 100, "days": 30},
}

WELCOME_TEXT = (
    "👋 <b>Hello & Welcome to our Bot!</b>\n\n"
    "We provide <b>all types of videos</b>:\n"
    "1️⃣ MMS\n"
    "2️⃣ CP\n"
    "3️⃣ Gay\n"
    "4️⃣ Lesbian\n"
    "5️⃣ & so on...\n\n"
    "Neeche se option choose karo 👇"
)
