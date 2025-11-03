"""
Script para explorar completamente la base de datos PostgreSQL
"""
import psycopg2
from pathlib import Path
import os
from dotenv import load_dotenv

load_dotenv()

def explore_database():
    """
    Explora la estructura completa de la base de datos
    """

    print("\n" + "="*70)
    print("EXPLORACION COMPLETA DE LA BASE DE DATOS POSTGRESQL")
    print("="*70)

    try:
        connection_params = {
            'host': os.getenv('DB_HOST'),
            'port': int(os.getenv('DB_PORT')),
            'database': os.getenv('DB_NAME'),
            'user': os.getenv('DB_USER'),
            'sslmode': os.getenv('PGSSLMODE'),
            'sslcert': os.getenv('PGSSLCERT'),
            'sslkey': os.getenv('PGSSLKEY'),
            'sslrootcert': os.getenv('PGSSLROOTCERT'),
        }

        conn = psycopg2.connect(**connection_params)
        cursor = conn.cursor()

        # 1. Version
        print(f"\n[1. VERSION]")
        cursor.execute("SELECT version();")
        version = cursor.fetchone()[0]
        print(f"  {version}")

        # 2. Base de datos actual
        print(f"\n[2. BASE DE DATOS ACTUAL]")
        cursor.execute("SELECT current_database(), current_user;")
        db, user = cursor.fetchone()
        print(f"  Database: {db}")
        print(f"  User: {user}")

        # 3. Esquemas disponibles
        print(f"\n[3. ESQUEMAS DISPONIBLES]")
        cursor.execute("""
            SELECT schema_name FROM information_schema.schemata
            WHERE schema_name NOT IN ('pg_catalog', 'information_schema', 'pg_toast', 'pg_temp_1')
            ORDER BY schema_name;
        """)
        schemas = cursor.fetchall()
        for schema in schemas:
            print(f"  - {schema[0]}")

        # 4. Tablas por esquema
        print(f"\n[4. TABLAS POR ESQUEMA]")
        for schema in schemas:
            schema_name = schema[0]
            cursor.execute(f"""
                SELECT table_name FROM information_schema.tables
                WHERE table_schema = '{schema_name}'
                ORDER BY table_name;
            """)
            tables = cursor.fetchall()

            if tables:
                print(f"\n  Esquema: {schema_name}")
                for table in tables:
                    table_name = table[0]

                    # Contar filas
                    cursor.execute(f"SELECT COUNT(*) FROM {schema_name}.{table_name};")
                    count = cursor.fetchone()[0]
                    print(f"    - {table_name} ({count} registros)")

                    # Listar columnas
                    cursor.execute(f"""
                        SELECT column_name, data_type
                        FROM information_schema.columns
                        WHERE table_schema = '{schema_name}' AND table_name = '{table_name}'
                        ORDER BY ordinal_position;
                    """)
                    columns = cursor.fetchall()
                    for col in columns:
                        col_name, col_type = col
                        print(f"        - {col_name}: {col_type}")

        # 5. Vistas
        print(f"\n[5. VISTAS]")
        cursor.execute("""
            SELECT table_schema, table_name FROM information_schema.views
            WHERE table_schema NOT IN ('pg_catalog', 'information_schema')
            ORDER BY table_schema, table_name;
        """)
        views = cursor.fetchall()
        if views:
            for view in views:
                schema, view_name = view
                print(f"  {schema}.{view_name}")
        else:
            print(f"  (Ninguna)")

        # 6. Procedimientos almacenados / Funciones
        print(f"\n[6. FUNCIONES/PROCEDIMIENTOS]")
        cursor.execute("""
            SELECT proname FROM pg_proc
            WHERE proowner != 1  -- Excluir funciones del sistema
            ORDER BY proname;
        """)
        functions = cursor.fetchall()
        if functions:
            for func in functions:
                print(f"  - {func[0]}")
        else:
            print(f"  (Ninguna)")

        # 7. Secuencias
        print(f"\n[7. SECUENCIAS]")
        cursor.execute("""
            SELECT sequence_schema, sequence_name FROM information_schema.sequences
            WHERE sequence_schema NOT IN ('pg_catalog', 'information_schema')
            ORDER BY sequence_schema, sequence_name;
        """)
        sequences = cursor.fetchall()
        if sequences:
            for seq in sequences:
                schema, seq_name = seq
                print(f"  {schema}.{seq_name}")
        else:
            print(f"  (Ninguna)")

        # 8. Indices
        print(f"\n[8. INDICES]")
        cursor.execute("""
            SELECT indexname FROM pg_indexes
            WHERE schemaname NOT IN ('pg_catalog', 'information_schema')
            ORDER BY schemaname, indexname;
        """)
        indices = cursor.fetchall()
        if indices:
            for idx in indices:
                print(f"  - {idx[0]}")
        else:
            print(f"  (Ninguno)")

        cursor.close()
        conn.close()

        print(f"\n" + "="*70)
        print("EXPLORACION COMPLETADA EXITOSAMENTE")
        print("="*70)

        return True

    except Exception as e:
        print(f"\n[ERROR] {type(e).__name__}")
        print(f"  {str(e)}")
        return False

if __name__ == "__main__":
    explore_database()
