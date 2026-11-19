from datetime import datetime, timedelta
import os
import re
import threading
import time
from flask import Flask
import telebot
from telebot.apihelper import ApiTelegramException
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

BOT_TOKEN = os.getenv("BOT_TOKEN", "9000383726:AAF_1RKfb3jlwdpJir0-CN2nfPltnET4cGY")

# Admin Telegram numeric User ID
ADMIN_ID = 741140918

# Required markers and freshness window
REQUIRED_PHONE_SNIPPET = "127"
CBE_ACCOUNT = "1000307290247"
MAX_AGE_MINUTES = 30

PAYMENT_INFO = (
    "💳 **የክፍያ አማራጮች (Payment Methods):**\n"
    "• **Telebirr:** `0940277822` (ወርቅዬ ንጉሱ ቸሩ)\n"
    "• **CBE:** `1000307290247` (ወርቅዬ ንጉሱ ቸሩ)\n\n"
    f"📩 ክፍያውን ከፈጸሙ በኋላ **የCBE ማረጋገጫ መልዕክቱን** (በቀጥታ ወይም **Forward** አድርገው) እዚህ ይላኩ። በ `{MAX_AGE_MINUTES}` ደቂቃ ውስጥ የተላከ እና `127` ያለበት መሆን አለበት።"
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

# Track used transaction references in current process
used_tx_refs = set()


@app.route("/", methods=["GET", "HEAD"])
@app.route("/health", methods=["GET", "HEAD"])
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


def get_effective_message_datetime(message) -> datetime:
    ts = getattr(message, "forward_date", None) or message.date
    return datetime.fromtimestamp(ts)


def get_forward_source_label(message) -> str:
    if getattr(message, "forward_from_chat", None):
        title = message.forward_from_chat.title or "Channel/Chat"
        return f"Forwarded Chat: {title} ({message.forward_from_chat.id})"
    if getattr(message, "forward_from", None):
        u = message.forward_from
        uname = f"@{u.username}" if u.username else f"ID:{u.id}"
        return f"Forwarded User: {u.first_name or ''} ({uname})".strip()
    if getattr(message, "forward_date", None):
        return "Forwarded (Hidden Source)"
    return "Direct Text"


def parse_receipt_datetime(text: str, fallback_now: datetime):
    date_patterns = [
        (r"\b(\d{4})-(\d{1,2})-(\d{1,2})\b", "YMD"),
        (r"\b(\d{1,2})/(\d{1,2})/(\d{4})\b", "DMY"),
        (r"\b(\d{1,2})-(\d{1,2})-(\d{4})\b", "DMY"),
    ]
    found_date = None
    for pattern, fmt in date_patterns:
        m = re.search(pattern, text)
        if m:
            try:
                if fmt == "YMD":
                    y, mo, d = int(m.group(1)), int(m.group(2)), int(m.group(3))
                else:
                    d, mo, y = int(m.group(1)), int(m.group(2)), int(m.group(3))
                found_date = datetime(y, mo, d).date()
                break
            except ValueError:
                pass

    time_12 = re.search(r"\b(\d{1,2}):(\d{2})(?::\d{2})?\s*(AM|PM)\b", text, flags=re.IGNORECASE)
    time_24 = re.search(r"\b([01]?\d|2[0-3]):([0-5]\d)(?::[0-5]\d)?\b", text)

    found_time = None
    if time_12:
        hour = int(time_12.group(1))
        minute = int(time_12.group(2))
        ampm = time_12.group(3).upper()
        if ampm == "PM" and hour != 12:
            hour += 12
        elif ampm == "AM" and hour == 12:
            hour = 0
        if 0 <= hour <= 23 and 0 <= minute <= 59:
            found_time = (hour, minute)
    elif time_24:
        hour = int(time_24.group(1))
        minute = int(time_24.group(2))
        found_time = (hour, minute)

    if not found_date and not found_time:
        return None, "በመልዕክቱ ውስጥ ቀን ወይም ሰዓት አልተገኘም።"

    target_date = found_date or fallback_now.date()
    hour, minute = found_time or (fallback_now.hour, fallback_now.minute)
    try:
        parsed_dt = datetime(target_date.year, target_date.month, target_date.day, hour, minute)
    except ValueError:
        return None, "የተገኘው የቀን ወይም የሰዓት ቅርጸት ትክክል አይደለም።"

    return parsed_dt, None


def validate_payment_message(text: str, msg_dt: datetime):
    now = datetime.now()

    if (now - msg_dt) > timedelta(minutes=MAX_AGE_MINUTES):
        return False, f"የመልዕክቱ ቀን/ሰዓት ከ `{MAX_AGE_MINUTES}` ደቂቃ በላይ አልፎታል።"

    lowered = text.lower()
    has_cbe = (
        "cbe" in lowered
        or "commercial bank of ethiopia" in lowered
        or CBE_ACCOUNT in text
    )
    has_phone_127 = REQUIRED_PHONE_SNIPPET in text

    if not has_cbe:
        return False, "መልዕክቱ የCBE ክፍያ ማረጋገጫ መሆኑ አልተረጋገጠም።"
    if not has_phone_127:
        return False, f"በመልዕክቱ ውስጥ `{REQUIRED_PHONE_SNIPPET}` አልተገኘም።"

    receipt_dt, dt_err = parse_receipt_datetime(text, now)
    if dt_err:
        return False, dt_err

    if receipt_dt.date() != now.date():
        return False, f"የደረሰኙ ቀን (`{receipt_dt.date()}`) የዛሬ ቀን (`{now.date()}`) አይደለም።"

    age = abs(now - receipt_dt)
    if age > timedelta(minutes=MAX_AGE_MINUTES):
        return False, f"የደረሰኙ ሰዓት (`{receipt_dt.strftime('%H:%M')}`) ከ `{MAX_AGE_MINUTES}` ደቂቃ በላይ ልዩነት አለው።"

    ref_match = re.search(r"\b(?:FT[A-Z0-9]{6,}|[A-Z0-9]{8,})\b", text, flags=re.IGNORECASE)
    tx_ref = ref_match.group(0).upper() if ref_match else None

    if tx_ref and tx_ref in used_tx_refs:
        return False, f"ይህ የግብይት መለያ (`{tx_ref}`) ቀደም ብሎ ጥቅም ላይ ውሏል።"

    return True, (tx_ref, receipt_dt)


def deliver_book(target_user_id, book):
    file_path = book["file"]
    if not os.path.exists(file_path):
        return False, f"File missing: {file_path}"

    bot.send_message(
        target_user_id,
        f"🎉 ክፍያዎ በራስ-ሰር ተረጋግጧል! ስለገዙን እናመሰግናለን።\n📖 **{book['title']}** እነሆ፦",
        parse_mode="Markdown",
        protect_content=True,
    )
    with open(file_path, "rb") as pdf_file:
        bot.send_document(
            target_user_id,
            pdf_file,
            protect_content=True,
        )
    return True, None


def forward_flag_to_admin(message, reason: str):
    user = message.from_user
    uname = f"@{user.username}" if user.username else "No username"
    book_id = user_selected_book.get(user.id)
    book_title = BOOKS[book_id]["title"] if book_id in BOOKS else "Not selected"
    try:
        bot.forward_message(ADMIN_ID, message.chat.id, message.message_id)
        bot.send_message(
            ADMIN_ID,
            f"⚠️ **Flagged / Unverified Submission (No Book Sent)**\n"
            f"👤 **User:** {user.first_name or 'User'} ({uname}) | ID: `{user.id}`\n"
            f"📚 **Selected Book:** {book_title}\n"
            f"📌 **Reason:** {reason}",
            parse_mode="Markdown",
        )
    except Exception as e:
        print(f"Failed to forward flagged message to admin: {e}")


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


@bot.message_handler(content_types=["document", "photo"])
def handle_doc_or_photo(message):
    kind = "document" if message.content_type == "document" else "photo screenshot"
    forward_flag_to_admin(message, f"Buyer sent a {kind} instead of verified CBE text")
    bot.reply_to(
        message,
        "⚠️ የላኩት ፋይል/ፎቶ በራስ-ሰር አልተረጋገጠም፤ ለክትትል ለአድሚን ተላልፏል። እባክዎ ቀኑ እና ሰዓቱ ያሉበትን **የCBE ማረጋገጫ መልዕክት ጽሑፍ** ይላኩ።",
    )


@bot.message_handler(func=lambda message: True, content_types=["text"])
def handle_payment_message(message):
    text = (message.text or "").strip()
    if text.startswith("/"):
        return

    user_id = message.from_user.id
    book_id = user_selected_book.get(user_id)

    if not book_id:
        bot.reply_to(
            message,
            "⚠️ እባክዎ መጀመሪያ /start በመጫን የሚፈልጉትን መጽሐፍ ይምረጡ፣ ከዚያም የCBE ማረጋገጫ መልዕክቱን ይላኩ።",
        )
        return

    msg_dt = get_effective_message_datetime(message)
    is_valid, result = validate_payment_message(text, msg_dt)
    if not is_valid:
        forward_flag_to_admin(message, result)
        bot.reply_to(
            message,
            f"❌ በራስ-ሰር ማጽደቅ አልተቻለም፦ {result}",
            parse_mode="Markdown",
        )
        return

    tx_ref, receipt_dt = result
    book = BOOKS[book_id]
    user_name = message.from_user.first_name or "Customer"
    username = f"@{message.from_user.username}" if message.from_user.username else "No username"
    source_label = get_forward_source_label(message)

    bot.reply_to(
        message,
        "✅ የCBE መልዕክት፣ `127`፣ እንዲሁም ቀን እና ሰዓት ተረጋግጠዋል! መጽሐፉ አሁን እየተላከ ነው...",
        parse_mode="Markdown",
    )

    ok, err = deliver_book(user_id, book)
    if not ok:
        bot.send_message(
            user_id,
            "❌ መጽሐፉን ለመላክ ጊዜያዊ ችግር አጋጥሟል። እባክዎ ቆይተው ይሞክሩ።",
        )
        bot.send_message(
            ADMIN_ID,
            f"⚠️ Delivery failed for `{user_id}` ({book['title']}): {err}",
            parse_mode="Markdown",
        )
        return

    if tx_ref:
        used_tx_refs.add(tx_ref)
    user_selected_book.pop(user_id, None)

    admin_text = (
        f"🤖 **በራስ-ሰር የተላከ ትዕዛዝ (Auto-Approved)**\n"
        f"👤 **ገዢ:** {user_name} ({username})\n"
        f"🆔 **User ID:** `{user_id}`\n"
        f"📡 **Source:** `{source_label}`\n"
        f"📚 **መጽሐፍ:** {book['title']}\n"
        f"💰 **ዋጋ:** {book['price']}\n"
        f"🔖 **Ref:** `{tx_ref or 'N/A'}`\n"
        f"🕒 **Receipt Time:** `{receipt_dt.strftime('%Y-%m-%d %H:%M')}`\n"
        f"📩 **Msg Date:** `{msg_dt.strftime('%Y-%m-%d %H:%M')}`"
    )
    try:
        bot.send_message(ADMIN_ID, admin_text, parse_mode="Markdown")
    except Exception as e:
        print(f"Failed to notify admin: {e}")


def run_polling():
    try:
        bot.remove_webhook()
    except Exception:
        pass

    while True:
        try:
            bot.infinity_polling(skip_pending=True, timeout=30, long_polling_timeout=25)
        except ApiTelegramException as e:
            if e.error_code == 409:
                time.sleep(10)
            else:
                time.sleep(5)
        except Exception as e:
            print(f"Polling error: {e}")
            time.sleep(5)


if __name__ == "__main__":
    server_thread = threading.Thread(target=run_web_server, daemon=True)
    server_thread.start()
    print("Web server & bot are running...")
    run_polling()
