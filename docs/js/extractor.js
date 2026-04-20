// ── Port exacto de entity_extractor.py ───────────────────────────────────────
// Extrae (nombre, monto) de texto dictado en español.

const NUMBER_WORDS = {
    "cero": 0, "un": 1, "uno": 1, "una": 1,
    "dos": 2, "tres": 3, "cuatro": 4, "cinco": 5,
    "seis": 6, "siete": 7, "ocho": 8, "nueve": 9,
    "diez": 10, "once": 11, "doce": 12, "trece": 13,
    "catorce": 14, "quince": 15, "veinte": 20,
    "treinta": 30, "cuarenta": 40, "cincuenta": 50,
    "sesenta": 60, "setenta": 70, "ochenta": 80,
    "noventa": 90, "cien": 100, "medio": 50, "media": 50,
};

const STOP_WORDS = new Set([
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
]);

const MONETARY_WORDS = new Set(["sol", "soles", "peso", "pesos", "centavo", "centavos"]);
const SEPARATOR_WORDS = new Set(["con", "y", "punto"]);

function removeAccents(text) {
    return text.normalize("NFD").replace(/[\u0300-\u036f]/g, "");
}

function textToNumber(words) {
    if (!words || words.length === 0) return null;

    const cleaned = words.map(w => removeAccents(w));

    const partsBeforeSep = [];
    const partsAfterSep = [];
    let foundSeparator = false;

    for (const w of cleaned) {
        if (MONETARY_WORDS.has(w)) continue;
        if (SEPARATOR_WORDS.has(w)) { foundSeparator = true; continue; }
        if (foundSeparator) partsAfterSep.push(w);
        else partsBeforeSep.push(w);
    }

    // Calcular parte entera
    let integerPart = 0;
    if (partsBeforeSep.length > 0) {
        for (const w of partsBeforeSep) {
            const val = NUMBER_WORDS[w];
            if (val === undefined) return null;
            integerPart += val;
        }
    }

    // Calcular parte decimal
    let decimalPart = 0;
    if (partsAfterSep.length > 0) {
        for (const w of partsAfterSep) {
            const val = NUMBER_WORDS[w];
            if (val === undefined) return null;
            decimalPart += val;
        }
    }

    let result;
    if (foundSeparator) {
        if (decimalPart >= 1) decimalPart = decimalPart / 100.0;
        result = integerPart + decimalPart;
    } else {
        if (partsBeforeSep.length >= 2) {
            const lastWord = partsBeforeSep[partsBeforeSep.length - 1];
            const lastVal = NUMBER_WORDS[lastWord] || 0;
            const restWords = partsBeforeSep.slice(0, -1);
            const restVal = restWords.reduce((s, w) => s + (NUMBER_WORDS[w] || 0), 0);
            if (restVal > 0 && lastVal >= 10 && lastVal <= 99) {
                result = restVal + lastVal / 100.0;
            } else {
                result = integerPart;
            }
        } else {
            if (partsBeforeSep[0] === "medio" || partsBeforeSep[0] === "media") {
                result = 0.50;
            } else {
                result = integerPart;
            }
        }
    }

    return result > 0 ? Math.round(result * 100) / 100 : null;
}

function extraerDatos(texto) {
    texto = texto.trim();
    if (!texto) return { nombre: null, monto: null };

    let monto = null;
    let textoLimpio = texto;

    // Fase A: número decimal directo (3.50, 3,50)
    const matchDecimal = texto.match(/(\d+)[.,](\d{1,2})/);
    if (matchDecimal) {
        const decimal = matchDecimal[2].padEnd(2, "0");
        monto = parseFloat(`${matchDecimal[1]}.${decimal}`);
        textoLimpio = texto.replace(matchDecimal[0], " ");
    }

    // Fase A2: número entero solo (Pedro 2 soles)
    if (monto === null) {
        const matchInt = textoLimpio.match(/\b(\d+)\b/);
        if (matchInt) {
            monto = parseFloat(matchInt[1]);
            textoLimpio = textoLimpio.replace(matchInt[0], " ");
        }
    }

    // Fase B: palabras numéricas
    const words = textoLimpio.toLowerCase().split(/\s+/).filter(Boolean);
    const wordsNoAccent = words.map(removeAccents);

    if (monto === null) {
        const numWords = wordsNoAccent.filter(w =>
            NUMBER_WORDS[w] !== undefined ||
            MONETARY_WORDS.has(w) ||
            SEPARATOR_WORDS.has(w)
        );
        if (numWords.length > 0) {
            monto = textToNumber(numWords);
        }
    }

    // Fase C: extraer nombre
    const originalWords = textoLimpio.toLowerCase().split(/\s+/).filter(Boolean);
    const nameParts = [];

    for (const w of originalWords) {
        const wClean = removeAccents(w);
        if (STOP_WORDS.has(wClean)) continue;
        if (SEPARATOR_WORDS.has(wClean)) continue;
        if (/^\d+[.,]?\d*$/.test(w)) continue;
        if (/^s\/\.?$/.test(w)) continue;
        nameParts.push(w);
    }

    let nombre = null;
    if (nameParts.length > 0) {
        nombre = nameParts
            .join(" ")
            .trim()
            .replace(/[,;.!?]+$/, "")
            .trim();
        // Capitalizar cada palabra
        nombre = nombre.replace(/\b\w/g, c => c.toUpperCase());
        if (nombre === "") nombre = null;
    }

    return { nombre, monto };
}
