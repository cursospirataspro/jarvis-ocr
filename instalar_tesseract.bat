@echo off
setlocal enabledelayedexpansion

echo 🟡 Descargando Tesseract OCR 5.5...
curl -L -o tesseract-installer.exe "https://github.com/tesseract-ocr/tesseract/releases/download/5.5.0/tesseract-ocr-w64-setup-5.5.0.20241111.exe"

echo 🟢 Instalando Tesseract silenciosamente...
start /wait tesseract-installer.exe /SILENT

echo 🔍 Buscando ubicación de tesseract.exe...

set "tesseract_path="
for %%f in ("C:\Program Files\Tesseract-OCR\tesseract.exe" "C:\Program Files (x86)\Tesseract-OCR\tesseract.exe" "%ProgramFiles%\Tesseract-OCR\tesseract.exe") do (
    if exist "%%~f" (
        set "tesseract_path=%%~f"
        goto found
    )
)

:found
if defined tesseract_path (
    echo ✅ Tesseract instalado exitosamente en:
    echo !tesseract_path!
    echo.
    echo Copia esta ruta y pégala en tu script de Python:
    echo.
    echo pytesseract.pytesseract.tesseract_cmd = "!tesseract_path!"
) else (
    echo ❌ No se encontró tesseract.exe. Revisa si la instalación fue correcta.
)

pause
exit
