// ── Lógica principal de la aplicación ────────────────────────────────────────

// ── Estado global ─────────────────────────────────────────────────────────────
const State = {
    currentTab: "dia",
    selectedName: null,
    pendingNombre: null,
    pendingMonto: null,
    sheetMode: null,    // "confirm" | "ask-nombre" | "ask-monto" | "corregir" | "borrar"
    askCallback: null,
};

// ── Inicialización ────────────────────────────────────────────────────────────
document.addEventListener("DOMContentLoaded", () => {
    // Verificar configuración Supabase
    if (SUPABASE_URL === "TU_URL_AQUI" || SUPABASE_KEY === "TU_ANON_KEY_AQUI") {
        showSetupScreen();
        return;
    }

    if (!initSupabase()) {
        showToast("Error al conectar con la base de datos.", "error");
        return;
    }

    setupVoice();
    setupManualInput();
    setupSwipeToDelete();
    refreshTable();
});

// ── Pantalla de configuración ─────────────────────────────────────────────────
function showSetupScreen() {
    document.getElementById("appMain").classList.add("hidden");
    document.getElementById("setupScreen").classList.remove("hidden");

    document.getElementById("btnSaveSetup").addEventListener("click", () => {
        const url = document.getElementById("inputSupabaseUrl").value.trim();
        const key = document.getElementById("inputSupabaseKey").value.trim();
        if (!url || !key) { showToast("Completa ambos campos.", "warning"); return; }
        localStorage.setItem("sb_url", url);
        localStorage.setItem("sb_key", key);
        showToast("✅ Configuración guardada. Recargando...", "success");
        setTimeout(() => location.reload(), 1200);
    });

    // Cargar valores guardados si existen
    const savedUrl = localStorage.getItem("sb_url");
    const savedKey = localStorage.getItem("sb_key");
    if (savedUrl) document.getElementById("inputSupabaseUrl").value = savedUrl;
    if (savedKey) document.getElementById("inputSupabaseKey").value = savedKey;
}

// ── Voz ───────────────────────────────────────────────────────────────────────
function setupVoice() {
    Voice.onStart = () => {
        const btn = document.getElementById("voiceBtn");
        btn.classList.replace("idle", "recording");
        document.getElementById("voiceLabel").textContent = "GRABANDO...";
    };
    Voice.onEnd = () => {
        const btn = document.getElementById("voiceBtn");
        btn.classList.replace("recording", "idle");
        document.getElementById("voiceLabel").textContent = "DICTAR VENTA";
    };
    Voice.onResult = (texto) => {
        showToast(`🎙️ Escuché: "${texto}"`, "info");
        processText(texto);
    };
    Voice.onError = (msg) => {
        showToast(msg, "error");
    };
}

function onVoiceClick() {
    if (Voice.isRecording) { Voice.stop(); return; }
    Voice.start();
}

// ── Entrada manual ────────────────────────────────────────────────────────────
function setupManualInput() {
    const input = document.getElementById("manualInput");
    input.addEventListener("keydown", (e) => {
        if (e.key === "Enter") {
            e.preventDefault();
            submitManual();
        }
    });
}

function submitManual() {
    const input = document.getElementById("manualInput");
    const texto = input.value.trim();
    if (!texto) return;
    processText(texto);
    input.value = "";
}

// ── Procesar texto (voz o manual) ─────────────────────────────────────────────
function processText(texto) {
    const { nombre, monto } = extraerDatos(texto);

    if (!nombre && !monto) {
        showToast('No entendí. Intenta: "Carlos 3.50"', "error");
        return;
    }

    if (!nombre) {
        openSheet("ask-nombre", { monto, callback: (n) => showConfirm(n, monto) });
        return;
    }
    if (!monto) {
        openSheet("ask-monto", { nombre, callback: (m) => showConfirm(nombre, m) });
        return;
    }

    showConfirm(nombre, monto);
}

// ── Confirmar registro ────────────────────────────────────────────────────────
function showConfirm(nombre, monto) {
    State.pendingNombre = nombre;
    State.pendingMonto = monto;
    document.getElementById("sheetTitle").textContent = "¿Registrar esta venta?";
    document.getElementById("sheetDetail").textContent = `${nombre}  →  S/ ${monto.toFixed(2)}`;
    document.getElementById("sheetDetail").classList.remove("hidden");
    document.getElementById("sheetInput").classList.add("hidden");
    document.getElementById("sheetHint").classList.add("hidden");
    document.getElementById("btnSheetConfirm").textContent = "✅ Sí, registrar";
    document.getElementById("btnSheetConfirm").className = "btn-confirm";
    State.sheetMode = "confirm";
    openOverlay();
}

// ── Corregir ──────────────────────────────────────────────────────────────────
function onCorregir() {
    if (!State.selectedName) { showToast("Toca primero un nombre de la lista.", "error"); return; }
    document.getElementById("sheetTitle").textContent = `✏️ Corregir monto de ${State.selectedName}`;
    document.getElementById("sheetDetail").classList.add("hidden");
    const inp = document.getElementById("sheetInput");
    inp.value = "";
    inp.type = "number";
    inp.inputMode = "decimal";
    inp.placeholder = "Nuevo monto (ej: 3.50)";
    inp.classList.remove("hidden");
    document.getElementById("sheetHint").textContent = "El monto anterior será reemplazado";
    document.getElementById("sheetHint").classList.remove("hidden");
    document.getElementById("btnSheetConfirm").textContent = "Guardar";
    document.getElementById("btnSheetConfirm").className = "btn-confirm";
    State.sheetMode = "corregir";
    openOverlay();
    setTimeout(() => inp.focus(), 350);
}

// ── Borrar ────────────────────────────────────────────────────────────────────
function onBorrar() {
    if (!State.selectedName) { showToast("Toca primero un nombre de la lista.", "error"); return; }
    document.getElementById("sheetTitle").textContent = `🗑️ Eliminar a ${State.selectedName}`;
    document.getElementById("sheetDetail").textContent = `¿Seguro que quieres borrar\n el registro de hoy?`;
    document.getElementById("sheetDetail").classList.remove("hidden");
    document.getElementById("sheetInput").classList.add("hidden");
    document.getElementById("sheetHint").classList.add("hidden");
    document.getElementById("btnSheetConfirm").textContent = "Sí, eliminar";
    document.getElementById("btnSheetConfirm").className = "btn-confirm-red";
    State.sheetMode = "borrar";
    openOverlay();
}

// ── Preguntar dato faltante ───────────────────────────────────────────────────
function openSheet(mode, { monto, nombre, callback }) {
    State.sheetMode = mode;
    State.askCallback = callback;

    const inp = document.getElementById("sheetInput");
    document.getElementById("sheetDetail").classList.add("hidden");
    inp.classList.remove("hidden");
    inp.value = "";

    if (mode === "ask-nombre") {
        document.getElementById("sheetTitle").textContent = "¿Para quién es?";
        document.getElementById("sheetHint").textContent = `Monto detectado: S/ ${monto.toFixed(2)}`;
        inp.type = "text";
        inp.inputMode = "text";
        inp.placeholder = "Escribe el nombre";
    } else if (mode === "ask-monto") {
        document.getElementById("sheetTitle").textContent = "¿Cuánto fue?";
        document.getElementById("sheetHint").textContent = `Nombre: ${nombre}`;
        inp.type = "number";
        inp.inputMode = "decimal";
        inp.placeholder = "Monto (ej: 3.50)";
    }

    document.getElementById("sheetHint").classList.remove("hidden");
    document.getElementById("btnSheetConfirm").textContent = "Continuar";
    document.getElementById("btnSheetConfirm").className = "btn-confirm";
    openOverlay();
    setTimeout(() => inp.focus(), 350);
}

// ── Confirmación del bottom sheet ────────────────────────────────────────────
async function onSheetConfirm() {
    const mode = State.sheetMode;

    if (mode === "confirm") {
        closeOverlay();
        await doRegister(State.pendingNombre, State.pendingMonto);

    } else if (mode === "ask-nombre") {
        const val = document.getElementById("sheetInput").value.trim();
        if (!val) { showToast("Escribe un nombre.", "warning"); return; }
        closeOverlay();
        State.askCallback(val);

    } else if (mode === "ask-monto") {
        const val = parseFloat(document.getElementById("sheetInput").value.replace(",", "."));
        if (isNaN(val) || val <= 0) { showToast("Monto inválido.", "warning"); return; }
        closeOverlay();
        State.askCallback(val);

    } else if (mode === "corregir") {
        const val = parseFloat(document.getElementById("sheetInput").value.replace(",", "."));
        if (isNaN(val) || val < 0) { showToast("Monto inválido.", "warning"); return; }
        closeOverlay();
        const result = await corregirMonto(State.selectedName, val);
        if (!result.ok) { showToast(result.error, "error"); return; }
        showToast(`✅ ${result.nombre}: S/ ${result.montoAnterior.toFixed(2)} → S/ ${result.nuevoMonto.toFixed(2)}`, "success");
        State.selectedName = null;
        updateActionBar();
        refreshTable();

    } else if (mode === "borrar") {
        closeOverlay();
        const result = await borrarEntrada(State.selectedName);
        if (!result.ok) { showToast(result.error, "error"); return; }
        showToast(`🗑️ ${result.nombre} eliminado.`, "success");
        State.selectedName = null;
        updateActionBar();
        refreshTable();
    }
}

// ── Registrar venta ───────────────────────────────────────────────────────────
async function doRegister(nombre, monto) {
    const result = await registrarVenta(nombre, monto);
    if (!result.ok) { showToast(result.error, "error"); return; }

    let msg;
    if (result.accion === "INSERT") {
        msg = `✅ ${result.nombre} registrado: S/ ${monto.toFixed(2)}`;
    } else {
        msg = `✅ ${result.nombre}: S/ ${result.montoAnterior.toFixed(2)} → S/ ${result.nuevoTotal.toFixed(2)}`;
    }
    showToast(msg, "success");
    await refreshTable(result.nombre);
}

// ── Tabs ──────────────────────────────────────────────────────────────────────
function switchTab(tab) {
    State.currentTab = tab;
    State.selectedName = null;
    updateActionBar();
    document.getElementById("tabDia").classList.toggle("active", tab === "dia");
    document.getElementById("tabSemanal").classList.toggle("active", tab === "semanal");
    refreshTable();
}

// ── Tabla ─────────────────────────────────────────────────────────────────────
async function refreshTable(flashName = null) {
    const wrap = document.getElementById("tableWrap");
    wrap.innerHTML = `<div style="text-align:center;padding:24px;"><span class="spinner"></span></div>`;

    let result;
    if (State.currentTab === "dia") {
        result = await obtenerResumenDia();
    } else {
        result = await obtenerResumenSemanal();
    }

    if (!result.ok) {
        wrap.innerHTML = `<div class="empty-state"><div class="empty-icon">⚠️</div><p>${result.error}</p></div>`;
        return;
    }

    const registros = result.registros;
    document.getElementById("totalLabel").textContent = State.currentTab === "dia" ? "Total del día" : "Total semanal";
    document.getElementById("totalValue").textContent = `S/ ${result.total.toFixed(2)}`;

    if (registros.length === 0) {
        wrap.innerHTML = `<div class="empty-state"><div class="empty-icon">🍽️</div><p>Aún no hay ventas ${State.currentTab === "dia" ? "hoy" : "esta semana"}.<br>¡Dicta la primera!</p></div>`;
        return;
    }

    let html = "";
    for (const r of registros) {
        const nombre = r.nombre;
        const isSelected = State.selectedName === nombre;
        const isNew = nombre === flashName;
        const selClass = isSelected ? " selected" : "";
        const newClass = isNew ? " new-entry" : "";

        const safeNombre = nombre.replace(/'/g, "\\'").replace(/"/g, "&quot;");

        if (State.currentTab === "dia") {
            html += `
            <div class="entry${selClass}${newClass}" onclick="selectEntry('${safeNombre}')">
                <div class="swipe-hint">🗑️</div>
                <span class="entry-name">${nombre}</span>
                <div class="entry-amounts">
                    <span class="entry-daily">S/ ${r.totalDiario.toFixed(2)}</span>
                    <span class="entry-weekly">semana: S/ ${r.totalSemanal.toFixed(2)}</span>
                </div>
            </div>`;
        } else {
            html += `
            <div class="entry${selClass}" onclick="selectEntry('${safeNombre}')">
                <span class="entry-name">${nombre}</span>
                <div class="entry-amounts">
                    <span class="entry-daily">S/ ${r.totalSemanal.toFixed(2)}</span>
                </div>
            </div>`;
        }
    }
    wrap.innerHTML = html;
    setupSwipeToDelete();
}

function selectEntry(nombre) {
    State.selectedName = State.selectedName === nombre ? null : nombre;
    updateActionBar();
    // Re-renderizar solo los estilos de selección sin recargar desde DB
    document.querySelectorAll(".entry").forEach(el => {
        const entryName = el.querySelector(".entry-name")?.textContent;
        el.classList.toggle("selected", entryName === State.selectedName);
    });
}

function updateActionBar() {
    const bar = document.getElementById("actionBar");
    if (State.selectedName) {
        bar.classList.add("visible");
    } else {
        bar.classList.remove("visible");
    }
}

// ── Swipe para borrar ─────────────────────────────────────────────────────────
function setupSwipeToDelete() {
    const entries = document.querySelectorAll(".entry");
    entries.forEach(el => {
        let startX = 0;
        let isSwiped = false;

        el.addEventListener("touchstart", (e) => {
            startX = e.touches[0].clientX;
        }, { passive: true });

        el.addEventListener("touchend", (e) => {
            const diffX = startX - e.changedTouches[0].clientX;
            if (diffX > 60 && !isSwiped) {
                isSwiped = true;
                el.classList.add("swiped");
                // Al tocar el hint, borrar
                el.querySelector(".swipe-hint")?.addEventListener("click", (ev) => {
                    ev.stopPropagation();
                    const nombre = el.querySelector(".entry-name")?.textContent;
                    if (nombre) {
                        State.selectedName = nombre;
                        onBorrar();
                    }
                }, { once: true });
            } else if (diffX < -20 && isSwiped) {
                isSwiped = false;
                el.classList.remove("swiped");
            }
        }, { passive: true });
    });
}

// ── Overlay / Bottom Sheet ────────────────────────────────────────────────────
function openOverlay() {
    document.getElementById("sheetOverlay").classList.add("show");
    document.getElementById("bottomSheet").classList.add("show");
}

function closeOverlay() {
    document.getElementById("sheetOverlay").classList.remove("show");
    document.getElementById("bottomSheet").classList.remove("show");
    State.sheetMode = null;
    State.askCallback = null;
}

// ── Toast notifications ───────────────────────────────────────────────────────
function showToast(msg, type = "info") {
    const container = document.getElementById("toastContainer");
    const toast = document.createElement("div");
    toast.className = `toast ${type}`;
    toast.textContent = msg;
    container.appendChild(toast);
    setTimeout(() => toast.remove(), 4200);
}

// ── Export ────────────────────────────────────────────────────────────────────
function onExportar() {
    exportarExcel();
}
