"""
Script para probar si la conexion basica funciona sin verificacion SSL
"""
import psycopg2
from pathlib import Path
import os
from dotenv import load_dotenv

load_dotenv()

def test_allow_mode():
    """
    Prueba sin verificacion SSL para ver si es un problema de certificado
    o de la conexion basica
    """

    print("\n" + "="*70)
    print("PROBANDO CONEXION SIN VERIFICACION SSL (sslmode=allow)")
    print("="*70)

    try:
        # SIN certificados, solo la conexion basica
        connection_params = {
            'host': os.getenv('DB_HOST'),
            'port': int(os.getenv('DB_PORT')),
            'database': os.getenv('DB_NAME'),
            'user': os.getenv('DB_USER'),
            'sslmode': 'allow',  # Permite SSL pero no verifica
        }

        print(f"\n[PARAMETROS]")
        print(f"  host: {connection_params['host']}")
        print(f"  port: {connection_params['port']}")
        print(f"  database: {connection_params['database']}")
        print(f"  user: {connection_params['user']}")
        print(f"  sslmode: {connection_params['sslmode']}")
        print(f"  (SIN certificados)")

        print(f"\n[INTENTANDO CONECTAR]...")
        conn = psycopg2.connect(**connection_params)
        cursor = conn.cursor()

        cursor.execute("SELECT version();")
        version = cursor.fetchone()

        print(f"\n[EXITO] CONEXION ESTABLECIDA (sin verificacion SSL)")
        print(f"\nPostgreSQL Version:")
        print(f"  {version[0]}")

        cursor.close()
        conn.close()

        print(f"\n[OK] La conexion basica funciona sin verificacion")
        return True

    except Exception as e:
        print(f"\n[ERROR] {type(e).__name__}")
        print(f"  Mensaje: {str(e)[:100]}")
        return False

if __name__ == "__main__":
    exito = test_allow_mode()

    if exito:
        print("\n" + "="*70)
        print("CONCLUSION")
        print("="*70)
        print("""
Si esta conexion funciona, significa:
  - El servidor PostgreSQL esta accesible
  - La autenticacion de usuario funciona
  - El problema es SOLO con la verificacion SSL

En ese caso, probablemente DBeaver:
  - Tiene una forma diferente de manejar certificados
  - O tiene configurada una opcion de "skip verification"
        """)
    else:
        print("\n[FALLO] Ni siquiera sin SSL funciona - problema diferente")
