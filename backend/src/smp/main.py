"""
=====================================================================
APLICACIN FASTAPI PRINCIPAL - BACKEND TDV COTIZADOR - COMPLETAMENTE CORREGIDO
=====================================================================
[OK] Nuevos endpoints agregados:
- /verificar-estilo-completo/{codigo_estilo} - Auto-completado completo
- /ops-utilizadas-cotizacion - OPs reales utilizadas
[OK] Todos los endpoints corregidos con version_calculo
[OK] Manejo mejorado de errores y logging
"""

from fastapi import FastAPI, HTTPException, Body
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse as FastAPIJSONResponse
from typing import List, Optional, Dict, Any
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
# CONFIGURACIN FASTAPI
# =====================================================================

app = FastAPI(
    title=settings.api_title,
    version=settings.api_version,
    description="Sistema de cotizacin inteligente basado en metodologa WIP para TDV - COMPLETAMENTE CORREGIDO",
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
    """Endpoint raz con informacin del sistema"""
    return {
        "sistema": "Cotizador TDV Expert",
        "version": settings.api_version,
        "status": "activo",
        "arquitectura": "TDV Real Database",
        "features": [
            "[OK] CORREGIDO: Bsqueda mejorada en costo_op_detalle",
            "[OK] CORREGIDO: Configurador WIPs desde resumen_wip_por_prenda",
            "[OK] CORREGIDO: Categorizacin automtica de estilos",
            "[OK] NUEVO: Auto-completado inteligente para estilos recurrentes",
            "[OK] NUEVO: Endpoint OPs reales utilizadas",
            "[OK] CORREGIDO: Manejo completo de versiones de clculo",
            "[OK] CORREGIDO: Rutas textiles restauradas",
            "Factores de ajuste basados en anlisis TDV",
            "Informacin comercial avanzada",
            "Anlisis inteligente WIPs por estabilidad + fecha_corrida",
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
    """Verificacin de estado del sistema y BD"""
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
#  NUEVOS ENDPOINTS CRTICOS
# =====================================================================


@app.get("/verificar-estilo-completo/{codigo_estilo}", tags=["Bsqueda"])
async def verificar_estilo_completo_con_autocompletado(
    codigo_estilo: str,
    version_calculo: Optional[VersionCalculo] = VersionCalculo.FLUIDA,
):
    """
    [OK] NUEVO ENDPOINT: Verificacin completa de estilo con auto-completado

    Este endpoint proporciona:
    1. Verificacin si es nuevo/recurrente
    2. Auto-completado de familia_producto y tipo_prenda
    3. Informacin detallada del estilo
    4. Volumen histrico y categorizacin
    """
    try:
        # PASO 1: Verificacin bsica
        existe = await tdv_queries.verificar_estilo_existente(
            codigo_estilo, version_calculo
        )
        es_nuevo = not existe

        # PASO 2: Informacin detallada si existe
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
                        f"[OK] Auto-completado disponible para {codigo_estilo}: {campos_sugeridos}"
                    )

            except Exception as e:
                logger.warning(
                    f"[WARN] Error obteniendo info detallada para {codigo_estilo}: {e}"
                )
                info_detallada = None

        # PASO 3: Volumen y categorizacin
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
            f"[OK] Verificacin completa {codigo_estilo}: existe={existe}, auto-completado={autocompletado_disponible}"
        )
        return respuesta

    except Exception as e:
        logger.error(f"[ERROR] Error en verificacin completa {codigo_estilo}: {e}")
        raise HTTPException(
            status_code=500, detail=f"Error verificando estilo: {str(e)}"
        )


@app.post("/ops-utilizadas-cotizacion", tags=["Anlisis"])
async def obtener_ops_utilizadas_cotizacion(input_data: CotizacionInput):
    """
    [OK] NUEVO ENDPOINT: Obtiene las OPs reales utilizadas para una cotizacin

    Retorna las rdenes de produccin especficas que se usaron como base
    para calcular los costos de la cotizacin.
    """
    try:
        logger.info(
            f" Obteniendo OPs utilizadas para: {input_data.codigo_estilo} ({input_data.version_calculo})"
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
            f"[OK] OPs encontradas: {respuesta['total_ops_encontradas']} para {input_data.codigo_estilo}"
        )
        return respuesta

    except Exception as e:
        logger.error(f"[ERROR] Error obteniendo OPs utilizadas: {e}")
        raise HTTPException(status_code=500, detail=f"Error obteniendo OPs: {str(e)}")


# =====================================================================
# ENDPOINTS DE CONFIGURACIN - CORREGIDOS CON VERSION_CALCULO
# =====================================================================


@app.get("/configuracion", response_model=ConfiguracionResponse, tags=["Configuracin"])
async def obtener_configuracion():
    """Obtiene configuracin completa del sistema"""
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
    "/wips-disponibles", response_model=WipsDisponiblesResponse, tags=["Configuracin"]
)
async def obtener_wips_disponibles(
    tipo_prenda: Optional[str] = None,
    version_calculo: Optional[VersionCalculo] = VersionCalculo.FLUIDA,
):
    """[OK] CORREGIDO: Obtiene WIPs disponibles con costos actuales - ANLISIS INTELIGENTE CON VERSION_CALCULO"""
    try:
        logger.info(
            f" Obteniendo WIPs disponibles: tipo_prenda={tipo_prenda}, version={version_calculo}"
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
            f"[OK] WIPs obtenidas: {respuesta.total_disponibles} disponibles para {tipo_prenda or 'genrico'} ({version_calculo})"
        )
        return respuesta

    except Exception as e:
        logger.error(f"[ERROR] Error obteniendo WIPs: {e}")
        raise HTTPException(status_code=500, detail=f"Error obteniendo WIPs: {str(e)}")


@app.get("/ruta-textil-recomendada/{tipo_prenda}", tags=["Configuracin"])
async def obtener_ruta_textil_recomendada(
    tipo_prenda: str,
    version_calculo: Optional[VersionCalculo] = VersionCalculo.FLUIDA,
):
    """[OK] CORREGIDO: Obtiene ruta textil recomendada para un tipo de prenda especfico"""
    try:
        logger.info(
            f" Obteniendo ruta textil para: {tipo_prenda} ({version_calculo})"
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
            f"[OK] Ruta textil obtenida: {len(ruta_textil.get('wips_recomendadas', []))} WIPs recomendadas"
        )
        return ruta_textil

    except Exception as e:
        logger.error(f"[ERROR] Error obteniendo ruta textil para {tipo_prenda}: {e}")
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
    """[OK] CORREGIDO: Obtiene lista de clientes disponibles CON VERSION_CALCULO"""
    try:
        logger.info(f" Cargando clientes para versin: {version_calculo}")

        clientes = await tdv_queries.obtener_clientes_disponibles(version_calculo)

        respuesta = {
            "clientes": clientes,
            "total": len(clientes),
            "fuente": "costo_op_detalle",
            "version_calculo": version_calculo,
            "timestamp": datetime.now().isoformat(),
        }

        logger.info(f"[OK] Clientes cargados: {len(clientes)} para {version_calculo}")
        return respuesta

    except Exception as e:
        logger.error(f"[ERROR] Error obteniendo clientes: {e}")
        raise HTTPException(
            status_code=500, detail=f"Error obteniendo clientes: {str(e)}"
        )


@app.get("/familias-productos", tags=["Datos Maestros"])
async def obtener_familias_productos(
    version_calculo: Optional[VersionCalculo] = VersionCalculo.FLUIDA,
):
    """Obtiene familias de productos disponibles CON VERSION_CALCULO"""
    try:
        logger.info(f" Cargando familias para versin: {version_calculo}")

        familias = await tdv_queries.obtener_familias_productos(version_calculo)

        respuesta = {
            "familias": familias,
            "total": len(familias),
            "fuente": "costo_op_detalle",
            "version_calculo": version_calculo,
            "timestamp": datetime.now().isoformat(),
        }

        logger.info(f"[OK] Familias cargadas: {len(familias)} para {version_calculo}")
        return respuesta

    except Exception as e:
        logger.error(f"[ERROR] Error obteniendo familias: {e}")
        raise HTTPException(
            status_code=500, detail=f"Error obteniendo familias: {str(e)}"
        )


@app.get("/tipos-prenda", tags=["Datos Maestros"])
async def obtener_todos_tipos_prenda(
    version_calculo: Optional[VersionCalculo] = VersionCalculo.FLUIDA
):
    """[OK] Obtiene TODOS los tipos de prenda disponibles (sin familia)"""
    try:
        logger.info(f"Cargando todos los tipos de prenda ({version_calculo})")

        tipos = await tdv_queries.obtener_todos_tipos_prenda(version_calculo)

        respuesta = {
            "tipos": tipos,
            "total": len(tipos),
            "fuente": "costo_op_detalle",
            "version_calculo": version_calculo,
            "timestamp": datetime.now().isoformat(),
        }

        logger.info(
            f"Tipos cargados: {len(tipos)} ({version_calculo})"
        )
        return respuesta

    except Exception as e:
        logger.error(f"Error obteniendo tipos de prenda: {e}")
        raise HTTPException(status_code=500, detail=f"Error obteniendo tipos: {str(e)}")


@app.get("/tipos-prenda/{familia}", tags=["Datos Maestros"])
async def obtener_tipos_prenda(
    familia: str, version_calculo: Optional[VersionCalculo] = VersionCalculo.FLUIDA
):
    """[OK] CORREGIDO: Obtiene tipos de prenda para una familia especfica CON VERSION_CALCULO"""
    try:
        logger.info(f"Cargando tipos para familia: {familia} ({version_calculo})")

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
            f"[OK] Tipos cargados: {len(tipos)} para {familia} ({version_calculo})"
        )
        return respuesta

    except Exception as e:
        logger.error(f"[ERROR] Error obteniendo tipos de prenda: {e}")
        raise HTTPException(status_code=500, detail=f"Error obteniendo tipos: {str(e)}")


# =====================================================================
# ENDPOINTS DE BSQUEDA - CORREGIDOS CON VERSION_CALCULO
# =====================================================================


@app.get(
    "/buscar-estilos/{codigo_estilo}",
    response_model=List[EstiloSimilar],
    tags=["Bsqueda"],
)
async def buscar_estilos_similares(
    codigo_estilo: str,
    cliente: Optional[str] = None,
    limite: Optional[int] = 10,
    version_calculo: Optional[VersionCalculo] = VersionCalculo.FLUIDA,
):
    """[OK] CORREGIDO: Busca estilos similares por cdigo y cliente CON VERSION_CALCULO"""
    try:
        if len(codigo_estilo) < 3:
            return []

        logger.info(
            f" Buscando estilos similares: {codigo_estilo} para {cliente or 'cualquier cliente'} ({version_calculo})"
        )

        estilos = await tdv_queries.buscar_estilos_similares(
            codigo_estilo, cliente or "", limite, version_calculo
        )

        logger.info(
            f"[OK] Estilos similares encontrados: {len(estilos)} para {codigo_estilo} ({version_calculo})"
        )
        return estilos

    except Exception as e:
        logger.error(f"[ERROR] Error buscando estilos: {e}")
        raise HTTPException(status_code=500, detail=f"Error en bsqueda: {str(e)}")


@app.get("/verificar-estilo/{codigo_estilo}", tags=["Bsqueda"])
async def verificar_estilo_existente(
    codigo_estilo: str,
    version_calculo: Optional[VersionCalculo] = VersionCalculo.FLUIDA,
):
    """[OK] MANTENIDO: Verificacin bsica de estilo (compatibilidad)"""
    try:
        existe = await tdv_queries.verificar_estilo_existente(
            codigo_estilo, version_calculo
        )
        es_nuevo = not existe

        # Determinar categora especfica si es recurrente
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
            f"[OK] Verificacin bsica {codigo_estilo}: existe={existe}, categora={categoria}, volumen={volumen_historico}"
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
        logger.error(f"[ERROR] Error verificando estilo: {e}")
        raise HTTPException(
            status_code=500, detail=f"Error verificando estilo: {str(e)}"
        )


# =====================================================================
# NUEVO ENDPOINT: OBTENER OPS DETALLADAS PARA TABLA INTERACTIVA
# =====================================================================

@app.get("/obtener-ops-detalladas/{codigo_estilo}", tags=["Bsqueda"])
async def obtener_ops_detalladas(
    codigo_estilo: str,
    version_calculo: Optional[VersionCalculo] = VersionCalculo.FLUIDA,
    meses: int = 12,
):
    """
    Obtiene lista detallada de OPs para un estilo sin aplicar factor de seguridad.
    Retorna todos los datos unitarios para mostrar en tabla interactiva.
    Si no hay OPs con los filtros (>= 200 prendas), retorna lista vaca (estilo nuevo).
    """
    try:
        ops_detalladas = await tdv_queries.obtener_ops_detalladas_para_tabla(
            codigo_estilo, meses, version_calculo
        )

        es_estilo_nuevo = len(ops_detalladas) == 0

        logger.info(
            f" OPs obtenidas para {codigo_estilo}: {len(ops_detalladas)} registros, es_nuevo={es_estilo_nuevo}"
        )

        return {
            "codigo_estilo": codigo_estilo,
            "version_calculo": version_calculo,
            "es_estilo_nuevo": es_estilo_nuevo,
            "ops_encontradas": len(ops_detalladas),
            "ops": ops_detalladas,
        }

    except Exception as e:
        logger.error(f"Error obteniendo OPs detalladas para {codigo_estilo}: {e}")
        raise HTTPException(
            status_code=500, detail=f"Error obteniendo OPs: {str(e)}"
        )


@app.post("/calcular-promedios-ops-seleccionadas", tags=["Bsqueda"])
async def calcular_promedios_ops_seleccionadas(ops_seleccionadas: List[Dict[str, Any]]):
    """
    Calcula promedios sin factor de seguridad basado en OPs seleccionadas.
    Recibe lista de OPs con flag 'seleccionado' indicando cules usar.
    """
    try:
        # Filtrar solo las OPs que estn seleccionadas
        ops_activas = [op for op in ops_seleccionadas if op.get("seleccionado", False)]

        if not ops_activas:
            logger.warning("No hay OPs seleccionadas para calcular promedios")
            return {
                "error": "No hay OPs seleccionadas",
                "ops_usadas": 0,
                "promedios": {},
            }

        # Calcular promedios sin aplicar factor de seguridad
        promedios = {
            "textil_unitario": sum(op.get("textil_unitario", 0) for op in ops_activas) / len(ops_activas),
            "manufactura_unitario": sum(op.get("manufactura_unitario", 0) for op in ops_activas) / len(ops_activas),
            "materia_prima_unitario": sum(op.get("materia_prima_unitario", 0) for op in ops_activas) / len(ops_activas),
            "avios_unitario": sum(op.get("avios_unitario", 0) for op in ops_activas) / len(ops_activas),
            "indirecto_fijo_unitario": sum(op.get("indirecto_fijo_unitario", 0) for op in ops_activas) / len(ops_activas),
            "administracion_unitario": sum(op.get("administracion_unitario", 0) for op in ops_activas) / len(ops_activas),
            "ventas_unitario": sum(op.get("ventas_unitario", 0) for op in ops_activas) / len(ops_activas),
        }

        # Calcular subtotal
        subtotal = sum(promedios.values())

        logger.info(
            f" Promedios calculados sin factor de seguridad: {len(ops_activas)} OPs usadas, subtotal=${subtotal:.4f}"
        )

        return {
            "ops_usadas": len(ops_activas),
            "promedios": promedios,
            "subtotal": subtotal,
        }

    except Exception as e:
        logger.error(f"Error calculando promedios: {e}")
        raise HTTPException(
            status_code=500, detail=f"Error calculando promedios: {str(e)}"
        )


@app.post("/desglose-wip-ops", tags=["Bsqueda"])
async def desglose_wip_ops(data: Dict[str, Any] = Body(...)):
    """
    Obtiene desglose de costos por WIP para OPs seleccionadas.
    Retorna costo_textil y costo_manufactura promedio por cada WIP.
    """
    try:
        cod_ordpros = data.get("cod_ordpros", [])
        version_calculo = data.get("version_calculo", "FLUIDA")

        logger.info(f" [ENDPOINT-DESGLOSE-WIP] Request recibida")
        logger.info(f" [ENDPOINT-DESGLOSE-WIP] cod_ordpros recibidos: {cod_ordpros} (tipo: {type(cod_ordpros)}, len: {len(cod_ordpros) if cod_ordpros else 0})")
        logger.info(f" [ENDPOINT-DESGLOSE-WIP] version_calculo: {version_calculo}")

        if not cod_ordpros:
            logger.warning(f" [ENDPOINT-DESGLOSE-WIP] No se proporcionaron OPs")
            return {
                "error": "No se proporcionaron OPs",
                "desgloses": [],
            }

        # DEBUG: Obtener desglose de WIPs
        logger.info(f" [ENDPOINT-DESGLOSE-WIP] Llamando a obtener_desglose_wip_por_ops con {len(cod_ordpros)} OPs")
        desgloses = await tdv_queries.obtener_desglose_wip_por_ops(
            cod_ordpros, version_calculo
        )
        logger.info(f" [ENDPOINT-DESGLOSE-WIP] Resultado: {len(desgloses)} WIPs encontrados")

        # Separar por grupo
        desgloses_textil = [d for d in desgloses if d["grupo_wip"] == "textil"]
        desgloses_manufactura = [d for d in desgloses if d["grupo_wip"] == "manufactura"]

        logger.info(
            f" [ENDPOINT-DESGLOSE-WIP] Desglose WIP: {len(desgloses_textil)} WIPs textil, {len(desgloses_manufactura)} WIPs manufactura"
        )

        return {
            "ops_analizadas": len(cod_ordpros),
            "desgloses_textil": desgloses_textil,
            "desgloses_manufactura": desgloses_manufactura,
            "desgloses_total": desgloses,
            "_debug": {
                "cod_ordpros_input": cod_ordpros,
                "version_input": version_calculo,
                "desgloses_count": len(desgloses)
            }
        }

    except Exception as e:
        logger.error(f" [ENDPOINT-DESGLOSE-WIP] Error obteniendo desglose WIP: {e}")
        import traceback
        logger.error(f" [ENDPOINT-DESGLOSE-WIP] Traceback: {traceback.format_exc()}")
        raise HTTPException(
            status_code=500, detail=f"Error obteniendo desglose WIP: {str(e)}"
        )


# =====================================================================
# ENDPOINT PRINCIPAL DE COTIZACIN - YA MANEJA VERSION_CALCULO VIA INPUT_DATA
# =====================================================================


@app.post("/cotizar", response_model=CotizacionResponse, tags=["Cotizacin"])
async def crear_cotizacion(input_data: CotizacionInput):
    """[OK] CORREGIDO: Endpoint principal para crear cotizaciones - CON SOPORTE COMPLETO VERSION_CALCULO"""
    try:
        logger.info(
            f" Nueva cotizacin: {input_data.usuario} | {input_data.codigo_estilo} | Versin: {input_data.version_calculo} | OPs: {input_data.cod_ordpros}"
        )

        # Validar version_calculo
        if hasattr(input_data, "version_calculo") and input_data.version_calculo:
            versiones_validas = ["FLUIDA", "truncado"]
            version_value = input_data.version_calculo.value if hasattr(input_data.version_calculo, 'value') else str(input_data.version_calculo)
            if version_value not in versiones_validas:
                raise ValueError(
                    f"version_calculo debe ser una de: {versiones_validas}"
                )
        else:
            # Asignar default si no viene en input
            input_data.version_calculo = VersionCalculo.FLUIDA

        # Rutear a método optimizado si hay OPs seleccionadas
        if input_data.cod_ordpros and len(input_data.cod_ordpros) > 0:
            logger.info(f"[COTIZACION RAPIDA] Usando método optimizado para {len(input_data.cod_ordpros)} OPs seleccionadas")
            resultado = await cotizador_tdv.procesar_cotizacion_rapida_por_ops(input_data)
        else:
            # Usar método estándar si no hay OPs seleccionadas
            resultado = await cotizador_tdv.procesar_cotizacion(input_data)

        logger.info(
            f"[OK] Cotizacin completada: {resultado.id_cotizacion} | ${resultado.precio_final:.2f} | Versin: {resultado.version_calculo_usada}"
        )
        return resultado

    except ValueError as e:
        logger.warning(f"[WARN] Error de validacin: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"[ERROR] Error procesando cotizacin: {e}")
        raise HTTPException(status_code=500, detail=f"Error interno: {str(e)}")


# =====================================================================
# ENDPOINTS DE ANLISIS - CORREGIDOS CON VERSION_CALCULO
# =====================================================================


@app.get("/analisis-historico", tags=["Anlisis"])
async def obtener_analisis_historico(
    familia: str,
    tipo: Optional[str] = None,
    meses: Optional[int] = 12,
    version_calculo: Optional[VersionCalculo] = VersionCalculo.FLUIDA,
):
    """[OK] CORREGIDO: Anlisis histrico para benchmarking CON VERSION_CALCULO"""
    try:
        logger.info(f"[DATA] Anlisis histrico: {familia}/{tipo} ({version_calculo})")

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
            f"[OK] Anlisis histrico completado para {familia}/{tipo} ({version_calculo})"
        )
        return respuesta

    except Exception as e:
        logger.error(f"[ERROR] Error en anlisis histrico: {e}")
        raise HTTPException(status_code=500, detail=f"Error en anlisis: {str(e)}")


# =====================================================================
# ENDPOINTS DE UTILIDAD - MANTENER ORIGINALES
# =====================================================================


@app.get("/categoria-lote/{cantidad}", tags=["Utilidades"])
async def categorizar_lote_por_cantidad(cantidad: int):
    """Categoriza un lote basndose en cantidad de prendas"""
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
    """Obtiene factor de marca para un cliente especfico"""
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
# ENDPOINTS DE INFORMACIN SISTEMA
# =====================================================================


@app.get("/info-fechas-corrida", tags=["Anlisis"])
async def obtener_info_fechas_corrida(
    version_calculo: Optional[VersionCalculo] = VersionCalculo.FLUIDA,
):
    """[OK] CORREGIDO: Obtiene informacin sobre las fechas de corrida CON VERSION_CALCULO"""
    try:
        logger.info(f" Obteniendo fechas corrida para versin: {version_calculo}")

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

        logger.info(f"[OK] Fechas corrida obtenidas para {version_calculo}")
        return respuesta

    except Exception as e:
        logger.error(f"[ERROR] Error obteniendo info fechas corrida: {e}")
        raise HTTPException(
            status_code=500, detail=f"Error obteniendo fechas: {str(e)}"
        )


@app.get("/verificar-estilo-completo/{codigo_estilo}", tags=["Bsqueda"])
async def verificar_estilo_completo(
    codigo_estilo: str,
    familia_producto: Optional[str] = None,
    tipo_prenda: Optional[str] = None,
    version_calculo: Optional[VersionCalculo] = VersionCalculo.FLUIDA,
):
    """
    [OK] ENDPOINT NUEVO: Verificacin completa con auto-completado y ruta
    Este endpoint era referenciado en el frontend pero no exista
    """
    try:
        logger.info(
            f" Verificacin completa para estilo: {codigo_estilo} (versin: {version_calculo})"
        )

        # PASO 1: Verificacin bsica
        existe = await tdv_queries.verificar_estilo_existente(
            codigo_estilo, version_calculo
        )
        es_nuevo = not existe

        logger.info(
            f" Resultado verificacin bsica - existe: {existe}, es_nuevo: {es_nuevo}"
        )

        # PASO 2: Informacin detallada si existe
        info_detallada = await tdv_queries.obtener_info_detallada_estilo(
            codigo_estilo, version_calculo
        )

        # PASO 3: Determinar categora y auto-completado
        if info_detallada.get("encontrado", False):
            categoria = info_detallada.get("categoria", "Nuevo")
            volumen_historico = info_detallada.get("volumen_total", 0)
            familia_autocompletada = info_detallada.get("familia_producto")
            tipo_autocompletado = info_detallada.get("tipo_prenda")

            logger.info(
                f"[OK] Info detallada encontrada - categora: {categoria}, volumen: {volumen_historico}"
            )
        else:
            categoria = "Nuevo"
            volumen_historico = 0
            familia_autocompletada = None
            tipo_autocompletado = None

            logger.info(f"[WARN] Info detallada NO encontrada para {codigo_estilo}")

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

        # PASO 5: Ruta automtica para estilos nuevos (si se proporcionan familia/tipo)
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
                    f"[OK] Ruta automtica agregada para estilo nuevo: {codigo_estilo}"
                )

            except Exception as e:
                logger.warning(f"[WARN] Error obteniendo ruta automtica: {e}")
                resultado["ruta_automatica"] = {"disponible": False, "error": str(e)}

        logger.info(
            f"[OK] Verificacin completa finalizada para {codigo_estilo}: {resultado}"
        )
        return resultado

    except Exception as e:
        logger.error(f"[ERROR] Error en verificacin completa: {e}")
        raise HTTPException(status_code=500, detail=f"Error en verificacin: {str(e)}")


@app.get("/autocompletar-estilo/{codigo_estilo}", tags=["Bsqueda"])
async def autocompletar_estilo_recurrente(
    codigo_estilo: str,
    version_calculo: Optional[VersionCalculo] = VersionCalculo.FLUIDA,
):
    """
    [OK] ENDPOINT NUEVO: Auto-completa informacin para estilos recurrentes
    """
    try:
        logger.info(
            f" Auto-completado solicitado para: {codigo_estilo} (versin: {version_calculo})"
        )

        # Obtener informacin detallada
        info_detallada = await tdv_queries.obtener_info_detallada_estilo(
            codigo_estilo, version_calculo
        )

        if info_detallada.get("encontrado", False):
            logger.info(f"[OK] Auto-completado disponible para {codigo_estilo}")

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
            logger.info(f"[WARN] Auto-completado NO disponible para {codigo_estilo}")

            return {
                "codigo_estilo": codigo_estilo,
                "autocompletado_disponible": False,
                "razon": "Estilo no encontrado en base de datos",
                "es_estilo_nuevo": True,
                "version_calculo": version_calculo,
                "debug_info": info_detallada,
            }

    except Exception as e:
        logger.error(f"[ERROR] Error en autocompletado: {e}")
        raise HTTPException(
            status_code=500, detail=f"Error obteniendo autocompletado: {str(e)}"
        )


@app.get("/debug-estilo/{codigo_estilo}", tags=["Debug"])
async def debug_estilo_clasificacion(
    codigo_estilo: str,
    version_calculo: Optional[VersionCalculo] = VersionCalculo.FLUIDA,
):
    """
     ENDPOINT DE DEBUG: Para diagnosticar problemas de clasificacin
    """
    try:
        debug_info = {}

        # 1. Verificacin en historial_estilos
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

        # 2. Verificacin en costo_op_detalle
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

        # 3. Bsqueda con LIKE
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

        # 4. Funcin actual de verificacin
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
        logger.error(f"[ERROR] Error en debug: {e}")
        return {
            "codigo_estilo": codigo_estilo,
            "error": str(e),
            "timestamp": datetime.now().isoformat(),
        }


@app.get("/versiones-calculo", tags=["Configuracin"])
async def obtener_versiones_calculo():
    """[OK] CORREGIDO: Obtiene informacin sobre las versiones de clculo disponibles"""
    try:
        logger.info("[INFO] Obteniendo informacin de versiones de clculo")

        versiones_info = {}
        versiones = ["FLUIDA", "truncado"]

        for version in versiones:
            try:
                # Obtener estadsticas bsicas por versin
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
                "FLUIDA": "Metodologa de clculo actual con optimizaciones",
                "truncado": "Metodologa de clculo con datos truncados/limitados",
            },
            "timestamp_consulta": datetime.now(),
        }

        logger.info(f"[OK] Versiones de clculo obtenidas: {list(versiones_info.keys())}")
        return respuesta

    except Exception as e:
        logger.error(f"[ERROR] Error obteniendo versiones de clculo: {e}")
        raise HTTPException(
            status_code=500, detail=f"Error obteniendo versiones: {str(e)}"
        )


# =====================================================================
# STARTUP Y CONFIGURACIN
# =====================================================================


@app.on_event("startup")
async def startup_event():
    """Eventos de inicio de la aplicacin"""
    logger.info("[STARTUP] Iniciando Sistema Cotizador TDV CORREGIDO")
    logger.info(f"[VERSION] Versi_n: {settings.api_version}")
    logger.info(f"[DATABASE] Base de datos: {settings.db_host}")
    logger.info(f"[CORS] CORS habilitado para: {settings.cors_origins}")
    logger.info("[OK] CORRECCIONES APLICADAS:")
    logger.info(
        "   - [OK] Nuevos endpoints: /verificar-estilo-completo y /ops-utilizadas-cotizacion"
    )
    logger.info("   - [OK] Auto-completado inteligente para estilos recurrentes")
    logger.info("   - [OK] Manejo completo de version_calculo en todos los endpoints")
    logger.info("   - [OK] WIPs por estabilidad (37,45 = 6 meses | resto = ultlast)")
    logger.info("   - [OK] Gastos indirectos: (MAX + PROMEDIO)/2")
    logger.info("   - [OK] Materia prima/avios: ltimo costo")
    logger.info("   - [OK] Filtros por fecha_corrida en lugar de GETDATE()")
    logger.info("   - [OK] Rutas textiles restauradas y mejoradas")
    logger.info("   - [OK] Logging mejorado con emojis para mejor seguimiento")

    # Verificar conexin inicial
    try:
        tablas = await tdv_queries.health_check()
        logger.info(f"[INFO] Tablas verificadas: {tablas}")

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
                logger.info("[DATA] Versiones de clculo disponibles:")
                for version_info in versiones_resultado:
                    version, registros = version_info
                    logger.info(f"     - {version}: {registros} registros")
            else:
                logger.warning(
                    "[WARN] No se encontraron versiones de clculo en costo_op_detalle"
                )

        except Exception as e:
            logger.warning(f"[WARN] Error verificando versiones de clculo: {e}")

        # Verificar fechas de corrida por versin
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
                                f" {tabla} ({version}): ltima corrida {fecha_max} ({dias_antiguedad} das)"
                            )
                    except Exception:
                        # Si no existe la versin, no es crtico
                        pass
            except Exception as e:
                logger.warning(f"[WARN] {tabla}: error obteniendo fechas corrida - {e}")

    except Exception as e:
        logger.error(f"[ERROR] Error verificando BD en startup: {e}")


@app.on_event("shutdown")
async def shutdown_event():
    """Eventos de cierre de la aplicacin"""
    logger.info(" Cerrando Sistema Cotizador TDV")


# =====================================================================
# PUNTO DE ENTRADA
# =====================================================================

if __name__ == "__main__":
    import uvicorn

    logger.info(f"[STARTUP] Iniciando servidor en {settings.api_host}:{settings.api_port}")
    uvicorn.run(
        "smp.main:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=settings.debug,
        log_level=settings.log_level.lower(),
    )
