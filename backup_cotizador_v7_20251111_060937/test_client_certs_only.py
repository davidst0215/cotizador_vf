"""
Probar conectar SOLO con certificados de cliente, sin CA Root
"""
import psycopg2
from pathlib import Path
import os
from dotenv import load_dotenv

load_dotenv()

def test_client_certs_only():
    """
    Intenta conectar SOLO con certificados de cliente (sslcert + sslkey)
    sin pasar el sslrootcert
    """

    print("\n" + "="*70)
    print("PROBANDO CON SOLO CERTIFICADOS DE CLIENTE (SIN CA ROOT)")
    print("="*70)

    try:
        cert_path = os.getenv('PGSSLCERT')
        key_path = os.getenv('PGSSLKEY')

        connection_params = {
            'host': os.getenv('DB_HOST'),
            'port': int(os.getenv('DB_PORT')),
            'database': os.getenv('DB_NAME'),
            'user': os.getenv('DB_USER'),
            'sslmode': 'require',  # SSL obligatorio
            'sslcert': cert_path,
            'sslkey': key_path,
            # NOTA: NO incluimos sslrootcert aqui
        }

        print(f"\n[PARAMETROS]")
        print(f"  host: {connection_params['host']}")
        print(f"  port: {connection_params['port']}")
        print(f"  database: {connection_params['database']}")
        print(f"  user: {connection_params['user']}")
        print(f"  sslmode: {connection_params['sslmode']}")
        print(f"  sslcert: {Path(cert_path).name}")
        print(f"  sslkey: {Path(key_path).name}")
        print(f"  sslrootcert: NO INCLUIDO (esto es lo importante)")

        print(f"\n[INTENTANDO CONECTAR]...")
        conn = psycopg2.connect(**connection_params)
        cursor = conn.cursor()

        cursor.execute("SELECT version();")
        version = cursor.fetchone()

        print(f"\n[EXITO] CONEXION ESTABLECIDA!")
        print(f"\nPostgreSQL Version:")
        print(f"  {version[0]}")

        # Listar bases de datos
        cursor.execute("""
            SELECT datname FROM pg_database
            WHERE datistemplate = false
            ORDER BY datname;
        """)

        databases = cursor.fetchall()
        print(f"\n[BASES DE DATOS] Disponibles:")
        for db in databases:
            print(f"  - {db[0]}")

        # Listar tablas
        cursor.execute("""
            SELECT table_name
            FROM information_schema.tables
            WHERE table_schema = 'public'
            ORDER BY table_name;
        """)

        tables = cursor.fetchall()
        print(f"\n[TABLAS EN PUBLIC] Total: {len(tables)}")
        for table in tables:
            print(f"  - {table[0]}")

        cursor.close()
        conn.close()

        print(f"\n[OK] FUNCIONA!")
        return True

    except Exception as e:
        print(f"\n[ERROR] {type(e).__name__}")
        print(f"  Mensaje: {str(e)[:150]}")
        return False

if __name__ == "__main__":
    exito = test_client_certs_only()

    if exito:
        print("\n" + "="*70)
        print("SOLUCION ENCONTRADA")
        print("="*70)
        print("""
El problema era que sslrootcert NO es necesario si el servidor
usa certificados del almacen de Windows.

Actualiza el .env asi:
  PGSSLMODE=require
  PGSSLCERT=C:\\Users\\siste\\OneDrive\\...\\david (1).crt
  PGSSLKEY=C:\\Users\\siste\\OneDrive\\...\\david.pk8
  # PGSSLROOTCERT se puede comentar o dejar en blanco
        """)
    else:
        print("\n[FALLO] Aun sin sslrootcert no funciona")
        print("\nSiguiente paso: Confirma que DBeaver REALMENTE esta conectado")
