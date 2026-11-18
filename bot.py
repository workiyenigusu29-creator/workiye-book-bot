import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler, CallbackQueryHandler, MessageHandler, filters

# የቦት ቶከን
TOKEN = "9000383726:AAEjB5oyItxLQnyidModpHop4H66IMhlL3s"

# የ 6 መጽሐፍት ዝርዝር እና የፋይል ስሞች
BOOKS = {
    "book_1": {"title": "ሀገር በቀል እፅዋትና የህክምና ጥቅማቸው", "price": "100 ብር", "file": "medcine book.pdf"},
    "book_2": {"title": "የትምህርት ሙያዊ ብቃትና ተግባራዊ አፈጻጸም", "price": "150 ብር", "file": "የትምህርት ሙያዊ ብቃት.pdf"},
    "book_3": {"title": "Professional competence and practical performance in education", "price": "150 ብር", "file": "Educational competency.pdf"},
    "book_4": {"title": "የመሪነት ጥበብ", "price": "200 ብር", "file": "የመሪነት ጥበብ.pdf"},
    "book_5": {"title": "የስኬት ምስጢር", "price": "200 ብር", "file": "የስኬት ምስጢር.pdf"},
    "book_6": {"title": "የሲቭል ሰርቭስ የብቃት ምዘና ጥያቄዎች 457 በላይ", "price": "200 ብር", "file": "civil service exam.pdf"},
}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_name = update.effective_user.first_name
    welcome_text = (
        f"ሰላም <b>{user_name}</b>! እንኳን ወደ መጽሐፍ መሸጫ ቦታችን በደህና መጡ።\n\n"
        "ከዚህ በታች ያሉትን ጥራት ያላቸው መጽሐፍት በመምረጥ ማግኘት ይችላሉ። ለመግዛት የሚፈልጉትን መጽሐፍ ይምረጡ፡"
    )
    
    keyboard = []
    for key, book in BOOKS.items():
        keyboard.append([InlineKeyboardButton(f"📖 {book['title']} — {book['price']}", callback_data=key)])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_html(welcome_text, reply_markup=reply_markup)

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    book_key = query.data
    
    if book_key in BOOKS:
        book = BOOKS[book_key]
        context.user_data['selected_book'] = book_key
        
        text = (
            f"📚 <b>የመረጡት መጽሐፍ:</b> {book['title']}\n"
            f"💰 <b>ዋጋ:</b> {book['price']}\n\n"
            "መጽሐፉን ለመግዛት እባክዎ ከታች ባሉት የክፍያ አካውንቶች ክፍያውን ይፈጽሙ፡\n\n"
            "🟢 <b>Telebirr:</b> 0940277822 (workiye Nigusu)\n"
            "🏦 <b>የኢትዮጵያ ንግድ ባንክ (CBE):</b> 1000307290247\n\n"
            "ክፍያውን ከፈጸሙ በኋላ <b>የባንኩን ወይም የቴሌቢርን የደረሰኝ ፎቶ (Screenshot)</b> ወደዚህ ቦት ይላኩ!"
        )
        await query.message.reply_html(text)

async def handle_payment(update: Update, context: ContextTypes.DEFAULT_TYPE):
    book_key = context.user_data.get('selected_book')
    
    if not book_key:
        await update.message.reply_text("እባክዎ መጀመሪያ /start በመጫን መጽሐፍ ይምረጡ።")
        return

    if update.message.photo:
        # ለጊዜው አውቶማቲክ እንዲልክ የሚከተለውን ኮድ እንጠቀማለን (በኋላ በአስተዳዳሪ ማረጋገጫ መቀየር ይችላሉ)
        book = BOOKS[book_key]
        file_name = book['file']
        
        await update.message.reply_text("✅ የክፍያ ማረጋገጫዎ ደርሷል! መጽሐፍዎ ደህንነቱ በተጠበቀ ሁኔታ እየተላከ ነው...")
        
        try:
            # 💡 protect_content=True ማለት ተጠቃሚው እንዳያወርድ፣ እንዳይቀዳ (Forward) እና እንዳይቆርጥ ይከለክላል
            with open(file_name, 'rb') as pdf_file:
                await update.message.reply_document(
                    document=pdf_file,
                    caption=f"📖 <b>{book['title']}</b>\n\nይህ መጽሐፍ ለግል ንባብ ብቻ የተዘጋጀ ነው። የ π / የቅጂ መብት የተጠበቀ ነው።",
                    parse_mode="HTML",
                    protect_content=True  # 🔒 ማውረድ እና ፎርዋርድ ማድረግን ይከለክላል
                )
        except Exception as e:
            await update.message.reply_text(f"ይቅርታ፣ ፋይሉን መላክ አልተቻለም። እባክዎ አስተዳዳሪውን ያነጋገሩ። (ስህተት: {e})")
            
        # ከተላከ በኋላ የተመረጠውን መጽሐፍ ማጽዳት
        context.user_data['selected_book'] = None
    else:
        await update.message.reply_text("እባክዎ ትክክለኛ የክፍያ ደረሰኝ ፎቶ (Screenshot) ይላኩ።")

def main():
    app = ApplicationBuilder().token(TOKEN).build()
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button_handler))
    app.add_handler(MessageHandler(filters.PHOTO | filters.TEXT & ~filters.COMMAND, handle_payment))
    
    print("ቦቱ በመሥራት ላይ ነው...")
    app.run_polling()

if __name__ == "__main__":
    main()
