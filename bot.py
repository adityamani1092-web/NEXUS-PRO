"""
NEXUS PROTECTION — starter Telegram group-management bot.
This is a fresh starter project. Features marked in README are implemented as a baseline;
third-party game actions cannot be intercepted/undone by Telegram Bot API.
"""
import os, re, logging, asyncio, sqlite3
from datetime import timedelta
from dotenv import load_dotenv
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, KeyboardButton, ReplyKeyboardMarkup
from telegram.constants import ChatType
from telegram.ext import (
    Application, CommandHandler, MessageHandler, CallbackQueryHandler,
    ContextTypes, filters
)
from telegram.error import TelegramError

load_dotenv()
TOKEN = os.getenv("BOT_TOKEN", "")
OWNER_USERNAME = os.getenv("OWNER_USERNAME", "Look_at_me60").lstrip("@")
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
log = logging.getLogger("nexus")

# Simple in-memory starter state. For production, replace with MongoDB persistence.
verified_users = set()
protection = {}  # user_id -> {"kill": bool, "rob": bool}
DB_PATH = os.getenv("DATABASE_PATH", "nexus_protection.db")

def init_db():
    with sqlite3.connect(DB_PATH) as db:
        db.execute("""CREATE TABLE IF NOT EXISTS protection (
            user_id INTEGER PRIMARY KEY, kill INTEGER NOT NULL DEFAULT 0,
            rob INTEGER NOT NULL DEFAULT 0)""")
        db.commit()

def load_protection(user_id):
    with sqlite3.connect(DB_PATH) as db:
        row = db.execute("SELECT kill, rob FROM protection WHERE user_id=?", (user_id,)).fetchone()
    return {"kill": bool(row[0]), "rob": bool(row[1])} if row else {"kill": False, "rob": False}

def save_protection(user_id, values):
    with sqlite3.connect(DB_PATH) as db:
        db.execute("INSERT INTO protection(user_id,kill,rob) VALUES(?,?,?) "
                   "ON CONFLICT(user_id) DO UPDATE SET kill=excluded.kill, rob=excluded.rob",
                   (user_id, int(values["kill"]), int(values["rob"])))
        db.commit()

def get_protection(user_id):
    if user_id not in protection:
        protection[user_id] = load_protection(user_id)
    return protection[user_id]
group_settings = {} # chat_id -> settings

def is_owner(user):
    return bool(user and user.username and user.username.lower() == OWNER_USERNAME.lower())

def main_menu():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("➕ Add to Group", url=f"https://t.me/{os.getenv('BOT_USERNAME','nexus_anbot')}?startgroup=true"),
         InlineKeyboardButton("📚 Help", callback_data="help")],
        [InlineKeyboardButton("🎮 Game Protection", callback_data="game"),
         InlineKeyboardButton("📡 Ping", callback_data="ping")],
        [InlineKeyboardButton("👑 Owner", callback_data="owner")]
    ])

def game_menu(user_id):
    p=get_protection(user_id)
    verified=user_id in verified_users
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("📱 Verify Telegram Number", callback_data="verify")],
        [InlineKeyboardButton(f"🛡️ Kill Protection: {'ON' if p['kill'] else 'OFF'}", callback_data="toggle_kill"),
         InlineKeyboardButton(f"💰 Rob Protection: {'ON' if p['rob'] else 'OFF'}", callback_data="toggle_rob")],
        [InlineKeyboardButton("📊 My Protection Status", callback_data="status")],
        [InlineKeyboardButton("⬅️ Main Menu", callback_data="home")]
    ])

def help_menu():
    sections=[
        ("👥 Group Management","/ban /unban /kick /mute /unmute /tmute /warn /warnings"),
        ("🛡️ Member Protection","/approve /unapprove /free /unfree /userinfo"),
        ("🚨 Anti-Spam","/antispam /setwarnlimit /lock /unlock"),
        ("🔎 Filters","/filter /filters /stop /stopall"),
        ("🧹 Message Tools","/purge /pin /unpin /slowmode"),
        ("👋 Welcome & Rules","/setwelcome /setrules /rules"),
        ("🎮 Game Protection","DM: /gameprotection; auto-delete reply /kill and /rob commands where visible"),
        ("⚙️ Group Settings","/settings"),
        ("👑 Owner Panel","/stats /broadcast (owner only)")
    ]
    rows=[[InlineKeyboardButton(name, callback_data=f"help_{i}")] for i,(name,_) in enumerate(sections)]
    rows.append([InlineKeyboardButton("⬅️ Main Menu", callback_data="home")])
    return InlineKeyboardMarkup(rows), sections

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type == ChatType.PRIVATE:
        await update.effective_message.reply_text(
            "🛡️ <b>NEXUS PROTECTION</b>\\n\\nProtect your group. Manage members.\\n\\n"
            f"👑 Owner: @{OWNER_USERNAME}\\n🤖 Bot: @{os.getenv('BOT_USERNAME','nexus_anbot')}",
            parse_mode="HTML", reply_markup=main_menu()
        )
    else:
        await update.effective_message.reply_text("🛡️ NEXUS PROTECTION is active. Admins: use /help.")

async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    kb, _ = help_menu()
    await update.effective_message.reply_text("📚 <b>NEXUS HELP CENTER</b>\\nChoose a category:", parse_mode="HTML", reply_markup=kb)

async def game_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid=update.effective_user.id
    await update.effective_message.reply_text(
        f"🎮 <b>NEXUS GAME PROTECTION</b>\\n\\n🆔 User ID: <code>{uid}</code>\\n"
        f"📱 Number verification: {'Verified' if uid in verified_users else 'Not verified'}\\n"
        "🛡️ Kill and 💰 Rob toggles are stored for this user.",
        parse_mode="HTML", reply_markup=game_menu(uid)
    )

async def button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q=update.callback_query
    await q.answer()
    uid=q.from_user.id
    if q.data=="home":
        await q.edit_message_text("🛡️ <b>NEXUS PROTECTION</b>\\nChoose an option:", parse_mode="HTML", reply_markup=main_menu())
    elif q.data=="help":
        kb,_=help_menu()
        await q.edit_message_text("📚 <b>NEXUS HELP CENTER</b>", parse_mode="HTML", reply_markup=kb)
    elif q.data=="game":
        await q.edit_message_text("🎮 <b>NEXUS GAME PROTECTION</b>\\nVerify your contact once, then manage your protection.", parse_mode="HTML", reply_markup=game_menu(uid))
    elif q.data=="ping":
        await q.edit_message_text(f"📡 Pong! {round(context.application.bot_data.get('started_at',0) and 0 or 0)} ms")
    elif q.data=="owner":
        await q.edit_message_text(f"👑 Owner: @{OWNER_USERNAME}")
    elif q.data=="verify":
        kb=ReplyKeyboardMarkup([[KeyboardButton("📱 Share my Telegram contact", request_contact=True)]], resize_keyboard=True, one_time_keyboard=True)
        await q.message.reply_text("Share your own contact to verify. We do not request Telegram OTP or password.", reply_markup=kb)
    elif q.data in ("toggle_kill","toggle_rob"):
        key="kill" if q.data=="toggle_kill" else "rob"
        p=get_protection(uid)
        p[key]=not p[key]
        await q.edit_message_reply_markup(reply_markup=game_menu(uid))
    elif q.data=="status":
        p=get_protection(uid)
        await q.edit_message_text(f"📊 Protection status\\n🛡️ Kill: {'ON' if p['kill'] else 'OFF'}\\n💰 Rob: {'ON' if p['rob'] else 'OFF'}\\n📱 Verified: {'Yes' if uid in verified_users else 'No'}", reply_markup=game_menu(uid))
    elif q.data.startswith("help_"):
        _, sections=help_menu()
        i=int(q.data.split("_")[1])
        await q.edit_message_text(sections[i][1], reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ Help",callback_data="help")]]))

async def contact_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    c=update.effective_message.contact
    u=update.effective_user
    if c and c.user_id == u.id:
        verified_users.add(u.id)
        await update.effective_message.reply_text("✅ Contact verified. Your User ID is now marked verified. Use /gameprotection to manage settings.")
    else:
        await update.effective_message.reply_text("❌ Please share your own Telegram contact using the button.")

async def admin_check(update, context):
    if update.effective_chat.type == ChatType.PRIVATE: return False
    try:
        member=await context.bot.get_chat_member(update.effective_chat.id, update.effective_user.id)
        return member.status in ("administrator","creator") or is_owner(update.effective_user)
    except TelegramError:
        return is_owner(update.effective_user)

async def auto_delete_game_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg=update.effective_message
    if not msg or update.effective_chat.type == ChatType.PRIVATE: return
    text=msg.text or msg.caption or ""
    match = re.match(r"^\\s*/(kill|rob)(?:@\\w+)?(?:\\s|$)", text, re.I)
    if not match or not msg.reply_to_message: return
    target_id = msg.reply_to_message.from_user.id
    action = match.group(1).lower()
    p = get_protection(target_id)
    if p.get(action, False):
        try:
            await msg.delete()
            await msg.reply_to_message.reply_text(
                f"🛡️ {action.title()} Protection blocked this action for "
                f"{msg.reply_to_message.from_user.mention_html()}",
                parse_mode="HTML"
            )
        except TelegramError:
            log.info("Could not delete game command; bot may need delete permission.")

async def protect_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    p = get_protection(uid)
    p["kill"] = True
    p["rob"] = True
    save_protection(uid, p)
    await update.effective_message.reply_text(
        "🛡️ Kill Protection: ON\\n💰 Rob Protection: ON\\n"
        "Protection is saved permanently and stays ON after bot restarts. "
        "Use /unprotect to turn both off."
    )

async def unprotect_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    p = get_protection(uid)
    p["kill"] = False
    p["rob"] = False
    save_protection(uid, p)
    await update.effective_message.reply_text("⚠️ Kill and Rob Protection are now OFF.")

async def target_user(update, context):
    msg=update.effective_message
    if msg.reply_to_message:
        return msg.reply_to_message.from_user
    if context.args:
        arg=context.args[0]
        if arg.isdigit():
            try: return await context.bot.get_chat(int(arg))
            except TelegramError: return None
        if arg.startswith("@"):
            try: return await context.bot.get_chat(arg)
            except TelegramError: return None
    return None

async def ban(update, context):
    if not await admin_check(update, context):
        return await update.effective_message.reply_text("Admins only.")
    target=await target_user(update,context)
    if not target: return await update.effective_message.reply_text("Reply to a member or use /ban <user_id|@username>.")
    try:
        await context.bot.ban_chat_member(update.effective_chat.id,target.id)
        await update.effective_message.reply_text(f"🛡️ Banned: {target.first_name}")
    except TelegramError as e: await update.effective_message.reply_text(f"Could not ban: {e}")

async def unban(update, context):
    if not await admin_check(update, context): return
    if not context.args or not context.args[0].isdigit(): return await update.effective_message.reply_text("Usage: /unban <user_id>")
    try:
        await context.bot.unban_chat_member(update.effective_chat.id,int(context.args[0]), only_if_banned=True)
        await update.effective_message.reply_text("✅ Member unbanned.")
    except TelegramError as e: await update.effective_message.reply_text(f"Could not unban: {e}")

async def mute(update, context):
    if not await admin_check(update, context): return
    target=await target_user(update,context)
    if not target: return await update.effective_message.reply_text("Reply or use /mute <user_id|@username>.")
    from telegram import ChatPermissions
    try:
        await context.bot.restrict_chat_member(update.effective_chat.id,target.id,ChatPermissions(can_send_messages=False))
        await update.effective_message.reply_text(f"🔇 Muted: {target.first_name}")
    except TelegramError as e: await update.effective_message.reply_text(f"Could not mute: {e}")

async def unmute(update, context):
    if not await admin_check(update, context): return
    target=await target_user(update,context)
    if not target: return await update.effective_message.reply_text("Reply or use /unmute <user_id>.")
    from telegram import ChatPermissions
    try:
        await context.bot.restrict_chat_member(update.effective_chat.id,target.id,ChatPermissions(can_send_messages=True,can_send_audios=True,can_send_documents=True,can_send_photos=True,can_send_videos=True,can_send_video_notes=True,can_send_voice_notes=True,can_send_polls=True,can_send_other_messages=True,can_add_web_page_previews=True))
        await update.effective_message.reply_text(f"🔊 Unmuted: {target.first_name}")
    except TelegramError as e: await update.effective_message.reply_text(f"Could not unmute: {e}")

async def stats(update, context):
    if not is_owner(update.effective_user): return
    await update.effective_message.reply_text(f"👑 NEXUS OWNER STATS\\nKnown verified users: {len(verified_users)}\\nNote: persistent MongoDB and full group/user counters are not configured in this starter.")

async def broadcast(update, context):
    if not is_owner(update.effective_user): return
    if not context.args: return await update.effective_message.reply_text("Usage: /broadcast <text>")
    await update.effective_message.reply_text("Broadcast needs persistent user/group registry; configure MongoDB before using.")

def main():
    if not TOKEN:
        raise SystemExit("BOT_TOKEN missing. Copy .env.example to .env and set your token.")
    init_db()
    app=Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start",start))
    app.add_handler(CommandHandler("help",help_cmd))
    app.add_handler(CommandHandler(["gameprotection","game"],game_cmd))
    app.add_handler(CommandHandler("protect", protect_cmd))
    app.add_handler(CommandHandler("unprotect",unprotect_cmd))
    app.add_handler(CommandHandler("ban",ban))
    app.add_handler(CommandHandler("unban",unban))
    app.add_handler(CommandHandler("mute",mute))
    app.add_handler(CommandHandler("unmute",unmute))
    app.add_handler(CommandHandler("stats",stats))
    app.add_handler(CommandHandler("broadcast",broadcast))
    app.add_handler(CallbackQueryHandler(button))
    app.add_handler(MessageHandler(filters.CONTACT,contact_handler))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND,auto_delete_game_command))
    app.add_handler(MessageHandler(filters.COMMAND,auto_delete_game_command))
    log.info("NEXUS PROTECTION starting...")
    app.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__=="__main__":
    main()
