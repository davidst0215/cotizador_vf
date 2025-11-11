"""
Script de diagnostico detallado para PostgreSQL
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

def log(nivel, msg):
    """Función de logging"""
    print(f"[{nivel:8}] {msg}")

def test_postgres_connection_debug():
    """Prueba conexion a PostgreSQL con logs detallados"""

    log("INICIO", "=== DIAGNOSTICO DE CONEXION A POSTGRESQL ===\n")

    # 1. Verificar variables de entorno
    log("CONFIG", "1. VARIABLES DE ENTORNO:")
    db_host = os.getenv('DB_HOST')
    db_port = os.getenv('DB_PORT')
    db_user = os.getenv('DB_USER')
    db_password = os.getenv('DB_PASSWORD')
    db_name = os.getenv('DB_NAME')
    db_schema = os.getenv('DB_SCHEMA')
    pgsslmode = os.getenv('PGSSLMODE')
    pgsslcert = os.getenv('PGSSLCERT')
    pgsslkey = os.getenv('PGSSLKEY')
    pgsslrootcert = os.getenv('PGSSLROOTCERT')

    log("INFO", f"   DB_HOST: {db_host}")
    log("INFO", f"   DB_PORT: {db_port}")
    log("INFO", f"   DB_USER: {db_user}")
    log("INFO", f"   DB_PASSWORD: {'*' * len(db_password) if db_password else '(vacio)'}")
    log("INFO", f"   DB_NAME: {db_name}")
    log("INFO", f"   DB_SCHEMA: {db_schema}")
    log("INFO", f"   PGSSLMODE: {pgsslmode}")
    log("INFO", f"   PGSSLCERT: {pgsslcert}")
    log("INFO", f"   PGSSLKEY: {pgsslkey}")
    log("INFO", f"   PGSSLROOTCERT: {pgsslrootcert}")

    # 2. Verificar que existen los archivos de certificados
    log("ARCHIVOS", "\n2. VERIFICANDO ARCHIVOS DE CERTIFICADOS:")

    cert_paths = {
        'PGSSLCERT': pgsslcert,
        'PGSSLKEY': pgsslkey,
        'PGSSLROOTCERT': pgsslrootcert
    }

    for cert_name, cert_path in cert_paths.items():
        if cert_path:
            existe = Path(cert_path).exists()
            estado = "EXISTE" if existe else "NO EXISTE"
            log("ARCH", f"   {cert_name}: {estado}")
            log("ARCH", f"      Ruta: {cert_path}")
            if existe:
                tamanio = Path(cert_path).stat().st_size
                log("ARCH", f"      Tamanio: {tamanio} bytes")
        else:
            log("ARCH", f"   {cert_name}: NO CONFIGURADO")

    # 3. Preparar parámetros de conexión
    log("CONEX", "\n3. PREPARANDO PARAMETROS DE CONEXION:")

    connection_params = {
        'host': db_host,
        'port': int(db_port),
        'database': db_name,
        'user': db_user,
        'sslmode': pgsslmode or 'disable',
    }

    log("PARAM", f"   host: {connection_params['host']}")
    log("PARAM", f"   port: {connection_params['port']}")
    log("PARAM", f"   database: {connection_params['database']}")
    log("PARAM", f"   user: {connection_params['user']}")
    log("PARAM", f"   sslmode: {connection_params['sslmode']}")

    # Agregar contraseña si existe
    if db_password:
        connection_params['password'] = db_password
        log("PARAM", f"   password: {'*' * len(db_password)}")

    # Agregar certificados si existen y están configurados
    if pgsslcert and Path(pgsslcert).exists():
        connection_params['sslcert'] = pgsslcert
        log("PARAM", f"   sslcert: {pgsslcert}")

    if pgsslkey and Path(pgsslkey).exists():
        connection_params['sslkey'] = pgsslkey
        log("PARAM", f"   sslkey: {pgsslkey}")

    if pgsslrootcert and Path(pgsslrootcert).exists():
        connection_params['sslrootcert'] = pgsslrootcert
        log("PARAM", f"   sslrootcert: {pgsslrootcert}")

    # 4. Intentar conexión
    log("CONEX", "\n4. INTENTANDO CONECTAR...")

    try:
        log("DEBUG", "   Llamando psycopg2.connect()...")
        conn = psycopg2.connect(**connection_params)
        log("EXITO", "   Conexion establecida!")

        cursor = conn.cursor()
        log("DEBUG", "   Cursor creado")

        # 5. Probar query
        log("QUERY", "\n5. PROBANDO QUERY:")
        log("DEBUG", "   SELECT version();")

        cursor.execute("SELECT version();")
        version = cursor.fetchone()

        log("EXITO", f"   Respuesta: {version[0][:80]}...")

        # 6. Listar tablas
        log("TABLAS", "\n6. LISTANDO TABLAS EN SCHEMA 'public':")

        cursor.execute("""
            SELECT table_name
            FROM information_schema.tables
            WHERE table_schema = 'public'
            ORDER BY table_name;
        """)

        tables = cursor.fetchall()
        log("INFO", f"   Total de tablas: {len(tables)}")

        for table in tables:
            log("TABLA", f"   - {table[0]}")

        # 7. Listar columnas de tablas importantes
        log("SCHEMA", "\n7. ESQUEMA DE TABLAS IMPORTANTES:")

        for tabla in ['costo_op_detalle', 'historial_estilos']:
            log("DEBUG", f"   Obteniendo esquema de '{tabla}'...")

            cursor.execute(f"""
                SELECT column_name, data_type
                FROM information_schema.columns
                WHERE table_name = '{tabla}'
                ORDER BY ordinal_position;
            """)

            columnas = cursor.fetchall()

            if columnas:
                log("TABLA", f"   {tabla} ({len(columnas)} columnas):")
                for col_name, col_type in columnas:
                    log("COL", f"      - {col_name}: {col_type}")
            else:
                log("WARN", f"   {tabla}: NO ENCONTRADA")

        # 8. Estadísticas
        log("STATS", "\n8. ESTADISTICAS:")

        cursor.execute("""
            SELECT schemaname, tablename, pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) as size
            FROM pg_tables
            WHERE schemaname = 'public'
            ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC
            LIMIT 10;
        """)

        stats = cursor.fetchall()
        for schema, tabla, tamanio in stats:
            log("STAT", f"   {tabla}: {tamanio}")

        cursor.close()
        conn.close()

        log("EXITO", "\n=== CONEXION COMPLETAMENTE EXITOSA ===\n")
        return True

    except psycopg2.OperationalError as e:
        log("ERROR", f"\n!!! ERROR OPERACIONAL !!!")
        log("ERROR", f"   Tipo: {type(e).__name__}")
        log("ERROR", f"   Mensaje: {str(e)}")

        # Analizar el error
        error_str = str(e)
        if "does not exist" in error_str:
            log("DIAG", "   DIAGNOSTICO: Archivo de certificado no encontrado")
            log("DIAG", "   ACCION: Verifica las rutas de los certificados")
        elif "no pg_hba.conf entry" in error_str:
            log("DIAG", "   DIAGNOSTICO: Servidor rechaza conexion (pg_hba.conf)")
            log("DIAG", "   ACCION: Se requiere SSL")
        elif "connection requires a valid client certificate" in error_str:
            log("DIAG", "   DIAGNOSTICO: Se requiere certificado de cliente")
            log("DIAG", "   ACCION: Configura PGSSLCERT y PGSSLKEY")
        elif "FATAL" in error_str:
            log("DIAG", "   DIAGNOSTICO: Error fatal del servidor")
            if "password authentication failed" in error_str:
                log("DIAG", "   CAUSA: Credenciales incorrectas")
            elif "no encryption" in error_str:
                log("DIAG", "   CAUSA: Conexion sin SSL no permitida")

        return False

    except Exception as e:
        log("ERROR", f"\n!!! ERROR INESPERADO !!!")
        log("ERROR", f"   Tipo: {type(e).__name__}")
        log("ERROR", f"   Mensaje: {str(e)}")

        import traceback
        log("TRACE", "\n   TRACEBACK:")
        for line in traceback.format_exc().split('\n'):
            log("TRACE", f"   {line}")

        return False

if __name__ == "__main__":
    success = test_postgres_connection_debug()
    exit(0 if success else 1)
