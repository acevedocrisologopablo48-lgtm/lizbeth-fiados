import io
import tempfile
import numpy as np
import sounddevice as sd
from scipy.io.wavfile import write as wav_write

from config import SAMPLE_RATE, SILENCE_THRESHOLD, SILENCE_DURATION, MAX_RECORD_SECONDS


def grabar_audio() -> str | None:
    """
    Graba audio desde el micrófono hasta detectar silencio o alcanzar el máximo.
    Retorna la ruta del archivo .wav temporal, o None si no se grabó nada útil.
    """
    print("  🎙️  Escuchando... (habla ahora, se detendrá al detectar silencio)")

    chunk_duration = 0.1  # Leer en bloques de 100ms
    chunk_samples = int(SAMPLE_RATE * chunk_duration)
    silence_chunks = int(SILENCE_DURATION / chunk_duration)
    max_chunks = int(MAX_RECORD_SECONDS / chunk_duration)

    audio_chunks = []
    silent_count = 0
    has_speech = False

    try:
        with sd.InputStream(samplerate=SAMPLE_RATE, channels=1, dtype="float32") as stream:
            for _ in range(max_chunks):
                data, _ = stream.read(chunk_samples)
                audio_chunks.append(data.copy())

                # Calcular nivel de energía (RMS)
                rms = np.sqrt(np.mean(data ** 2))

                if rms > SILENCE_THRESHOLD:
                    has_speech = True
                    silent_count = 0
                else:
                    silent_count += 1

                # Si ya hubo habla y ahora hay silencio prolongado, parar
                if has_speech and silent_count >= silence_chunks:
                    break

    except sd.PortAudioError as e:
        print(f"  ❌ Error de audio: {e}")
        print("     Verifica que tengas un micrófono conectado.")
        return None
    except Exception as e:
        print(f"  ❌ Error inesperado al grabar: {e}")
        return None

    if not has_speech:
        print("  ⚠️  No se detectó voz.")
        return None

    # Concatenar y guardar como WAV temporal
    audio = np.concatenate(audio_chunks, axis=0)
    audio_int16 = np.int16(audio * 32767)

    tmp = tempfile.NamedTemporaryFile(suffix=".wav", delete=False)
    wav_write(tmp.name, SAMPLE_RATE, audio_int16)
    tmp.close()

    print("  ✅ Audio capturado.")
    return tmp.name
