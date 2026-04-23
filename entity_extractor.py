import re
import unicodedata

from config import NUMBER_WORDS, STOP_WORDS


def _remove_accents(text: str) -> str:
    """Quita tildes para comparación."""
    nfkd = unicodedata.normalize("NFKD", text)
    return "".join(c for c in nfkd if not unicodedata.combining(c))


def _text_to_number(words: list[str]) -> float | None:
    """
    Convierte una lista de palabras numéricas a un float.
    Ejemplos:
        ["tres", "cincuenta"] -> 3.50
        ["un", "sol", "con", "cincuenta"] -> 1.50
        ["dos", "soles"] -> 2.00
        ["tres", "con", "cincuenta"] -> 3.50
        ["uno", "cincuenta"] -> 1.50
        ["medio"] -> 0.50
        ["quince"] -> 15.00
    """
    if not words:
        return None

    # Limpiar palabras monetarias y conectores
    cleaned = [_remove_accents(w) for w in words]

    # Filtrar "sol", "soles", "centavos"
    monetary = {"sol", "soles", "peso", "pesos", "centavo", "centavos"}
    separators = {"con", "y", "punto"}

    parts_before_sep = []
    parts_after_sep = []
    found_separator = False

    for w in cleaned:
        if w in monetary:
            continue
        if w in separators:
            found_separator = True
            continue
        if found_separator:
            parts_after_sep.append(w)
        else:
            parts_before_sep.append(w)

    # Calcular parte entera
    integer_part = 0.0
    if parts_before_sep:
        for w in parts_before_sep:
            val = NUMBER_WORDS.get(w)
            if val is not None:
                integer_part += val
            else:
                return None  # Palabra no reconocida

    # Calcular parte decimal
    decimal_part = 0.0
    if parts_after_sep:
        for w in parts_after_sep:
            val = NUMBER_WORDS.get(w)
            if val is not None:
                decimal_part += val
            else:
                return None

    if found_separator:
        # "tres con cincuenta" -> 3 + 0.50
        # decimal_part se interpreta como centavos si >= 1
        if decimal_part >= 1:
            decimal_part = decimal_part / 100.0
        result = integer_part + decimal_part
    else:
        # Sin separador: decidir si es "tres cincuenta" (3.50) o "quince" (15)
        if len(parts_before_sep) >= 2:
            # El último podría ser centavos: "tres cincuenta" -> 3 + 0.50
            last_word = parts_before_sep[-1]
            last_val = NUMBER_WORDS.get(last_word, 0)
            rest_words = parts_before_sep[:-1]

            # Si la última palabra vale >=10 y hay palabras antes que valen <100
            # probablemente es formato "X centavos"
            rest_val = sum(NUMBER_WORDS.get(w, 0) for w in rest_words)
            if rest_val > 0 and 10 <= last_val <= 99:
                result = rest_val + last_val / 100.0
            else:
                result = integer_part
        else:
            # Una sola palabra: "medio" -> 0.50, "cinco" -> 5.00
            if parts_before_sep and parts_before_sep[0] in ("medio", "media"):
                result = 0.50
            else:
                result = integer_part

    return round(result, 2) if result > 0 else None


def extraer_datos(texto: str) -> tuple[str | None, float | None]:
    """
    Extrae (nombre, monto) de un texto dictado.

    Maneja formatos como:
        "Carlos tres cincuenta" -> ("Carlos", 3.50)
        "Anota tres cincuenta para Carlos" -> ("Carlos", 3.50)
        "Luis 3.50" -> ("Luis", 3.50)
        "Un sol con cincuenta para María" -> ("María", 1.50)
        "Pedro 2 soles" -> ("Pedro", 2.00)
        "Ana medio sol" -> ("Ana", 0.50)
    """
    texto = texto.strip()
    if not texto:
        return None, None

    # Paso 1: Buscar números directos (3.50, 3,50, 3.5)
    monto = None
    texto_limpio = texto

    # Patrón para números decimales
    match_decimal = re.search(r'(\d+)[.,](\d{1,2})', texto)
    if match_decimal:
        entero = match_decimal.group(1)
        decimal = match_decimal.group(2).ljust(2, '0')
        monto = float(f"{entero}.{decimal}")
        texto_limpio = texto[:match_decimal.start()] + texto[match_decimal.end():]

    # Patrón para números enteros solos (ej: "Pedro 2 soles", "Ana 5")
    if monto is None:
        match_int = re.search(r'\b(\d+)\b', texto)
        if match_int:
            monto = float(match_int.group(1))
            texto_limpio = texto[:match_int.start()] + texto[match_int.end():]

    # Paso 2: Si no hay número directo, buscar texto numérico
    words = texto_limpio.lower().split()
    words_no_accent = [_remove_accents(w) for w in words]

    if monto is None:
        # Identificar las palabras numéricas
        num_words = []
        for w in words_no_accent:
            if w in NUMBER_WORDS or w in {"con", "y", "sol", "soles", "punto",
                                           "peso", "pesos", "centavo", "centavos"}:
                num_words.append(w)

        if num_words:
            monto = _text_to_number(num_words)

    # Paso 3: Extraer el nombre
    # El nombre es todo lo que no es número, palabra monetaria o stop word
    name_parts = []
    for i, w in enumerate(words):
        w_clean = _remove_accents(w.lower())
        # Saltar si es stop word, número textual, o signo
        if w_clean in STOP_WORDS:
            continue
        if w_clean in {"con", "y", "punto", "centavo", "centavos"}:
            continue
        # Saltar si es dígito
        if re.match(r'^\d+[.,]?\d*$', w):
            continue
        # Saltar "s/" o similar
        if re.match(r'^s/\.?$', w.lower()):
            continue
        name_parts.append(w)

    nombre = None
    if name_parts:
        nombre = " ".join(name_parts).strip().title()
        # Limpiar puntuación residual
        nombre = re.sub(r'[,;.!?]+$', '', nombre).strip()

    if nombre == "":
        nombre = None

    return nombre, monto
