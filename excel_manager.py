"""
Capa de datos — usa SQLite como almacenamiento persistente.
La exportación a Excel se genera en memoria (BytesIO) sin tocar disco.
"""
import io
import sqlite3
import unicodedata
from collections import defaultdict, OrderedDict
from contextlib import contextmanager
from datetime import datetime, timedelta

import openpyxl
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side

from config import DB_PATH, DATE_FORMAT


# ── Utilidades ────────────────────────────────────────────────────────────────

def _normalize(name: str) -> str:
    name = name.strip().lower()
    nfkd = unicodedata.normalize("NFKD", name)
    return "".join(c for c in nfkd if not unicodedata.combining(c))


def _get_week_range(date: datetime) -> tuple[datetime, datetime]:
    monday = date - timedelta(days=date.weekday())
    sunday = monday + timedelta(days=6)
    return monday, sunday


@contextmanager
def _conn():
    con = sqlite3.connect(DB_PATH)
    con.row_factory = sqlite3.Row
    try:
        yield con
        con.commit()
    except Exception:
        con.rollback()
        raise
    finally:
        con.close()


def _ensure_db():
    """Crea la tabla si no existe. Devuelve True (compatibilidad)."""
    with _conn() as con:
        con.execute("""
            CREATE TABLE IF NOT EXISTS ventas (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                fecha       TEXT    NOT NULL,
                nombre      TEXT    NOT NULL,
                nombre_norm TEXT    NOT NULL,
                monto       REAL    NOT NULL DEFAULT 0.0
            )
        """)
        con.execute("CREATE INDEX IF NOT EXISTS idx_fecha       ON ventas(fecha)")
        con.execute("CREATE INDEX IF NOT EXISTS idx_nombre_norm ON ventas(nombre_norm)")
    return True


# ── API pública ───────────────────────────────────────────────────────────────

def registrar_venta(nombre: str, monto: float) -> dict:
    _ensure_db()
    today    = datetime.now()
    date_str = today.strftime(DATE_FORMAT)
    nombre   = nombre.strip().title()
    norm     = _normalize(nombre)

    with _conn() as con:
        row = con.execute(
            "SELECT id, monto FROM ventas WHERE fecha=? AND nombre_norm=?",
            (date_str, norm),
        ).fetchone()

        if row:
            monto_ant  = row["monto"]
            nuevo_total = round(monto_ant + monto, 2)
            con.execute("UPDATE ventas SET monto=? WHERE id=?", (nuevo_total, row["id"]))
            return {
                "accion": "UPDATE",
                "nombre": nombre,
                "monto_anterior": monto_ant,
                "monto_agregado": monto,
                "nuevo_total": nuevo_total,
            }
        else:
            con.execute(
                "INSERT INTO ventas (fecha, nombre, nombre_norm, monto) VALUES (?,?,?,?)",
                (date_str, nombre, norm, round(monto, 2)),
            )
            return {"accion": "INSERT", "nombre": nombre, "monto": monto}


def corregir_monto(nombre: str, nuevo_monto: float) -> dict:
    _ensure_db()
    date_str = datetime.now().strftime(DATE_FORMAT)
    nombre   = nombre.strip().title()
    norm     = _normalize(nombre)

    with _conn() as con:
        row = con.execute(
            "SELECT id, monto FROM ventas WHERE fecha=? AND nombre_norm=?",
            (date_str, norm),
        ).fetchone()
        if not row:
            return {"error": f"No se encontró a '{nombre}' en el registro de hoy."}
        monto_ant = row["monto"]
        con.execute("UPDATE ventas SET monto=? WHERE id=?", (round(nuevo_monto, 2), row["id"]))

    return {"accion": "CORREGIR", "nombre": nombre,
            "monto_anterior": monto_ant, "nuevo_monto": nuevo_monto}


def borrar_entrada(nombre: str) -> dict:
    _ensure_db()
    date_str = datetime.now().strftime(DATE_FORMAT)
    nombre_t = nombre.strip().title()
    norm     = _normalize(nombre_t)

    with _conn() as con:
        row = con.execute(
            "SELECT id, monto FROM ventas WHERE fecha=? AND nombre_norm=?",
            (date_str, norm),
        ).fetchone()
        if not row:
            return {"error": f"No se encontró a '{nombre_t}' en el registro de hoy."}
        monto = row["monto"]
        con.execute("DELETE FROM ventas WHERE id=?", (row["id"],))

    return {"accion": "BORRAR", "nombre": nombre_t, "monto_eliminado": monto}


def editar_entrada(nombre_antiguo: str, nombre_nuevo: str, nuevo_monto: float) -> dict:
    _ensure_db()
    date_str       = datetime.now().strftime(DATE_FORMAT)
    nombre_antiguo = nombre_antiguo.strip().title()
    nombre_nuevo   = nombre_nuevo.strip().title()
    norm_ant       = _normalize(nombre_antiguo)
    norm_nuevo     = _normalize(nombre_nuevo)

    with _conn() as con:
        row = con.execute(
            "SELECT id, monto FROM ventas WHERE fecha=? AND nombre_norm=?",
            (date_str, norm_ant),
        ).fetchone()
        if not row:
            return {"error": f"No se encontró a '{nombre_antiguo}' en el registro de hoy."}
        monto_ant = row["monto"]
        con.execute(
            "UPDATE ventas SET nombre=?, nombre_norm=?, monto=? WHERE id=?",
            (nombre_nuevo, norm_nuevo, round(nuevo_monto, 2), row["id"]),
        )

    return {
        "accion": "EDITAR",
        "nombre_anterior": nombre_antiguo,
        "nombre_nuevo": nombre_nuevo,
        "monto_anterior": monto_ant,
        "nuevo_monto": nuevo_monto,
    }


def _weekly_total(nombre_norm: str, today: datetime) -> float:
    monday, sunday = _get_week_range(today)
    with _conn() as con:
        rows = con.execute(
            "SELECT fecha, monto FROM ventas WHERE nombre_norm=?", (nombre_norm,)
        ).fetchall()
    total = 0.0
    for r in rows:
        try:
            d = datetime.strptime(r["fecha"], DATE_FORMAT)
        except ValueError:
            continue
        if monday <= d <= sunday:
            total += r["monto"]
    return round(total, 2)


def resumen_dia() -> list[dict]:
    _ensure_db()
    today    = datetime.now()
    date_str = today.strftime(DATE_FORMAT)
    with _conn() as con:
        rows = con.execute(
            "SELECT nombre, nombre_norm, monto FROM ventas WHERE fecha=? ORDER BY nombre",
            (date_str,),
        ).fetchall()
    return [
        {
            "nombre": r["nombre"],
            "total_diario": r["monto"],
            "total_semanal": _weekly_total(r["nombre_norm"], today),
        }
        for r in rows
    ]


def resumen_semanal() -> list[dict]:
    _ensure_db()
    today         = datetime.now()
    monday, sunday = _get_week_range(today)

    with _conn() as con:
        rows = con.execute(
            "SELECT nombre, nombre_norm, fecha, monto FROM ventas ORDER BY nombre"
        ).fetchall()

    acumulado: dict[str, tuple[str, float]] = {}
    for r in rows:
        try:
            d = datetime.strptime(r["fecha"], DATE_FORMAT)
        except ValueError:
            continue
        if monday <= d <= sunday:
            norm = r["nombre_norm"]
            prev = acumulado.get(norm, (r["nombre"], 0.0))
            acumulado[norm] = (prev[0], prev[1] + r["monto"])

    return [
        {"nombre": v[0], "total_semanal": round(v[1], 2)}
        for v in sorted(acumulado.values(), key=lambda x: x[0])
    ]


# ── Exportación Excel estilizada ──────────────────────────────────────────────

_C_TITLE    = "1F3864"
_C_DATE     = "2E75B6"
_C_COL_HDR  = "4472C4"
_C_ODD      = "DEEAF1"
_C_EVEN     = "FFFFFF"
_C_SUBTOTAL = "BDD7EE"
_C_TOTAL    = "1F3864"
_C_AMOUNT   = "1F5C99"


def _bdr(style="thin"):
    s = Side(style=style)
    return Border(left=s, right=s, top=s, bottom=s)

def _fill(hex_color):
    return PatternFill(start_color=hex_color, end_color=hex_color, fill_type="solid")

def _fnt(bold=False, size=11, color="000000"):
    return Font(name="Calibri", bold=bold, size=size, color=color)

def _aln(h="center", v="center"):
    return Alignment(horizontal=h, vertical=v)


def generate_styled_export() -> io.BytesIO:
    """
    Lee TODOS los datos de SQLite y genera un Excel estilizado en memoria.
    Agrupa por fecha, subtotal por día, gran total al final.
    """
    _ensure_db()

    with _conn() as con:
        all_rows = con.execute(
            "SELECT fecha, nombre, nombre_norm, monto FROM ventas ORDER BY fecha, nombre"
        ).fetchall()

    # Agrupar por fecha
    days: dict[str, list[dict]] = defaultdict(list)
    for r in all_rows:
        date_str = r["fecha"]
        try:
            date_obj = datetime.strptime(date_str, DATE_FORMAT)
        except ValueError:
            continue
        days[date_str].append({
            "date_obj": date_obj,
            "nombre": r["nombre"],
            "nombre_norm": r["nombre_norm"],
            "monto": r["monto"],
        })

    sorted_days = OrderedDict(
        sorted(days.items(), key=lambda x: x[1][0]["date_obj"])
    )

    # ── Construir workbook ────────────────────────────────────────────────
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Registro de Fiado"
    ws.sheet_view.showGridLines = False
    ws.column_dimensions["A"].width = 16
    ws.column_dimensions["B"].width = 24
    ws.column_dimensions["C"].width = 20
    ws.column_dimensions["D"].width = 22

    cur = 1

    # Título
    ws.merge_cells(f"A{cur}:D{cur}")
    c = ws.cell(row=cur, column=1, value="🍽️  SISTEMA DE FIADO — LIZBETH")
    c.font = _fnt(bold=True, size=14, color="FFFFFF")
    c.fill = _fill(_C_TITLE); c.alignment = _aln(); c.border = _bdr("medium")
    ws.row_dimensions[cur].height = 28; cur += 1

    ws.merge_cells(f"A{cur}:D{cur}")
    c = ws.cell(row=cur, column=1,
                value=f"Generado el {datetime.now().strftime('%d/%m/%Y  %H:%M')}")
    c.font = _fnt(size=10, color="FFFFFF")
    c.fill = _fill(_C_TITLE); c.alignment = _aln(); c.border = _bdr()
    ws.row_dimensions[cur].height = 18; cur += 1

    grand_total = 0.0
    day_names   = {0:"Lunes",1:"Martes",2:"Miércoles",3:"Jueves",
                   4:"Viernes",5:"Sábado",6:"Domingo"}

    for date_str, entries in sorted_days.items():
        date_obj = entries[0]["date_obj"]

        # Separador + cabecera de fecha
        ws.row_dimensions[cur].height = 6; cur += 1
        ws.merge_cells(f"A{cur}:D{cur}")
        c = ws.cell(row=cur, column=1,
                    value=f"📅  {day_names[date_obj.weekday()]}  {date_str}")
        c.font = _fnt(bold=True, size=11, color="FFFFFF")
        c.fill = _fill(_C_DATE); c.alignment = _aln("left"); c.border = _bdr("medium")
        ws.row_dimensions[cur].height = 22; cur += 1

        # Cabecera columnas
        for col, lbl in enumerate(["#","Nombre","Monto del Día (S/)","Total Semanal (S/)"],1):
            c = ws.cell(row=cur, column=col, value=lbl)
            c.font = _fnt(bold=True, size=10, color="FFFFFF")
            c.fill = _fill(_C_COL_HDR); c.alignment = _aln(); c.border = _bdr()
        ws.row_dimensions[cur].height = 18; cur += 1

        # Calcular totales semanales para esta fecha de una sola consulta
        monday, sunday = _get_week_range(date_obj)
        with _conn() as con:
            week_rows = con.execute(
                "SELECT nombre_norm, SUM(monto) as total FROM ventas "
                "WHERE fecha >= ? AND fecha <= ? GROUP BY nombre_norm",
                (monday.strftime(DATE_FORMAT), sunday.strftime(DATE_FORMAT)),
            ).fetchall()
        weekly_map = {r["nombre_norm"]: r["total"] for r in week_rows}

        day_total = 0.0
        for i, entry in enumerate(sorted(entries, key=lambda x: x["nombre"]), 1):
            bg = _C_ODD if i % 2 == 1 else _C_EVEN
            weekly = round(weekly_map.get(entry["nombre_norm"], 0.0), 2)

            for col, val in enumerate([i, entry["nombre"], entry["monto"], weekly], 1):
                c = ws.cell(row=cur, column=col, value=val)
                c.fill = _fill(bg); c.border = _bdr(); c.font = _fnt(size=10)
                if col == 1:
                    c.alignment = _aln()
                elif col == 2:
                    c.alignment = _aln("left")
                else:
                    c.alignment = _aln("right")
                    c.number_format = '"S/ "#,##0.00'
                    c.font = _fnt(size=10, color=_C_AMOUNT, bold=(col == 3))
            day_total += entry["monto"]
            ws.row_dimensions[cur].height = 17; cur += 1

        # Subtotal del día
        ws.merge_cells(f"A{cur}:B{cur}")
        c = ws.cell(row=cur, column=1, value="Subtotal del día")
        c.font = _fnt(bold=True, size=10, color="1F3864")
        c.fill = _fill(_C_SUBTOTAL); c.alignment = _aln("right"); c.border = _bdr()
        c = ws.cell(row=cur, column=3, value=round(day_total, 2))
        c.font = _fnt(bold=True, size=11, color="1F3864")
        c.fill = _fill(_C_SUBTOTAL); c.alignment = _aln("right")
        c.number_format = '"S/ "#,##0.00'; c.border = _bdr()
        c = ws.cell(row=cur, column=4, value="")
        c.fill = _fill(_C_SUBTOTAL); c.border = _bdr()
        ws.row_dimensions[cur].height = 18
        grand_total += day_total; cur += 1

    # Gran total
    ws.row_dimensions[cur].height = 8; cur += 1
    ws.merge_cells(f"A{cur}:B{cur}")
    c = ws.cell(row=cur, column=1, value="GRAN TOTAL ACUMULADO")
    c.font = _fnt(bold=True, size=12, color="FFFFFF")
    c.fill = _fill(_C_TOTAL); c.alignment = _aln("right"); c.border = _bdr("medium")
    c = ws.cell(row=cur, column=3, value=round(grand_total, 2))
    c.font = _fnt(bold=True, size=13, color="FFFFFF")
    c.fill = _fill(_C_TOTAL); c.alignment = _aln("right")
    c.number_format = '"S/ "#,##0.00'; c.border = _bdr("medium")
    c = ws.cell(row=cur, column=4, value="")
    c.fill = _fill(_C_TOTAL); c.border = _bdr("medium")
    ws.row_dimensions[cur].height = 24
    ws.freeze_panes = "A3"

    buf = io.BytesIO()
    wb.save(buf)
    buf.seek(0)
    return buf


