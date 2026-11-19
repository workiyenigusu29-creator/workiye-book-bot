import os
import threading
from flask import Flask
import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

BOT_TOKEN = os.getenv("BOT_TOKEN", "9000383726:AAF_1RKfb3jlwdpJir0-CN2nfPltnET4cGY")

# Admin Telegram numeric User ID
ADMIN_ID = 741140918

# Payment details shown to buyers
PAYMENT_INFO = (
    "💳 **የክፍያ አማራጮች (Payment Methods):**\n"
    "• **Telebirr:** `0940277822` (ወርቅዬ ንጉሱ ቸሩ)\n"
    "• **CBE:** `1000307290247` (ወርቅዬ ንጉሱ ቸሩ)\n\n"
    "📸 ክፍያውን ከፈጸሙ በኋላ **የደረሰኙን ፎቶ (Screenshot)** እዚህ ይላኩ።"
)

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

bot = telebot.TeleBot(BOT_TOKEN)
app = Flask(__name__)

# Track selected book per user: {user_id: "book_1"}
user_selected_book = {}


@app.route("/")
@app.route("/health")
def home():
    return "Bot is running", 200


def run_web_server():
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port, debug=False, use_reloader=False)


def get_books_keyboard():
    markup = InlineKeyboardMarkup(row_width=1)
    for book_id, info in BOOKS.items():
        btn_text = f"📚 {info['title']} — {info['price']}"
        markup.add(InlineKeyboardButton(btn_text, callback_data=f"select_{book_id}"))
    return markup


@bot.message_handler(commands=["start", "books"])
def send_welcome(message):
    welcome_text = (
        "👋 **እንኳን በደህና መጡ!**\n"
        "አዘጋጅ፦ **ወርቅዬ ንጉሱ ቸሩ**\n\n"
        "ለመግዛት የሚፈልጉትን መጽሐፍ ከታች ካለው ዝርዝር ይምረጡ፦"
    )
    bot.send_message(
        message.chat.id,
        welcome_text,
        parse_mode="Markdown",
        reply_markup=get_books_keyboard(),
    )


@bot.callback_query_handler(func=lambda call: call.data.startswith("select_"))
def handle_book_selection(call):
    book_id = call.data.replace("select_", "")
    book = BOOKS.get(book_id)

    if not book:
        bot.answer_callback_query(call.id, "መጽሐፉ አልተገኘም!")
        return

    user_selected_book[call.from_user.id] = book_id
    bot.answer_callback_query(call.id)

    order_text = (
        f"📖 **የመረጡት መጽሐፍ:** {book['title']}\n"
        f"💰 **ዋጋ:** {book['price']}\n\n"
        f"{PAYMENT_INFO}"
    )
    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton("⬅️ ወደ ዝርዝር ተመለስ", callback_data="back_to_list"))

    bot.edit_message_text(
        chat_id=call.message.chat.id,
        message_id=call.message.message_id,
        text=order_text,
        parse_mode="Markdown",
        reply_markup=markup,
    )


@bot.callback_query_handler(func=lambda call: call.data == "back_to_list")
def handle_back_to_list(call):
    bot.answer_callback_query(call.id)
    welcome_text = (
        "📚 **የሚገኙ መጻሕፍት ዝርዝር**\n"
        "ለመግዛት የሚፈልጉትን መጽሐፍ ይምረጡ፦"
    )
    bot.edit_message_text(
        chat_id=call.message.chat.id,
        message_id=call.message.message_id,
        text=welcome_text,
        parse_mode="Markdown",
        reply_markup=get_books_keyboard(),
    )


@bot.message_handler(content_types=["photo"])
def handle_payment_receipt(message):
    user_id = message.from_user.id
    book_id = user_selected_book.get(user_id)

    if not book_id:
        bot.reply_to(
            message,
            "⚠️ እባክዎ መጀመሪያ /start በመጫን የሚፈልጉትን መጽሐፍ ይምረጡ፣ ከዚያም ደረሰኙን ይላኩ።",
        )
        return

    book = BOOKS[book_id]
    user_name = message.from_user.first_name or "Customer"
    username = f"@{message.from_user.username}" if message.from_user.username else "No username"

    bot.reply_to(
        message,
        "✅ ደረሰኝዎ ደርሶናል! ክፍያዎ እንደተረጋገጠ መጽሐፉ ወዲያውኑ ይላክልዎታል።",
    )

    admin_caption = (
        f"🔔 **አዲስ የክፍያ ጥያቄ (New Order)**\n"
        f"👤 **ገዢ:** {user_name} ({username})\n"
        f"🆔 **User ID:** `{user_id}`\n"
        f"📚 **መጽሐፍ:** {book['title']}\n"
        f"💰 **ዋጋ:** {book['price']}"
    )
    approve_markup = InlineKeyboardMarkup(row_width=2)
    approve_markup.add(
        InlineKeyboardButton("✅ አጽድቅና ላክ", callback_data=f"approve_{user_id}_{book_id}"),
        InlineKeyboardButton("❌ ውድቅ አድርግ", callback_data=f"reject_{user_id}"),
    )

    photo_file_id = message.photo[-1].file_id
    bot.send_photo(
        ADMIN_ID,
        photo_file_id,
        caption=admin_caption,
        parse_mode="Markdown",
        reply_markup=approve_markup,
    )


@bot.callback_query_handler(func=lambda call: call.data.startswith("approve_"))
def handle_admin_approve(call):
    if call.from_user.id != ADMIN_ID:
        bot.answer_callback_query(call.id, "ፈቃድ የለዎትም!")
        return

    _, target_user_id_str, book_id = call.data.split("_", 2)
    target_user_id = int(target_user_id_str)
    book = BOOKS.get(book_id)

    if not book:
        bot.answer_callback_query(call.id, "Book not found in dictionary.")
        return

    file_path = book["file"]
    if not os.path.exists(file_path):
        bot.answer_callback_query(call.id, f"File missing: {file_path}", show_alert=True)
        return

    try:
        bot.send_message(
            target_user_id,
            f"🎉 ክፍያዎ ተረጋግጧል! ስለገዙን እናመሰግናለን።\n📖 **{book['title']}** እነሆ፦",
            parse_mode="Markdown",
            protect_content=True,
        )
        with open(file_path, "rb") as pdf_file:
            bot.send_document(
                target_user_id,
                pdf_file,
                protect_content=True,
            )

        bot.edit_message_caption(
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            caption=call.message.caption + "\n\n✅ **ጸድቋል — መጽሐፉ ተልኳል!**",
            parse_mode="Markdown",
        )
        bot.answer_callback_query(call.id, "መጽሐፉ ተልኳል!")
    except Exception as e:
        bot.answer_callback_query(call.id, f"Error: {e}", show_alert=True)


@bot.callback_query_handler(func=lambda call: call.data.startswith("reject_"))
def handle_admin_reject(call):
    if call.from_user.id != ADMIN_ID:
        bot.answer_callback_query(call.id, "ፈቃድ የለዎትም!")
        return

    target_user_id = int(call.data.split("_")[1])
    bot.send_message(
        target_user_id,
        "❌ የላኩት የክፍያ ደረሰኝ ትክክለኛ አይደለም ወይም አልተረጋገጠም። እባክዎ ትክክለኛውን ደረሰኝ በድጋሚ ይላኩ።",
    )
    bot.edit_message_caption(
        chat_id=call.message.chat.id,
        message_id=call.message.message_id,
        caption=call.message.caption + "\n\n❌ **ውድቅ ተደርጓል!**",
        parse_mode="Markdown",
    )
    bot.answer_callback_query(call.id, "ውድቅ ተደርጓል።")


if __name__ == "__main__":
    server_thread = threading.Thread(target=run_web_server, daemon=True)
    server_thread.start()
    print("Web server & bot are running...")
    bot.infinity_polling(skip_pending=True, timeout=30, long_polling_timeout=25)
