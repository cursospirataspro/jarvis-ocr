import google.generativeai as genai

# Reemplaza aquí con tu clave de Gemini
GEMINI_API_KEY = "AIzaSyAQOnN-SaPw-Tn3gQDl-pp-_OCR5FkR4Fk"

# Configura la clave
genai.configure(api_key=GEMINI_API_KEY)

# Lista todos los modelos disponibles para esta cuenta
modelos = genai.list_models()

# Mostrar nombres y características
for modelo in modelos:
    print("Nombre del modelo:", modelo.name)
    if "generateContent" in modelo.supported_generation_methods:
        print("✔️ Este modelo soporta generateContent (sirve para tu bot)")
    print()
