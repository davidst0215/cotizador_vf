#!/usr/bin/env python3
"""Script para revisar datos en la BD del SMP"""

import pyodbc
import json
from datetime import datetime

# Credenciales
DB_SERVER = "131.107.20.77"
DB_PORT = 1433
DB_USER = "CHSAYA01"
DB_PASSWORD = "NewServerAz654@!"
DB_NAME = "TDV"
DB_SCHEMA = "saya"

# Connection string
conn_str = f"DRIVER={{SQL Server}};SERVER={DB_SERVER},{DB_PORT};UID={DB_USER};PWD={DB_PASSWORD};DATABASE={DB_NAME};TrustServerCertificate=yes;"

print("[*] Conectando a la BD...")
try:
    conn = pyodbc.connect(conn_str)
    cursor = conn.cursor()
    print("[OK] Conexion exitosa!\n")

    # 1. WIPs disponibles
    print("=" * 80)
    print("[1] WIPS DISPONIBLES (RESUMEN_WIP_POR_PRENDA)")
    print("=" * 80)
    cursor.execute(f"SELECT TOP 10 * FROM {DB_SCHEMA}.resumen_wip_por_prenda")
    columns = [desc[0] for desc in cursor.description]
    for row in cursor.fetchall():
        print(dict(zip(columns, row)))
    print()

    # 2. Clientes únicos
    print("=" * 80)
    print("[2] CLIENTES UNICOS")
    print("=" * 80)
    cursor.execute(f"SELECT DISTINCT TOP 10 cliente FROM {DB_SCHEMA}.costo_op_detalle")
    for row in cursor.fetchall():
        print(f"  - {row[0]}")
    print()

    # 3. Familias de productos
    print("=" * 80)
    print("[3] FAMILIAS DE PRODUCTOS")
    print("=" * 80)
    cursor.execute(f"SELECT DISTINCT TOP 10 familia_de_productos FROM {DB_SCHEMA}.costo_op_detalle")
    for row in cursor.fetchall():
        print(f"  - {row[0]}")
    print()

    # 4. Tipos de prenda
    print("=" * 80)
    print("[4] TIPOS DE PRENDA")
    print("=" * 80)
    cursor.execute(f"SELECT DISTINCT TOP 10 tipo_de_producto FROM {DB_SCHEMA}.costo_op_detalle")
    for row in cursor.fetchall():
        print(f"  - {row[0]}")
    print()

    # 5. Contar registros
    print("=" * 80)
    print("[5] CONTEO DE REGISTROS")
    print("=" * 80)

    tables = [
        f"{DB_SCHEMA}.costo_op_detalle",
        f"{DB_SCHEMA}.resumen_wip_por_prenda",
        f"{DB_SCHEMA}.historial_estilos"
    ]

    for table in tables:
        cursor.execute(f"SELECT COUNT(*) as total FROM {table}")
        total = cursor.fetchone()[0]
        print(f"  {table}: {total} registros")

    conn.close()
    print("\n[OK] Completado!")

except Exception as e:
    print(f"[ERROR] Error: {e}")
    import traceback
    traceback.print_exc()
