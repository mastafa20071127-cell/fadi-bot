# -*- coding: utf-8 -*-

import telebot
import json
import os

from telebot.types import (
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    ReplyKeyboardMarkup,
    KeyboardButton
)

TOKEN = "8709748632:AAGI2l0Q3iYVWUMYzHLZ0WwNv8f4NUx5NFY"
ADMIN_ID = 8065884629  # حط ايديك هنا
CHANNEL_LINK = "https://t.me/OxfordMul7deen"

bot = telebot.TeleBot(TOKEN)

USERS_FILE = "users.json"
STATS_FILE = "stats.json"

broadcast_mode = {}


# ---------------- الملفات ---------------- #

def load_users():
    if not os.path.exists(USERS_FILE):
        with open(USERS_FILE, "w") as f:
            json.dump([], f)

    with open(USERS_FILE, "r") as f:
        return json.load(f)


def save_users(users):
    with open(USERS_FILE, "w") as f:
        json.dump(users, f)


def add_user(user_id):
    users = load_users()

    if user_id not in users:
        users.append(user_id)
        save_users(users)


def load_stats():
    if not os.path.exists(STATS_FILE):
        data = {
            "join_requests": 0
        }

        with open(STATS_FILE, "w") as f:
            json.dump(data, f)

    with open(STATS_FILE, "r") as f:
        return json.load(f)


def save_stats(data):
    with open(STATS_FILE, "w") as f:
        json.dump(data, f)


# ---------------- لوحة الادمن ---------------- #

def admin_panel():
    kb = ReplyKeyboardMarkup(resize_keyboard=True)

    kb.row(
        KeyboardButton("📢 اذاعة"),
        KeyboardButton("📊 الاحصائيات")
    )

    kb.row(
        KeyboardButton("👥 المستخدمين")
    )

    return kb


# ---------------- ترحيب ---------------- #

@bot.message_handler(commands=["start"])
def start(message):
    add_user(message.from_user.id)

    kb = InlineKeyboardMarkup()

    kb.add(
        InlineKeyboardButton(
            "قناة الكروب",
            url=CHANNEL_LINK
        )
    )

    text = """
أهلاً بكم في اكسفورد ملحدين
نورتونا جميعاً
"""

    if message.from_user.id == ADMIN_ID:
        bot.send_message(
            message.chat.id,
            text,
            reply_markup=kb
        )

        bot.send_message(
            message.chat.id,
            "لوحة التحكم",
            reply_markup=admin_panel()
        )

    else:
        bot.send_message(
            message.chat.id,
            text,
            reply_markup=kb
        )


# ---------------- طلبات الانضمام ---------------- #

@bot.chat_join_request_handler()
def join_request(request):
    stats = load_stats()
    stats["join_requests"] += 1
    save_stats(stats)

    user_id = request.from_user.id

    add_user(user_id)

    kb = InlineKeyboardMarkup()

    kb.add(
        InlineKeyboardButton(
            "قناة الكروب",
            url=CHANNEL_LINK
        )
    )

    bot.send_message(
        user_id,
        "تم إرسال طلب الانضمام",
        reply_markup=kb
    )


# ---------------- اذاعة ---------------- #

@bot.message_handler(func=lambda m: m.text == "📢 اذاعة")
def broadcast_button(message):
    if message.from_user.id != ADMIN_ID:
        return

    broadcast_mode[message.from_user.id] = True

    bot.send_message(
        message.chat.id,
        "ارسل رسالة الاذاعة الآن"
    )


@bot.message_handler(func=lambda m: True)
def all_messages(message):

    # اذاعة
    if broadcast_mode.get(message.from_user.id):

        broadcast_mode[message.from_user.id] = False

        users = load_users()

        sent = 0
        failed = 0

        for user_id in users:
            try:
                bot.send_message(
                    user_id,
                    message.text
                )

                sent += 1

            except:
                failed += 1

        bot.send_message(
            message.chat.id,
            f"""
تم انتهاء الاذاعة

تم الارسال : {sent}
فشل : {failed}
"""
        )

        return

    # الاحصائيات
    if message.text == "📊 الاحصائيات":

        if message.from_user.id != ADMIN_ID:
            return

        stats = load_stats()
        users = load_users()

        bot.send_message(
            message.chat.id,
            f"""
الاحصائيات

طلبات الانضمام : {stats['join_requests']}
عدد المستخدمين : {len(users)}
"""
        )

    # المستخدمين
    elif message.text == "👥 المستخدمين":

        if message.from_user.id != ADMIN_ID:
            return

        users = load_users()

        bot.send_message(
            message.chat.id,
            f"عدد المستخدمين : {len(users)}"
        )


print("Bot Running...")
bot.infinity_polling()
