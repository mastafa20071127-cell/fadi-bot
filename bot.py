import os
import json
import time
import traceback
import requests
import telebot
from datetime import datetime, timedelta
from dotenv import load_dotenv
from telebot.types import Message

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
LOG_CHAT_ID = int(os.getenv("LOG_CHAT_ID", "0"))

MAX_WARNINGS = int(os.getenv("MAX_WARNINGS", "3"))
STRICT_MODE = os.getenv("STRICT_MODE", "true").lower() == "true"
DELETE_VIDEOS_FIRST = os.getenv("DELETE_VIDEOS_FIRST", "true").lower() == "true"
DELETE_GIFS_FIRST = os.getenv("DELETE_GIFS_FIRST", "true").lower() == "true"

DATA_FILE = "data.json"

bot = telebot.TeleBot(BOT_TOKEN, parse_mode="HTML")


def now_text():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def load_data():
    if not os.path.exists(DATA_FILE):
        return {"warnings": {}, "spam": {}}
    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return {"warnings": {}, "spam": {}}


def save_data(data):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def user_name(user):
    name = user.first_name or "Unknown"
    if user.last_name:
        name += " " + user.last_name
    if user.username:
        name += f" (@{user.username})"
    return name


def log_admin(text):
    try:
        if LOG_CHAT_ID:
            bot.send_message(LOG_CHAT_ID, text)
    except Exception as e:
        print("LOG ERROR:", e)


def safe_delete(message):
    try:
        bot.delete_message(message.chat.id, message.message_id)
        return True
    except Exception as e:
        print("DELETE ERROR:", e)
        return False


def warn_user(message, reason):
    data = load_data()
    chat_id = str(message.chat.id)
    user_id = str(message.from_user.id)

    data.setdefault("warnings", {})
    data["warnings"].setdefault(chat_id, {})
    data["warnings"][chat_id].setdefault(user_id, 0)
    data["warnings"][chat_id][user_id] += 1

    warns = data["warnings"][chat_id][user_id]
    save_data(data)

    text = f"""
⚠️ <b>تم حذف محتوى مخالف</b>

👤 العضو: {user_name(message.from_user)}
🆔 الايدي: <code>{message.from_user.id}</code>
📌 السبب: {reason}
🔢 التحذيرات: {warns}/{MAX_WARNINGS}
🕒 الوقت: {now_text()}
"""

    try:
        bot.send_message(message.chat.id, text)
    except:
        pass

    log_admin(f"""
🚨 <b>تقرير حماية</b>

📍 الكروب: {message.chat.title}
🆔 كروب ID: <code>{message.chat.id}</code>
👤 العضو: {user_name(message.from_user)}
🆔 العضو ID: <code>{message.from_user.id}</code>
📌 السبب: {reason}
🔢 التحذيرات: {warns}/{MAX_WARNINGS}
🕒 الوقت: {now_text()}
""")

    if warns >= MAX_WARNINGS:
        mute_user(message, "وصل الحد الأعلى من التحذيرات")


def mute_user(message, reason):
    try:
        until_date = datetime.now() + timedelta(hours=24)
        bot.restrict_chat_member(
            message.chat.id,
            message.from_user.id,
            until_date=until_date,
            can_send_messages=False,
            can_send_audios=False,
            can_send_documents=False,
            can_send_photos=False,
            can_send_videos=False,
            can_send_video_notes=False,
            can_send_voice_notes=False,
            can_send_polls=False,
            can_send_other_messages=False,
            can_add_web_page_previews=False,
            can_change_info=False,
            can_invite_users=True,
            can_pin_messages=False
        )

        bot.send_message(
            message.chat.id,
            f"🔇 تم كتم {user_name(message.from_user)} لمدة 24 ساعة.\n📌 السبب: {reason}"
        )

        log_admin(f"""
🔇 <b>تم كتم عضو</b>

👤 العضو: {user_name(message.from_user)}
🆔 الايدي: <code>{message.from_user.id}</code>
📌 السبب: {reason}
🕒 الوقت: {now_text()}
""")
    except Exception as e:
        print("MUTE ERROR:", e)


def anti_spam_media(message):
    data = load_data()
    chat_id = str(message.chat.id)
    user_id = str(message.from_user.id)
    key = f"{chat_id}:{user_id}"

    data.setdefault("spam", {})
    timestamps = data["spam"].get(key, [])

    current = time.time()
    timestamps = [t for t in timestamps if current - t < 10]
    timestamps.append(current)

    data["spam"][key] = timestamps
    save_data(data)

    if len(timestamps) >= 4:
        safe_delete(message)
        warn_user(message, "إرسال وسائط بسرعة عالية / سبام")
        return True

    return False


def openai_check_image(image_url):
    try:
        headers = {
            "Authorization": f"Bearer {OPENAI_API_KEY}",
            "Content-Type": "application/json"
        }

        prompt = """
أنت نظام حماية صارم للكروبات.
افحص الصورة بدقة.

اعتبرها مخالفة إذا تحتوي على:
- عري أو إباحية أو إيحاء جنسي قوي
- دم واضح أو جروح قوية
- جثث أو موت
- انتحار أو إيذاء نفس
- تفجير أو إرهاب أو عنف دموي
- تعذيب أو مشاهد صادمة
- أطفال في سياق جنسي أو خطر

أجب فقط بصيغة JSON:
{
  "violation": true أو false,
  "reason": "سبب مختصر بالعربية",
  "confidence": رقم من 0 إلى 100
}
"""

        payload = {
            "model": "gpt-4.1-mini",
            "input": [
                {
                    "role": "user",
                    "content": [
                        {"type": "input_text", "text": prompt},
                        {"type": "input_image", "image_url": image_url}
                    ]
                }
            ]
        }

        r = requests.post(
            "https://api.openai.com/v1/responses",
            headers=headers,
            json=payload,
            timeout=20
        )

        text = r.text
        print("OPENAI:", text[:1000])

        low = text.lower()

        bad_words = [
            '"violation": true',
            '"violation":true',
            "sexual",
            "nudity",
            "porn",
            "gore",
            "blood",
            "corpse",
            "dead body",
            "self-harm",
            "suicide",
            "violence",
            "terror",
            "explosion",
            "نعم",
            "مخالفة",
            "إباحية",
            "اباحية",
            "دم",
            "جثة",
            "انتحار",
            "عنف",
            "تفجير"
        ]

        if any(w in low for w in bad_words):
            return True, "محتوى مخالف حسب فحص الذكاء"

        return False, "سليم"

    except Exception as e:
        print("OPENAI ERROR:", e)
        traceback.print_exc()

        if STRICT_MODE:
            return True, "تعذر فحص الصورة - وضع الحماية القصوى"
        return False, "تعذر الفحص"


def get_file_url(file_id):
    file_info = bot.get_file(file_id)
    return f"https://api.telegram.org/file/bot{BOT_TOKEN}/{file_info.file_path}"


@bot.message_handler(commands=["start"])
def start_cmd(message):
    bot.reply_to(
        message,
        "✅ بوت الحماية شغال.\n\nارفعني مشرف وفعل صلاحية حذف الرسائل حتى أحمي الكروب."
    )


@bot.message_handler(commands=["ping"])
def ping_cmd(message):
    bot.reply_to(message, "✅ البوت شغال ويفحص الرسائل.")


@bot.message_handler(commands=["warns"])
def warns_cmd(message):
    data = load_data()
    chat_id = str(message.chat.id)

    if not message.reply_to_message:
        bot.reply_to(message, "رد على العضو واكتب /warns")
        return

    user_id = str(message.reply_to_message.from_user.id)
    warns = data.get("warnings", {}).get(chat_id, {}).get(user_id, 0)
    bot.reply_to(message, f"🔢 تحذيرات العضو: {warns}/{MAX_WARNINGS}")


@bot.message_handler(commands=["resetwarns"])
def reset_warns_cmd(message):
    if not message.reply_to_message:
        bot.reply_to(message, "رد على العضو واكتب /resetwarns")
        return

    data = load_data()
    chat_id = str(message.chat.id)
    user_id = str(message.reply_to_message.from_user.id)

    try:
        data["warnings"][chat_id][user_id] = 0
        save_data(data)
    except:
        pass

    bot.reply_to(message, "✅ تم تصفير تحذيرات العضو.")


@bot.message_handler(content_types=["video"])
def handle_video(message: Message):
    print("RECEIVED VIDEO")
    if anti_spam_media(message):
        return

    if DELETE_VIDEOS_FIRST or STRICT_MODE:
        safe_delete(message)
        warn_user(message, "الفيديوهات ممنوعة في وضع الحماية القصوى")
        return


@bot.message_handler(content_types=["animation"])
def handle_animation(message: Message):
    print("RECEIVED GIF")
    if anti_spam_media(message):
        return

    if DELETE_GIFS_FIRST or STRICT_MODE:
        safe_delete(message)
        warn_user(message, "GIF / متحرك ممنوع في وضع الحماية القصوى")
        return


@bot.message_handler(content_types=["video_note"])
def handle_video_note(message: Message):
    print("RECEIVED VIDEO NOTE")
    if anti_spam_media(message):
        return

    safe_delete(message)
    warn_user(message, "رسالة فيديو دائرية ممنوعة في وضع الحماية القصوى")


@bot.message_handler(content_types=["sticker"])
def handle_sticker(message: Message):
    print("RECEIVED STICKER")
    if anti_spam_media(message):
        return

    try:
        if message.sticker.is_animated or message.sticker.is_video:
            safe_delete(message)
            warn_user(message, "ملصق متحرك/فيديو ممنوع")
            return

        file_url = get_file_url(message.sticker.file_id)
        bad, reason = openai_check_image(file_url)

        if bad:
            safe_delete(message)
            warn_user(message, reason)

    except Exception as e:
        print("STICKER ERROR:", e)
        if STRICT_MODE:
            safe_delete(message)
            warn_user(message, "تعذر فحص الملصق - وضع الحماية القصوى")


@bot.message_handler(content_types=["photo"])
def handle_photo(message: Message):
    print("RECEIVED PHOTO")

    if anti_spam_media(message):
        return

    try:
        file_id = message.photo[-1].file_id
        file_url = get_file_url(file_id)

        bad, reason = openai_check_image(file_url)

        if bad:
            safe_delete(message)
            warn_user(message, reason)
        else:
            print("PHOTO SAFE")

    except Exception as e:
        print("PHOTO ERROR:", e)
        traceback.print_exc()

        if STRICT_MODE:
            safe_delete(message)
            warn_user(message, "تعذر فحص الصورة - وضع الحماية القصوى")


@bot.message_handler(content_types=["document"])
def handle_document(message: Message):
    print("RECEIVED DOCUMENT")
    if anti_spam_media(message):
        return

    file_name = message.document.file_name or ""
    mime = message.document.mime_type or ""

    dangerous = [
        "image/",
        "video/",
        "application/x-msdownload",
        "application/octet-stream"
    ]

    if STRICT_MODE and any(mime.startswith(x) for x in dangerous):
        safe_delete(message)
        warn_user(message, f"ملف ممنوع في وضع الحماية القصوى: {mime}")
        return


@bot.message_handler(content_types=["text"])
def handle_text(message: Message):
    text = message.text or ""

    bad_links = [
        "porn",
        "xxx",
        "xvideos",
        "xnxx",
        "onlyfans",
        "t.me/+",
        "telegram.me/+"
    ]

    if any(x in text.lower() for x in bad_links):
        safe_delete(message)
        warn_user(message, "رابط أو كلمة ممنوعة")
        return


def startup_check():
    print("====================================")
    print("Bot Started")
    print("BOT_TOKEN:", "OK" if BOT_TOKEN else "MISSING")
    print("OPENAI_API_KEY:", "OK" if OPENAI_API_KEY else "MISSING")
    print("LOG_CHAT_ID:", LOG_CHAT_ID)
    print("STRICT_MODE:", STRICT_MODE)
    print("DELETE_VIDEOS_FIRST:", DELETE_VIDEOS_FIRST)
    print("DELETE_GIFS_FIRST:", DELETE_GIFS_FIRST)
    print("====================================")

    try:
        log_admin("✅ بوت الحماية اشتغل بنجاح.")
    except:
        pass


if __name__ == "__main__":
    startup_check()

    while True:
        try:
            bot.infinity_polling(
                skip_pending=True,
                timeout=20,
                long_polling_timeout=20,
                allowed_updates=[
                    "message",
                    "edited_message",
                    "chat_member",
                    "my_chat_member"
                ]
            )
        except Exception as e:
            print("POLLING ERROR:", e)
            traceback.print_exc()
            time.sleep(5)
