import os
import telebot
from flask import Flask
from threading import Thread
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

# ==================== CONFIGURATION ====================
TOKEN = "8777498362:AAEBasfJ75olNP93pUjBiCLu2XgIER0Jvqk"
ADMIN_ID = 741140918
PDF_FILE_PATH = "workiye_book.pdf"
# =======================================================

bot = telebot.TeleBot(TOKEN)

BOOK_TITLE = "የትምህርት ሙያዊ ብቃትና ተግባራዊ አፈጻጸም"
PRICE = "150 ETB"
TELEBIRR = "0940277822 (Workiye Nigusu)"
CBE_ACC = "1000307290247 (Workiye Nigusu)"

# ==================== FLASK SERVER FOR RENDER ====================
app = Flask('')

@app.route('/')
def home():
    return "Bot is active and running!"

def run_flask():
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)

def keep_alive():
    t = Thread(target=run_flask)
    t.daemon = True
    t.start()
# ================================================================

@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    welcome_text = (
        f"ሰላም {message.from_user.first_name}! እንኳን ደህና መጡ።\n\n"
        f"📚 **{BOOK_TITLE}**\n"
        f"✍️ አዘጋጅ፦ ወርቅዬ ንጉሱ\n"
        f"💰 ዋጋ፦ {PRICE}\n\n"
        f"ይህን መጽሐፍ ለመግዛት እባክዎ ከታች ባሉት አካውንቶች ክፍያውን ይፈጽሙ፡\n\n"
        f"📱 **Telebirr**: `{TELEBIRR}`\n"
        f"🏦 **CBE (የኢትዮጵያ ንግድ ባንክ)**: `{CBE_ACC}`\n\n"
        f"ክፍያውን ከፈጸሙ በኋላ የክፍያ ማረጋገጫ (Receipt Screenshot ወይም Transaction ID) በዚህ ቦት ይላኩ!"
    )
    bot.reply_to(message, welcome_text, parse_mode="Markdown")

@bot.message_handler(content_types=['photo', 'text', 'document'])
def handle_payment_proof(message):
    if message.from_user.id == ADMIN_ID:
        bot.reply_to(message, "⚠️ እርስዎ አስተዳዳሪ (Admin) ነዎት። ተጠቃሚዎች የሚልኩት የክፍያ ማረጋገጫ ወደዚህ ይመጣል።")
        return

    user_id = message.from_user.id
    user_name = message.from_user.first_name
    username = f"@{message.from_user.username}" if message.from_user.username else "የሌለው"

    markup = InlineKeyboardMarkup()
    markup.row(
        InlineKeyboardButton("✅ አጽድቅ (Approve)", callback_data=f"approve_{user_id}"),
        InlineKeyboardButton("❌ ውድቅ አድርግ (Reject)", callback_data=f"reject_{user_id}")
    )

    forward_text = (
        f"📥 **አዲስ የክፍያ ማረጋገጫ ደርሷል!**\n\n"
        f"👤 ስም: {user_name}\n"
        f"🔗 ዩዘርናም: {username}\n"
        f"🆔 User ID: `{user_id}`"
    )

    if message.photo:
        bot.send_photo(ADMIN_ID, message.photo[-1].file_id, caption=forward_text, reply_markup=markup, parse_mode="Markdown")
    elif message.document:
        bot.send_document(ADMIN_ID, message.document.file_id, caption=forward_text, reply_markup=markup, parse_mode="Markdown")
    else:
        bot.send_message(ADMIN_ID, f"{forward_text}\n\n💬 መልዕክት/TxID: {message.text}", reply_markup=markup, parse_mode="Markdown")

    bot.reply_to(message, "✅ የክፍያ ማረጋገጫዎ ደርሶናል! አስተዳዳሪው ሲያረጋግጠው ፒዲኤፉ ወዲያውኑ ይላክልዎታል። እናመሰግናለን!")

@bot.callback_query_handler(func=lambda call: True)
def callback_query(call):
    try:
        action, target_user_id_str = call.data.split("_")
        target_user_id = int(target_user_id_str)
    except Exception:
        bot.answer_callback_query(call.id, "⚠️ ስህተት ተፈጥሯል!")
        return

    if action == "approve":
        bot.send_message(target_user_id, "🎉 ክፍያዎ በትክክል ጸድቋል! መጽሐፉን ከዚህ በታች ማውረድ ይችላሉ። እናመሰግናለን! 📚")
        try:
            with open(PDF_FILE_PATH, "rb") as pdf_file:
                bot.send_document(target_user_id, pdf_file, protect_content=True)
            bot.answer_callback_query(call.id, "ተጠቃሚው ጸድቆ ፒዲኤፉ ተልኳል!")
        except FileNotFoundError:
            bot.send_message(target_user_id, "⚠️ የፒዲኤፍ ፋይሉ በሲስተሙ አልተገኘም፤ እባክዎ አስተዳዳሪውን ያነጋግሩ።")
            bot.send_message(ADMIN_ID, "⚠️ ማስጠንቀቂያ: workiye_book.pdf ፋይሉ በቦቱ አቃፊ ውስጥ አልተገኘም!")
        
        try:
            if call.message.photo:
                bot.edit_message_caption(chat_id=call.message.chat.id, message_id=call.message.message_id, caption=f"{call.message.caption}\n\n✅ **ጸድቋል (Approved)**", parse_mode="Markdown")
            else:
                bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id, text=f"{call.message.text}\n\n✅ **ጸድቋል (Approved)**", parse_mode="Markdown")
        except Exception:
            pass

    elif action == "reject":
        bot.send_message(target_user_id, "❌ ይቅርታ፣ የክፍያ ማረጋገጫዎ አልተረጋገጠም። እባክዎ በትክክል እንደገና ይሞክሩ።")
        bot.answer_callback_query(call.id, "ክፍያው ውድቅ ተደርጓል።")
        try:
            if call.message.photo:
                bot.edit_message_caption(chat_id=call.message.chat.id, message_id=call.message.message_id, caption=f"{call.message.caption}\n\n❌ **ውድቅ ተደርጓል (Rejected)**", parse_mode="Markdown")
            else:
                bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id, text=f"{call.message.text}\n\n❌ **ውድቅ ተደርጓል (Rejected)**", parse_mode="Markdown")
        except Exception:
            pass

if __name__ == "__main__":
    print("🤖 Starting Flask Keep-Alive Server...")
    keep_alive()
    print("🤖 Telegram Bot is running with infinity polling...")
    bot.infinity_polling(skip_pending=True)
