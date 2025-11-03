"""
Script para probar diferentes modos de SSL
"""
import psycopg2
from pathlib import Path
import os

# Cargar variables de entorno
from dotenv import load_dotenv
load_dotenv()

def test_ssl_mode(sslmode_name, sslmode_value, with_certs=False):
    """Prueba un modo de SSL específico"""

    print(f"\n{'='*60}")
    print(f"PROBANDO: sslmode={sslmode_value}")
    print(f"{'='*60}")

    try:
        connection_params = {
            'host': os.getenv('DB_HOST'),
            'port': int(os.getenv('DB_PORT')),
            'database': os.getenv('DB_NAME'),
            'user': os.getenv('DB_USER'),
            'sslmode': sslmode_value,
        }

        # Agregar certificados si se solicita
        if with_certs:
            pgsslcert = os.getenv('PGSSLCERT')
            pgsslkey = os.getenv('PGSSLKEY')
            pgsslrootcert = os.getenv('PGSSLROOTCERT')

            if pgsslcert and Path(pgsslcert).exists():
                connection_params['sslcert'] = pgsslcert
            if pgsslkey and Path(pgsslkey).exists():
                connection_params['sslkey'] = pgsslkey
            if pgsslrootcert and Path(pgsslrootcert).exists():
                connection_params['sslrootcert'] = pgsslrootcert

            print("[INFO] Usando certificados")
        else:
            print("[INFO] SIN certificados")

        print(f"[CONECTANDO] host={connection_params['host']}, port={connection_params['port']}")

        conn = psycopg2.connect(**connection_params)
        cursor = conn.cursor()

        cursor.execute("SELECT version();")
        version = cursor.fetchone()

        print(f"[EXITO] CONEXION ESTABLECIDA!")
        print(f"[VERSION] {version[0][:60]}...")

        # Listar tablas
        cursor.execute("""
            SELECT COUNT(*) FROM information_schema.tables
            WHERE table_schema = 'public';
        """)
        table_count = cursor.fetchone()[0]
        print(f"[TABLAS] {table_count} tablas disponibles en schema 'public'")

        cursor.close()
        conn.close()

        return True

    except Exception as e:
        print(f"[FALLO] {type(e).__name__}")
        error_msg = str(e)
        # Mostrar solo el error relevante
        if "certificate verify failed" in error_msg:
            print(f"[CAUSA] El certificado del servidor no puede ser verificado")
        elif "no pg_hba.conf entry" in error_msg:
            print(f"[CAUSA] Servidor rechaza conexion sin SSL")
        elif "connection requires" in error_msg:
            print(f"[CAUSA] Servidor requiere certificado de cliente")
        elif "FATAL" in error_msg:
            print(f"[CAUSA] {error_msg.split('FATAL')[1][:60] if 'FATAL' in error_msg else error_msg[:60]}")
        else:
            print(f"[CAUSA] {error_msg[:80]}")

        return False

if __name__ == "__main__":
    print("\n" + "="*60)
    print("PROANDO DIFERENTES MODOS DE SSL PARA POSTGRESQL")
    print("="*60)

    # Lista de modos a probar
    modos = [
        ("ALLOW (sin SSL)", "allow", False),
        ("PREFER (preferir SSL)", "prefer", True),
        ("REQUIRE (SSL obligatorio)", "require", True),
        ("VERIFY-CA (verificar CA)", "verify-ca", True),
        ("VERIFY-FULL (verificar completo)", "verify-full", True),
    ]

    resultados = {}

    for nombre, modo, usar_certs in modos:
        exito = test_ssl_mode(nombre, modo, usar_certs)
        resultados[nombre] = exito

    # Resumen
    print("\n" + "="*60)
    print("RESUMEN DE RESULTADOS")
    print("="*60)

    for nombre, exito in resultados.items():
        estado = "[EXITO]" if exito else "[FALLO]"
        print(f"{estado} {nombre}")

    # Encontrar el modo que funciona
    modo_funciona = [nombre for nombre, exito in resultados.items() if exito]

    if modo_funciona:
        print(f"\n[RECOMENDACION] Usa: sslmode={modo_funciona[0].split('(')[0].strip().lower()}")
    else:
        print("\n[PROBLEMA] Ningún modo de SSL funciona!")
        print("[SIGUIENTE] Verifica:")
        print("   1. Que los certificados sean correctos")
        print("   2. Que el servidor PostgreSQL esté accesible")
        print("   3. Que la red permita la conexion")
