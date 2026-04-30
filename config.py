# config.py - Configuration File
# ⚠️ EDIT THIS FILE WITH YOUR OWN VALUES

import os

# ========== BOT SETTINGS ==========
BOT_TOKEN = "YOUR_BOT_TOKEN_HERE"  # Get from @BotFather

# ========== ADMIN IDs ==========
ADMIN_IDS = [123456789]  # Replace with YOUR Telegram user ID

# ========== FORCE JOIN CHANNELS ==========
# Format: (channel_username, channel_id, invite_link)
FORCE_CHANNELS = [
    ("@sigmatrickspk", -1001234567890, "https://t.me/sigmatrickspk"),
    ("@sigmatrickspkchat", -1001234567891, "https://t.me/sigmatrickspkchat"),
    ("@premiumssupportpro", -1001234567892, "https://t.me/premiumssupportpro"),
    ("@fftournamenthubpk", -1001234567893, "https://t.me/fftournamenthubpk"),
    ("@Sigmaogchat_bot", -1001234567894, "https://t.me/Sigmaogchat_bot"),
]

# ========== SUPPORT & CONTACTS ==========
PREMIUM_CONTACT = "@sigmaogchat_bot"      # Contact for buying premium
SUPPORT_CONTACT = "@sigmaogchat_bot"      # For all user inquiries

# ========== NOTIFICATION CHANNEL ==========
NOTIFICATION_CHANNEL = "@ytpayouts"       # All bot events posted here

# ========== ECONOMY SETTINGS ==========
DAILY_FREE_SEARCHES = 5          # Free searches per day for non-premium
COINS_PER_REFERRAL = 3           # Coins earned per referral
COINS_PER_GAME = 1               # Coins per game played
COINS_PER_WIN = 2                # Coins bonus for winning
XP_PER_WIN = 50                  # XP for winning
XP_PER_LOSS = 10                 # XP for losing
XP_PER_REFERRAL = 25             # XP per referral
DAILY_REWARD_BASE = 5            # Base daily reward coins
COST_PER_EXTRA_GAME = 2          # Coins cost to play after free limit

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
        "price_usd": "$0.15",
        "searches_per_day": 20,
        "desc": "🕐 **1 Day** — Limited to **20 searches** total",
    },
    {
        "name": "7 Days",
        "days": 7,
        "price_pkr": 70,
        "price_usd": "$0.50",
        "searches_per_day": 20,
        "desc": "📅 **7 Days** — Up to **20 searches/day**",
    },
    {
        "name": "30 Days",
        "days": 30,
        "price_pkr": 250,
        "price_usd": "$1.80",
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
