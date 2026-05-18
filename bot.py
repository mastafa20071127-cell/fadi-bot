import os
import json
import time
import base64
import asyncio
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional

import aiohttp
from dotenv import load_dotenv
from aiogram import Bot, Dispatcher, F
from aiogram.filters import Command
from aiogram.types import Message
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN", "").strip()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "").strip()
LOG_CHAT_ID = int(os.getenv("LOG_CHAT_ID", "0"))
MAX_WARNINGS = int(os.getenv("MAX_WARNINGS", "3"))
STRICT_MODE = os.getenv("STRICT_MODE", "true").lower() == "true"
DELETE_VIDEOS_FIRST = os.getenv("DELETE_VIDEOS_FIRST", "true").lower() == "true"
DELETE_GIFS_FIRST = os.getenv("DELETE_GIFS_FIRST", "true").lower() == "true"
MUTE_MINUTES = int(os.getenv("MUTE_MINUTES", "1440"))
MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")

if not BOT_TOKEN:
    raise RuntimeError("BOT_TOKEN missing in .env")
if not OPENAI_API_KEY:
    raise RuntimeError("OPENAI_API_KEY missing in .env")
if not LOG_CHAT_ID:
    raise RuntimeError("LOG_CHAT_ID missing in .env")

DATA_FILE = Path("warnings.json")
TEMP_DIR = Path("temp")
TEMP_DIR.mkdir(exist_ok=True)

bot = Bot(BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
dp = Dispatcher()


def load_data() -> Dict[str, Any]:
    if DATA_FILE.exists():
        try:
            return json.loads(DATA_FILE.read_text(encoding="utf-8"))
        except Exception:
            return {}
    return {}


def save_data(data: Dict[str, Any]) -> None:
    DATA_FILE.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def user_name(m: Message) -> str:
    u = m.from_user
    if not u:
        return "Unknown"
    name = (u.full_name or "Unknown").replace("<", "").replace(">", "")
    if u.username:
        name += f" (@{u.username})"
    return name


def now_text() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


async def safe_delete(message: Message) -> bool:
    try:
        await message.delete()
        return True
    except Exception:
        return False


async def warn_and_maybe_mute(message: Message, reason: str) -> int:
    data = load_data()
    uid = str(message.from_user.id)
    gid = str(message.chat.id)
    data.setdefault(gid, {})
    data[gid][uid] = data[gid].get(uid, 0) + 1
    warns = data[gid][uid]
    save_data(data)

    try:
        await message.answer(
            f"⚠️ <b>تم حذف محتوى مخالف</b>\n"
            f"👤 العضو: {user_name(message)}\n"
            f"🚫 السبب: {reason}\n"
            f"📌 التحذيرات: {warns}/{MAX_WARNINGS}"
        )
    except Exception:
        pass

    if warns >= MAX_WARNINGS:
        try:
            until = int(time.time()) + MUTE_MINUTES * 60
            await bot.restrict_chat_member(
                chat_id=message.chat.id,
                user_id=message.from_user.id,
                permissions={
                    "can_send_messages": False,
                    "can_send_audios": False,
                    "can_send_documents": False,
                    "can_send_photos": False,
                    "can_send_videos": False,
                    "can_send_video_notes": False,
                    "can_send_voice_notes": False,
                    "can_send_polls": False,
                    "can_send_other_messages": False,
                    "can_add_web_page_previews": False,
                    "can_change_info": False,
                    "can_invite_users": False,
                    "can_pin_messages": False,
                    "can_manage_topics": False,
                },
                until_date=until,
            )
            await message.answer(f"🔇 تم كتم العضو بسبب تكرار المخالفات {MAX_WARNINGS}/{MAX_WARNINGS}")
        except Exception:
            pass
    return warns


async def send_log(message: Message, media_type: str, reason: str, ai_result: Optional[Dict[str, Any]] = None, deleted: bool = True):
    details = ""
    if ai_result:
        details = f"\n🧠 النتيجة: <code>{json.dumps(ai_result, ensure_ascii=False)[:900]}</code>"

    text = (
        f"🚫 <b>تقرير حماية</b>\n\n"
        f"👤 الاسم: {user_name(message)}\n"
        f"🆔 الآيدي: <code>{message.from_user.id if message.from_user else 'unknown'}</code>\n"
        f"📍 الكروب: {message.chat.title or message.chat.id}\n"
        f"📌 النوع: {media_type}\n"
        f"🛡️ الإجراء: {'حذف' if deleted else 'مراقبة'}\n"
        f"🚨 السبب: {reason}\n"
        f"🕒 الوقت: {now_text()}"
        f"{details}"
    )
    try:
        await bot.send_message(LOG_CHAT_ID, text)
    except Exception:
        pass


async def download_file(file_id: str, suffix: str) -> Path:
    tg_file = await bot.get_file(file_id)
    out = TEMP_DIR / f"{file_id}_{int(time.time()*1000)}{suffix}"
    await bot.download_file(tg_file.file_path, destination=out)
    return out


def image_to_data_url(path: Path) -> str:
    raw = path.read_bytes()
    b64 = base64.b64encode(raw).decode("utf-8")
    # Telegram stickers may be webp; OpenAI supports common image formats. PNG/JPEG/WebP usually OK.
    ext = path.suffix.lower().replace(".", "") or "jpeg"
    mime = "jpeg" if ext in ["jpg", "jpeg"] else ext
    return f"data:image/{mime};base64,{b64}"


async def check_image_ai(path: Path) -> Dict[str, Any]:
    data_url = image_to_data_url(path)
    prompt = (
        "You are a strict Telegram group safety moderator. Analyze this image. "
        "Return ONLY valid compact JSON with keys: unsafe(boolean), categories(array), severity(0-10), reason_ar(string). "
        "Mark unsafe=true for nudity, sexual content, porn, graphic violence, blood/gore, corpse, suicide/self-harm, explosion/terror, torture, extreme injury, or hateful extremist imagery. "
        "If uncertain but likely dangerous, mark unsafe=true. Arabic reason only in reason_ar."
    )
    payload = {
        "model": MODEL,
        "messages": [{
            "role": "user",
            "content": [
                {"type": "text", "text": prompt},
                {"type": "image_url", "image_url": {"url": data_url}},
            ],
        }],
        "temperature": 0,
        "max_tokens": 220,
    }
    headers = {
        "Authorization": f"Bearer {OPENAI_API_KEY}",
        "Content-Type": "application/json",
    }
    async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=20)) as session:
        async with session.post("https://api.openai.com/v1/chat/completions", json=payload, headers=headers) as resp:
            text = await resp.text()
            if resp.status >= 400:
                return {"unsafe": STRICT_MODE, "categories": ["api_error"], "severity": 10 if STRICT_MODE else 0, "reason_ar": f"خطأ فحص الذكاء: {resp.status}"}
            try:
                content = json.loads(text)["choices"][0]["message"]["content"].strip()
                content = content.replace("```json", "").replace("```", "").strip()
                return json.loads(content)
            except Exception:
                return {"unsafe": STRICT_MODE, "categories": ["parse_error"], "severity": 10 if STRICT_MODE else 0, "reason_ar": "تعذر قراءة نتيجة الفحص"}


async def process_image_message(message: Message, file_id: str, suffix: str, media_type: str):
    path = None
    try:
        path = await download_file(file_id, suffix)
        result = await check_image_ai(path)
        unsafe = bool(result.get("unsafe")) or int(result.get("severity", 0)) >= 7
        reason = result.get("reason_ar") or "محتوى مخالف"
        if unsafe:
            deleted = await safe_delete(message)
            await warn_and_maybe_mute(message, reason)
            await send_log(message, media_type, reason, result, deleted)
    except Exception as e:
        # strict mode: if checking fails, delete media to protect the group
        if STRICT_MODE:
            deleted = await safe_delete(message)
            reason = f"فشل الفحص وتم الحذف للحماية: {type(e).__name__}"
            await warn_and_maybe_mute(message, reason)
            await send_log(message, media_type, reason, {"error": str(e)[:300]}, deleted)
    finally:
        if path and path.exists():
            try:
                path.unlink()
            except Exception:
                pass


@dp.message(Command("start"))
async def start_cmd(message: Message):
    await message.answer(
        "🛡️ بوت الحماية شغال\n\n"
        "يفحص الصور والملصقات الثابتة بالذكاء.\n"
        "ويحذف الفيديو/GIF/الملصقات المتحركة فوراً بأقصى حماية."
    )


@dp.message(Command("warns"))
async def warns_cmd(message: Message):
    data = load_data()
    gid = str(message.chat.id)
    if not data.get(gid):
        await message.answer("ماكو تحذيرات بهذا الكروب.")
        return
    lines = ["📌 تحذيرات الكروب:"]
    for uid, count in sorted(data[gid].items(), key=lambda x: x[1], reverse=True)[:20]:
        lines.append(f"<code>{uid}</code> : {count}")
    await message.answer("\n".join(lines))


@dp.message(Command("resetwarns"))
async def reset_warns_cmd(message: Message):
    member = await bot.get_chat_member(message.chat.id, message.from_user.id)
    if member.status not in ["creator", "administrator"]:
        return
    data = load_data()
    data[str(message.chat.id)] = {}
    save_data(data)
    await message.answer("✅ تم تصفير التحذيرات لهذا الكروب.")


@dp.message(F.photo)
async def on_photo(message: Message):
    # largest photo version
    photo = message.photo[-1]
    asyncio.create_task(process_image_message(message, photo.file_id, ".jpg", "صورة"))


@dp.message(F.sticker)
async def on_sticker(message: Message):
    st = message.sticker
    if st.is_animated or st.is_video:
        deleted = await safe_delete(message)
        reason = "ملصق متحرك/فيديو محذوف فوراً بأقصى حماية"
        await warn_and_maybe_mute(message, reason)
        await send_log(message, "ملصق متحرك", reason, None, deleted)
        return
    asyncio.create_task(process_image_message(message, st.file_id, ".webp", "ملصق ثابت"))


@dp.message(F.video)
async def on_video(message: Message):
    if DELETE_VIDEOS_FIRST:
        deleted = await safe_delete(message)
        reason = "الفيديوهات ممنوعة ومحذوفة فوراً بأقصى حماية"
        await warn_and_maybe_mute(message, reason)
        await send_log(message, "فيديو", reason, None, deleted)


@dp.message(F.animation)
async def on_animation(message: Message):
    if DELETE_GIFS_FIRST:
        deleted = await safe_delete(message)
        reason = "GIF/متحرك ممنوع ومحذوف فوراً بأقصى حماية"
        await warn_and_maybe_mute(message, reason)
        await send_log(message, "GIF/متحرك", reason, None, deleted)


@dp.message(F.video_note)
async def on_video_note(message: Message):
    deleted = await safe_delete(message)
    reason = "رسالة فيديو دائرية محذوفة فوراً بأقصى حماية"
    await warn_and_maybe_mute(message, reason)
    await send_log(message, "Video note", reason, None, deleted)


async def main():
    print("Protection bot started...")
    await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())


if __name__ == "__main__":
    asyncio.run(main())
