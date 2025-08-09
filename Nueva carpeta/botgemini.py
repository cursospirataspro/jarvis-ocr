from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, MessageHandler, CommandHandler, filters
import google.generativeai as genai

# Tus claves seguras
TELEGRAM_BOT_TOKEN = "7606439237:AAEx1gU7OOi3-WZn39103Xq5BeeTua6z-D8"
GEMINI_API_KEY = "AIzaSyAQOnN-SaPw-Tn3gQDl-pp-_OCR5FkR4Fk"

# Configura Gemini
genai.configure(api_key=GEMINI_API_KEY)

# Usa el modelo rápido gratuito
model = genai.GenerativeModel(model_name="models/gemini-2.5-flash")

# Comando /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("¡Hola! Soy tu bot Gemini 2.5 Flash. Escríbeme algo.")

# Respuesta a mensajes normales
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_input = update.message.text
    try:
        response = model.generate_content(user_input)
        reply = response.text
    except Exception as e:
        reply = f"❌ Error: {e}"
    await update.message.reply_text(reply)

# Ejecutar bot
if __name__ == '__main__':
    app = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    print("🤖 Bot corriendo con Gemini 2.5 Flash...")
    app.run_polling()
