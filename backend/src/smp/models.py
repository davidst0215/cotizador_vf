"""
=====================================================================
MODELOS PYDANTIC - BACKEND TDV COTIZADOR - COMPLETAMENTE CORREGIDOS
=====================================================================
 Nuevos modelos para auto-completado
 Modelos para OPs reales utilizadas
 Modelos mejorados para respuestas completas
 Validaciones robustas
 Compatibilidad total con frontend corregido
"""

from pydantic import BaseModel, Field, field_validator
from typing import List, Optional, Dict, Any
from datetime import datetime
from enum import Enum


# =====================================================================
# ENUMS Y CONSTANTES
# =====================================================================


class VersionCalculo(str, Enum):
    """Versiones de clculo disponibles"""

    FLUIDO = "FLUIDO"  # Versión fluida (compatible con BD y frontend)
    TRUNCADO = "truncado"


class TipoEstilo(str, Enum):
    """Tipos de estilo segn volumen histrico"""

    NUEVO = "Nuevo"
    RECURRENTE = "Recurrente"
    MUY_RECURRENTE = "Muy Recurrente"


class FuenteCosto(str, Enum):
    """Fuentes de donde provienen los costos"""

    HISTORICO = "historico"
    WIP = "wip"
    FORMULA = "formula"
    ULTIMO_COSTO = "ultimo_costo"
    PROMEDIO_RANGO = "promedio_rango"


# =====================================================================
# MODELOS DE ENTRADA (ALINEADOS CON FRONTEND)
# =====================================================================


class WipSeleccionada(BaseModel):
    """WIP seleccionada con factor de ajuste"""

    wip_id: str = Field(..., description="ID de la WIP")
    factor_ajuste: float = Field(
        default=1.0, ge=0.1, le=2.0, description="Factor de ajuste"
    )
    costo_base: Optional[float] = Field(None, description="Costo base de la WIP")


class WipConfiguracion(BaseModel):
    """Configuracin de WIP para respuesta"""

    wip_id: str = Field(..., description="ID de la WIP")
    nombre: str = Field(..., description="Nombre de la WIP")
    costo: float = Field(..., description="Costo de la WIP")
    grupo: str = Field(..., description="Grupo (Textil/Manufactura)")


class CotizacionInput(BaseModel):
    """ MODELO PRINCIPAL CORREGIDO: Input para cotizacin (alineado con frontend)"""

    # Campos exactos del frontend
    cliente_marca: str = Field(
        ..., min_length=1, max_length=100, description="Cliente/Marca"
    )
    # NOTA: temporada y familia_producto ahora son OPCIONALES (no se usan en la UI)
    temporada: Optional[str] = Field(None, max_length=50, description="Temporada (opcional)")
    categoria_lote: str = Field(..., description="Categora del lote")
    familia_producto: Optional[str] = Field(
        None, max_length=100, description="Familia de producto (opcional)"
    )
    tipo_prenda: str = Field(
        ..., min_length=1, max_length=100, description="Tipo de prenda"
    )
    codigo_estilo: str = Field(
        ..., min_length=1, max_length=50, description="Cdigo del estilo"
    )
    usuario: str = Field(
        default="Sistema", max_length=100, description="Usuario que cotiza"
    )
    cantidad_prendas: Optional[int] = Field(
        None, ge=1, description="Cantidad de prendas del lote"
    )
    esfuerzo_total: Optional[int] = Field(
        None, ge=1, le=10, description="Esfuerzo total (1-10)"
    )
    margen_adicional: Optional[float] = Field(
        None, ge=0, le=100, description="Margen adicional en %"
    )

    #  CORREGIDO: Campo para versin de clculo con enum
    version_calculo: VersionCalculo = Field(
        default=VersionCalculo.FLUIDO, description="Versin de clculo"
    )

    # Campos determinados automticamente por el backend
    es_estilo_nuevo: Optional[bool] = Field(
        None, description="Se determina automticamente"
    )

    # OPs seleccionadas para estimar costos ponderados
    cod_ordpros: Optional[List[str]] = Field(
        None, description="Cdigos de OPs seleccionadas para calcular costos ponderados"
    )

    # WIPs para estilos nuevos
    wips_textiles: Optional[List[WipSeleccionada]] = Field(
        None, description="WIPs textiles seleccionadas"
    )
    wips_manufactura: Optional[List[WipSeleccionada]] = Field(
        None, description="WIPs manufactura seleccionadas"
    )

    @field_validator("categoria_lote")
    def validar_categoria_lote(cls, v):
        categorias_validas = [
            "Micro Lote",
            "Lote Pequeo",
            "Lote Mediano",
            "Lote Grande",
            "Lote Masivo",
        ]
        if v not in categorias_validas:
            raise ValueError(f"Categora debe ser una de: {categorias_validas}")
        return v

    @field_validator("version_calculo", mode="before")
    def validar_version_calculo(cls, v):
        """Valida y normaliza la versin de clculo"""
        if isinstance(v, str):
            # Aceptar tanto "FLUIDO" (UI frontend) como "FLUIDA" (BD compatibility)
            if v.upper() in ("FLUIDO", "FLUIDA"):
                return VersionCalculo.FLUIDO
            elif v.lower() == "truncado":
                return VersionCalculo.TRUNCADO
            else:
                raise ValueError(f"Versin debe ser FLUIDO o truncado, recibido: {v}")
        return v


# =====================================================================
#  NUEVOS MODELOS PARA AUTO-COMPLETADO
# =====================================================================


class AutoCompletadoInfo(BaseModel):
    """ NUEVO: Informacin de auto-completado para estilos recurrentes"""

    disponible: bool = Field(..., description="Si el auto-completado est disponible")
    familia_producto: Optional[str] = Field(
        None, description="Familia de producto sugerida"
    )
    tipo_prenda: Optional[str] = Field(None, description="Tipo de prenda sugerido")


class InfoEstiloDetallada(BaseModel):
    """ NUEVO: Informacin detallada de un estilo"""

    codigo_estilo: str = Field(..., description="Cdigo del estilo")
    familia_producto: Optional[str] = Field(None, description="Familia de producto")
    tipo_prenda: Optional[str] = Field(None, description="Tipo de prenda")
    cliente_principal: Optional[str] = Field(None, description="Cliente principal")
    total_ops: int = Field(default=0, description="Total de OPs encontradas")
    volumen_total: int = Field(default=0, description="Volumen total histrico")
    esfuerzo_promedio: float = Field(default=6.0, description="Esfuerzo promedio")
    ultima_facturacion: Optional[datetime] = Field(
        None, description="ltima facturacin"
    )
    primera_facturacion: Optional[datetime] = Field(
        None, description="Primera facturacin"
    )
    categoria: TipoEstilo = Field(
        default=TipoEstilo.NUEVO, description="Categora del estilo"
    )
    encontrado: bool = Field(default=False, description="Si fue encontrado en BD")
    fuente: Optional[str] = Field(None, description="Fuente de la informacin")
    version_calculo: VersionCalculo = Field(
        default=VersionCalculo.FLUIDO, description="Versin usada"
    )


class VerificacionEstiloCompleta(BaseModel):
    """ NUEVO: Respuesta completa de verificacin de estilo"""

    codigo_estilo: str = Field(..., description="Cdigo del estilo verificado")
    existe_en_bd: bool = Field(..., description="Si existe en base de datos")
    es_estilo_nuevo: bool = Field(..., description="Si es considerado nuevo")
    categoria: TipoEstilo = Field(..., description="Categora determinada")
    volumen_historico: int = Field(default=0, description="Volumen histrico")
    version_calculo: VersionCalculo = Field(..., description="Versin de clculo usada")
    autocompletado: AutoCompletadoInfo = Field(
        ..., description="Info de auto-completado"
    )
    info_detallada: Optional[InfoEstiloDetallada] = Field(
        None, description="Informacin detallada si existe"
    )
    timestamp: datetime = Field(
        default_factory=datetime.now, description="Momento de la verificacin"
    )


# =====================================================================
#  NUEVOS MODELOS PARA OPS REALES
# =====================================================================


class CostosComponentesOP(BaseModel):
    """ NUEVO: Costos por componentes de una OP"""

    textil: float = Field(default=0.0, description="Costo textil unitario")
    manufactura: float = Field(default=0.0, description="Costo manufactura unitario")
    avios: float = Field(default=0.0, description="Costo avos unitario")
    materia_prima: float = Field(
        default=0.0, description="Costo materia prima unitario"
    )
    indirecto_fijo: float = Field(
        default=0.0, description="Costo indirecto fijo unitario"
    )
    gasto_admin: float = Field(default=0.0, description="Gasto administracin unitario")
    gasto_ventas: float = Field(default=0.0, description="Gasto ventas unitario")


class OpReal(BaseModel):
    """ NUEVO: Orden de produccin real utilizada en clculo"""

    cod_ordpro: str = Field(..., description="Cdigo de orden de produccin")
    estilo_propio: str = Field(..., description="Cdigo del estilo")
    cliente: str = Field(..., description="Cliente de la OP")
    fecha_facturacion: Optional[datetime] = Field(
        None, description="Fecha de facturacin"
    )
    prendas_requeridas: int = Field(..., ge=0, description="Cantidad de prendas")
    monto_factura: float = Field(..., ge=0, description="Monto total facturado")
    precio_unitario: float = Field(..., ge=0, description="Precio unitario")
    costos_componentes: CostosComponentesOP = Field(
        ..., description="Desglose de costos"
    )
    costo_total_unitario: float = Field(..., ge=0, description="Costo total unitario")
    esfuerzo_total: int = Field(
        default=6, ge=1, le=10, description="Esfuerzo total de la OP"
    )

    #  NUEVOS: Campos para lmites aplicados
    precio_ajustado: Optional[bool] = Field(
        default=False, description="Si el precio fue ajustado por lmites"
    )
    precio_original: Optional[float] = Field(
        None, description="Precio original antes de ajustes"
    )
    total_ajustes_aplicados: Optional[int] = Field(
        default=0, description="Nmero de ajustes aplicados"
    )


class EstadisticasOPs(BaseModel):
    """ NUEVO: Estadsticas de las OPs utilizadas"""

    total_ops: int = Field(..., ge=0, description="Total de OPs encontradas")
    costo_promedio: float = Field(..., ge=0, description="Costo promedio")
    costo_min: float = Field(..., ge=0, description="Costo mnimo")
    costo_max: float = Field(..., ge=0, description="Costo mximo")
    precio_promedio: Optional[float] = Field(None, ge=0, description="Precio promedio")
    precio_min: Optional[float] = Field(None, ge=0, description="Precio mnimo")
    precio_max: Optional[float] = Field(None, ge=0, description="Precio mximo")
    esfuerzo_promedio: float = Field(
        default=6.0, ge=1, le=10, description="Esfuerzo promedio"
    )
    ops_con_ajustes: Optional[int] = Field(
        default=0, description="OPs con ajustes aplicados"
    )
    rango_fechas: Optional[Dict[str, str]] = Field(
        None, description="Rango de fechas de las OPs"
    )


class ParametrosBusquedaOPs(BaseModel):
    """ NUEVO: Parmetros usados para buscar OPs"""

    codigo_estilo: Optional[str] = Field(None, description="Cdigo de estilo buscado")
    familia_producto: Optional[str] = Field(None, description="Familia de producto")
    tipo_prenda: Optional[str] = Field(None, description="Tipo de prenda")
    cliente: Optional[str] = Field(None, description="Cliente")
    version_calculo: VersionCalculo = Field(..., description="Versin de clculo usada")


class OpsDataResponse(BaseModel):
    """ NUEVO: Datos de OPs utilizadas"""

    ops_utilizadas: List[OpReal] = Field(..., description="Lista de OPs utilizadas")
    metodo_utilizado: str = Field(
        ..., description="Mtodo usado para encontrar las OPs"
    )
    estadisticas: EstadisticasOPs = Field(..., description="Estadsticas de las OPs")
    parametros_busqueda: ParametrosBusquedaOPs = Field(
        ..., description="Parmetros de bsqueda"
    )
    limites_aplicados: Optional[bool] = Field(
        default=False, description="Si se aplicaron lmites"
    )


class OpsUtilizadasResponse(BaseModel):
    """ NUEVO: Respuesta completa de OPs utilizadas"""

    ops_data: OpsDataResponse = Field(..., description="Datos de las OPs")
    timestamp: datetime = Field(
        default_factory=datetime.now, description="Momento de la consulta"
    )
    total_ops_encontradas: int = Field(
        ..., ge=0, description="Total de OPs encontradas"
    )
    parametros_entrada: Dict[str, Any] = Field(
        ..., description="Parmetros de entrada originales"
    )


# =====================================================================
# MODELOS DE BSQUEDA Y RESPUESTA (MEJORADOS)
# =====================================================================


class EstiloSimilar(BaseModel):
    """Estilo similar encontrado en bsqueda"""

    codigo: str = Field(..., description="Cdigo del estilo")
    familia_producto: str = Field(..., description="Familia de producto")
    tipo_prenda: str = Field(..., description="Tipo de prenda")
    temporada: Optional[str] = Field(None, description="Temporada")
    ops_encontradas: int = Field(..., description="Nmero de OPs encontradas")
    costo_promedio: float = Field(..., description="Costo promedio por prenda")


class WipDisponible(BaseModel):
    """WIP disponible con costos actuales"""

    wip_id: str = Field(..., description="ID de la WIP")
    nombre: str = Field(..., description="Nombre descriptivo")
    costo_actual: float = Field(..., description="Costo actual por prenda")
    disponible: bool = Field(..., description="Si est disponible")
    grupo: str = Field(..., description="Textil o Manufactura")


class ComponenteCosto(BaseModel):
    """ MODELO MEJORADO: Componente individual de costo"""

    nombre: str = Field(..., description="Nombre del componente")
    costo_unitario: float = Field(..., description="Costo unitario")
    fuente: FuenteCosto = Field(..., description="Fuente del costo")
    detalles: Optional[Dict[str, Any]] = Field(None, description="Detalles adicionales")
    validado: bool = Field(default=False, description="Si fue validado")
    ajustado_por_rango: bool = Field(
        default=False, description="Si fue ajustado por rango"
    )

    @field_validator("fuente", mode="before")
    def validar_fuente(cls, v):
        """Convierte string a enum si es necesario"""
        if isinstance(v, str):
            fuente_map = {
                "historico": FuenteCosto.HISTORICO,
                "wip": FuenteCosto.WIP,
                "formula": FuenteCosto.FORMULA,
                "ultimo_costo": FuenteCosto.ULTIMO_COSTO,
                "promedio_rango": FuenteCosto.PROMEDIO_RANGO,
            }
            return fuente_map.get(v, FuenteCosto.HISTORICO)
        return v


class InfoComercial(BaseModel):
    """ MODELO MEJORADO: Informacin comercial avanzada"""

    ops_utilizadas: int = Field(..., description="OPs utilizadas para clculo")
    historico_volumen: Dict[str, Any] = Field(..., description="Histrico de volumen")
    tendencias_costos: List[Dict[str, Any]] = Field(
        ..., description="Tendencias de costos"
    )
    analisis_competitividad: Optional[List[Dict[str, Any]]] = Field(
        None, description="Anlisis competitivo"
    )


# =====================================================================
#  NUEVOS MODELOS PARA RUTAS TEXTILES
# =====================================================================


class WipRecomendada(BaseModel):
    """ NUEVO: WIP recomendada en ruta textil"""

    wip_id: str = Field(..., description="ID de la WIP")
    nombre: str = Field(..., description="Nombre de la WIP")
    frecuencia_uso: int = Field(..., ge=0, description="Frecuencia de uso")
    costo_promedio: float = Field(..., ge=0, description="Costo promedio")
    ultimo_uso: Optional[datetime] = Field(None, description="ltimo uso registrado")
    recomendacion: str = Field(
        ..., description="Nivel de recomendacin (Alta/Media/Baja)"
    )


class RutaTextilResponse(BaseModel):
    """ NUEVO: Respuesta de ruta textil recomendada"""

    tipo_prenda: str = Field(..., description="Tipo de prenda")
    version_calculo: VersionCalculo = Field(..., description="Versin de clculo usada")
    wips_recomendadas: List[WipRecomendada] = Field(
        ..., description="WIPs recomendadas"
    )
    wips_textiles_recomendadas: List[WipRecomendada] = Field(
        ..., description="WIPs textiles especficas"
    )
    wips_manufactura_recomendadas: List[WipRecomendada] = Field(
        ..., description="WIPs manufactura especficas"
    )
    total_recomendadas: int = Field(..., ge=0, description="Total de WIPs recomendadas")
    metodo: str = Field(..., description="Mtodo usado para recomendacin")
    fecha_analisis: datetime = Field(
        default_factory=datetime.now, description="Fecha del anlisis"
    )
    timestamp: Optional[str] = Field(None, description="Timestamp adicional")


# =====================================================================
# MODELO DE RESPUESTA PRINCIPAL (MEJORADO)
# =====================================================================


class CotizacionResponse(BaseModel):
    """ MODELO PRINCIPAL MEJORADO: Respuesta de cotizacin (formato exacto frontend)"""

    # Identificacin
    id_cotizacion: str = Field(..., description="ID nico de cotizacin")
    fecha_cotizacion: datetime = Field(..., description="Fecha de cotizacin")

    # Inputs procesados (incluye version_calculo)
    inputs: CotizacionInput = Field(..., description="Datos de entrada")

    # Categorizacin automtica
    categoria_lote: str = Field(..., description="Categora del lote determinada")
    categoria_esfuerzo: Optional[int] = Field(None, description="Nivel de esfuerzo")
    categoria_estilo: TipoEstilo = Field(..., description="Categora del estilo")
    factor_marca: float = Field(..., description="Factor aplicado por marca")

    # Componentes de costo
    componentes: List[ComponenteCosto] = Field(
        ..., description="Desglose de componentes"
    )

    # Clculos individuales
    costo_textil: float = Field(..., description="Costo textil unitario")
    costo_manufactura: float = Field(..., description="Costo manufactura unitario")
    costo_avios: float = Field(..., description="Costo avos unitario")
    costo_materia_prima: float = Field(..., description="Costo materia prima unitario")
    costo_indirecto_fijo: float = Field(
        ..., description="Costo indirecto fijo unitario"
    )
    gasto_administracion: float = Field(
        ..., description="Gasto administracin unitario"
    )
    gasto_ventas: float = Field(..., description="Gasto ventas unitario")
    costo_base_total: float = Field(..., description="Costo base total unitario")

    # Vector de ajuste
    factor_lote: float = Field(..., description="Factor de lote aplicado")
    factor_esfuerzo: float = Field(..., description="Factor de esfuerzo aplicado")
    factor_estilo: float = Field(..., description="Factor de estilo aplicado")
    vector_total: float = Field(..., description="Vector total de ajuste")

    # Resultado final
    precio_final: float = Field(..., description="Precio final por prenda")
    margen_aplicado: float = Field(..., description="Margen aplicado en porcentaje")

    # Validaciones y alertas
    validaciones: List[str] = Field(..., description="Lista de validaciones exitosas")
    alertas: List[str] = Field(..., description="Lista de alertas/advertencias")

    # Info comercial avanzada
    info_comercial: InfoComercial = Field(..., description="Informacin comercial")

    # Metadatos de procesamiento
    metodos_usados: List[str] = Field(..., description="Mtodos utilizados")
    registros_encontrados: int = Field(..., description="Registros encontrados en BD")
    precision_estimada: float = Field(..., description="Precisin estimada del clculo")

    #  CAMPOS MEJORADOS Y NUEVOS
    version_calculo_usada: VersionCalculo = Field(
        ..., description="Versin de clculo aplicada"
    )
    codigo_estilo: Optional[str] = Field(None, description="Cdigo del estilo")
    volumen_historico: Optional[int] = Field(
        None, description="Volumen histrico del estilo"
    )
    estrategia_costos: Optional[str] = Field(
        None, description="Estrategia de costos usada"
    )
    configuracion_wips: Optional[List[WipConfiguracion]] = Field(
        default_factory=list, description="WIPs configuradas"
    )
    metadatos_adicionales: Optional[Dict[str, Any]] = Field(
        default_factory=dict, description="Metadatos adicionales"
    )
    timestamp: Optional[datetime] = Field(
        None, description="Timestamp de la cotizacin"
    )
    usuario: Optional[str] = Field(
        None, description="Usuario que realiz la cotizacin"
    )


# =====================================================================
# MODELOS DE UTILIDAD Y CONFIGURACIN (MEJORADOS)
# =====================================================================


class HealthCheck(BaseModel):
    """Respuesta de health check"""

    status: str = Field(..., description="Estado del servicio")
    database: str = Field(..., description="Estado de la base de datos")
    tablas: Dict[str, int] = Field(..., description="Conteo de registros por tabla")
    timestamp: datetime = Field(..., description="Timestamp del check")


class ConfiguracionResponse(BaseModel):
    """Respuesta de configuracin del sistema"""

    rangos_lote: Dict[str, Any] = Field(..., description="Rangos de lote")
    factores_esfuerzo: Dict[str, Any] = Field(..., description="Factores de esfuerzo")
    factores_estilo: Dict[str, Any] = Field(..., description="Factores de estilo")
    factores_marca: Dict[str, float] = Field(..., description="Factores de marca")
    wips_disponibles: Dict[str, List[str]] = Field(..., description="WIPs disponibles")
    rangos_seguridad: Dict[str, Any] = Field(..., description="Rangos de seguridad")


class WipsDisponiblesResponse(BaseModel):
    """ MODELO MEJORADO: Respuesta de WIPs disponibles"""

    wips_textiles: List[WipDisponible] = Field(..., description="WIPs textiles")
    wips_manufactura: List[WipDisponible] = Field(..., description="WIPs manufactura")
    total_disponibles: int = Field(..., description="Total de WIPs disponibles")
    fuente: str = Field(..., description="Fuente de los datos")
    fecha_actualizacion: datetime = Field(..., description="Fecha de actualizacin")
    metodo_analisis: Optional[str] = Field(None, description="Mtodo de anlisis usado")
    tipo_prenda_filtro: Optional[str] = Field(
        None, description="Tipo de prenda filtrado"
    )
    version_calculo: VersionCalculo = Field(
        default=VersionCalculo.FLUIDO, description="Versin de clculo usada"
    )


class ErrorResponse(BaseModel):
    """Respuesta de error estndar"""

    error: str = Field(..., description="Tipo de error")
    mensaje: str = Field(..., description="Mensaje descriptivo")
    detalles: Optional[Dict[str, Any]] = Field(None, description="Detalles adicionales")
    timestamp: datetime = Field(
        default_factory=datetime.now, description="Timestamp del error"
    )


# =====================================================================
#  NUEVOS MODELOS PARA DATOS MAESTROS
# =====================================================================


class ClientesResponse(BaseModel):
    """ NUEVO: Respuesta de clientes disponibles"""

    clientes: List[str] = Field(..., description="Lista de clientes")
    total: int = Field(..., ge=0, description="Total de clientes")
    fuente: str = Field(..., description="Fuente de los datos")
    version_calculo: VersionCalculo = Field(..., description="Versin de clculo usada")
    timestamp: datetime = Field(
        default_factory=datetime.now, description="Timestamp de la consulta"
    )


class FamiliasResponse(BaseModel):
    """ NUEVO: Respuesta de familias de productos"""

    familias: List[str] = Field(..., description="Lista de familias")
    total: int = Field(..., ge=0, description="Total de familias")
    fuente: str = Field(..., description="Fuente de los datos")
    version_calculo: VersionCalculo = Field(..., description="Versin de clculo usada")
    timestamp: datetime = Field(
        default_factory=datetime.now, description="Timestamp de la consulta"
    )


class TiposPrendaResponse(BaseModel):
    """ NUEVO: Respuesta de tipos de prenda"""

    tipos: List[str] = Field(..., description="Lista de tipos")
    familia: str = Field(..., description="Familia de producto")
    total: int = Field(..., ge=0, description="Total de tipos")
    fuente: str = Field(..., description="Fuente de los datos")
    version_calculo: VersionCalculo = Field(..., description="Versin de clculo usada")
    timestamp: datetime = Field(
        default_factory=datetime.now, description="Timestamp de la consulta"
    )


# =====================================================================
#  MODELO PARA ANLISIS HISTRICO
# =====================================================================


class AnalisisHistoricoData(BaseModel):
    """ NUEVO: Datos de anlisis histrico"""

    total_ops: int = Field(..., ge=0, description="Total de OPs")
    total_prendas: int = Field(..., ge=0, description="Total de prendas")
    precio_promedio: float = Field(..., ge=0, description="Precio promedio")
    costo_promedio: float = Field(..., ge=0, description="Costo promedio")
    esfuerzo_promedio: float = Field(..., ge=1, le=10, description="Esfuerzo promedio")
    clientes_unicos: int = Field(..., ge=0, description="Clientes nicos")


class AnalisisHistoricoResponse(BaseModel):
    """ NUEVO: Respuesta de anlisis histrico"""

    analisis: AnalisisHistoricoData = Field(..., description="Datos del anlisis")
    parametros: Dict[str, Any] = Field(..., description="Parmetros usados")
    fuente: str = Field(..., description="Fuente de los datos")
    metodo: str = Field(..., description="Mtodo de anlisis")
    timestamp: datetime = Field(
        default_factory=datetime.now, description="Timestamp del anlisis"
    )
