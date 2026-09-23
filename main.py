    from alive import keep_alive
    keep_alive()
# ============================================================
#  Premium Video Bot — Single File Build
#  Owner-controlled via /admin panel
# ============================================================

# ========== CONFIG — EDIT THESE ==========
BOT_TOKEN    = "8919555551:AAGV6HmgGy5ioNkB5BylHA5ZiLKGBcFEpF8"          # from @BotFather
ADMIN_CHAT_ID = 8395006857                   # your Telegram user ID (from @userinfobot)
CHANNEL_ID    = -1001234567890                # your private upload channel ID (starts with -100)

# ========== EDITABLE LINKS (also editable via /admin) ==========
HELP_DM_LINK         = "https://t.me/Premiumselee"
DEMO_GROUP_LINK      = "https://t.me/+3CIhP6FePCJlOTNl"
PREMIUM_CHANNEL_LINK = "https://t.me/+BffX1nv6dsZkZjk1"

UPI_ID        = "7302110953@fam"
QR_IMAGE_PATH = "qr.png"

# ========== PLANS ==========
PLANS = {
    "50":  {"label": "50 Links",  "price": 100, "days": 30},
    "100": {"label": "100 Links", "price": 150, "days": 30},
}

# ========== TEXTS ==========
WELCOME_TEXT = (
    "👋 <b>Hello! Welcome to our bot.</b>\n\n"
    "We provide <b>all type of videos</b>:\n"
    "1️⃣ MMS\n"
    "2️⃣ CP\n"
    "3️⃣ Gay\n"
    "4️⃣ Lesbian\n"
    "5️⃣ &amp; so on...\n\n"
    "Choose an option below 👇"
)

HELP_TEXT = (
    "🆘 <b>Help</b>\n\n"
    "Koi bhi doubt ya support ke liye DM karo:\n"
    "👉 <b>@Premiumselee</b>\n\n"
    "Hum jaldi reply karenge."
)

DEMO_TEXT = (
    "🎬 <b>Demo / Preview Group</b>\n\n"
    "Yahan free preview content dekh sakte ho:\n"
    "👉 <b>Join below</b>"
)


# ========== IMPORTS ==========
import sqlite3
import os
import json
import tempfile
import zipfile
import asyncio
from datetime import datetime, timedelta
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application, CommandHandler, CallbackQueryHandler, MessageHandler,
    filters, ContextTypes
)

try:
    asyncio.get_event_loop()
except RuntimeError:
    asyncio.set_event_loop(asyncio.new_event_loop())


# ========== DATABASE ==========
conn = sqlite3.connect("database.db", check_same_thread=False)
cursor = conn.cursor()

cursor.execute('''
    CREATE TABLE IF NOT EXISTS users (
        user_id INTEGER PRIMARY KEY,
        username TEXT,
        is_premium INTEGER DEFAULT 0,
        subscription_expiry TEXT,
        pending_plan TEXT,
        payment_status TEXT
    )
''')
cursor.execute('''
    CREATE TABLE IF NOT EXISTS videos (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        file_id TEXT, title TEXT, duration INTEGER, size INTEGER,
        thumbnail_file_id TEXT, added_date TEXT, views INTEGER DEFAULT 0
    )
''')
conn.commit()


# ========== EDITABLE LINKS STORE ==========
LINKS_FILE = "links.json"

def load_links():
    try:
        with open(LINKS_FILE, "r") as f:
            return json.load(f)
    except Exception:
        return {
            "help":    HELP_DM_LINK,
            "demo":    DEMO_GROUP_LINK,
            "channel": PREMIUM_CHANNEL_LINK,
            "upi":     UPI_ID,
        }

def save_links(data):
    with open(LINKS_FILE, "w") as f:
        json.dump(data, f, indent=4)

LINKS = load_links()


# ========== USER HELPERS ==========
def get_user(uid):
    cursor.execute("SELECT * FROM users WHERE user_id=?", (uid,))
    r = cursor.fetchone()
    if r:
        return {'user_id': r[0], 'username': r[1], 'is_premium': r[2],
                'subscription_expiry': r[3], 'pending_plan': r[4], 'payment_status': r[5]}
    return None

def create_user(uid, uname):
    cursor.execute("INSERT OR IGNORE INTO users (user_id, username) VALUES (?,?)", (uid, uname))
    conn.commit()

def update_user_premium(uid, expiry):
    cursor.execute("UPDATE users SET is_premium=?, subscription_expiry=? WHERE user_id=?",
                   (1 if expiry else 0, expiry, uid))
    conn.commit()

def update_pending_plan(uid, plan, status):
    cursor.execute("UPDATE users SET pending_plan=?, payment_status=? WHERE user_id=?",
                   (plan, status, uid))
    conn.commit()

def get_pending_requests():
    cursor.execute("SELECT user_id, username, pending_plan, payment_status FROM users WHERE payment_status='awaiting'")
    return cursor.fetchall()

def get_all_users():
    cursor.execute("SELECT user_id FROM users")
    return cursor.fetchall()


# ========== ADMIN MANAGEMENT ==========
ADMINS_FILE = "admins.json"

def load_admins():
    try:
        with open(ADMINS_FILE) as f:
            return json.load(f)
    except Exception:
        return []

def save_admins(a):
    with open(ADMINS_FILE, "w") as f:
        json.dump(a, f, indent=4)

def is_admin_user(uid):
    return uid == ADMIN_CHAT_ID or uid in load_admins()

def add_admin_user(uid):
    a = load_admins()
    if uid not in a and uid != ADMIN_CHAT_ID:
        a.append(uid); save_admins(a); return True
    return False

def remove_admin_user(uid):
    a = load_admins()
    if uid in a:
        a.remove(uid); save_admins(a); return True
    return False


# ========== KEYBOARDS ==========
def start_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🆘 Help", callback_data='help'),
         InlineKeyboardButton("🎬 Demo", callback_data='demo')],
        [InlineKeyboardButton("💎 Buy Premium", callback_data='buy')],
    ])

def plans_keyboard():
    kb = []
    for key, p in PLANS.items():
        kb.append([InlineKeyboardButton(f"💎 {p['label']} – ₹{p['price']}", callback_data=f'plan_{key}')])
    kb.append([InlineKeyboardButton("🔙 Back", callback_data='start')])
    return InlineKeyboardMarkup(kb)

def back_kb(cb='start'):
    return InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Back", callback_data=cb)]])

def admin_panel_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("📋 Pending Payments", callback_data='admin_pending')],
        [InlineKeyboardButton("📊 Stats", callback_data='admin_stats')],
        [InlineKeyboardButton("🔗 Edit Links", callback_data='admin_links')],
        [InlineKeyboardButton("💳 Edit UPI ID", callback_data='admin_upi')],
        [InlineKeyboardButton("📸 Update QR", callback_data='admin_setqr')],
        [InlineKeyboardButton("📢 Broadcast", callback_data='admin_broadcast')],
        [InlineKeyboardButton("📦 Upload Zip", callback_data='admin_zip')],
        [InlineKeyboardButton("👑 Manage Admins", callback_data='admin_manage')],
        [InlineKeyboardButton("🔙 Main Menu", callback_data='start')],
    ])

def links_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton(f"🆘 Help: {LINKS['help'][:30]}", callback_data='edit_help')],
        [InlineKeyboardButton(f"🎬 Demo: {LINKS['demo'][:30]}", callback_data='edit_demo')],
        [InlineKeyboardButton(f"📢 Channel: {LINKS['channel'][:30]}", callback_data='edit_channel')],
        [InlineKeyboardButton("🔙 Back", callback_data='admin_panel')],
    ])


# ========== USER-FACING HANDLERS ==========
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    u = update.effective_user
    create_user(u.id, u.username)
    context.user_data.clear()
    text = WELCOME_TEXT
    kb = start_keyboard()
    if update.callback_query:
        await update.callback_query.answer()
        await update.callback_query.edit_message_text(text, reply_markup=kb, parse_mode="HTML")
    else:
        await update.effective_message.reply_text(text, reply_markup=kb, parse_mode="HTML")

async def help_cb(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    kb = InlineKeyboardMarkup([
        [InlineKeyboardButton("💬 Open DM", url=LINKS['help'])],
        [InlineKeyboardButton("🔙 Back", callback_data='start')],
    ])
    await q.edit_message_text(HELP_TEXT, reply_markup=kb, parse_mode="HTML")

async def demo_cb(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    kb = InlineKeyboardMarkup([
        [InlineKeyboardButton("🎬 Join Demo Group", url=LINKS['demo'])],
        [InlineKeyboardButton("🔙 Back", callback_data='start')],
    ])
    await q.edit_message_text(DEMO_TEXT, reply_markup=kb, parse_mode="HTML")

async def buy_cb(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    await q.edit_message_text(
        "💎 <b>Premium Plans</b>\n\nNeeche se apna plan choose karo:",
        reply_markup=plans_keyboard(),
        parse_mode="HTML"
    )

async def plan_selected(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    key = q.data.split('_')[1]
    plan = PLANS.get(key)
    if not plan:
        await q.edit_message_text("❌ Invalid plan.")
        return
    uid = q.from_user.id
    update_pending_plan(uid, key, 'awaiting')

    text = (f"📲 <b>Payment Details</b>\n\n"
            f"💎 Plan: <b>{plan['label']}</b>\n"
            f"💰 Amount: <b>₹{plan['price']}</b>\n"
            f"🆔 UPI ID: <code>{LINKS['upi']}</code>\n\n"
            f"✅ Payment karke <b>screenshot bhejo</b> isi chat pe.\n"
            f"Admin verify karke channel link de dega.")

    await q.edit_message_text(text, reply_markup=back_kb('buy'), parse_mode="HTML")

    # Send QR if it exists
    try:
        with open(QR_IMAGE_PATH, 'rb') as qr:
            await context.bot.send_photo(chat_id=uid, photo=qr,
                                         caption="📸 Scan & pay, then send screenshot here.")
    except FileNotFoundError:
        pass

    await context.bot.send_message(uid,
        "📩 <b>Ab apna payment screenshot bhejo isi chat pe.</b>",
        parse_mode="HTML")


# ========== SCREENSHOT HANDLER ==========
async def handle_user_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    u = update.effective_user
    photo = update.message.photo[-1]
    ud = get_user(u.id)

    if not ud or not ud['pending_plan']:
        await update.message.reply_text(
            "❌ Pehle <b>Buy</b> pe click karke plan select karo.",
            parse_mode="HTML")
        return

    plan = PLANS.get(ud['pending_plan'])
    if not plan:
        await update.message.reply_text("❌ Invalid plan. Dobara Buy karo.")
        return

    kb = InlineKeyboardMarkup([[
        InlineKeyboardButton("✅ Approve", callback_data=f'approve_{u.id}'),
        InlineKeyboardButton("❌ Reject",  callback_data=f'reject_{u.id}'),
    ]])

    await context.bot.send_photo(
        chat_id=ADMIN_CHAT_ID,
        photo=photo.file_id,
        caption=(f"📩 <b>New Payment Request</b>\n"
                 f"👤 @{u.username or 'no_username'} (ID: <code>{u.id}</code>)\n"
                 f"💎 Plan: <b>{plan['label']}</b>\n"
                 f"💰 Amount: ₹{plan['price']}"),
        reply_markup=kb,
        parse_mode="HTML"
    )
    await update.message.reply_text(
        "✅ Screenshot mil gaya! Admin verify karke jald hi channel link bhejega.",
        parse_mode="HTML")


# ========== APPROVE / REJECT ==========
async def approve_payment(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer("Approved ✅")
    uid = int(q.data.split('_')[1])
    ud = get_user(uid)
    if not ud:
        await q.edit_message_caption(caption="❌ User not found.")
        return
    plan = PLANS.get(ud['pending_plan'])
    if not plan:
        await q.edit_message_caption(caption="❌ Plan missing.")
        return

    expiry = datetime.now() + timedelta(days=plan['days'])
    update_user_premium(uid, expiry.strftime("%Y-%m-%d %H:%M:%S"))
    update_pending_plan(uid, None, 'approved')

    text = (f"🎉 <b>Payment Approved!</b>\n\n"
            f"💎 Plan: <b>{plan['label']}</b>\n"
            f"📅 Expiry: {expiry.strftime('%d %b %Y')}\n\n"
            f"📢 <b>Yeh raha aapka premium channel link:</b>\n"
            f"👉 {LINKS['channel']}\n\n"
            f"Join karo aur enjoy karo!")

    kb = InlineKeyboardMarkup([[
        InlineKeyboardButton("📢 Join Premium Channel", url=LINKS['channel'])
    ]])
    try:
        await context.bot.send_message(uid, text, reply_markup=kb, parse_mode="HTML")
    except Exception as e:
        print(f"Could not DM user {uid}: {e}")

    try:
        await q.edit_message_caption(
            caption=f"✅ Approved by @{q.from_user.username or q.from_user.id}")
    except Exception:
        pass

async def reject_payment(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer("Rejected ❌")
    uid = int(q.data.split('_')[1])
    update_pending_plan(uid, None, 'rejected')
    try:
        await context.bot.send_message(uid,
            "❌ Aapka payment verify nahi ho paya. Support se baat karo.")
    except Exception:
        pass
    try:
        await q.edit_message_caption(
            caption=f"❌ Rejected by @{q.from_user.username or q.from_user.id}")
    except Exception:
        pass


# ========== ADMIN PANEL ==========
async def admin_panel_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin_user(update.effective_user.id):
        await update.effective_message.reply_text("❌ Sirf admin.")
        return
    context.user_data.clear()
    await update.effective_message.reply_text(
        "🛠 <b>Admin Panel</b>\nKya karna hai?",
        reply_markup=admin_panel_keyboard(), parse_mode="HTML")

async def admin_panel_cb(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    if not is_admin_user(q.from_user.id):
        return
    context.user_data.clear()
    await q.edit_message_text("🛠 <b>Admin Panel</b>\nKya karna hai?",
                              reply_markup=admin_panel_keyboard(), parse_mode="HTML")

async def admin_pending(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    if not is_admin_user(q.from_user.id): return
    rows = get_pending_requests()
    if not rows:
        await q.edit_message_text("Koi pending nahi.", reply_markup=admin_panel_keyboard())
        return
    txt = "📋 <b>Pending Payments:</b>\n\n"
    for uid, uname, pk, _ in rows:
        label = PLANS.get(pk, {}).get('label', pk)
        txt += f"• @{uname or 'none'} (<code>{uid}</code>) – {label}\n"
    await q.edit_message_text(txt, reply_markup=admin_panel_keyboard(), parse_mode="HTML")

async def admin_stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    if not is_admin_user(q.from_user.id): return
    cursor.execute("SELECT COUNT(*) FROM users"); total = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM users WHERE is_premium=1"); prem = cursor.fetchone()[0]
    txt = f"📊 <b>Stats</b>\n\n👥 Total Users: <b>{total}</b>\n💎 Premium Users: <b>{prem}</b>"
    await q.edit_message_text(txt, reply_markup=admin_panel_keyboard(), parse_mode="HTML")

async def admin_links_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    if not is_admin_user(q.from_user.id): return
    await q.edit_message_text("🔗 <b>Edit Links</b>\nKonsa link badalna hai?",
                              reply_markup=links_keyboard(), parse_mode="HTML")

async def edit_link_prompt(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    if not is_admin_user(q.from_user.id): return
    key = q.data.split('_')[1]
    context.user_data['edit_link_key'] = key
    await q.message.reply_text(
        f"✏️ Naya <b>{key}</b> link bhejo.\n<i>(/cancel to abort)</i>",
        parse_mode="HTML")

async def admin_upi_prompt(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    if not is_admin_user(q.from_user.id): return
    context.user_data['edit_upi'] = True
    await q.message.reply_text(
        "💳 Naya UPI ID bhejo.\n<i>(/cancel to abort)</i>", parse_mode="HTML")

async def admin_setqr_prompt(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    if not is_admin_user(q.from_user.id): return
    context.user_data['awaiting_qr'] = True
    await q.message.reply_text("📸 Apna UPI QR image bhejo. (/cancel to abort)")

async def admin_broadcast_prompt(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    if not is_admin_user(q.from_user.id): return
    context.user_data['broadcast'] = True
    await q.message.reply_text(
        "📢 Broadcast message likho.\n<i>(/cancel to abort)</i>", parse_mode="HTML")

async def admin_zip_prompt(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    if not is_admin_user(q.from_user.id): return
    context.user_data['awaiting_zip'] = True
    await q.message.reply_text("📦 Zip file bhejo. (/cancel to abort)")


# ========== ADMIN — MANAGE ADMINS ==========
async def admin_manage_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    if not is_admin_user(q.from_user.id): return
    admins = load_admins()
    txt = (f"👑 <b>Admin Management</b>\n\n"
           f"Owner: <code>{ADMIN_CHAT_ID}</code>\n\n"
           f"Admins ({len(admins)}):\n")
    txt += "\n".join([f"• <code>{a}</code>" for a in admins]) if admins else "Koi nahi."
    kb = InlineKeyboardMarkup([
        [InlineKeyboardButton("➕ Add", callback_data='admin_add')],
        [InlineKeyboardButton("➖ Remove", callback_data='admin_remove')],
        [InlineKeyboardButton("🔙 Back", callback_data='admin_panel')],
    ])
    await q.edit_message_text(txt, reply_markup=kb, parse_mode="HTML")

async def admin_add_prompt(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    if not is_admin_user(q.from_user.id): return
    context.user_data['awaiting_admin_add'] = True
    await q.message.reply_text("Nayi admin ki User ID bhejo.\n/cancel to abort")

async def admin_remove_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    if not is_admin_user(q.from_user.id): return
    admins = load_admins()
    if not admins:
        await q.edit_message_text("Koi co-admin nahi hai.", reply_markup=back_kb('admin_manage'))
        return
    kb = [[InlineKeyboardButton(f"{a}", callback_data=f"rmadm_{a}")] for a in admins]
    kb.append([InlineKeyboardButton("Back", callback_data='admin_manage')])
    await q.edit_message_text("Kisko remove karna hai?", reply_markup=InlineKeyboardMarkup(kb))

async def admin_remove_confirm(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    if not is_admin_user(q.from_user.id): return
    aid = int(q.data.split('_')[-1])
    ok = remove_admin_user(aid)
    await q.edit_message_text(f"Removed {aid}" if ok else "Failed.", reply_markup=back_kb('admin_manage'), parse_mode="HTML")

# ======= COMBINED TEXT HANDLER - FINAL =======
async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.text:
        return
    u = update.effective_user
    text = update.message.text.strip()
    ud = context.user_data

    if text.lower() == '/cancel':
        ud.clear()
        await update.message.reply_text("Cancelled.")
        return

    if not is_admin_user(u.id):
        return

    if ud.get('awaiting_admin_add'):
        ud['awaiting_admin_add'] = False
        try:
            nid = int(text)
            if add_admin_user(nid):
                await update.message.reply_text(f"Admin {nid} added!")
            else:
                await update.message.reply_text("Already admin.")
        except:
            await update.message.reply_text("Send valid ID.")
        return

    if ud.get('awaiting_admin_remove'):
        ud['awaiting_admin_remove'] = False
        try:
            nid = int(text)
            if remove_admin_user(nid):
                await update.message.reply_text(f"Admin {nid} removed!")
            else:
                await update.message.reply_text("Not found.")
        except:
            await update.message.reply_text("Send valid ID.")
        return
