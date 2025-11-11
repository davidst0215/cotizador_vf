# SCRIPT DE DIAGNSTICO PARA version_calculo
# Ejecuta esto para encontrar el problema exacto

import pyodbc
from config import settings


def diagnosticar_version_calculo():
    """Diagnstica qu est mal con version_calculo"""

    connection_string = settings.connection_string

    try:
        conn = pyodbc.connect(connection_string)
        cursor = conn.cursor()

        print(" DIAGNSTICO DE version_calculo")
        print("=" * 50)

        # 1. Verificar conexin a BD correcta
        cursor.execute("SELECT DB_NAME()")
        db_name = cursor.fetchone()[0]
        print(f" Conectado a BD: {db_name}")

        # 2. Verificar esquema disponible
        cursor.execute("SELECT SCHEMA_NAME FROM INFORMATION_SCHEMA.SCHEMATA")
        schemas = [row[0] for row in cursor.fetchall()]
        print(f" Esquemas disponibles: {schemas}")

        # 3. Verificar tablas
        cursor.execute(f"""
            SELECT TABLE_NAME
            FROM INFORMATION_SCHEMA.TABLES
            WHERE TABLE_SCHEMA = '{settings.db_schema}'
        """)
        tablas = [row[0] for row in cursor.fetchall()]
        print(f" Tablas: {tablas}")

        # 4. Verificar columnas en costo_op_detalle
        cursor.execute(f"""
            SELECT COLUMN_NAME, DATA_TYPE
            FROM INFORMATION_SCHEMA.COLUMNS
            WHERE TABLE_SCHEMA = '{settings.db_schema}'
            AND TABLE_NAME = 'costo_op_detalle'
            ORDER BY ORDINAL_POSITION
        """)
        columnas_costo = cursor.fetchall()
        print(" Columnas en costo_op_detalle:")
        for col, tipo in columnas_costo:
            print(f"   - {col} ({tipo})")

        # 5. PRUEBA ESPECFICA: Existe version_calculo?
        version_calculo_existe = any(
            col[0] == "version_calculo" for col in columnas_costo
        )
        print(
            f" Existe version_calculo en costo_op_detalle? {version_calculo_existe}"
        )

        # 6. Si existe, probar consulta simple
        if version_calculo_existe:
            cursor.execute(f"""
                SELECT DISTINCT version_calculo, COUNT(*) as registros
                FROM {settings.db_schema}.costo_op_detalle
                GROUP BY version_calculo
                ORDER BY registros DESC
            """)
            versiones = cursor.fetchall()
            print(" Versiones disponibles en costo_op_detalle:")
            for version, count in versiones:
                print(f"   - {version}: {count:,} registros")

            # 7. Probar consulta con parmetro (la que falla)
            print("\n PROBANDO CONSULTA PROBLEMTICA:")
            try:
                cursor.execute(
                    f"""
                    SELECT COUNT(*)
                    FROM {settings.db_schema}.costo_op_detalle
                    WHERE version_calculo = ?
                """,
                    ("FLUIDO",),
                )
                resultado = cursor.fetchone()[0]
                print(
                    f" Query con parmetro FUNCIONA: {resultado:,} registros FLUIDO"
                )

            except Exception as e:
                print(f" Query con parmetro FALLA: {e}")

            # 8. Probar consulta con fecha_corrida (la problemtica completa)
            print("\n PROBANDO CONSULTA CON fecha_corrida:")
            try:
                cursor.execute(
                    f"""
                    SELECT MAX(fecha_corrida) as fecha_max
                    FROM {settings.db_schema}.costo_op_detalle
                    WHERE version_calculo = ?
                """,
                    ("FLUIDO",),
                )
                resultado = cursor.fetchone()[0]
                print(f" Query completa FUNCIONA: {resultado}")

            except Exception as e:
                print(f" Query completa FALLA: {e}")

        # 9. Verificar otras tablas problemticas
        for tabla in ["historial_estilos", "resumen_wip_por_prenda"]:
            try:
                cursor.execute(f"""
                    SELECT COLUMN_NAME
                    FROM INFORMATION_SCHEMA.COLUMNS
                    WHERE TABLE_SCHEMA = 'saya'
                    AND TABLE_NAME = '{tabla}'
                    AND COLUMN_NAME = 'version_calculo'
                """)
                existe = cursor.fetchone()
                print(f" {tabla} tiene version_calculo: {existe is not None}")

                if existe:
                    cursor.execute(
                        f"SELECT DISTINCT version_calculo FROM {settings.db_schema}.{tabla}"
                    )
                    versiones = [row[0] for row in cursor.fetchall()]
                    print(f"   Versiones: {versiones}")

            except Exception as e:
                print(f" Error verificando {tabla}: {e}")

        conn.close()

    except Exception as e:
        print(f" ERROR DE CONEXIN: {e}")
        print(f"   Connection string: {connection_string}")


if __name__ == "__main__":
    diagnosticar_version_calculo()
