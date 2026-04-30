# 🤖 Premium Akinator Telegram Bot

A full-featured Telegram bot that plays **Akinator** — the AI that guesses your character!

## ✨ Features

### 🎮 Gameplay
- Think of a character, answer yes/no questions, Akinator guesses it!
- Multiple themes: Characters, Animals, Objects
- Multi-language support
- Child mode filter

### 💰 Economy System
- 🪙 **Coins** — Earn by playing, winning, daily rewards, and referrals
- 💵 **Buy Coins**: 20 for Rs.50 | 40 for Rs.100 | 100 for Rs.200
- 👑 **Premium Plans**:
  - 1 Day — Rs.20 (20 searches total)
  - 7 Days — Rs.70 (20 searches/day)
  - 30 Days — Rs.250 (30 searches/day)
- ✨ Free 5 searches/day for all users
- ⚡ XP & Level system

### 👥 Referral System
- Unique referral code per user
- Earn **3 🪙 + 25 XP** per referral
- New user gets **5 🪙 + 2 bonus searches**

### 📢 Notifications
- All events sent to `@ytpayouts`:
  - New user joins
  - Referrals
  - Premium purchases/granting
  - Admin actions

### 👑 Admin Panel
- `/addcoins <uid> <amount>` — Add coins
- `/setcoins <uid> <amount>` — Set coins
- `/grantprem <uid> <days>` — Grant premium
- `/removeprem <uid>` — Remove premium
- `/ban <uid> [reason]` — Ban user
- `/unban <uid>` — Unban user
- `/info <uid>` — User info
- `/broadcast <msg>` — Message all users
- `/logs` — View admin logs

### 🔒 Force Join
- Users must join all channels before using the bot:
  - @sigmatrickspk
  - @sigmatrickspkchat
  - @premiumssupportpro
  - @fftournamenthubpk
  - @Sigmaogchat_bot

## 🚀 Installation

### On Kali Linux / Ubuntu / Debian:

```bash
# 1. Update system
sudo apt update && sudo apt upgrade -y

# 2. Install Python & pip
sudo apt install python3 python3-pip git -y

# 3. Create project directory
mkdir ~/akinator_bot && cd ~/akinator_bot

# 4. Install requirements
pip3 install python-telegram-bot akinator-python

# 5. Edit config
nano config.py   # ← Add your BOT_TOKEN, channel IDs, admin IDs

# 6. Run the bot
python3 main.py
