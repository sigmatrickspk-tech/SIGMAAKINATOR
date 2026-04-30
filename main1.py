                [
                    InlineKeyboardButton(ANSWER_LABELS["yes"], callback_data=cb("ans", "yes")),
                    InlineKeyboardButton(ANSWER_LABELS["no"], callback_data=cb("ans", "no")),
                ],
                [
                    InlineKeyboardButton(ANSWER_LABELS["idk"], callback_data=cb("ans", "idk")),
                    InlineKeyboardButton(ANSWER_LABELS["probably"], callback_data=cb("ans", "probably")),
                    InlineKeyboardButton(ANSWER_LABELS["probnot"], callback_data=cb("ans", "probnot")),
                ],
                [
                    InlineKeyboardButton("🔙 Back", callback_data=cb("back")),
                    InlineKeyboardButton("🚪 Quit", callback_data=cb("home")),
                ],
            ]
            await update.callback_query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode=ParseMode.MARKDOWN)

    except Exception as e:
        logger.error(f"Answer error: {e}")
        await update.callback_query.answer(f"❌ Error: {str(e)[:50]}", show_alert=True)


async def go_back(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Go back one question"""
    chat_id = update.effective_chat.id
    session = active_games.get(chat_id)
    if not session:
        await update.callback_query.answer("❌ No active game!", show_alert=True)
        return
    try:
        session.go_back()
        text = (
            f"🎭 **Question #{session.step}**\n"
            f"`Progress: {session.progression:.1f}%`\n"
            f"━" * 24 + "\n\n"
            f"❓ `{session.question}`\n\n"
        )
        keyboard = [
            [
                InlineKeyboardButton(ANSWER_LABELS["yes"], callback_data=cb("ans", "yes")),
                InlineKeyboardButton(ANSWER_LABELS["no"], callback_data=cb("ans", "no")),
            ],
            [
                InlineKeyboardButton(ANSWER_LABELS["idk"], callback_data=cb("ans", "idk")),
                InlineKeyboardButton(ANSWER_LABELS["probably"], callback_data=cb("ans", "probably")),
                InlineKeyboardButton(ANSWER_LABELS["probnot"], callback_data=cb("ans", "probnot")),
            ],
            [
                InlineKeyboardButton("🔙 Back", callback_data=cb("back")),
                InlineKeyboardButton("🚪 Quit", callback_data=cb("home")),
            ],
        ]
        await update.callback_query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode=ParseMode.MARKDOWN)
    except Exception as e:
        await update.callback_query.answer(f"Cannot go back: {str(e)[:30]}", show_alert=True)


async def wrong_guess(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """User said Akinator was wrong"""
    chat_id = update.effective_chat.id
    uid = update.effective_user.id
    session = active_games.get(chat_id)

    if session:
        questions = session.step
        db.add_game(uid, "Wrong Guess", questions, won=False)
        db.add_xp(uid, XP_PER_LOSS)
        db.add_coins(uid, 1, "Participation")
        del active_games[chat_id]

    text = (
        f"😅 **Aww man!**\n\n"
        f"I couldn't get it right this time!\n"
        f"Tell {PREMIUM_CONTACT} to add more characters! 🎮\n\n"
        f"**+1** 🪙 for trying\n"
        f"**+{XP_PER_LOSS}** XP\n\n"
        f"Want to try again with a different character?"
    )
    keyboard = [
        [InlineKeyboardButton("🎮 Play Again", callback_data=cb("play"))],
        [InlineKeyboardButton("🔙 Menu", callback_data=cb("home"))],
    ]
    await update.callback_query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode=ParseMode.MARKDOWN)


# ============================================================
# PAY TO PLAY (when out of free searches)
# ============================================================

async def pay_to_play(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Let user spend coins to play when out of free searches"""
    uid = update.effective_user.id
    if db.spend_coins(uid, COST_PER_EXTRA_GAME, "Paid play (extra game)"):
        await update.callback_query.answer(f"Charged {COST_PER_EXTRA_GAME} 🪙", show_alert=True)
        await start_game(update, context)
    else:
        await update.callback_query.answer(f"❌ Need {COST_PER_EXTRA_GAME} 🪙", show_alert=True)


# ============================================================
# PROFILE
# ============================================================

async def show_profile(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show user profile"""
    uid = update.effective_user.id
    u = db.get_user(uid)
    prem = db.is_premium(uid)
    wr = (u["games_won"] / u["games_played"] * 100) if u["games_played"] > 0 else 0
    _, rem, is_prem = db.can_search(uid)
    searches_avail = "♾️" if rem == 0 and is_prem else rem

    prem_status = "👑 **Active**" if prem else "🔴 **Not Active**"
    if prem:
        exp = u.get("premium_expiry", "N/A")[:19]
        prem_status += f"\n`Expires:` {exp}"
        pd = u.get("premium_searches_per_day", 20)
        ru = u.get("premium_searches_used", 0)
        prem_status += f"\n`Searches:` {pd - ru}/{pd} today"

    text = (
        f"👤 **{update.effective_user.first_name}'s Profile**\n"
        f"━" * 24 + "\n\n"
        f"**Stats**\n"
        f"🎮 Games: {u['games_played']} | 🏆 Won: {u['games_won']} | ❌ Lost: {u['games_lost']}\n"
        f"📊 Win Rate: {wr:.1f}%\n\n"
        f"**Economy**\n"
        f"🪙 Coins: **{u['coins']}**\n"
        f"🔍 Searches: **{searches_avail}**/day\n\n"
        f"**Progression**\n"
        f"⭐ Level: **{u['level']}**  |  ⚡ XP: {u['xp']} (Next: {((u['level']) * 100)})\n\n"
        f"**Premium**\n"
        f"{prem_status}\n\n"
        f"**Referrals**\n"
        f"👥 Refs: {u.get('referrals_count', 0)}\n"
        f"🔑 Code: `{u.get('referral_code', 'N/A')}`\n\n"
        f"📞 Contact: {PREMIUM_CONTACT}"
    )
    keyboard = [
        [InlineKeyboardButton("🛒 Get Premium", callback_data=cb("buy_premium"))],
        [InlineKeyboardButton("💰 Daily Reward", callback_data=cb("daily"))],
        [InlineKeyboardButton("🔙 Back", callback_data=cb("home"))],
    ]
    await update.callback_query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode=ParseMode.MARKDOWN)


# ============================================================
# DAILY REWARD
# ============================================================

async def daily_reward(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Claim daily reward"""
    uid = update.effective_user.id
    can, hours_remaining = db.can_claim_daily(uid)
    if not can:
        hours_str = f"{hours_remaining:.1f}" if hours_remaining > 1 else f"{hours_remaining*60:.0f} minutes"
        text = f"⏳ **Daily already claimed!**\n\nCome back in **{hours_str}** hours!\n\n📞 Contact: {PREMIUM_CONTACT}"
        await update.callback_query.edit_message_text(text, parse_mode=ParseMode.MARKDOWN)
        return

    result = db.claim_daily(uid)
    db.add_game(uid, "daily_claim", 0, True)

    text = (
        f"💰 **Daily Reward Claimed!** 🔥\n\n"
        f"🪙 **+{result['coins']} Coins**\n"
        f"⚡ **+{result['xp']} XP**\n"
        f"📊 Level: {result['level']}\n"
        f"🔥 Streak: **{result['streak']} days**\n\n"
        f"Come back tomorrow for more!"
    )
    keyboard = [[InlineKeyboardButton("🎮 Play Now", callback_data=cb("play"))],
                [InlineKeyboardButton("🔙 Menu", callback_data=cb("home"))]]

    await update.callback_query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode=ParseMode.MARKDOWN)

    await notify_event(
        context, "daily_claim",
        user_id=uid,
        user_name=get_user_display(uid),
        coins=result['coins'],
        xp=result['xp'],
        streak=result['streak'],
    )


# ============================================================
# SHOP
# ============================================================

async def shop_menu(update: Update, context: ContextTypes.DEFAULT_TYPE, edit: bool = False):
    """Show the shop menu"""
    text = (
        f"🛒 **Premium Akinator Shop**\n"
        f"━" * 24 + "\n\n"
        f"**🪙 Buy Coins**\n"
        f"• 20 🪙 — **Rs. 50** (Instant)\n"
        f"• 40 🪙 — **Rs. 100** (Instant)\n"
        f"• 100 🪙 — **Rs. 200** (Instant)\n\n"
        f"**👑 Premium Plans** (Unlimited Play)\n"
        f"• **1 Day** — Rs. 20 (20 searches)\n"
        f"• **7 Days** — Rs. 70 (20/day)\n"
        f"• **30 Days** — Rs. 250 (30/day)\n\n"
        f"📞 **Contact:** {PREMIUM_CONTACT}\n"
        f"⚡ Send payment screenshot to activate!\n"
    )
    keyboard = [
        [InlineKeyboardButton("🪙 Buy Coins", callback_data=cb("buy_coins"))],
        [InlineKeyboardButton("👑 Premium Plans", callback_data=cb("buy_premium"))],
        [InlineKeyboardButton("🔙 Back", callback_data=cb("home"))],
    ]
    await update.callback_query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode=ParseMode.MARKDOWN)


async def buy_coins_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show coin packs"""
    uid = update.effective_user.id
    text = "🪙 **Coin Packs**\n\nChoose a pack and contact admin:\n\n"
    keyboard = []
    for key, pack in COINS_PACKS.items():
        text += f"• **{pack['coins']} 🪙** — Rs. {pack['price_pkr']}\n"
        keyboard.append([InlineKeyboardButton(f"🪙 {pack['coins']} Coins — Rs.{pack['price_pkr']}", callback_data=cb("coins_pack", key))])
    text += f"\n📞 **Pay & Send Screenshot To:** {PREMIUM_CONTACT}"
    keyboard.append([InlineKeyboardButton("🔙 Back", callback_data=cb("shop"))])
    await update.callback_query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode=ParseMode.MARKDOWN)


async def coins_pack_selected(update: Update, context: ContextTypes.DEFAULT_TYPE, pack_key: str):
    """User selected a coin pack"""
    uid = update.effective_user.id
    pack = COINS_PACKS.get(pack_key)
    if not pack:
        await update.callback_query.answer("Invalid pack", show_alert=True)
        return

    success, msg = db.purchase_coins_pack(uid, pack_key)
    await update.callback_query.edit_message_text(msg, parse_mode=ParseMode.MARKDOWN)

    # Notify @ytpayouts
    await notify_event(
        context, "coins_purchased",
        user_id=uid,
        user_name=get_user_display(uid),
        pack=pack_key,
        coins=pack['coins'],
        amount=pack['price_pkr'],
    )


async def premium_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show premium plans"""
    uid = update.effective_user.id
    prem = db.is_premium(uid)
    text = "👑 **Premium Plans**\n\n"
    if prem:
        u = db.get_user(uid)
        exp = u.get("premium_expiry", "")[:19]
        text += f"✅ **You already have Premium!**\n`Expires: {exp}`\n\n"

    text += "Unlock unlimited guessing power:\n\n"
    keyboard = []
    for plan in PREMIUM_PLANS:
        text += f"• {plan['desc']} — **Rs.{plan['price_pkr']}**\n"
        keyboard.append([InlineKeyboardButton(f"👑 {plan['name']} — Rs.{plan['price_pkr']}", callback_data=cb("prem_plan", str(plan['days'])))])

    text += f"\n📞 **Contact:** {PREMIUM_CONTACT}\n⚡ Send screenshot after payment!"
    keyboard.append([InlineKeyboardButton("🔙 Back", callback_data=cb("shop"))])
    await update.callback_query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode=ParseMode.MARKDOWN)


async def premium_plan_selected(update: Update, context: ContextTypes.DEFAULT_TYPE, days_str: str):
    """User selected a premium plan"""
    uid = update.effective_user.id
    try:
        days = int(days_str)
    except ValueError:
        await update.callback_query.answer("Invalid plan", show_alert=True)
        return

    plan = None
    for p in PREMIUM_PLANS:
        if p["days"] == days:
            plan = p
            break

    if not plan:
        await update.callback_query.answer("Plan not found", show_alert=True)
        return

    text = (
        f"👑 **Premium Plan Selected!**\n"
        f"━" * 20 + "\n\n"
        f"**{plan['name']} Plan**\n"
        f"`Price   :` Rs. {plan['price_pkr']}\n"
        f"`Searches:` Up to {plan['searches_per_day']}/day\n\n"
        f"**How to Buy:**\n"
        f"1️⃣ Send **Rs. {plan['price_pkr']}** to admin\n"
        f"2️⃣ Forward payment screenshot to {PREMIUM_CONTACT}\n"
        f"3️⃣ Get instant activation! ✅\n\n"
        f"📞 **Contact:** {PREMIUM_CONTACT}\n"
        f"⚡ Usually takes < 5 minutes!\n\n"
        f"Tap the button below to contact:"
    )
    keyboard = [
        [InlineKeyboardButton(f"💬 Contact {PREMIUM_CONTACT}", url=f"https://t.me/sigmaogchat_bot")],
        [InlineKeyboardButton("🔙 Back to Plans", callback_data=cb("buy_premium"))],
        [InlineKeyboardButton("🔙 Shop", callback_data=cb("shop"))],
    ]

    # Log sale request
    db.record_premium_sale(uid, plan["name"], days, plan["price_pkr"])

    await notify_event(
        context, "premium_purchased",
        user_id=uid,
        user_name=get_user_display(uid),
        days=days,
        plan=plan["name"],
        amount=plan["price_pkr"],
    )

    await update.callback_query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode=ParseMode.MARKDOWN)


# ============================================================
# REFERRAL
# ============================================================

async def referral_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show referral info"""
    uid = update.effective_user.id
    code = db.get_ref_code(uid)
    u = db.get_user(uid)
    bot_username = (await context.bot.get_me()).username
    ref_link = f"https://t.me/{bot_username}?start={code}"
    count = u.get("referrals_count", 0)
    earnings = u.get("referral_earnings", 0) or count * COINS_PER_REFERRAL

    text = (
        f"👥 **Referral Program**\n"
        f"━" * 24 + "\n\n"
        f"Invite friends and earn rewards!\n\n"
        f"**Referral Link:**\n"
        f"`{ref_link}`\n\n"
        f"**Your Stats:**\n"
        f"• Referrals: **{count}**\n"
        f"• Earned: **+{earnings} 🪙**\n"
        f"• Per referral: **+{COINS_PER_REFERRAL} 🪙** + **{XP_PER_REFERRAL} XP**\n\n"
        f"Your friend also gets **+5 🪙** + **2 bonus searches**! 🎁"
    )
    keyboard = [
        [InlineKeyboardButton("📤 Share Referral Link",
                              url=f"tg://msg_url?url={ref_link}&text=🎮%20Play%20Akinator%20with%20me!%20Use%20my%20referral%20link%20to%20start%20with%20bonus%20coins!")],
        [InlineKeyboardButton("🏆 Top Referrers", callback_data=cb("lb_ref"))],
        [InlineKeyboardButton("🔙 Back", callback_data=cb("home"))],
    ]
    await update.callback_query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode=ParseMode.MARKDOWN)


# ============================================================
# SETTINGS
# ============================================================

async def settings_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show settings"""
    uid = update.effective_user.id
    s = db.get_user(uid)["settings"]
    lang = s.get("lang", "en")
    theme = s.get("theme", "characters")
    child = s.get("child_mode", False)

    text = (
        f"⚙️ **Settings**\n"
        f"━" * 24 + "\n\n"
        f"`Language :` {LANGUAGES.get(lang, '🇬🇧 English')}\n"
        f"`Theme    :` {THEMES.get(theme, 'Characters')}\n"
        f"`Child OK :` {'🟢 On' if child else '🔴 Off'}\n\n"
        f"Choose what to change:"
    )
    keyboard = [
        [InlineKeyboardButton(f"🌐 Language ({LANGUAGES.get(lang, 'en')[:4]})", callback_data=cb("set_lang"))],
        [InlineKeyboardButton(f"🎭 Theme ({THEMES.get(theme, 'Characters')})", callback_data=cb("set_theme"))],
        [InlineKeyboardButton(f"👶 Child Mode: {'✅' if child else '❌'}", callback_data=cb("toggle_child"))],
        [InlineKeyboardButton("🔙 Back", callback_data=cb("home"))],
    ]
    await update.callback_query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode=ParseMode.MARKDOWN)


async def set_lang(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Choose language"""
    uid = update.effective_user.id
    keyboard = []
    row = []
    for code, label in list(LANGUAGES.items())[:12]:
        row.append(InlineKeyboardButton(label, callback_data=cb("lang", code)))
        if len(row) == 2:
            keyboard.append(row)
            row = []
    if row:
        keyboard.append(row)
    keyboard.append([InlineKeyboardButton("🔙 Back", callback_data=cb("settings"))])
    await update.callback_query.edit_message_text(
        "🌐 **Choose Language:**", reply_markup=InlineKeyboardMarkup(keyboard), parse_mode=ParseMode.MARKDOWN
    )


async def set_theme_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Choose theme"""
    keyboard = []
    for key, label in THEMES.items():
        keyboard.append([InlineKeyboardButton(label, callback_data=cb("theme", key))])
    keyboard.append([InlineKeyboardButton("🔙 Back", callback_data=cb("settings"))])
    await update.callback_query.edit_message_text(
        "🎭 **Choose Theme:**", reply_markup=InlineKeyboardMarkup(keyboard), parse_mode=ParseMode.MARKDOWN
    )


# ============================================================
# LEADERBOARD
# ============================================================

async def leaderboard(update: Update, context: ContextTypes.DEFAULT_TYPE, category: str = "xp"):
    """Show leaderboard"""
    entries = db.get_leaderboard(category, limit=10)
    if not entries:
        text = "🏆 **Leaderboard** — No data yet!\n\nStart playing to rank up!"
        keyboard = [[InlineKeyboardButton("🔙 Back", callback_data=cb("home"))]]
        await update.callback_query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode=ParseMode.MARKDOWN)
        return

    labels = {
        "xp": "⚡ XP Leaderboard", "coins": "🪙 Coins Leaderboard",
        "wins": "🏆 Wins Leaderboard", "games": "🎮 Games Leaderboard",
        "level": "⭐ Level Leaderboard", "referrals": "👥 Top Referrers",
        "streak": "🔥 Streak Leaderboard",
    }
    title = labels.get(category, "🏆 Leaderboard")
    medals = ["🥇", "🥈", "🥉"]

    text = f"**{title}**\n" + "━" * 24 + "\n\n"
    for i, (uid, data) in enumerate(entries):
        medal = medals[i] if i < 3 else f"`{i+1}.`"
        name = data.get("first_name", data.get("username", f"User{uid}"))
        uname = data.get("username", "")
        if uname:
            name += f" (@{uname})"
        value = {
            "xp": data["xp"], "coins": data["coins"], "wins": data["games_won"],
            "games": data["games_played"], "level": data["level"],
            "referrals": data.get("referrals_count", 0),
            "streak": data.get("daily_streak", 0),
        }.get(category, data["xp"])
        uom = {"xp": "XP", "coins": "🪙", "wins": "🏆", "games": "🎮", "level": "⭐", "referrals": "👥", "streak": "🔥"}.get(category, "")
        text += f"{medal} **{name}** — `{value}` {uom}\n"

    keyboard = []
    cats = ["xp", "coins", "wins", "games", "level", "referrals", "streak"]
    row = []
    for c in cats:
        lbl = {"xp": "XP", "coins": "🪙", "wins": "🏆", "games": "🎮", "level": "⭐", "referrals": "👥", "streak": "🔥"}[c]
        row.append(InlineKeyboardButton(lbl, callback_data=cb("lb", c)))
        if len(row) == 3:
            keyboard.append(row)
            row = []
    if row:
        keyboard.append(row)
    keyboard.append([InlineKeyboardButton("🔙 Back", callback_data=cb("home"))])
    await update.callback_query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode=ParseMode.MARKDOWN)


# ============================================================
# ADMIN PANEL
# ============================================================

async def admin_panel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Admin panel main menu"""
    uid = update.effective_user.id
    if uid not in ADMIN_IDS:
        await update.callback_query.answer("⛔ Unauthorized", show_alert=True)
        return

    stats = f"**Users:** {db.get_user_count()}\n**Games:** {db.data['total_games']}\n**Revenue:** Rs.{db.get_total_premium_revenue()}\n**Coins Earned:** {db.data['total_coins_earned']} 🪙\n**Coins Spent:** {db.data['total_coins_spent']} 🪙"
    text = (
        f"👑 **Admin Panel**\n"
        f"━" * 24 + "\n\n"
        f"{stats}\n\n"
        f"**Commands (in chat):**\n"
        f"• `/addcoins <uid> <amount>` — Add coins\n"
        f"• `/setcoins <uid> <amount>` — Set coins\n"
        f"• `/grantprem <uid> <days>` — Grant premium\n"
        f"• `/removeprem <uid>` — Remove premium\n"
        f"• `/ban <uid> [reason]` — Ban user\n"
        f"• `/unban <uid>` — Unban user\n"
        f"• `/info <uid>` — User info\n"
        f"• `/broadcast <msg>` — Broadcast to all\n"
        f"• `/logs` — Admin logs"
    )
    keyboard = [
        [InlineKeyboardButton("💸 Premium Sales", callback_data=cb("admin_sales"))],
        [InlineKeyboardButton("📊 User List", callback_data=cb("admin_users"))],
        [InlineKeyboardButton("📋 Admin Logs", callback_data=cb("admin_logs"))],
        [InlineKeyboardButton("🔙 Back", callback_data=cb("home"))],
    ]
    await update.callback_query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode=ParseMode.MARKDOWN)


async def admin_sales(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show premium sales"""
    if update.effective_user.id not in ADMIN_IDS:
        return
    sales = db.get_premium_sales(15)
    if not sales:
        text = "💸 **No sales yet.**"
    else:
        text = "💸 **Premium Sales Log**\n" + "━" * 24 + "\n\n"
        for s in reversed(sales):
            uid = s.get("user_id", "?")
            plan = s.get("plan", "?")
            days = s.get("days", "?")
            amount = s.get("amount_pkr", "?")
            ts = s.get("timestamp", "")[:19]
            text += f"• User `{uid}` — {plan} ({days}d) — Rs.{amount} @ {ts}\n"
    keyboard = [[InlineKeyboardButton("🔙 Back", callback_data=cb("admin"))]]
    await update.callback_query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode=ParseMode.MARKDOWN)


async def admin_users_list(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show user list"""
    if update.effective_user.id not in ADMIN_IDS:
        return
    users = db.get_all_users()
    text = f"📊 **Users ({len(users)} total)**\n" + "━" * 24 + "\n\n"
    count = 0
    for uid in sorted(users.keys(), key=lambda x: int(x)):
        if count >= 15:
            text += f"... and {len(users) - 15} more\n"
            break
        u = users[uid]
        premium = u.get("is_premium", False) and db.is_premium(int(uid))
        prem_tag = " [👑]" if premium else ""
        ban_tag = " [🚫]" if u.get("banned") else ""
        text += f"• `{uid}` — {u.get('first_name', '?')}{prem_tag}{ban_tag}\n"
        count += 1
    keyboard = [[InlineKeyboardButton("🔙 Back", callback_data=cb("admin"))]]
    await update.callback_query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode=ParseMode.MARKDOWN)


async def admin_logs_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show admin logs"""
    if update.effective_user.id not in ADMIN_IDS:
        return
    logs = db.get_logs(20)
    if not logs:
        text = "📋 **No logs yet.**"
    else:
        text = "📋 **Recent Logs**\n" + "━" * 24 + "\n\n"
        for log in reversed(logs):
            ts = log.get("timestamp", "")[:19]
            msg = log.get("message", "")
            text += f"`{ts}` {msg}\n"
    keyboard = [[InlineKeyboardButton("🔙 Back", callback_data=cb("admin"))]]
    await update.callback_query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode=ParseMode.MARKDOWN)


# ============================================================
# ADMIN COMMAND HANDLERS (in-chat)
# ============================================================

async def admin_broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Broadcast message to all users"""
    uid = update.effective_user.id
    if uid not in ADMIN_IDS:
        await update.message.reply_text("⛔ Unauthorized")
        return

    if not context.args:
        await update.message.reply_text("Usage: `/broadcast <message>`", parse_mode=ParseMode.MARKDOWN)
        return

    msg = " ".join(context.args)
    sent = 0
    failed = 0
    total = db.get_user_count()

    status_msg = await update.message.reply_text(f"📢 Broadcasting to {total} users...")

    for uid_str in db.data["users"]:
        try:
            await context.bot.send_message(
                chat_id=int(uid_str),
                text=f"📢 **Broadcast**\n\n{msg}\n\n━" * 10 + "\nContact: {PREMIUM_CONTACT}",
                parse_mode=ParseMode.MARKDOWN,
            )
            sent += 1
            await asyncio.sleep(0.05)
        except Exception:
            failed += 1

    await status_msg.edit_text(f"✅ Broadcast complete!\n📤 Sent: {sent}\n❌ Failed: {failed}")

    await notify_event(
        context, "admin_action",
        action="Broadcast",
        target_id="ALL",
        target_name=f"Sent to {sent}/{total}",
        admin_id=uid,
    )


async def admin_addcoins(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Add coins to a user"""
    uid = update.effective_user.id
    if uid not in ADMIN_IDS:
        return

    if len(context.args) < 2:
        await update.message.reply_text("Usage: `/addcoins <user_id> <amount>`", parse_mode=ParseMode.MARKDOWN)
        return

    try:
        target = int(context.args[0])
        amount = int(context.args[1])
    except ValueError:
        await update.message.reply_text("❌ Invalid arguments. Use numbers.")
        return

    if amount <= 0:
        await update.message.reply_text("❌ Amount must be positive.")
        return

    db.add_coins(target, amount, f"Admin {uid} added")
    bal = db.get_balance(target)
    name = get_user_display(target)
    await update.message.reply_text(f"✅ Added **{amount} 🪙** to `{target}` ({name})\nNew balance: **{bal} 🪙**", parse_mode=ParseMode.MARKDOWN)

    await notify_event(
        context, "admin_action",
        action=f"Add {amount} coins",
        target_id=target,
        target_name=name,
        admin_id=uid,
    )


async def admin_setcoins(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Set coins for a user"""
    uid = update.effective_user.id
    if uid not in ADMIN_IDS:
        return

    if len(context.args) < 2:
        await update.message.reply_text("Usage: `/setcoins <user_id> <amount>`", parse_mode=ParseMode.MARKDOWN)
        return

    try:
        target = int(context.args[0])
        amount = int(context.args[1])
    except ValueError:
        await update.message.reply_text("❌ Invalid arguments.")
        return

    db.set_coins(target, amount, admin_id=uid)
    name = get_user_display(target)
    await update.message.reply_text(f"✅ Set `{target}` ({name}) coins to **{amount} 🪙**", parse_mode=ParseMode.MARKDOWN)

    await notify_event(
        context, "admin_action",
        action=f"Set coins to {amount}",
        target_id=target,
        target_name=name,
        admin_id=uid,
    )


async def admin_grantprem(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Grant premium to a user"""
    uid = update.effective_user.id
    if uid not in ADMIN_IDS:
        return

    if len(context.args) < 2:
        await update.message.reply_text("Usage: `/grantprem <user_id> <days>`", parse_mode=ParseMode.MARKDOWN)
        return

    try:
        target = int(context.args[0])
        days = int(context.args[1])
    except ValueError:
        await update.message.reply_text("❌ Invalid arguments.")
        return

    expiry = db.set_premium(target, days, admin_id=uid)
    name = get_user_display(target)
    await update.message.reply_text(f"✅ Granted **{days} days** premium to `{target}` ({name})\nExpires: {expiry[:19]}", parse_mode=ParseMode.MARKDOWN)

    await notify_event(
        context, "premium_granted",
        user_id=target,
        user_name=name,
        days=days,
        admin_id=uid,
        expiry=expiry,
    )


async def admin_removeprem(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Remove premium from user"""
    uid = update.effective_user.id
    if uid not in ADMIN_IDS:
        return

    if len(context.args) < 1:
        await update.message.reply_text("Usage: `/removeprem <user_id>`", parse_mode=ParseMode.MARKDOWN)
        return

    try:
        target = int(context.args[0])
    except ValueError:
        await update.message.reply_text("❌ Invalid user ID.")
        return

    db.remove_premium(target, admin_id=uid)
    name = get_user_display(target)
    await update.message.reply_text(f"✅ Removed premium from `{target}` ({name})", parse_mode=ParseMode.MARKDOWN)

    await notify_event(
        context, "admin_action",
        action="Remove Premium",
        target_id=target,
        target_name=name,
        admin_id=uid,
    )


async def admin_ban(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Ban a user"""
    uid = update.effective_user.id
    if uid not in ADMIN_IDS:
        return

    if not context.args:
        await update.message.reply_text("Usage: `/ban <user_id> [reason]`", parse_mode=ParseMode.MARKDOWN)
        return

    try:
        target = int(context.args[0])
        reason = " ".join(context.args[1:]) if len(context.args) > 1 else "No reason"
    except ValueError:
        await update.message.reply_text("❌ Invalid user ID.")
        return

    db.ban(target, reason, admin_id=uid)
    name = get_user_display(target)
    await update.message.reply_text(f"🚫 Banned `{target}` ({name})\nReason: {reason}", parse_mode=ParseMode.MARKDOWN)

    # Try to notify the user
    try:
        await context.bot.send_message(
            chat_id=target,
            text=f"🚫 **You have been banned.**\nReason: {reason}\n\n📞 Contact: {PREMIUM_CONTACT}",
            parse_mode=ParseMode.MARKDOWN,
        )
    except Exception:
        pass

    await notify_event(
        context, "user_banned",
        user_id=target,
        user_name=name,
        reason=reason,
        admin_id=uid,
    )


async def admin_unban(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Unban a user"""
    uid = update.effective_user.id
    if uid not in ADMIN_IDS:
        return

    if not context.args:
        await update.message.reply_text("Usage: `/unban <user_id>`", parse_mode=ParseMode.MARKDOWN)
        return

    try:
        target = int(context.args[0])
    except ValueError:
        await update.message.reply_text("❌ Invalid user ID.")
        return

    db.unban(target, admin_id=uid)
    name = get_user_display(target)
    await update.message.reply_text(f"✅ Unbanned `{target}` ({name})", parse_mode=ParseMode.MARKDOWN)

    await notify_event(
        context, "user_unbanned",
        user_id=target,
        user_name=name,
        admin_id=uid,
    )


async def admin_info(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show user info"""
    uid = update.effective_user.id
    if uid not in ADMIN_IDS:
        return

    if not context.args:
        await update.message.reply_text("Usage: `/info <user_id>`", parse_mode=ParseMode.MARKDOWN)
        return

    try:
        target = int(context.args[0])
    except ValueError:
        await update.message.reply_text("❌ Invalid user ID.")
        return

    info = db.get_user_info(target)
    await update.message.reply_text(info, parse_mode=ParseMode.MARKDOWN)


async def admin_logs_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show admin logs via command"""
    uid = update.effective_user.id
    if uid not in ADMIN_IDS:
        return

    logs = db.get_logs(10)
    if not logs:
        await update.message.reply_text("📋 **No logs yet.**", parse_mode=ParseMode.MARKDOWN)
        return

    text = "📋 **Recent Logs**\n" + "━" * 24 + "\n\n"
    for log in reversed(logs[-10:]):
        ts = log.get("timestamp", "")[:19]
        msg = log.get("message", "")
        text += f"`{ts}` {msg}\n"

    await update.message.reply_text(text, parse_mode=ParseMode.MARKDOWN)


# ============================================================
# CALLBACK ROUTER
# ============================================================

async def callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Route all callback queries"""
    query = update.callback_query
    data = query.data
    uid = update.effective_user.id

    if db.is_banned(uid):
        await query.answer("❌ You are banned!", show_alert=True)
        return

    # Check force join for all callbacks except verify
    if not data.startswith("aki:verify"):
        ok, missing = await check_subscriptions(uid, context)
        if not ok:
            await force_join_prompt(update, context, missing)
            return

    # Parse callback: aki:action:data OR aki:action
    parts = data.split(":", 2)
    if len(parts) < 2 or parts[0] != "aki":
        await query.answer()
        return

    action = parts[1]
    extra = parts[2] if len(parts) > 2 else ""

    await query.answer()

    route_map = {
        "home": lambda: main_menu(update, context, edit=True),
        "play": lambda: start_game(update, context),
        "profile": lambda: show_profile(update, context),
        "daily": lambda: daily_reward(update, context),
        "shop": lambda: shop_menu(update, context),
        "buy_coins": lambda: buy_coins_menu(update, context),
        "buy_premium": lambda: premium_menu(update, context),
        "referral": lambda: referral_menu(update, context),
        "settings": lambda: settings_menu(update, context),
        "set_lang": lambda: set_lang(update, context),
        "set_theme": lambda: set_theme_menu(update, context),
        "verify": lambda: verify_subscription(update, context),
        "wrong": lambda: wrong_guess(update, context),
        "back_game": lambda: go_back(update, context),
        "pay_play": lambda: pay_to_play(update, context),
        "admin": lambda: admin_panel(update, context),
        "admin_sales": lambda: admin_sales(update, context),
        "admin_users": lambda: admin_users_list(update, context),
        "admin_logs_panel": lambda: admin_logs_menu(update, context),
    }

    if action == "ans" and extra:
        await handle_answer(update, context, extra)
    elif action == "back":
        await go_back(update, context)
    elif action == "coins_pack" and extra:
        await coins_pack_selected(update, context, extra)
    elif action == "prem_plan" and extra:
        await premium_plan_selected(update, context, extra)
    elif action == "lb" and extra:
        await leaderboard(update, context, extra)
    elif action in ("lb_xp", "lb_coins", "lb_wins", "lb_games", "lb_level", "lb_ref", "lb_streak"):
        cat = action.replace("lb_", "")
        await leaderboard(update, context, cat)
    elif action == "lang" and extra:
        db.update_user(uid, settings={**db.get_user(uid)["settings"], "lang": extra})
        await query.answer(f"✅ Language set!", show_alert=True)
        await settings_menu(update, context)
    elif action == "theme" and extra:
        db.update_user(uid, settings={**db.get_user(uid)["settings"], "theme": extra})
        await query.answer(f"✅ Theme set!", show_alert=True)
        await settings_menu(update, context)
    elif action == "toggle_child":
        s = db.get_user(uid)["settings"]
        db.update_user(uid, settings={**s, "child_mode": not s.get("child_mode", False)})
        await query.answer(f"✅ Child mode toggled!", show_alert=True)
        await settings_menu(update, context)
    elif action in route_map:
        await route_map[action]()
    else:
        # Default: fallback for LB
        if action.startswith("lb_"):
            cat = action.replace("lb_", "")
            await leaderboard(update, context, cat)
        else:
            await main_menu(update, context, edit=True)


# ============================================================
# ERROR HANDLER
# ============================================================

async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE):
    """Handle errors"""
    logger.error(f"Update {update} caused error {context.error}")
    try:
        if isinstance(update, Update) and update.effective_chat:
            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text=f"❌ An error occurred. Please try again.\n\n📞 Contact: {PREMIUM_CONTACT}",
            )
    except Exception:
        pass


# ============================================================
# MAIN
# ============================================================

def main():
    """Start the bot"""
    print("=" * 50)
    print("🚀 PREMIUM AKINATOR BOT")
    print(f"📆 Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"👑 Admins: {ADMIN_IDS}")
    print(f"📢 Notification: {NOTIFICATION_CHANNEL}")
    print(f"📞 Support: {PREMIUM_CONTACT}")
    print(f"🔧 Akinator Lib: {'✅ Installed' if AKINATOR_AVAILABLE else '❌ NOT INSTALLED'}")
    print(f"💾 Database: {db.filepath}")
    print(f"👤 Users: {db.get_user_count()}")
    print("=" * 50)

    app = Application.builder().token(BOT_TOKEN).build()

    # -- Command Handlers --
    app.add_handler(CommandHandler("start", home_handler))
    app.add_handler(CommandHandler("menu", home_handler))
    app.add_handler(CommandHandler("home", home_handler))

    # Admin commands
    app.add_handler(CommandHandler("broadcast", admin_broadcast, filters.User(user_id=ADMIN_IDS)))
    app.add_handler(CommandHandler("addcoins", admin_addcoins, filters.User(user_id=ADMIN_IDS)))
    app.add_handler(CommandHandler("setcoins", admin_setcoins, filters.User(user_id=ADMIN_IDS)))
    app.add_handler(CommandHandler("grantprem", admin_grantprem, filters.User(user_id=ADMIN_IDS)))
    app.add_handler(CommandHandler("removeprem", admin_removeprem, filters.User(user_id=ADMIN_IDS)))
    app.add_handler(CommandHandler("ban", admin_ban, filters.User(user_id=ADMIN_IDS)))
    app.add_handler(CommandHandler("unban", admin_unban, filters.User(user_id=ADMIN_IDS)))
    app.add_handler(CommandHandler("info", admin_info, filters.User(user_id=ADMIN_IDS)))
    app.add_handler(CommandHandler("logs", admin_logs_cmd, filters.User(user_id=ADMIN_IDS)))

    # Callback handler
    app.add_handler(CallbackQueryHandler(callback_handler, pattern=r"^aki:"))

    # Error handler
    app.add_error_handler(error_handler)

    print("\n✨ Bot is running! Press Ctrl+C to stop.\n")

    # Run the bot
    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
