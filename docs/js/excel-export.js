// ── Exportar Excel con SheetJS ────────────────────────────────────────────────
// Genera y descarga un .xlsx directamente en el navegador (sin servidor)

async function exportarExcel() {
    // Obtener datos de la semana
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

    // Calcular totales semanales por nombre
    const semanalPorNombre = {};
    for (const r of registros) {
        const n = r.nombre.trim();
        semanalPorNombre[n] = (semanalPorNombre[n] || 0) + parseFloat(r.total_diario);
    }

    // Construir filas para el Excel
    const filas = registros.map(r => ({
        "Fecha":              r.fecha,
        "Nombre":             r.nombre,
        "Total Diario (S/)":  parseFloat(r.total_diario),
        "Total Semanal (S/)": Math.round((semanalPorNombre[r.nombre.trim()] || 0) * 100) / 100,
    }));

    // Crear workbook con SheetJS
    const wb = XLSX.utils.book_new();
    const ws = XLSX.utils.json_to_sheet(filas);

    // Anchos de columna
    ws["!cols"] = [
        { wch: 14 },  // Fecha
        { wch: 22 },  // Nombre
        { wch: 20 },  // Total Diario
        { wch: 22 },  // Total Semanal
    ];

    XLSX.utils.book_append_sheet(wb, ws, "Registro");

    // Nombre del archivo con la semana
    const hoy = new Date();
    const fechaStr = `${hoy.getDate().toString().padStart(2,"0")}-${(hoy.getMonth()+1).toString().padStart(2,"0")}-${hoy.getFullYear()}`;
    XLSX.writeFile(wb, `fiado_semana_${fechaStr}.xlsx`);

    showToast("📥 Excel de la semana descargado", "success");
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

    // Agrupar por semana para calcular totales semanales
    const semanalPorNombreYSemana = {};
    for (const r of registros) {
        const d = new Date(r.fecha + "T12:00:00"); // mediodía para evitar UTC
        const day = d.getDay();
        const diffToMonday = day === 0 ? -6 : 1 - day;
        const lunes = new Date(d);
        lunes.setDate(d.getDate() + diffToMonday);
        const semanaKey = `${lunes.getFullYear()}-${String(lunes.getMonth()+1).padStart(2,"0")}-${String(lunes.getDate()).padStart(2,"0")}`;
        const key = `${r.nombre.trim()}|${semanaKey}`;
        semanalPorNombreYSemana[key] = (semanalPorNombreYSemana[key] || 0) + parseFloat(r.total_diario);
    }

    // Construir filas
    const filas = registros.map(r => {
        const d = new Date(r.fecha + "T12:00:00");
        const day = d.getDay();
        const diffToMonday = day === 0 ? -6 : 1 - day;
        const lunes = new Date(d);
        lunes.setDate(d.getDate() + diffToMonday);
        const semanaKey = `${lunes.getFullYear()}-${String(lunes.getMonth()+1).padStart(2,"0")}-${String(lunes.getDate()).padStart(2,"0")}`;
        const key = `${r.nombre.trim()}|${semanaKey}`;

        return {
            "Fecha":              r.fecha,
            "Nombre":             r.nombre,
            "Total Diario (S/)":  parseFloat(r.total_diario),
            "Total Semanal (S/)": Math.round((semanalPorNombreYSemana[key] || 0) * 100) / 100,
            "Semana del":         semanaKey,
        };
    });

    const wb = XLSX.utils.book_new();
    const ws = XLSX.utils.json_to_sheet(filas);
    ws["!cols"] = [
        { wch: 14 },  // Fecha
        { wch: 22 },  // Nombre
        { wch: 20 },  // Total Diario
        { wch: 22 },  // Total Semanal
        { wch: 14 },  // Semana del
    ];

    XLSX.utils.book_append_sheet(wb, ws, "Historial");

    const hoy = new Date();
    const fechaStr = `${hoy.getDate().toString().padStart(2,"0")}-${(hoy.getMonth()+1).toString().padStart(2,"0")}-${hoy.getFullYear()}`;
    XLSX.writeFile(wb, `fiado_historial_${fechaStr}.xlsx`);

    showToast(`📥 Historial completo descargado (${registros.length} registros)`, "success");
}
