// ── Configuración de Supabase ─────────────────────────────────────────────────
// Las credenciales se cargan desde localStorage (guardadas en la pantalla de setup)
// o desde las constantes de abajo si ya las tienes.
//
// Para configurar manualmente, reemplaza los valores:
const SUPABASE_URL  = localStorage.getItem("sb_url")  || "https://gvqnhmpcnjxlnumlrmce.supabase.co";
const SUPABASE_KEY  = localStorage.getItem("sb_key")  || "sb_publishable__GLMZus6oZBOjqPebPPl5w_IOGAAYB7";

// Cliente de Supabase (se inicializa después de cargar el SDK)
let supabaseClient = null;

function initSupabase() {
    if (typeof window.supabase === "undefined") {
        console.error("Supabase SDK no cargado.");
        return false;
    }
    if (SUPABASE_URL === "TU_URL_AQUI" || SUPABASE_KEY === "TU_ANON_KEY_AQUI") {
        return false; // Fuerza pantalla de setup
    }
    supabaseClient = window.supabase.createClient(SUPABASE_URL, SUPABASE_KEY);
    return true;
}

function getClient() {
    if (!supabaseClient) initSupabase();
    return supabaseClient;
}
