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

    showToast("📥 Excel descargado correctamente", "success");
}
