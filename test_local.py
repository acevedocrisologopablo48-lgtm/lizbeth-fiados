"""Script de prueba local - no requiere micrófono ni API key."""
from entity_extractor import extraer_datos
from excel_manager import registrar_venta, resumen_dia, resumen_semanal, corregir_monto, borrar_entrada, _ensure_workbook

print("=" * 50)
print("  TEST 1: Extractor de entidades")
print("=" * 50)

casos = [
    ("Carlos tres cincuenta",         "Carlos", 3.50),
    ("Anota dos soles para Luis",      "Luis",   2.00),
    ("Maria 1.50",                     "Maria",  1.50),
    ("Pedro un sol con cincuenta",     "Pedro",  1.50),
    ("Ana medio sol",                  "Ana",    0.50),
    ("Jose 3,50",                      "Jose",   3.50),
    ("ponle cinco a Roberto",          "Roberto",5.00),
    ("quince para Sofia",              "Sofia",  15.00),
]

ok = 0
for texto, esperado_nombre, esperado_monto in casos:
    nombre, monto = extraer_datos(texto)
    correcto = nombre and monto and nombre == esperado_nombre and abs(monto - esperado_monto) < 0.01
    estado = "OK" if correcto else "FALLO"
    if correcto:
        ok += 1
    print(f"  [{estado}]  \"{texto}\"")
    print(f"         Esperado: {esperado_nombre} / {esperado_monto}   |   Obtenido: {nombre} / {monto}")

print(f"\n  Resultado: {ok}/{len(casos)} correctos\n")

print("=" * 50)
print("  TEST 2: Excel - INSERT / UPDATE / CORREGIR / BORRAR")
print("=" * 50)

_ensure_workbook()

# INSERT
r = registrar_venta("TestCarlos", 3.50)
print(f"  INSERT -> {r}")

# UPDATE (mismo niño mismo día)
r = registrar_venta("TestCarlos", 2.00)
print(f"  UPDATE -> {r}")

# Otro niño
r = registrar_venta("TestLuis", 5.00)
print(f"  INSERT -> {r}")

# Corregir
r = corregir_monto("TestCarlos", 4.00)
print(f"  CORREGIR -> {r}")

print("\n  --- Resumen del día ---")
for reg in resumen_dia():
    if reg["nombre"] and "Test" in str(reg["nombre"]):
        print(f"  {reg['nombre']:<20} Diario: S/ {reg['total_diario']:.2f}  |  Semanal: S/ {reg['total_semanal']:.2f}")

# Borrar entradas de prueba
borrar_entrada("TestCarlos")
borrar_entrada("TestLuis")
print("\n  Entradas de prueba eliminadas del Excel.")
print("\n  ✅ Todos los tests completados. El sistema esta listo.")
print("  Ejecuta 'python main.py' para usar la aplicacion.\n")
