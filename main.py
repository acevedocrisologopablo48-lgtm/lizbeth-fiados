import os
import sys
from datetime import datetime

from config import EXCEL_PATH, DATE_FORMAT
from audio_capture import grabar_audio
from transcriber import transcribir_audio
from entity_extractor import extraer_datos
from excel_manager import (
    registrar_venta,
    corregir_monto,
    borrar_entrada,
    resumen_dia,
    resumen_semanal,
    _ensure_workbook,
)


def limpiar_pantalla():
    os.system("cls" if os.name == "nt" else "clear")


def mostrar_banner():
    today = datetime.now().strftime(DATE_FORMAT)
    print("=" * 50)
    print("   🍽️  SISTEMA DE FIADO — LIZBETH")
    print(f"   📅 Fecha: {today}")
    print("=" * 50)
    print()


def mostrar_menu():
    print("  Comandos:")
    print("    [ENTER]    → Dictar una venta por voz")
    print("    [texto]    → Escribir manualmente (ej: Carlos 3.50)")
    print("    ver        → Resumen del día")
    print("    semanal    → Resumen semanal")
    print("    corregir   → Corregir monto de un niño")
    print("    borrar     → Eliminar entrada de hoy")
    print("    salir      → Guardar y salir")
    print()


def procesar_dictado_voz():
    """Graba, transcribe, extrae datos y registra."""
    ruta = grabar_audio()
    if ruta is None:
        return

    print("  🔄 Transcribiendo...")
    texto = transcribir_audio(ruta)
    if texto is None:
        return

    print(f'  📝 Escuché: "{texto}"')
    nombre, monto = extraer_datos(texto)

    if nombre is None and monto is None:
        print("  ⚠️  No pude extraer nombre ni monto. Intenta de nuevo.")
        return

    if nombre is None:
        print(f"  ⚠️  Detecté monto S/ {monto:.2f} pero no un nombre.")
        nombre = input("     ¿Para quién es? → ").strip()
        if not nombre:
            print("  ❌ Cancelado.")
            return

    if monto is None:
        print(f"  ⚠️  Detecté el nombre '{nombre}' pero no un monto.")
        try:
            monto = float(input("     ¿Cuánto fue? → ").strip().replace(",", "."))
        except ValueError:
            print("  ❌ Monto inválido. Cancelado.")
            return

    # Confirmación
    print(f"\n  📋 {nombre} → S/ {monto:.2f}")
    confirm = input("     ¿Correcto? (s/n) → ").strip().lower()
    if confirm not in ("s", "si", "sí", ""):
        print("  ❌ Descartado. Intenta de nuevo.")
        return

    resultado = registrar_venta(nombre, monto)
    _mostrar_resultado(resultado)


def procesar_texto_manual(texto: str):
    """Procesa texto escrito manualmente."""
    nombre, monto = extraer_datos(texto)

    if nombre is None and monto is None:
        print("  ⚠️  No pude entender. Usa formato: Nombre Monto (ej: Carlos 3.50)")
        return

    if nombre is None:
        print(f"  ⚠️  Detecté monto S/ {monto:.2f} pero no un nombre.")
        nombre = input("     ¿Para quién es? → ").strip()
        if not nombre:
            print("  ❌ Cancelado.")
            return

    if monto is None:
        print(f"  ⚠️  Detecté '{nombre}' pero no un monto.")
        try:
            monto = float(input("     ¿Cuánto fue? → ").strip().replace(",", "."))
        except ValueError:
            print("  ❌ Monto inválido. Cancelado.")
            return

    print(f"\n  📋 {nombre} → S/ {monto:.2f}")
    confirm = input("     ¿Correcto? (s/n) → ").strip().lower()
    if confirm not in ("s", "si", "sí", ""):
        print("  ❌ Descartado.")
        return

    resultado = registrar_venta(nombre, monto)
    _mostrar_resultado(resultado)


def _mostrar_resultado(resultado: dict):
    """Muestra el resultado de una operación."""
    if "error" in resultado:
        print(f"  ❌ {resultado['error']}")
        return

    accion = resultado["accion"]
    nombre = resultado["nombre"]

    if accion == "INSERT":
        print(f"  ✅ {nombre} registrado: S/ {resultado['monto']:.2f}")
    elif accion == "UPDATE":
        print(f"  ✅ {nombre} actualizado: S/ {resultado['monto_anterior']:.2f} → S/ {resultado['nuevo_total']:.2f}")
    elif accion == "CORREGIR":
        print(f"  ✅ {nombre} corregido: S/ {resultado['monto_anterior']:.2f} → S/ {resultado['nuevo_monto']:.2f}")
    elif accion == "BORRAR":
        print(f"  ✅ {nombre} eliminado (era S/ {resultado['monto_eliminado']:.2f})")


def cmd_ver_dia():
    """Muestra el resumen del día."""
    registros = resumen_dia()
    if not registros:
        print("  📭 No hay registros para hoy.")
        return

    today = datetime.now().strftime(DATE_FORMAT)
    print(f"\n  {'═' * 40}")
    print(f"  📊 RESUMEN DEL DÍA {today}")
    print(f"  {'═' * 40}")
    total = 0.0
    for r in registros:
        print(f"    {r['nombre']:<20} S/ {r['total_diario']:>6.2f}")
        total += r["total_diario"]
    print(f"  {'─' * 40}")
    print(f"    {'TOTAL':<20} S/ {total:>6.2f}")
    print()


def cmd_ver_semanal():
    """Muestra el resumen semanal."""
    registros = resumen_semanal()
    if not registros:
        print("  📭 No hay registros esta semana.")
        return

    print(f"\n  {'═' * 40}")
    print(f"  📊 RESUMEN SEMANAL")
    print(f"  {'═' * 40}")
    total = 0.0
    for r in registros:
        print(f"    {r['nombre']:<20} S/ {r['total_semanal']:>6.2f}")
        total += r["total_semanal"]
    print(f"  {'─' * 40}")
    print(f"    {'TOTAL':<20} S/ {total:>6.2f}")
    print()


def cmd_corregir():
    """Corrige el monto de un niño para hoy."""
    nombre = input("  ¿Nombre del niño a corregir? → ").strip()
    if not nombre:
        print("  ❌ Cancelado.")
        return

    try:
        nuevo = float(input(f"  ¿Nuevo monto para {nombre}? → ").strip().replace(",", "."))
    except ValueError:
        print("  ❌ Monto inválido.")
        return

    resultado = corregir_monto(nombre, nuevo)
    _mostrar_resultado(resultado)


def cmd_borrar():
    """Elimina la entrada de un niño para hoy."""
    nombre = input("  ¿Nombre del niño a borrar? → ").strip()
    if not nombre:
        print("  ❌ Cancelado.")
        return

    confirm = input(f"  ¿Seguro que quieres borrar a {nombre} de hoy? (s/n) → ").strip().lower()
    if confirm not in ("s", "si", "sí"):
        print("  ❌ Cancelado.")
        return

    resultado = borrar_entrada(nombre)
    _mostrar_resultado(resultado)


def main():
    """Loop principal del sistema."""
    limpiar_pantalla()
    mostrar_banner()

    # Asegurar que el Excel existe
    _ensure_workbook()
    print(f"  📁 Excel: {EXCEL_PATH}\n")

    mostrar_menu()

    while True:
        try:
            entrada = input("  > ").strip()
        except (KeyboardInterrupt, EOFError):
            print("\n")
            break

        if entrada.lower() in ("salir", "exit", "q"):
            break
        elif entrada.lower() == "ver":
            cmd_ver_dia()
        elif entrada.lower() == "semanal":
            cmd_ver_semanal()
        elif entrada.lower() == "corregir":
            cmd_corregir()
        elif entrada.lower() == "borrar":
            cmd_borrar()
        elif entrada.lower() == "menu":
            mostrar_menu()
        elif entrada.lower() == "cls":
            limpiar_pantalla()
            mostrar_banner()
            mostrar_menu()
        elif entrada == "":
            # ENTER → dictar por voz
            procesar_dictado_voz()
        else:
            # Texto manual
            procesar_texto_manual(entrada)

        print()

    print("  💾 Archivo guardado en:", EXCEL_PATH)
    print("  ¡Buenas noches! 🌙")


if __name__ == "__main__":
    main()
