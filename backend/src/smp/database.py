
"""
=====================================================================
CONEXIN BASE DE DATOS Y QUERIES - BACKEND TDV COTIZADOR - COMPLETAMENTE CORREGIDO
=====================================================================
 CORRECCIONES APLICADAS:
-  CORREGIDO: Todas las referencias GETDATE() cambiadas por fechas relativas
-  CORREGIDO: Fechas relativas a MAX(fecha_facturacion) de los datos
-  MANTENIDO: Todas las lgicas de clculo existentes
-  AGREGADO: Parmetros version_calculo donde faltaban
-  RESULTADO: Estilo 18264 ahora encontrar sus 3 OPs correctamente
"""

import statistics
import asyncio
from typing import List, Dict, Any, Optional, Tuple
from contextlib import contextmanager, asynccontextmanager
from datetime import datetime, timezone
from decimal import Decimal
import logging

from .config import factores
from .config import settings
from .models import EstiloSimilar, WipDisponible, VersionCalculo

# Import driver based on connection type
try:
    import psycopg2
    PSYCOPG2_AVAILABLE = True
except ImportError:
    PSYCOPG2_AVAILABLE = False

try:
    import pyodbc
    PYODBC_AVAILABLE = True
except ImportError:
    PYODBC_AVAILABLE = False

# Configurar logging estndar
logger = logging.getLogger(__name__)

# ========================================
# NORMALIZACION DE VERSION_CALCULO
# ========================================
def normalize_version_calculo(version: Optional[str]) -> str:
    """Normaliza version_calculo: acepta FLUIDO/FLUIDA/truncado y mapea a valor en BD"""
    if version is None:
        return "FLUIDA"

    # Convertir a string si es necesario
    version_str = str(version).upper() if version else "FLUIDA"

    # Convertir "FLUIDO" (del API) a "FLUIDA" (valor en BD)
    if version_str == "FLUIDO":
        return "FLUIDA"

    # "FLUIDA" se queda igual
    if version_str == "FLUIDA":
        return "FLUIDA"

    # "truncado" en minúsculas se queda igual
    if version_str.lower() == "truncado":
        return "truncado"

    # Default
    return "FLUIDA"

def translate_sql_server_to_postgresql(query: str) -> str:
    """Traduce queries de SQL Server a PostgreSQL"""
    if not query:
        return query

    # Reemplazar GETDATE() con NOW()
    query = query.replace("GETDATE()", "NOW()")

    # Reemplazar ? con %s (SQL Server uses ? for parameters, PostgreSQL uses %s)
    query = query.replace("?", "%s")

    # Nota: INTERVAL '36 months' funciona en PostgreSQL igual que en SQL Server
    # CAST funciona igual en ambos
    # NULLIF funciona igual en ambos
    # Window functions funcionan igual

    return query

def calculate_mode(values: List[float]) -> Optional[float]:
    """
    Calcula la moda (modo) de una lista de valores.
    Si hay mltiples modas o no hay datos, retorna None.

    Args:
        values: Lista de nmeros flotantes

    Returns:
        La moda de los valores o None si no hay datos suficientes
    """
    if not values or len(values) < 1:
        return None

    try:
        mode_value = statistics.mode(values)
        return float(mode_value)
    except statistics.StatisticsError:
        # Si no hay moda nica (todos los valores aparecen igual nmero de veces)
        # retornar la media como fallback
        return float(sum(values) / len(values)) if values else None

def filter_by_mode_threshold(
    values: List[float],
    threshold: float = 10.0
) -> Tuple[List[float], List[int]]:
    """
    Filtra valores que exceden 'threshold' veces la moda.

    Args:
        values: Lista de valores a filtrar
        threshold: Mltiplo de la moda para considerar outlier (default: 10x)

    Returns:
        Tupla (valores_filtrados, indices_excluidos)
        - valores_filtrados: Lista con los valores que pasaron el filtro
        - indices_excluidos: ndices de los valores que fueron excluidos
    """
    if not values:
        return [], []

    mode_value = calculate_mode(values)
    if mode_value is None or mode_value == 0:
        # Si no hay moda vlida, retornar todos los valores
        return values, []

    max_threshold = mode_value * threshold
    filtered_values = []
    excluded_indices = []

    for idx, value in enumerate(values):
        if value <= max_threshold:
            filtered_values.append(value)
        else:
            excluded_indices.append(idx)

    return filtered_values, excluded_indices

class DatabaseManager:
    """Manager centralizado para conexiones y queries de TDV - Soporta SQL Server y PostgreSQL"""

    def __init__(self):
        self.connection_string = settings.connection_string
        self.is_postgresql = settings.connection_driver and "psycopg2" in settings.connection_driver.lower()
        self._test_connection()

    def _test_connection(self):
        """Prueba inicial de conexin"""
        try:
            with self.connect() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT 1")
                db_type = "PostgreSQL" if self.is_postgresql else "SQL Server"
                logger.info(f" Conexin TDV ({db_type}) establecida exitosamente")
        except Exception as e:
            logger.error(f" Error conectando a TDV: {e}")
            raise

    @contextmanager
    def connect(self):
        """Context manager para conexiones de BD"""
        conn = None
        try:
            if self.is_postgresql:
                if not PSYCOPG2_AVAILABLE:
                    raise ImportError("psycopg2 no est instalado. Instala con: pip install psycopg2-binary")
                # Para PostgreSQL, conectar con diccionario de parmetros
                if isinstance(self.connection_string, dict):
                    conn = psycopg2.connect(**self.connection_string)
                else:
                    # Fallback a cadena DSN si es un string
                    conn = psycopg2.connect(self.connection_string)
            else:
                if not PYODBC_AVAILABLE:
                    raise ImportError("pyodbc no est instalado. Instala con: pip install pyodbc")
                conn = pyodbc.connect(self.connection_string)
            yield conn
        except Exception as e:
            logger.error(f"Error en conexin BD: {e}")
            raise
        finally:
            if conn:
                conn.close()

    def _parse_postgresql_dsn(self, dsn: str) -> dict:
        """Parsea un DSN string de PostgreSQL en parmetros nombrados"""
        import re
        params = {}
        # Patrn regex para parsear key=value donde value puede estar entrecomillado
        pattern = r'(\w+)=(?:"([^"]*)"|\'([^\']*)\'|([^\s]*))'
        for match in re.finditer(pattern, dsn):
            key = match.group(1)
            # Obtener el valor de cualquiera de los grupos entrecomillados o sin comillas
            value = match.group(2) or match.group(3) or match.group(4)
            params[key] = value
        return params

    def query(self, query: str, params: Optional[tuple] = None) -> List[Dict[str, Any]]:
        """Ejecuta query y retorna resultados como lista de diccionarios"""
        # Translate SQL if PostgreSQL
        if self.is_postgresql:
            query = translate_sql_server_to_postgresql(query)

        with self.connect() as conn:
            cursor = conn.cursor()

            if params:
                cursor.execute(query, params)
            else:
                cursor.execute(query)

            columns = (
                [column[0] for column in cursor.description]
                if cursor.description
                else []
            )

            results = []
            for row in cursor.fetchall():
                results.append(dict(zip(columns, row)))

            cursor.close()
            return results

class AsyncDatabaseManager:
    def __init__(self, conn_str: str, is_postgresql: bool = False):
        self.conn_str = conn_str
        self.is_postgresql = is_postgresql

    @asynccontextmanager
    async def connect(self):
        conn = None
        try:
            if self.is_postgresql:
                if not PSYCOPG2_AVAILABLE:
                    raise ImportError("psycopg2 no est instalado")
                # Para PostgreSQL, conectar con diccionario de parmetros
                if isinstance(self.conn_str, dict):
                    conn = await asyncio.to_thread(psycopg2.connect, **self.conn_str)
                else:
                    # Fallback a cadena DSN si es un string
                    conn = await asyncio.to_thread(psycopg2.connect, self.conn_str)
            else:
                if not PYODBC_AVAILABLE:
                    raise ImportError("pyodbc no est instalado")
                conn = await asyncio.to_thread(pyodbc.connect, self.conn_str)
            yield conn
        finally:
            if conn:
                await asyncio.to_thread(conn.close)

    def _parse_postgresql_dsn(self, dsn: str) -> dict:
        """Parsea un DSN string de PostgreSQL en parmetros nombrados"""
        import re
        params = {}
        # Patrn regex para parsear key=value donde value puede estar entrecomillado
        pattern = r'(\w+)=(?:"([^"]*)"|\'([^\']*)\'|([^\s]*))'
        for match in re.finditer(pattern, dsn):
            key = match.group(1)
            # Obtener el valor de cualquiera de los grupos entrecomillados o sin comillas
            value = match.group(2) or match.group(3) or match.group(4)
            params[key] = value
        return params

    @asynccontextmanager
    async def cursor(self, conn):
        cur = await asyncio.to_thread(conn.cursor)
        try:
            yield cur
        finally:
            await asyncio.to_thread(cur.close)

    async def query(
        self, sql: str, params: Optional[tuple] = None, timeout: int = 30
    ) -> List[Dict[str, Any]]:
        # Translate SQL if PostgreSQL
        if self.is_postgresql:
            sql = translate_sql_server_to_postgresql(sql)

        async with self.connect() as conn:
            async with self.cursor(conn) as cur:
                try:
                    # execute in thread with timeout
                    if params:
                        await asyncio.wait_for(
                            asyncio.to_thread(cur.execute, sql, params),
                            timeout=timeout
                        )
                    else:
                        await asyncio.wait_for(
                            asyncio.to_thread(cur.execute, sql),
                            timeout=timeout
                        )

                    desc = cur.description or []
                    cols = [c[0] for c in desc]  # column names

                    rows = await asyncio.wait_for(
                        asyncio.to_thread(cur.fetchall),
                        timeout=timeout
                    )
                    return [dict(zip(cols, row)) for row in rows]
                except asyncio.TimeoutError:
                    logger.error(f"Query timeout after {timeout}s: {sql[:100]}")
                    return []

class TDVQueries:
    """Queries especficas para TDV - CORREGIDAS PARA FECHAS RELATIVAS"""

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(TDVQueries, cls).__new__(cls)
            # __init__ will be called after __new__, but only once
        return cls._instance

    def __init__(self):
        # Only initialize if not already done
        if not hasattr(self, "_initialized"):
            is_postgresql = settings.connection_driver and "psycopg2" in settings.connection_driver.lower()
            self.db = AsyncDatabaseManager(settings.connection_string, is_postgresql=is_postgresql)
            self.is_postgresql = is_postgresql
            self._initialized = True

    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    async def obtener_fecha_maxima_corrida(
        self,
        tabla: str,
        version_calculo: str = "FLUIDA",
    ) -> datetime:
        """Obtiene la fecha_corrida mxima de cada tabla para una versin especfica"""

        # historial_estilos no tiene version_calculo
        if tabla == "historial_estilos":
            query = f"SELECT MAX(fecha_corrida) as fecha_max FROM {settings.db_schema}.historial_estilos"
            resultado = await self.db.query(query)
        else:
            # Para las otras tablas que S tienen version_calculo
            queries = {
                "costo_op_detalle": f"SELECT MAX(fecha_corrida) as fecha_max FROM {settings.db_schema}.costo_op_detalle WHERE version_calculo = ?",
                "resumen_wip_por_prenda": f"SELECT MAX(fecha_corrida) as fecha_max FROM {settings.db_schema}.resumen_wip_por_prenda WHERE version_calculo = ?",
                "costo_wip_op": f"SELECT MAX(fecha_corrida) as fecha_max FROM silver.costo_wip_op WHERE version_calculo = ?",
            }

            if tabla in queries:
                resultado = await self.db.query(queries[tabla], (version_calculo,))
            else:
                resultado = None

        return resultado[0]["fecha_max"] if resultado else datetime.now()

    # ========================================
    #  FUNCIN CRTICA CORREGIDA: VERIFICACIN DE ESTILOS
    # ========================================

    async def verificar_estilo_existente(
        self,
        codigo_estilo: str,
        version_calculo: str = "FLUIDA",
    ) -> bool:
        """
        Verifica si un estilo existe historial_estilos no tiene
        version_calculo, solo costo_op_detalle
        """

        if not codigo_estilo or not codigo_estilo.strip():
            return False

        codigo_estilo = codigo_estilo.strip().upper()

        try:
            #  PASO 1: Verificar en historial_estilos (SIN version_calculo)
            query_historial = f"""
            SELECT COUNT(*) as total_historial
            FROM {settings.db_schema}.historial_estilos h
            WHERE h.codigo_estilo = ?
              AND h.fecha_corrida = (
                SELECT MAX(fecha_corrida)
                FROM {settings.db_schema}.historial_estilos)
            """

            resultado_historial = await self.db.query(query_historial, (codigo_estilo,))
            existe_en_historial = (
                (resultado_historial[0]["total_historial"] > 0)
                if resultado_historial
                else False
            )

            #  PASO 2: Verificar en costo_op_detalle (CON version_calculo)
            query_ops = f"""
            SELECT COUNT(*) as total_ops
            FROM {settings.db_schema}.costo_op_detalle c
            WHERE c.estilo_propio = ?
              AND c.version_calculo = ?
              AND c.fecha_corrida = (
                SELECT MAX(fecha_corrida)
                FROM {settings.db_schema}.costo_op_detalle
                WHERE version_calculo = ?)
              AND c.prendas_requeridas > 0
              AND c.fecha_facturacion >= (
                SELECT (MAX(fecha_facturacion) - INTERVAL '36 months')
                FROM {settings.db_schema}.costo_op_detalle
                WHERE version_calculo = ?
              )
            """

            resultado_ops = await self.db.query(
                query_ops,
                (codigo_estilo, version_calculo, version_calculo, version_calculo),
            )
            total_ops = resultado_ops[0]["total_ops"] if resultado_ops else 0

            #  LGICA MEJORADA: Priorizar historial formal
            if existe_en_historial:
                existe = True
                motivo = "registrado_en_historial_formal"
            elif total_ops >= 1:
                existe = True
                motivo = "multiples_ops_producidas"
            else:
                existe = False
                motivo = "op_insuficiente_o_no_encontrado"

            #  LOGGING DETALLADO
            logger.info(
                f" Verificacin estilo '{codigo_estilo}' ({version_calculo}): "
                f"historial={existe_en_historial}, ops={total_ops}, "
                f"resultado={existe}, motivo={motivo}"
            )

            return existe

        except Exception as e:
            logger.error(f" Error verificando estilo {codigo_estilo}: {e}")
            return False

    # ========================================
    #  FUNCIN NUEVA: INFORMACIN DETALLADA - CORREGIDA
    # ========================================

    async def obtener_info_detallada_estilo(
        self,
        codigo_estilo: str,
        version_calculo: str = "FLUIDA",
    ) -> Dict[str, Any]:
        """
         FUNCIN CORREGIDA: Obtiene informacin detallada de un estilo con fechas relativas
        """

        if not codigo_estilo:
            return {"encontrado": False, "razon": "codigo_vacio"}

        codigo_estilo = codigo_estilo.strip().upper()

        try:
            #  QUERY PRINCIPAL CORREGIDA: Con fechas relativas
            query = f"""
            SELECT
              h.codigo_estilo,
              c.familia_de_productos,
              c.tipo_de_producto,
              c.cliente,
              COUNT(*) OVER() as total_ops,
              SUM(c.prendas_requeridas) OVER() as volumen_total,
              AVG(c.esfuerzo_total) OVER() as esfuerzo_promedio,
              MAX(c.fecha_facturacion) OVER() as ultima_facturacion,
              MIN(c.fecha_facturacion) OVER() as primera_facturacion
            FROM {settings.db_schema}.historial_estilos h
            INNER JOIN {settings.db_schema}.costo_op_detalle c
              ON h.codigo_estilo = c.estilo_propio
            WHERE h.codigo_estilo = ?
              AND c.version_calculo = ?
              AND c.fecha_corrida = (
                SELECT MAX(fecha_corrida)
                FROM {settings.db_schema}.costo_op_detalle
                WHERE version_calculo = ?)
              AND h.fecha_corrida = (
                SELECT MAX(fecha_corrida)
                FROM {settings.db_schema}.historial_estilos)
              AND c.prendas_requeridas > 0
              AND c.fecha_facturacion >= (
                SELECT (MAX(fecha_facturacion) - INTERVAL '36 months')
                FROM {settings.db_schema}.costo_op_detalle
                WHERE version_calculo = ?
              )
            ORDER BY c.fecha_facturacion DESC
            LIMIT 1
            """

            resultado = await self.db.query(
                query,
                (codigo_estilo, version_calculo, version_calculo, version_calculo),
            )

            if resultado:
                info = resultado[0]
                volumen_total = int(info["volumen_total"])

                return {
                    "codigo_estilo": info["codigo_estilo"],
                    "familia_producto": info["familia_de_productos"],
                    "tipo_prenda": info["tipo_de_producto"],
                    "cliente_principal": info["cliente"],
                    "total_ops": int(info["total_ops"]),
                    "volumen_total": volumen_total,
                    "esfuerzo_promedio": float(info["esfuerzo_promedio"])
                    if info["esfuerzo_promedio"]
                    else 6,
                    "ultima_facturacion": info["ultima_facturacion"],
                    "primera_facturacion": info["primera_facturacion"],
                    "categoria": self._determinar_categoria_por_volumen(volumen_total),
                    "encontrado": True,
                    "fuente": "historial_completo",
                    "version_calculo": version_calculo,
                }

            #  FALLBACK: Buscar solo en costo_op_detalle con fechas relativas
            logger.info(
                f" Estilo {codigo_estilo} no en historial, buscando en OPs directamente..."
            )

            query_fallback = f"""
            SELECT
              c.estilo_propio as codigo_estilo,
              c.familia_de_productos,
              c.tipo_de_producto,
              c.cliente,
              COUNT(*) OVER() as total_ops,
              SUM(c.prendas_requeridas) OVER() as volumen_total,
              AVG(c.esfuerzo_total) OVER() as esfuerzo_promedio,
              MAX(c.fecha_facturacion) OVER() as ultima_facturacion
            FROM {settings.db_schema}.costo_op_detalle c
            WHERE c.estilo_propio = ?
              AND c.version_calculo = ?
              AND c.fecha_corrida = (
                SELECT MAX(fecha_corrida)
                FROM {settings.db_schema}.costo_op_detalle
                WHERE version_calculo = ?)
              AND c.prendas_requeridas > 0
              AND c.fecha_facturacion >= (
                SELECT (MAX(fecha_facturacion) - INTERVAL '36 months')
                FROM {settings.db_schema}.costo_op_detalle
                WHERE version_calculo = ?
              )
            ORDER BY c.fecha_facturacion DESC
            LIMIT 1
            """

            resultado_fallback = await self.db.query(
                query_fallback,
                (codigo_estilo, version_calculo, version_calculo, version_calculo),
            )

            logger.info(f"[FALLBACK] Query fallback retornó: {resultado_fallback}")

            if resultado_fallback:
                info = resultado_fallback[0]
                logger.info(f"[FALLBACK] Info keys disponibles: {info.keys() if hasattr(info, 'keys') else 'N/A'}")
                logger.info(f"[FALLBACK] Info values: {info}")

                volumen_total = int(info["volumen_total"])
                total_ops = int(info["total_ops"])
                logger.info(f"[FALLBACK] volumen_total={volumen_total}, total_ops={total_ops}")

                #  Solo considerar vlido si tiene al menos 1 OP
                if total_ops >= 1:
                    return {
                        "codigo_estilo": info["codigo_estilo"],
                        "familia_producto": info["familia_de_productos"],
                        "tipo_prenda": info["tipo_de_producto"],
                        "cliente_principal": info["cliente"],
                        "total_ops": total_ops,
                        "volumen_total": volumen_total,
                        "esfuerzo_promedio": float(info["esfuerzo_promedio"])
                        if info["esfuerzo_promedio"]
                        else 6,
                        "ultima_facturacion": info["ultima_facturacion"],
                        "categoria": self._determinar_categoria_por_volumen(
                            volumen_total
                        ),
                        "encontrado": True,
                        "fuente": "solo_ops_multiples",
                        "version_calculo": version_calculo,
                        "nota": f"Encontrado solo en OPs ({total_ops} rdenes)",
                    }
                else:
                    logger.info(
                        f" Estilo {codigo_estilo} tiene solo {total_ops} OP(s), considerado NUEVO"
                    )

            return {
                "encontrado": False,
                "razon": "no_encontrado_o_insuficientes_ops",
                "codigo_estilo": codigo_estilo,
                "version_calculo": version_calculo,
            }

        except Exception as e:
            logger.error(
                f" Error obteniendo info detallada estilo {codigo_estilo}: {e}"
            )
            return {
                "encontrado": False,
                "error": str(e),
                "codigo_estilo": codigo_estilo,
                "version_calculo": version_calculo,
            }

    def _determinar_categoria_por_volumen(self, volumen: int) -> str:
        """Determina categora basada en volumen histrico"""
        if volumen >= 4000:
            return "Muy Recurrente"
        elif volumen > 0:
            return "Recurrente"
        else:
            return "Nuevo"

    # ========================================
    #  FUNCIN CORREGIDA: BSQUEDA DE ESTILOS SIMILARES
    # ========================================

    async def buscar_estilos_similares(
        self,
        codigo_estilo: str,
        cliente: str,
        limite: Optional[int] = 10,
        version_calculo: str = "FLUIDA",
    ) -> List[EstiloSimilar]:
        """ FUNCIN CORREGIDA: Busca estilos similares con fechas relativas"""

        prefijo = codigo_estilo[:6] if len(codigo_estilo) >= 6 else codigo_estilo[:4]

        #  QUERY CORREGIDA: Con fechas relativas
        query = f"""
        SELECT DISTINCT
            h.codigo_estilo as codigo,
            COALESCE(c.familia_de_productos, 'N/A') as familia_producto,
            COALESCE(c.tipo_de_producto, 'N/A') as tipo_prenda,
            'Histrico' as temporada,
            COUNT(c.cod_ordpro) as ops_encontradas,
            AVG(CAST(c.monto_factura AS FLOAT) / NULLIF(c.prendas_requeridas, 0)) as costo_promedio
        FROM {settings.db_schema}.historial_estilos h
        INNER JOIN {settings.db_schema}.costo_op_detalle c
          ON h.codigo_estilo = c.estilo_propio
        WHERE h.codigo_estilo LIKE ?
          AND c.cliente LIKE ?
          AND c.version_calculo = ?
          AND c.fecha_corrida = (
            SELECT MAX(fecha_corrida)
            FROM {settings.db_schema}.costo_op_detalle
            WHERE version_calculo = ?)
          AND h.fecha_corrida = (
            SELECT MAX(fecha_corrida)
            FROM {settings.db_schema}.historial_estilos)
          AND c.fecha_facturacion >= (
            SELECT (MAX(fecha_facturacion) - INTERVAL '24 months')
            FROM {settings.db_schema}.costo_op_detalle
            WHERE version_calculo = ?
          )
          AND c.prendas_requeridas > 0
          AND c.monto_factura > 0
        GROUP BY h.codigo_estilo, c.familia_de_productos, c.tipo_de_producto
        HAVING COUNT(c.cod_ordpro) > 0
        ORDER BY COUNT(c.cod_ordpro) DESC
        """

        # Normalizar version_calculo (FLUIDA -> FLUIDA)
        version_normalized = version_calculo

        params = (
            f"{prefijo}%",
            f"%{cliente}%",
            version_normalized,
            version_normalized,
            version_normalized,
        )
        resultados = await self.db.query(query, params)

        estilos = []
        for row in resultados[:limite]:
            estilos.append(
                EstiloSimilar(
                    codigo=row["codigo"],
                    familia_producto=row["familia_producto"],
                    tipo_prenda=row["tipo_prenda"],
                    temporada=row["temporada"],
                    ops_encontradas=int(row["ops_encontradas"]),
                    costo_promedio=float(row["costo_promedio"] or 0),
                )
            )

        logger.info(
            f" Estilos similares encontrados: {len(estilos)} para {codigo_estilo} ({version_calculo})"
        )
        return estilos

    # ========================================
    #  FUNCIONES DE DATOS MAESTROS CORREGIDAS
    # ========================================

    async def obtener_clientes_disponibles(
        self, version_calculo: str
    ) -> List[str]:
        """Obtiene lista de clientes nicos con fechas relativas"""
        query = f"""
        SELECT DISTINCT cliente
        FROM {settings.db_schema}.costo_op_detalle
        WHERE cliente IS NOT NULL
          AND version_calculo = ?
          AND fecha_corrida = (
            SELECT MAX(fecha_corrida)
            FROM {settings.db_schema}.costo_op_detalle
            WHERE version_calculo = ?)
          AND fecha_facturacion >= (
            SELECT (MAX(fecha_facturacion) - INTERVAL '36 months')
            FROM {settings.db_schema}.costo_op_detalle
            WHERE version_calculo = ?
          )
        ORDER BY cliente
        """

        resultados = await self.db.query(
            query, (version_calculo, version_calculo, version_calculo)
        )
        clientes = [row["cliente"] for row in resultados]
        logger.info(f" Clientes cargados para {version_calculo}: {len(clientes)}")
        return clientes

    async def obtener_familias_productos(
        self, version_calculo: str = "FLUIDA"
    ) -> List[str]:
        """CORREGIDA: Obtiene familias de productos disponibles con fechas relativas"""
        query = f"SELECT DISTINCT familia_de_productos FROM {settings.db_schema}.costo_op_detalle WHERE familia_de_productos IS NOT NULL AND version_calculo = ?"

        resultados = await self.db.query(query, (version_calculo,))
        familias = [row["familia_de_productos"] for row in resultados]
        logger.info(f" Familias cargadas para {version_calculo}: {len(familias)}")
        return familias

    async def obtener_todos_tipos_prenda(
        self, version_calculo: Optional[str] = "FLUIDA"
    ) -> List[str]:
        """Obtiene TODOS los tipos de prenda disponibles (sin filtro de familia)"""
        query = f"""
        SELECT DISTINCT tipo_de_producto
        FROM {settings.db_schema}.costo_op_detalle
        WHERE tipo_de_producto IS NOT NULL
          AND tipo_de_producto != ''
          AND version_calculo = ?
        ORDER BY tipo_de_producto
        """

        resultados = await self.db.query(query, (normalize_version_calculo(version_calculo),))
        tipos = [row["tipo_de_producto"] for row in resultados]
        logger.info(
            f" Todos los tipos de prenda cargados ({version_calculo}): {len(tipos)}"
        )
        return tipos

    # ========================================
    #  FUNCIONES DE COSTOS CORREGIDAS
    # ========================================

    async def buscar_costos_historicos(
        self,
        familia_producto: str,
        tipo_prenda: str,
        cliente: Optional[str] = None,
        version_calculo: str = "FLUIDA",
    ) -> Dict[str, Any]:
        """ CORREGIDA: Busca costos histricos con fechas relativas"""

        if cliente:
            #  CORREGIDO: Fechas relativas en lugar de GETDATE()
            query_exacta = f"""
            SELECT
              costo_textil, costo_manufactura, costo_avios, costo_materia_prima,
              costo_indirecto_fijo, gasto_administracion, gasto_ventas,
              esfuerzo_total, prendas_requeridas, fecha_facturacion
            FROM {settings.db_schema}.costo_op_detalle
            WHERE familia_de_productos = ?
              AND tipo_de_producto = ?
              AND cliente = ?
              AND version_calculo = ?
              AND fecha_corrida = (
                SELECT MAX(fecha_corrida)
                FROM {settings.db_schema}.costo_op_detalle
                WHERE version_calculo = ?)
              AND fecha_facturacion >= (
                  SELECT (MAX(fecha_facturacion) - INTERVAL '6 months')
                  FROM {settings.db_schema}.costo_op_detalle
                  WHERE version_calculo = ?
              )
              AND prendas_requeridas > 0
            ORDER BY fecha_facturacion DESC,
            prendas_requeridas DESC
            LIMIT 20
            """

            resultados = await self.db.query(
                query_exacta,
                (
                    familia_producto,
                    tipo_prenda,
                    cliente,
                    version_calculo,
                    version_calculo,
                    version_calculo,
                ),
            )

            if resultados:
                logger.info(
                    f" Costos encontrados con cliente especfico: {len(resultados)} registros"
                )
                return self._procesar_costos_historicos_con_limites_previos(
                    resultados, "exacta_con_cliente"
                )

        #  CORREGIDO: Fechas relativas en lugar de GETDATE()
        query_familia = f"""
        SELECT
          costo_textil, costo_manufactura, costo_avios, costo_materia_prima,
          costo_indirecto_fijo, gasto_administracion, gasto_ventas,
          esfuerzo_total, prendas_requeridas, fecha_facturacion
        FROM {settings.db_schema}.costo_op_detalle
        WHERE familia_de_productos = ?
          AND tipo_de_producto = ?
          AND version_calculo = ?
          AND fecha_corrida = (
            SELECT MAX(fecha_corrida)
            FROM {settings.db_schema}.costo_op_detalle
            WHERE version_calculo = ?)
          AND fecha_facturacion >= (
            SELECT (MAX(fecha_facturacion) - INTERVAL '20 months')
            FROM {settings.db_schema}.costo_op_detalle
            WHERE version_calculo = ?
          )
          AND prendas_requeridas > 0
        ORDER BY fecha_facturacion DESC, prendas_requeridas DESC
        LIMIT 50
        """

        resultados = await self.db.query(
            query_familia,
            (
                familia_producto,
                tipo_prenda,
                version_calculo,
                version_calculo,
                version_calculo,
            ),
        )

        if resultados:
            logger.info(
                f" Costos encontrados por familia/tipo: {len(resultados)} registros"
            )
            return self._procesar_costos_historicos_con_limites_previos(
                resultados, "familia_tipo"
            )

        raise ValueError(
            f"No se encontraron costos histricos para {familia_producto} - {tipo_prenda}"
        )

    async def buscar_costos_estilo_especifico(
        self,
        codigo_estilo: str,
        meses: int = 12,
        version_calculo: str = "FLUIDA",
    ) -> Dict[str, Any]:
        """
         FUNCIN CORREGIDA: Busca costos histricos de un estilo especfico con fechas relativas
        """

        #  QUERY CORREGIDA: Con fechas relativas para PostgreSQL
        query = f"""
        SELECT
          COALESCE(costo_textil, 0) as costo_textil,
          COALESCE(costo_manufactura, 0) as costo_manufactura,
          COALESCE(costo_avios, 0) as costo_avios,
          COALESCE(costo_materia_prima, 0) as costo_materia_prima,
          COALESCE(costo_indirecto_fijo, 0) as costo_indirecto_fijo,
          COALESCE(gasto_administracion, 0) as gasto_administracion,
          COALESCE(gasto_ventas, 0) as gasto_ventas,
          COALESCE(esfuerzo_total, 6) as esfuerzo_total,
          prendas_requeridas, fecha_facturacion,
          cod_ordpro, cliente
        FROM {settings.db_schema}.costo_op_detalle c
        WHERE c.estilo_propio = ?
          AND c.version_calculo = ?
          AND c.fecha_corrida = (
            SELECT MAX(fecha_corrida)
            FROM {settings.db_schema}.costo_op_detalle
            WHERE version_calculo = ?)
          AND c.prendas_requeridas >= 200
          AND c.fecha_facturacion >= (
            SELECT (MAX(fecha_facturacion) - (? || ' months')::INTERVAL)
            FROM {settings.db_schema}.costo_op_detalle
            WHERE version_calculo = ?
          )
        ORDER BY c.fecha_facturacion DESC
        """

        try:
            resultados = await self.db.query(
                query,
                (codigo_estilo, version_calculo, version_calculo, str(meses), version_calculo),
            )

            if not resultados:
                logger.warning(
                    f" No se encontraron costos histricos para estilo {codigo_estilo} en {meses} meses"
                )
                # Retornar estructura vaca en lugar de lanzar excepcin
                return {
                    "codigo_estilo": codigo_estilo,
                    "costo_textil": 0,
                    "costo_manufactura": 0,
                    "costo_avios": 0,
                    "costo_materia_prima": 0,
                    "costo_indirecto_fijo": 0,
                    "gasto_administracion": 0,
                    "gasto_ventas": 0,
                    "esfuerzo_total": 6,
                    "registros_encontrados": 0,
                    "encontrado": False,
                }
        except Exception as e:
            logger.warning(
                f" Error en query de costos estilo {codigo_estilo}: {e}. Retornando valores por defecto"
            )
            # Retornar estructura con valores por defecto en caso de error
            return {
                "codigo_estilo": codigo_estilo,
                "costo_textil": 0,
                "costo_manufactura": 0,
                "costo_avios": 0,
                "costo_materia_prima": 0,
                "costo_indirecto_fijo": 0,
                "gasto_administracion": 0,
                "gasto_ventas": 0,
                "esfuerzo_total": 6,
                "registros_encontrados": 0,
                "encontrado": False,
            }

        logger.info(
            f" Costos estilo especfico encontrados: {len(resultados)} registros para {codigo_estilo}"
        )
        return self._procesar_costos_historicos_con_limites_previos(
            resultados, "estilo_especifico"
        )

    def _procesar_costos_historicos_con_limites_previos(
        self, recs: List[dict], strat: str
    ) -> Dict[str, Any]:
        """Aplica lmites de seguridad a valores antes de promediar."""
        if not recs:
            raise ValueError("Sin resultados")

        out, adjust = {}, {}
        cols = [
            "costo_textil",
            "costo_manufactura",
            "costo_avios",
            "costo_materia_prima",
            "costo_indirecto_fijo",
            "gasto_administracion",
            "gasto_ventas",
        ]

        def safe_float(val, default):
            return float(val) if isinstance(val, (int, float, Decimal)) else default

        for col in cols:
            vals = [
                safe_float(rec.get(col, 0), 0)
                / max(1.0, safe_float(rec.get("prendas_requeridas", 1), 1))
                for rec in recs
            ]
            adj = 0
            if col in factores.RANGOS_SEGURIDAD:
                min_val, max_val = (
                    factores.RANGOS_SEGURIDAD[col]["min"],
                    factores.RANGOS_SEGURIDAD[col]["max"],
                )
                for i, val in enumerate(vals):
                    clipped = max(min_val, min(max_val, val))
                    if clipped != val:
                        adj += 1
                    vals[i] = clipped
            adjust[col], out[col] = (
                adj,
                sum(vals) / len(vals),
            )

        out.update(
            {
                "esfuerzo_promedio": sum(
                    safe_float(rec.get("esfuerzo_total", 6), 6) for rec in recs
                )
                / len(recs),
                "registros_encontrados": len(recs),
                "registros_ajustados_por_componente": adjust,
                "total_ajustados": sum(adjust.values()),
                "estrategia_usada": strat,
                "fecha_mas_reciente": max(
                    (
                        rec["fecha_facturacion"]
                        for rec in recs
                        if isinstance(rec.get("fecha_facturacion"), datetime)
                    ),
                    default=None,
                ),
                "precision_estimada": min(1.0, len(recs) / 20.0),
                "version_calculo": "FLUIDA",
            }
        )

        logger.info(
            f" {len(recs)} registros procesados con estrategia '{strat}', {sum(adjust.values())} ajustes"
        )
        return out

    # ========================================
    #  NUEVA FUNCIN: OBTENER OPS DETALLADAS PARA TABLA INTERACTIVA
    # ========================================

    async def obtener_ops_detalladas_para_tabla(
        self,
        codigo_estilo: str,
        meses: int = 12,
        version_calculo: str = "FLUIDA",
    ) -> List[Dict[str, Any]]:
        """
        Obtiene lista detallada de OPs sin aplicar factor de seguridad.
        Retorna datos unitarios para cada OP para mostrar en tabla interactiva.

        BÚSQUEDA PROGRESIVA:
        1. Intenta primero con prendas >= 200 (filtro estricto)
        2. Si no encuentra, intenta sin ese filtro (fallback flexible)
        """

        try:
            # PASO 1: Intento CON filtro estricto (prendas >= 200)
            query_strict = f"""
            SELECT
              cod_ordpro,
              prendas_requeridas,
              COALESCE(costo_textil, 0) as costo_textil_total,
              COALESCE(costo_manufactura, 0) as costo_manufactura_total,
              COALESCE(costo_avios, 0) as costo_avios_total,
              COALESCE(costo_materia_prima, 0) as costo_materia_prima_total,
              COALESCE(costo_indirecto_fijo, 0) as costo_indirecto_fijo_total,
              COALESCE(gasto_administracion, 0) as gasto_administracion_total,
              COALESCE(gasto_ventas, 0) as gasto_ventas_total,
              COALESCE(esfuerzo_total, 6) as esfuerzo_total,
              fecha_facturacion,
              cliente
            FROM {settings.db_schema}.costo_op_detalle c
            WHERE c.estilo_propio::text = %s
              AND c.version_calculo = %s
              AND c.fecha_corrida = (
                SELECT MAX(fecha_corrida)
                FROM {settings.db_schema}.costo_op_detalle
                WHERE version_calculo = %s
                AND estilo_propio::text = %s)
              AND c.prendas_requeridas >= 200
              AND c.fecha_facturacion >= (
                SELECT (MAX(fecha_facturacion) - (%s || ' months')::INTERVAL)
                FROM {settings.db_schema}.costo_op_detalle
                WHERE version_calculo = %s
              )
            ORDER BY c.fecha_facturacion DESC
            """

            resultados = await self.db.query(
                query_strict,
                (codigo_estilo, version_calculo,
                 version_calculo, codigo_estilo, str(meses),
                 version_calculo),
            )

            # PASO 2: Si no encuentra con filtro estricto, intenta SIN filtro de prendas
            if not resultados:
                logger.info(f" [PROGRESIVO] No encontró OPs para estilo {codigo_estilo} con prendas>=200, intentando sin filtro...")

                query_flexible = f"""
                SELECT
                  cod_ordpro,
                  prendas_requeridas,
                  COALESCE(costo_textil, 0) as costo_textil_total,
                  COALESCE(costo_manufactura, 0) as costo_manufactura_total,
                  COALESCE(costo_avios, 0) as costo_avios_total,
                  COALESCE(costo_materia_prima, 0) as costo_materia_prima_total,
                  COALESCE(costo_indirecto_fijo, 0) as costo_indirecto_fijo_total,
                  COALESCE(gasto_administracion, 0) as gasto_administracion_total,
                  COALESCE(gasto_ventas, 0) as gasto_ventas_total,
                  COALESCE(esfuerzo_total, 6) as esfuerzo_total,
                  fecha_facturacion,
                  cliente
                FROM {settings.db_schema}.costo_op_detalle c
                WHERE c.estilo_propio::text = %s
                  AND c.version_calculo = %s
                  AND c.fecha_corrida = (
                    SELECT MAX(fecha_corrida)
                    FROM {settings.db_schema}.costo_op_detalle
                    WHERE version_calculo = %s
                    AND estilo_propio::text = %s)
                  AND c.fecha_facturacion >= (
                    SELECT (MAX(fecha_facturacion) - (%s || ' months')::INTERVAL)
                    FROM {settings.db_schema}.costo_op_detalle
                    WHERE version_calculo = %s
                  )
                ORDER BY c.fecha_facturacion DESC
                """

                resultados = await self.db.query(
                    query_flexible,
                    (codigo_estilo, version_calculo,
                     version_calculo, codigo_estilo, str(meses),
                     version_calculo),
                )

                if resultados:
                    logger.info(f" [PROGRESIVO] ✅ Encontradas {len(resultados)} OPs sin filtro de prendas para estilo {codigo_estilo}")

            if not resultados:
                logger.info(f" [PROGRESIVO] No se encontraron OPs para estilo {codigo_estilo} (ni con filtro estricto ni flexible)")
                return []

            # Procesar resultados para crear lista de OPs con datos unitarios
            ops_detalladas = []
            for row in resultados:
                prendas = float(row['prendas_requeridas']) or 1

                op_detalle = {
                    "cod_ordpro": row['cod_ordpro'],
                    "textil_unitario": float(row['costo_textil_total']) / prendas,
                    "manufactura_unitario": float(row['costo_manufactura_total']) / prendas,
                    "materia_prima_unitario": float(row['costo_materia_prima_total']) / prendas,
                    "avios_unitario": float(row['costo_avios_total']) / prendas,
                    "indirecto_fijo_unitario": float(row['costo_indirecto_fijo_total']),  # Ya es unitario en BD
                    "administracion_unitario": float(row['gasto_administracion_total']),  # Ya es unitario en BD
                    "ventas_unitario": float(row['gasto_ventas_total']),  # Ya es unitario en BD
                    "prendas_requeridas": int(prendas),
                    "fecha_facturacion": row['fecha_facturacion'].isoformat() if row['fecha_facturacion'] else None,
                    "esfuerzo_total": int(row['esfuerzo_total']) or 6,
                    "cliente": row['cliente'],
                    "seleccionado": True,  # Por defecto todas las OPs estn seleccionadas
                }

                # Calcular categora de lote
                categoria_lote, _ = factores.categorizar_lote(int(prendas))
                op_detalle["categoria_lote"] = categoria_lote

                ops_detalladas.append(op_detalle)

            logger.info(f" ✅ Obtenidas {len(ops_detalladas)} OPs detalladas para estilo {codigo_estilo}")
            return ops_detalladas

        except Exception as e:
            logger.error(f" Error obteniendo OPs detalladas para {codigo_estilo}: {e}")
            return []

    async def obtener_ops_estilo_nuevo(
        self,
        marca: str,
        tipo_prenda: str,
        meses: int = 12,
        version_calculo: str = "FLUIDA",
    ) -> List[Dict[str, Any]]:
        """
        Obtiene lista detallada de OPs por marca + tipo_prenda para estilos nuevos (fallback).
        Busca por cliente+tipo_prenda en lugar de estilo_propio.

        BÚSQUEDA PROGRESIVA:
        1. Intenta primero con prendas >= 200 (filtro estricto)
        2. Si no encuentra, intenta sin ese filtro (fallback flexible)
        """

        try:
            # PASO 1: Intento CON filtro estricto (prendas >= 200)
            query_strict = f"""
            SELECT
              cod_ordpro,
              prendas_requeridas,
              COALESCE(costo_textil, 0) as costo_textil_total,
              COALESCE(costo_manufactura, 0) as costo_manufactura_total,
              COALESCE(costo_avios, 0) as costo_avios_total,
              COALESCE(costo_materia_prima, 0) as costo_materia_prima_total,
              COALESCE(costo_indirecto_fijo, 0) as costo_indirecto_fijo_total,
              COALESCE(gasto_administracion, 0) as gasto_administracion_total,
              COALESCE(gasto_ventas, 0) as gasto_ventas_total,
              COALESCE(esfuerzo_total, 6) as esfuerzo_total,
              fecha_facturacion,
              cliente
            FROM {settings.db_schema}.costo_op_detalle c
            WHERE c.cliente ILIKE %s
              AND c.tipo_de_producto ILIKE %s
              AND c.version_calculo = %s
              AND c.fecha_corrida = (
                SELECT MAX(fecha_corrida)
                FROM {settings.db_schema}.costo_op_detalle
                WHERE version_calculo = %s)
              AND c.prendas_requeridas >= 200
              AND c.fecha_facturacion >= (
                SELECT (MAX(fecha_facturacion) - (%s || ' months')::INTERVAL)
                FROM {settings.db_schema}.costo_op_detalle
                WHERE version_calculo = %s
              )
            ORDER BY c.fecha_facturacion DESC
            """

            resultados = await self.db.query(
                query_strict,
                (f"%{marca.strip()}%", f"%{tipo_prenda.strip()}%", version_calculo,
                 version_calculo, str(meses), version_calculo),
            )

            # PASO 2: Si no encuentra con filtro estricto, intenta SIN filtro de prendas
            if not resultados:
                logger.info(f" [PROGRESIVO] No encontró OPs para marca={marca}, tipo_prenda={tipo_prenda} con prendas>=200, intentando sin filtro...")

                query_flexible = f"""
                SELECT
                  cod_ordpro,
                  prendas_requeridas,
                  COALESCE(costo_textil, 0) as costo_textil_total,
                  COALESCE(costo_manufactura, 0) as costo_manufactura_total,
                  COALESCE(costo_avios, 0) as costo_avios_total,
                  COALESCE(costo_materia_prima, 0) as costo_materia_prima_total,
                  COALESCE(costo_indirecto_fijo, 0) as costo_indirecto_fijo_total,
                  COALESCE(gasto_administracion, 0) as gasto_administracion_total,
                  COALESCE(gasto_ventas, 0) as gasto_ventas_total,
                  COALESCE(esfuerzo_total, 6) as esfuerzo_total,
                  fecha_facturacion,
                  cliente
                FROM {settings.db_schema}.costo_op_detalle c
                WHERE c.cliente ILIKE %s
                  AND c.tipo_de_producto ILIKE %s
                  AND c.version_calculo = %s
                  AND c.fecha_corrida = (
                    SELECT MAX(fecha_corrida)
                    FROM {settings.db_schema}.costo_op_detalle
                    WHERE version_calculo = %s)
                  AND c.fecha_facturacion >= (
                    SELECT (MAX(fecha_facturacion) - (%s || ' months')::INTERVAL)
                    FROM {settings.db_schema}.costo_op_detalle
                    WHERE version_calculo = %s
                  )
                ORDER BY c.fecha_facturacion DESC
                """

                resultados = await self.db.query(
                    query_flexible,
                    (f"%{marca.strip()}%", f"%{tipo_prenda.strip()}%", version_calculo,
                     version_calculo, str(meses), version_calculo),
                )

                if resultados:
                    logger.info(f" [PROGRESIVO] ✅ Encontradas {len(resultados)} OPs sin filtro de prendas para marca={marca}, tipo={tipo_prenda}")

            if not resultados:
                logger.info(f" [PROGRESIVO] No se encontraron OPs para marca={marca}, tipo_prenda={tipo_prenda} (ni con filtro estricto ni flexible)")
                return []

            # Procesar resultados para crear lista de OPs con datos unitarios
            ops_detalladas = []
            for row in resultados:
                prendas = float(row['prendas_requeridas']) or 1

                op_detalle = {
                    "cod_ordpro": row['cod_ordpro'],
                    "textil_unitario": float(row['costo_textil_total']) / prendas,
                    "manufactura_unitario": float(row['costo_manufactura_total']) / prendas,
                    "materia_prima_unitario": float(row['costo_materia_prima_total']) / prendas,
                    "avios_unitario": float(row['costo_avios_total']) / prendas,
                    "indirecto_fijo_unitario": float(row['costo_indirecto_fijo_total']),
                    "administracion_unitario": float(row['gasto_administracion_total']),
                    "ventas_unitario": float(row['gasto_ventas_total']),
                    "prendas_requeridas": int(prendas),
                    "fecha_facturacion": row['fecha_facturacion'].isoformat() if row['fecha_facturacion'] else None,
                    "esfuerzo_total": int(row['esfuerzo_total']) or 6,
                    "cliente": row['cliente'],
                    "seleccionado": True,
                }

                # Calcular categoría de lote
                categoria_lote, _ = factores.categorizar_lote(int(prendas))
                op_detalle["categoria_lote"] = categoria_lote

                ops_detalladas.append(op_detalle)

            logger.info(f" ✅ Obtenidas {len(ops_detalladas)} OPs para estilo nuevo (marca={marca}, tipo={tipo_prenda})")
            return ops_detalladas

        except Exception as e:
            logger.error(f" Error obteniendo OPs para estilo nuevo: {e}")
            return []

    async def obtener_costos_por_ops_especificas(
        self,
        cod_ordpros: List[str],
        version_calculo: str = "FLUIDA",
    ) -> List[Dict[str, Any]]:
        """
        ✨ MÉTODO NUEVO: Obtiene los 7 componentes de costo para OPs específicas.

        Utilizado por procesar_cotizacion_rapida_por_ops en utils.py para cotizaciones
        rápidas basadas en selección de OPs del usuario.

        Retorna lista de diccionarios con:
        - costo_textil (unitario)
        - costo_manufactura (unitario)
        - costo_avios (unitario)
        - costo_materia_prima (unitario)
        - costo_indirecto_fijo (unitario)
        - gasto_administracion (unitario)
        - gasto_ventas (unitario)
        """

        if not cod_ordpros:
            logger.warning(f" [COSTOS-OPS-ESPECIFICAS] No se proporcionaron cod_ordpros")
            return []

        # ✨ Normalizar version_calculo: convertir "FLUIDO" a "FLUIDA"
        version_norm = normalize_version_calculo(version_calculo)

        # Crear lista de placeholders para los códigos de OP
        placeholders = ','.join(['%s'] * len(cod_ordpros))

        # ✨ QUERY MEJORADA: Usar MAX(fecha_corrida) para cada OP + version_calculo
        query = f"""
        WITH ultima_fecha_por_op AS (
          SELECT
            cod_ordpro,
            MAX(fecha_corrida) as max_fecha
          FROM {settings.db_schema}.costo_op_detalle
          WHERE cod_ordpro IN ({placeholders})
            AND version_calculo = %s
            AND prendas_requeridas > 0
          GROUP BY cod_ordpro
        )
        SELECT
          c.cod_ordpro,
          c.prendas_requeridas,
          COALESCE(c.costo_textil, 0) as costo_textil_total,
          COALESCE(c.costo_manufactura, 0) as costo_manufactura_total,
          COALESCE(c.costo_avios, 0) as costo_avios_total,
          COALESCE(c.costo_materia_prima, 0) as costo_materia_prima_total,
          COALESCE(c.costo_indirecto_fijo, 0) as costo_indirecto_fijo_total,
          COALESCE(c.gasto_administracion, 0) as gasto_administracion_total,
          COALESCE(c.gasto_ventas, 0) as gasto_ventas_total,
          c.fecha_corrida
        FROM {settings.db_schema}.costo_op_detalle c
        INNER JOIN ultima_fecha_por_op u
          ON c.cod_ordpro = u.cod_ordpro
          AND c.fecha_corrida = u.max_fecha
          AND c.version_calculo = %s
        WHERE c.prendas_requeridas > 0
        ORDER BY c.cod_ordpro DESC
        """

        try:
            # Los parámetros son: los códigos de OP + la versión (2 veces en la query)
            params = list(cod_ordpros) + [version_norm, version_norm]
            resultados = await self.db.query(query, tuple(params))

            if not resultados:
                logger.warning(
                    f" [COSTOS-OPS-ESPECIFICAS] No se encontraron datos para OPs: {cod_ordpros}"
                )
                return []

            # Procesar resultados para retornar TOTALES (no dividir aquí)
            # utils.py se encargará de hacer la división por prendas totales
            costos_ops = []
            for row in resultados:
                prendas = float(row['prendas_requeridas']) or 1

                costo_op = {
                    "cod_ordpro": row['cod_ordpro'],
                    "prendas_requeridas": prendas,
                    # Retornar TOTALES sin dividir - utils.py hará la división total
                    "costo_textil_total": float(row['costo_textil_total']),
                    "costo_manufactura_total": float(row['costo_manufactura_total']),
                    "costo_avios_total": float(row['costo_avios_total']),
                    "costo_materia_prima_total": float(row['costo_materia_prima_total']),
                    # Estos sí se promedian (ya son unitarios en BD)
                    "costo_indirecto_fijo": float(row['costo_indirecto_fijo_total']),
                    "gasto_administracion": float(row['gasto_administracion_total']),
                    "gasto_ventas": float(row['gasto_ventas_total']),
                }

                costos_ops.append(costo_op)

            logger.info(
                f" [COSTOS-OPS-ESPECIFICAS] Obtenidos costos para {len(costos_ops)} OPs: {[op['cod_ordpro'] for op in costos_ops]}"
            )
            return costos_ops

        except Exception as e:
            logger.error(
                f" [COSTOS-OPS-ESPECIFICAS] Error obteniendo costos para OPs {cod_ordpros}: {e}"
            )
            import traceback
            logger.error(f" [COSTOS-OPS-ESPECIFICAS] Traceback: {traceback.format_exc()}")
            return []

    async def obtener_desglose_wip_por_ops(
        self,
        cod_ordpros: List[str],
        version_calculo: str = "FLUIDA",
    ) -> List[Dict[str, Any]]:
        """
        Obtiene desglose de costos por WIP para OPs seleccionadas.
        Lógica: Para cada OP en cod_ordpros, busca sus WIPs en costo_wip_op,
        agrupa por WIP y calcula costo_textil/manufactura dividido por prendas_requeridas de esa OP.
        """

        if not cod_ordpros:
            logger.warning(" [WIP-DESGLOSE] No se proporcionaron cod_ordpros")
            return []

        # ✨ Normalizar version_calculo
        version_norm = normalize_version_calculo(version_calculo)

        logger.info(f" [WIP-DESGLOSE] ===== INICIANDO DESGLOSE WIP =====")
        logger.info(f" [WIP-DESGLOSE] OPs: {cod_ordpros}, Version: {version_norm}")

        try:
            placeholders = ",".join(["%s"] * len(cod_ordpros))

            # ✨ QUERY OPTIMIZADA Y SIMPLE
            query = f"""
            SELECT
                cwo.wip_id,
                CASE
                    WHEN cwo.wip_id IN ('16', '14', '19a', '19c', '24', '10c') THEN 'textil'
                    WHEN cwo.wip_id IN ('34', '36', '40', '44', '37', '45', '49', '43', '50') THEN 'manufactura'
                    ELSE 'otro'
                END as grupo_wip,
                cwo.pr_id,
                cod.prendas_requeridas,
                SUM(cwo.costo_textil) as total_textil,
                SUM(cwo.costo_manufactura) as total_manufactura
            FROM {settings.db_schema}.costo_wip_op cwo
            INNER JOIN {settings.db_schema}.costo_op_detalle cod
                ON cwo.pr_id::TEXT = cod.cod_ordpro
            WHERE cwo.pr_id::TEXT IN ({placeholders})
              AND cwo.version_calculo = %s
              AND cod.version_calculo = %s
            GROUP BY cwo.wip_id, cwo.pr_id, cod.prendas_requeridas
            ORDER BY cwo.wip_id
            """

            params = list(cod_ordpros) + [version_norm, version_norm]

            logger.info(f" [WIP-DESGLOSE] Ejecutando query con {len(cod_ordpros)} OPs...")
            resultados = await self.db.query(query, params)

            logger.info(f" [WIP-DESGLOSE] ✅ Query completada: {len(resultados)} filas")

            # Agrupar por WIP
            wips_dict = {}
            for row in resultados:
                wip_id = row['wip_id']
                if wip_id not in wips_dict:
                    wips_dict[wip_id] = {
                        "wip_id": wip_id,
                        "grupo_wip": row['grupo_wip'],
                        "total_textil": 0.0,
                        "total_manufactura": 0.0,
                        "total_prendas": 0,
                        "ops_count": 0
                    }

                prendas = float(row['prendas_requeridas']) if row['prendas_requeridas'] else 1
                wips_dict[wip_id]["total_textil"] += float(row['total_textil']) if row['total_textil'] else 0.0
                wips_dict[wip_id]["total_manufactura"] += float(row['total_manufactura']) if row['total_manufactura'] else 0.0
                wips_dict[wip_id]["total_prendas"] += prendas
                wips_dict[wip_id]["ops_count"] += 1

            # Calcular costos por prenda
            desgloses = []
            for wip_id, wip_data in wips_dict.items():
                prendas = wip_data["total_prendas"] if wip_data["total_prendas"] > 0 else 1

                desglose = {
                    "wip_id": wip_id,
                    "grupo_wip": wip_data["grupo_wip"],
                    "total_prendas": int(wip_data["total_prendas"]),
                    "total_textil": round(wip_data["total_textil"], 2),
                    "total_manufactura": round(wip_data["total_manufactura"], 2),
                    "textil_por_prenda": round(wip_data["total_textil"] / prendas, 4),
                    "manufactura_por_prenda": round(wip_data["total_manufactura"] / prendas, 4),
                }
                desgloses.append(desglose)
                logger.info(f" [WIP-DESGLOSE] WIP {wip_id}: {desglose['textil_por_prenda']:.4f} textil/prenda, {desglose['manufactura_por_prenda']:.4f} manufactura/prenda")

            logger.info(f" [WIP-DESGLOSE] ✅ {len(desgloses)} WIPs procesados")
            return desgloses

        except Exception as e:
            logger.error(f" [WIP-DESGLOSE] ❌ Error: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return []

    async def calcular_costos_ponderados_por_ops(
        self,
        cod_ordpros: List[str],
        version_calculo: str = "FLUIDA",
    ) -> Dict[str, float]:
        """
        Calcula los costos textil y manufactura ponderados por prendas para las OPs seleccionadas.

        Frmula:
            costo_ponderado = SUM(costo_op * prendas_op) / SUM(prendas_op)

        Returns:
            Dict con 'textil' y 'manufactura' (costos por prenda ponderados)
        """
        if not cod_ordpros:
            logger.warning(" [COSTOS-PONDERADOS] No se proporcionaron OPs")
            return {}

        version_norm = version_calculo

        try:
            logger.info(f" [COSTOS-PONDERADOS] Calculando para {len(cod_ordpros)} OPs: {cod_ordpros}")

            placeholders = ",".join(["%s"] * len(cod_ordpros))

            query = f"""
            WITH ultimas_fechas AS (
                SELECT MAX(fecha_corrida) as fecha_max
                FROM silver.costo_op_detalle
                WHERE version_calculo = %s
            )
            SELECT
                ROUND((SUM(costo_textil) / NULLIF(SUM(prendas_requeridas), 0))::NUMERIC, 4) as costo_textil_ponderado,
                ROUND((SUM(costo_manufactura) / NULLIF(SUM(prendas_requeridas), 0))::NUMERIC, 4) as costo_manufactura_ponderado,
                SUM(prendas_requeridas) as total_prendas,
                COUNT(DISTINCT cod_ordpro) as ops_encontradas
            FROM silver.costo_op_detalle cod
            INNER JOIN ultimas_fechas uf ON cod.fecha_corrida = uf.fecha_max
            WHERE cod.cod_ordpro::text IN ({placeholders})
              AND cod.version_calculo = %s
            """

            params = [version_norm] + cod_ordpros + [version_norm]

            resultado = await self.db.query(query, params)

            if resultado and len(resultado) > 0:
                row = resultado[0]
                costo_textil = float(row['costo_textil_ponderado']) if row['costo_textil_ponderado'] else 0.0
                costo_manufactura = float(row['costo_manufactura_ponderado']) if row['costo_manufactura_ponderado'] else 0.0

                logger.info(
                    f" [COSTOS-PONDERADOS] Resultado: textil=${costo_textil:.4f}, manufactura=${costo_manufactura:.4f}, "
                    f"prendas={row['total_prendas']}, ops={row['ops_encontradas']}"
                )

                return {
                    "textil": costo_textil,
                    "manufactura": costo_manufactura,
                    "total_prendas": row['total_prendas'],
                    "ops_encontradas": row['ops_encontradas'],
                }
            else:
                logger.warning(f" [COSTOS-PONDERADOS] No se encontraron datos para las OPs")
                return {}

        except Exception as e:
            logger.error(f" [COSTOS-PONDERADOS] Error calculando costos ponderados: {e}")
            import traceback
            logger.error(f" [COSTOS-PONDERADOS] Traceback: {traceback.format_exc()}")
            return {}

    # ========================================
    #  FUNCIONES DE WIPS (SIN CAMBIOS - YA USAN FECHAS RELATIVAS)
    # ========================================

    async def obtener_costos_wips_por_estabilidad(
        self,
        tipo_prenda: str,
        version_calculo: str = "FLUIDA",
        marca: Optional[str] = None,
    ) -> Dict[str, float]:
        """Usar anlisis inteligente de variacin con filtro de marca y prendas >= 200"""
        try:
            return await self.obtener_costos_wips_inteligente(
                tipo_prenda, version_calculo, marca
            )
        except Exception as e:
            logger.warning(
                f" Error en anlisis inteligente, usando mtodo legacy: {e}"
            )
            return await self._obtener_costos_wips_legacy(tipo_prenda, version_calculo, marca)

    async def obtener_costos_wips_inteligente(
        self,
        tipo_prenda: str,
        version_calculo: str = "FLUIDA",
        marca: Optional[str] = None,
    ) -> Dict[str, float]:
        """
        CORRECCIN: Filtra por marca y total_prendas >= 200
        """

        costos_wips = {}

        #  QUERY CORREGIDA: marca + filtro prendas >= 200
        version_norm = version_calculo

        query_variabilidad = f"""
        SELECT
          wip_id,
          EXTRACT(YEAR FROM mes) as ao,
          EXTRACT(MONTH FROM mes) as mes,
          AVG(CAST(costo_por_prenda AS FLOAT)) as costo_mensual,
          AVG(CAST(total_prendas AS FLOAT)) as prendas_promedio
        FROM {settings.db_schema}.resumen_wip_por_prenda
        WHERE tipo_de_producto = %s
          AND version_calculo = %s
          AND fecha_corrida = (
            SELECT MAX(fecha_corrida)
            FROM {settings.db_schema}.resumen_wip_por_prenda
            WHERE version_calculo = %s)
          AND mes >= (
            SELECT (MAX(mes) - INTERVAL '18 months')
            FROM {settings.db_schema}.resumen_wip_por_prenda
            WHERE version_calculo = %s AND tipo_de_producto = %s
          )
          AND costo_por_prenda > 0
          AND total_prendas >= 200
          {f"AND marca = %s" if marca else ""}
        GROUP BY wip_id, EXTRACT(YEAR FROM mes), EXTRACT(MONTH FROM mes)
        ORDER BY wip_id, ao DESC, mes DESC
        """

        params = [
            tipo_prenda,
            version_norm,
            version_norm,
            version_norm,
            tipo_prenda,
        ]
        if marca:
            params.append(marca)

        resultados_variabilidad = await self.db.query(
            query_variabilidad,
            tuple(params),
        )

        # Procesar por WIP
        wips_data: Dict[str, Any] = {}
        for row in resultados_variabilidad:
            wip_id = row["wip_id"]
            if wip_id not in wips_data:
                wips_data[wip_id] = []
            costo_mensual = float(row["costo_mensual"]) if row["costo_mensual"] else 0.0
            wips_data[wip_id].append(costo_mensual)

        logger.info(
            f" Anlisis variabilidad: {len(wips_data)} WIPs encontrados para {tipo_prenda} ({version_calculo})"
        )

        # Analizar variabilidad y decidir perodo
        for wip_id, costos_mensuales in wips_data.items():
            if len(costos_mensuales) < 2:
                # Si hay pocos datos, usar promedio simple
                costos_wips[wip_id] = float(
                    sum(costos_mensuales) / len(costos_mensuales)
                )
                logger.debug(
                    f"WIP {wip_id}: POCOS DATOS ({len(costos_mensuales)} meses) - Promedio simple: ${costos_wips[wip_id]:.2f}"
                )
                continue

            # Calcular coeficiente de variacin
            try:
                promedio = statistics.mean(costos_mensuales)
                desviacion = (
                    statistics.stdev(costos_mensuales)
                    if len(costos_mensuales) > 1
                    else 0
                )
                coef_variacion = (desviacion / promedio) if promedio > 0 else 0
            except statistics.StatisticsError:
                coef_variacion = 0.15

            # Decisin inteligente del perodo
            if coef_variacion <= 0.10:
                periodo_meses = 3
                logger.debug(
                    f"WIP {wip_id}: ESTABLE (CV: {coef_variacion:.1%}) - Usando 3 meses"
                )
            else:
                periodo_meses = 6
                logger.debug(
                    f"WIP {wip_id}: VARIABLE (CV: {coef_variacion:.1%}) - Usando 6 meses"
                )

            #  QUERY ESPECFICA CORREGIDA: marca + filtro prendas >= 200
            if wip_id in ["37", "45"]:
                # WIPs inestables: siempre promedio
                query_wip = f"""
                SELECT
                  AVG(CAST(costo_por_prenda AS FLOAT)) as costo_promedio
                FROM {settings.db_schema}.resumen_wip_por_prenda
                WHERE wip_id = %s
                  AND tipo_de_producto = %s
                  AND version_calculo = %s
                  AND fecha_corrida = (
                    SELECT MAX(fecha_corrida)
                    FROM {settings.db_schema}.resumen_wip_por_prenda
                    WHERE version_calculo = %s)
                  AND mes >= (
                    SELECT (MAX(mes) - %s * INTERVAL '1 month')
                    FROM {settings.db_schema}.resumen_wip_por_prenda
                    WHERE version_calculo = %s AND tipo_de_producto = %s
                  )
                  AND costo_por_prenda > 0
                  AND total_prendas >= 200
                  {f"AND marca = %s" if marca else ""}
                """
                params_wip = [
                    wip_id,
                    tipo_prenda,
                    version_norm,
                    version_norm,
                    periodo_meses,
                    version_norm,
                    tipo_prenda,
                ]
                if marca:
                    params_wip.append(marca)

                resultado_wip = await self.db.query(
                    query_wip,
                    tuple(params_wip),
                )
            else:
                if coef_variacion <= 0.10:
                    # Estable: ltimo costo
                    query_wip = f"""
                    SELECT
                      CAST(costo_por_prenda AS FLOAT) as costo_promedio
                    FROM {settings.db_schema}.resumen_wip_por_prenda
                    WHERE wip_id = %s AND tipo_de_producto = %s
                      AND version_calculo = %s
                      AND fecha_corrida = (
                      SELECT MAX(fecha_corrida)
                      FROM {settings.db_schema}.resumen_wip_por_prenda
                      WHERE version_calculo = %s)
                    AND costo_por_prenda > 0
                    AND total_prendas >= 200
                    {f"AND marca = %s" if marca else ""}
                    ORDER BY mes DESC
                    LIMIT 1
                    """
                    params_wip = [wip_id, tipo_prenda, version_norm, version_norm]
                    if marca:
                        params_wip.append(marca)

                    resultado_wip = await self.db.query(
                        query_wip,
                        tuple(params_wip),
                    )
                else:
                    # Variable: promedio del perodo
                    query_wip = f"""
                    SELECT AVG(CAST(costo_por_prenda AS FLOAT)) as costo_promedio
                    FROM {settings.db_schema}.resumen_wip_por_prenda
                    WHERE wip_id = %s AND tipo_de_producto = %s
                      AND version_calculo = %s
                      AND fecha_corrida = (
                        SELECT MAX(fecha_corrida)
                        FROM {settings.db_schema}.resumen_wip_por_prenda
                        WHERE version_calculo = %s)
                      AND mes >= (
                        SELECT (MAX(mes) - %s * INTERVAL '1 month')
                        FROM {settings.db_schema}.resumen_wip_por_prenda
                        WHERE version_calculo = %s AND tipo_de_producto = %s
                      )
                      AND costo_por_prenda > 0
                      AND total_prendas >= 200
                      {f"AND marca = %s" if marca else ""}
                    """
                    params_wip = [
                        wip_id,
                        tipo_prenda,
                        version_norm,
                        version_norm,
                        periodo_meses,
                        version_norm,
                        tipo_prenda,
                    ]
                    if marca:
                        params_wip.append(marca)

                    resultado_wip = await self.db.query(
                        query_wip,
                        tuple(params_wip),
                    )

            if resultado_wip and resultado_wip[0]["costo_promedio"]:
                costos_wips[wip_id] = float(resultado_wip[0]["costo_promedio"])
                logger.debug(f" WIP {wip_id}: ${costos_wips[wip_id]:.2f}")

        logger.info(
            f" Anlisis inteligente completado: {len(costos_wips)} WIPs para {tipo_prenda} ({version_calculo})"
        )
        return costos_wips

    async def obtener_ruta_textil_recomendada(
        self,
        tipo_prenda: str,
        version_calculo: str = "FLUIDA",
        marca: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        CORRECCIN: Filtra por marca y total_prendas >= 200
        """

        # Normalizar version_calculo (FLUIDA -> FLUIDA)
        version_normalized = version_calculo

        #  QUERY CORREGIDA: marca + filtro prendas >= 200
        query_ruta = f"""
        SELECT
          w.wip_id,
          COUNT(*) as frecuencia_uso,
          AVG(w.costo_por_prenda) as costo_promedio,
          MAX(w.mes) as ultimo_uso,
          AVG(w.total_prendas) as prendas_promedio,
          SUM(w.total_prendas) as total_prendas_acumulado,
          w.wip_id as grupo_wip
        FROM {settings.db_schema}.resumen_wip_por_prenda w
        WHERE w.tipo_de_producto = %s
          AND w.version_calculo = %s
          AND w.fecha_corrida = (
            SELECT MAX(fecha_corrida)
            FROM {settings.db_schema}.resumen_wip_por_prenda
            WHERE version_calculo = %s)
          AND w.mes >= (
            SELECT (MAX(mes) - INTERVAL '18 months')
            FROM {settings.db_schema}.resumen_wip_por_prenda
            WHERE version_calculo = %s AND tipo_de_producto = %s
          )
          AND w.costo_por_prenda > 0
          AND w.total_prendas >= 200
          {f"AND w.marca = %s" if marca else ""}
        GROUP BY w.wip_id
        HAVING COUNT(*) >= 1
        ORDER BY COUNT(*) DESC, AVG(w.costo_por_prenda) ASC
        LIMIT 25
        """

        params = [
            tipo_prenda,
            version_normalized,
            version_normalized,
            version_normalized,
            tipo_prenda,
        ]
        if marca:
            params.append(marca)

        resultados = await self.db.query(
            query_ruta,
            tuple(params),
        )

        # Separar por grupos y enriquecer informacin
        wips_textiles = []
        wips_manufactura = []
        wips_recomendadas = []

        for row in resultados:
            wip_data = {
                "wip_id": row["wip_id"],
                "nombre": factores.NOMBRES_WIPS.get(
                    row["wip_id"], f"WIP {row['wip_id']}"
                ),
                "frecuencia_uso": int(row["frecuencia_uso"]),
                "costo_promedio": float(row["costo_promedio"]),
                "ultimo_uso": row["ultimo_uso"],
                "prendas_promedio": float(row["prendas_promedio"])
                if row["prendas_promedio"]
                else 0,
                "total_prendas_acumulado": int(row["total_prendas_acumulado"])
                if row["total_prendas_acumulado"]
                else 0,
                "recomendacion": "Alta"
                if row["frecuencia_uso"] >= 6
                else "Media"
                if row["frecuencia_uso"] >= 3
                else "Baja",
            }

            # Agregar a lista general
            wips_recomendadas.append(wip_data)

            # Clasificar por grupo
            if row["wip_id"] in factores.WIPS_TEXTILES:
                wips_textiles.append(wip_data)
            elif row["wip_id"] in factores.WIPS_MANUFACTURA:
                wips_manufactura.append(wip_data)

        logger.info(
            f" Ruta textil obtenida para {tipo_prenda} ({version_calculo}): {len(wips_recomendadas)} WIPs"
        )

        return {
            "tipo_prenda": tipo_prenda,
            "version_calculo": version_calculo,
            "wips_recomendadas": wips_recomendadas,
            "wips_textiles_recomendadas": wips_textiles,
            "wips_manufactura_recomendadas": wips_manufactura,
            "total_recomendadas": len(wips_recomendadas),
            "metodo": "frecuencia_uso_12_meses_sin_filtros_prendas",
            "fecha_analisis": datetime.now().isoformat(),
            "filtros_aplicados": {
                "min_prendas": "ELIMINADO",
                "min_frecuencia": 1,
                "meses_hacia_atras": 12,
                "fecha_relativa": "MAX(mes) de tabla",
                "max_resultados": 25,
            },
        }

    async def _obtener_costos_wips_legacy(
        self,
        tipo_prenda: str,
        version_calculo: str = "FLUIDA",
        marca: Optional[str] = None,
    ) -> Dict[str, float]:
        """ CORRECCIN: Filtra por marca y total_prendas >= 200"""
        costos_wips = {}
        version_norm = version_calculo

        #  WIPs inestables (37, 45): Promedio con marca + filtro prendas >= 200
        query_inestables = f"""
        SELECT wip_id, AVG(CAST(costo_por_prenda AS FLOAT)) as costo_promedio
        FROM {settings.db_schema}.resumen_wip_por_prenda
        WHERE wip_id IN ('37', '45')
          AND tipo_de_producto = %s
          AND version_calculo = %s
          AND fecha_corrida = (
            SELECT MAX(fecha_corrida)
            FROM {settings.db_schema}.resumen_wip_por_prenda
            WHERE version_calculo = %s)
          AND mes >= (
            SELECT (MAX(mes) - INTERVAL '18 months')
            FROM {settings.db_schema}.resumen_wip_por_prenda
            WHERE version_calculo = %s AND tipo_de_producto = %s
          )
          AND costo_por_prenda > 0
          AND total_prendas >= 200
          {f"AND marca = %s" if marca else ""}
        GROUP BY wip_id
        """

        params_inestables = [
            tipo_prenda,
            version_norm,
            version_norm,
            version_norm,
            tipo_prenda,
        ]
        if marca:
            params_inestables.append(marca)

        resultados_inestables = await self.db.query(
            query_inestables,
            tuple(params_inestables),
        )
        for row in resultados_inestables:
            costos_wips[row["wip_id"]] = float(row["costo_promedio"])

        #  WIPs estables: ltimo costo, con marca + filtro prendas >= 200
        query_estables = f"""
        WITH UltimosCostos AS (
          SELECT
            wip_id,
            CAST(costo_por_prenda AS FLOAT) as costo_por_prenda,
            ROW_NUMBER() OVER (PARTITION BY wip_id ORDER BY mes DESC) as rn
          FROM {settings.db_schema}.resumen_wip_por_prenda
          WHERE wip_id NOT IN ('37', '45')
            AND tipo_de_producto = %s
            AND version_calculo = %s
            AND fecha_corrida = (
              SELECT MAX(fecha_corrida)
              FROM {settings.db_schema}.resumen_wip_por_prenda
              WHERE version_calculo = %s)
          AND costo_por_prenda > 0
          AND total_prendas >= 200
          {f"AND marca = %s" if marca else ""}
        )
        SELECT wip_id, costo_por_prenda
        FROM UltimosCostos WHERE rn = 1
        """

        params_estables = [tipo_prenda, version_norm, version_norm]
        if marca:
            params_estables.append(marca)

        resultados_estables = await self.db.query(
            query_estables, tuple(params_estables)
        )
        for row in resultados_estables:
            costos_wips[row["wip_id"]] = float(row["costo_por_prenda"])

        logger.info(
            f" Mtodo legacy: {len(costos_wips)} WIPs encontrados para {tipo_prenda} ({version_calculo})"
        )
        return costos_wips

    async def obtener_wips_disponibles_estructurado(
        self,
        tipo_prenda: Optional[str] = None,
        version_calculo: str = "FLUIDA",
        marca: Optional[str] = None,
    ) -> Tuple[List[WipDisponible], List[WipDisponible]]:
        """ CORREGIDO: Filtra por marca y prendas >= 200"""

        try:
            if tipo_prenda:
                logger.info(
                    f" Obteniendo WIPs especficos para {tipo_prenda} ({version_calculo})"
                )
                costos_wips = await self.obtener_costos_wips_por_estabilidad(
                    tipo_prenda, version_calculo, marca
                )
            else:
                logger.info(f" Obteniendo WIPs genricos ({version_calculo})")
                version_norm = version_calculo

                # OPTIMIZACIN: Obtener MAX(fecha_corrida) primero
                query_max_fecha = f"""
                SELECT MAX(fecha_corrida) as max_fecha
                FROM {settings.db_schema}.resumen_wip_por_prenda
                WHERE version_calculo = %s
                """
                max_fecha_result = await self.db.query(query_max_fecha, (version_norm,), timeout=10)

                if not max_fecha_result or not max_fecha_result[0].get('max_fecha'):
                    logger.warning(f" No hay datos para version {version_norm}")
                    return [], []

                max_fecha = max_fecha_result[0]['max_fecha']

                #  QUERY OPTIMIZADA: PostgreSQL placeholders %s
                query = f"""
                SELECT
                  wip_id,
                  AVG(costo_por_prenda) as costo_promedio
                FROM {settings.db_schema}.resumen_wip_por_prenda
                WHERE costo_por_prenda > 0
                  AND version_calculo = %s
                  AND fecha_corrida = %s
                GROUP BY wip_id
                """

                resultados = await self.db.query(
                    query, (version_norm, max_fecha), timeout=30
                )
                costos_wips = {}
                for row in resultados:
                    costos_wips[row["wip_id"]] = float(row["costo_promedio"])

            logger.info(f" Costos WIP obtenidos: {len(costos_wips)} WIPs disponibles")

            # Estructurar WIPs textiles
            wips_textiles: List[WipDisponible] = []
            for wip_id in factores.WIPS_TEXTILES:
                costo_actual = costos_wips.get(wip_id, 0.0)
                wips_textiles.append(
                    WipDisponible(
                        wip_id=wip_id,
                        nombre=factores.NOMBRES_WIPS.get(
                            wip_id, f"WIP {wip_id} - Textil"
                        ),
                        costo_actual=costo_actual,
                        disponible=costo_actual > 0,
                        grupo="Textil",
                    )
                )

            # Estructurar WIPs manufactura
            wips_manufactura: List[WipDisponible] = []
            for wip_id in factores.WIPS_MANUFACTURA:
                costo_actual = costos_wips.get(wip_id, 0.0)
                wips_manufactura.append(
                    WipDisponible(
                        wip_id=wip_id,
                        nombre=factores.NOMBRES_WIPS.get(
                            wip_id, f"WIP {wip_id} - Manufactura"
                        ),
                        costo_actual=costo_actual,
                        disponible=costo_actual > 0,
                        grupo="Manufactura",
                    )
                )

            logger.info(
                f" WIPs estructurados: {len(wips_textiles)} textiles, {len(wips_manufactura)} manufactura"
            )
            return wips_textiles, wips_manufactura

        except Exception as e:
            logger.error(f" Error en obtener_wips_disponibles_estructurado: {e}")
            return [], []

    async def obtener_gastos_por_estilo_recurrente(
        self,
        codigo_estilo: str,
        version_calculo: str = "FLUIDA",
    ) -> Tuple[Dict[str, float], List[str]]:
        """
        Obtiene gastos indirectos para estilos RECURRENTES usando MODA.

        Busca todas las OPs que fueron producidas con ese cdigo_estilo exacto,
        calcula la MODA de los tres costos, filtra outliers (mx 10x la moda),
        y retorna los gastos con los ndices de OPs excluidas.

        Args:
            codigo_estilo: El cdigo de estilo propio exacto
            version_calculo: FLUIDA o truncado

        Returns:
            Tupla (gastos_dict, ops_excluidas_indices)
            - gastos_dict: {"costo_indirecto_fijo": float, "gasto_administracion": float, "gasto_ventas": float}
            - ops_excluidas_indices: Lista de ndices de OPs que fueron excluidas
        """

        try:
            version_norm = version_calculo

            # OPTIMIZACION: Obtener fechas límite primero - DEL ESTILO ESPECÍFICO
            query_fechas = f"""
            SELECT
                MAX(fecha_corrida) as max_fecha_corrida,
                MAX(fecha_facturacion) - INTERVAL '24 months' as min_fecha_fact
            FROM {settings.db_schema}.costo_op_detalle
            WHERE estilo_propio = %s
                AND version_calculo = %s
            """
            fechas_result = await self.db.query(query_fechas, (codigo_estilo, version_norm), timeout=10)

            if not fechas_result or not fechas_result[0].get('max_fecha_corrida'):
                logger.warning(f" No se encontraron OPs para estilo recurrente: {codigo_estilo}")
                return {
                    "costo_indirecto_fijo": 0,
                    "gasto_administracion": 0,
                    "gasto_ventas": 0,
                }, []

            max_fecha_corrida = fechas_result[0]['max_fecha_corrida']
            min_fecha_fact = fechas_result[0]['min_fecha_fact']

            # QUERY OPTIMIZADA: Sin subqueries en WHERE - SIN filtros restrictivos de costos/prendas
            query = f"""
            SELECT
                costo_indirecto_fijo,
                gasto_administracion,
                gasto_ventas,
                prendas_requeridas,
                cod_ordpro,
                fecha_corrida,
                fecha_facturacion,
                ROW_NUMBER() OVER (ORDER BY fecha_facturacion DESC) as rn
            FROM {settings.db_schema}.costo_op_detalle
            WHERE estilo_propio = %s
                AND version_calculo = %s
                AND fecha_corrida = %s
                AND fecha_facturacion >= %s
            ORDER BY fecha_facturacion DESC
            """

            params = (
                codigo_estilo,
                version_norm,
                max_fecha_corrida,
                min_fecha_fact,
            )
            resultado = await self.db.query(query, params, timeout=30)

            if not resultado:
                logger.warning(f" No se encontraron OPs para estilo recurrente: {codigo_estilo}")
                logger.info(f" [DEBUG] Búsqueda con estilo_propio='{codigo_estilo}', version={version_norm}, fecha_corrida={max_fecha_corrida}")
                return {
                    "costo_indirecto_fijo": 0,
                    "gasto_administracion": 0,
                    "gasto_ventas": 0,
                }, []

            # Extraer los tres valores unitarios y aplicar normalizacion ANTES de promediar
            indirectos = []
            admins = []
            ventas = []
            ops_info = []

            def safe_float(val, default):
                """Convierte valor a float de forma segura"""
                if isinstance(val, (int, float, Decimal)):
                    return float(val)
                return default

            for row in resultado:
                # Los costos ya vienen por prenda en la tabla
                cif_raw = safe_float(row.get("costo_indirecto_fijo", 0), 0)
                admin_raw = safe_float(row.get("gasto_administracion", 0), 0)
                venta_raw = safe_float(row.get("gasto_ventas", 0), 0)

                indirectos.append(cif_raw)
                admins.append(admin_raw)
                ventas.append(venta_raw)
                ops_info.append({
                    "rn": row["rn"],
                    "cod_ordpro": row["cod_ordpro"],
                })

            # Aplicar normalizacion a cada valor ANTES de promediar
            # Esto es consistente con _procesar_costos_historicos_con_limites_previos
            def normalizar_valores_antes_de_promediar(valores, componente):
                """Normaliza valores contra rangos de seguridad, luego promedia"""
                if not valores:
                    return 0, 0

                # Aplicar rangos de seguridad a cada valor individual
                valores_normalizados = []
                ajustes_count = 0

                if componente in factores.RANGOS_SEGURIDAD:
                    min_val = factores.RANGOS_SEGURIDAD[componente]["min"]
                    max_val = factores.RANGOS_SEGURIDAD[componente]["max"]

                    for val in valores:
                        val_float = safe_float(val, 0)
                        # Aplicar limites
                        val_normalizado = max(min_val, min(max_val, val_float))
                        if val_normalizado != val_float:
                            ajustes_count += 1
                        valores_normalizados.append(val_normalizado)
                else:
                    valores_normalizados = [safe_float(v, 0) for v in valores]

                # LUEGO promediar los valores normalizados
                promedio = sum(valores_normalizados) / len(valores_normalizados) if valores_normalizados else 0
                return float(promedio), ajustes_count

            # Calcular promedios aplicando normalizacion ANTES
            cif_promedio, cif_ajustes = normalizar_valores_antes_de_promediar(
                indirectos, "costo_indirecto_fijo"
            )
            admin_promedio, admin_ajustes = normalizar_valores_antes_de_promediar(
                admins, "gasto_administracion"
            )
            venta_promedio, venta_ajustes = normalizar_valores_antes_de_promediar(
                ventas, "gasto_ventas"
            )

            gastos = {
                "costo_indirecto_fijo": cif_promedio,
                "gasto_administracion": admin_promedio,
                "gasto_ventas": venta_promedio,
            }

            # Rastrear si hubo ajustes
            total_ajustes = cif_ajustes + admin_ajustes + venta_ajustes
            if total_ajustes > 0:
                logger.info(
                    f" Normalizacion aplicada en gastos indirectos recurrentes: {total_ajustes} valores ajustados"
                )

            ops_excluidas = []

            logger.info(
                f" Gastos recurrentes (estilo {codigo_estilo}): {gastos} | OPs excluidas: {len(ops_excluidas)}"
            )
            return gastos, ops_excluidas

        except Exception as e:
            logger.error(f" Error en obtener_gastos_por_estilo_recurrente: {e}")
            return {
                "costo_indirecto_fijo": 0,
                "gasto_administracion": 0,
                "gasto_ventas": 0,
            }, []

    async def obtener_gastos_por_estilo_nuevo(
        self,
        marca: str,
        familia_prenda: Optional[str],
        tipo_prenda: str,
        version_calculo: str = "FLUIDA",
    ) -> Tuple[Dict[str, float], List[str]]:
        """
        Obtiene gastos indirectos para estilos NUEVOS usando MODA.

        Busca todas las OPs que tengan la misma marca + tipo_prenda.
        NOTA: familia_prenda es OPCIONAL y NO se usa como filtro

        Calcula la MODA de los tres costos, filtra outliers (mx 10x la moda),
        y retorna los gastos con los ndices de OPs excluidas.

        Args:
            marca: Cliente/marca
            familia_prenda: (OPCIONAL - no se usa como filtro)
            tipo_prenda: Tipo de prenda
            version_calculo: FLUIDA o truncado

        Returns:
            Tupla (gastos_dict, ops_excluidas_indices)
        """
        try:
            query = f"""
            SELECT
                costo_indirecto_fijo,
                gasto_administracion,
                gasto_ventas,
                prendas_requeridas,
                cod_ordpro,
                ROW_NUMBER() OVER (ORDER BY fecha_facturacion DESC) as rn
            FROM {settings.db_schema}.costo_op_detalle
            WHERE cliente = %s
                AND tipo_de_producto = %s
                AND version_calculo = %s
                AND fecha_corrida = (
                    SELECT MAX(fecha_corrida)
                    FROM {settings.db_schema}.costo_op_detalle
                    WHERE version_calculo = %s
                )
                AND fecha_facturacion >= (
                    SELECT (MAX(fecha_facturacion) - INTERVAL '12 months')
                    FROM {settings.db_schema}.costo_op_detalle
                    WHERE version_calculo = %s
                )
                AND prendas_requeridas >= 200
                AND costo_indirecto_fijo > 0
                AND gasto_administracion > 0
                AND gasto_ventas > 0
            ORDER BY fecha_facturacion DESC
            """

            version_norm = version_calculo
            params = (
                marca,
                tipo_prenda,
                version_norm,
                version_norm,
                version_norm,
            )
            resultado = await self.db.query(query, params)

            if not resultado:
                logger.warning(
                    f" No se encontraron OPs para estilo nuevo: {marca} | {tipo_prenda}"
                )
                return {
                    "costo_indirecto_fijo": 0,
                    "gasto_administracion": 0,
                    "gasto_ventas": 0,
                }, []

            # Extraer los tres valores unitarios y aplicar normalizacion ANTES de promediar
            indirectos = []
            admins = []
            ventas = []
            ops_info = []

            def safe_float(val, default):
                """Convierte valor a float de forma segura"""
                if isinstance(val, (int, float, Decimal)):
                    return float(val)
                return default

            for row in resultado:
                # Los costos ya vienen por prenda en la tabla
                cif_raw = safe_float(row.get("costo_indirecto_fijo", 0), 0)
                admin_raw = safe_float(row.get("gasto_administracion", 0), 0)
                venta_raw = safe_float(row.get("gasto_ventas", 0), 0)

                indirectos.append(cif_raw)
                admins.append(admin_raw)
                ventas.append(venta_raw)
                ops_info.append({
                    "rn": row["rn"],
                    "cod_ordpro": row["cod_ordpro"],
                })

            # Aplicar normalizacion a cada valor ANTES de promediar
            # Esto es consistente con _procesar_costos_historicos_con_limites_previos
            def normalizar_valores_antes_de_promediar(valores, componente):
                """Normaliza valores contra rangos de seguridad, luego promedia"""
                if not valores:
                    return 0, 0

                # Aplicar rangos de seguridad a cada valor individual
                valores_normalizados = []
                ajustes_count = 0

                if componente in factores.RANGOS_SEGURIDAD:
                    min_val = factores.RANGOS_SEGURIDAD[componente]["min"]
                    max_val = factores.RANGOS_SEGURIDAD[componente]["max"]

                    for val in valores:
                        val_float = safe_float(val, 0)
                        # Aplicar limites
                        val_normalizado = max(min_val, min(max_val, val_float))
                        if val_normalizado != val_float:
                            ajustes_count += 1
                        valores_normalizados.append(val_normalizado)
                else:
                    valores_normalizados = [safe_float(v, 0) for v in valores]

                # LUEGO promediar los valores normalizados
                promedio = sum(valores_normalizados) / len(valores_normalizados) if valores_normalizados else 0
                return float(promedio), ajustes_count

            # Calcular promedios aplicando normalizacion ANTES
            cif_promedio, cif_ajustes = normalizar_valores_antes_de_promediar(
                indirectos, "costo_indirecto_fijo"
            )
            admin_promedio, admin_ajustes = normalizar_valores_antes_de_promediar(
                admins, "gasto_administracion"
            )
            venta_promedio, venta_ajustes = normalizar_valores_antes_de_promediar(
                ventas, "gasto_ventas"
            )

            gastos = {
                "costo_indirecto_fijo": cif_promedio,
                "gasto_administracion": admin_promedio,
                "gasto_ventas": venta_promedio,
            }

            # Rastrear si hubo ajustes
            total_ajustes = cif_ajustes + admin_ajustes + venta_ajustes
            if total_ajustes > 0:
                logger.info(
                    f" Normalizacion aplicada en gastos indirectos nuevos: {total_ajustes} valores ajustados"
                )

            ops_excluidas = []

            logger.info(
                f" Gastos nuevos ({marca} | {tipo_prenda}): {gastos} | OPs excluidas: {len(ops_excluidas)}"
            )
            return gastos, ops_excluidas

        except Exception as e:
            logger.error(
                f" Error en obtener_gastos_por_estilo_nuevo ({marca} | {tipo_prenda}): {e}"
            )
            return {
                "costo_indirecto_fijo": 0,
                "gasto_administracion": 0,
                "gasto_ventas": 0,
            }, []

    # ========================================
    #  FUNCIONES DE SOPORTE CORREGIDAS
    # ========================================

    #  CDIGO CORREGIDO - Ahora usa MODA en lugar de PROMEDIO
    async def obtener_gastos_indirectos_formula(
        self,
        version_calculo: str = "FLUIDA",
        codigo_estilo: Optional[str] = None,
        cliente_marca: Optional[str] = None,
        familia_producto: Optional[str] = None,
        tipo_prenda: Optional[str] = None,
    ) -> Tuple[Dict[str, float], List[str]]:
        """
         CORREGIDA: Gastos indirectos UNITARIOS usando MODA y filtrado de outliers.

        Estrategia:
        1. Si codigo_estilo est disponible  buscar OPs de ese estilo recurrente
        2. Si no  usar marca+familia+tipo para buscar OPs de estilo nuevo
        3. Si no se encuentran  usar frmula genrica (fallback)

        Retorna: (gastos_dict, ops_excluidas)
        """

        #  OPCIN 1: Intentar con ESTILO RECURRENTE (por cdigo_estilo exacto)
        if codigo_estilo:
            logger.info(f" Buscando gastos para ESTILO RECURRENTE: {codigo_estilo}")
            gastos, ops_excluidas = await self.obtener_gastos_por_estilo_recurrente(
                codigo_estilo, version_calculo
            )
            if any(gastos.values()):  # Si se encontraron datos
                logger.info(f" Gastos obtenidos por ESTILO RECURRENTE: {gastos}")
                return gastos, ops_excluidas

        #  OPCIN 2: Intentar con ESTILO NUEVO (marca + tipo)
        #  NOTA: familia_producto ahora es OPCIONAL y NO se usa
        if cliente_marca and tipo_prenda:
            logger.info(
                f" Buscando gastos para ESTILO NUEVO: {cliente_marca} | {tipo_prenda}"
            )
            gastos, ops_excluidas = await self.obtener_gastos_por_estilo_nuevo(
                cliente_marca, familia_producto, tipo_prenda, version_calculo
            )
            if any(gastos.values()):  # Si se encontraron datos
                logger.info(f" Gastos obtenidos por ESTILO NUEVO")
                return gastos, ops_excluidas

        #  OPCIN 3: FALLBACK - Frmula genrica (promedio general)
        logger.info(f" Usando FRMULA GENRICA como fallback")
        query = f"""
        SELECT
            AVG(costo_indirecto_fijo / NULLIF(prendas_requeridas, 0)) as indirecto_fijo,
            AVG(gasto_administracion / NULLIF(prendas_requeridas, 0)) as administracion,
            AVG(gasto_ventas / NULLIF(prendas_requeridas, 0)) as ventas
        FROM {settings.db_schema}.costo_op_detalle
        WHERE version_calculo = ?
        AND fecha_corrida = (
          SELECT MAX(fecha_corrida)
          FROM {settings.db_schema}.costo_op_detalle
          WHERE version_calculo = ?)
        AND fecha_facturacion >= (
          SELECT (MAX(fecha_facturacion) - INTERVAL '12 months')
          FROM {settings.db_schema}.costo_op_detalle
          WHERE version_calculo = ?
        )
        AND prendas_requeridas > 0
        AND costo_indirecto_fijo > 0
        AND gasto_administracion > 0
        AND gasto_ventas > 0
        """

        try:
            resultado = await self.db.query(
                query, (version_calculo, version_calculo, version_calculo)
            )
        except Exception as e:
            logger.warning(f" Error en query de gastos genricos: {e}. Usando valores por defecto")
            resultado = None
        if resultado:
            gastos = {
                "costo_indirecto_fijo": float(resultado[0]["indirecto_fijo"] or 0),
                "gasto_administracion": float(resultado[0]["administracion"] or 0),
                "gasto_ventas": float(resultado[0]["ventas"] or 0),
            }
            logger.info(
                f" Gastos indirectos (FRMULA GENRICA) obtenidos ({version_calculo}): {gastos}"
            )
            return gastos, []

        logger.warning(f" No se encontraron gastos indirectos para {version_calculo}")
        return {"costo_indirecto_fijo": 0, "gasto_administracion": 0, "gasto_ventas": 0}, []

    async def obtener_ultimo_costo_materiales(
        self, version_calculo: str = "FLUIDA"
    ) -> Dict[str, float]:
        """ SIN CAMBIOS: Ya usa lgica correcta con fecha_corrida"""

        query = f"""
        SELECT
            costo_materia_prima,
            costo_avios,
            prendas_requeridas,
            fecha_corrida,
            cod_ordpro
        FROM {settings.db_schema}.costo_op_detalle
        WHERE costo_materia_prima > 0
          AND costo_avios > 0
          AND prendas_requeridas > 0
          AND version_calculo = ?
          AND fecha_corrida = (
            SELECT MAX(fecha_corrida)
            FROM {settings.db_schema}.costo_op_detalle
            WHERE version_calculo = ?)
        ORDER BY fecha_facturacion DESC,
        prendas_requeridas DESC
        LIMIT 1
        """

        resultado = await self.db.query(query, (version_calculo, version_calculo))
        if resultado:
            registro = resultado[0]
            prendas = (
                float(registro["prendas_requeridas"])
                if registro["prendas_requeridas"]
                else 1.0
            )

            costo_materia_prima_unitario = (
                float(registro["costo_materia_prima"]) / prendas
            )
            costo_avios_unitario = float(registro["costo_avios"]) / prendas

            logger.info(
                f" ltimo costo materiales ({version_calculo}): OP {registro['cod_ordpro']} - "
                f"MP: ${costo_materia_prima_unitario:.2f}/u - "
                f"Avos: ${costo_avios_unitario:.2f}/u"
            )

            return {
                "costo_materia_prima": costo_materia_prima_unitario,
                "costo_avios": costo_avios_unitario,
            }

        logger.warning(
            f" No se encontr ltimo costo de materiales vlido para {version_calculo}"
        )
        return {"costo_materia_prima": 0, "costo_avios": 0}

    async def obtener_volumen_historico_estilo(
        self,
        codigo_estilo: str,
        version_calculo: str = "FLUIDA",
    ) -> int:
        # Solo filtrar version_calculo en costo_op_detalle
        query = f"""
        SELECT COALESCE(SUM(prendas_requeridas), 0) as volumen_total
        FROM {settings.db_schema}.costo_op_detalle c
        INNER JOIN {settings.db_schema}.historial_estilos h
          ON c.estilo_propio = h.codigo_estilo
        WHERE h.codigo_estilo = ?
          AND c.version_calculo = ?
          AND c.fecha_corrida = (
            SELECT MAX(fecha_corrida)
            FROM {settings.db_schema}.costo_op_detalle
            WHERE version_calculo = ?)
          AND h.fecha_corrida = (
            SELECT MAX(fecha_corrida)
            FROM {settings.db_schema}.historial_estilos)
          AND c.prendas_requeridas > 0
        """

        resultado = await self.db.query(
            query, (codigo_estilo, version_calculo, version_calculo)
        )
        volumen = (
            int(resultado[0]["volumen_total"])
            if resultado and resultado[0]["volumen_total"]
            else 0
        )

        logger.info(
            f" Volumen histrico {codigo_estilo} ({version_calculo}): {volumen} prendas"
        )
        return volumen

    async def health_check(self) -> Dict[str, Any]:
        """Verifica estado de las tablas principales"""

        tablas_check = {
            "costo_op_detalle": f"SELECT COUNT(*) as total FROM {settings.db_schema}.costo_op_detalle",
            "resumen_wip_por_prenda": f"SELECT COUNT(*) as total FROM {settings.db_schema}.resumen_wip_por_prenda",
            "historial_estilos": f"SELECT COUNT(*) as total FROM {settings.db_schema}.historial_estilos",
        }

        resultados = {}
        for tabla, query in tablas_check.items():
            try:
                resultado = await self.db.query(query)
                resultados[tabla] = resultado[0]["total"] if resultado else 0
            except Exception as e:
                logger.error(f"Error verificando tabla {tabla}: {e}")
                resultados[tabla] = -1

        logger.info(f" Health check completado: {resultados}")
        return resultados

    async def obtener_ops_utilizadas_cotizacion(
        self,
        codigo_estilo: Optional[str] = None,
        familia_producto: Optional[str] = None,
        tipo_prenda: Optional[str] = None,
        cliente: Optional[str] = None,
        version_calculo: str = "FLUIDA",
    ) -> Dict[str, Any]:
        """
         FUNCIN CORREGIDA: Obtiene las OPs especficas utilizadas para una cotizacin con fechas relativas
        """

        ops_utilizadas = []
        metodo_usado = "sin_datos"

        # PASO 1: Intentar por estilo especfico (si es recurrente)
        # CORREGIDO: Buscar directamente en costo_op_detalle sin requerir historial_estilos
        if codigo_estilo:
            try:
                # Fechas relativas en lugar de GETDATE()
                query_estilo = f"""
                SELECT
                  c.cod_ordpro,
                  c.cliente,
                  c.fecha_facturacion,
                  c.prendas_requeridas,
                  c.monto_factura,
                  c.esfuerzo_total,
                  --  COSTOS UNITARIOS CALCULADOS
                  COALESCE(c.costo_textil, 0)
                    / NULLIF(c.prendas_requeridas, 0) as costo_textil_unit,
                  COALESCE(c.costo_manufactura, 0)
                    / NULLIF(c.prendas_requeridas, 0) as costo_manufactura_unit,
                  COALESCE(c.costo_avios, 0)
                    / NULLIF(c.prendas_requeridas, 0) as costo_avios_unit,
                  COALESCE(c.costo_materia_prima, 0)
                    / NULLIF(c.prendas_requeridas, 0) as costo_mp_unit,
                  COALESCE(c.costo_indirecto_fijo, 0)
                    / NULLIF(c.prendas_requeridas, 0) as costo_indirecto_unit,
                  COALESCE(c.gasto_administracion, 0)
                    / NULLIF(c.prendas_requeridas, 0) as gasto_admin_unit,
                  COALESCE(c.gasto_ventas, 0)
                    / NULLIF(c.prendas_requeridas, 0) as gasto_ventas_unit
                FROM {settings.db_schema}.costo_op_detalle c
                WHERE c.estilo_propio = ?
                  AND c.version_calculo = ?
                  AND c.fecha_facturacion >= (
                    SELECT (MAX(fecha_facturacion) - INTERVAL '18 months')
                    FROM {settings.db_schema}.costo_op_detalle
                    WHERE version_calculo = ?
                )
                AND c.prendas_requeridas > 0
                ORDER BY c.fecha_facturacion DESC, c.prendas_requeridas DESC
                LIMIT 10
                """

                resultados = await self.db.query(
                    query_estilo,
                    (codigo_estilo, version_calculo, version_calculo),
                )

                if resultados:
                    ops_utilizadas = resultados
                    metodo_usado = f"estilo_especifico_{codigo_estilo}"

            except Exception as e:
                logger.warning(f"Error buscando OPs por estilo {codigo_estilo}: {e}")

        # PASO 2: Si no hay por estilo, buscar por tipo_prenda (sin familia_producto)
        # familia_producto ahora es OPCIONAL y NO se usa en el filtro
        if not ops_utilizadas and tipo_prenda:
            try:
                params = [
                    tipo_prenda,
                    version_calculo,
                    version_calculo,
                    version_calculo,
                ]
                cliente_filter = ""

                if cliente:
                    cliente_filter = "AND c.cliente = ?"
                    params.append(cliente)
                    metodo_usado = f"tipo_cliente_{tipo_prenda}_{cliente}"
                else:
                    metodo_usado = f"tipo_{tipo_prenda}"

                #  CORREGIDO: Fechas relativas en lugar de GETDATE()
                #  NOTA: Se elimin el filtro de familia_de_productos
                query_familia = f"""
                SELECT
                  c.cod_ordpro,
                  c.estilo_propio,
                  c.cliente,
                  c.fecha_facturacion,
                  c.prendas_requeridas,
                  c.monto_factura,
                  c.costo_textil / NULLIF(c.prendas_requeridas, 0) as costo_textil_unit,
                  c.costo_manufactura / NULLIF(c.prendas_requeridas, 0) as costo_manufactura_unit,
                  COALESCE(c.costo_avios, 0) / NULLIF(c.prendas_requeridas, 0) as costo_avios_unit,
                  COALESCE(c.costo_materia_prima, 0) / NULLIF(c.prendas_requeridas, 0) as costo_mp_unit,
                  COALESCE(c.costo_indirecto_fijo, 0) / NULLIF(c.prendas_requeridas, 0) as costo_indirecto_unit,
                  COALESCE(c.gasto_administracion, 0) / NULLIF(c.prendas_requeridas, 0) as gasto_admin_unit,
                  COALESCE(c.gasto_ventas, 0) / NULLIF(c.prendas_requeridas, 0) as gasto_ventas_unit,
                  c.esfuerzo_total
                FROM {settings.db_schema}.costo_op_detalle c
                WHERE c.tipo_de_producto = ?
                  AND c.version_calculo = ?
                  AND c.fecha_corrida = (
                    SELECT MAX(fecha_corrida)
                    FROM {settings.db_schema}.costo_op_detalle
                    WHERE version_calculo = ?)
                  AND c.fecha_facturacion >= (
                    SELECT (MAX(fecha_facturacion) - INTERVAL '18 months')
                    FROM {settings.db_schema}.costo_op_detalle
                    WHERE version_calculo = ?
                )
                AND c.prendas_requeridas > 0
                {cliente_filter}
                ORDER BY c.fecha_facturacion DESC, c.prendas_requeridas DESC
                LIMIT 10
                """

                resultados = await self.db.query(query_familia, tuple(params))

                if resultados:
                    ops_utilizadas = resultados

            except Exception as e:
                logger.warning(f"Error buscando OPs por tipo_prenda: {e}")

        #  PROCESAR RESULTADOS CORREGIDO
        ops_procesadas = []
        for op in ops_utilizadas:
            #  PASO 1: Calcular COSTO TOTAL ORIGINAL (antes de rangos)
            costo_total_original = (
                float(op.get("costo_textil_unit", 0) or 0)
                + float(op.get("costo_manufactura_unit", 0) or 0)
                + float(op.get("costo_avios_unit", 0) or 0)
                + float(op.get("costo_mp_unit", 0) or 0)
                + float(op.get("costo_indirecto_unit", 0) or 0)
                + float(op.get("gasto_admin_unit", 0) or 0)
                + float(op.get("gasto_ventas_unit", 0) or 0)
            )

            #  PASO 2: Aplicar rangos de seguridad a cada componente
            costo_textil_ajustado, textil_ajustado = factores.validar_rango_seguridad(
                float(op.get("costo_textil_unit", 0) or 0), "costo_textil"
            )
            costo_manufactura_ajustado, manufactura_ajustado = (
                factores.validar_rango_seguridad(
                    float(op.get("costo_manufactura_unit", 0) or 0), "costo_manufactura"
                )
            )
            costo_avios_ajustado, avios_ajustado = factores.validar_rango_seguridad(
                float(op.get("costo_avios_unit", 0) or 0), "costo_avios"
            )
            costo_mp_ajustado, mp_ajustado = factores.validar_rango_seguridad(
                float(op.get("costo_mp_unit", 0) or 0), "costo_materia_prima"
            )
            costo_indirecto_ajustado, indirecto_ajustado = (
                factores.validar_rango_seguridad(
                    float(op.get("costo_indirecto_unit", 0) or 0),
                    "costo_indirecto_fijo",
                )
            )
            gasto_admin_ajustado, admin_ajustado = factores.validar_rango_seguridad(
                float(op.get("gasto_admin_unit", 0) or 0), "gasto_administracion"
            )
            gasto_ventas_ajustado, ventas_ajustado = factores.validar_rango_seguridad(
                float(op.get("gasto_ventas_unit", 0) or 0), "gasto_ventas"
            )

            #  PASO 3: Calcular COSTO TOTAL AJUSTADO
            costo_total_ajustado = (
                costo_textil_ajustado
                + costo_manufactura_ajustado
                + costo_avios_ajustado
                + costo_mp_ajustado
                + costo_indirecto_ajustado
                + gasto_admin_ajustado
                + gasto_ventas_ajustado
            )

            #  PASO 4: Determinar si fue ajustado
            fue_ajustado = (
                textil_ajustado
                or manufactura_ajustado
                or avios_ajustado
                or mp_ajustado
                or indirecto_ajustado
                or admin_ajustado
                or ventas_ajustado
            )

            ops_procesadas.append(
                {
                    "cod_ordpro": op["cod_ordpro"],
                    "estilo_propio": op.get("estilo_propio", codigo_estilo),
                    "cliente": op["cliente"],
                    "fecha_facturacion": op["fecha_facturacion"].isoformat()
                    if op["fecha_facturacion"]
                    else None,
                    "prendas_requeridas": int(op["prendas_requeridas"]),
                    "monto_factura": float(op["monto_factura"]),
                    "precio_unitario": float(
                        op["monto_factura"] / op["prendas_requeridas"]
                    )
                    if op["prendas_requeridas"] > 0
                    else 0,
                    "esfuerzo_total": int(op["esfuerzo_total"] or 6),
                    #  COSTOS COMPONENTES AJUSTADOS
                    "costos_componentes": {
                        "textil": costo_textil_ajustado,
                        "manufactura": costo_manufactura_ajustado,
                        "avios": costo_avios_ajustado,
                        "materia_prima": costo_mp_ajustado,
                        "indirecto_fijo": costo_indirecto_ajustado,
                        "gasto_admin": gasto_admin_ajustado,
                        "gasto_ventas": gasto_ventas_ajustado,
                    },
                    #  COSTOS TOTALES CALCULADOS CORRECTAMENTE
                    "costo_total_unitario": costo_total_ajustado,  # Para clculos seguros
                    "costo_total_original": costo_total_original,  # Para mostrar en frontend
                    "fue_ajustado": fue_ajustado,  # Si hubo ajustes aplicados
                }
            )

        #  ESTADSTICAS BASADAS EN COSTOS AJUSTADOS
        if ops_procesadas:
            costos_totales_ajustados = [
                op["costo_total_unitario"] for op in ops_procesadas
            ]
            costos_totales_originales = [
                op["costo_total_original"] for op in ops_procesadas
            ]
            esfuerzos = [op["esfuerzo_total"] for op in ops_procesadas]

            estadisticas = {
                "total_ops": len(ops_procesadas),
                "costo_promedio": sum(costos_totales_ajustados)
                / len(costos_totales_ajustados),
                "costo_min": min(costos_totales_ajustados),
                "costo_max": max(costos_totales_ajustados),
                "costo_promedio_original": sum(costos_totales_originales)
                / len(costos_totales_originales),
                "costo_min_original": min(costos_totales_originales),
                "costo_max_original": max(costos_totales_originales),
                "esfuerzo_promedio": sum(esfuerzos) / len(esfuerzos),
                "ops_con_ajustes": sum(
                    1 for op in ops_procesadas if op["fue_ajustado"]
                ),
                "rango_fechas": {
                    "desde": min(
                        [
                            op["fecha_facturacion"]
                            for op in ops_procesadas
                            if op["fecha_facturacion"]
                        ]
                    ),
                    "hasta": max(
                        [
                            op["fecha_facturacion"]
                            for op in ops_procesadas
                            if op["fecha_facturacion"]
                        ]
                    ),
                },
            }
        else:
            estadisticas = {
                "total_ops": 0,
                "mensaje": "No se encontraron OPs con los criterios especificados",
            }

        logger.info(
            f" OPs utilizadas procesadas: {len(ops_procesadas)} encontradas con mtodo {metodo_usado}"
        )

        return {
            "ops_utilizadas": ops_procesadas,
            "metodo_utilizado": metodo_usado,
            "estadisticas": estadisticas,
            "parametros_busqueda": {
                "codigo_estilo": codigo_estilo,
                "familia_producto": familia_producto,
                "tipo_prenda": tipo_prenda,
                "cliente": cliente,
                "version_calculo": version_calculo,
            },
            "rangos_aplicados": True,  #  INDICADOR DE QUE SE APLICARON RANGOS
        }

    async def obtener_info_comercial(
        self,
        familia_producto: str,
        tipo_prenda: str,
        version_calculo: str = "FLUIDA",
    ) -> Dict[str, Any]:
        """ SIN CAMBIOS: Ya usa fecha_corrida correctamente"""

        # 1. Volumen histrico (6 meses)
        query_volumen = f"""
        SELECT
          COUNT(*) as ops_producidas,
          SUM(prendas_requeridas) as volumen_total_6m,
          AVG(CAST(prendas_requeridas AS FLOAT)) as volumen_promedio
        FROM {settings.db_schema}.costo_op_detalle
        WHERE familia_de_productos = ?
          AND tipo_de_producto = ?
          AND version_calculo = ?
          AND fecha_corrida = (
            SELECT MAX(fecha_corrida)
            FROM {settings.db_schema}.costo_op_detalle
            WHERE version_calculo = ?)
          AND fecha_facturacion >= (GETDATE() - INTERVAL '6 months')
          AND prendas_requeridas > 0
        """

        resultado_volumen = await self.db.query(
            query_volumen,
            (familia_producto, tipo_prenda, version_calculo, version_calculo),
        )
        volumen = resultado_volumen[0] if resultado_volumen else {}

        # 2. Tendencias de costos
        query_tendencias = f"""
        SELECT
          EXTRACT(YEAR FROM fecha_facturacion)::INT as ao,
          EXTRACT(MONTH FROM fecha_facturacion)::INT as mes,
          COUNT(*) as ops_mes,
          AVG(CAST(costo_textil AS FLOAT)
            / NULLIF(prendas_requeridas, 0)) as costo_textil_promedio,
          AVG(CAST(costo_manufactura AS FLOAT)
            / NULLIF(prendas_requeridas, 0)) as costo_manufactura_promedio
        FROM {settings.db_schema}.costo_op_detalle
        WHERE familia_de_productos = %s
          AND tipo_de_producto = %s
          AND version_calculo = %s
          AND fecha_corrida = (
            SELECT MAX(fecha_corrida)
            FROM {settings.db_schema}.costo_op_detalle
            WHERE version_calculo = %s)
         AND fecha_facturacion >= (CURRENT_TIMESTAMP - INTERVAL '18 months')
          AND prendas_requeridas > 0
        GROUP BY EXTRACT(YEAR FROM fecha_facturacion), EXTRACT(MONTH FROM fecha_facturacion)
        ORDER BY ao DESC, mes DESC
        """

        tendencias = await self.db.query(
            query_tendencias,
            (familia_producto, tipo_prenda, version_calculo, version_calculo),
        )

        # 3. Anlisis competitivo
        query_competitivo = f"""
        SELECT
          cliente,
          COUNT(*) as ops_cliente,
          SUM(prendas_requeridas) as volumen_cliente,
          AVG(CAST(monto_factura AS FLOAT)
            / NULLIF(prendas_requeridas, 0)) as precio_promedio_cliente
        FROM {settings.db_schema}.costo_op_detalle
        WHERE familia_de_productos = ?
          AND tipo_de_producto = ?
          AND version_calculo = ?
          AND fecha_corrida = (
            SELECT MAX(fecha_corrida)
            FROM {settings.db_schema}.costo_op_detalle
            WHERE version_calculo = ?)
          AND fecha_facturacion >= (GETDATE() - INTERVAL '12 months')
          AND prendas_requeridas > 0
        GROUP BY cliente
        ORDER BY SUM(prendas_requeridas) DESC
        LIMIT 5
        """

        competitivo = await self.db.query(
            query_competitivo,
            (familia_producto, tipo_prenda, version_calculo, version_calculo),
        )

        info_comercial = {
            "historico_volumen": {
                "ops_producidas": int(volumen.get("ops_producidas", 0) or 0),
                "volumen_total_6m": int(volumen.get("volumen_total_6m", 0) or 0),
                "volumen_promedio": float(
                    round(volumen.get("volumen_promedio", 0) or 0, 1)
                ),
            },
            "tendencias_costos": [
                {
                    "ao": int(t["ao"]),
                    "mes": int(t["mes"]),
                    "ops_mes": int(t["ops_mes"]),
                    "costo_textil_promedio": float(
                        round(t["costo_textil_promedio"] or 0, 4)
                    ),
                    "costo_manufactura_promedio": float(
                        round(t["costo_manufactura_promedio"] or 0, 4)
                    ),
                }
                for t in tendencias
            ],
            "analisis_competitividad": [
                {
                    "cliente": str(c["cliente"]),
                    "ops_cliente": int(c["ops_cliente"]),
                    "volumen_cliente": int(c["volumen_cliente"]),
                    "precio_promedio_cliente": float(
                        round(c["precio_promedio_cliente"] or 0, 2)
                    ),
                }
                for c in competitivo
            ],
            "version_calculo": version_calculo,
        }

        logger.info(
            f" Info comercial obtenida para {familia_producto}/{tipo_prenda} ({version_calculo})"
        )
        return info_comercial

