import os, json, re, random, time
import telebot, requests
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

TOKEN = "8516176029:AAH-s3Y0nLAdmQN_LyeR3aS-tbK1XInMINY"
RAPID_API_KEY = "7c9ef53d4dmsh8490d4a7e6aa829p1d4e17jsn2ffd61fefcb8"

OWNER_ID = 8065884629
BOT_USERNAME = "fadifvambot"
DEV_USERNAME = "fvamv"
FORCE_CHANNEL = "@fadifva"

bot = telebot.TeleBot(TOKEN, parse_mode="HTML")
DATA_FILE = "data.json"

DEFAULT_DATA = {
    "locks": {}, "ranks": {}, "muted": {}, "users": {}, "groups": {},
    "replies": {}, "media": {}, "notify": True,
    "bank": {}, "robbers": {}, "cooldowns": {},
    "settings": {"welcome": True, "replies": True, "id_photo": True, "games": True},
    "join_info": {}, "points": {}
}

waiting_reply = {}
xo_games = {}
quiz_games = {}

MOVIES = [
    "The Godfather", "Inception", "Interstellar", "Fight Club", "The Dark Knight",
    "Gladiator", "Parasite", "Se7en", "Joker", "Titanic", "Avatar", "The Matrix",
    "Forrest Gump", "The Shawshank Redemption", "Spider-Man", "John Wick"
]

GAME_QUESTIONS = {
    "جمل": [("رتب الجملة: جميل / العراق / بلد", "العراق بلد جميل")],
    "كلمات": [("كلمة تبدأ بحرف م؟", "ماء")],
    "دين": [("كم عدد الصلوات المفروضة باليوم؟", "5")],
    "عربي": [("جمع كلمة كتاب؟", "كتب")],
    "اكمل": [("أكمل: العلم نور والجهل ...", "ظلام")],
    "صور": [("شنو الشي اللي نلتقطه بالكاميرا؟", "صورة")],
    "كت تويت": [("شنو حلمك؟", "حلمي")],
    "مؤقت": [("اكتب 10", "10")],
    "اعلام": [("علم العراق بيه كم لون؟", "3")],
    "معاني": [("ما معنى الغيث؟", "المطر")],
    "تخمين": [("خمن رقم من 1 إلى 3", "2")],
    "احكام": [("حكم الصلاة واجبة لو مستحبة؟", "واجبة")],
    "ارقام": [("اكتب الرقم 7", "7")],
    "احسب": [("2+2=?", "4")],
    "رياضيات": [("2+2=?", "4")],
    "خواتم": [("خاتم يلبس باليد لو بالرجل؟", "اليد")],
    "انقليزي": [("ترجمة كلمة book؟", "كتاب")],
    "ترتيب": [("رتب: ب ا ت ك", "كتاب")],
    "انمي": [("بطل انمي ناروتو اسمه؟", "ناروتو")],
    "تركيب": [("ركب كلمة: م + ا + ء", "ماء")],
    "تفكيك": [("فكك كلمة باب", "ب ا ب")],
    "عواصم": [("عاصمة العراق؟", "بغداد")],
    "روليت": [("اكتب أحمر أو أسود", "أحمر")],
    "سيارات": [("شركة سيارة تبدأ بت؟", "تويوتا")],
    "ايموجي": [("اكتب هذا الايموجي 😂", "😂")],
    "حجره": [("حجرة ورقة مقص؟ اكتب حجرة", "حجرة")],
    "ديمون": [("اكتب ديمون", "ديمون")]
}

def save_data(d):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(d, f, ensure_ascii=False, indent=2)

def load_data():
    if not os.path.exists(DATA_FILE):
        save_data(DEFAULT_DATA)
    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            d = json.load(f)
        for k, v in DEFAULT_DATA.items():
            if k not in d:
                d[k] = v
        save_data(d)
        return d
    except:
        save_data(DEFAULT_DATA)
        return DEFAULT_DATA.copy()

data = load_data()

def sid(x):
    return str(x)

def register_user(message):
    if not message.from_user:
        return
    uid = sid(message.from_user.id)
    if uid not in data["users"]:
        data["users"][uid] = {
            "name": message.from_user.first_name or "",
            "username": message.from_user.username or "ماكو"
        }
        save_data(data)
        if data.get("notify", True):
            try:
                bot.send_message(
                    OWNER_ID,
                    f"🔔 دخول مستخدم جديد\n\n"
                    f"👤 الاسم: {message.from_user.first_name}\n"
                    f"🔗 اليوزر: @{message.from_user.username or 'ماكو'}\n"
                    f"🆔 الايدي: {message.from_user.id}"
                )
            except:
                pass

    if message.chat.type in ["group", "supergroup"]:
        cid = sid(message.chat.id)
        if cid not in data["groups"]:
            data["groups"][cid] = {"title": message.chat.title or "", "username": message.chat.username or ""}
            save_data(data)

def save_media_message(message):
    if message.chat.type not in ["group", "supergroup"]:
        return
    if message.content_type not in ["photo", "video", "sticker", "animation", "document", "audio", "voice"]:
        return
    cid = sid(message.chat.id)
    data["media"].setdefault(cid, [])
    data["media"][cid].append({"message_id": message.message_id, "type": message.content_type})
    data["media"][cid] = data["media"][cid][-1000:]
    save_data(data)

def is_subscribed(user_id):
    try:
        m = bot.get_chat_member(FORCE_CHANNEL, user_id)
        return m.status in ["member", "administrator", "creator"]
    except:
        return True

def check_sub(message):
    if message.from_user and not is_subscribed(message.from_user.id):
        kb = InlineKeyboardMarkup()
        kb.add(InlineKeyboardButton("اشترك بالقناة", url="https://t.me/fadifva"))
        bot.reply_to(message, "⚠️ لازم تشترك بقناة البوت أولاً", reply_markup=kb)
        return False
    return True

def get_locks(chat_id):
    cid = sid(chat_id)
    if cid not in data["locks"]:
        data["locks"][cid] = {
            "links": False, "photos": False, "stickers": False, "videos": False,
            "forward": False, "bots": False, "all": False, "voice": False,
            "files": False, "animation": False, "channels": False
        }
        save_data(data)
    return data["locks"][cid]

def get_rank(chat_id, user_id):
    return data["ranks"].get(sid(chat_id), {}).get(sid(user_id))

def set_rank(chat_id, user_id, rank):
    data["ranks"].setdefault(sid(chat_id), {})
    data["ranks"][sid(chat_id)][sid(user_id)] = rank
    save_data(data)

def del_rank(chat_id, user_id):
    cid, uid = sid(chat_id), sid(user_id)
    if cid in data["ranks"] and uid in data["ranks"][cid]:
        del data["ranks"][cid][uid]
        save_data(data)

def is_admin(chat_id, user_id):
    try:
        m = bot.get_chat_member(chat_id, user_id)
        if m.status in ["creator", "administrator"]:
            return True
        return get_rank(chat_id, user_id) in ["مالك اساسي", "مالك", "منشئ", "مدير", "ادمن", "مشرف"]
    except:
        return False

def can_admin(message):
    if message.chat.type == "private":
        return False
    if not is_admin(message.chat.id, message.from_user.id):
        bot.reply_to(message, "❌ هذا الأمر للمشرفين فقط")
        return False
    return True

def target_user(message):
    if not message.reply_to_message:
        bot.reply_to(message, "❗ رد على رسالة الشخص")
        return None
    return message.reply_to_message.from_user

def main_menu():
    kb = InlineKeyboardMarkup(row_width=1)
    kb.add(InlineKeyboardButton("1️⃣ أوامر الإدارة", callback_data="help_admin"))
    kb.add(InlineKeyboardButton("2️⃣ أوامر القفل والفتح", callback_data="help_locks"))
    kb.add(InlineKeyboardButton("3️⃣ أوامر الردود", callback_data="help_replies"))
    kb.add(InlineKeyboardButton("4️⃣ أوامر البنك", callback_data="help_bank"))
    kb.add(InlineKeyboardButton("5️⃣ أوامر الألعاب", callback_data="help_games"))
    kb.add(InlineKeyboardButton("6️⃣ أوامر الميوزك", callback_data="help_music"))
    kb.add(InlineKeyboardButton("⚙️ أوامر Dev", callback_data="help_dev"))
    return kb

def owner_panel():
    kb = InlineKeyboardMarkup(row_width=2)
    kb.add(InlineKeyboardButton("🟢➕ صانع الردود", callback_data="owner_add_reply"))
    kb.add(InlineKeyboardButton("🔵📜 الردود", callback_data="owner_replies"), InlineKeyboardButton("🔵👥 المستخدمين", callback_data="owner_users"))
    kb.add(InlineKeyboardButton("🔴🗑 حذف رد", callback_data="owner_del_reply"), InlineKeyboardButton("🔵📊 الكروبات", callback_data="owner_groups"))
    kb.add(InlineKeyboardButton("🟡🔔 إشعار الدخول", callback_data="owner_notify"))
    kb.add(InlineKeyboardButton("🔴 رجوع", callback_data="commands"))
    return kb

def start_buttons():
    kb = InlineKeyboardMarkup()
    kb.add(InlineKeyboardButton("👨‍💻 المطور", url=f"https://t.me/{DEV_USERNAME}"))
    kb.add(InlineKeyboardButton("➕ اضفني للكروب", url=f"https://t.me/{BOT_USERNAME}?startgroup=true"))
    kb.add(InlineKeyboardButton("💰 شراء بوت مشابه", url=f"https://t.me/{DEV_USERNAME}"))
    kb.add(InlineKeyboardButton("📚 الأوامر", callback_data="commands"))
    return kb

HELP_ADMIN = """
<b>❨ أوامر الإدارة ❩</b>

• حظر بالرد
• طرد بالرد
• كتم بالرد
• تقييد 5 / 10 / 30 / 60 / يوم / اسبوع بالرد
• الغاء الحظر بالرد
• الغاء الكتم بالرد
• الغاء التقييد بالرد
• رفع مشرف / تنزيل مشرف بالرد
• رفع ادمن / تنزيل ادمن بالرد
• رفع مميز / تنزيل مميز بالرد
• تنزيل الكل بالرد
• تنزيل الكل بدون رد
• صلاحياته بالرد

<b>❨ أوامر المسح والتنظيف ❩</b>

• امسح بالرد
• مسح بالرد
• مسح + العدد
• مسح الميديا
• مسح الصور
• مسح الفيديو
• مسح الملصقات
• مسح المتحركات
• مسح الملفات
• مسح الفويسات
• مسح الصوتيات
• مسح الردود
"""

HELP_LOCKS = """
<b>❨ أوامر القفل والفتح ❩</b>

• قفل الروابط / فتح الروابط
• قفل الصور / فتح الصور
• قفل الفيديو / فتح الفيديو
• قفل الملصقات / فتح الملصقات
• قفل الفويسات / فتح الفويسات
• قفل الملفات / فتح الملفات
• قفل المتحركات / فتح المتحركات
• قفل التوجيه / فتح التوجيه
• قفل البوتات / فتح البوتات
• قفل الكل / فتح الكل
"""

HELP_REPLIES = """
<b>❨ أوامر الردود ❩</b>

• الردود
• اضف رد
• مسح رد
• مسح الردود
"""

HELP_BANK = """
<b>✜ أوامر البنك</b>

• انشاء حساب بنكي
• مسح حساب بنكي
• حسابي
• فلوسي
• تحويل + المبلغ بالرد
• راتب
• بخشيش
• زرف بالرد
• استثمار + المبلغ
• حظ + المبلغ
• مضاربه + المبلغ
• توب الفلوس
• توب الحراميه
"""

HELP_GAMES = """
<b>❖ أوامر الألعاب</b>

• تفعيل الالعاب
• تعطيل الالعاب

• جمل
• كلمات
• دين
• عربي
• اكمل
• صور
• كت تويت
• مؤقت
• اعلام
• معاني
• تخمين
• احكام
• ارقام
• احسب
• رياضيات
• خواتم
• انقليزي
• ترتيب
• انمي
• تركيب
• تفكيك
• عواصم
• روليت
• سيارات
• ايموجي
• حجره
• ديمون
• افلام
• ز / زوجني
• طلاق
"""

HELP_MUSIC = """
<b>❨ أوامر الميوزك ❩</b>

• يوت اسم الاغنية

مثال:
• يوت فيروز سألوني الناس
"""

HELP_DEV = f"""
<b>❨ أوامر Dev ❩</b>

• سورس
• المطور
• شراء بوت مشابه
• الاوامر
• لوحة
• ايدي
• تفعيل الايدي
• تعطيل الايدي
• منو ضافني

المطور: @{DEV_USERNAME}
القناة: {FORCE_CHANNEL}
"""

def bank_user(uid):
    return data["bank"].get(sid(uid))

def create_bank(uid):
    uid = sid(uid)
    if uid in data["bank"]:
        return False
    acc = random.randint(100000, 999999)
    data["bank"][uid] = {"account": acc, "money": 1000}
    save_data(data)
    return True

def cd_ok(uid, key, seconds):
    uid, now = sid(uid), int(time.time())
    data["cooldowns"].setdefault(uid, {})
    last = data["cooldowns"][uid].get(key, 0)
    if now - last < seconds:
        return False, seconds - (now - last)
    data["cooldowns"][uid][key] = now
    save_data(data)
    return True, 0

def parse_amount(text):
    try:
        return max(1, int(text.split()[1]))
    except:
        return None

def add_point(uid):
    uid = sid(uid)
    data["points"][uid] = data["points"].get(uid, 0) + 1
    save_data(data)

def make_quiz(message, game_name):
    if not data["settings"].get("games", True):
        return bot.reply_to(message, "❌ الألعاب معطلة")

    if game_name in ["رياضيات", "احسب"]:
        a, b = random.randint(1, 20), random.randint(1, 20)
        op = random.choice(["+", "-", "*"])
        ans = str(eval(f"{a}{op}{b}"))
        q = f"🧮 جاوب بالرد على هذه الرسالة:\n{a} {op} {b} = ؟"
    else:
        q, ans = random.choice(GAME_QUESTIONS.get(game_name, [("اكتب صح", "صح")]))
        q = f"🎮 لعبة {game_name}\n\n{q}\n\nجاوب بالرد على هذه الرسالة"

    m = bot.reply_to(message, q)
    quiz_games[m.message_id] = {"answer": ans.strip().lower(), "chat": message.chat.id, "game": game_name}

@bot.message_handler(commands=["start"])
def start(message):
    if message.chat.type != "private":
        return
    register_user(message)
    if not check_sub(message):
        return
    if message.from_user.id == OWNER_ID:
        bot.send_message(message.chat.id, "⚙️ <b>لوحة تحكم المطور</b>\n\nاختر من الأزرار:", reply_markup=owner_panel())
    else:
        bot.send_message(message.chat.id, "أهلاً بك في بوت فادي المطور 🌷\nاختر من الأزرار بالأسفل 👇", reply_markup=start_buttons())

@bot.callback_query_handler(func=lambda call: True)
def callbacks(call):
    try:
        bot.answer_callback_query(call.id)
    except:
        pass

    if call.data == "commands":
        return bot.edit_message_text("📚 قائمة أوامر بوت فادي\nاختر القسم:", call.message.chat.id, call.message.message_id, reply_markup=main_menu())
    if call.data == "help_admin":
        return bot.edit_message_text(HELP_ADMIN, call.message.chat.id, call.message.message_id, reply_markup=main_menu())
    if call.data == "help_locks":
        return bot.edit_message_text(HELP_LOCKS, call.message.chat.id, call.message.message_id, reply_markup=main_menu())
    if call.data == "help_replies":
        return bot.edit_message_text(HELP_REPLIES, call.message.chat.id, call.message.message_id, reply_markup=main_menu())
    if call.data == "help_bank":
        return bot.edit_message_text(HELP_BANK, call.message.chat.id, call.message.message_id, reply_markup=main_menu())
    if call.data == "help_games":
        return bot.edit_message_text(HELP_GAMES, call.message.chat.id, call.message.message_id, reply_markup=main_menu())
    if call.data == "help_music":
        return bot.edit_message_text(HELP_MUSIC, call.message.chat.id, call.message.message_id, reply_markup=main_menu())
    if call.data == "help_dev":
        return bot.edit_message_text(HELP_DEV, call.message.chat.id, call.message.message_id, reply_markup=main_menu())

    if call.data.startswith("owner_"):
        if call.from_user.id != OWNER_ID:
            return bot.answer_callback_query(call.id, "للمطور فقط", show_alert=True)
        if call.data == "owner_add_reply":
            waiting_reply[call.from_user.id] = {"step": "add_word"}
            return bot.send_message(call.message.chat.id, "اكتب الكلمة:")
        if call.data == "owner_del_reply":
            waiting_reply[call.from_user.id] = {"step": "del_word"}
            return bot.send_message(call.message.chat.id, "اكتب الكلمة التي تريد حذفها:")
        if call.data == "owner_replies":
            txt = "📜 الردود:\n\n" + "\n".join([f"• {k}" for k in data["replies"]]) if data["replies"] else "لا توجد ردود."
            return bot.send_message(call.message.chat.id, txt)
        if call.data == "owner_users":
            return bot.send_message(call.message.chat.id, f"👥 عدد المستخدمين: {len(data['users'])}")
        if call.data == "owner_groups":
            return bot.send_message(call.message.chat.id, f"📊 عدد الكروبات: {len(data['groups'])}")
        if call.data == "owner_notify":
            data["notify"] = not data.get("notify", True)
            save_data(data)
            return bot.send_message(call.message.chat.id, "🔔 إشعار الدخول: " + ("مفعل" if data["notify"] else "متوقف"))

@bot.message_handler(content_types=["new_chat_members"])
def welcome(message):
    register_user(message)
    for u in message.new_chat_members:
        data["join_info"][sid(u.id)] = {"chat": message.chat.title or "", "by": "رابط أو إضافة", "time": int(time.time())}
        save_data(data)
        if data["settings"].get("welcome", True):
            bot.send_message(message.chat.id, f"هلا {u.first_name} 🌷\nنورت الكروب")

@bot.message_handler(content_types=["text", "photo", "video", "sticker", "animation", "document", "audio", "voice"])
def handler(message):
    register_user(message)
    save_media_message(message)

    if message.chat.type != "private" and not check_sub(message):
        return

    locks = get_locks(message.chat.id)
    text = message.text or ""

    if message.chat.type != "private" and not is_admin(message.chat.id, message.from_user.id):
        should_delete = False
        if locks.get("all"): should_delete = True
        if locks.get("links") and text and ("http://" in text or "https://" in text or "t.me/" in text): should_delete = True
        if locks.get("photos") and message.content_type == "photo": should_delete = True
        if locks.get("videos") and message.content_type == "video": should_delete = True
        if locks.get("stickers") and message.content_type == "sticker": should_delete = True
        if locks.get("voice") and message.content_type == "voice": should_delete = True
        if locks.get("files") and message.content_type == "document": should_delete = True
        if locks.get("animation") and message.content_type == "animation": should_delete = True
        if locks.get("forward") and message.forward_date: should_delete = True
        if should_delete:
            try:
                bot.delete_message(message.chat.id, message.message_id)
            except:
                pass
            return

    if not text:
        return

    if message.reply_to_message and message.reply_to_message.message_id in quiz_games:
        q = quiz_games[message.reply_to_message.message_id]
        if text.strip().lower() == q["answer"]:
            add_point(message.from_user.id)
            quiz_games.pop(message.reply_to_message.message_id, None)
            pts = data["points"].get(sid(message.from_user.id), 0)
            return bot.reply_to(message, f"✅ مبروك جوابك صح\nربحت نقطة 🎉\nنقاطك: {pts}")
        else:
            return bot.reply_to(message, "❌ جوابك غلط")

    if message.from_user.id in waiting_reply:
        st = waiting_reply[message.from_user.id]
        if st["step"] == "add_word":
            waiting_reply[message.from_user.id] = {"step": "add_answer", "word": text}
            return bot.reply_to(message, "اكتب الرد:")
        if st["step"] == "add_answer":
            data["replies"][st["word"]] = text
            save_data(data)
            del waiting_reply[message.from_user.id]
            return bot.reply_to(message, "✅ تم إضافة الرد")
        if st["step"] == "del_word":
            data["replies"].pop(text, None)
            save_data(data)
            del waiting_reply[message.from_user.id]
            return bot.reply_to(message, "✅ تم حذف الرد")

    if data["settings"].get("replies", True) and text in data["replies"]:
        return bot.reply_to(message, data["replies"][text])

    if text in ["الاوامر", "الأوامر", "اوامر"]:
        return bot.reply_to(message, "📚 اختر قسم الأوامر:", reply_markup=main_menu())
    if text in ["لوحة", "لوحه"] and message.from_user.id == OWNER_ID:
        return bot.reply_to(message, "لوحة المطور", reply_markup=owner_panel())
    if text == "سورس": return bot.reply_to(message, "أهلاً بك في سورس فادي 🔥")
    if text == "المطور": return bot.reply_to(message, f"👨‍💻 المطور: @{DEV_USERNAME}")
    if text == "شراء بوت مشابه": return bot.reply_to(message, f"للشراء راسل: @{DEV_USERNAME}")

    if text == "ايدي":
        rank = get_rank(message.chat.id, message.from_user.id) or "عضو"
        username = f"@{message.from_user.username}" if message.from_user.username else "لايوجد"
        pts = data["points"].get(sid(message.from_user.id), 0)
        txt = f"↶ USE = {username}\n↶ STA = {rank}\n↶ ID = <code>{message.from_user.id}</code>\n↶ PTS = {pts}"
        if data["settings"].get("id_photo", True):
            try:
                photos = bot.get_user_profile_photos(message.from_user.id, limit=1)
                if photos.total_count > 0:
                    return bot.send_photo(message.chat.id, photos.photos[0][-1].file_id, caption=txt, reply_to_message_id=message.message_id)
            except:
                pass
        return bot.reply_to(message, txt)

    if text == "تفعيل الايدي":
        data["settings"]["id_photo"] = True; save_data(data)
        return bot.reply_to(message, "✅ تم تفعيل الايدي بالصورة")
    if text == "تعطيل الايدي":
        data["settings"]["id_photo"] = False; save_data(data)
        return bot.reply_to(message, "✅ تم تعطيل صورة الايدي")
    if text == "منو ضافني":
        info = data["join_info"].get(sid(message.from_user.id))
        return bot.reply_to(message, f"تمت إضافتك إلى: {info.get('chat')}\nالطريقة: {info.get('by')}" if info else "ما عندي معلومات عن إضافتك.")

    if text in ["اضف رد", "اضافة رد"]:
        waiting_reply[message.from_user.id] = {"step": "add_word"}
        return bot.reply_to(message, "اكتب الكلمة:")
    if text == "مسح رد":
        waiting_reply[message.from_user.id] = {"step": "del_word"}
        return bot.reply_to(message, "اكتب الكلمة:")
    if text == "الردود":
        return bot.reply_to(message, "📜 الردود:\n" + "\n".join(data["replies"].keys()) if data["replies"] else "ماكو ردود")
    if text == "مسح الردود":
        if not can_admin(message): return
        data["replies"] = {}; save_data(data)
        return bot.reply_to(message, "✅ تم مسح الردود")

    if text in ["تفعيل الترحيب", "تعطيل الترحيب", "تفعيل الردود", "تعطيل الردود", "تفعيل الالعاب", "تعطيل الالعاب"]:
        if not can_admin(message): return
        key = "welcome" if "الترحيب" in text else "replies" if "الردود" in text else "games"
        data["settings"][key] = text.startswith("تفعيل")
        save_data(data)
        return bot.reply_to(message, "✅ تم التحديث")

    if text.startswith("قفل ") or text.startswith("فتح "):
        if not can_admin(message): return
        action = "قفل" if text.startswith("قفل ") else "فتح"
        name = text.replace(action + " ", "").strip()
        mapping = {
            "الروابط": "links", "الصور": "photos", "الفيديو": "videos",
            "الفويسات": "voice", "الملصقات": "stickers", "الملفات": "files",
            "المتحركات": "animation", "التوجيه": "forward", "البوتات": "bots", "الكل": "all"
        }
        if name not in mapping:
            return bot.reply_to(message, "هذا الأمر غير موجود")
        locks[mapping[name]] = action == "قفل"
        save_data(data)
        return bot.reply_to(message, f"{'🔒 تم قفل' if action == 'قفل' else '🔓 تم فتح'} {name}")

    if text in ["امسح", "مسح بالرد"]:
        if not can_admin(message): return
        if not message.reply_to_message: return bot.reply_to(message, "رد على رسالة")
        try:
            bot.delete_message(message.chat.id, message.reply_to_message.message_id)
            bot.delete_message(message.chat.id, message.message_id)
        except:
            bot.reply_to(message, "ما اكدر أمسح")
        return

    if text.startswith("مسح ") and text.split()[1].isdigit():
        if not can_admin(message): return
        count = min(int(text.split()[1]), 100)
        for i in range(count + 1):
            try: bot.delete_message(message.chat.id, message.message_id - i)
            except: pass
        return

    if text in ["مسح الميديا", "مسح الصور", "مسح الفيديو", "مسح الملصقات", "مسح المتحركات", "مسح الملفات", "مسح الفويسات", "مسح الصوتيات"]:
        if not can_admin(message): return
        cid = sid(message.chat.id)
        saved = data["media"].get(cid, [])
        type_map = {
            "مسح الصور": ["photo"],
            "مسح الفيديو": ["video"],
            "مسح الملصقات": ["sticker"],
            "مسح المتحركات": ["animation"],
            "مسح الملفات": ["document"],
            "مسح الفويسات": ["voice"],
            "مسح الصوتيات": ["audio"],
            "مسح الميديا": ["photo", "video", "sticker", "animation", "document", "audio", "voice"]
        }
        allowed = type_map[text]
        deleted, remaining = 0, []
        for item in saved:
            if item["type"] in allowed:
                try:
                    bot.delete_message(message.chat.id, item["message_id"])
                    deleted += 1
                except:
                    pass
            else:
                remaining.append(item)
        data["media"][cid] = remaining
        save_data(data)
        return bot.reply_to(message, f"✅ تم تنظيف {deleted} رسالة")

    if text in ["حظر", "طرد", "كتم", "الغاء الكتم", "الغاء الحظر", "الغاء التقييد"]:
        if not can_admin(message): return
        u = target_user(message)
        if not u: return
        try:
            if text == "حظر": bot.ban_chat_member(message.chat.id, u.id); bot.reply_to(message, "تم الحظر")
            elif text == "الغاء الحظر": bot.unban_chat_member(message.chat.id, u.id); bot.reply_to(message, "تم إلغاء الحظر")
            elif text == "طرد": bot.ban_chat_member(message.chat.id, u.id); bot.unban_chat_member(message.chat.id, u.id); bot.reply_to(message, "تم الطرد")
            elif text == "كتم": bot.restrict_chat_member(message.chat.id, u.id, can_send_messages=False); bot.reply_to(message, "تم الكتم")
            else:
                bot.restrict_chat_member(message.chat.id, u.id, can_send_messages=True, can_send_media_messages=True, can_send_other_messages=True, can_add_web_page_previews=True)
                bot.reply_to(message, "تم رفع القيود")
        except:
            bot.reply_to(message, "تأكد البوت مشرف")
        return

    if text.startswith("تقييد "):
        if not can_admin(message): return
        u = target_user(message)
        if not u: return
        val = text.replace("تقييد ", "").strip()
        secs = {"5":300, "10":600, "30":1800, "60":3600, "ساعة":3600, "يوم":86400, "اسبوع":604800}.get(val)
        if not secs:
            return bot.reply_to(message, "اكتب: تقييد 5 أو 10 أو 30 أو ساعة أو يوم أو اسبوع بالرد")
        try:
            until = int(time.time()) + secs
            bot.restrict_chat_member(message.chat.id, u.id, until_date=until, can_send_messages=False)
            bot.reply_to(message, "✅ تم تقييده")
        except:
            bot.reply_to(message, "تأكد البوت مشرف")
        return

    if text.startswith("رفع "):
        if not can_admin(message): return
        u = target_user(message)
        if not u: return
        rank = text.replace("رفع ", "").strip()
        allowed = ["مالك اساسي", "مالك", "منشئ", "مدير", "ادمن", "مشرف", "مميز", "هطف", "حمار", "كلب", "خروف", "بقلبي"]
        if rank not in allowed:
            return bot.reply_to(message, "هذه الرتبة غير موجودة")
        set_rank(message.chat.id, u.id, rank)
        return bot.reply_to(message, f"تم رفعه {rank}")

    if text.startswith("تنزيل "):
        if not can_admin(message): return
        if text == "تنزيل الكل":
            if message.reply_to_message:
                del_rank(message.chat.id, message.reply_to_message.from_user.id)
                return bot.reply_to(message, "تم تنزيل رتبته")
            data["ranks"][sid(message.chat.id)] = {}
            save_data(data)
            return bot.reply_to(message, "تم تنزيل كل الرتب")
        u = target_user(message)
        if not u: return
        del_rank(message.chat.id, u.id)
        return bot.reply_to(message, "تم تنزيل رتبته")

    if text == "صلاحياته":
        if not message.reply_to_message: return bot.reply_to(message, "رد على شخص")
        try:
            m = bot.get_chat_member(message.chat.id, message.reply_to_message.from_user.id)
            st = "مشرف" if m.status == "administrator" else "مالك" if m.status == "creator" else "عضو"
            def mark(x): return "ꪜ" if x else "✘"
            txt = f"""⇜ {st}
⇜ لقبه ( لايوجد )
⇜ والصلاحيات هي ↓

1 ⇠ صلاحيه تغيير المعلومات ( {mark(getattr(m, 'can_change_info', False))} )
2 ⇠ صلاحيه حذف الرسائل ( {mark(getattr(m, 'can_delete_messages', False))} )
3 ⇠ صلاحيه دعوه مستخدمين ( {mark(getattr(m, 'can_invite_users', False))} )
4 ⇠ صلاحيه حظر وتقييد المستخدمين ( {mark(getattr(m, 'can_restrict_members', False))} )
5 ⇠ صلاحيه تثبيت الرسائل ( {mark(getattr(m, 'can_pin_messages', False))} )
6 ⇠ صلاحيه رفع مشرفين اخرين ( {mark(getattr(m, 'can_promote_members', False))} )
7 ⇠ صلاحيه إدارة المكالمات ( {mark(getattr(m, 'can_manage_video_chats', False))} )
8 ⇠ صلاحيه إدارة الستوريات ( {mark(getattr(m, 'can_manage_stories', False))} )"""
            bot.reply_to(message, txt)
        except:
            bot.reply_to(message, "ما قدرت أجيب صلاحياته")
        return

    if text == "انشاء حساب بنكي":
        return bot.reply_to(message, "✅ تم إنشاء حسابك البنكي ورصيدك 1000$" if create_bank(message.from_user.id) else "عندك حساب بنكي مسبقاً")
    if text == "مسح حساب بنكي":
        data["bank"].pop(sid(message.from_user.id), None); save_data(data)
        return bot.reply_to(message, "✅ تم مسح حسابك البنكي")
    if text == "حسابي":
        acc = bank_user(message.from_user.id)
        return bot.reply_to(message, f"🏦 رقم حسابك: <code>{acc['account']}</code>" if acc else "ما عندك حساب. اكتب: انشاء حساب بنكي")
    if text == "فلوسي":
        acc = bank_user(message.from_user.id)
        return bot.reply_to(message, f"💰 فلوسك: {acc['money']}$" if acc else "ما عندك حساب.")
    if text == "راتب":
        acc = bank_user(message.from_user.id)
        if not acc: return bot.reply_to(message, "سوّي حساب بنكي أولاً")
        ok, left = cd_ok(message.from_user.id, "salary", 1200)
        if not ok: return bot.reply_to(message, f"انتظر {left} ثانية")
        amount = random.randint(500, 1500); acc["money"] += amount; save_data(data)
        return bot.reply_to(message, f"💵 راتبك: {amount}$")
    if text == "بخشيش":
        acc = bank_user(message.from_user.id)
        if not acc: return bot.reply_to(message, "سوّي حساب بنكي أولاً")
        ok, left = cd_ok(message.from_user.id, "tip", 600)
        if not ok: return bot.reply_to(message, f"انتظر {left} ثانية")
        amount = random.randint(100, 600); acc["money"] += amount; save_data(data)
        return bot.reply_to(message, f"🎁 بخشيش: {amount}$")
    if text == "زرف":
        acc = bank_user(message.from_user.id)
        if not acc: return bot.reply_to(message, "سوّي حساب بنكي أولاً")
        if not message.reply_to_message: return bot.reply_to(message, "رد على شخص حتى تزرفه")
        victim = bank_user(message.reply_to_message.from_user.id)
        if not victim: return bot.reply_to(message, "الشخص ما عنده حساب")
        ok, left = cd_ok(message.from_user.id, "rob", 600)
        if not ok: return bot.reply_to(message, f"انتظر {left} ثانية")
        amount = min(victim["money"], random.randint(50, 500))
        victim["money"] -= amount; acc["money"] += amount
        data["robbers"][sid(message.from_user.id)] = data["robbers"].get(sid(message.from_user.id), 0) + 1
        save_data(data)
        return bot.reply_to(message, f"🦹 زرفت {amount}$")
    if text.startswith("تحويل "):
        acc = bank_user(message.from_user.id)
        amount = parse_amount(text)
        if not acc or not amount: return bot.reply_to(message, "اكتب: تحويل 100 بالرد")
        if not message.reply_to_message: return bot.reply_to(message, "رد على الشخص")
        other = bank_user(message.reply_to_message.from_user.id)
        if not other: return bot.reply_to(message, "الشخص ما عنده حساب")
        if acc["money"] < amount: return bot.reply_to(message, "فلوسك ما تكفي")
        acc["money"] -= amount; other["money"] += amount; save_data(data)
        return bot.reply_to(message, f"✅ تم تحويل {amount}$")
    if text.startswith("استثمار "):
        acc = bank_user(message.from_user.id); amount = parse_amount(text)
        if not acc or not amount: return bot.reply_to(message, "اكتب: استثمار 100")
        if acc["money"] < amount: return bot.reply_to(message, "فلوسك ما تكفي")
        profit = int(amount * random.randint(1, 15) / 100)
        acc["money"] += profit; save_data(data)
        return bot.reply_to(message, f"📈 ربحت {profit}$")
    if text.startswith("حظ "):
        acc = bank_user(message.from_user.id); amount = parse_amount(text)
        if not acc or not amount: return bot.reply_to(message, "اكتب: حظ 100")
        if acc["money"] < amount: return bot.reply_to(message, "فلوسك ما تكفي")
        if random.choice([True, False]):
            acc["money"] += amount; msg = f"🎲 فزت وربحت {amount}$"
        else:
            acc["money"] -= amount; msg = f"🎲 خسرت {amount}$"
        save_data(data); return bot.reply_to(message, msg)
    if text.startswith("مضاربه "):
        acc = bank_user(message.from_user.id); amount = parse_amount(text)
        if not acc or not amount: return bot.reply_to(message, "اكتب: مضاربه 100")
        if acc["money"] < amount: return bot.reply_to(message, "فلوسك ما تكفي")
        percent = random.randint(-90, 90); change = int(amount * percent / 100)
        acc["money"] += change; save_data(data)
        return bot.reply_to(message, f"📊 النسبة: {percent}%\nالنتيجة: {change}$")
    if text == "توب الفلوس":
        items = sorted(data["bank"].items(), key=lambda x: x[1].get("money", 0), reverse=True)[:10]
        return bot.reply_to(message, "\n".join([f"{i+1}. {data['users'].get(uid,{}).get('name',uid)} — {info['money']}$" for i,(uid,info) in enumerate(items)]) or "ماكو")
    if text == "توب الحراميه":
        items = sorted(data["robbers"].items(), key=lambda x: x[1], reverse=True)[:10]
        return bot.reply_to(message, "\n".join([f"{i+1}. {data['users'].get(uid,{}).get('name',uid)} — {c}" for i,(uid,c) in enumerate(items)]) or "ماكو")

    if text in GAME_QUESTIONS or text in ["رياضيات", "احسب"]:
        return make_quiz(message, text)

    if text == "افلام":
        return bot.reply_to(message, "🎬 أفلام مقترحة:\n\n" + "\n".join(random.sample(MOVIES, min(6, len(MOVIES)))))

    if text in ["ز", "زوجني"]:
        names = ["سارة", "نور", "ملاك", "زينب", "حوراء", "فاطمة", "رقيه", "شهد"]
        return bot.reply_to(message, f"💍 تم زواجك من @{random.choice(names)}")
    if text == "طلاق":
        return bot.reply_to(message, "💔 تم الطلاق بنجاح")

    if text.startswith("يوت "):
        query = text.replace("يوت ", "").strip()
        if not query:
            return bot.reply_to(message, "اكتب اسم الأغنية")
        wait = bot.reply_to(message, "🔎 جاري البحث...")
        try:
            search_res = requests.get("https://www.youtube.com/results", params={"search_query": query}, timeout=20)
            ids = re.findall(r"watch\?v=(\S{11})", search_res.text)
            if not ids:
                return bot.reply_to(message, "ما حصلت نتيجة")
            video_url = f"https://www.youtube.com/watch?v={ids[0]}"
            headers = {
                "X-RapidAPI-Key": RAPID_API_KEY,
                "X-RapidAPI-Host": "yt-search-and-download-mp3.p.rapidapi.com"
            }
            api = requests.get(
                "https://yt-search-and-download-mp3.p.rapidapi.com/mp3",
                headers=headers,
                params={"url": video_url},
                timeout=60
            ).json()
            print("API RESPONSE:", api)
            audio_url = (
                api.get("link") or api.get("url") or api.get("audio") or
                api.get("download") or api.get("mp3") or api.get("downloadUrl") or
                api.get("download_url") or api.get("audioUrl") or api.get("result")
            )
            title = api.get("title") or query
            try:
                bot.delete_message(message.chat.id, wait.message_id)
            except:
                pass
            if not audio_url:
                return bot.reply_to(message, "ما حصلت رابط الصوت")
            return bot.send_audio(
                message.chat.id,
                audio_url,
                title=title,
                performer="Aurelius",
                caption=f"🎧 {title}",
                reply_to_message_id=message.message_id
            )
        except Exception as e:
            print("MUSIC ERROR:", e)
            return bot.reply_to(message, "صار خطأ أثناء جلب الأغنية")

print("Aurelius bot is running...")
bot.infinity_polling(skip_pending=True)
