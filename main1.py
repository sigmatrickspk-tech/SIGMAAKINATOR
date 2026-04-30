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
