import os
import threading
from flask import Flask
import telebot
from telebot import types

BOT_TOKEN = (
    os.environ.get("BOT_TOKEN")
    or "9000383726:AAEjB5oyItxLQnyidModpHop4H66IMhlL3s"
).strip()
ADMIN_IDS = {741140918}

BOOKS = {
    "book_1": {
        "title": "ሀገር በቀል እፅዋትና የህክምና ጥቅማቸው",
        "price": "100 ብር",
        "file": "medcine book.pdf.pdf",
    },
    "book_2": {
        "title": "የትምህርት ሙያዊ ብቃትና ተግባራዊ አፈጻጸም",
        "price": "150 ብር",
        "file": "የትምህርት ሙያዊ ብቃት.pdf.pdf",
    },
    "book_3": {
        "title": "Professional competence and practical performance in education",
        "price": "150 ብር",
        "file": "Educational competency.pdf.pdf",
    },
    "book_4": {
        "title": "የመሪነት ጥበብ",
        "price": "200 ብር",
        "file": "የመሪነት ጥበብ.pdf.pdf",
    },
    "book_5": {
        "title": "የስኬት ምስጢር",
        "price": "200 ብር",
        "file": "የስኬት ምስጢር.pdf.pdf",
    },
    "book_6": {
        "title": "የሲቭል ሰርቭስ የብቃት ምዘና ጥያቄዎች 457 በላይ",
        "price": "200 ብር",
        "file": "civil service exam.pdf.pdf",
    },
}

user_choice = {}

app = Flask(__name__)
bot = telebot.TeleBot(BOT_TOKEN)


@app.route("/")
@app.route("/health")
def home():
    return "Bot is running!", 200


def is_admin(user_id: int) -> bool:
    return user_id in ADMIN_IDS


def books_text_and_keyboard():
    lines = ["📚 **የመጽሐፍት ዝርዝር እና ዋጋ (Book List & Prices):**\n"]
    markup = types.InlineKeyboardMarkup(row_width=1)

    for idx, (code, info) in enumerate(BOOKS.items(), start=1):
        lines.append(f"{idx}. {info['title']} — **{info['price']}**")
        markup.add(
            types.InlineKeyboardButton(
                text=f"📖 {info['title']} ({info['price']})",
                callback_data=f"pick_{code}",
            )
        )

    lines.append(
        "\n💳 **የክፍያ አካውንቶች፡**\n"
        "🟢 Telebirr: `0940277822` (Workiye Nigusu)\n"
        "🏦 CBE: `1000307290247`\n\n"
        "📸 **ደረጃ 3：** መጽሐፉን ይምረጡ፣ ይክፈሉ እና **የደረሰኝ ፎቶ (Screenshot)** በዚህ ቻት ይላኩ።\n"
        "⏳ **ደረጃ 4：** የአድሚን ማረጋገጫ ይጠብቁ።"
    )
    return "\n".join(lines), markup


def send_catalog(chat_id: int):
    text, markup = books_text_and_keyboard()
    bot.send_message(chat_id, text, parse_mode="Markdown", reply_markup=markup)


@bot.message_handler(commands=["start"])
def handle_start(message):
    user_id = message.from_user.id
    if is_admin(user_id):
        bot.reply_to(
            message,
            f"ሰላም አድሚን ወርቅዬ (ID: `{user_id}`)! 👑\n"
            "የገዥዎች የክፍያ Screenshot ሲመጣ በቁልፍ ማጽደቅ ወይም `/sendbook <user_id> <book_code>` መጠቀም ይችላሉ።",
            parse_mode="Markdown",
        )
        return
    send_catalog(message.chat.id)


@bot.message_handler(
    func=lambda m: (
        m.content_type == "text"
        and m.text is not None
        and m.text.strip().lower() == "start"
        and not is_admin(m.from_user.id)
    )
)
def handle_plain_start(message):
    send_catalog(message.chat.id)


@bot.callback_query_handler(func=lambda call: call.data.startswith("pick_"))
def handle_book_pick(call):
    user_id = call.from_user.id
    code = call.data.replace("pick_", "", 1)
    if code not in BOOKS:
        bot.answer_callback_query(call.id, "መጽሐፉ አልተገኘም።")
        return

    user_choice[user_id] = code
    book = BOOKS[code]
    bot.answer_callback_query(call.id, f"{book['title']} ({book['price']})")
    bot.send_message(
        call.message.chat.id,
        f"✅ የመረጡት መጽሐፍ፡ **{book['title']}** — **{book['price']}**\n\n"
        "💳 **ክፍያ ይፈጽሙ፡**\n"
        "🟢 Telebirr: `0940277822` (Workiye Nigusu)\n"
        "🏦 CBE: `1000307290247`\n\n"
        "📸 ከከፈሉ በኋላ **የደረሰኝ ፎቶ (Screenshot)** ይላኩና **የአድሚን ማረጋገጫ ይጠብቁ**።",
        parse_mode="Markdown",
    )


@bot.message_handler(content_types=["photo"])
def handle_screenshot(message):
    user_id = message.from_user.id
    if is_admin(user_id):
        return

    code = user_choice.get(user_id, "book_1")
    book = BOOKS[code]
    username = f"@{message.from_user.username}" if message.from_user.username else "የለውም"
    name = message.from_user.first_name or "ገዥ"

    approve_markup = types.InlineKeyboardMarkup()
    approve_markup.add(
        types.InlineKeyboardButton(
            text=f"✅ አጽድቅና መጽሐፍ ላክ ({code})",
            callback_data=f"approve_{user_id}_{code}",
        )
    )

    for admin_id in ADMIN_IDS:
        try:
            bot.send_message(
                admin_id,
                f"🧾 **አዲስ የክፍያ Screenshot ደርሷል**\n"
                f"👤 ገዥ፡ {name} ({username})\n"
                f"🆔 User ID: `{user_id}`\n"
                f"📚 መጽሐፍ፡ {book['title']} ({book['price']})",
                parse_mode="Markdown",
                reply_markup=approve_markup,
            )
            bot.forward_message(admin_id, message.chat.id, message.message_id)
        except Exception as e:
            print(f"Error notifying admin {admin_id}: {e}", flush=True)

    bot.reply_to(
        message,
        "⏳ **የክፍያ ደረሰኝዎ (Screenshot) ደርሷል።**\n"
        "እባክዎ **የአድሚን ማረጋገጫ ይጠብቁ** (Wait for admin approval)። ክፍያው ሲረጋገጥ መጽሐፍዎ በPDF ይላክልዎታል።",
        parse_mode="Markdown",
    )


@bot.callback_query_handler(func=lambda call: call.data.startswith("approve_"))
def handle_approve(call):
    if not is_admin(call.from_user.id):
        bot.answer_callback_query(call.id, "ለአድሚን ብቻ ነው።", show_alert=True)
        return

    payload = call.data.replace("approve_", "", 1)
    parts = payload.split("_", 1)
    if len(parts) != 2:
        bot.answer_callback_query(call.id, "መረጃው ስህተት አለው።")
        return

    try:
        buyer_id = int(parts[0])
    except ValueError:
        bot.answer_callback_query(call.id, "የገዥ ID ስህተት አለው።")
        return

    code = parts[1]
    if code not in BOOKS:
        bot.answer_callback_query(call.id, "መጽሐፉ አልተገኘም።")
        return

    book = BOOKS[code]
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
                    f"✅ **ክፍያዎ በአድሚን ተረጋግጧል!**\n"
                    f"📖 መጽሐፍ፡ {book['title']}\n"
                    f"አዘጋጅ፡ ወርቅዬ ንጉሱ ቸሩ\n"
                    f"መልካም ንባብ!"
                ),
                parse_mode="Markdown",
            )
        bot.answer_callback_query(call.id, "ተረጋግጦ ተልኳል! ✅")
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
        bot.reply_to(message, "⛔ ይህ ትዕዛዝ ለአድሚን ብቻ ነው።")
        return

    parts = message.text.split()
    if len(parts) < 3:
        bot.reply_to(message, "አጠቃቀም፡ `/sendbook <user_id> <book_code>`", parse_mode="Markdown")
        return

    try:
        buyer_id = int(parts[1])
    except ValueError:
        bot.reply_to(message, "❌ ትክክለኛ የገዥ User ID ያስገቡ።")
        return

    code = parts[2].lower()
    if code not in BOOKS:
        bot.reply_to(message, f"❌ ኮድ `{code}` አልተገኘም።", parse_mode="Markdown")
        return

    book = BOOKS[code]
    file_path = book["file"]
    if not os.path.exists(file_path):
        bot.reply_to(message, f"⚠️ ፋይሉ `{file_path}` አልተገኘም።", parse_mode="Markdown")
        return

    try:
        with open(file_path, "rb") as pdf_file:
            bot.send_document(
                buyer_id,
                pdf_file,
                caption=f"✅ ክፍያዎ ተረጋግጧል!\n📖 መጽሐፍ፡ {book['title']}\nአዘጋጅ፡ ወርቅዬ ንጉሱ ቸሩ",
            )
        bot.reply_to(message, f"✅ «{book['title']}» ወደ `{buyer_id}` ተልኳል።")
    except Exception as e:
        bot.reply_to(message, f"❌ ስህተት፡ {e}")


def run_polling():
    print("🤖 Telegram Bot is running with infinity polling...", flush=True)
    bot.infinity_polling(skip_pending=True)


threading.Thread(target=run_polling, daemon=True).start()

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    print(f"🌐 Starting Flask server on port {port}...", flush=True)
    app.run(host="0.0.0.0", port=port)
