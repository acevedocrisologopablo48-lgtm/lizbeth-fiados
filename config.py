import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

# Ruta base del proyecto
BASE_DIR = Path(__file__).parent

# Archivo Excel
EXCEL_PATH = BASE_DIR / "ventas_fiado.xlsx"
SHEET_NAME = "Registro"

# OpenAI
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")

# Audio
SAMPLE_RATE = 16000  # Hz, óptimo para Whisper
SILENCE_THRESHOLD = 0.01  # Umbral RMS para detectar silencio
SILENCE_DURATION = 2.0  # Segundos de silencio para detener grabación
MAX_RECORD_SECONDS = 15  # Máximo de grabación por dictado

# Formato
DATE_FORMAT = "%d/%m/%Y"

# Palabras que se ignoran al extraer el nombre
STOP_WORDS = {
    "anota", "pon", "ponle", "apunta", "registra", "cobra",
    "para", "de", "del", "a", "al", "el", "la", "los", "las",
    "un", "una", "uno", "unos", "unas",
    "sol", "soles", "con", "y", "pesos", "peso",
    "cincuenta", "cero", "dos", "tres", "cuatro", "cinco",
    "seis", "siete", "ocho", "nueve", "diez",
    "once", "doce", "trece", "catorce", "quince",
    "veinte", "treinta", "cuarenta", "sesenta", "setenta",
    "ochenta", "noventa", "cien", "medio", "media",
    "centavos", "centavo",
}

# Mapeo de texto a números
NUMBER_WORDS = {
    "cero": 0, "un": 1, "uno": 1, "una": 1,
    "dos": 2, "tres": 3, "cuatro": 4, "cinco": 5,
    "seis": 6, "siete": 7, "ocho": 8, "nueve": 9,
    "diez": 10, "once": 11, "doce": 12, "trece": 13,
    "catorce": 14, "quince": 15, "veinte": 20,
    "treinta": 30, "cuarenta": 40, "cincuenta": 50,
    "sesenta": 60, "setenta": 70, "ochenta": 80,
    "noventa": 90, "cien": 100, "medio": 50, "media": 50,
}
