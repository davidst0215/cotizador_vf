import pyodbc
import os
from datetime import datetime, date
from dotenv import load_dotenv

load_dotenv()

# Obtener variables de entorno
db_host = os.getenv('DB_HOST')
db_name = os.getenv('DB_NAME')
db_user = os.getenv('DB_USER')
db_password = os.getenv('DB_PASSWORD')

print(f"📦 Conectando a {db_host}/{db_name}")

# Intentar con diferentes drivers
drivers = ["ODBC Driver 17 for SQL Server", "ODBC Driver 18 for SQL Server", "SQL Server"]

conn = None
for driver in drivers:
    try:
        conn = pyodbc.connect(
            f"Driver={{{driver}}};"
            f"Server={db_host};"
            f"Database={db_name};"
            f"UID={db_user};"
            f"PWD={db_password};"
            f"Encrypt=yes;TrustServerCertificate=yes"
        )
        print(f"✅ Conectado con driver: {driver}\n")
        break
    except Exception as e:
        print(f"❌ {driver}: {str(e)[:50]}")
        continue

if not conn:
    print("Error: No se pudo conectar a la base de datos")
    exit(1)

cursor = conn.cursor()
schema = "tecnificacion_proceso"
today = date.today()

print(f"🔍 Validando fechas_corrida - Hoy: {today}\n")

# 1. Verificar costo_op_detalle
print("=" * 70)
print("1️⃣ TABLA: costo_op_detalle")
print("=" * 70)

query1 = f"""
SELECT 
  DISTINCT fecha_corrida,
  COUNT(*) as cantidad_registros
FROM {schema}.costo_op_detalle
GROUP BY fecha_corrida
ORDER BY fecha_corrida DESC
"""

cursor.execute(query1)
resultados1 = cursor.fetchall()

if resultados1:
    for fecha, cant in resultados1[:10]:  # Top 10 fechas
        es_hoy = "✅ HOY" if fecha == today else ""
        print(f"  {fecha} : {cant:,} registros {es_hoy}")
else:
    print("  ❌ Sin registros")

# 2. Verificar costo_wip_op
print("\n" + "=" * 70)
print("2️⃣ TABLA: costo_wip_op")
print("=" * 70)

query2 = f"""
SELECT 
  DISTINCT fecha_corrida,
  COUNT(*) as cantidad_registros
FROM {schema}.costo_wip_op
GROUP BY fecha_corrida
ORDER BY fecha_corrida DESC
"""

cursor.execute(query2)
resultados2 = cursor.fetchall()

if resultados2:
    for fecha, cant in resultados2[:10]:  # Top 10 fechas
        es_hoy = "✅ HOY" if fecha == today else ""
        print(f"  {fecha} : {cant:,} registros {es_hoy}")
else:
    print("  ❌ Sin registros")

# 3. MAX(fecha_corrida) en ambas tablas
print("\n" + "=" * 70)
print("3️⃣ ÚLTIMA FECHA_CORRIDA (MAX)")
print("=" * 70)

query3a = f"SELECT MAX(fecha_corrida) as max_fecha FROM {schema}.costo_op_detalle"
cursor.execute(query3a)
max_cod = cursor.fetchone()[0]
print(f"  costo_op_detalle    : {max_cod}")

query3b = f"SELECT MAX(fecha_corrida) as max_fecha FROM {schema}.costo_wip_op"
cursor.execute(query3b)
max_wip = cursor.fetchone()[0]
print(f"  costo_wip_op        : {max_wip}")

if max_cod == today:
    print(f"  ✅ costo_op_detalle TIENE datos de HOY")
else:
    print(f"  ⚠️  costo_op_detalle ÚLTIMA fecha: {max_cod} (no es hoy)")

if max_wip == today:
    print(f"  ✅ costo_wip_op TIENE datos de HOY")
else:
    print(f"  ⚠️  costo_wip_op ÚLTIMA fecha: {max_wip} (no es hoy)")

# 4. Contar registros de hoy en cada tabla
print("\n" + "=" * 70)
print("4️⃣ REGISTROS DE HOY")
print("=" * 70)

query4a = f"SELECT COUNT(*) FROM {schema}.costo_op_detalle WHERE fecha_corrida = ?"
cursor.execute(query4a, (today,))
cant_cod_hoy = cursor.fetchone()[0]
print(f"  costo_op_detalle    : {cant_cod_hoy:,} registros")

query4b = f"SELECT COUNT(*) FROM {schema}.costo_wip_op WHERE fecha_corrida = ?"
cursor.execute(query4b, (today,))
cant_wip_hoy = cursor.fetchone()[0]
print(f"  costo_wip_op        : {cant_wip_hoy:,} registros")

conn.close()
print("\n" + "=" * 70)
