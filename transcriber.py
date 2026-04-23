import os
import speech_recognition as sr


def transcribir_audio(ruta_wav: str) -> str | None:
    """
    Transcribe un archivo WAV usando Google Speech Recognition (gratis, sin API key).
    """
    recognizer = sr.Recognizer()

    try:
        with sr.AudioFile(ruta_wav) as source:
            audio = recognizer.record(source)

        texto = recognizer.recognize_google(audio, language="es-PE")
        texto = texto.strip()
        if not texto:
            return None
        return texto

    except sr.UnknownValueError:
        return None
    except sr.RequestError as e:
        print(f"  Error de conexión con Google Speech: {e}")
        return None
    except Exception as e:
        print(f"  Error al transcribir: {e}")
        return None
    finally:
        try:
            os.unlink(ruta_wav)
        except OSError:
            pass
