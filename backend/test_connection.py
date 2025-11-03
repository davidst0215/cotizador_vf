"""
Script para probar conexion a PostgreSQL
"""
import psycopg2
from pathlib import Path
import os
import sys

# Configurar encoding UTF-8
if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')

# Cargar variables de entorno
from dotenv import load_dotenv
load_dotenv()

def test_postgres_connection():
    """Prueba conexion a PostgreSQL"""
    try:
        print("[INFO] Intentando conectar a PostgreSQL...")
        print(f"   Host: {os.getenv('DB_HOST')}")
        print(f"   Puerto: {os.getenv('DB_PORT')}")
        print(f"   Usuario: {os.getenv('DB_USER')}")
        print(f"   Base de datos: {os.getenv('DB_NAME')}")

        connection_params = {
            'host': os.getenv('DB_HOST'),
            'port': int(os.getenv('DB_PORT')),
            'database': os.getenv('DB_NAME'),
            'user': os.getenv('DB_USER'),
            'sslmode': os.getenv('PGSSLMODE', 'disable'),
        }

        # Agregar certificados si existen
        sslcert = os.getenv('PGSSLCERT')
        sslkey = os.getenv('PGSSLKEY')
        sslrootcert = os.getenv('PGSSLROOTCERT')

        if sslcert and Path(sslcert).exists():
            connection_params['sslcert'] = sslcert
            print(f"   [OK] Certificado cliente: {sslcert}")

        if sslkey and Path(sslkey).exists():
            connection_params['sslkey'] = sslkey
            print(f"   [OK] Clave privada: {sslkey}")

        if sslrootcert and Path(sslrootcert).exists():
            connection_params['sslrootcert'] = sslrootcert
            print(f"   [OK] Certificado CA: {sslrootcert}")

        # Intentar conexión
        print("\n[CONECTANDO] Estableciendo conexion...")
        conn = psycopg2.connect(**connection_params)
        cursor = conn.cursor()

        # Probar query
        cursor.execute("SELECT version();")
        version = cursor.fetchone()

        print("\n[EXITO] CONEXION EXITOSA!")
        print(f"   PostgreSQL version: {version[0]}")

        # Listar tablas
        cursor.execute("""
            SELECT table_name
            FROM information_schema.tables
            WHERE table_schema = 'public'
            ORDER BY table_name;
        """)

        tables = cursor.fetchall()
        print(f"\n[TABLAS] Disponibles ({len(tables)}):")
        for table in tables:
            print(f"   - {table[0]}")

        # Listar columnas de tablas importantes
        for tabla in ['costo_op_detalle', 'historial_estilos']:
            cursor.execute(f"""
                SELECT column_name, data_type
                FROM information_schema.columns
                WHERE table_name = '{tabla}'
                ORDER BY ordinal_position;
            """)
            columnas = cursor.fetchall()
            if columnas:
                print(f"\n[ESQUEMA] {tabla}:")
                for col_name, col_type in columnas:
                    print(f"   - {col_name}: {col_type}")

        cursor.close()
        conn.close()

        return True

    except Exception as e:
        print(f"\n[ERROR] CONEXION FALLIDA!")
        print(f"   {type(e).__name__}: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_postgres_connection()
    exit(0 if success else 1)
