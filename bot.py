import telebot
import os

TOKEN = os.getenv("BOT_TOKEN")

bot = telebot.TeleBot(TOKEN)

@bot.message_handler(commands=['start'])
def start(message):
    bot.reply_to(message, "✅ البوت شغال")

@bot.message_handler(commands=['ping'])
def ping(message):
    bot.reply_to(message, "🏓 Pong")

@bot.message_handler(func=lambda m: True)
def all_messages(message):
    text = message.text.lower()

    bad_words = [
        "اباحي",
        "سكس",
        "نيك",
        "زب",
        "كس"
    ]

    for word in bad_words:
        if word in text:
            try:
                bot.delete_message(message.chat.id, message.message_id)
                bot.send_message(
                    message.chat.id,
                    f"🚫 تم حذف رسالة مخالفة من {message.from_user.first_name}"
                )
            except:
                pass

print("Bot is running...")
bot.infinity_polling(skip_pending=True)
