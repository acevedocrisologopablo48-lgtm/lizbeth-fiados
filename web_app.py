"""
SISTEMA DE FIADO — LIZBETH
Servidor web Flask para acceso desde el teléfono.
"""

import os
from datetime import datetime
from flask import Flask, render_template, request, jsonify, send_file

from config import EXCEL_PATH, DATE_FORMAT
from entity_extractor import extraer_datos
from excel_manager import (
    registrar_venta,
    corregir_monto,
    borrar_entrada,
    resumen_dia,
    resumen_semanal,
    editar_entrada,
    generate_styled_export,
    _ensure_workbook,
)

app = Flask(__name__)


@app.route("/")
def index():
    today = datetime.now().strftime(DATE_FORMAT)
    return render_template("index.html", fecha=today)


# ── API: Extraer nombre y monto de texto ─────────────
@app.route("/api/extraer", methods=["POST"])
def api_extraer():
    data = request.get_json(silent=True) or {}
    texto = (data.get("texto") or "").strip()
    if not texto:
        return jsonify({"ok": False, "error": "Texto vacío"}), 400

    nombre, monto = extraer_datos(texto)
    return jsonify({
        "ok": True,
        "nombre": nombre,
        "monto": monto,
    })


# ── API: Registrar venta ─────────────────────────────
@app.route("/api/registrar", methods=["POST"])
def api_registrar():
    data = request.get_json(silent=True) or {}
    nombre = (data.get("nombre") or "").strip()
    monto = data.get("monto")

    if not nombre:
        return jsonify({"ok": False, "error": "Falta el nombre"}), 400
    try:
        monto = float(monto)
    except (TypeError, ValueError):
        return jsonify({"ok": False, "error": "Monto inválido"}), 400
    if monto <= 0:
        return jsonify({"ok": False, "error": "El monto debe ser mayor a 0"}), 400

    resultado = registrar_venta(nombre, monto)
    return jsonify({"ok": True, **resultado})


# ── API: Corregir monto ──────────────────────────────
@app.route("/api/corregir", methods=["POST"])
def api_corregir():
    data = request.get_json(silent=True) or {}
    nombre = (data.get("nombre") or "").strip()
    nuevo_monto = data.get("nuevo_monto")

    if not nombre:
        return jsonify({"ok": False, "error": "Falta el nombre"}), 400
    try:
        nuevo_monto = float(nuevo_monto)
    except (TypeError, ValueError):
        return jsonify({"ok": False, "error": "Monto inválido"}), 400

    resultado = corregir_monto(nombre, nuevo_monto)
    if "error" in resultado:
        return jsonify({"ok": False, "error": resultado["error"]}), 404
    return jsonify({"ok": True, **resultado})


# ── API: Editar nombre y/o monto ────────────────────
@app.route("/api/editar", methods=["POST"])
def api_editar():
    data = request.get_json(silent=True) or {}
    nombre_antiguo = (data.get("nombre_antiguo") or "").strip()
    nombre_nuevo = (data.get("nombre_nuevo") or "").strip()
    nuevo_monto = data.get("nuevo_monto")

    if not nombre_antiguo or not nombre_nuevo:
        return jsonify({"ok": False, "error": "Falta el nombre"}), 400
    try:
        nuevo_monto = float(nuevo_monto)
    except (TypeError, ValueError):
        return jsonify({"ok": False, "error": "Monto inválido"}), 400
    if nuevo_monto <= 0:
        return jsonify({"ok": False, "error": "El monto debe ser mayor a 0"}), 400

    resultado = editar_entrada(nombre_antiguo, nombre_nuevo, nuevo_monto)
    if "error" in resultado:
        return jsonify({"ok": False, "error": resultado["error"]}), 404
    return jsonify({"ok": True, **resultado})


# ── API: Borrar entrada ──────────────────────────────
@app.route("/api/borrar", methods=["POST"])
def api_borrar():
    data = request.get_json(silent=True) or {}
    nombre = (data.get("nombre") or "").strip()

    if not nombre:
        return jsonify({"ok": False, "error": "Falta el nombre"}), 400

    resultado = borrar_entrada(nombre)
    if "error" in resultado:
        return jsonify({"ok": False, "error": resultado["error"]}), 404
    return jsonify({"ok": True, **resultado})


# ── API: Resumen del día ─────────────────────────────
@app.route("/api/resumen/dia")
def api_resumen_dia():
    registros = resumen_dia()
    total = sum(r["total_diario"] for r in registros)
    return jsonify({"ok": True, "registros": registros, "total": round(total, 2)})


# ── API: Resumen semanal ─────────────────────────────
@app.route("/api/resumen/semanal")
def api_resumen_semanal():
    registros = resumen_semanal()
    total = sum(r["total_semanal"] for r in registros)
    return jsonify({"ok": True, "registros": registros, "total": round(total, 2)})


# ── API: Exportar Excel ─────────────────────────────
@app.route("/api/exportar")
def api_exportar():
    _ensure_workbook()
    if not EXCEL_PATH.exists():
        return jsonify({"ok": False, "error": "No hay archivo Excel"}), 404
    buf = generate_styled_export()
    return send_file(
        buf,
        as_attachment=True,
        download_name=f"fiado_{datetime.now().strftime('%d-%m-%Y')}.xlsx",
        mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )


if __name__ == "__main__":
    _ensure_workbook()
    # 0.0.0.0 permite acceso desde otros dispositivos en la misma red
    print("\n  ╔══════════════════════════════════════════════════╗")
    print("  ║   🍽️  SISTEMA DE FIADO — LIZBETH                ║")
    print("  ║                                                  ║")
    print("  ║   Abre en tu teléfono:                           ║")

    # Mostrar la IP local
    import socket
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
    except Exception:
        ip = "127.0.0.1"

    url = f"http://{ip}:5000"
    print(f"  ║   📱  {url:<39} ║")
    print("  ║                                                  ║")
    print("  ║   (PC y teléfono en el mismo WiFi)               ║")
    print("  ╚══════════════════════════════════════════════════╝\n")

    app.run(host="0.0.0.0", port=5000, debug=False)
