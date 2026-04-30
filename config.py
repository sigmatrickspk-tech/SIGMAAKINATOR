# config.py - Configuration File
# ⚠️ EDIT THIS FILE WITH YOUR OWN VALUES

import os

# ========== BOT SETTINGS ==========
BOT_TOKEN = "8730336571:AAHMqpkjelGfC9IUrREm0IGnGmUKG6NrUCU"  # Get from @BotFather

# ========== ADMIN IDs ==========
ADMIN_IDS = [7285267844,8278238550]  # Replace with YOUR Telegram user ID

# ========== FORCE JOIN CHANNELS ==========
# Format: (channel_username, channel_id, invite_link)
FORCE_CHANNELS = [
    ("@sigmatrickspk", -1003762892243, "https://t.me/sigmatrickspk"),
    ("@sigmatrickspkchat", -1003772238103, "https://t.me/sigmatrickspkchat"),
    ("@premiumssupportpro", -1003793206654, "https://t.me/premiumssupportpro"),
    ("@fftournamenthubpk", -1003777775818, "https://t.me/fftournamenthubpk"),
    ("@ytpayouts", -1003712868096, "https://t.me/ytpayouts"),
]

# ========== SUPPORT & CONTACTS ==========
PREMIUM_CONTACT = "@sigmaogchat_bot"      # Contact for buying premium
SUPPORT_CONTACT = "@sigmaogchat_bot"      # For all user inquiries

# ========== NOTIFICATION CHANNEL ==========
NOTIFICATION_CHANNEL = "@ytpayouts"       # All bot events posted here

# ========== ECONOMY SETTINGS ==========
DAILY_FREE_SEARCHES = 5          # Free searches per day for non-premium
COINS_PER_REFERRAL = 2           # Coins earned per referral
COINS_PER_GAME = 1               # Coins per game played
COINS_PER_WIN = 1               # Coins bonus for winning
XP_PER_WIN = 30                  # XP for winning
XP_PER_LOSS = 5                 # XP for losing
XP_PER_REFERRAL = 15             # XP per referral
DAILY_REWARD_BASE = 5            # Base daily reward coins
COST_PER_EXTRA_GAME = 3          # Coins cost to play after free limit

# ========== COINS PACKS (Price in PKR) ==========
COINS_PACKS = {
    "small": {"coins": 20, "price_pkr": 50, "price_usd": "$0.30"},
    "medium": {"coins": 40, "price_pkr": 100, "price_usd": "$0.60"},
    "large": {"coins": 100, "price_pkr": 200, "price_usd": "$1.20"},
}

# ========== PREMIUM PLANS (Price in PKR) ==========
PREMIUM_PLANS = [
    {
        "name": "1 Day",
        "days": 1,
        "price_pkr": 20,
        "price_usd": "$0.10",
        "searches_per_day": 20,
        "desc": "🕐 **1 Day** — Limited to **20 searches** total",
    },
    {
        "name": "7 Days",
        "days": 7,
        "price_pkr": 70,
        "price_usd": "$0.30",
        "searches_per_day": 20,
        "desc": "📅 **7 Days** — Up to **20 searches/day**",
    },
    {
        "name": "30 Days",
        "days": 30,
        "price_pkr": 250,
        "price_usd": "$1.00",
        "searches_per_day": 30,
        "desc": "🌙 **30 Days** — Up to **30 searches/day**",
    },
]

# ========== PREMIUM SEARCH LIMITS ==========
# Premium users have these limits applied per day
PREMIUM_SEARCH_LIMITS = {
    1: 20,    # 1 day plan: 20 searches total (not per day)
    7: 20,    # 7 day plan: 20 per day
    30: 30,   # 30 day plan: 30 per day
}
