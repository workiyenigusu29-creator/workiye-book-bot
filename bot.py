import os
import threading
from flask import Flask
import telebot
from telebot import types

BOT_TOKEN = os.environ.get("BOT_TOKEN") or "9000383726:AAEjB5oyItxLQnyidModpHop4H66IMhlL3s"
ADMIN_IDS = {741140918}

BOOKS = {
    "book_1": {
        "title": "ሀገር በቀል እፅዋትና የህክምና ጥቅማቸው",
        "price": "100 ብር",
        "file": "medcine book.pdf",
    },
    "book_2": {
        "title": "የትምህርት ሙያዊ ብቃትና ተግባራዊ አፈጻጸም",
        "price": "150 ብር",
        "file": "የትምህርት ሙያዊ ብቃት.pdf",
    },
    "book_3": {
        "title": "Professional competence and practical performance in education",
        "price": "150 ብር",
        "file": "Educational competency.pdf",
    },
    "book_4": {
        "title": "የመሪነት ጥበብ",
        "price": "200 ብር",
        "file": "የመሪነት ጥበብ.pdf",
    },
    "book_5": {
        "title": "የስኬት ምስጢር",
        "price": "200 ብር",
        "file": "የስኬት ምስጢር.pdf",
    },
    "book_6": {
        "title": "የሲቭል ሰርቭስ የብቃት ምዘና ጥያቄዎች 457 በላይ",
        "price": "200 ብር",
        "file": "civil service exam.pdf",
    },
}

# Stores each buyer's currently selected book: {buyer_user_id: book_code}
user_selected_book = {}

bot = telebot.TeleBot(BOT_TOKEN)
app = Flask(__name__)


@app.route("/")
def home():
    return "Bot is running!"


def is_admin(user_id: int) -> bool:
    return user_id in ADMIN_IDS


def build_book_keyboard():
    markup = types.InlineKeyboardMarkup(row_width=1)
    for code, info in BOOKS.items():
        btn = types.InlineKeyboardButton(
            text=f"📖 {info['title']} — {info['price']}",
            callback_data=f"select_{code}",
        )
        markup.add(btn)
    return markup


@bot.message_handler(commands=["start"])
def handle_start(message):
    user_id = message.from_user.id

    if is_admin(user_id):
        bot.reply_to(
            message,
            f"ሰላም አድሚን ወርቅዬ (ID: `{user_id}`)! 👑\n\n"
            "የገዥዎች የክፍያ ደረሰኝ ሲመጣ ከስር ባለው **✅ አጽድቅና መጽሐፍ ላክ** ቁልፍ በቀጥታ ማጽደቅ ይችላሉ፣ ወይም `/sendbook <user_id> <book_code>` መጠቀም ይችላሉ።",
            parse_mode="Markdown",
        )
        return

    bot.send_message(
        message.chat.id,
        "ሰላም! ወደ የመጽሐፍ መሸጫ ቦት (@Lisanwork12_Bot) እንኳን ደህና መጡ። 📚\n\n"
        "እባክዎ መጀመሪያ የሚፈልጉትን መጽሐፍ ከታች ይምረጡ፡-",
        reply_markup=build_book_keyboard(),
    )


@bot.callback_query_handler(func=lambda call: call.data.startswith("select_"))
def handle_book_selection(call):
    user_id = call.from_user.id
    book_code = call.data.replace("select_", "", 1)

    if book_code not in BOOKS:
        bot.answer_callback_query(call.id, "መጽሐፉ አልተገኘም።")
        return

    user_selected_book[user_id] = book_code
    book = BOOKS[book_code]

    bot.answer_callback_query(call.id, f"{book['title']} ተመርጧል")
    bot.send_message(
        call.message.chat.id,
        f"✅ የመረጡት መጽሐፍ፡ **{book['title']}**\n"
        f"💰 የሚከፈል ዋጋ፡ **{book['price']}**\n\n"
        "💳 **ክፍያ የሚፈጽሙባቸው አካውንቶች፡**\n"
        "🟢 Telebirr: `0940277822` (Workiye Nigusu)\n"
        "🏦 CBE: `1000307290247`\n\n"
        "📸 ክፍያውን ከፈጸሙ በኋላ **የደረሰኝ ፎቶ (Screenshot)** በዚህ ቻት ይላኩ። አድሚኑ ሲያረጋግጥ መጽሐፉ በPDF ይላክልዎታል።",
        parse_mode="Markdown",
    )


@bot.callback_query_handler(func=lambda call: call.data.startswith("approve_"))
def handle_admin_approval(call):
    if not is_admin(call.from_user.id):
        bot.answer_callback_query(call.id, "ለአድሚን ብቻ ነው።", show_alert=True)
        return

    # Format: approve_<buyer_id>_<book_code>
    payload = call.data.replace("approve_", "", 1)
    parts = payload.split("_", 1)
    if len(parts) != 2:
        bot.answer_callback_query(call.id, "የትዕዛዝ መረጃ ስህተት አለው።")
        return

    try:
        buyer_id = int(parts[0])
    except ValueError:
        bot.answer_callback_query(call.id, "የገዥ ID ስህተት አለው።")
        return

    book_code = parts[1]
    if book_code not in BOOKS:
        bot.answer_callback_query(call.id, "መጽሐፉ አልተገኘም።")
        return

    book = BOOKS[book_code]
    file_path = book["file"]

    if not os.path.exists(file_path):
        bot.answer_callback_query(call.id, f"ፋይሉ {file_path} አልተገኘም።", show_alert=True)
        bot.send_message(call.from_user.id, f"⚠️ ፋይሉ `{file_path}` በሰርቨሩ ላይ አልተገኘም።", parse_mode="Markdown")
        return

    try:
        with open(file_path, "rb") as pdf_file:
            bot.send_document(
                buyer_id,
                pdf_file,
                caption=(
                    f"✅ ክፍያዎ ተረጋግጧል!\n"
                    f"📖 መጽሐፍ፡ {book['title']}\n"
                    f"አዘጋጅ፡ ወርቅዬ ንጉሱ ቸሩ\n"
                    f"መልካም ንባብ!"
                ),
            )
        bot.answer_callback_query(call.id, "መጽሐፉ ተልኳል! ✅")
        bot.edit_message_reply_markup(call.message.chat.id, call.message.message_id, reply_markup=None)
        bot.send_message(
            call.from_user.id,
            f"✅ ተጸድቋል! «{book['title']}» ለገዥ ID `{buyer_id}` ተልኳል።",
            parse_mode="Markdown",
        )
    except Exception as e:
        bot.answer_callback_query(call.id, "መላክ አልተቻለም።", show_alert=True)
        bot.send_message(call.from_user.id, f"❌ መጽሐፉን መላክ አልተቻለም፡ {e}")


@bot.message_handler(commands=["sendbook"])
def handle_sendbook(message):
    if not is_admin(message.from_user.id):
        bot.reply_to(message, "⛔ ይህ ትዕዛዝ ለአድሚን ብቻ የተፈቀደ ነው።")
        return

    parts = message.text.split()
    if len(parts) < 3:
        bot.reply_to(message, "አጠቃቀም፡ `/sendbook <user_id> <book_code>`", parse_mode="Markdown")
        return

    try:
        target_user_id = int(parts[1])
    except ValueError:
        bot.reply_to(message, "❌ ትክክለኛ የገዥ User ID (ቁጥር) ያስገቡ።")
        return

    book_code = parts[2].lower()
    if book_code not in BOOKS:
        bot.reply_to(message, f"❌ የመጽሐፍ ኮድ `{book_code}` አልተገኘም።", parse_mode="Markdown")
        return

    book = BOOKS[book_code]
    file_path = book["file"]
    if not os.path.exists(file_path):
        bot.reply_to(message, f"⚠️ ፋይሉ `{file_path}` በሰርቨሩ ላይ አልተገኘም።", parse_mode="Markdown")
        return

    try:
        with open(file_path, "rb") as pdf_file:
            bot.send_document(
                target_user_id,
                pdf_file,
                caption=f"✅ ክፍያዎ ተረጋግጧል!\n📖 መጽሐፍ፡ {book['title']}\nአዘጋጅ፡ ወርቅዬ ንጉሱ ቸሩ\nመልካም ንባብ!",
            )
        bot.reply_to(message, f"✅ «{book['title']}» ወደ User ID `{target_user_id}` ተልኳል።", parse_mode="Markdown")
    except Exception as e:
        bot.reply_to(message, f"❌ መጽሐፉን መላክ አልተቻለም፡ {e}")


@bot.message_handler(content_types=["photo", "document", "text"])
def handle_user_messages(message):
    user_id = message.from_user.id
    if is_admin(user_id):
        return

    # Ignore plain text commands not caught above if user hasn't selected a book yet
    selected_code = user_selected_book.get(user_id)
    if not selected_code and message.content_type == "text":
        bot.send_message(
            message.chat.id,
            "እባክዎ መጀመሪያ የሚፈልጉትን መጽሐፍ ይምረጡ፡-",
            reply_markup=build_book_keyboard(),
        )
        return

    book = BOOKS.get(selected_code, {
        "title": "ያልተመረጠ መጽሐፍ (ገዥው በጽሑፍ ሊገልጽ ይችላል)",
        "price": "—",
    })
    effective_code = selected_code or "book_1"

    username = f"@{message.from_user.username}" if message.from_user.username else "የለውም"
    full_name = message.from_user.first_name or "ገዥ"

    approve_markup = types.InlineKeyboardMarkup()
    approve_markup.add(
        types.InlineKeyboardButton(
            text=f"✅ አጽድቅና መጽሐፍ ላክ ({effective_code})",
            callback_data=f"approve_{user_id}_{effective_code}",
        )
    )

    for admin_id in ADMIN_IDS:
        try:
            bot.send_message(
                admin_id,
                f"📩 **አዲስ የክፍያ ማረጋገጫ ጥያቄ**\n"
                f"👤 ገዥ፡ {full_name} ({username})\n"
                f"🆔 User ID: `{user_id}`\n"
                f"📚 የመረጠው መጽሐፍ፡ {book['title']} ({book['price']})",
                parse_mode="Markdown",
                reply_markup=approve_markup,
            )
            bot.forward_message(admin_id, message.chat.id, message.message_id)
        except Exception as e:
            print(f"Admin notification error: {e}")

    bot.reply_to(
        message,
        "✅ የክፍያ ማረጋገጫዎ ለአድሚኑ ደርሷል። ክፍያው ሲረጋገጥ መጽሐፉ በዚህ ቻት ይላክልዎታል።",
    )


def run_polling():
    bot.infinity_polling(skip_pending=True)


if __name__ == "__main__":
    threading.Thread(target=run_polling, daemon=True).start()
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
