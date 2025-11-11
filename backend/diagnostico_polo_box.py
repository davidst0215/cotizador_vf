#!/usr/bin/env python3
"""
Script de diagnóstico para validar datos de "polo box" en COSTO_OP_DETALLE
"""

import asyncio
import sys
sys.path.insert(0, 'src')

from smp.config import settings
from smp.database import TDVDatabase

async def main():
    db = TDVDatabase()

    print("\n" + "="*80)
    print("DIAGNÓSTICO: ESTILO 'POLO BOX'")
    print("="*80)

    # 1. Verificar si existe con prendas_requeridas > 0
    print("\n1️⃣  REGISTROS CON prendas_requeridas > 0:")
    query1 = f"""
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
        version_calculo
    FROM {settings.db_schema}.costo_op_detalle
    WHERE UPPER(estilo_propio) LIKE '%POLO BOX%'
        AND prendas_requeridas > 0
    ORDER BY fecha_facturacion DESC
    LIMIT 10
    """

    try:
        resultados = await db.query(query1)
        if resultados:
            print(f"✓ Encontrados {len(resultados)} registros:")
            for row in resultados:
                print(f"  OP: {row.get('cod_ordpro')} | Prendas: {row.get('prendas_requeridas')} | "
                      f"Indirecto: {row.get('costo_indirecto_fijo')} | "
                      f"Admin: {row.get('gasto_administracion')} | "
                      f"Ventas: {row.get('gasto_ventas')} | "
                      f"Fecha: {row.get('fecha_facturacion')}")
        else:
            print("✗ No hay registros con prendas_requeridas > 0")
    except Exception as e:
        print(f"✗ Error: {e}")

    # 2. Verificar sin filtro de gastos
    print("\n2️⃣  MISMO QUERY SIN FILTROS DE GASTOS > 0:")
    query2 = f"""
    SELECT
        cod_ordpro,
        estilo_propio,
        prendas_requeridas,
        costo_indirecto_fijo,
        gasto_administracion,
        gasto_ventas,
        fecha_facturacion
    FROM {settings.db_schema}.costo_op_detalle
    WHERE UPPER(estilo_propio) LIKE '%POLO BOX%'
        AND prendas_requeridas > 0
    ORDER BY fecha_facturacion DESC
    LIMIT 10
    """

    try:
        resultados = await db.query(query2)
        if resultados:
            print(f"✓ Encontrados {len(resultados)} registros:")
            for row in resultados:
                indirecto = row.get('costo_indirecto_fijo')
                admin = row.get('gasto_administracion')
                ventas = row.get('gasto_ventas')
                print(f"  OP: {row.get('cod_ordpro')} | Indirecto: {indirecto} (>0: {indirecto > 0}) | "
                      f"Admin: {admin} (>0: {admin > 0}) | "
                      f"Ventas: {ventas} (>0: {ventas > 0})")
        else:
            print("✗ No hay registros")
    except Exception as e:
        print(f"✗ Error: {e}")

    # 3. Contar total de variaciones del estilo
    print("\n3️⃣  TODAS LAS VARIACIONES DE POLO BOX:")
    query3 = f"""
    SELECT DISTINCT estilo_propio, COUNT(*) as total
    FROM {settings.db_schema}.costo_op_detalle
    WHERE UPPER(estilo_propio) LIKE '%POLO BOX%'
    GROUP BY estilo_propio
    ORDER BY total DESC
    """

    try:
        resultados = await db.query(query3)
        if resultados:
            print(f"✓ Encontradas {len(resultados)} variaciones:")
            for row in resultados:
                print(f"  {row.get('estilo_propio')}: {row.get('total')} registros")
        else:
            print("✗ No hay registros")
    except Exception as e:
        print(f"✗ Error: {e}")

    # 4. Validar EXACTAMENTE la query que usa obtener_gastos_por_estilo_recurrente
    print("\n4️⃣  QUERY EXACTA DE obtener_gastos_por_estilo_recurrente (POLO BOX):")
    query4 = f"""
    SELECT
        costo_indirecto_fijo,
        gasto_administracion,
        gasto_ventas,
        prendas_requeridas,
        cod_ordpro,
        ROW_NUMBER() OVER (ORDER BY fecha_facturacion DESC) as rn
    FROM {settings.db_schema}.costo_op_detalle
    WHERE estilo_propio = ?
        AND version_calculo = ?
        AND fecha_facturacion >= (
            SELECT (MAX(fecha_facturacion) - INTERVAL '12 months')
            FROM {settings.db_schema}.costo_op_detalle
            WHERE version_calculo = ?
        )
        AND prendas_requeridas > 0
        AND costo_indirecto_fijo > 0
        AND gasto_administracion > 0
        AND gasto_ventas > 0
    ORDER BY fecha_facturacion DESC
    """

    try:
        resultados = await db.query(query4, ('POLO BOX', 'FLUIDO', 'FLUIDO'))
        if resultados:
            print(f"✓ Encontrados {len(resultados)} registros CON TODOS LOS FILTROS:")
            for row in resultados:
                print(f"  OP: {row.get('cod_ordpro')} | Indirecto: {row.get('costo_indirecto_fijo')} | "
                      f"Admin: {row.get('gasto_administracion')} | "
                      f"Ventas: {row.get('gasto_ventas')}")
        else:
            print("✗ SIN REGISTROS - Ese es el problema!")
            print("\nInvestigando por qué se pierden...")

            # Ver cuáles registros fallan en cada filtro
            query_debug = f"""
            SELECT
                cod_ordpro,
                estilo_propio,
                prendas_requeridas,
                costo_indirecto_fijo,
                gasto_administracion,
                gasto_ventas,
                fecha_facturacion,
                version_calculo
            FROM {settings.db_schema}.costo_op_detalle
            WHERE estilo_propio = 'POLO BOX'
                AND version_calculo = 'FLUIDO'
            ORDER BY fecha_facturacion DESC
            """
            debug_resultados = await db.query(query_debug)
            if debug_resultados:
                print(f"\nRegistros totales de POLO BOX (FLUIDO): {len(debug_resultados)}")
                for row in debug_resultados:
                    prendas = row.get('prendas_requeridas', 0)
                    indirecto = row.get('costo_indirecto_fijo', 0)
                    admin = row.get('gasto_administracion', 0)
                    ventas = row.get('gasto_ventas', 0)
                    fecha = row.get('fecha_facturacion')

                    prendas_ok = prendas > 0
                    indirecto_ok = indirecto > 0
                    admin_ok = admin > 0
                    ventas_ok = ventas > 0

                    print(f"\n  OP: {row.get('cod_ordpro')}")
                    print(f"    Prendas: {prendas} {'✓' if prendas_ok else '✗'} | "
                          f"Indirecto: {indirecto} {'✓' if indirecto_ok else '✗'} | "
                          f"Admin: {admin} {'✓' if admin_ok else '✗'} | "
                          f"Ventas: {ventas} {'✓' if ventas_ok else '✗'}")
                    print(f"    Fecha: {fecha}")
            else:
                print("\nNi siquiera existe POLO BOX en la tabla!")
    except Exception as e:
        print(f"✗ Error: {e}")
        import traceback
        traceback.print_exc()

    await db.close()
    print("\n" + "="*80)

if __name__ == "__main__":
    asyncio.run(main())
