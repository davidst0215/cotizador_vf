"""
Probar con rutas absolutas y formato especifico
"""
import psycopg2
from pathlib import Path
import os
from dotenv import load_dotenv

load_dotenv()

def test_absolute_paths():
    """
    Intenta conectar con rutas absolutas sin variables de entorno
    """

    print("\n" + "="*70)
    print("PROBANDO CON RUTAS ABSOLUTAS EXPLÍCITAS")
    print("="*70)

    # Rutas absolutas hard-coded como existen en Windows
    cert_path = r"C:\Users\siste\OneDrive\SAYA INVESTMENTS\calidad de venta\audios\piloto_abril\david (1).crt"
    key_path = r"C:\Users\siste\OneDrive\SAYA INVESTMENTS\calidad de venta\audios\piloto_abril\david.pk8"
    root_cert_path = r"C:\Users\siste\OneDrive\SAYA INVESTMENTS\calidad de venta\audios\piloto_abril\root.crt"

    print(f"\n[VERIFICANDO ARCHIVOS]")
    print(f"  Certificado: {Path(cert_path).exists()} - {Path(cert_path).name}")
    print(f"  Clave: {Path(key_path).exists()} - {Path(key_path).name}")
    print(f"  CA Root: {Path(root_cert_path).exists()} - {Path(root_cert_path).name}")

    try:
        # Intenta con verify-ca como DBeaver
        connection_params = {
            'host': '18.118.59.50',
            'port': 5432,
            'database': 'tdv',
            'user': 'david',
            'sslmode': 'verify-ca',
            'sslcert': cert_path,
            'sslkey': key_path,
            'sslrootcert': root_cert_path,
        }

        print(f"\n[CONECTANDO CON verify-ca]...")
        conn = psycopg2.connect(**connection_params)
        cursor = conn.cursor()

        cursor.execute("SELECT version();")
        version = cursor.fetchone()

        print(f"[EXITO] CONEXION ESTABLECIDA!")
        print(f"Version: {version[0]}")

        cursor.close()
        conn.close()
        return True

    except Exception as e:
        print(f"[ERROR con verify-ca] {str(e)[:80]}")

    # Intenta con require
    try:
        print(f"\n[CONECTANDO CON require]...")
        connection_params = {
            'host': '18.118.59.50',
            'port': 5432,
            'database': 'tdv',
            'user': 'david',
            'sslmode': 'require',
            'sslcert': cert_path,
            'sslkey': key_path,
        }

        conn = psycopg2.connect(**connection_params)
        cursor = conn.cursor()

        cursor.execute("SELECT version();")
        version = cursor.fetchone()

        print(f"[EXITO] CONEXION ESTABLECIDA!")
        print(f"Version: {version[0]}")

        cursor.close()
        conn.close()
        return True

    except Exception as e:
        print(f"[ERROR con require] {str(e)[:80]}")
        return False

if __name__ == "__main__":
    test_absolute_paths()
