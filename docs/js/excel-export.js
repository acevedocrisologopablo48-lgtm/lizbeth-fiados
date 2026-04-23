// ── Exportar Excel con xlsx-js-style ─────────────────────────────────────────
// Genera un Excel estilizado dia por dia

// ── Paleta de colores ─────────────────────────────────────────────────────────
const C = {
    TITULO_BG:    "1F3864",  // Azul marino oscuro
    TITULO_FG:    "FFFFFF",
    FECHA_BG:     "2E75B6",  // Azul medio
    FECHA_FG:     "FFFFFF",
    HEADER_BG:    "4472C4",  // Azul columna
    HEADER_FG:    "FFFFFF",
    FILA_PAR_BG:  "DEEAF1",  // Azul muy claro
    FILA_IMP_BG:  "FFFFFF",  // Blanco
    FILA_FG:      "1F1F1F",
    SUBTOTAL_BG:  "BDD7EE",  // Azul claro
    SUBTOTAL_FG:  "1F3864",
    TOTAL_BG:     "1F3864",
    TOTAL_FG:     "FFFFFF",
    META_FG:      "595959",
};

// ── Borde delgado ─────────────────────────────────────────────────────────────
function borde() {
    const thin = { style: "thin", color: { rgb: "B8CCE4" } };
    return { top: thin, bottom: thin, left: thin, right: thin };
}

// ── Crear celda con estilo ────────────────────────────────────────────────────
function celda(v, s) {
    const t = typeof v === "number" ? "n" : "s";
    return { v, t, s };
}

// ── Formatos ──────────────────────────────────────────────────────────────────
const FMT_SOL  = '"S/ "#,##0.00';
const FMT_TEXT = "@";

// ── Helpers fecha ─────────────────────────────────────────────────────────────
function formatearFechaLabel(fechaISO) {
    const d = new Date(fechaISO + "T12:00:00");
    return d.toLocaleDateString("es-PE", {
        weekday: "long",
        day:     "2-digit",
        month:   "long",
        year:    "numeric",
    }).toUpperCase();
}

function fechaArchivo() {
    const d = new Date();
    return `${String(d.getDate()).padStart(2,"0")}-${String(d.getMonth()+1).padStart(2,"0")}-${d.getFullYear()}`;
}

// ── Escribir celda en hoja ────────────────────────────────────────────────────
function setCelda(ws, col, row, v, s, z) {
    const ref = `${col}${row}`;
    ws[ref] = celda(v, s);
    if (z) ws[ref].z = z;
}

// ── Construir hoja con estilos ────────────────────────────────────────────────
function construirHoja(registros, titulo) {
    const porFecha = {};
    for (const r of registros) {
        if (!porFecha[r.fecha]) porFecha[r.fecha] = [];
        porFecha[r.fecha].push(r);
    }
    const fechas = Object.keys(porFecha).sort();

    const ws = {};
    let fila = 1;
    let maxRow = 1;

    // ── Estilos reutilizables ─────────────────────────────────────────────────
    const sTitulo = {
        fill: { fgColor: { rgb: C.TITULO_BG } },
        font: { bold: true, color: { rgb: C.TITULO_FG }, sz: 14 },
        alignment: { horizontal: "center", vertical: "center" },
    };
    const sMeta = {
        font: { italic: true, color: { rgb: C.META_FG }, sz: 10 },
        alignment: { horizontal: "center" },
    };
    const sFecha = {
        fill: { fgColor: { rgb: C.FECHA_BG } },
        font: { bold: true, color: { rgb: C.FECHA_FG }, sz: 11 },
        alignment: { horizontal: "center", vertical: "center" },
        border: borde(),
    };
    const sHeaderNombre = {
        fill: { fgColor: { rgb: C.HEADER_BG } },
        font: { bold: true, color: { rgb: C.HEADER_FG }, sz: 11 },
        alignment: { horizontal: "center", vertical: "center", wrapText: true },
        border: borde(),
    };
    const sHeaderMonto = {
        fill: { fgColor: { rgb: C.HEADER_BG } },
        font: { bold: true, color: { rgb: C.HEADER_FG }, sz: 11 },
        alignment: { horizontal: "center", vertical: "center" },
        border: borde(),
    };
    const sSubtotalNombre = {
        fill: { fgColor: { rgb: C.SUBTOTAL_BG } },
        font: { bold: true, color: { rgb: C.SUBTOTAL_FG }, sz: 11 },
        alignment: { horizontal: "right", vertical: "center" },
        border: borde(),
    };
    const sSubtotalMonto = {
        fill: { fgColor: { rgb: C.SUBTOTAL_BG } },
        font: { bold: true, color: { rgb: C.SUBTOTAL_FG }, sz: 11 },
        alignment: { horizontal: "center", vertical: "center" },
        border: borde(),
    };
    const sTotalNombre = {
        fill: { fgColor: { rgb: C.TOTAL_BG } },
        font: { bold: true, color: { rgb: C.TOTAL_FG }, sz: 12 },
        alignment: { horizontal: "right", vertical: "center" },
        border: borde(),
    };
    const sTotalMonto = {
        fill: { fgColor: { rgb: C.TOTAL_BG } },
        font: { bold: true, color: { rgb: C.TOTAL_FG }, sz: 12 },
        alignment: { horizontal: "center", vertical: "center" },
        border: borde(),
    };

    // ── Fila de título ────────────────────────────────────────────────────────
    ws["A" + fila] = celda(titulo, sTitulo);
    ws["B" + fila] = celda("", sTitulo);
    ws["!merges"] = ws["!merges"] || [];
    ws["!merges"].push({ s: { r: fila - 1, c: 0 }, e: { r: fila - 1, c: 1 } });
    fila++;

    // ── Fila de fecha de exportación ──────────────────────────────────────────
    ws["A" + fila] = celda(`Exportado el: ${new Date().toLocaleDateString("es-PE")}`, sMeta);
    ws["B" + fila] = celda("", sMeta);
    ws["!merges"].push({ s: { r: fila - 1, c: 0 }, e: { r: fila - 1, c: 1 } });
    fila++;
    fila++; // fila vacía separadora

    let totalGeneral = 0;

    // ── Bloque por día ────────────────────────────────────────────────────────
    for (const fecha of fechas) {
        const filasDia = porFecha[fecha].sort((a, b) => a.nombre.localeCompare(b.nombre));

        // Encabezado del día (merge A:B)
        ws["A" + fila] = celda(formatearFechaLabel(fecha), sFecha);
        ws["B" + fila] = celda("", sFecha);
        ws["!merges"].push({ s: { r: fila - 1, c: 0 }, e: { r: fila - 1, c: 1 } });
        fila++;

        // Cabeceras de columna
        ws["A" + fila] = celda("NOMBRE", sHeaderNombre);
        ws["B" + fila] = celda("MONTO (S/)", sHeaderMonto);
        fila++;

        // Filas de datos
        let subtotal = 0;
        filasDia.forEach((r, idx) => {
            const esPar = idx % 2 === 0;
            const sNombre = {
                fill: { fgColor: { rgb: esPar ? C.FILA_PAR_BG : C.FILA_IMP_BG } },
                font: { color: { rgb: C.FILA_FG }, sz: 11 },
                alignment: { horizontal: "left", vertical: "center" },
                border: borde(),
            };
            const sMonto = {
                fill: { fgColor: { rgb: esPar ? C.FILA_PAR_BG : C.FILA_IMP_BG } },
                font: { color: { rgb: C.FILA_FG }, sz: 11 },
                alignment: { horizontal: "center", vertical: "center" },
                border: borde(),
            };
            const monto = parseFloat(r.total_diario);
            ws["A" + fila] = celda(r.nombre, sNombre);
            setCelda(ws, "B", fila, monto, sMonto, FMT_SOL);
            subtotal += monto;
            fila++;
        });

        subtotal = Math.round(subtotal * 100) / 100;
        totalGeneral += subtotal;

        // Fila subtotal del día
        ws["A" + fila] = celda("TOTAL DEL DÍA", sSubtotalNombre);
        setCelda(ws, "B", fila, subtotal, sSubtotalMonto, FMT_SOL);
        fila++;
        fila++; // separador
    }

    // ── Total general ─────────────────────────────────────────────────────────
    if (fechas.length > 1) {
        ws["A" + fila] = celda("TOTAL GENERAL", sTotalNombre);
        setCelda(ws, "B", fila, Math.round(totalGeneral * 100) / 100, sTotalMonto, FMT_SOL);
        fila++;
    }

    maxRow = fila;

    // ── Rango y anchos ────────────────────────────────────────────────────────
    ws["!ref"] = `A1:B${maxRow}`;
    ws["!cols"] = [{ wch: 34 }, { wch: 18 }];

    // ── Alto de filas clave ───────────────────────────────────────────────────
    ws["!rows"] = [{ hpt: 30 }, { hpt: 18 }];

    return ws;
}

// ── Exportar semana actual ────────────────────────────────────────────────────
async function exportarExcel() {
    const result = await obtenerTodoSemanal();
    if (!result.ok) { showToast("Error al obtener datos: " + result.error, "error"); return; }
    const registros = result.registros;
    if (registros.length === 0) { showToast("No hay registros esta semana para exportar.", "warning"); return; }

    const ws = construirHoja(registros, "FIADOS LIZBETH — SEMANA ACTUAL");
    const wb = XLSX.utils.book_new();
    XLSX.utils.book_append_sheet(wb, ws, "Semana");
    XLSX.writeFile(wb, `fiado_semana_${fechaArchivo()}.xlsx`);
    showToast(`Descargado: ${registros.length} registros`, "success");
}

// ── Exportar historial completo ───────────────────────────────────────────────
async function exportarHistorial() {
    const result = await obtenerTodoHistorial();
    if (!result.ok) { showToast("Error al obtener datos: " + result.error, "error"); return; }
    const registros = result.registros;
    if (registros.length === 0) { showToast("No hay registros para exportar.", "warning"); return; }

    const ws = construirHoja(registros, "FIADOS LIZBETH — HISTORIAL COMPLETO");
    const wb = XLSX.utils.book_new();
    XLSX.utils.book_append_sheet(wb, ws, "Historial");
    XLSX.writeFile(wb, `fiado_historial_${fechaArchivo()}.xlsx`);
    showToast(`Historial descargado: ${registros.length} registros`, "success");
}
