#!/usr/bin/env python3
"""
Validar datos de estilo 18420 en COSTO_OP_DETALLE
"""

import sys
sys.path.insert(0, 'src')

from smp.config import settings
import psycopg2

def validar_estilo_18420():
    """Conecta directamente a la BD y valida 18420"""

    try:
        conn = psycopg2.connect(
            host=settings.db_host,
            port=settings.db_port,
            database=settings.db_name,
            user=settings.db_user,
            password=settings.db_password,
            sslmode='require'
        )
        cursor = conn.cursor()

        print("\n" + "="*80)
        print("VALIDACIÓN: ESTILO 18420 EN COSTO_OP_DETALLE")
        print("="*80)

        # 1. Contar total de registros
        print("\n1️⃣  TOTAL DE REGISTROS PARA ESTILO 18420:")
        query1 = f"""
        SELECT COUNT(*) as total
        FROM {settings.db_schema}.costo_op_detalle
        WHERE estilo_propio = '18420'
        """
        cursor.execute(query1)
        resultado = cursor.fetchone()
        total_registros = resultado[0] if resultado else 0
        print(f"Total registros: {total_registros}")

        # 2. Información de fechas
        print("\n2️⃣  FECHAS DE LOS REGISTROS:")
        query2 = f"""
        SELECT
            MIN(fecha_facturacion) as fecha_minima,
            MAX(fecha_facturacion) as fecha_maxima,
            COUNT(DISTINCT DATE_TRUNC('month', fecha_facturacion)) as meses_diferentes
        FROM {settings.db_schema}.costo_op_detalle
        WHERE estilo_propio = '18420'
        """
        cursor.execute(query2)
        resultado = cursor.fetchone()
        if resultado:
            fecha_min, fecha_max, meses_diferentes = resultado
            print(f"Fecha mínima: {fecha_min}")
            print(f"Fecha máxima: {fecha_max}")
            print(f"Meses diferentes: {meses_diferentes}")

            # Calcular diferencia en meses
            from dateutil.relativedelta import relativedelta
            if fecha_min and fecha_max:
                diff = relativedelta(fecha_max, fecha_min)
                meses_totales = diff.years * 12 + diff.months
                print(f"Diferencia total: {meses_totales} meses")

        # 3. Desglose por version_calculo
        print("\n3️⃣  DESGLOSE POR VERSION_CALCULO:")
        query3 = f"""
        SELECT
            version_calculo,
            COUNT(*) as total,
            MIN(fecha_facturacion) as fecha_min,
            MAX(fecha_facturacion) as fecha_max
        FROM {settings.db_schema}.costo_op_detalle
        WHERE estilo_propio = '18420'
        GROUP BY version_calculo
        ORDER BY version_calculo
        """
        cursor.execute(query3)
        resultados = cursor.fetchall()
        for version, total, fecha_min, fecha_max in resultados:
            print(f"  {version}: {total} registros | {fecha_min} a {fecha_max}")

        # 4. Ver ALL los registros
        print("\n4️⃣  DETALLE COMPLETO DE TODOS LOS REGISTROS:")
        query4 = f"""
        SELECT
            cod_ordpro,
            estilo_propio,
            prendas_requeridas,
            costo_textil,
            costo_manufactura,
            costo_avios,
            costo_materia_prima,
            costo_indirecto_fijo,
            gasto_administracion,
            gasto_ventas,
            fecha_facturacion,
            version_calculo,
            fecha_corrida
        FROM {settings.db_schema}.costo_op_detalle
        WHERE estilo_propio = '18420'
        ORDER BY fecha_facturacion DESC
        """
        cursor.execute(query4)
        resultados = cursor.fetchall()

        for i, row in enumerate(resultados, 1):
            cod_ordpro, estilo, prendas, costo_textil, costo_manuf, costo_avios, costo_mp, \
            costo_ind, gasto_admin, gasto_ventas, fecha_fact, version, fecha_corrida = row

            print(f"\n  Registro {i}:")
            print(f"    OP: {cod_ordpro}")
            print(f"    Prendas: {prendas}")
            print(f"    Costos: Textil={costo_textil}, Manuf={costo_manuf}, Avios={costo_avios}, MP={costo_mp}")
            print(f"    Gastos: Indirecto={costo_ind}, Admin={gasto_admin}, Ventas={gasto_ventas}")
            print(f"    Fecha facturación: {fecha_fact}")
            print(f"    Version: {version}")
            print(f"    Fecha corrida: {fecha_corrida}")

        # 5. Validar con filtros de 12 meses
        print("\n5️⃣  REGISTROS CON FILTRO DE 12 MESES (DESDE MAX(fecha_facturacion)):")
        query5 = f"""
        SELECT COUNT(*) as total
        FROM {settings.db_schema}.costo_op_detalle
        WHERE estilo_propio = '18420'
          AND fecha_facturacion >= (
            SELECT (MAX(fecha_facturacion) - INTERVAL '12 months')
            FROM {settings.db_schema}.costo_op_detalle
            WHERE version_calculo = 'FLUIDO'
          )
          AND version_calculo = 'FLUIDO'
        """
        cursor.execute(query5)
        resultado = cursor.fetchone()
        registros_12m = resultado[0] if resultado else 0
        print(f"Registros últimos 12 meses (FLUIDO): {registros_12m}")

        # 6. Validar con filtros de 36 meses
        print("\n6️⃣  REGISTROS CON FILTRO DE 36 MESES (DESDE MAX(fecha_facturacion)):")
        query6 = f"""
        SELECT COUNT(*) as total
        FROM {settings.db_schema}.costo_op_detalle
        WHERE estilo_propio = '18420'
          AND fecha_facturacion >= (
            SELECT (MAX(fecha_facturacion) - INTERVAL '36 months')
            FROM {settings.db_schema}.costo_op_detalle
            WHERE version_calculo = 'FLUIDO'
          )
          AND version_calculo = 'FLUIDO'
        """
        cursor.execute(query6)
        resultado = cursor.fetchone()
        registros_36m = resultado[0] if resultado else 0
        print(f"Registros últimos 36 meses (FLUIDO): {registros_36m}")

        cursor.close()
        conn.close()

        print("\n" + "="*80)
        print("CONCLUSIÓN:")
        if registros_12m > 0:
            print("✓ Con 12 meses: ENCONTRARÁ DATOS")
        else:
            print("✗ Con 12 meses: NO ENCONTRARÁ DATOS")

        if registros_36m > 0:
            print(f"✓ Con 36 meses: ENCONTRARÁ DATOS ({registros_36m} registros)")
        else:
            print("✗ Con 36 meses: NO ENCONTRARÁ DATOS")
        print("="*80 + "\n")

    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    validar_estilo_18420()
