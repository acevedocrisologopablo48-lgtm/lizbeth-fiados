"""Patch docs/js/app.js with updated showConfirm, onCorregir, openSheet, onSheetConfirm."""
import re, pathlib, sys

APP = pathlib.Path(__file__).parent / "docs/js/app.js"
src = APP.read_text(encoding="utf-8")

# ── 1) Add _showFields helper BEFORE showConfirm ─────────────────────────────
HELPER = """\
// ── Helper: alternar campos dobles vs campo simple ────────────────────────────
function _showFields(useDouble) {
    document.getElementById("sheetFields").classList.toggle("hidden", !useDouble);
    document.getElementById("sheetInputSingle").classList.toggle("hidden", useDouble);
}

"""

CONFIRM_HEADER = "// \u2500\u2500 Confirmar registro \u2500"
if "_showFields" not in src:
    src = src.replace(CONFIRM_HEADER, HELPER + CONFIRM_HEADER)
    print("✓ _showFields helper added")
else:
    print("  _showFields already present")

# ── 2) Replace showConfirm body ───────────────────────────────────────────────
OLD_CONFIRM = """\
function showConfirm(nombre, monto, montos) {
    State.pendingNombre = nombre;
    State.pendingMonto = monto;
    document.getElementById("sheetTitle").textContent = "\u00bfRegistrar esta venta?";

    let detailText;
    if (montos && montos.length >= 2) {
        // Mostrar desglose: S/ 3.50 + S/ 2.00 = S/ 5.50
        const partes = montos.map(m => `S/ ${m.toFixed(2)}`).join(" + ");
        detailText = `${nombre}\\n${partes} = S/ ${monto.toFixed(2)}`;
    } else {
        detailText = `${nombre}  \u2192  S/ ${monto.toFixed(2)}`;
    }

    document.getElementById("sheetDetail").textContent = detailText;
    document.getElementById("sheetDetail").classList.remove("hidden");
    document.getElementById("sheetInput").classList.add("hidden");
    document.getElementById("sheetHint").classList.add("hidden");
    document.getElementById("btnSheetConfirm").textContent = "\u2705 S\u00ed, registrar";
    document.getElementById("btnSheetConfirm").className = "btn-confirm";
    State.sheetMode = "confirm";
    openOverlay();
}"""

NEW_CONFIRM = """\
function showConfirm(nombre, monto, montos) {
    State.pendingNombre = nombre;
    State.pendingMonto = monto;

    let titleText = "\u2705 Confirmar venta";
    if (montos && montos.length >= 2) {
        const partes = montos.map(m => `S/ ${m.toFixed(2)}`).join(" + ");
        titleText = `\u2705 Confirmar (${partes})`;
    }
    document.getElementById("sheetTitle").textContent = titleText;
    document.getElementById("sheetDetail").classList.add("hidden");

    document.getElementById("sheetInput").value = nombre;
    document.getElementById("sheetInput").type = "text";
    document.getElementById("sheetLabel1").textContent = "Nombre";
    document.getElementById("sheetInput2").value = monto.toFixed(2);
    document.getElementById("sheetLabel2").textContent = "Monto (S/)";
    _showFields(true);
    document.getElementById("sheetHint").classList.add("hidden");
    document.getElementById("btnSheetConfirm").textContent = "\u2705 Registrar";
    document.getElementById("btnSheetConfirm").className = "btn-confirm";
    State.sheetMode = "confirm";
    openOverlay();
    setTimeout(() => document.getElementById("sheetInput").focus(), 350);
}"""

if OLD_CONFIRM in src:
    src = src.replace(OLD_CONFIRM, NEW_CONFIRM, 1)
    print("✓ showConfirm updated")
else:
    print("✗ showConfirm old string NOT found")

# ── 3) Replace onCorregir body ────────────────────────────────────────────────
OLD_CORREGIR = """\
// \u2500\u2500 Corregir \u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500
function onCorregir() {
    if (!State.selectedName) { showToast("Toca primero un nombre de la lista.", "error"); return; }
    document.getElementById("sheetTitle").textContent = `\u270f\ufe0f Corregir monto de ${State.selectedName}`;
    document.getElementById("sheetDetail").classList.add("hidden");
    const inp = document.getElementById("sheetInput");
    inp.value = "";
    inp.type = "number";
    inp.inputMode = "decimal";
    inp.placeholder = "Nuevo monto (ej: 3.50)";
    inp.classList.remove("hidden");
    document.getElementById("sheetHint").textContent = "El monto anterior ser\u00e1 reemplazado";
    document.getElementById("sheetHint").classList.remove("hidden");
    document.getElementById("btnSheetConfirm").textContent = "Guardar";
    document.getElementById("btnSheetConfirm").className = "btn-confirm";
    State.sheetMode = "corregir";
    openOverlay();
    setTimeout(() => inp.focus(), 350);
}"""

NEW_CORREGIR = """\
// \u2500\u2500 Editar nombre y monto \u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500
function onCorregir() {
    if (!State.selectedName) { showToast("Toca primero un nombre de la lista.", "error"); return; }
    document.getElementById("sheetTitle").textContent = `\u270f\ufe0f Editar: ${State.selectedName}`;
    document.getElementById("sheetDetail").classList.add("hidden");

    document.getElementById("sheetInput").value = State.selectedName;
    document.getElementById("sheetInput").type = "text";
    document.getElementById("sheetLabel1").textContent = "Nombre";
    document.getElementById("sheetInput2").value = "";
    document.getElementById("sheetInput2").placeholder = "Nuevo monto (ej: 3.50)";
    document.getElementById("sheetLabel2").textContent = "Nuevo monto (S/)";
    _showFields(true);
    document.getElementById("sheetHint").textContent = "Cambia nombre y/o monto";
    document.getElementById("sheetHint").classList.remove("hidden");
    document.getElementById("btnSheetConfirm").textContent = "Guardar cambios";
    document.getElementById("btnSheetConfirm").className = "btn-confirm";
    State.sheetMode = "editar";
    openOverlay();
    setTimeout(() => document.getElementById("sheetInput2").focus(), 350);
}"""

if OLD_CORREGIR in src:
    src = src.replace(OLD_CORREGIR, NEW_CORREGIR, 1)
    print("✓ onCorregir updated")
else:
    print("✗ onCorregir old string NOT found - trying fuzzy...")
    # Try without the box-drawing header
    idx = src.find("function onCorregir()")
    if idx > -1:
        end = src.find("\n}", idx) + 2
        old_func = src[idx:end]
        src = src[:idx] + NEW_CORREGIR[NEW_CORREGIR.find("function"):] + src[end:]
        print("✓ onCorregir updated via fuzzy")
    else:
        print("✗ onCorregir NOT found at all")

# ── 4) Replace openSheet (sheetInput -> sheetInputSingle) ──────────────────
OLD_OPENSHEET_INP = '    const inp = document.getElementById("sheetInput");\n    document.getElementById("sheetDetail").classList.add("hidden");\n    inp.classList.remove("hidden");\n    inp.value = "";'
NEW_OPENSHEET_INP = '    const inp = document.getElementById("sheetInputSingle");\n    document.getElementById("sheetDetail").classList.add("hidden");\n    _showFields(false);\n    inp.classList.remove("hidden");\n    inp.value = "";'

if OLD_OPENSHEET_INP in src:
    src = src.replace(OLD_OPENSHEET_INP, NEW_OPENSHEET_INP, 1)
    print("✓ openSheet input reference updated")
else:
    print("✗ openSheet input NOT found")

# ── 5) Replace onSheetConfirm ─────────────────────────────────────────────
OLD_SHEET_CONFIRM_BLOCK = """\
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
        if (isNaN(val) || val <= 0) { showToast("Monto inv\u00e1lido.", "warning"); return; }
        closeOverlay();
        State.askCallback(val);

    } else if (mode === "corregir") {
        const val = parseFloat(document.getElementById("sheetInput").value.replace(",", "."));
        if (isNaN(val) || val < 0) { showToast("Monto inv\u00e1lido.", "warning"); return; }
        closeOverlay();
        const result = await corregirMonto(State.selectedName, val);
        if (!result.ok) { showToast(result.error, "error"); return; }
        showToast(`\u2705 ${result.nombre}: S/ ${result.montoAnterior.toFixed(2)} \u2192 S/ ${result.nuevoMonto.toFixed(2)}`, "success");
        State.selectedName = null;
        updateActionBar();
        refreshTable();

    } else if (mode === "borrar") {
        closeOverlay();
        const result = await borrarEntrada(State.selectedName);
        if (!result.ok) { showToast(result.error, "error"); return; }
        showToast(`\ud83d\uddd1\ufe0f ${result.nombre} eliminado.`, "success");
        State.selectedName = null;
        updateActionBar();
        refreshTable();
    }"""

NEW_SHEET_CONFIRM_BLOCK = """\
    if (mode === "confirm") {
        const nombre = document.getElementById("sheetInput").value.trim();
        const montoRaw = parseFloat(document.getElementById("sheetInput2").value.replace(",", "."));
        if (!nombre) { showToast("Escribe el nombre.", "warning"); return; }
        if (isNaN(montoRaw) || montoRaw <= 0) { showToast("Monto inv\u00e1lido.", "warning"); return; }
        closeOverlay();
        await doRegister(nombre, montoRaw);

    } else if (mode === "ask-nombre") {
        const val = document.getElementById("sheetInputSingle").value.trim();
        if (!val) { showToast("Escribe un nombre.", "warning"); return; }
        closeOverlay();
        State.askCallback(val);

    } else if (mode === "ask-monto") {
        const val = parseFloat(document.getElementById("sheetInputSingle").value.replace(",", "."));
        if (isNaN(val) || val <= 0) { showToast("Monto inv\u00e1lido.", "warning"); return; }
        closeOverlay();
        State.askCallback(val);

    } else if (mode === "editar") {
        const nombreNuevo = document.getElementById("sheetInput").value.trim();
        const nuevoMonto = parseFloat(document.getElementById("sheetInput2").value.replace(",", "."));
        if (!nombreNuevo) { showToast("Escribe el nombre.", "warning"); return; }
        if (isNaN(nuevoMonto) || nuevoMonto < 0) { showToast("Monto inv\u00e1lido.", "warning"); return; }
        closeOverlay();
        const result = await editarEntrada(State.selectedName, nombreNuevo, nuevoMonto);
        if (!result.ok) { showToast(result.error, "error"); return; }
        showToast(`\u2705 ${result.nombreNuevo}: S/ ${result.nuevoMonto.toFixed(2)}`, "success");
        State.selectedName = null;
        updateActionBar();
        refreshTable();

    } else if (mode === "borrar") {
        closeOverlay();
        const result = await borrarEntrada(State.selectedName);
        if (!result.ok) { showToast(result.error, "error"); return; }
        showToast(`\ud83d\uddd1\ufe0f ${result.nombre} eliminado.`, "success");
        State.selectedName = null;
        updateActionBar();
        refreshTable();
    }"""

if OLD_SHEET_CONFIRM_BLOCK in src:
    src = src.replace(OLD_SHEET_CONFIRM_BLOCK, NEW_SHEET_CONFIRM_BLOCK, 1)
    print("✓ onSheetConfirm updated")
else:
    print("✗ onSheetConfirm block NOT found")

APP.write_text(src, encoding="utf-8")
print("\nDone. File written.")
