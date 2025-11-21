"""
ANÁLISIS DETALLADO DEL CÁLCULO DE HILOS PARA ESTILO 18738
Muestra paso a paso cómo se agregan y calculan los valores
"""

import psycopg2
from psycopg2.extras import RealDictCursor
import os

# Configuración de conexión
DB_HOST = "localhost"
DB_USER = "postgres"
DB_PASSWORD = "siste"
DB_NAME = "cotizador_db"
DB_PORT = 5432
DB_SCHEMA = "public"

def analizar_estilo_18738():
    """Analiza el cálculo de hilos para el estilo 18738"""

    try:
        # Conectar a la BD
        conn = psycopg2.connect(
            host=DB_HOST,
            user=DB_USER,
            password=DB_PASSWORD,
            database=DB_NAME,
            port=DB_PORT
        )
        cursor = conn.cursor(cursor_factory=RealDictCursor)

        print("=" * 130)
        print("ANÁLISIS DE CÁLCULO DE HILOS - ESTILO 18738")
        print("=" * 130)

        # PASO 1: Obtener las OPs del estilo 18738
        print("\n[PASO 1] OBTENER OPs DEL ESTILO 18738")
        print("-" * 130)

        query_ops = f"""
        SELECT DISTINCT cod_ordpro, estilo_propio, estilo_cliente, cliente, tipo_de_producto
        FROM {DB_SCHEMA}.costo_op_detalle
        WHERE (estilo_propio = '18738' OR estilo_cliente = '18738')
        AND version_calculo = 'FLUIDA'
        ORDER BY cod_ordpro
        """

        cursor.execute(query_ops)
        ops = cursor.fetchall()

        print(f"Total de OPs encontradas: {len(ops)}")
        for i, op in enumerate(ops, 1):
            print(f"  OP {i}: {op['cod_ordpro']:15} | Estilo Propio: {str(op['estilo_propio']):10} | Estilo Cliente: {str(op['estilo_cliente']):10} | Cliente: {op['cliente'][:20]:20}")

        if len(ops) == 0:
            print("  ⚠️ No se encontraron OPs para el estilo 18738")
            conn.close()
            return

        cod_ordpros = [op['cod_ordpro'] for op in ops]
        placeholders = ','.join(['%s'] * len(cod_ordpros))

        # PASO 2: Para cada OP, obtener todos los hilos SIN AGREGAR
        print("\n[PASO 2] OBTENER HILOS DETALLADOS POR OP (SIN AGREGAR)")
        print("-" * 130)

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
        FROM {DB_SCHEMA}.costo_hilados_detalle_op chdo
        WHERE chdo.op_codigo IN ({placeholders})
        ORDER BY chdo.op_codigo, chdo.cod_hilado, chdo.tipo_hilo, chdo.fecha_corrida DESC
        LIMIT 100
        """

        cursor.execute(query_hilos_detalle, cod_ordpros)
        hilos_detalle = cursor.fetchall()

        # Agrupar por OP para visualizar
        hilos_por_op = {}
        for row in hilos_detalle:
            op_codigo = row['op_codigo']
            if op_codigo not in hilos_por_op:
                hilos_por_op[op_codigo] = []
            hilos_por_op[op_codigo].append(row)

        # Mostrar los datos crudos agrupados por OP
        for op_codigo in sorted(hilos_por_op.keys()):
            print(f"\n  📦 OP: {op_codigo}")
            print(f"  {'Cod Hilo':12} {'Descripción':32} {'Tipo':12} {'kg/prenda':>12} {'Costo Total':>12} {'kg Req':>10} {'Prendas':>8} {'Fecha'}")
            print(f"  {'-'*130}")

            for row in hilos_por_op[op_codigo]:
                print(f"  {row['cod_hilado']:12} {str(row['descripcion_hilo'])[:30]:32} {row['tipo_hilo']:12} {float(row['kg_por_prenda']):>12.4f} {float(row['costo_total_original']):>12.2f} {float(row['kg_requeridos']):>10.2f} {int(row['prendas_requeridas']):>8} {str(row['fecha_corrida'])[:10]}")

        # PASO 3: Mostrar la agregación NIVEL 1 (SUM por OP)
        print("\n[PASO 3] AGREGACIÓN NIVEL 1 - SUM POR OP (máxima fecha_corrida por OP)")
        print("-" * 130)

        query_nivel1 = f"""
        WITH max_fechas AS (
            SELECT
                op_codigo,
                MAX(fecha_corrida) as fecha_corrida_max
            FROM {DB_SCHEMA}.costo_hilados_detalle_op
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
            FROM {DB_SCHEMA}.costo_hilados_detalle_op chdo
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
        LIMIT 50
        """

        cursor.execute(query_nivel1, cod_ordpros + cod_ordpros)
        nivel1_data = cursor.fetchall()

        print(f"\n  Registros después de Nivel 1 (SUM por OP):")
        print(f"  {'Cod Hilo':12} {'Descripción':32} {'Tipo':12} {'OP':12} {'kg_sum':>12} {'costo_sum':>12} {'kg_req_sum':>12} {'prendas_sum':>10}")
        print(f"  {'-'*130}")

        nivel1_dict = {}
        for row in nivel1_data:
            cod_hilado = row['cod_hilado']
            tipo = row['tipo_hilo']
            op_codigo = row['op_codigo']
            key = (cod_hilado, tipo)
            if key not in nivel1_dict:
                nivel1_dict[key] = {'desc': row['descripcion_hilo'], 'ops': []}
            nivel1_dict[key]['ops'].append({
                'op': op_codigo,
                'kg_sum': float(row['kg_por_prenda_sum']),
                'costo_sum': float(row['costo_total_sum']),
                'kg_req_sum': float(row['kg_requeridos_sum']),
                'prendas_sum': int(row['prendas_requeridas_sum'])
            })

            print(f"  {cod_hilado:12} {str(row['descripcion_hilo'])[:30]:32} {tipo:12} {op_codigo:12} {float(row['kg_por_prenda_sum']):>12.4f} {float(row['costo_total_sum']):>12.2f} {float(row['kg_requeridos_sum']):>12.2f} {int(row['prendas_requeridas_sum']):>10}")

        # PASO 4: Mostrar la agregación NIVEL 2 (AVG entre OPs)
        print("\n[PASO 4] AGREGACIÓN NIVEL 2 - AVG ENTRE OPs")
        print("-" * 130)

        query_nivel2 = f"""
        WITH max_fechas AS (
            SELECT
                op_codigo,
                MAX(fecha_corrida) as fecha_corrida_max
            FROM {DB_SCHEMA}.costo_hilados_detalle_op
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
            FROM {DB_SCHEMA}.costo_hilados_detalle_op chdo
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
        LIMIT 30
        """

        cursor.execute(query_nivel2, cod_ordpros + cod_ordpros)
        nivel2_data = cursor.fetchall()

        print(f"\n  Registros después de Nivel 2 (AVG entre OPs) - TABLA FINAL:")
        print(f"  {'Cod Hilo':12} {'Descripción':32} {'Tipo':12} {'kg_avg':>12} {'costo_avg':>12} {'kg_req_avg':>12} {'Frecuencia':>10}")
        print(f"  {'-'*130}")

        for row in nivel2_data:
            print(f"  {row['cod_hilado']:12} {str(row['descripcion_hilo'])[:30]:32} {row['tipo_hilo']:12} {float(row['kg_por_prenda']):>12.4f} {float(row['costo_total_original']):>12.2f} {float(row['kg_requeridos']):>12.2f} {int(row['frecuencia_ops']):>10}")

        # PASO 5: Ejemplo con cálculos manuales para 1 hilo
        print("\n[PASO 5] EJEMPLO MANUAL - CÁLCULO PARA UN HILO ESPECÍFICO")
        print("-" * 130)

        if nivel1_dict:
            # Tomar el primer hilo como ejemplo
            first_key = list(nivel1_dict.keys())[0]
            cod_hilado, tipo_hilo = first_key
            desc_hilo = nivel1_dict[first_key]['desc']
            ops_data = nivel1_dict[first_key]['ops']

            print(f"\n  HILO: {cod_hilado} - {desc_hilo} (Tipo: {tipo_hilo})")
            print(f"\n  Paso 1: Recolectar datos de Nivel 1 (ya sumados por OP)")
            for i, op_data in enumerate(ops_data, 1):
                print(f"    OP {i} ({op_data['op']}): kg_sum={op_data['kg_sum']:.4f}, costo_sum={op_data['costo_sum']:.2f}, kg_req_sum={op_data['kg_req_sum']:.2f}")

            # Calcular promedios
            kg_values = [op['kg_sum'] for op in ops_data]
            costo_values = [op['costo_sum'] for op in ops_data]
            kg_req_values = [op['kg_req_sum'] for op in ops_data]

            kg_avg = sum(kg_values) / len(kg_values)
            costo_avg = sum(costo_values) / len(costo_values)
            kg_req_avg = sum(kg_req_values) / len(kg_req_values)
            freq = len(ops_data)

            print(f"\n  Paso 2: Calcular promedios (NIVEL 2)")
            print(f"    kg_avg = ({' + '.join([f'{v:.4f}' for v in kg_values])}) / {len(kg_values)} = {kg_avg:.4f}")
            print(f"    costo_avg = ({' + '.join([f'{v:.2f}' for v in costo_values])}) / {len(costo_values)} = {costo_avg:.2f}")
            print(f"    kg_req_avg = ({' + '.join([f'{v:.2f}' for v in kg_req_values])}) / {len(kg_req_values)} = {kg_req_avg:.2f}")
            print(f"    frecuencia_ops = {freq}")

            print(f"\n  Paso 3: Calcular costo_por_kg (en el FRONTEND)")
            if kg_req_avg > 0:
                costo_por_kg = costo_avg / kg_req_avg
                print(f"    costo_por_kg = costo_avg / kg_req_avg = {costo_avg:.2f} / {kg_req_avg:.2f} = {costo_por_kg:.6f}")

                print(f"\n  Paso 4: Calcular costo_por_prenda_final (en el FRONTEND)")
                costo_por_prenda = costo_por_kg * kg_avg
                print(f"    costo_por_prenda = costo_por_kg × kg_avg = {costo_por_kg:.6f} × {kg_avg:.4f} = {costo_por_prenda:.2f}")
            else:
                print(f"    ⚠️ kg_req_avg es 0, no se puede calcular costo_por_kg")

        cursor.close()
        conn.close()

        print("\n" + "=" * 130)
        print("FIN DEL ANÁLISIS")
        print("=" * 130)

    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    analizar_estilo_18738()
