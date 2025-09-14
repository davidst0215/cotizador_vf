"""
=====================================================================
APLICACIÓN FASTAPI PRINCIPAL - BACKEND TDV COTIZADOR - COMPLETAMENTE CORREGIDO
=====================================================================
✅ Nuevos endpoints agregados:
- /verificar-estilo-completo/{codigo_estilo} - Auto-completado completo
- /ops-utilizadas-cotizacion - OPs reales utilizadas
✅ Todos los endpoints corregidos con version_calculo
✅ Manejo mejorado de errores y logging
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse as FastAPIJSONResponse
from typing import List, Optional
from datetime import datetime
import logging
import json
import pyodbc
from decimal import Decimal

# Imports locales
from .config import settings, factores
from .models import (
    CotizacionInput,
    CotizacionResponse,
    EstiloSimilar,
    HealthCheck,
    ConfiguracionResponse,
    WipsDisponiblesResponse,
    VersionCalculo,
)
from .database import TDVQueries
from .utils import cotizador_tdv

logger = logging.getLogger(__name__)
tdv_queries: TDVQueries = TDVQueries.get_instance()


# SERIALIZADOR JSON PERSONALIZADO
class JSONEncoder(json.JSONEncoder):
    """Encoder JSON personalizado para manejar datetime y Decimal"""

    def default(self, obj):
        if isinstance(obj, datetime):
            return obj.isoformat()
        elif isinstance(obj, Decimal):
            return float(obj)
        return super().default(obj)


# RESPUESTA JSON PERSONALIZADA
class CustomJSONResponse(FastAPIJSONResponse):
    """JSONResponse personalizada que maneja datetime y Decimal"""

    def render(self, content) -> bytes:
        return json.dumps(
            content,
            ensure_ascii=False,
            allow_nan=False,
            indent=None,
            separators=(",", ":"),
            cls=JSONEncoder,
        ).encode("utf-8")


# =====================================================================
# CONFIGURACIÓN FASTAPI
# =====================================================================

app = FastAPI(
    title=settings.api_title,
    version=settings.api_version,
    description="Sistema de cotización inteligente basado en metodología WIP para TDV - COMPLETAMENTE CORREGIDO",
    docs_url="/docs",
    redoc_url="/redoc",
)

# Configurar CORS
origins = settings.cors_origins.split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# =====================================================================
# MANEJADORES DE ERRORES CORREGIDOS
# =====================================================================


@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    """Manejador de excepciones HTTP corregido"""
    error_response = {
        "error": "HTTP_ERROR",
        "mensaje": exc.detail,
        "detalles": {"status_code": exc.status_code},
        "timestamp": datetime.now().isoformat(),
    }
    return CustomJSONResponse(status_code=exc.status_code, content=error_response)


@app.exception_handler(ValueError)
async def value_error_handler(request, exc):
    """Manejador de errores de valor corregido"""
    error_response = {
        "error": "VALUE_ERROR",
        "mensaje": str(exc),
        "detalles": {"tipo": "ValueError"},
        "timestamp": datetime.now().isoformat(),
    }
    return CustomJSONResponse(status_code=400, content=error_response)


@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    """Manejador general de excepciones corregido"""
    logger.error(f"Error no manejado: {exc}")
    error_response = {
        "error": "INTERNAL_ERROR",
        "mensaje": "Error interno del servidor",
        "detalles": {"tipo": type(exc).__name__},
        "timestamp": datetime.now().isoformat(),
    }
    return CustomJSONResponse(status_code=500, content=error_response)


# =====================================================================
# ENDPOINTS PRINCIPALES
# =====================================================================


@app.get("/", tags=["General"])
async def root():
    """Endpoint raíz con información del sistema"""
    return {
        "sistema": "Cotizador TDV Expert",
        "version": settings.api_version,
        "status": "activo",
        "arquitectura": "TDV Real Database",
        "features": [
            "✅ CORREGIDO: Búsqueda mejorada en costo_op_detalle",
            "✅ CORREGIDO: Configurador WIPs desde resumen_wip_por_prenda",
            "✅ CORREGIDO: Categorización automática de estilos",
            "✅ NUEVO: Auto-completado inteligente para estilos recurrentes",
            "✅ NUEVO: Endpoint OPs reales utilizadas",
            "✅ CORREGIDO: Manejo completo de versiones de cálculo",
            "✅ CORREGIDO: Rutas textiles restauradas",
            "Factores de ajuste basados en análisis TDV",
            "Información comercial avanzada",
            "Análisis inteligente WIPs por estabilidad + fecha_corrida",
        ],
        "versiones_calculo_soportadas": ["FLUIDA", "truncado"],
        "endpoints_nuevos": [
            "/verificar-estilo-completo/{codigo_estilo}",
            "/ops-utilizadas-cotizacion",
        ],
        "timestamp": datetime.now(),
    }


@app.get("/health", response_model=HealthCheck, tags=["General"])
async def health_check():
    """Verificación de estado del sistema y BD"""
    try:
        tablas_status = await tdv_queries.health_check()

        estado_general = (
            "healthy"
            if all(count >= 0 for count in tablas_status.values())
            else "degraded"
        )
        estado_bd = (
            "connected"
            if all(count >= 0 for count in tablas_status.values())
            else "error"
        )

        return HealthCheck(
            status=estado_general,
            database=estado_bd,
            tablas=tablas_status,
            timestamp=datetime.now(),
        )

    except Exception as e:
        logger.error(f"Error en health check: {e}")
        raise HTTPException(status_code=503, detail=f"Sistema no disponible: {str(e)}")


# =====================================================================
# 🆕 NUEVOS ENDPOINTS CRÍTICOS
# =====================================================================


@app.get("/verificar-estilo-completo/{codigo_estilo}", tags=["Búsqueda"])
async def verificar_estilo_completo_con_autocompletado(
    codigo_estilo: str,
    version_calculo: Optional[VersionCalculo] = VersionCalculo.FLUIDA,
):
    """
    ✅ NUEVO ENDPOINT: Verificación completa de estilo con auto-completado

    Este endpoint proporciona:
    1. Verificación si es nuevo/recurrente
    2. Auto-completado de familia_producto y tipo_prenda
    3. Información detallada del estilo
    4. Volumen histórico y categorización
    """
    try:
        # PASO 1: Verificación básica
        existe = await tdv_queries.verificar_estilo_existente(
            codigo_estilo, version_calculo
        )
        es_nuevo = not existe

        # PASO 2: Información detallada si existe
        info_detallada = None
        autocompletado_disponible = False
        campos_sugeridos = {}

        if not es_nuevo:
            try:
                info_detallada = await tdv_queries.obtener_info_detallada_estilo(
                    codigo_estilo, version_calculo
                )

                if info_detallada.get("encontrado", False):
                    autocompletado_disponible = True
                    campos_sugeridos = {
                        "familia_producto": info_detallada.get("familia_producto"),
                        "tipo_prenda": info_detallada.get("tipo_prenda"),
                    }

                    logger.info(
                        f"✅ Auto-completado disponible para {codigo_estilo}: {campos_sugeridos}"
                    )

            except Exception as e:
                logger.warning(
                    f"⚠️ Error obteniendo info detallada para {codigo_estilo}: {e}"
                )
                info_detallada = None

        # PASO 3: Volumen y categorización
        volumen_historico = 0
        categoria = "Nuevo"

        if not es_nuevo and info_detallada and info_detallada.get("encontrado"):
            volumen_historico = info_detallada.get("volumen_total", 0)
            categoria = info_detallada.get("categoria", "Recurrente")
        elif not es_nuevo:
            # Fallback: obtener volumen directamente
            try:
                volumen_historico = await tdv_queries.obtener_volumen_historico_estilo(
                    codigo_estilo, version_calculo
                )
                categoria = (
                    "Muy Recurrente"
                    if volumen_historico >= 4000
                    else "Recurrente"
                    if volumen_historico > 0
                    else "Nuevo"
                )
            except pyodbc.Error:
                volumen_historico = 0
                categoria = "Nuevo"

        # PASO 4: Respuesta estructurada
        respuesta = {
            "codigo_estilo": codigo_estilo,
            "existe_en_bd": existe,
            "es_estilo_nuevo": es_nuevo,
            "categoria": categoria,
            "volumen_historico": volumen_historico,
            "version_calculo": version_calculo,
            "autocompletado": {
                "disponible": autocompletado_disponible,
                "familia_producto": campos_sugeridos.get("familia_producto"),
                "tipo_prenda": campos_sugeridos.get("tipo_prenda"),
            },
            "info_detallada": info_detallada,
            "timestamp": datetime.now().isoformat(),
        }

        logger.info(
            f"✅ Verificación completa {codigo_estilo}: existe={existe}, auto-completado={autocompletado_disponible}"
        )
        return respuesta

    except Exception as e:
        logger.error(f"❌ Error en verificación completa {codigo_estilo}: {e}")
        raise HTTPException(
            status_code=500, detail=f"Error verificando estilo: {str(e)}"
        )


@app.post("/ops-utilizadas-cotizacion", tags=["Análisis"])
async def obtener_ops_utilizadas_cotizacion(input_data: CotizacionInput):
    """
    ✅ NUEVO ENDPOINT: Obtiene las OPs reales utilizadas para una cotización

    Retorna las órdenes de producción específicas que se usaron como base
    para calcular los costos de la cotización.
    """
    try:
        logger.info(
            f"🔍 Obteniendo OPs utilizadas para: {input_data.codigo_estilo} ({input_data.version_calculo})"
        )

        # Obtener OPs utilizadas desde database
        ops_data = await tdv_queries.obtener_ops_utilizadas_cotizacion(
            codigo_estilo=input_data.codigo_estilo
            if input_data.codigo_estilo
            else None,
            familia_producto=input_data.familia_producto,
            tipo_prenda=input_data.tipo_prenda,
            cliente=input_data.cliente_marca,
            version_calculo=input_data.version_calculo,
        )

        # Estructura de respuesta
        respuesta = {
            "ops_data": ops_data,
            "timestamp": datetime.now().isoformat(),
            "total_ops_encontradas": len(ops_data.get("ops_utilizadas", [])),
            "parametros_entrada": {
                "codigo_estilo": input_data.codigo_estilo,
                "familia_producto": input_data.familia_producto,
                "tipo_prenda": input_data.tipo_prenda,
                "cliente": input_data.cliente_marca,
                "version_calculo": input_data.version_calculo,
            },
        }

        logger.info(
            f"✅ OPs encontradas: {respuesta['total_ops_encontradas']} para {input_data.codigo_estilo}"
        )
        return respuesta

    except Exception as e:
        logger.error(f"❌ Error obteniendo OPs utilizadas: {e}")
        raise HTTPException(status_code=500, detail=f"Error obteniendo OPs: {str(e)}")


# =====================================================================
# ENDPOINTS DE CONFIGURACIÓN - CORREGIDOS CON VERSION_CALCULO
# =====================================================================


@app.get("/configuracion", response_model=ConfiguracionResponse, tags=["Configuración"])
async def obtener_configuracion():
    """Obtiene configuración completa del sistema"""
    return ConfiguracionResponse(
        rangos_lote=factores.RANGOS_LOTE,
        factores_esfuerzo=factores.FACTORES_ESFUERZO,
        factores_estilo=factores.FACTORES_ESTILO,
        factores_marca=factores.FACTORES_MARCA,
        wips_disponibles={
            "textiles": factores.WIPS_TEXTILES,
            "manufactura": factores.WIPS_MANUFACTURA,
        },
        rangos_seguridad=factores.RANGOS_SEGURIDAD,
    )


@app.get(
    "/wips-disponibles", response_model=WipsDisponiblesResponse, tags=["Configuración"]
)
async def obtener_wips_disponibles(
    tipo_prenda: Optional[str] = None,
    version_calculo: Optional[VersionCalculo] = VersionCalculo.FLUIDA,
):
    """✅ CORREGIDO: Obtiene WIPs disponibles con costos actuales - ANÁLISIS INTELIGENTE CON VERSION_CALCULO"""
    try:
        logger.info(
            f"🔍 Obteniendo WIPs disponibles: tipo_prenda={tipo_prenda}, version={version_calculo}"
        )

        (
            wips_textiles,
            wips_manufactura,
        ) = await tdv_queries.obtener_wips_disponibles_estructurado(
            tipo_prenda, version_calculo
        )

        metodo_usado = "analisis_inteligente_variacion" if tipo_prenda else "generico"

        respuesta = WipsDisponiblesResponse(
            wips_textiles=wips_textiles,
            wips_manufactura=wips_manufactura,
            total_disponibles=len(
                [w for w in wips_textiles + wips_manufactura if w.disponible]
            ),
            fuente="resumen_wip_por_prenda",
            fecha_actualizacion=datetime.now(),
            metodo_analisis=metodo_usado,
            tipo_prenda_filtro=tipo_prenda,
            version_calculo=version_calculo,
        )

        logger.info(
            f"✅ WIPs obtenidas: {respuesta.total_disponibles} disponibles para {tipo_prenda or 'genérico'} ({version_calculo})"
        )
        return respuesta

    except Exception as e:
        logger.error(f"❌ Error obteniendo WIPs: {e}")
        raise HTTPException(status_code=500, detail=f"Error obteniendo WIPs: {str(e)}")


@app.get("/ruta-textil-recomendada/{tipo_prenda}", tags=["Configuración"])
async def obtener_ruta_textil_recomendada(
    tipo_prenda: str,
    version_calculo: Optional[VersionCalculo] = VersionCalculo.FLUIDA,
):
    """✅ CORREGIDO: Obtiene ruta textil recomendada para un tipo de prenda específico"""
    try:
        logger.info(
            f"🧵 Obteniendo ruta textil para: {tipo_prenda} ({version_calculo})"
        )

        ruta_textil = await tdv_queries.obtener_ruta_textil_recomendada(
            tipo_prenda, version_calculo
        )

        # Enriquecer respuesta con version_calculo
        if isinstance(ruta_textil, dict):
            ruta_textil["version_calculo"] = version_calculo
            ruta_textil["timestamp"] = datetime.now().isoformat()
        else:
            # Si es una lista, crear respuesta estructurada
            ruta_textil = {
                "ruta_textil": ruta_textil,
                "tipo_prenda": tipo_prenda,
                "version_calculo": version_calculo,
                "timestamp": datetime.now().isoformat(),
            }

        logger.info(
            f"✅ Ruta textil obtenida: {len(ruta_textil.get('wips_recomendadas', []))} WIPs recomendadas"
        )
        return ruta_textil

    except Exception as e:
        logger.error(f"❌ Error obteniendo ruta textil para {tipo_prenda}: {e}")
        raise HTTPException(
            status_code=500, detail=f"Error obteniendo ruta textil: {str(e)}"
        )


# =====================================================================
# ENDPOINTS DE DATOS MAESTROS - CORREGIDOS CON VERSION_CALCULO
# =====================================================================


@app.get("/clientes", tags=["Datos Maestros"])
async def obtener_clientes(
    version_calculo: Optional[VersionCalculo] = VersionCalculo.FLUIDA,
):
    """✅ CORREGIDO: Obtiene lista de clientes disponibles CON VERSION_CALCULO"""
    try:
        logger.info(f"👥 Cargando clientes para versión: {version_calculo}")

        clientes = await tdv_queries.obtener_clientes_disponibles(version_calculo)

        respuesta = {
            "clientes": clientes,
            "total": len(clientes),
            "fuente": "costo_op_detalle",
            "version_calculo": version_calculo,
            "timestamp": datetime.now().isoformat(),
        }

        logger.info(f"✅ Clientes cargados: {len(clientes)} para {version_calculo}")
        return respuesta

    except Exception as e:
        logger.error(f"❌ Error obteniendo clientes: {e}")
        raise HTTPException(
            status_code=500, detail=f"Error obteniendo clientes: {str(e)}"
        )


@app.get("/familias-productos", tags=["Datos Maestros"])
async def obtener_familias_productos(
    version_calculo: Optional[VersionCalculo] = VersionCalculo.FLUIDA,
):
    """Obtiene familias de productos disponibles CON VERSION_CALCULO"""
    try:
        logger.info(f"📁 Cargando familias para versión: {version_calculo}")

        familias = await tdv_queries.obtener_familias_productos(version_calculo)

        respuesta = {
            "familias": familias,
            "total": len(familias),
            "fuente": "costo_op_detalle",
            "version_calculo": version_calculo,
            "timestamp": datetime.now().isoformat(),
        }

        logger.info(f"✅ Familias cargadas: {len(familias)} para {version_calculo}")
        return respuesta

    except Exception as e:
        logger.error(f"❌ Error obteniendo familias: {e}")
        raise HTTPException(
            status_code=500, detail=f"Error obteniendo familias: {str(e)}"
        )


@app.get("/tipos-prenda/{familia}", tags=["Datos Maestros"])
async def obtener_tipos_prenda(
    familia: str, version_calculo: Optional[VersionCalculo] = VersionCalculo.FLUIDA
):
    """✅ CORREGIDO: Obtiene tipos de prenda para una familia específica CON VERSION_CALCULO"""
    try:
        logger.info(f"🏷️ Cargando tipos para familia: {familia} ({version_calculo})")

        tipos = await tdv_queries.obtener_tipos_prenda(familia, version_calculo)

        respuesta = {
            "tipos": tipos,
            "familia": familia,
            "total": len(tipos),
            "fuente": "costo_op_detalle",
            "version_calculo": version_calculo,
            "timestamp": datetime.now().isoformat(),
        }

        logger.info(
            f"✅ Tipos cargados: {len(tipos)} para {familia} ({version_calculo})"
        )
        return respuesta

    except Exception as e:
        logger.error(f"❌ Error obteniendo tipos de prenda: {e}")
        raise HTTPException(status_code=500, detail=f"Error obteniendo tipos: {str(e)}")


# =====================================================================
# ENDPOINTS DE BÚSQUEDA - CORREGIDOS CON VERSION_CALCULO
# =====================================================================


@app.get(
    "/buscar-estilos/{codigo_estilo}",
    response_model=List[EstiloSimilar],
    tags=["Búsqueda"],
)
async def buscar_estilos_similares(
    codigo_estilo: str,
    cliente: Optional[str] = None,
    limite: Optional[int] = 10,
    version_calculo: Optional[VersionCalculo] = VersionCalculo.FLUIDA,
):
    """✅ CORREGIDO: Busca estilos similares por código y cliente CON VERSION_CALCULO"""
    try:
        if len(codigo_estilo) < 3:
            return []

        logger.info(
            f"🔍 Buscando estilos similares: {codigo_estilo} para {cliente or 'cualquier cliente'} ({version_calculo})"
        )

        estilos = await tdv_queries.buscar_estilos_similares(
            codigo_estilo, cliente or "", limite, version_calculo
        )

        logger.info(
            f"✅ Estilos similares encontrados: {len(estilos)} para {codigo_estilo} ({version_calculo})"
        )
        return estilos

    except Exception as e:
        logger.error(f"❌ Error buscando estilos: {e}")
        raise HTTPException(status_code=500, detail=f"Error en búsqueda: {str(e)}")


@app.get("/verificar-estilo/{codigo_estilo}", tags=["Búsqueda"])
async def verificar_estilo_existente(
    codigo_estilo: str,
    version_calculo: Optional[VersionCalculo] = VersionCalculo.FLUIDA,
):
    """✅ MANTENIDO: Verificación básica de estilo (compatibilidad)"""
    try:
        existe = await tdv_queries.verificar_estilo_existente(
            codigo_estilo, version_calculo
        )
        es_nuevo = not existe

        # Determinar categoría específica si es recurrente
        categoria = "Nuevo"
        volumen_historico = 0

        if not es_nuevo:
            try:
                volumen_total = await tdv_queries.obtener_volumen_historico_estilo(
                    codigo_estilo, version_calculo
                )
                volumen_historico = volumen_total

                if volumen_total >= 4000:
                    categoria = "Muy Recurrente"
                elif volumen_total > 0:
                    categoria = "Recurrente"
                else:
                    categoria = "Nuevo"
            except pyodbc.Error:
                categoria = "Recurrente"  # Fallback si no se puede obtener volumen

        logger.info(
            f"✅ Verificación básica {codigo_estilo}: existe={existe}, categoría={categoria}, volumen={volumen_historico}"
        )

        return {
            "codigo_estilo": codigo_estilo,
            "existe_en_bd": existe,
            "es_estilo_nuevo": es_nuevo,
            "categoria": categoria,
            "volumen_historico": volumen_historico,
            "version_calculo": version_calculo,
        }

    except Exception as e:
        logger.error(f"❌ Error verificando estilo: {e}")
        raise HTTPException(
            status_code=500, detail=f"Error verificando estilo: {str(e)}"
        )


# =====================================================================
# ENDPOINT PRINCIPAL DE COTIZACIÓN - YA MANEJA VERSION_CALCULO VIA INPUT_DATA
# =====================================================================


@app.post("/cotizar", response_model=CotizacionResponse, tags=["Cotización"])
async def crear_cotizacion(input_data: CotizacionInput):
    """✅ CORREGIDO: Endpoint principal para crear cotizaciones - CON SOPORTE COMPLETO VERSION_CALCULO"""
    try:
        logger.info(
            f"💰 Nueva cotización: {input_data.usuario} | {input_data.codigo_estilo} | Versión: {input_data.version_calculo}"
        )

        # Validar version_calculo
        if hasattr(input_data, "version_calculo") and input_data.version_calculo:
            versiones_validas = ["FLUIDA", "truncado"]
            if input_data.version_calculo not in versiones_validas:
                raise ValueError(
                    f"version_calculo debe ser una de: {versiones_validas}"
                )
        else:
            # Asignar default si no viene en input
            input_data.version_calculo = VersionCalculo.FLUIDA

        # Procesar cotización
        resultado = await cotizador_tdv.procesar_cotizacion(input_data)

        logger.info(
            f"✅ Cotización completada: {resultado.id_cotizacion} | ${resultado.precio_final:.2f} | Versión: {resultado.version_calculo_usada}"
        )
        return resultado

    except ValueError as e:
        logger.warning(f"⚠️ Error de validación: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"❌ Error procesando cotización: {e}")
        raise HTTPException(status_code=500, detail=f"Error interno: {str(e)}")


# =====================================================================
# ENDPOINTS DE ANÁLISIS - CORREGIDOS CON VERSION_CALCULO
# =====================================================================


@app.get("/analisis-historico", tags=["Análisis"])
async def obtener_analisis_historico(
    familia: str,
    tipo: Optional[str] = None,
    meses: Optional[int] = 12,
    version_calculo: Optional[VersionCalculo] = VersionCalculo.FLUIDA,
):
    """✅ CORREGIDO: Análisis histórico para benchmarking CON VERSION_CALCULO"""
    try:
        logger.info(f"📊 Análisis histórico: {familia}/{tipo} ({version_calculo})")

        # Query base actualizada CON VERSION_CALCULO
        base_params = [familia, version_calculo, meses]
        base_query = f"""
        SELECT
            COUNT(*) as total_ops,
            SUM(prendas_requeridas) as total_prendas,
            AVG(monto_factura / NULLIF(prendas_requeridas, 0)) as precio_promedio,
            AVG((costo_textil + costo_manufactura + costo_avios
                 + costo_materia_prima + costo_indirecto_fijo
                 + gasto_administracion + gasto_ventas)
                 / NULLIF(prendas_requeridas, 0)) as costo_promedio,
            AVG(CAST(esfuerzo_total AS FLOAT)) as esfuerzo_promedio,
            COUNT(DISTINCT cliente) as clientes_unicos
        FROM {settings.db_schema}.costo_op_detalle
        WHERE familia_de_productos = ?
          AND version_calculo = ?
          AND fecha_corrida >= DATEADD(month, -?,
              (SELECT MAX(fecha_corrida)
               FROM {settings.db_schema}.costo_op_detalle
               WHERE version_calculo = ?))
          AND prendas_requeridas > 0
        """
        base_params.append(version_calculo)  # Para el subquery

        if tipo:
            base_query += " AND tipo_de_producto = ?"
            base_params.append(tipo)

        resultado = await tdv_queries.db.query(base_query, tuple(base_params))

        respuesta = {
            "analisis": resultado[0] if resultado else {},
            "parametros": {
                "familia": familia,
                "tipo": tipo,
                "meses": meses,
                "version_calculo": version_calculo,
            },
            "fuente": "costo_op_detalle",
            "metodo": "fecha_corrida_maxima_con_version_calculo",
            "timestamp": datetime.now().isoformat(),
        }

        logger.info(
            f"✅ Análisis histórico completado para {familia}/{tipo} ({version_calculo})"
        )
        return respuesta

    except Exception as e:
        logger.error(f"❌ Error en análisis histórico: {e}")
        raise HTTPException(status_code=500, detail=f"Error en análisis: {str(e)}")


# =====================================================================
# ENDPOINTS DE UTILIDAD - MANTENER ORIGINALES
# =====================================================================


@app.get("/categoria-lote/{cantidad}", tags=["Utilidades"])
async def categorizar_lote_por_cantidad(cantidad: int):
    """Categoriza un lote basándose en cantidad de prendas"""
    try:
        categoria, factor = factores.categorizar_lote(cantidad)
        return {
            "cantidad_prendas": cantidad,
            "categoria": categoria,
            "factor": factor,
            "rango": factores.RANGOS_LOTE[categoria],
        }
    except Exception as e:
        logger.error(f"Error categorizando lote: {e}")
        raise HTTPException(status_code=500, detail=f"Error categorizando: {str(e)}")


@app.get("/factor-marca/{cliente}", tags=["Utilidades"])
async def obtener_factor_marca(cliente: str):
    """Obtiene factor de marca para un cliente específico"""
    try:
        factor = factores.obtener_factor_marca(cliente)
        return {
            "cliente": cliente,
            "factor_marca": factor,
            "estrategia": "Aumentar Margen"
            if factor > 1.0
            else "Mantener Volumen"
            if factor == 1.0
            else "Reducir Margen",
        }
    except Exception as e:
        logger.error(f"Error obteniendo factor marca: {e}")
        raise HTTPException(
            status_code=500, detail=f"Error obteniendo factor: {str(e)}"
        )


# =====================================================================
# ENDPOINTS DE INFORMACIÓN SISTEMA
# =====================================================================


@app.get("/info-fechas-corrida", tags=["Análisis"])
async def obtener_info_fechas_corrida(
    version_calculo: Optional[VersionCalculo] = VersionCalculo.FLUIDA,
):
    """✅ CORREGIDO: Obtiene información sobre las fechas de corrida CON VERSION_CALCULO"""
    try:
        logger.info(f"📅 Obteniendo fechas corrida para versión: {version_calculo}")

        info_fechas = {}
        tablas = ["costo_op_detalle", "resumen_wip_por_prenda", "historial_estilos"]

        for tabla in tablas:
            try:
                fecha_max = await tdv_queries.obtener_fecha_maxima_corrida(
                    tabla, version_calculo
                )
                info_fechas[tabla] = {
                    "fecha_maxima_corrida": fecha_max,
                    "dias_antiguedad": (datetime.now() - fecha_max).days
                    if fecha_max
                    else None,
                    "estado": "actualizada"
                    if fecha_max and (datetime.now() - fecha_max).days <= 7
                    else "desactualizada",
                    "version_calculo": version_calculo,
                }
            except Exception as e:
                info_fechas[tabla] = {
                    "error": str(e),
                    "estado": "error",
                    "version_calculo": version_calculo,
                }

        respuesta = {
            "fechas_corrida": info_fechas,
            "timestamp_consulta": datetime.now(),
            "metodo": "fecha_corrida_maxima_por_tabla_con_version",
            "version_calculo": version_calculo,
        }

        logger.info(f"✅ Fechas corrida obtenidas para {version_calculo}")
        return respuesta

    except Exception as e:
        logger.error(f"❌ Error obteniendo info fechas corrida: {e}")
        raise HTTPException(
            status_code=500, detail=f"Error obteniendo fechas: {str(e)}"
        )


@app.get("/verificar-estilo-completo/{codigo_estilo}", tags=["Búsqueda"])
async def verificar_estilo_completo(
    codigo_estilo: str,
    familia_producto: Optional[str] = None,
    tipo_prenda: Optional[str] = None,
    version_calculo: Optional[VersionCalculo] = VersionCalculo.FLUIDA,
):
    """
    ✅ ENDPOINT NUEVO: Verificación completa con auto-completado y ruta
    Este endpoint era referenciado en el frontend pero no existía
    """
    try:
        logger.info(
            f"🔍 Verificación completa para estilo: {codigo_estilo} (versión: {version_calculo})"
        )

        # PASO 1: Verificación básica
        existe = await tdv_queries.verificar_estilo_existente(
            codigo_estilo, version_calculo
        )
        es_nuevo = not existe

        logger.info(
            f"🔍 Resultado verificación básica - existe: {existe}, es_nuevo: {es_nuevo}"
        )

        # PASO 2: Información detallada si existe
        info_detallada = await tdv_queries.obtener_info_detallada_estilo(
            codigo_estilo, version_calculo
        )

        # PASO 3: Determinar categoría y auto-completado
        if info_detallada.get("encontrado", False):
            categoria = info_detallada.get("categoria", "Nuevo")
            volumen_historico = info_detallada.get("volumen_total", 0)
            familia_autocompletada = info_detallada.get("familia_producto")
            tipo_autocompletado = info_detallada.get("tipo_prenda")

            logger.info(
                f"✅ Info detallada encontrada - categoría: {categoria}, volumen: {volumen_historico}"
            )
        else:
            categoria = "Nuevo"
            volumen_historico = 0
            familia_autocompletada = None
            tipo_autocompletado = None

            logger.info(f"⚠️ Info detallada NO encontrada para {codigo_estilo}")

        # PASO 4: Respuesta estructurada
        resultado = {
            "codigo_estilo": codigo_estilo,
            "existe_en_bd": existe,
            "es_estilo_nuevo": es_nuevo,
            "categoria": categoria,
            "volumen_historico": volumen_historico,
            "version_calculo": version_calculo,
            "autocompletado": {
                "disponible": info_detallada.get("encontrado", False),
                "familia_producto": familia_autocompletada,
                "tipo_prenda": tipo_autocompletado,
            },
            "debug_info": {
                "info_detallada_encontrada": info_detallada.get("encontrado", False),
                "fuente": info_detallada.get("fuente", "no_encontrado"),
                "total_ops": info_detallada.get("total_ops", 0),
            },
        }

        # PASO 5: Ruta automática para estilos nuevos (si se proporcionan familia/tipo)
        if es_nuevo and familia_producto and tipo_prenda:
            try:
                ruta_recomendada = await tdv_queries.obtener_ruta_textil_recomendada(
                    tipo_prenda, version_calculo
                )
                (
                    wips_textiles,
                    wips_manufactura,
                ) = await tdv_queries.obtener_wips_disponibles_estructurado(
                    tipo_prenda, version_calculo
                )

                resultado.update(
                    {
                        "ruta_automatica": {
                            "disponible": True,
                            "tipo_prenda": tipo_prenda,
                            "familia_producto": familia_producto,
                            "wips_recomendadas": ruta_recomendada.get(
                                "wips_recomendadas", []
                            )[:5],
                            "wips_textiles_disponibles": [
                                {
                                    "wip_id": w.wip_id,
                                    "nombre": w.nombre,
                                    "costo": w.costo_actual,
                                }
                                for w in wips_textiles
                                if w.disponible
                            ][:3],
                            "wips_manufactura_disponibles": [
                                {
                                    "wip_id": w.wip_id,
                                    "nombre": w.nombre,
                                    "costo": w.costo_actual,
                                }
                                for w in wips_manufactura
                                if w.disponible
                            ][:3],
                        }
                    }
                )

                logger.info(
                    f"✅ Ruta automática agregada para estilo nuevo: {codigo_estilo}"
                )

            except Exception as e:
                logger.warning(f"⚠️ Error obteniendo ruta automática: {e}")
                resultado["ruta_automatica"] = {"disponible": False, "error": str(e)}

        logger.info(
            f"✅ Verificación completa finalizada para {codigo_estilo}: {resultado}"
        )
        return resultado

    except Exception as e:
        logger.error(f"❌ Error en verificación completa: {e}")
        raise HTTPException(status_code=500, detail=f"Error en verificación: {str(e)}")


@app.get("/autocompletar-estilo/{codigo_estilo}", tags=["Búsqueda"])
async def autocompletar_estilo_recurrente(
    codigo_estilo: str,
    version_calculo: Optional[VersionCalculo] = VersionCalculo.FLUIDA,
):
    """
    ✅ ENDPOINT NUEVO: Auto-completa información para estilos recurrentes
    """
    try:
        logger.info(
            f"🔍 Auto-completado solicitado para: {codigo_estilo} (versión: {version_calculo})"
        )

        # Obtener información detallada
        info_detallada = await tdv_queries.obtener_info_detallada_estilo(
            codigo_estilo, version_calculo
        )

        if info_detallada.get("encontrado", False):
            logger.info(f"✅ Auto-completado disponible para {codigo_estilo}")

            return {
                "codigo_estilo": codigo_estilo,
                "autocompletado_disponible": True,
                "info_estilo": info_detallada,
                "campos_sugeridos": {
                    "familia_producto": info_detallada.get("familia_producto"),
                    "tipo_prenda": info_detallada.get("tipo_prenda"),
                },
                "metadata": {
                    "total_ops": info_detallada.get("total_ops", 0),
                    "volumen_total": info_detallada.get("volumen_total", 0),
                    "categoria": info_detallada.get("categoria", "Nuevo"),
                    "version_calculo": version_calculo,
                    "fuente": info_detallada.get("fuente", "historial_completo"),
                },
            }
        else:
            logger.info(f"⚠️ Auto-completado NO disponible para {codigo_estilo}")

            return {
                "codigo_estilo": codigo_estilo,
                "autocompletado_disponible": False,
                "razon": "Estilo no encontrado en base de datos",
                "es_estilo_nuevo": True,
                "version_calculo": version_calculo,
                "debug_info": info_detallada,
            }

    except Exception as e:
        logger.error(f"❌ Error en autocompletado: {e}")
        raise HTTPException(
            status_code=500, detail=f"Error obteniendo autocompletado: {str(e)}"
        )


@app.get("/debug-estilo/{codigo_estilo}", tags=["Debug"])
async def debug_estilo_clasificacion(
    codigo_estilo: str,
    version_calculo: Optional[VersionCalculo] = VersionCalculo.FLUIDA,
):
    """
    🔍 ENDPOINT DE DEBUG: Para diagnosticar problemas de clasificación
    """
    try:
        debug_info = {}

        # 1. Verificación en historial_estilos
        query_historial = f"""
        SELECT COUNT(*) as total, MAX(fecha_corrida) as ultima_corrida
        FROM {settings.db_schema}.historial_estilos
        WHERE codigo_estilo = ? AND version_calculo = ?
        """
        resultado_historial = await tdv_queries.db.query(
            query_historial, (codigo_estilo, version_calculo)
        )
        debug_info["historial_estilos"] = (
            resultado_historial[0] if resultado_historial else {}
        )

        # 2. Verificación en costo_op_detalle
        query_ops = f"""
        SELECT
          COUNT(*) as total_ops,
          SUM(prendas_requeridas) as volumen_total,
          MAX(fecha_corrida) as ultima_corrida,
          MAX(fecha_facturacion) as ultima_facturacion
        FROM {settings.db_schema}.costo_op_detalle
        WHERE estilo_propio = ? AND version_calculo = ?
        """
        resultado_ops = await tdv_queries.db.query(
            query_ops, (codigo_estilo, version_calculo)
        )
        debug_info["costo_op_detalle"] = resultado_ops[0] if resultado_ops else {}

        # 3. Búsqueda con LIKE
        query_like = f"""
        SELECT codigo_estilo, COUNT(*) as total
        FROM {settings.db_schema}.historial_estilos
        WHERE codigo_estilo LIKE ? AND version_calculo = ?
        GROUP BY codigo_estilo
        ORDER BY codigo_estilo
        """
        resultado_like = await tdv_queries.db.query(
            query_like, (f"%{codigo_estilo}%", version_calculo)
        )
        debug_info["busqueda_similar"] = resultado_like

        # 4. Función actual de verificación
        existe_actual = await tdv_queries.verificar_estilo_existente(
            codigo_estilo, version_calculo
        )
        debug_info["verificacion_actual"] = existe_actual

        # 5. Info detallada
        info_detallada = await tdv_queries.obtener_info_detallada_estilo(
            codigo_estilo, version_calculo
        )
        debug_info["info_detallada"] = info_detallada

        return {
            "codigo_estilo": codigo_estilo,
            "version_calculo": version_calculo,
            "debug_completo": debug_info,
            "timestamp": datetime.now().isoformat(),
        }

    except Exception as e:
        logger.error(f"❌ Error en debug: {e}")
        return {
            "codigo_estilo": codigo_estilo,
            "error": str(e),
            "timestamp": datetime.now().isoformat(),
        }


@app.get("/versiones-calculo", tags=["Configuración"])
async def obtener_versiones_calculo():
    """✅ CORREGIDO: Obtiene información sobre las versiones de cálculo disponibles"""
    try:
        logger.info("📋 Obteniendo información de versiones de cálculo")

        versiones_info = {}
        versiones = ["FLUIDA", "truncado"]

        for version in versiones:
            try:
                # Obtener estadísticas básicas por versión
                query = f"""
                SELECT
                  COUNT(*) as total_registros,
                  COUNT(DISTINCT cliente) as clientes_unicos,
                  COUNT(DISTINCT familia_de_productos) as familias_unicas,
                  MAX(fecha_corrida) as ultima_fecha_corrida
                FROM {settings.db_schema}.costo_op_detalle
                WHERE version_calculo = ?
                """
                resultado = await tdv_queries.db.query(query, (version,))

                if resultado and resultado[0]:
                    stats = resultado[0]
                    versiones_info[version] = {
                        "total_registros": int(stats[0] or 0),
                        "clientes_unicos": int(stats[1] or 0),
                        "familias_unicas": int(stats[2] or 0),
                        "ultima_fecha_corrida": stats[3],
                        "estado": "disponible" if (stats[0] or 0) > 0 else "sin_datos",
                    }
                else:
                    versiones_info[version] = {
                        "total_registros": 0,
                        "estado": "sin_datos",
                    }

            except Exception as e:
                versiones_info[version] = {"error": str(e), "estado": "error"}

        respuesta = {
            "versiones_disponibles": versiones_info,
            "version_por_defecto": "FLUIDA",
            "descripcion": {
                "FLUIDA": "Metodología de cálculo actual con optimizaciones",
                "truncado": "Metodología de cálculo con datos truncados/limitados",
            },
            "timestamp_consulta": datetime.now(),
        }

        logger.info(f"✅ Versiones de cálculo obtenidas: {list(versiones_info.keys())}")
        return respuesta

    except Exception as e:
        logger.error(f"❌ Error obteniendo versiones de cálculo: {e}")
        raise HTTPException(
            status_code=500, detail=f"Error obteniendo versiones: {str(e)}"
        )


# =====================================================================
# STARTUP Y CONFIGURACIÓN
# =====================================================================


@app.on_event("startup")
async def startup_event():
    """Eventos de inicio de la aplicación"""
    logger.info("🚀 Iniciando Sistema Cotizador TDV CORREGIDO")
    logger.info(f"📋 Versión: {settings.api_version}")
    logger.info(f"🗄️ Base de datos: {settings.db_host}")
    logger.info(f"🌐 CORS habilitado para: {settings.cors_origins}")
    logger.info("✅ CORRECCIONES APLICADAS:")
    logger.info(
        "   - ✅ Nuevos endpoints: /verificar-estilo-completo y /ops-utilizadas-cotizacion"
    )
    logger.info("   - ✅ Auto-completado inteligente para estilos recurrentes")
    logger.info("   - ✅ Manejo completo de version_calculo en todos los endpoints")
    logger.info("   - ✅ WIPs por estabilidad (37,45 = 6 meses | resto = último)")
    logger.info("   - ✅ Gastos indirectos: (MAX + PROMEDIO)/2")
    logger.info("   - ✅ Materia prima/avios: último costo")
    logger.info("   - ✅ Filtros por fecha_corrida en lugar de GETDATE()")
    logger.info("   - ✅ Rutas textiles restauradas y mejoradas")
    logger.info("   - ✅ Logging mejorado con emojis para mejor seguimiento")

    # Verificar conexión inicial
    try:
        tablas = await tdv_queries.health_check()
        logger.info(f"📋 Tablas verificadas: {tablas}")

        # Verificar versiones disponibles
        try:
            versiones_query = f"""
            SELECT DISTINCT version_calculo, COUNT(*) as registros
            FROM {settings.db_schema}.costo_op_detalle
            GROUP BY version_calculo
            ORDER BY registros DESC
            """
            versiones_resultado = await tdv_queries.db.query(versiones_query)

            if versiones_resultado:
                logger.info("📊 Versiones de cálculo disponibles:")
                for version_info in versiones_resultado:
                    version, registros = version_info
                    logger.info(f"     - {version}: {registros} registros")
            else:
                logger.warning(
                    "⚠️ No se encontraron versiones de cálculo en costo_op_detalle"
                )

        except Exception as e:
            logger.warning(f"⚠️ Error verificando versiones de cálculo: {e}")

        # Verificar fechas de corrida por versión
        for tabla in ["costo_op_detalle", "resumen_wip_por_prenda"]:
            try:
                for version in ["FLUIDA", "truncado"]:
                    try:
                        fecha_max = await tdv_queries.obtener_fecha_maxima_corrida(
                            tabla, version
                        )
                        if fecha_max:
                            dias_antiguedad = (datetime.now() - fecha_max).days
                            logger.info(
                                f"📅 {tabla} ({version}): última corrida {fecha_max} ({dias_antiguedad} días)"
                            )
                    except Exception:
                        # Si no existe la versión, no es crítico
                        pass
            except Exception as e:
                logger.warning(f"⚠️ {tabla}: error obteniendo fechas corrida - {e}")

    except Exception as e:
        logger.error(f"❌ Error verificando BD en startup: {e}")


@app.on_event("shutdown")
async def shutdown_event():
    """Eventos de cierre de la aplicación"""
    logger.info("🛑 Cerrando Sistema Cotizador TDV")


# =====================================================================
# PUNTO DE ENTRADA
# =====================================================================

if __name__ == "__main__":
    import uvicorn

    logger.info(f"🚀 Iniciando servidor en {settings.api_host}:{settings.api_port}")
    uvicorn.run(
        "app",
        host=settings.api_host,
        port=settings.api_port,
        reload=settings.debug,
        log_level=settings.log_level.lower(),
    )
