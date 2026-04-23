// ── Exportar Excel con SheetJS ────────────────────────────────────────────────
// Genera un Excel estructurado día por día (sin mezclar fechas)

// ── Helpers ───────────────────────────────────────────────────────────────────
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

function construirHoja(registros, titulo) {
    // Agrupar por fecha (ordenado ascendente)
    const porFecha = {};
    for (const r of registros) {
        if (!porFecha[r.fecha]) porFecha[r.fecha] = [];
        porFecha[r.fecha].push(r);
    }
    const fechas = Object.keys(porFecha).sort();

    const aoa = []; // array de arrays → filas del Excel

    // ── Encabezado del archivo ────────────────────────────────────────────────
    aoa.push([titulo]);
    aoa.push([`Exportado el: ${new Date().toLocaleDateString("es-PE")}`]);
    aoa.push([]); // fila vacía

    let totalGeneral = 0;

    // ── Bloque por día ────────────────────────────────────────────────────────
    for (const fecha of fechas) {
        const filasDia = porFecha[fecha];

        // Título del día
        aoa.push([formatearFechaLabel(fecha)]);
        // Cabecera de columnas
        aoa.push(["Nombre", "Monto (S/)"]);

        let subtotal = 0;
        // Ordenar alfabéticamente por nombre
        filasDia.sort((a, b) => a.nombre.localeCompare(b.nombre));

        for (const r of filasDia) {
            aoa.push([r.nombre, parseFloat(r.total_diario)]);
            subtotal += parseFloat(r.total_diario);
        }

        subtotal = Math.round(subtotal * 100) / 100;
        totalGeneral += subtotal;

        // Subtotal del día
        aoa.push(["TOTAL DEL DÍA", subtotal]);
        // Fila separadora
        aoa.push([]);
    }

    // ── Total general ─────────────────────────────────────────────────────────
    if (fechas.length > 1) {
        aoa.push(["TOTAL GENERAL", Math.round(totalGeneral * 100) / 100]);
    }

    // ── Crear hoja SheetJS ────────────────────────────────────────────────────
    const ws = XLSX.utils.aoa_to_sheet(aoa);

    // Anchos de columna
    ws["!cols"] = [{ wch: 32 }, { wch: 16 }];

    // Formato de moneda para columna B
    for (const cellRef in ws) {
        if (cellRef[0] === "B" && cellRef !== "B1") {
            const cell = ws[cellRef];
            if (cell && cell.v !== undefined && !isNaN(cell.v)) {
                cell.t = "n";
                cell.z = '"S/ "#,##0.00';
            }
        }
    }

    return ws;
}

// ── Exportar semana actual ────────────────────────────────────────────────────
async function exportarExcel() {
    const result = await obtenerTodoSemanal();
    if (!result.ok) {
        showToast("Error al obtener datos: " + result.error, "error");
        return;
    }

    const registros = result.registros;
    if (registros.length === 0) {
        showToast("No hay registros esta semana para exportar.", "warning");
        return;
    }

    const ws = construirHoja(registros, "FIADOS LIZBETH — SEMANA ACTUAL");
    const wb = XLSX.utils.book_new();
    XLSX.utils.book_append_sheet(wb, ws, "Semana");

    XLSX.writeFile(wb, `fiado_semana_${fechaArchivo()}.xlsx`);
    showToast(`✅ Excel de la semana descargado (${registros.length} registros)`, "success");
}

// ── Exportar historial completo a Excel ──────────────────────────────────────
async function exportarHistorial() {
    const result = await obtenerTodoHistorial();
    if (!result.ok) {
        showToast("Error al obtener datos: " + result.error, "error");
        return;
    }

    const registros = result.registros;
    if (registros.length === 0) {
        showToast("No hay registros para exportar.", "warning");
        return;
    }

    const ws = construirHoja(registros, "FIADOS LIZBETH — HISTORIAL COMPLETO");
    const wb = XLSX.utils.book_new();
    XLSX.utils.book_append_sheet(wb, ws, "Historial");

    XLSX.writeFile(wb, `fiado_historial_${fechaArchivo()}.xlsx`);
    showToast(`✅ Historial descargado (${registros.length} registros)`, "success");
}
