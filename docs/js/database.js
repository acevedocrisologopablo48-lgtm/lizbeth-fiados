// ── CRUD contra Supabase ──────────────────────────────────────────────────────
// Todas las operaciones retornan { ok, data?, error? }

function hoyISO() {
    const d = new Date();
    return `${d.getFullYear()}-${String(d.getMonth()+1).padStart(2,"0")}-${String(d.getDate()).padStart(2,"0")}`;
}

function lunesISO() {
    const d = new Date();
    const day = d.getDay(); // 0=dom
    const diff = day === 0 ? -6 : 1 - day;
    const lunes = new Date(d);
    lunes.setDate(d.getDate() + diff);
    return `${lunes.getFullYear()}-${String(lunes.getMonth()+1).padStart(2,"0")}-${String(lunes.getDate()).padStart(2,"0")}`;
}

function domingoISO() {
    const d = new Date();
    const day = d.getDay(); // 0=dom
    const diffToSunday = day === 0 ? 0 : 7 - day;
    const domingo = new Date(d);
    domingo.setDate(d.getDate() + diffToSunday);
    return `${domingo.getFullYear()}-${String(domingo.getMonth()+1).padStart(2,"0")}-${String(domingo.getDate()).padStart(2,"0")}`;
}

// ── Registrar venta (INSERT o UPDATE acumulado) ───────────────────────────────
async function registrarVenta(nombre, monto) {
    const db = getClient();
    const hoy = hoyISO();
    const nombreNorm = nombre.trim();

    // Buscar si ya existe entrada hoy para este nombre (case-insensitive)
    const { data: existentes, error: errSelect } = await db
        .from("ventas")
        .select("id, total_diario")
        .eq("fecha", hoy)
        .ilike("nombre", nombreNorm)
        .limit(1);

    if (errSelect) return { ok: false, error: errSelect.message };

    if (existentes && existentes.length > 0) {
        // UPDATE: sumar al monto existente
        const fila = existentes[0];
        const anterior = parseFloat(fila.total_diario);
        const nuevoTotal = Math.round((anterior + monto) * 100) / 100;

        const { error: errUpdate } = await db
            .from("ventas")
            .update({ total_diario: nuevoTotal, updated_at: new Date().toISOString() })
            .eq("id", fila.id);

        if (errUpdate) return { ok: false, error: errUpdate.message };

        return { ok: true, accion: "UPDATE", nombre: nombreNorm, montoAnterior: anterior, montoAgregado: monto, nuevoTotal };
    } else {
        // INSERT: nueva fila
        const { error: errInsert } = await db
            .from("ventas")
            .insert({ fecha: hoy, nombre: nombreNorm, total_diario: monto });

        if (errInsert) return { ok: false, error: errInsert.message };

        return { ok: true, accion: "INSERT", nombre: nombreNorm, monto };
    }
}

// ── Corregir monto (reemplazar total del día) ─────────────────────────────────
async function corregirMonto(nombre, nuevoMonto) {
    const db = getClient();
    const hoy = hoyISO();

    const { data: existentes, error: errSelect } = await db
        .from("ventas")
        .select("id, total_diario")
        .eq("fecha", hoy)
        .ilike("nombre", nombre.trim())
        .limit(1);

    if (errSelect) return { ok: false, error: errSelect.message };
    if (!existentes || existentes.length === 0) return { ok: false, error: `No se encontró a "${nombre}" hoy.` };

    const fila = existentes[0];
    const anterior = parseFloat(fila.total_diario);

    const { error: errUpdate } = await db
        .from("ventas")
        .update({ total_diario: nuevoMonto, updated_at: new Date().toISOString() })
        .eq("id", fila.id);

    if (errUpdate) return { ok: false, error: errUpdate.message };

    return { ok: true, accion: "CORREGIR", nombre: nombre.trim(), montoAnterior: anterior, nuevoMonto };
}

// ── Borrar entrada del día ────────────────────────────────────────────────────
async function borrarEntrada(nombre) {
    const db = getClient();
    const hoy = hoyISO();

    const { data: existentes, error: errSelect } = await db
        .from("ventas")
        .select("id, total_diario")
        .eq("fecha", hoy)
        .ilike("nombre", nombre.trim())
        .limit(1);

    if (errSelect) return { ok: false, error: errSelect.message };
    if (!existentes || existentes.length === 0) return { ok: false, error: `No se encontró a "${nombre}" hoy.` };

    const fila = existentes[0];

    const { error: errDelete } = await db
        .from("ventas")
        .delete()
        .eq("id", fila.id);

    if (errDelete) return { ok: false, error: errDelete.message };

    return { ok: true, accion: "BORRAR", nombre: nombre.trim(), montoEliminado: parseFloat(fila.total_diario) };
}

// ── Resumen del día ───────────────────────────────────────────────────────────
async function obtenerResumenDia() {
    const db = getClient();
    const hoy = hoyISO();

    // Obtener registros del día
    const { data, error } = await db
        .from("ventas")
        .select("nombre, total_diario, fecha")
        .eq("fecha", hoy)
        .order("nombre");

    if (error) return { ok: false, error: error.message };

    // Calcular total semanal por nombre para mostrar en la tabla
    const lunes = lunesISO();
    const domingo = domingoISO();

    const { data: semanal, error: errSem } = await db
        .from("ventas")
        .select("nombre, total_diario")
        .gte("fecha", lunes)
        .lte("fecha", domingo);

    const totalSemanalPorNombre = {};
    if (!errSem && semanal) {
        for (const r of semanal) {
            const n = r.nombre.trim();
            totalSemanalPorNombre[n] = (totalSemanalPorNombre[n] || 0) + parseFloat(r.total_diario);
        }
    }

    const registros = (data || []).map(r => ({
        nombre: r.nombre,
        totalDiario: parseFloat(r.total_diario),
        totalSemanal: Math.round((totalSemanalPorNombre[r.nombre.trim()] || 0) * 100) / 100,
    }));

    const total = registros.reduce((s, r) => s + r.totalDiario, 0);
    return { ok: true, registros, total: Math.round(total * 100) / 100 };
}

// ── Resumen semanal ───────────────────────────────────────────────────────────
async function obtenerResumenSemanal() {
    const db = getClient();
    const lunes = lunesISO();
    const domingo = domingoISO();

    const { data, error } = await db
        .from("ventas")
        .select("nombre, total_diario")
        .gte("fecha", lunes)
        .lte("fecha", domingo)
        .order("nombre");

    if (error) return { ok: false, error: error.message };

    // Agrupar por nombre
    const acumulado = {};
    for (const r of (data || [])) {
        const n = r.nombre.trim();
        acumulado[n] = (acumulado[n] || 0) + parseFloat(r.total_diario);
    }

    const registros = Object.entries(acumulado)
        .sort((a, b) => a[0].localeCompare(b[0]))
        .map(([nombre, total]) => ({
            nombre,
            totalSemanal: Math.round(total * 100) / 100,
        }));

    const total = registros.reduce((s, r) => s + r.totalSemanal, 0);
    return { ok: true, registros, total: Math.round(total * 100) / 100 };
}

// ── Obtener todos los registros de la semana (para Excel) ─────────────────────
async function obtenerTodoSemanal() {
    const db = getClient();
    const lunes = lunesISO();
    const domingo = domingoISO();

    const { data, error } = await db
        .from("ventas")
        .select("fecha, nombre, total_diario")
        .gte("fecha", lunes)
        .lte("fecha", domingo)
        .order("fecha")
        .order("nombre");

    if (error) return { ok: false, error: error.message };
    return { ok: true, registros: data || [] };
}
