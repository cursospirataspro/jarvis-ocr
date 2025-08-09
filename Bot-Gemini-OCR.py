import os
import io
import fitz  # PyMuPDF
import pytesseract
from PIL import Image
from pdf2image import convert_from_bytes
from telegram import Update, InputFile, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.constants import ChatAction  # ✅ Corrección aquí
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    filters,
    ContextTypes,
    CallbackQueryHandler,
)
from google.generativeai import configure, GenerativeModel

# 🔐 Credenciales
TELEGRAM_API_KEY = "7606439237:AAEx1gU7OOi3-WZn39103Xq5BeeTua6z-D8"
GEMINI_API_KEY = "AIzaSyAQOnN-SaPw-Tn3gQDl-pp-_OCR5FkR4Fk"
GEMINI_MODEL = "models/gemini-2.5-flash"

# Configurar Gemini
configure(api_key=GEMINI_API_KEY)
model = GenerativeModel(GEMINI_MODEL)

# Ruta de Tesseract
pytesseract.pytesseract.tesseract_cmd = r"C:\Users\Hunter Garcia\AppData\Local\Programs\Tesseract-OCR\tesseract.exe"

# Memoria de archivos
user_files_memory = {}

# Diccionario de palabras clave para activar búsqueda en web
busqueda_keywords = ["buscar", "investiga", "encuentra", "info", "información", "necesito", "hallar", "dime", "consulta"]

# 🧠 Menú de botones
def obtener_menu():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🧠 Hablar con Jarvis", callback_data="jarvis")],
        [InlineKeyboardButton("🖼️ Analizar imágenes", callback_data="imagen")],
        [InlineKeyboardButton("📄 Analizar documentos", callback_data="documento")],
        [InlineKeyboardButton("🌐 Buscar en la web", callback_data="buscar")],
        [InlineKeyboardButton("🗑️ Borrar datos", callback_data="borrar")]
    ])

# Comando /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 ¡Hola! Bienvenido.\nEstoy listo para ayudarte. ¿Qué deseas hacer?",
        reply_markup=obtener_menu()
    )

# Comando /menu o /menú
async def show_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("📋 Elige una opción:", reply_markup=obtener_menu())

# Borrar memoria
async def borrar_chat(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user_files_memory[user_id] = []
    await update.message.reply_text("🗑️ Tu historial de archivos ha sido borrado.")

# Callback para botones
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    data = query.data
    if data == "jarvis":
        await query.edit_message_text("🎤 Puedes hablarme como Jarvis, ¿en qué te ayudo?")
    elif data == "imagen":
        await query.edit_message_text("📸 Envíame una imagen para analizar.")
    elif data == "documento":
        await query.edit_message_text("📄 Envíame un documento PDF para analizar.")
    elif data == "buscar":
        await query.edit_message_text("🔍 ¿Qué deseas que busque en la web?")
    elif data == "borrar":
        user_id = update.effective_user.id
        user_files_memory[user_id] = []
        await query.edit_message_text("🗑️ Todos tus datos fueron borrados.")

# Procesar archivo
async def handle_file(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.message
    user_id = message.from_user.id

    try:
        if message.document:
            file_info = await context.bot.get_file(message.document.file_id)
            file_bytes = await file_info.download_as_bytearray()
            file_name = message.document.file_name
        elif message.photo:
            photo = message.photo[-1]
            file_info = await context.bot.get_file(photo.file_id)
            file_bytes = await file_info.download_as_bytearray()
            file_name = f"photo_{message.message_id}.jpg"
        else:
            await message.reply_text("⚠️ Solo se aceptan imágenes o documentos PDF.")
            return

        await message.reply_text("📥 Analizando archivo...")

        extracted_text = ""
        if file_name.lower().endswith(".pdf"):
            images = convert_from_bytes(file_bytes, poppler_path=r"C:\poppler\Library\bin")
            for img in images:
                text = pytesseract.image_to_string(img)
                extracted_text += text + "\n"
        elif file_name.lower().endswith((".jpg", ".jpeg", ".png")) or "photo_" in file_name:
            image = Image.open(io.BytesIO(file_bytes))
            extracted_text = pytesseract.image_to_string(image)
        else:
            extracted_text = "⚠️ No es un archivo compatible."

        if user_id not in user_files_memory:
            user_files_memory[user_id] = []

        user_files_memory[user_id].append({
            "file_name": file_name,
            "content": extracted_text.strip()
        })

        await message.reply_text(
            f"✅ *{file_name}* analizado.\nAhora puedes hacer preguntas sobre su contenido.",
            parse_mode="Markdown"
        )

    except Exception as e:
        await message.reply_text(f"❌ Error al procesar el archivo:\n{e}")

# Procesar mensajes normales
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    text = update.message.text.strip()

    if not text:
        await update.message.reply_text("❗ Por favor, escribe algo.")
        return

    await context.bot.send_chat_action(chat_id=update.effective_chat.id, action=ChatAction.TYPING)

    # ¿Es una búsqueda web?
    if any(text.lower().startswith(kw) for kw in busqueda_keywords):
        prompt = f"Busca en Internet y responde en español a lo siguiente:\n\n{text}"
    else:
        context_text = ""
        if user_id in user_files_memory:
            for item in user_files_memory[user_id]:
                context_text += f"[📄 {item['file_name']}]\n{item['content']}\n"
        prompt = f"{context_text}\n\nUsuario pregunta: {text}"

    try:
        respuesta = model.generate_content(prompt)
        final_text = respuesta.text if hasattr(respuesta, 'text') else str(respuesta)
        await update.message.reply_text(final_text[:4000])
    except Exception as e:
        await update.message.reply_text(f"❌ Error al responder:\n{e}")

# Ejecutar bot
if __name__ == "__main__":
    app = ApplicationBuilder().token(TELEGRAM_API_KEY).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler(["menu"], show_menu))
    app.add_handler(CommandHandler("borrar", borrar_chat))
    app.add_handler(CallbackQueryHandler(button_handler))
    app.add_handler(MessageHandler(filters.Document.ALL | filters.PHOTO, handle_file))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    print("🤖 Bot Gemini-OCR está activo...")
    app.run_polling()
