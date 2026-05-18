import os, time, json, requests, traceback
from datetime import datetime, timedelta
import telebot

BOT_TOKEN = os.getenv("BOT_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
LOG_CHAT_ID = int(os.getenv("LOG_CHAT_ID", "0"))
MAX_WARNINGS = int(os.getenv("MAX_WARNINGS", "3"))

bot = telebot.TeleBot(BOT_TOKEN, parse_mode="HTML")

warnings = {}
spam = {}

BAD_WORDS = ["اباحي","سكس","نيك","كس","زب","طيز","شرموطة","منيوج","porn","xxx"]
BAD_LINKS = ["porn","xxx","xvideos","xnxx","onlyfans","t.me/+","telegram.me/+"]

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

def add_warn(m, reason):
    key = f"{m.chat.id}:{m.from_user.id}"
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
⚠️ التحذيرات: {w}/{MAX_WARNINGS}
🕒 الوقت: {now()}
""")

    if w >= MAX_WARNINGS:
        mute_user(m)

def mute_user(m):
    try:
        until = datetime.now() + timedelta(hours=24)
        bot.restrict_chat_member(
            m.chat.id,
            m.from_user.id,
            until_date=until,
            can_send_messages=False,
            can_send_photos=False,
            can_send_videos=False,
            can_send_audios=False,
            can_send_documents=False,
            can_send_other_messages=False,
            can_add_web_page_previews=False
        )
        bot.send_message(m.chat.id, f"🔇 تم كتم {name(m.from_user)} لمدة 24 ساعة")
    except Exception as e:
        print("MUTE ERROR:", e)

def is_spam(m):
    key = f"{m.chat.id}:{m.from_user.id}"
    t = time.time()
    spam[key] = [x for x in spam.get(key, []) if t - x < 7]
    spam[key].append(t)
    return len(spam[key]) >= 6

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
إذا تحتوي على عري، إباحية، إيحاء جنسي قوي، دم، جثث، انتحار، تفجير، تعذيب، عنف شديد أجب فقط JSON:
{"bad": true, "reason": "السبب"}
إذا سليمة:
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
            "إباحية", "اباحية", "عري", "دم", "جثة", "انتحار", "تفجير", "عنف"
        ]

        return any(x in txt for x in bad_keys)

    except Exception as e:
        print("AI ERROR:", e)
        traceback.print_exc()
        return True  # أقصى حماية: إذا فشل الفحص نحذف

@bot.message_handler(commands=["start"])
def start(m):
    bot.reply_to(m, "✅ بوت الحماية شغال\nارفعني مشرف وفعل حذف الرسائل والحظر.")

@bot.message_handler(commands=["ping"])
def ping(m):
    bot.reply_to(m, "🏓 Pong - الحماية شغالة")

@bot.message_handler(content_types=["new_chat_members"])
def new_member(m):
    for u in m.new_chat_members:
        if u.is_bot:
            delete_msg(m)
            log(f"🤖 تم منع بوت من الدخول: {name(u)}")
            try:
                bot.ban_chat_member(m.chat.id, u.id)
            except:
                pass

@bot.message_handler(content_types=["photo"])
def photo(m):
    print("PHOTO RECEIVED")

    if is_spam(m):
        delete_msg(m)
        add_warn(m, "سبام وسائط")
        return

    try:
        url = file_url(m.photo[-1].file_id)
        bad = ai_check_image(url)

        if bad:
            delete_msg(m)
            add_warn(m, "صورة مخالفة حسب فحص الذكاء")
        else:
            print("PHOTO SAFE")
    except:
        delete_msg(m)
        add_warn(m, "تعذر فحص الصورة - حذف احتياطي")

@bot.message_handler(content_types=["video"])
def video(m):
    print("VIDEO RECEIVED")
    delete_msg(m)
    add_warn(m, "الفيديوهات ممنوعة في الحماية القصوى")

@bot.message_handler(content_types=["animation"])
def gif(m):
    print("GIF RECEIVED")
    delete_msg(m)
    add_warn(m, "GIF / متحرك ممنوع في الحماية القصوى")

@bot.message_handler(content_types=["video_note"])
def video_note(m):
    print("VIDEO NOTE RECEIVED")
    delete_msg(m)
    add_warn(m, "رسالة فيديو دائرية ممنوعة")

@bot.message_handler(content_types=["sticker"])
def sticker(m):
    print("STICKER RECEIVED")

    if is_spam(m):
        delete_msg(m)
        add_warn(m, "سبام ملصقات")
        return

    try:
        if m.sticker.is_animated or m.sticker.is_video:
            delete_msg(m)
            add_warn(m, "ملصق متحرك/فيديو ممنوع")
            return

        url = file_url(m.sticker.file_id)
        bad = ai_check_image(url)

        if bad:
            delete_msg(m)
            add_warn(m, "ملصق مخالف حسب فحص الذكاء")
    except:
        delete_msg(m)
        add_warn(m, "تعذر فحص الملصق - حذف احتياطي")

@bot.message_handler(content_types=["document"])
def document(m):
    print("DOCUMENT RECEIVED")
    mime = m.document.mime_type or ""

    if mime.startswith("video/") or mime.startswith("image/"):
        delete_msg(m)
        add_warn(m, f"ملف وسائط ممنوع: {mime}")

@bot.message_handler(content_types=["text"])
def text(m):
    txt = (m.text or "").lower()

    if is_spam(m):
        delete_msg(m)
        add_warn(m, "سبام رسائل")
        return

    if any(w in txt for w in BAD_WORDS):
        delete_msg(m)
        add_warn(m, "كلمات ممنوعة")
        return

    if any(l in txt for l in BAD_LINKS):
        delete_msg(m)
        add_warn(m, "رابط ممنوع")
        return

    if m.forward_from or m.forward_from_chat:
        delete_msg(m)
        add_warn(m, "التحويل ممنوع")

print("================================")
print("Bot Started Successfully")
print("BOT_TOKEN:", "OK" if BOT_TOKEN else "MISSING")
print("OPENAI_API_KEY:", "OK" if OPENAI_API_KEY else "MISSING")
print("LOG_CHAT_ID:", LOG_CHAT_ID)
print("================================")

try:
    log("✅ بوت الحماية اشتغل بنجاح")
except:
    pass

bot.infinity_polling(skip_pending=True)
