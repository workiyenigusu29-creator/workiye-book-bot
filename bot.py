import os
import telebot

BOT_TOKEN = os.environ.get("9000383726:AAEjB5oyItxLQnyidModpHop4H66IMhlL3s")
ADMIN_IDS = {741140918}

# Map book codes to your PDF filenames
BOOKS = {
    "book_1": ("ሀገር በቀል እፅዋትና የህክምና ጥቅማቸው", "medcine book.pdf"),
    "book_2": ("የትምህርት ሙያዊ ብቃትና ተግባራዊ አፈጻጸም", "የትምህርት ሙያዊ ብቃት.pdf"),
    "book_3": ("Professional competence and practical performance in education", "Educational competency.pdf"),
    "book_4": ("የመሪነት ጥበብ", "የመሪነት ጥበብ.pdf"),
    "book_5": ("የስኬት ምስጢር", "የስኬት ምስጢር.pdf"),
    "book_6": ("የሲቭል ሰርቭስ የብቃት ምዘና ጥያቄዎች 457 በላይ", "civil service exam.pdf"),
}

bot = telebot.TeleBot(BOT_TOKEN)


def is_admin(user_id: int) -> bool:
    return user_id in ADMIN_IDS


@bot.message_handler(commands=["start"])
def handle_start(message):
    user_id = message.from_user.id

    if is_admin(user_id):
        book_list = "\n".join([f"• `{code}` → {title}" for code, (title, _) in BOOKS.items()])
        bot.reply_to(
            message,
            f"ሰላም አድሚን ወርቅዬ (ID: `{user_id}`)! 👑\n\n"
            "የአድሚን ትዕዛዞች፡\n"
            "• `/sendbook <user_id> <book_code>` — PDF መጽሐፍ ለገዥ ለመላክ\n"
            "• `/id` — የእርስዎን ID ለማየት\n\n"
            f"የመጽሐፍ ኮዶች (Book Codes):\n{book_list}",
            parse_mode="Markdown",
        )
    else:
        bot.reply_to(
            message,
            "ሰላም! ወደ የመጽሐፍ መሸጫ ቦት (@Lisanwork12_Bot) እንኳን ደህና መጡ። 📚\n\n"
            "መጽሐፍ ለመግዛት፡\n"
            "1. በድረ-ገጻችን ላይ የሚፈልጉትን መጽሐፍ ይምረጡና በTelebirr (0940277822) ወይም CBE (1000307290247) ይክፈሉ።\n"
            "2. የክፍያ ደረሰኝ ፎቶ (Screenshot) እና የመጽሐፉን ስም እዚህ ይላኩ።\n"
            "3. አድሚኑ እንዳረጋገጠ መጽሐፉ በቀጥታ እዚህ ይላክልዎታል።",
        )


@bot.message_handler(commands=["id"])
def handle_id(message):
    role = "Admin 👑" if is_admin(message.from_user.id) else "User 👤"
    bot.reply_to(message, f"User ID: `{message.from_user.id}`\nRole: {role}", parse_mode="Markdown")


@bot.message_handler(commands=["sendbook"])
def handle_sendbook(message):
    if not is_admin(message.from_user.id):
        bot.reply_to(message, "⛔ ይህ ትዕዛዝ ለአድሚን ብቻ የተፈቀደ ነው።")
        return

    parts = message.text.split()
    if len(parts) < 3:
        bot.reply_to(
            message,
            "አጠቃቀም፡ `/sendbook <user_id> <book_code>`\nምሳሌ፡ `/sendbook 123456789 book_1`",
            parse_mode="Markdown",
        )
        return

    try:
        target_user_id = int(parts[1])
    except ValueError:
        bot.reply_to(message, "❌ ትክክለኛ የገዥ User ID (ቁጥር) ያስገቡ።")
        return

    book_code = parts[2].lower()
    if book_code not in BOOKS:
        bot.reply_to(message, f"❌ የመጽሐፍ ኮድ `{book_code}` አልተገኘም። (`book_1` እስከ `book_6` ይጠቀሙ)", parse_mode="Markdown")
        return

    title, file_path = BOOKS[book_code]
    if not os.path.exists(file_path):
        bot.reply_to(message, f"⚠️ ፋይሉ `{file_path}` በቦቱ ፎልደር ውስጥ አልተገኘም።", parse_mode="Markdown")
        return

    try:
        with open(file_path, "rb") as pdf_file:
            bot.send_document(
                target_user_id,
                pdf_file,
                caption=f"✅ ክፍያዎ ተረጋግጧል!\n📖 መጽሐፍ፡ {title}\nአዘጋጅ፡ ወርቅዬ ንጉሱ ቸሩ\nመልካም ንባብ!",
            )
        bot.reply_to(message, f"✅ «{title}» ወደ User ID `{target_user_id}` በተሳካ ሁኔታ ተልኳል።", parse_mode="Markdown")
    except Exception as e:
        bot.reply_to(message, f"❌ መጽሐፉን መላክ አልተቻለም፡ {e}")


@bot.message_handler(content_types=["photo", "document", "text"])
def handle_user_messages(message):
    user_id = message.from_user.id

    # Admin messages are not treated as buyer payment receipts
    if is_admin(user_id):
        return

    username = f"@{message.from_user.username}" if message.from_user.username else "የለውም"
    full_name = message.from_user.first_name or "ገዥ"

    for admin_id in ADMIN_IDS:
        try:
            bot.send_message(
                admin_id,
                f"📩 **አዲስ የገዥ መልዕክት / ደረሰኝ**\n"
                f"👤 ስም፡ {full_name} ({username})\n"
                f"🆔 User ID: `{user_id}`\n\n"
                f"መጽሐፍ ለመላክ፡ `/sendbook {user_id} book_1`",
                parse_mode="Markdown",
            )
            bot.forward_message(admin_id, message.chat.id, message.message_id)
        except Exception as e:
            print(f"Admin notification error: {e}")

    bot.reply_to(
        message,
        "✅ መልዕክትዎ እና የክፍያ ማረጋገጫዎ ለአድሚኑ ደርሷል።\n"
        "እንደተረጋገጠ መጽሐፍዎ በዚህ ቻት ይላክልዎታል።",
    )


bot.infinity_polling()
