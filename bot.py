import os, time, requests, traceback
from datetime import datetime, timedelta
import telebot

BOT_TOKEN = os.getenv("BOT_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
LOG_CHAT_ID = int(os.getenv("LOG_CHAT_ID", "0"))
MAX_WARNINGS = int(os.getenv("MAX_WARNINGS", "3"))

bot = telebot.TeleBot(BOT_TOKEN, parse_mode="HTML")

warnings = {}
spam = {}

def now():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

def name(u):
    return f"{u.first_name or 'Unknown'}" + (f" @{u.username}" if u.username else "")

def log(text):
    try:
        if LOG_CHAT_ID:
            bot.send_message(LOG_CHAT_ID, text)
    except:
        pass

def delete_msg(m):
    try:
        bot.delete_message(m.chat.id, m.message_id)
        return True
    except Exception as e:
        print("DELETE ERROR:", e)
        return False

def is_spam(m):
    key = f"{m.chat.id}:{m.from_user.id}"
    t = time.time()
    spam[key] = [x for x in spam.get(key, []) if t - x < 7]
    spam[key].append(t)
    return len(spam[key]) >= 6

def smart_restrict(m, media_type):
    try:
        perms = {
            "can_send_messages": True,
            "can_send_audios": True,
            "can_send_documents": True,
            "can_send_photos": True,
            "can_send_videos": True,
            "can_send_video_notes": True,
            "can_send_voice_notes": True,
            "can_send_polls": True,
            "can_send_other_messages": True,
            "can_add_web_page_previews": True,
            "can_change_info": False,
            "can_invite_users": True,
            "can_pin_messages": False,
        }

        reason = "وسائط"

        if media_type == "photo":
            perms["can_send_photos"] = False
            reason = "الصور"

        elif media_type == "video":
            perms["can_send_videos"] = False
            perms["can_send_video_notes"] = False
            reason = "الفيديوهات"

        elif media_type == "sticker":
            perms["can_send_other_messages"] = False
            reason = "الملصقات"

        elif media_type == "gif":
            perms["can_send_other_messages"] = False
            reason = "المتحركات GIF"

        elif media_type == "document":
            perms["can_send_documents"] = False
            reason = "الملفات"

        until = datetime.now() + timedelta(hours=24)

        bot.restrict_chat_member(
            m.chat.id,
            m.from_user.id,
            until_date=until,
            **perms
        )

        bot.send_message(
            m.chat.id,
            f"🔇 تم منع {name(m.from_user)} من إرسال {reason} لمدة 24 ساعة"
        )

        log(f"""
🔇 <b>منع ذكي</b>

👤 العضو: {name(m.from_user)}
🆔 الايدي: <code>{m.from_user.id}</code>
📌 المنع: {reason}
⏱ المدة: 24 ساعة
🕒 الوقت: {now()}
""")

    except Exception as e:
        print("SMART RESTRICT ERROR:", e)

def add_warn(m, reason, media_type):
    key = f"{m.chat.id}:{m.from_user.id}:{media_type}"
    warnings[key] = warnings.get(key, 0) + 1
    w = warnings[key]

    text = f"""
🚫 <b>تم حذف محتوى مخالف</b>

👤 العضو: {name(m.from_user)}
🆔 الايدي: <code>{m.from_user.id}</code>
📌 السبب: {reason}
⚠️ التحذيرات: {w}/{MAX_WARNINGS}
🕒 الوقت: {now()}
"""

    try:
        bot.send_message(m.chat.id, text)
    except:
        pass

    log(f"""
🚨 <b>تقرير حماية</b>

📍 الكروب: {m.chat.title}
👤 العضو: {name(m.from_user)}
🆔 الايدي: <code>{m.from_user.id}</code>
📌 السبب: {reason}
📦 النوع: {media_type}
⚠️ التحذيرات: {w}/{MAX_WARNINGS}
🕒 الوقت: {now()}
""")

    if w >= MAX_WARNINGS:
        smart_restrict(m, media_type)
        warnings[key] = 0

def file_url(file_id):
    info = bot.get_file(file_id)
    return f"https://api.telegram.org/file/bot{BOT_TOKEN}/{info.file_path}"

def ai_check_image(url):
    try:
        headers = {
            "Authorization": f"Bearer {OPENAI_API_KEY}",
            "Content-Type": "application/json"
        }

        payload = {
            "model": "gpt-4.1-mini",
            "input": [{
                "role": "user",
                "content": [
                    {
                        "type": "input_text",
                        "text": """
افحص الصورة كحماية كروب.
مخالفة فقط إذا تحتوي على:
- عري أو إباحية
- إيحاء جنسي واضح
- دم أو جثث
- انتحار أو إيذاء نفس
- تفجير أو إرهاب
- تعذيب أو عنف شديد

أجب فقط JSON:
{"bad": true, "reason": "السبب"}
أو:
{"bad": false, "reason": "safe"}
"""
                    },
                    {
                        "type": "input_image",
                        "image_url": url
                    }
                ]
            }]
        }

        r = requests.post(
            "https://api.openai.com/v1/responses",
            headers=headers,
            json=payload,
            timeout=20
        )

        txt = r.text.lower()
        print("AI:", txt[:800])

        bad_keys = [
            '"bad": true',
            '"bad":true',
            "sexual", "nudity", "porn", "gore", "blood",
            "corpse", "suicide", "violence", "explosion",
            "إباحية", "اباحية", "عري", "دم", "جثة",
            "انتحار", "تفجير", "عنف", "تعذيب"
        ]

        return any(x in txt for x in bad_keys)

    except Exception as e:
        print("AI ERROR:", e)
        traceback.print_exc()
        return True

@bot.message_handler(commands=["start"])
def start(m):
    bot.reply_to(m, "✅ بوت الحماية شغال\nيفحص الصور والملصقات ويحذف الفيديوهات والمتحركات بسرعة.")

@bot.message_handler(commands=["ping"])
def ping(m):
    bot.reply_to(m, "🏓 Pong - الحماية شغالة")

@bot.message_handler(content_types=["photo"])
def photo(m):
    print("PHOTO RECEIVED")

    if is_spam(m):
        delete_msg(m)
        add_warn(m, "سبام صور", "photo")
        return

    try:
        url = file_url(m.photo[-1].file_id)
        bad = ai_check_image(url)

        if bad:
            delete_msg(m)
            add_warn(m, "صورة مخالفة حسب فحص الذكاء", "photo")
        else:
            print("PHOTO SAFE")

    except:
        delete_msg(m)
        add_warn(m, "تعذر فحص الصورة - حذف احتياطي", "photo")

@bot.message_handler(content_types=["sticker"])
def sticker(m):
    print("STICKER RECEIVED")

    if is_spam(m):
        delete_msg(m)
        add_warn(m, "سبام ملصقات", "sticker")
        return

    try:
        if m.sticker.is_animated or m.sticker.is_video:
            delete_msg(m)
            add_warn(m, "ملصق متحرك/فيديو ممنوع", "sticker")
            return

        url = file_url(m.sticker.file_id)
        bad = ai_check_image(url)

        if bad:
            delete_msg(m)
            add_warn(m, "ملصق مخالف حسب فحص الذكاء", "sticker")
        else:
            print("STICKER SAFE")

    except:
        delete_msg(m)
        add_warn(m, "تعذر فحص الملصق - حذف احتياطي", "sticker")

@bot.message_handler(content_types=["video"])
def video(m):
    print("VIDEO RECEIVED")
    delete_msg(m)
    add_warn(m, "الفيديوهات ممنوعة في الحماية القصوى", "video")

@bot.message_handler(content_types=["animation"])
def gif(m):
    print("GIF RECEIVED")
    delete_msg(m)
    add_warn(m, "GIF / متحرك ممنوع في الحماية القصوى", "gif")

@bot.message_handler(content_types=["video_note"])
def video_note(m):
    print("VIDEO NOTE RECEIVED")
    delete_msg(m)
    add_warn(m, "رسالة فيديو دائرية ممنوعة", "video")

@bot.message_handler(content_types=["document"])
def document(m):
    print("DOCUMENT RECEIVED")

    mime = m.document.mime_type or ""

    if mime.startswith("image/"):
        delete_msg(m)
        add_warn(m, f"ملف صورة ممنوع: {mime}", "document")
        return

    if mime.startswith("video/"):
        delete_msg(m)
        add_warn(m, f"ملف فيديو ممنوع: {mime}", "document")
        return

@bot.message_handler(content_types=["new_chat_members"])
def new_member(m):
    for u in m.new_chat_members:
        if u.is_bot:
            delete_msg(m)
            try:
                bot.ban_chat_member(m.chat.id, u.id)
            except:
                pass

@bot.message_handler(content_types=["text"])
def text(m):
    # لا يحذف كلمات نهائياً
    pass

print("================================")
print("Bot Started Successfully")
print("BOT_TOKEN:", "OK" if BOT_TOKEN else "MISSING")
print("OPENAI_API_KEY:", "OK" if OPENAI_API_KEY else "MISSING")
print("LOG_CHAT_ID:", LOG_CHAT_ID)
print("================================")

try:
    log("✅ بوت الحماية الذكي اشتغل بنجاح")
except:
    pass

bot.infinity_polling(skip_pending=True)
