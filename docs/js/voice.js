// ── Web Speech API ────────────────────────────────────────────────────────────

const SpeechRecognitionAPI = window.SpeechRecognition || window.webkitSpeechRecognition;
let _recognition = null;
let _isRecording = false;

// Callbacks configurables desde app.js
const Voice = {
    onResult: null,   // function(texto)
    onError: null,    // function(mensajeError)
    onStart: null,    // function()
    onEnd: null,      // function()

    get isSupported() {
        return !!SpeechRecognitionAPI;
    },

    get isRecording() {
        return _isRecording;
    },

    init() {
        if (!SpeechRecognitionAPI) return false;
        _recognition = new SpeechRecognitionAPI();
        _recognition.lang = "es-PE";
        _recognition.continuous = false;
        _recognition.interimResults = false;
        _recognition.maxAlternatives = 1;

        _recognition.onresult = (e) => {
            const texto = e.results[0][0].transcript.trim();
            _isRecording = false;
            if (Voice.onEnd) Voice.onEnd();
            if (Voice.onResult) Voice.onResult(texto);
        };

        _recognition.onerror = (e) => {
            _isRecording = false;
            if (Voice.onEnd) Voice.onEnd();
            let msg = "Error de voz.";
            if (e.error === "no-speech")    msg = "No se detectó voz. Intenta de nuevo.";
            if (e.error === "not-allowed")  msg = "Permiso de micrófono denegado. Ve a Ajustes → Chrome → Micrófono y actívalo.";
            if (e.error === "network")      msg = "Sin conexión a internet. El reconocimiento de voz necesita internet.";
            if (e.error === "aborted")      return; // cancelado manualmente, no mostrar error
            if (Voice.onError) Voice.onError(msg);
        };

        _recognition.onend = () => {
            if (_isRecording) {
                // Fue cortado antes de obtener resultado — no había voz
                _isRecording = false;
                if (Voice.onEnd) Voice.onEnd();
            }
        };

        return true;
    },

    start() {
        if (!_recognition && !Voice.init()) {
            if (Voice.onError) Voice.onError("Tu navegador no soporta reconocimiento de voz. Usa Chrome en Android.");
            return;
        }
        if (_isRecording) return;
        try {
            _isRecording = true;
            _recognition.start();
            if (Voice.onStart) Voice.onStart();
        } catch (e) {
            _isRecording = false;
            // Reiniciar reconocedor si ya estaba activo
            Voice.init();
        }
    },

    stop() {
        if (_recognition && _isRecording) {
            _recognition.stop();
        }
    },
};
