"""
ANÁLISIS DETALLADO DEL CÁLCULO DE HILOS PARA ESTILO 18738
Muestra paso a paso cómo se agregan y calculan los valores
"""

import sys
sys.path.insert(0, 'backend/src')

from smp.config import settings
import asyncio
import psycopg2

async def analizar_estilo_18738():
    """Analiza el cálculo de hilos para el estilo 18738"""

    # Conectar a la BD
    conn = psycopg2.connect(
        host=settings.db_host,
        user=settings.db_user,
        password=settings.db_password,
        database=settings.db_name,
        port=settings.db_port
    )
    cursor = conn.cursor()

    print("=" * 100)
    print("ANÁLISIS DE CÁLCULO DE HILOS - ESTILO 18738")
    print("=" * 100)

    # PASO 1: Obtener las OPs del estilo 18738
    print("\n[PASO 1] OBTENER OPs DEL ESTILO 18738")
    print("-" * 100)

    query_ops = f"""
    SELECT DISTINCT cod_ordpro, estilo_propio, estilo_cliente, cliente, tipo_de_producto
    FROM {settings.db_schema}.costo_op_detalle
    WHERE (estilo_propio = '18738' OR estilo_cliente = '18738')
    AND version_calculo = 'FLUIDA'
    ORDER BY cod_ordpro
    """

    cursor.execute(query_ops)
    ops = cursor.fetchall()

    print(f"Total de OPs encontradas: {len(ops)}")
    for i, op in enumerate(ops, 1):
        cod_ordpro, estilo_propio, estilo_cliente, cliente, tipo_producto = op
        print(f"  OP {i}: {cod_ordpro:15} | Estilo: {estilo_propio or estilo_cliente:10} | Cliente: {cliente:20} | Tipo: {tipo_producto}")

    # PASO 2: Para cada OP, obtener todos los hilos SIN AGREGAR
    print("\n[PASO 2] OBTENER HILOS DETALLADOS POR OP (SIN AGREGAR)")
    print("-" * 100)

    cod_ordpros = [op[0] for op in ops]
    placeholders = ','.join(['%s'] * len(cod_ordpros))

    query_hilos_detalle = f"""
    SELECT
        chdo.op_codigo,
        chdo.cod_hilado,
        chdo.descripcion_hilo,
        chdo.tipo_hilo,
        chdo.kg_por_prenda,
        chdo.costo_total_original,
        chdo.kg_requeridos,
        chdo.prendas_requeridas,
        chdo.fecha_corrida
    FROM {settings.db_schema}.costo_hilados_detalle_op chdo
    WHERE chdo.op_codigo IN ({placeholders})
    ORDER BY chdo.op_codigo, chdo.cod_hilado, chdo.tipo_hilo, chdo.fecha_corrida DESC
    """

    cursor.execute(query_hilos_detalle, cod_ordpros)
    hilos_detalle = cursor.fetchall()

    # Agrupar por OP para visualizar
    hilos_por_op = {}
    for row in hilos_detalle:
        op_codigo = row[0]
        if op_codigo not in hilos_por_op:
            hilos_por_op[op_codigo] = []
        hilos_por_op[op_codigo].append(row)

    # Mostrar los datos crudos agrupados por OP
    for op_codigo in sorted(hilos_por_op.keys()):
        print(f"\n  📦 OP: {op_codigo}")
        print(f"  {'Cod Hilo':10} {'Descripción':30} {'Tipo':10} {'kg/prenda':>12} {'Costo Total':>12} {'kg Req':>10} {'Prendas':>8} {'Fecha'}")
        print(f"  {'-'*110}")

        for row in hilos_por_op[op_codigo]:
            _, cod_hilado, desc, tipo, kg_prenda, costo_total, kg_req, prendas, fecha = row
            print(f"  {cod_hilado:10} {desc[:28]:30} {tipo:10} {float(kg_prenda):>12.4f} {float(costo_total):>12.2f} {float(kg_req):>10.2f} {int(prendas):>8} {str(fecha)[:10]}")

    # PASO 3: Mostrar la agregación NIVEL 1 (SUM por OP)
    print("\n[PASO 3] AGREGACIÓN NIVEL 1 - SUM POR OP (máxima fecha_corrida por OP)")
    print("-" * 100)

    query_nivel1 = f"""
    WITH max_fechas AS (
        SELECT
            op_codigo,
            MAX(fecha_corrida) as fecha_corrida_max
        FROM {settings.db_schema}.costo_hilados_detalle_op
        WHERE op_codigo IN ({placeholders})
        GROUP BY op_codigo
    ),
    hilos_por_op AS (
        SELECT
            chdo.cod_hilado,
            chdo.descripcion_hilo,
            chdo.tipo_hilo,
            chdo.op_codigo,
            SUM(chdo.kg_por_prenda) as kg_por_prenda_sum,
            SUM(chdo.costo_total_original) as costo_total_sum,
            SUM(chdo.kg_requeridos) as kg_requeridos_sum,
            SUM(chdo.prendas_requeridas) as prendas_requeridas_sum
        FROM {settings.db_schema}.costo_hilados_detalle_op chdo
        INNER JOIN max_fechas mf
            ON chdo.op_codigo = mf.op_codigo
            AND chdo.fecha_corrida = mf.fecha_corrida_max
        WHERE chdo.op_codigo IN ({placeholders})
        GROUP BY
            chdo.cod_hilado,
            chdo.descripcion_hilo,
            chdo.tipo_hilo,
            chdo.op_codigo
    )
    SELECT * FROM hilos_por_op
    ORDER BY cod_hilado, tipo_hilo, op_codigo
    """

    cursor.execute(query_nivel1, cod_ordpros + cod_ordpros)
    nivel1_data = cursor.fetchall()

    print(f"\n  Registros después de Nivel 1 (SUM por OP):")
    print(f"  {'Cod Hilo':10} {'Descripción':30} {'Tipo':10} {'OP':10} {'kg_sum':>12} {'costo_sum':>12} {'kg_req_sum':>12} {'prendas_sum':>10}")
    print(f"  {'-'*110}")

    nivel1_dict = {}
    for row in nivel1_data:
        cod_hilado, desc, tipo, op_codigo, kg_sum, costo_sum, kg_req_sum, prendas_sum = row
        key = (cod_hilado, tipo)
        if key not in nivel1_dict:
            nivel1_dict[key] = {'desc': desc, 'ops': []}
        nivel1_dict[key]['ops'].append({
            'op': op_codigo,
            'kg_sum': float(kg_sum),
            'costo_sum': float(costo_sum),
            'kg_req_sum': float(kg_req_sum),
            'prendas_sum': int(prendas_sum)
        })

        print(f"  {cod_hilado:10} {desc[:28]:30} {tipo:10} {op_codigo:10} {float(kg_sum):>12.4f} {float(costo_sum):>12.2f} {float(kg_req_sum):>12.2f} {int(prendas_sum):>10}")

    # PASO 4: Mostrar la agregación NIVEL 2 (AVG entre OPs)
    print("\n[PASO 4] AGREGACIÓN NIVEL 2 - AVG ENTRE OPs")
    print("-" * 100)

    query_nivel2 = f"""
    WITH max_fechas AS (
        SELECT
            op_codigo,
            MAX(fecha_corrida) as fecha_corrida_max
        FROM {settings.db_schema}.costo_hilados_detalle_op
        WHERE op_codigo IN ({placeholders})
        GROUP BY op_codigo
    ),
    hilos_por_op AS (
        SELECT
            chdo.cod_hilado,
            chdo.descripcion_hilo,
            chdo.tipo_hilo,
            chdo.op_codigo,
            SUM(chdo.kg_por_prenda) as kg_por_prenda_sum,
            SUM(chdo.costo_total_original) as costo_total_sum,
            SUM(chdo.kg_requeridos) as kg_requeridos_sum,
            SUM(chdo.prendas_requeridas) as prendas_requeridas_sum
        FROM {settings.db_schema}.costo_hilados_detalle_op chdo
        INNER JOIN max_fechas mf
            ON chdo.op_codigo = mf.op_codigo
            AND chdo.fecha_corrida = mf.fecha_corrida_max
        WHERE chdo.op_codigo IN ({placeholders})
        GROUP BY
            chdo.cod_hilado,
            chdo.descripcion_hilo,
            chdo.tipo_hilo,
            chdo.op_codigo
    )
    SELECT
        cod_hilado,
        descripcion_hilo,
        tipo_hilo,
        AVG(kg_por_prenda_sum) as kg_por_prenda,
        AVG(costo_total_sum) as costo_total_original,
        AVG(kg_requeridos_sum) as kg_requeridos,
        AVG(prendas_requeridas_sum) as prendas_requeridas,
        COUNT(DISTINCT op_codigo) as frecuencia_ops
    FROM hilos_por_op
    GROUP BY
        cod_hilado,
        descripcion_hilo,
        tipo_hilo
    ORDER BY descripcion_hilo
    """

    cursor.execute(query_nivel2, cod_ordpros + cod_ordpros)
    nivel2_data = cursor.fetchall()

    print(f"\n  Registros después de Nivel 2 (AVG entre OPs) - TABLA FINAL:")
    print(f"  {'Cod Hilo':10} {'Descripción':30} {'Tipo':10} {'kg_avg':>12} {'costo_avg':>12} {'kg_req_avg':>12} {'Frecuencia':>10}")
    print(f"  {'-'*110}")

    for row in nivel2_data:
        cod_hilado, desc, tipo, kg_avg, costo_avg, kg_req_avg, prendas_avg, freq = row
        print(f"  {cod_hilado:10} {desc[:28]:30} {tipo:10} {float(kg_avg):>12.4f} {float(costo_avg):>12.2f} {float(kg_req_avg):>12.2f} {int(freq):>10}")

    # PASO 5: Ejemplo con cálculos manuales para 1 hilo
    print("\n[PASO 5] EJEMPLO MANUAL - CÁLCULO PARA UN HILO ESPECÍFICO")
    print("-" * 100)

    if nivel1_dict:
        # Tomar el primer hilo como ejemplo
        first_key = list(nivel1_dict.keys())[0]
        cod_hilado, tipo_hilo = first_key
        desc_hilo = nivel1_dict[first_key]['desc']
        ops_data = nivel1_dict[first_key]['ops']

        print(f"\n  HILO: {cod_hilado} - {desc_hilo} (Tipo: {tipo_hilo})")
        print(f"\n  Paso 1: Recolectar datos de Nivel 1 (ya sumados por OP)")
        for i, op_data in enumerate(ops_data, 1):
            print(f"    OP {i} ({op_data['op']}): kg_sum={op_data['kg_sum']:.4f}, costo_sum={op_data['costo_sum']:.2f}")

        # Calcular promedios
        kg_values = [op['kg_sum'] for op in ops_data]
        costo_values = [op['costo_sum'] for op in ops_data]
        kg_req_values = [op['kg_req_sum'] for op in ops_data]

        kg_avg = sum(kg_values) / len(kg_values)
        costo_avg = sum(costo_values) / len(costo_values)
        kg_req_avg = sum(kg_req_values) / len(kg_req_values)
        freq = len(ops_data)

        print(f"\n  Paso 2: Calcular promedios")
        print(f"    kg_avg = ({' + '.join([f'{v:.4f}' for v in kg_values])}) / {len(kg_values)} = {kg_avg:.4f}")
        print(f"    costo_avg = ({' + '.join([f'{v:.2f}' for v in costo_values])}) / {len(costo_values)} = {costo_avg:.2f}")
        print(f"    kg_req_avg = ({' + '.join([f'{v:.2f}' for v in kg_req_values])}) / {len(kg_req_values)} = {kg_req_avg:.2f}")
        print(f"    frecuencia_ops = {freq}")

        print(f"\n  Paso 3: Calcular costo_por_kg (en backend frontend)")
        if kg_req_avg > 0:
            costo_por_kg = costo_avg / kg_req_avg
            print(f"    costo_por_kg = costo_avg / kg_req_avg = {costo_avg:.2f} / {kg_req_avg:.2f} = {costo_por_kg:.6f}")
        else:
            print(f"    ⚠️ kg_req_avg es 0, no se puede calcular costo_por_kg")

    cursor.close()
    conn.close()

    print("\n" + "=" * 100)
    print("FIN DEL ANÁLISIS")
    print("=" * 100)

if __name__ == "__main__":
    asyncio.run(analizar_estilo_18738())
