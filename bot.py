import os, json, re, random, time
import telebot, requests
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

TOKEN = os.getenv("TOKEN", "8331884456:AAFEKz7purqoRNh42aljNjrvnfz8nFztOd4")
RAPID_API_KEY = os.getenv("RAPID_API_KEY", "78420a7cadmsh4c0b551fb859336p128e4ajsne5d9fd86d545")

OWNER_ID = 8526612004
BOT_USERNAME = "fadifvambot"
DEV_USERNAME = "aaj_t"
FORCE_CHANNEL = "@fadifva"

bot = telebot.TeleBot(TOKEN, parse_mode="HTML")
DATA_FILE = "data.json"

DEFAULT_DATA = {
    "locks": {},
    "ranks": {},
    "users": {},
    "groups": {},
    "replies": {},
    "media": {},
    "bank": {},
    "robbers": {},
    "cooldowns": {},
    "points": {},
    "notify": True,
    "settings": {
        "welcome": True,
        "replies": True,
        "games": True,
        "bank": True,
        "id_photo": True
    }
}

GAME_QUESTIONS = {
    "جمل": [("رتب الجملة: جميل / العراق / بلد", "العراق بلد جميل")],
    "كلمات": [("كلمة تبدأ بحرف م؟", "ماء")],
    "دين": [("كم عدد الصلوات المفروضة باليوم؟", "5")],
    "عربي": [("جمع كلمة كتاب؟", "كتب")],
    "اكمل": [("أكمل: العلم نور والجهل ...", "ظلام")],
    "اعلام": [("علم العراق بيه كم لون؟", "3")],
    "عواصم": [("عاصمة العراق؟", "بغداد")],
    "انقليزي": [("ترجمة book؟", "كتاب")],
    "ايموجي": [("اكتب هذا 😂", "😂")]
}

MOVIES = ["Inception", "Interstellar", "Joker", "Titanic", "Avatar", "The Matrix"]

waiting_reply = {}
quiz_games = {}

def sid(x):
    return str(x)

def save_data():
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def load_data():
    if not os.path.exists(DATA_FILE):
        with open(DATA_FILE, "w", encoding="utf-8") as f:
            json.dump(DEFAULT_DATA, f, ensure_ascii=False, indent=2)

    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            d = json.load(f)
    except:
        d = DEFAULT_DATA.copy()

    for k, v in DEFAULT_DATA.items():
        d.setdefault(k, v)

    for k, v in DEFAULT_DATA["settings"].items():
        d["settings"].setdefault(k, v)

    return d

data = load_data()

def register(message):
    if not message.from_user:
        return

    uid = sid(message.from_user.id)
    if uid not in data["users"]:
        data["users"][uid] = {
            "name": message.from_user.first_name or "",
            "username": message.from_user.username or "ماكو"
        }
        save_data()

        if data.get("notify", True):
            try:
                bot.send_message(
                    OWNER_ID,
                    f"🔔 مستخدم جديد\n"
                    f"👤 {message.from_user.first_name}\n"
                    f"🔗 @{message.from_user.username or 'ماكو'}\n"
                    f"🆔 <code>{message.from_user.id}</code>"
                )
            except:
                pass

    if message.chat.type in ["group", "supergroup"]:
        cid = sid(message.chat.id)
        if cid not in data["groups"]:
            data["groups"][cid] = {
                "title": message.chat.title or "",
                "username": message.chat.username or ""
            }
            save_data()

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

LOCK_DEFAULTS = {
    "links": False,
    "photos": False,
    "videos": False,
    "stickers": False,
    "files": False,
    "voice": False,
    "audio": False,
    "animation": False,
    "forward": False,
    "bots": False,
    "all": False
}

def locks(chat_id):
    cid = sid(chat_id)
    data["locks"].setdefault(cid, LOCK_DEFAULTS.copy())
    for k, v in LOCK_DEFAULTS.items():
        data["locks"][cid].setdefault(k, v)
    save_data()
    return data["locks"][cid]

def get_rank(chat_id, user_id):
    return data["ranks"].get(sid(chat_id), {}).get(sid(user_id))

def set_rank(chat_id, user_id, rank):
    data["ranks"].setdefault(sid(chat_id), {})
    data["ranks"][sid(chat_id)][sid(user_id)] = rank
    save_data()

def del_rank(chat_id, user_id):
    cid, uid = sid(chat_id), sid(user_id)
    if cid in data["ranks"] and uid in data["ranks"][cid]:
        del data["ranks"][cid][uid]
        save_data()

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
        bot.reply_to(message, "❌ هذا الأمر داخل الكروبات فقط")
        return False

    if not is_admin(message.chat.id, message.from_user.id):
        bot.reply_to(message, "❌ هذا الأمر للمشرفين فقط")
        return False

    return True

def target(message):
    if not message.reply_to_message:
        bot.reply_to(message, "❗ رد على رسالة الشخص")
        return None
    return message.reply_to_message.from_user

def save_media(message):
    if message.chat.type not in ["group", "supergroup"]:
        return

    if message.content_type not in ["photo", "video", "sticker", "animation", "document", "audio", "voice"]:
        return

    cid = sid(message.chat.id)
    data["media"].setdefault(cid, [])
    data["media"][cid].append({
        "message_id": message.message_id,
        "type": message.content_type
    })
    data["media"][cid] = data["media"][cid][-1000:]
    save_data()

def main_menu():
    kb = InlineKeyboardMarkup(row_width=2)
    kb.add(
        InlineKeyboardButton("🛡 الحماية", callback_data="help_protect"),
        InlineKeyboardButton("🔒 القفل والفتح", callback_data="help_locks")
    )
    kb.add(
        InlineKeyboardButton("👮‍♂️ الأدمن", callback_data="help_admin"),
        InlineKeyboardButton("🧑‍💼 المدراء", callback_data="help_managers")
    )
    kb.add(
        InlineKeyboardButton("😂 التحشيش", callback_data="help_funny"),
        InlineKeyboardButton("🎮 التسلية", callback_data="help_games")
    )
    kb.add(
        InlineKeyboardButton("⚙️ التفعيل والتعطيل", callback_data="help_enable"),
        InlineKeyboardButton("🏦 البنك", callback_data="help_bank")
    )
    kb.add(
        InlineKeyboardButton("💬 الردود", callback_data="help_replies"),
        InlineKeyboardButton("👨‍💻 المطور", callback_data="help_dev")
    )
    return kb

def start_buttons():
    kb = InlineKeyboardMarkup()
    kb.add(InlineKeyboardButton("👨‍💻 المطور", url=f"https://t.me/{DEV_USERNAME}"))
    kb.add(InlineKeyboardButton("➕ اضفني للكروب", url=f"https://t.me/{BOT_USERNAME}?startgroup=true"))
    kb.add(InlineKeyboardButton("💰 شراء بوت مشابه", url=f"https://t.me/{DEV_USERNAME}"))
    kb.add(InlineKeyboardButton("📚 الأوامر", callback_data="commands"))
    return kb

def owner_panel():
    kb = InlineKeyboardMarkup(row_width=2)
    kb.add(InlineKeyboardButton("➕ صانع الردود", callback_data="owner_add_reply"))
    kb.add(
        InlineKeyboardButton("📜 الردود", callback_data="owner_replies"),
        InlineKeyboardButton("👥 المستخدمين", callback_data="owner_users")
    )
    kb.add(
        InlineKeyboardButton("🗑 حذف رد", callback_data="owner_del_reply"),
        InlineKeyboardButton("📊 الكروبات", callback_data="owner_groups")
    )
    kb.add(InlineKeyboardButton("🔔 إشعار الدخول", callback_data="owner_notify"))
    return kb

HELP_PROTECT = """
<b>✧︙اوامر الحمايه كالاتي ...</b>
— — — — — — — — —
✧︙قفل / فتح ← الامر

✧︙قفل الروابط ، فتح الروابط
✧︙قفل الصور ، فتح الصور
✧︙قفل الفيديو ، فتح الفيديو
✧︙قفل الملصقات ، فتح الملصقات
✧︙قفل الملفات ، فتح الملفات
✧︙قفل المتحركه ، فتح المتحركه
✧︙قفل الصوت ، فتح الصوت
✧︙قفل الاغاني ، فتح الاغاني
✧︙قفل التوجيه ، فتح التوجيه
✧︙قفل البوتات ، فتح البوتات
✧︙قفل الكل ، فتح الكل
"""

HELP_LOCKS = """
<b>✧︙اوامر القفل والفتح</b>
— — — — — — — — —
✧︙الروابط
✧︙الصور
✧︙الفيديو
✧︙الملصقات
✧︙المتحركه
✧︙الملفات
✧︙الصوت
✧︙الاغاني
✧︙التوجيه
✧︙البوتات
✧︙الكل

✧︙لمعرفة الحالة:
✧︙اكتب ← الاعدادات
"""

HELP_ADMIN = """
<b>✧︙اوامر ادمنية المجموعه</b>
— — — — — — — — —
✧︙رفع مميز / تنزيل مميز
✧︙رفع ادمن / تنزيل ادمن
✧︙رفع مشرف / تنزيل مشرف
✧︙تنزيل الكل

— — — — — — — — —
✧︙بالرد:
✧︙حظر
✧︙طرد
✧︙كتم
✧︙الغاء كتم
✧︙الغاء حظر
✧︙الغاء تقييد
✧︙تقييد 5 / 10 / 30 / 60 / ساعة / يوم / اسبوع
✧︙صلاحياته

— — — — — — — — —
✧︙مسح بالرد
✧︙مسح + عدد
✧︙مسح الميديا
✧︙مسح الصور
✧︙مسح الفيديو
✧︙مسح الملصقات
✧︙مسح المتحركات
✧︙مسح الملفات
✧︙مسح الفويسات
✧︙مسح الصوتيات
"""

HELP_MANAGERS = """
<b>✧︙اوامر المدراء</b>
— — — — — — — — —
✧︙اضف رد
✧︙مسح رد
✧︙الردود
✧︙مسح الردود

✧︙تفعيل الترحيب / تعطيل الترحيب
✧︙تفعيل الردود / تعطيل الردود
✧︙تفعيل الالعاب / تعطيل الالعاب
✧︙تفعيل البنك / تعطيل البنك
✧︙تفعيل الايدي / تعطيل الايدي
"""

HELP_FUNNY = """
<b>↫ اوامـــر التحشيـــش</b>
— — — — — — — — —
✧︙نسبه الحب
✧︙نسبه الكره
✧︙نسبه الرجوله
✧︙نسبه الانوثه
✧︙نسبه الذكاء
✧︙نسبه الغباء

— — — — — — — — —
✧︙شنو رايك بهذا ← بالرد
✧︙شنو رايك بهاي ← بالرد
✧︙انطي هديه ← بالرد
✧︙بوسه ← بالرد
✧︙صيحه ← بالرد
✧︙رزله ← بالرد
"""

HELP_GAMES = """
<b>︙اوامر التسليه</b>
— — — — — — — — —
✧︙تفعيل الالعاب / تعطيل الالعاب

✧︙جمل ، كلمات ، دين ، عربي
✧︙اكمل ، اعلام ، عواصم
✧︙انقليزي ، ايموجي
✧︙احسب ، رياضيات
✧︙افلام
✧︙زواج / زوجني
✧︙طلاق
✧︙يوت + اسم الاغنية
"""

HELP_ENABLE = """
<b>✧︙اوامر التفعيل والتعطيل</b>
— — — — — — — — —
✧︙تفعيل / تعطيل الترحيب
✧︙تفعيل / تعطيل الردود
✧︙تفعيل / تعطيل الالعاب
✧︙تفعيل / تعطيل البنك
✧︙تفعيل / تعطيل الايدي

مثال:
تفعيل الترحيب
تعطيل الالعاب
"""

HELP_BANK = """
<b>✧︙اوامر البنك</b>
— — — — — — — — —
✧︙انشاء حساب بنكي
✧︙مسح حساب بنكي
✧︙حسابي
✧︙فلوسي
✧︙راتب
✧︙بخشيش
✧︙استثمار + رقم
✧︙مضاربه + رقم
✧︙حظ + رقم
✧︙زرف / سرقه ← بالرد
✧︙تحويل + رقم ← بالرد
✧︙توب الحراميه
✧︙توب الفلوس
"""

HELP_REPLIES = """
<b>✧︙اوامر الردود</b>
— — — — — — — — —
✧︙اضف رد
✧︙مسح رد
✧︙الردود
✧︙مسح الردود
"""

HELP_DEV = f"""
<b>✧︙اوامر المطور</b>
— — — — — — — — —
✧︙لوحة
✧︙الاحصائيات
✧︙المطور
✧︙سورس
✧︙شراء بوت مشابه
✧︙الاشتراك الاجباري

المطور: @{DEV_USERNAME}
القناة: {FORCE_CHANNEL}
"""

PAGES = {
    "help_protect": HELP_PROTECT,
    "help_locks": HELP_LOCKS,
    "help_admin": HELP_ADMIN,
    "help_managers": HELP_MANAGERS,
    "help_funny": HELP_FUNNY,
    "help_games": HELP_GAMES,
    "help_enable": HELP_ENABLE,
    "help_bank": HELP_BANK,
    "help_replies": HELP_REPLIES,
    "help_dev": HELP_DEV
}

def bank_user(uid):
    return data["bank"].get(sid(uid))

def create_bank(uid):
    uid = sid(uid)
    if uid in data["bank"]:
        return False
    data["bank"][uid] = {"account": random.randint(100000, 999999), "money": 1000}
    save_data()
    return True

def parse_amount(text):
    try:
        return max(1, int(text.split()[1]))
    except:
        return None

def cooldown(uid, key, seconds):
    uid = sid(uid)
    now = int(time.time())
    data["cooldowns"].setdefault(uid, {})
    last = data["cooldowns"][uid].get(key, 0)

    if now - last < seconds:
        return False, seconds - (now - last)

    data["cooldowns"][uid][key] = now
    save_data()
    return True, 0

@bot.message_handler(commands=["start"])
def start(message):
    if message.chat.type != "private":
        return

    register(message)

    if not check_sub(message):
        return

    bot.send_message(
        message.chat.id,
        "أهلاً بك في بوت فادي المطور 🌷\nاختر من الأزرار بالأسفل 👇",
        reply_markup=start_buttons()
    )

    if message.from_user.id == OWNER_ID:
        bot.send_message(message.chat.id, "⚙️ لوحة المطور", reply_markup=owner_panel())

@bot.callback_query_handler(func=lambda call: True)
def callbacks(call):
    try:
        bot.answer_callback_query(call.id)
    except:
        pass

    if call.data == "commands":
        return bot.edit_message_text(
            "📚 قائمة أوامر بوت فادي\nاختر القسم:",
            call.message.chat.id,
            call.message.message_id,
            reply_markup=main_menu()
        )

    if call.data in PAGES:
        return bot.edit_message_text(
            PAGES[call.data],
            call.message.chat.id,
            call.message.message_id,
            reply_markup=main_menu()
        )

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
            txt = "📜 الردود:\n\n" + "\n".join(data["replies"].keys()) if data["replies"] else "لا توجد ردود"
            return bot.send_message(call.message.chat.id, txt)

        if call.data == "owner_users":
            return bot.send_message(call.message.chat.id, f"👥 المستخدمين: {len(data['users'])}")

        if call.data == "owner_groups":
            return bot.send_message(call.message.chat.id, f"📊 الكروبات: {len(data['groups'])}")

        if call.data == "owner_notify":
            data["notify"] = not data.get("notify", True)
            save_data()
            return bot.send_message(call.message.chat.id, "🔔 إشعار الدخول: " + ("مفعل" if data["notify"] else "متوقف"))

@bot.message_handler(content_types=["new_chat_members"])
def welcome(message):
    register(message)

    for u in message.new_chat_members:
        if u.is_bot and locks(message.chat.id).get("bots"):
            try:
                bot.ban_chat_member(message.chat.id, u.id)
                bot.unban_chat_member(message.chat.id, u.id)
            except:
                pass
            continue

        if data["settings"].get("welcome", True):
            bot.send_message(message.chat.id, f"هلا {u.first_name} 🌷\nنورت الكروب")

@bot.message_handler(content_types=["text", "photo", "video", "sticker", "animation", "document", "audio", "voice"])
def handler(message):
    register(message)
    save_media(message)

    if message.chat.type != "private" and not check_sub(message):
        return

    text = message.text or ""
    lk = locks(message.chat.id)

    if message.chat.type != "private" and not is_admin(message.chat.id, message.from_user.id):
        delete = False

        if lk.get("all"):
            delete = True
        if lk.get("links") and text and ("http://" in text or "https://" in text or "t.me/" in text):
            delete = True
        if lk.get("photos") and message.content_type == "photo":
            delete = True
        if lk.get("videos") and message.content_type == "video":
            delete = True
        if lk.get("stickers") and message.content_type == "sticker":
            delete = True
        if lk.get("files") and message.content_type == "document":
            delete = True
        if lk.get("voice") and message.content_type == "voice":
            delete = True
        if lk.get("audio") and message.content_type == "audio":
            delete = True
        if lk.get("animation") and message.content_type == "animation":
            delete = True
        if lk.get("forward") and (message.forward_date or message.forward_from or message.forward_from_chat):
            delete = True

        if delete:
            try:
                bot.delete_message(message.chat.id, message.message_id)
            except:
                pass
            return

    if not text:
        return

    if message.from_user.id in waiting_reply:
        st = waiting_reply[message.from_user.id]

        if st["step"] == "add_word":
            waiting_reply[message.from_user.id] = {"step": "add_answer", "word": text}
            return bot.reply_to(message, "اكتب الرد:")

        if st["step"] == "add_answer":
            data["replies"][st["word"]] = text
            save_data()
            del waiting_reply[message.from_user.id]
            return bot.reply_to(message, "✅ تم إضافة الرد")

        if st["step"] == "del_word":
            data["replies"].pop(text, None)
            save_data()
            del waiting_reply[message.from_user.id]
            return bot.reply_to(message, "✅ تم حذف الرد")

    if data["settings"].get("replies", True) and text in data["replies"]:
        return bot.reply_to(message, data["replies"][text])

    if text in ["الاوامر", "الأوامر", "اوامر"]:
        return bot.reply_to(message, "📚 اختر قسم الأوامر:", reply_markup=main_menu())

    if text in ["لوحة", "لوحه"] and message.from_user.id == OWNER_ID:
        return bot.reply_to(message, "لوحة المطور", reply_markup=owner_panel())

    if text in ["الاحصائيات", "احصائيات"] and message.from_user.id == OWNER_ID:
        return bot.reply_to(message, f"👥 المستخدمين: {len(data['users'])}\n📊 الكروبات: {len(data['groups'])}")

    if text == "سورس":
        return bot.reply_to(message, "أهلاً بك في سورس فادي 🔥")

    if text == "المطور":
        return bot.reply_to(message, f"👨‍💻 المطور: @{DEV_USERNAME}")

    if text == "شراء بوت مشابه":
        return bot.reply_to(message, f"للشراء راسل: @{DEV_USERNAME}")

    if text == "الاشتراك الاجباري":
        return bot.reply_to(message, f"قناة الاشتراك: {FORCE_CHANNEL}")

    if text in ["ايدي", "ايدي بالرد"]:
        user = message.reply_to_message.from_user if text == "ايدي بالرد" and message.reply_to_message else message.from_user
        rank = get_rank(message.chat.id, user.id) or "عضو"
        username = f"@{user.username}" if user.username else "لايوجد"
        pts = data["points"].get(sid(user.id), 0)

        info = f"↶ USE = {username}\n↶ STA = {rank}\n↶ ID = <code>{user.id}</code>\n↶ PTS = {pts}"

        if data["settings"].get("id_photo", True):
            try:
                photos = bot.get_user_profile_photos(user.id, limit=1)
                if photos.total_count > 0:
                    return bot.send_photo(
                        message.chat.id,
                        photos.photos[0][-1].file_id,
                        caption=info,
                        reply_to_message_id=message.message_id
                    )
            except:
                pass

        return bot.reply_to(message, info)

    toggle_map = {
        "الترحيب": "welcome",
        "الردود": "replies",
        "الالعاب": "games",
        "البنك": "bank",
        "الايدي": "id_photo",
        "الايدي بالصوره": "id_photo"
    }

    if text.startswith("تفعيل ") or text.startswith("تعطيل "):
        if not can_admin(message):
            return

        action = "تفعيل" if text.startswith("تفعيل ") else "تعطيل"
        name = text.replace(action + " ", "").strip()

        if name not in toggle_map:
            return bot.reply_to(message, "❌ هذا الأمر غير مبرمج")

        data["settings"][toggle_map[name]] = action == "تفعيل"
        save_data()
        return bot.reply_to(message, f"✅ تم {action} {name}")

    if text.startswith("قفل ") or text.startswith("فتح "):
        if not can_admin(message):
            return

        action = "قفل" if text.startswith("قفل ") else "فتح"
        name = text.replace(action + " ", "").strip()

        mapping = {
            "الروابط": "links",
            "الرابط": "links",
            "الصور": "photos",
            "الفيديو": "videos",
            "الملصقات": "stickers",
            "الملفات": "files",
            "المتحركه": "animation",
            "المتحركات": "animation",
            "الصوت": "voice",
            "الفويسات": "voice",
            "الاغاني": "audio",
            "الصوتيات": "audio",
            "التوجيه": "forward",
            "البوتات": "bots",
            "الكل": "all"
        }

        if name not in mapping:
            return bot.reply_to(message, "❌ هذا القفل غير مبرمج")

        lk[mapping[name]] = action == "قفل"
        save_data()
        return bot.reply_to(message, f"{'🔒 تم قفل' if action == 'قفل' else '🔓 تم فتح'} {name}")

    if text == "الاعدادات":
        names = {
            "links": "الروابط",
            "photos": "الصور",
            "videos": "الفيديو",
            "stickers": "الملصقات",
            "files": "الملفات",
            "animation": "المتحركات",
            "voice": "الصوت",
            "audio": "الاغاني",
            "forward": "التوجيه",
            "bots": "البوتات",
            "all": "الكل"
        }
        out = ["⚙️ اعدادات القفل:"]
        for k, n in names.items():
            out.append(f"{'✅' if lk.get(k) else '❌'} {n}")
        return bot.reply_to(message, "\n".join(out))

    if text in ["اضف رد", "اضافة رد"]:
        if message.chat.type != "private" and not can_admin(message):
            return
        waiting_reply[message.from_user.id] = {"step": "add_word"}
        return bot.reply_to(message, "اكتب الكلمة:")

    if text == "مسح رد":
        if message.chat.type != "private" and not can_admin(message):
            return
        waiting_reply[message.from_user.id] = {"step": "del_word"}
        return bot.reply_to(message, "اكتب الكلمة:")

    if text == "الردود":
        return bot.reply_to(message, "📜 الردود:\n" + "\n".join(data["replies"].keys()) if data["replies"] else "ماكو ردود")

    if text == "مسح الردود":
        if not can_admin(message):
            return
        data["replies"] = {}
        save_data()
        return bot.reply_to(message, "✅ تم مسح الردود")

    if text in ["حظر", "طرد", "كتم", "الغاء كتم", "الغاء حظر", "الغاء الحظر", "الغاء التقييد"]:
        if not can_admin(message):
            return

        u = target(message)
        if not u:
            return

        try:
            if text == "حظر":
                bot.ban_chat_member(message.chat.id, u.id)
                return bot.reply_to(message, "✅ تم الحظر")

            if text in ["الغاء حظر", "الغاء الحظر"]:
                bot.unban_chat_member(message.chat.id, u.id)
                return bot.reply_to(message, "✅ تم إلغاء الحظر")

            if text == "طرد":
                bot.ban_chat_member(message.chat.id, u.id)
                bot.unban_chat_member(message.chat.id, u.id)
                return bot.reply_to(message, "✅ تم الطرد")

            if text == "كتم":
                bot.restrict_chat_member(message.chat.id, u.id, can_send_messages=False)
                return bot.reply_to(message, "✅ تم الكتم")

            bot.restrict_chat_member(
                message.chat.id,
                u.id,
                can_send_messages=True,
                can_send_media_messages=True,
                can_send_other_messages=True,
                can_add_web_page_previews=True
            )
            return bot.reply_to(message, "✅ تم رفع القيود")
        except:
            return bot.reply_to(message, "❌ تأكد البوت مشرف وعنده صلاحيات")

    if text.startswith("تقييد "):
        if not can_admin(message):
            return

        u = target(message)
        if not u:
            return

        val = text.replace("تقييد ", "").strip()
        secs = {
            "5": 300,
            "10": 600,
            "30": 1800,
            "60": 3600,
            "ساعة": 3600,
            "يوم": 86400,
            "اسبوع": 604800
        }.get(val)

        if not secs:
            return bot.reply_to(message, "اكتب: تقييد 5 أو 10 أو 30 أو ساعة أو يوم أو اسبوع بالرد")

        try:
            bot.restrict_chat_member(message.chat.id, u.id, until_date=int(time.time()) + secs, can_send_messages=False)
            return bot.reply_to(message, "✅ تم التقييد")
        except:
            return bot.reply_to(message, "❌ تأكد البوت مشرف")

    if text.startswith("رفع "):
        if not can_admin(message):
            return

        u = target(message)
        if not u:
            return

        rank = text.replace("رفع ", "").strip()
        allowed = ["مالك اساسي", "مالك", "منشئ", "مدير", "ادمن", "مشرف", "مميز"]

        if rank not in allowed:
            return bot.reply_to(message, "❌ هذه الرتبة غير مبرمجة")

        set_rank(message.chat.id, u.id, rank)
        return bot.reply_to(message, f"✅ تم رفعه {rank}")

    if text.startswith("تنزيل "):
        if not can_admin(message):
            return

        if text in ["تنزيل الكل", "تنزيل جميع الرتب"]:
            if message.reply_to_message:
                del_rank(message.chat.id, message.reply_to_message.from_user.id)
                return bot.reply_to(message, "✅ تم تنزيل رتبته")

            data["ranks"][sid(message.chat.id)] = {}
            save_data()
            return bot.reply_to(message, "✅ تم تنزيل كل الرتب")

        u = target(message)
        if not u:
            return

        del_rank(message.chat.id, u.id)
        return bot.reply_to(message, "✅ تم تنزيل رتبته")

    if text == "صلاحياته":
        if not message.reply_to_message:
            return bot.reply_to(message, "رد على شخص")

        try:
            m = bot.get_chat_member(message.chat.id, message.reply_to_message.from_user.id)
            def mark(x): return "ꪜ" if x else "✘"

            txt = f"""⇜ الصلاحيات ↓

1 ⇠ تغيير المعلومات ( {mark(getattr(m, 'can_change_info', False))} )
2 ⇠ حذف الرسائل ( {mark(getattr(m, 'can_delete_messages', False))} )
3 ⇠ دعوة مستخدمين ( {mark(getattr(m, 'can_invite_users', False))} )
4 ⇠ حظر وتقييد ( {mark(getattr(m, 'can_restrict_members', False))} )
5 ⇠ تثبيت الرسائل ( {mark(getattr(m, 'can_pin_messages', False))} )
6 ⇠ رفع مشرفين ( {mark(getattr(m, 'can_promote_members', False))} )
"""
            return bot.reply_to(message, txt)
        except:
            return bot.reply_to(message, "ما قدرت أجيب صلاحياته")

    if text in ["مسح بالرد", "امسح"]:
        if not can_admin(message):
            return

        if not message.reply_to_message:
            return bot.reply_to(message, "رد على رسالة")

        try:
            bot.delete_message(message.chat.id, message.reply_to_message.message_id)
            bot.delete_message(message.chat.id, message.message_id)
        except:
            bot.reply_to(message, "ما اكدر أمسح")
        return

    if text.startswith("مسح ") and len(text.split()) > 1 and text.split()[1].isdigit():
        if not can_admin(message):
            return

        count = min(int(text.split()[1]), 100)
        for i in range(count + 1):
            try:
                bot.delete_message(message.chat.id, message.message_id - i)
            except:
                pass
        return

    if text in ["مسح الميديا", "تنظيف الميديا", "مسح الصور", "مسح الفيديو", "مسح الملصقات", "مسح المتحركات", "مسح الملفات", "مسح الفويسات", "مسح الصوتيات"]:
        if not can_admin(message):
            return

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
            "مسح الميديا": ["photo", "video", "sticker", "animation", "document", "audio", "voice"],
            "تنظيف الميديا": ["photo", "video", "sticker", "animation", "document", "audio", "voice"]
        }

        allowed = type_map[text]
        deleted = 0
        remaining = []

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
        save_data()
        return bot.reply_to(message, f"✅ تم تنظيف {deleted} رسالة")

    if text in ["نسبه الحب", "نسبة الحب", "نسبه الكره", "نسبة الكره", "نسبه الرجوله", "نسبة الرجوله", "نسبه الانوثه", "نسبة الانوثه", "نسبه الذكاء", "نسبة الذكاء", "نسبه الغباء", "نسبة الغباء"]:
        return bot.reply_to(message, f"{text}: {random.randint(1, 100)}%")

    if text in ["شنو رايك بهذا", "شنو رايك بهاي"]:
        if not message.reply_to_message:
            return bot.reply_to(message, "رد على شخص")
        return bot.reply_to(message, random.choice(["كيوت 🌷", "ثقيل دم 😂", "محبوب", "غريب شوي", "فخم"]))

    if text in ["انطي هديه", "بوسه", "بوسني", "صيحه", "رزله"]:
        if not message.reply_to_message:
            return bot.reply_to(message, "رد على شخص")
        return bot.reply_to(message, random.choice(["😂 تم", "🌷 وصلت", "🔥 قوية"]))

    if text == "انشاء حساب بنكي":
        if not data["settings"].get("bank", True):
            return bot.reply_to(message, "❌ البنك معطل")
        return bot.reply_to(message, "✅ تم إنشاء حسابك البنكي ورصيدك 1000$" if create_bank(message.from_user.id) else "عندك حساب بنكي مسبقاً")

    if text == "مسح حساب بنكي":
        data["bank"].pop(sid(message.from_user.id), None)
        save_data()
        return bot.reply_to(message, "✅ تم مسح حسابك البنكي")

    if text == "حسابي":
        acc = bank_user(message.from_user.id)
        return bot.reply_to(message, f"🏦 رقم حسابك: <code>{acc['account']}</code>" if acc else "ما عندك حساب. اكتب: انشاء حساب بنكي")

    if text == "فلوسي":
        acc = bank_user(message.from_user.id)
        return bot.reply_to(message, f"💰 فلوسك: {acc['money']}$" if acc else "ما عندك حساب.")

    if text in ["راتب", "بخشيش"]:
        acc = bank_user(message.from_user.id)
        if not acc:
            return bot.reply_to(message, "سوّي حساب بنكي أولاً")

        key = "salary" if text == "راتب" else "tip"
        wait = 1200 if text == "راتب" else 600
        ok, left = cooldown(message.from_user.id, key, wait)

        if not ok:
            return bot.reply_to(message, f"انتظر {left} ثانية")

        amount = random.randint(500, 1500) if text == "راتب" else random.randint(100, 600)
        acc["money"] += amount
        save_data()
        return bot.reply_to(message, f"💵 {text}: {amount}$")

    if text in ["زرف", "سرقه"]:
        acc = bank_user(message.from_user.id)
        if not acc:
            return bot.reply_to(message, "سوّي حساب بنكي أولاً")

        if not message.reply_to_message:
            return bot.reply_to(message, "رد على شخص")

        victim = bank_user(message.reply_to_message.from_user.id)
        if not victim:
            return bot.reply_to(message, "الشخص ما عنده حساب")

        ok, left = cooldown(message.from_user.id, "rob", 600)
        if not ok:
            return bot.reply_to(message, f"انتظر {left} ثانية")

        amount = min(victim["money"], random.randint(50, 500))
        victim["money"] -= amount
        acc["money"] += amount

        data["robbers"][sid(message.from_user.id)] = data["robbers"].get(sid(message.from_user.id), 0) + 1
        save_data()
        return bot.reply_to(message, f"🦹 زرفت {amount}$")

    if text.startswith("تحويل "):
        acc = bank_user(message.from_user.id)
        amount = parse_amount(text)

        if not acc or not amount:
            return bot.reply_to(message, "اكتب: تحويل 100 بالرد")

        if not message.reply_to_message:
            return bot.reply_to(message, "رد على الشخص")

        other = bank_user(message.reply_to_message.from_user.id)
        if not other:
            return bot.reply_to(message, "الشخص ما عنده حساب")

        if acc["money"] < amount:
            return bot.reply_to(message, "فلوسك ما تكفي")

        acc["money"] -= amount
        other["money"] += amount
        save_data()
        return bot.reply_to(message, f"✅ تم تحويل {amount}$")

    if text.startswith("استثمار "):
        acc = bank_user(message.from_user.id)
        amount = parse_amount(text)

        if not acc or not amount:
            return bot.reply_to(message, "اكتب: استثمار 100")

        if acc["money"] < amount:
            return bot.reply_to(message, "فلوسك ما تكفي")

        profit = int(amount * random.randint(1, 15) / 100)
        acc["money"] += profit
        save_data()
        return bot.reply_to(message, f"📈 ربحت {profit}$")

    if text.startswith("حظ "):
        acc = bank_user(message.from_user.id)
        amount = parse_amount(text)

        if not acc or not amount:
            return bot.reply_to(message, "اكتب: حظ 100")

        if acc["money"] < amount:
            return bot.reply_to(message, "فلوسك ما تكفي")

        if random.choice([True, False]):
            acc["money"] += amount
            msg = f"🎲 فزت وربحت {amount}$"
        else:
            acc["money"] -= amount
            msg = f"🎲 خسرت {amount}$"

        save_data()
        return bot.reply_to(message, msg)

    if text.startswith("مضاربه "):
        acc = bank_user(message.from_user.id)
        amount = parse_amount(text)

        if not acc or not amount:
            return bot.reply_to(message, "اكتب: مضاربه 100")

        if acc["money"] < amount:
            return bot.reply_to(message, "فلوسك ما تكفي")

        percent = random.randint(-90, 90)
        change = int(amount * percent / 100)
        acc["money"] += change
        save_data()
        return bot.reply_to(message, f"📊 النسبة: {percent}%\nالنتيجة: {change}$")

    if text == "توب الفلوس":
        items = sorted(data["bank"].items(), key=lambda x: x[1].get("money", 0), reverse=True)[:10]
        return bot.reply_to(message, "\n".join([f"{i+1}. {data['users'].get(uid,{}).get('name',uid)} — {info['money']}$" for i, (uid, info) in enumerate(items)]) or "ماكو")

    if text == "توب الحراميه":
        items = sorted(data["robbers"].items(), key=lambda x: x[1], reverse=True)[:10]
        return bot.reply_to(message, "\n".join([f"{i+1}. {data['users'].get(uid,{}).get('name',uid)} — {c}" for i, (uid, c) in enumerate(items)]) or "ماكو")

    if text in GAME_QUESTIONS:
        if not data["settings"].get("games", True):
            return bot.reply_to(message, "❌ الألعاب معطلة")

        q, ans = random.choice(GAME_QUESTIONS[text])
        m = bot.reply_to(message, f"🎮 لعبة {text}\n\n{q}\n\nجاوب بالرد على هذه الرسالة")
        quiz_games[m.message_id] = ans.strip().lower()
        return

    if message.reply_to_message and message.reply_to_message.message_id in quiz_games:
        ans = quiz_games[message.reply_to_message.message_id]
        if text.strip().lower() == ans:
            data["points"][sid(message.from_user.id)] = data["points"].get(sid(message.from_user.id), 0) + 1
            save_data()
            quiz_games.pop(message.reply_to_message.message_id, None)
            return bot.reply_to(message, "✅ جوابك صح وربحت نقطة")
        return bot.reply_to(message, "❌ جوابك غلط")

    if text in ["رياضيات", "احسب"]:
        if not data["settings"].get("games", True):
            return bot.reply_to(message, "❌ الألعاب معطلة")

        a = random.randint(1, 20)
        b = random.randint(1, 20)
        ans = str(a + b)
        m = bot.reply_to(message, f"🧮 جاوب بالرد:\n{a} + {b} = ؟")
        quiz_games[m.message_id] = ans
        return

    if text == "افلام":
        return bot.reply_to(message, "🎬 أفلام مقترحة:\n\n" + "\n".join(random.sample(MOVIES, 4)))

    if text in ["زواج", "زوجني", "ز"]:
        return bot.reply_to(message, "💍 تم زواجك 😂")

    if text == "طلاق":
        return bot.reply_to(message, "💔 تم الطلاق")

    if text.startswith("يوت "):
        query = text.replace("يوت ", "").strip()
        if not query:
            return bot.reply_to(message, "اكتب اسم الأغنية")

        wait = bot.reply_to(message, "🔎 جاري البحث...")

        try:
            search_res = requests.get("https://www.youtube.com/results", params={"search_query": query}, timeout=20)
            ids = re.findall(r"watch\\?v=(\\S{11})", search_res.text)

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
