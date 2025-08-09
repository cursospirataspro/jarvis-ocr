import os
import io
import fitz  # PyMuPDF
import pytesseract
from PIL import Image
from pdf2image import convert_from_bytes
from telegram import Update, InputFile, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes, CallbackQueryHandler
from google.generativeai import configure, GenerativeModel

# 🔐 Tus credenciales (REEMPLAZA POR LAS TUYAS)
TELEGRAM_API_KEY = "7606439237:AAEx1gU7OOi3-WZn39103Xq5BeeTua6z-D8"
GEMINI_API_KEY = "AIzaSyAQOnN-SaPw-Tn3gQDl-pp-_OCR5FkR4Fk"
GEMINI_MODEL = "models/gemini-2.5-flash"

# 📌 Configura Gemini
configure(api_key=GEMINI_API_KEY)
model = GenerativeModel(GEMINI_MODEL)

# Ruta para Tesseract
pytesseract.pytesseract.tesseract_cmd = r"C:\Users\Hunter Garcia\AppData\Local\Programs\Tesseract-OCR\tesseract.exe"

# 🧠 Memoria para cada archivo por usuario
user_files_memory = {}

# 📎 Comando /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🤖 ¡Hola! Soy tu bot con OCR + Gemini. Puedes enviarme imágenes o PDFs para analizarlos.")

# 📂 Procesar archivos (PDF o imágenes)
async def handle_file(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.message
    user_id = message.from_user.id

    try:
        # 📝 Detectar tipo de archivo
        if message.document:
            file_info = await context.bot.get_file(message.document.file_id)
            file_bytes = await file_info.download_as_bytearray()
            file_name = message.document.file_name
        elif message.photo:
            photo = message.photo[-1]  # mayor resolución
            file_info = await context.bot.get_file(photo.file_id)
            file_bytes = await file_info.download_as_bytearray()
            file_name = f"photo_{message.message_id}.jpg"
        else:
            await message.reply_text("⚠️ Archivo no compatible.")
            return

        await message.reply_text("📥 Analizando archivo...")

        # 🧠 Extraer texto dependiendo del tipo de archivo
        extracted_text = ""
        if file_name.lower().endswith(".pdf"):
            images = convert_from_bytes(file_bytes)
            for img in images:
                text = pytesseract.image_to_string(img)
                extracted_text += text + "\n"
        elif file_name.lower().endswith((".jpg", ".jpeg", ".png")) or "photo_" in file_name:
            image = Image.open(io.BytesIO(file_bytes))
            extracted_text = pytesseract.image_to_string(image)
        else:
            extracted_text = "⚠️ Formato de archivo no compatible para OCR."

        # 💾 Guardar en memoria por usuario
        if user_id not in user_files_memory:
            user_files_memory[user_id] = []
        user_files_memory[user_id].append({
            "file_name": file_name,
            "content": extracted_text.strip()
        })

        await message.reply_text(f"✅ Archivo analizado: *{file_name}*\n\nHazme cualquier pregunta sobre el contenido.",
                                 parse_mode="Markdown")

    except Exception as e:
        await message.reply_text(f"❌ Error al procesar el archivo:\n{e}")

# 💬 Procesar mensajes normales
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    user_text = update.message.text.strip()

    if not user_text:
        await update.message.reply_text("❗ Por favor, envía un mensaje válido.")
        return

    # 🧠 Verifica si hay memoria OCR previa
    context_text = ""
    if user_id in user_files_memory:
        for item in user_files_memory[user_id]:
            context_text += f"\n[📄 {item['file_name']}]\n{item['content']}\n"

    try:
        prompt = f"{context_text}\n\nPregunta del usuario: {user_text}"
        response = model.generate_content(prompt)
        reply = response.text if hasattr(response, 'text') else str(response)
        await update.message.reply_text(reply[:4000])  # evitar límite de Telegram
    except Exception as e:
        await update.message.reply_text(f"❌ Error al generar respuesta:\n{e}")

# 🗑️ Comando para borrar la memoria
async def borrar_chat(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    user_files_memory[user_id] = []
    await update.message.reply_text("🗑️ Se ha borrado toda tu memoria de archivos. Puedes empezar desde cero.")

# 🚀 Ejecutar bot
if __name__ == "__main__":
    app = ApplicationBuilder().token(TELEGRAM_API_KEY).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("borrar", borrar_chat))
    app.add_handler(MessageHandler(filters.Document.ALL | filters.PHOTO, handle_file))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    print("🤖 Bot Gemini-OCR está activo...")
    app.run_polling()
