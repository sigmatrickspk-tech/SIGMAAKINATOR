#!/usr/bin/env python3
# database.py - Complete JSON Database Manager for Premium Akinator Bot

import json
import os
import base64
import hashlib
from datetime import datetime, timedelta
from typing import Optional, Dict, List, Tuple, Any

from config import (
    COINS_PER_REFERRAL, XP_PER_REFERRAL, DAILY_REWARD_BASE,
    PREMIUM_SEARCH_LIMITS, COINS_PACKS,
)


class Database:
    """Full-featured JSON database for the Akinator bot"""

    def __init__(self, filepath="database.json"):
        self.filepath = filepath
        self.data = self._load()

    def _load(self) -> dict:
        default = {
            "users": {},
            "total_games": 0,
            "total_coins_earned": 0,
            "total_coins_spent": 0,
            "premium_sales": [],
            "admin_logs": [],
        }
        if os.path.exists(self.filepath):
            try:
                with open(self.filepath, "r") as f:
                    loaded = json.load(f)
                    for key in default:
                        if key not in loaded:
                            loaded[key] = default[key]
                    return loaded
            except (json.JSONDecodeError, IOError):
                pass
        return default

    def _save(self):
        os.makedirs(os.path.dirname(self.filepath) if os.path.dirname(self.filepath) else ".", exist_ok=True)
        with open(self.filepath, "w") as f:
            json.dump(self.data, f, indent=2, default=str)

    # ==================== USER ====================

    def get_user(self, user_id: int) -> dict:
        uid = str(user_id)
        if uid not in self.data["users"]:
            self.data["users"][uid] = {
                "username": "",
                "first_name": "",
                "joined_date": datetime.now().isoformat(),
                "last_active": datetime.now().isoformat(),
                "coins": 10,
                "total_coins_earned": 10,
                "total_coins_spent": 0,
                "games_played": 0,
                "games_won": 0,
                "games_lost": 0,
                "xp": 0,
                "level": 1,
                "daily_searches_used": 0,
                "last_search_date": "",
                "premium_searches_used": 0,
                "last_premium_search_date": "",
                "last_daily_claim": "",
                "daily_streak": 0,
                "referral_code": self._generate_code(user_id),
                "referred_by": None,
                "referrals_count": 0,
                "referral_earnings": 0,
                "is_premium": False,
                "premium_expiry": "",
                "premium_searches_per_day": 0,
                "banned": False,
                "ban_reason": "",
                "game_history": [],
                "settings": {
                    "lang": "en",
                    "theme": "characters",
                    "child_mode": False,
                },
            }
        return self.data["users"][uid]

    @staticmethod
    def _generate_code(uid: int) -> str:
        raw = f"{uid}-{datetime.now().timestamp()}"
        return base64.b32encode(hashlib.md5(raw.encode()).digest()).decode()[:8].upper()

    def update_user(self, user_id: int, **kwargs):
        user = self.get_user(user_id)
        for k, v in kwargs.items():
            if k in user:
                user[k] = v
        user["last_active"] = datetime.now().isoformat()
        self._save()

    def get_all_users(self) -> Dict[str, dict]:
        return self.data["users"]

    def get_user_count(self) -> int:
        return len(self.data["users"])

    # ==================== BAN ====================

    def is_banned(self, user_id: int) -> bool:
        return self.get_user(user_id).get("banned", False)

    def ban(self, user_id: int, reason: str = "", admin_id: int = 0):
        u = self.get_user(user_id)
        u["banned"] = True
        u["ban_reason"] = reason
        self._log(f"User {user_id} BANNED by admin {admin_id}. Reason: {reason}")
        self._save()

    def unban(self, user_id: int, admin_id: int = 0):
        u = self.get_user(user_id)
        u["banned"] = False
        u["ban_reason"] = ""
        self._log(f"User {user_id} UNBANNED by admin {admin_id}")
        self._save()

    # ==================== COINS ====================

    def add_coins(self, user_id: int, amount: int, reason: str = "") -> int:
        u = self.get_user(user_id)
        u["coins"] += amount
        if amount > 0:
            u["total_coins_earned"] += amount
            self.data["total_coins_earned"] += amount
        else:
            u["total_coins_spent"] += abs(amount)
            self.data["total_coins_spent"] += abs(amount)
        self._log(f"Coins {'+' if amount > 0 else ''}{amount} for {user_id} | {reason}")
        self._save()
        return u["coins"]

    def spend_coins(self, user_id: int, amount: int, reason: str = "") -> bool:
        u = self.get_user(user_id)
        if u["coins"] < amount:
            return False
        u["coins"] -= amount
        u["total_coins_spent"] += amount
        self.data["total_coins_spent"] += amount
        self._log(f"Coins -{amount} for {user_id} | {reason}")
        self._save()
        return True

    def set_coins(self, user_id: int, amount: int, admin_id: int = 0):
        u = self.get_user(user_id)
        old = u["coins"]
        u["coins"] = max(0, amount)
        self._log(f"Coins SET: {old} → {amount} for {user_id} by admin {admin_id}")
        self._save()

    def get_balance(self, user_id: int) -> int:
        return self.get_user(user_id)["coins"]

    # ==================== DAILY SEARCHES (FREE USERS) ====================

    def can_search(self, user_id: int) -> Tuple[bool, int, bool]:
        """Returns (can_search, remaining, is_premium)"""
        u = self.get_user(user_id)
        from config import DAILY_FREE_SEARCHES

        # Check premium first
        if u.get("is_premium", False):
            try:
                expiry = datetime.fromisoformat(u["premium_expiry"])
                if expiry > datetime.now():
                    # Premium user - check premium daily limit
                    limit = u.get("premium_searches_per_day", 20)
                    today = datetime.now().strftime("%Y-%m-%d")
                    if u.get("last_premium_search_date", "") != today:
                        u["premium_searches_used"] = 0
                        u["last_premium_search_date"] = today
                        self._save()
                    remaining = limit - u.get("premium_searches_used", 0)
                    return remaining > 0, max(0, remaining), True
            except (ValueError, TypeError):
                pass
            u["is_premium"] = False
            u["premium_expiry"] = ""
            self._save()

        # Free user check
        today = datetime.now().strftime("%Y-%m-%d")
        if u.get("last_search_date", "") != today:
            u["daily_searches_used"] = 0
            u["last_search_date"] = today
            self._save()

        remaining = DAILY_FREE_SEARCHES - u.get("daily_searches_used", 0)
        return remaining > 0, max(0, remaining), False

    def use_search(self, user_id: int) -> bool:
        """Record one search use"""
        u = self.get_user(user_id)
        
        # Check if premium
        if u.get("is_premium", False):
            try:
                expiry = datetime.fromisoformat(u["premium_expiry"])
                if expiry > datetime.now():
                    today = datetime.now().strftime("%Y-%m-%d")
                    if u.get("last_premium_search_date", "") != today:
                        u["premium_searches_used"] = 0
                        u["last_premium_search_date"] = today
                    u["premium_searches_used"] = u.get("premium_searches_used", 0) + 1
                    self._save()
                    return True
            except (ValueError, TypeError):
                pass

        # Free user
        today = datetime.now().strftime("%Y-%m-%d")
        if u.get("last_search_date", "") != today:
            u["daily_searches_used"] = 0
            u["last_search_date"] = today
        can, _, _ = self.can_search(user_id)
        if not can:
            return False
        u["daily_searches_used"] = u.get("daily_searches_used", 0) + 1
        u["last_search_date"] = today
        self._save()
        return True

    # ==================== XP & LEVEL ====================

    def add_xp(self, user_id: int, amount: int) -> Tuple[int, int, bool]:
        """Returns (total_xp, level, leveled_up)"""
        u = self.get_user(user_id)
        u["xp"] += amount
        old_level = u["level"]
        new_level = (u["xp"] // 100) + 1
        u["level"] = new_level
        leveled = new_level > old_level
        self._save()
        return u["xp"], u["level"], leveled

    # ==================== DAILY CLAIM ====================

    def can_claim_daily(self, user_id: int) -> Tuple[bool, float]:
        u = self.get_user(user_id)
        last = u.get("last_daily_claim", "")
        if not last:
            return True, 0
        try:
            last_time = datetime.fromisoformat(last)
            next_time = last_time + timedelta(hours=24)
            now = datetime.now()
            if now >= next_time:
                return True, 0
            remaining = (next_time - now).total_seconds() / 3600
            return False, remaining
        except (ValueError, TypeError):
            return True, 0

    def claim_daily(self, user_id: int) -> dict:
        u = self.get_user(user_id)
        u["last_daily_claim"] = datetime.now().isoformat()
        u["daily_streak"] = u.get("daily_streak", 0) + 1
        level = u["level"]
        coins = DAILY_REWARD_BASE + (level * 2)
        xp = level * 5 + 10
        # Bonus coins for streaks
        streak = u["daily_streak"]
        if streak >= 30:
            coins += 50
        elif streak >= 14:
            coins += 25
        elif streak >= 7:
            coins += 10
        self.add_coins(user_id, coins, "Daily claim")
        self.add_xp(user_id, xp)
        self._save()
        return {"coins": coins, "xp": xp, "level": level, "streak": streak}

    # ==================== REFERRALS ====================

    def get_ref_code(self, user_id: int) -> str:
        return self.get_user(user_id)["referral_code"]

    def get_user_by_ref(self, code: str) -> Optional[int]:
        code = code.upper()
        for uid, data in self.data["users"].items():
            if data.get("referral_code") == code:
                return int(uid)
        return None

    def process_referral(self, new_uid: int, ref_code: str) -> Tuple[bool, str, Optional[int]]:
        """Returns (success, message, referrer_id_or_None)"""
        referrer_id = self.get_user_by_ref(ref_code)
        if referrer_id is None:
            return False, "❌ Invalid referral code!", None
        if referrer_id == new_uid:
            return False, "❌ You cannot refer yourself!", None
        nu = self.get_user(new_uid)
        if nu.get("referred_by") is not None:
            return False, "❌ You were already referred by someone!", None
        nu["referred_by"] = referrer_id
        # Give 2 bonus searches for new user
        nu["daily_searches_used"] = max(0, nu.get("daily_searches_used", 0) - 2)
        self.add_coins(new_uid, 5, "Referral welcome bonus")
        self._save()

        ru = self.get_user(referrer_id)
        ru["referrals_count"] = ru.get("referrals_count", 0) + 1
        self.add_coins(referrer_id, COINS_PER_REFERRAL, f"Referral reward: {new_uid}")
        self.add_xp(referrer_id, XP_PER_REFERRAL)
        
        return True, (
            f"✅ **Referral Successful!** 🎉\n\n"
            f"You both got rewards!\n"
            f"• You: **+5 🪙** + **2 bonus searches**\n"
            f"• Your referrer: **+{COINS_PER_REFERRAL} 🪙** + **{XP_PER_REFERRAL} XP**"
        ), referrer_id

    # ==================== PREMIUM ====================

    def is_premium(self, user_id: int) -> bool:
        u = self.get_user(user_id)
        if not u.get("is_premium", False):
            return False
        try:
            exp = datetime.fromisoformat(u["premium_expiry"])
            if exp < datetime.now():
                u["is_premium"] = False
                u["premium_expiry"] = ""
                u["premium_searches_per_day"] = 0
                self._save()
                return False
            return True
        except (ValueError, TypeError):
            return False

    def set_premium(self, user_id: int, days: int, admin_id: int = 0):
        """Grant premium to a user for X days"""
        u = self.get_user(user_id)
        exp = datetime.now() + timedelta(days=days)
        u["is_premium"] = True
        u["premium_expiry"] = exp.isoformat()
        # Set searches per day based on plan
        limit = PREMIUM_SEARCH_LIMITS.get(days, 20)
        u["premium_searches_per_day"] = limit
        u["premium_searches_used"] = 0
        u["last_premium_search_date"] = ""
        self._log(f"PREMIUM {days}d for {user_id} by admin {admin_id}")
        self._save()
        return exp.isoformat()

    def remove_premium(self, user_id: int, admin_id: int = 0):
        u = self.get_user(user_id)
        u["is_premium"] = False
        u["premium_expiry"] = ""
        u["premium_searches_per_day"] = 0
        self._log(f"PREMIUM REMOVED for {user_id} by admin {admin_id}")
        self._save()

    def record_premium_sale(self, user_id: int, plan_name: str, days: int, amount_pkr: int):
        """Record a premium purchase in the sales log"""
        self.data["premium_sales"].append({
            "user_id": user_id,
            "plan": plan_name,
            "days": days,
            "amount_pkr": amount_pkr,
            "timestamp": datetime.now().isoformat(),
        })
        self._save()

    def get_premium_sales(self, limit: int = 20) -> list:
        return self.data.get("premium_sales", [])[-limit:]

    def get_total_premium_revenue(self) -> int:
        return sum(s.get("amount_pkr", 0) for s in self.data.get("premium_sales", []))

    # ==================== COINS SHOP ====================

    def purchase_coins_pack(self, user_id: int, pack_key: str) -> Tuple[bool, str]:
        """Record a coins pack purchase (user gets coins after admin confirmation)"""
        pack = COINS_PACKS.get(pack_key)
        if not pack:
            return False, "❌ Invalid pack!"
        self._log(f"COINS PURCHASE requested: {user_id} — {pack_key} ({pack['coins']} coins, Rs.{pack['price_pkr']})")
        self._save()
        return True, (
            f"✅ **Purchase Request Submitted!**\n\n"
            f"**Pack:** {pack['coins']} 🪙 for Rs.{pack['price_pkr']}\n"
            f"**Contact:** {PREMIUM_CONTACT}\n\n"
            f"Please send the payment screenshot to {PREMIUM_CONTACT}.\n"
            f"Admin will add the coins manually after verification."
        )

    # ==================== GAME HISTORY ====================

    def add_game(self, user_id: int, result: str, questions: int, won: bool):
        u = self.get_user(user_id)
        u["games_played"] += 1
        if won:
            u["games_won"] += 1
        else:
            u["games_lost"] += 1
        if "game_history" not in u:
            u["game_history"] = []
        u["game_history"].append({
            "timestamp": datetime.now().isoformat(),
            "result": result,
            "questions": questions,
            "won": won,
        })
        if len(u["game_history"]) > 50:
            u["game_history"] = u["game_history"][-50:]
        self._save()

    def get_history(self, user_id: int, limit: int = 10) -> list:
        return self.get_user(user_id).get("game_history", [])[-limit:]

    # ==================== LEADERBOARD ====================

    def get_leaderboard(self, category: str = "xp", limit: int = 10) -> list:
        users = []
        for uid, data in self.data["users"].items():
            if data.get("banned", False):
                continue
            users.append((int(uid), data))
        keys = {
            "xp": lambda x: x[1]["xp"],
            "coins": lambda x: x[1]["coins"],
            "wins": lambda x: x[1]["games_won"],
            "games": lambda x: x[1]["games_played"],
            "level": lambda x: x[1]["level"],
            "referrals": lambda x: x[1].get("referrals_count", 0),
            "streak": lambda x: x[1].get("daily_streak", 0),
        }
        key = keys.get(category, keys["xp"])
        return sorted(users, key=key, reverse=True)[:limit]

    # ==================== ADMIN ====================

    def _log(self, msg: str):
        self.data["admin_logs"].append({
            "timestamp": datetime.now().isoformat(),
            "message": msg,
        })
        if len(self.data["admin_logs"]) > 200:
            self.data["admin_logs"] = self.data["admin_logs"][-200:]

    def get_logs(self, limit: int = 20) -> list:
        return self.data["admin_logs"][-limit:]

    def get_user_info(self, user_id: int) -> str:
        u = self.get_user(user_id)
        wr = (u["games_won"] / u["games_played"] * 100) if u["games_played"] > 0 else 0
        prem = self.is_premium(user_id)
        
        prem_status = "👑 Yes" if prem else "❌ No"
        if prem:
            prem_status += f" (exp: {u.get('premium_expiry', 'N/A')[:19]})"

        text = (
            f"👤 **User Info — `{user_id}`**\n"
            f"━" * 26 + "\n"
            f"`Username   :` @{u.get('username', 'N/A')}\n"
            f"`Name       :` {u.get('first_name', 'N/A')}\n"
            f"`Joined     :` {u.get('joined_date', 'N/A')[:19]}\n"
            f"`Active     :` {u.get('last_active', 'N/A')[:19]}\n\n"
            f"💰 **Economy**\n"
            f"`Coins      :` {u['coins']} 🪙\n"
            f"`Earned     :` {u['total_coins_earned']} 🪙\n"
            f"`Spent      :` {u['total_coins_spent']} 🪙\n\n"
            f"🎮 **Games**\n"
            f"`Played     :` {u['games_played']}  Won: {u['games_won']}  Lost: {u['games_lost']}\n"
            f"`Winrate    :` {wr:.1f}%\n\n"
            f"📊 **Progression**\n"
            f"`Level      :` {u['level']}  XP: {u['xp']}\n\n"
            f"👥 **Referrals**\n"
            f"`Code       :` {u.get('referral_code', 'N/A')}\n"
            f"`Count      :` {u.get('referrals_count', 0)}\n"
            f"`Referred By:` {u.get('referred_by', 'None')}\n\n"
            f"🔒 **Status**\n"
            f"`Banned     :` {'❌ Yes' if u.get('banned') else '✅ No'}\n"
            f"`Premium    :` {prem_status}\n"
        )
        if u.get("banned") and u.get("ban_reason"):
            text += f"`Reason     :` {u['ban_reason']}\n"
        return text


# Global instance
db = Database()
