"""
Script para inspeccionar la estructura y datos de las tablas
"""
import os
import sys
from pathlib import Path

# Agregar el directorio src al path
sys.path.insert(0, str(Path(__file__).parent))

from src.smp.config import settings
import psycopg2

def inspect_database():
    """Inspecciona la estructura de la BD"""
    try:
        # Conectar a PostgreSQL
        conn = psycopg2.connect(
            host=settings.db_host,
            port=settings.db_port,
            user=settings.db_user,
            password=settings.db_password,
            database=settings.db_name
        )

        cursor = conn.cursor()

        # Consulta 1: Listar todas las tablas en el schema
        print("="*80)
        print("TABLAS EN EL SCHEMA:", settings.db_schema)
        print("="*80)

        cursor.execute(f"""
        SELECT table_name
        FROM information_schema.tables
        WHERE table_schema = '{settings.db_schema}'
        ORDER BY table_name
        """)

        tables = cursor.fetchall()
        for table in tables:
            print(f"  - {table[0]}")

        # Consulta 2: Estructura de costo_op_detalle
        print("\n" + "="*80)
        print("COLUMNAS DE costo_op_detalle")
        print("="*80)

        cursor.execute(f"""
        SELECT column_name, data_type
        FROM information_schema.columns
        WHERE table_schema = '{settings.db_schema}'
          AND table_name = 'costo_op_detalle'
        ORDER BY ordinal_position
        """)

        columns = cursor.fetchall()
        for col in columns:
            print(f"  {col[0]:<30} {col[1]}")

        # Consulta 3: Primeras 5 OPs con MONTAIGNE
        print("\n" + "="*80)
        print("OPs CON MONTAIGNE EN CLIENTE")
        print("="*80)

        cursor.execute(f"""
        SELECT
            cod_ordpro,
            cliente,
            tipo_de_producto,
            prendas_requeridas,
            version_calculo
        FROM {settings.db_schema}.costo_op_detalle
        WHERE cliente ILIKE '%MONTAIGNE%'
        LIMIT 10
        """)

        rows = cursor.fetchall()
        print(f"Encontrados {len(rows)} OPs")
        for row in rows:
            print(f"  OP: {row[0]:<10} Cliente: {row[1]:<40} Tipo: {row[2]:<20} Prendas: {row[3]}")

        # Consulta 4: Combinaciones de MONTAIGNE + Polo Box
        print("\n" + "="*80)
        print("OPs CON MONTAIGNE + POLO BOX")
        print("="*80)

        cursor.execute(f"""
        SELECT
            COUNT(*) as cantidad,
            cliente,
            tipo_de_producto
        FROM {settings.db_schema}.costo_op_detalle
        WHERE UPPER(TRIM(cliente)) LIKE '%MONTAIGNE%'
          AND UPPER(TRIM(tipo_de_producto)) LIKE '%POLO%BOX%'
        GROUP BY cliente, tipo_de_producto
        """)

        rows = cursor.fetchall()
        print(f"Encontradas {len(rows)} combinaciones")
        for row in rows:
            print(f"  Cantidad: {row[0]:<5} Cliente: '{row[1]}' Tipo: '{row[2]}'")

        # Consulta 5: Todos los tipos de producto que comienzan con Polo
        print("\n" + "="*80)
        print("TODOS LOS TIPOS COMO 'POLO...'")
        print("="*80)

        cursor.execute(f"""
        SELECT DISTINCT tipo_de_producto
        FROM {settings.db_schema}.costo_op_detalle
        WHERE tipo_de_producto ILIKE 'POLO%'
        ORDER BY tipo_de_producto
        """)

        rows = cursor.fetchall()
        print(f"Encontrados {len(rows)} tipos")
        for row in rows:
            print(f"  '{row[0]}'")

        cursor.close()
        conn.close()

    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    inspect_database()
