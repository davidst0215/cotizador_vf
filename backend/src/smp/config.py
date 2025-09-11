"""
=====================================================================
CONFIGURACIÓN Y FACTORES - BACKEND TDV COTIZADOR v2.0
=====================================================================
Configuración centralizada basada en análisis real de TDV
"""

from typing import Any, Dict
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Configuración principal de la aplicación"""

    # Base de datos
    db_server: str = "131.107.20.77"
    db_port: int = 1433
    db_username: str = "CHSAYA01"
    db_password: str = "NewServerAz654@!"
    db_database: str = "TDV"

    # API
    api_title: str = "Cotizador TDV Expert"
    api_version: str = "2.0"
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    debug: bool = True
    log_level: str = "INFO"

    # CORS
    cors_origins: str = "http://localhost:3000,http://127.0.0.1:3000"

    # Cache
    cache_ttl: int = 3600

    class Config:
        env_file = ".env"


# =====================================================================
# FACTORES DE AJUSTE (BASADOS EN IMÁGENES PROPORCIONADAS)
# =====================================================================

Factores = Dict[str, Dict[str, Any]]


class FactoresTDV:
    """Factores de ajuste basados en análisis TDV real"""

    # Rangos de lote (cantidad de prendas)
    RANGOS_LOTE: Factores = {
        "Micro Lote": {"min": 1, "max": 50, "factor": 1.15},
        "Lote Pequeño": {"min": 51, "max": 500, "factor": 1.10},
        "Lote Mediano": {"min": 501, "max": 1000, "factor": 1.05},
        "Lote Grande": {"min": 1001, "max": 4000, "factor": 1.00},
        "Lote Masivo": {"min": 4001, "max": 999999, "factor": 0.90},
    }

    # Factores de esfuerzo (de imagen 1)
    FACTORES_ESFUERZO: Factores = {
        "Bajo": {"rango": (0, 5), "factor": 0.90},
        "Medio": {"rango": (6, 6), "factor": 1.00},
        "Alto": {"rango": (7, 10), "factor": 1.15},
    }

    # Factores de estilo (de imagen 2)
    FACTORES_ESTILO: Factores = {
        "Muy Recurrente": {
            "descripcion": "Más de 4,000 prendas fabricadas",
            "factor": 0.95,
        },
        "Recurrente": {
            "descripcion": "Menos de 4,000 prendas fabricadas",
            "factor": 1.00,
        },
        "Nuevo": {"descripcion": "Estilo que aún no ha sido fabricado", "factor": 1.05},
    }

    # Factores de marca (de imagen 3)
    FACTORES_MARCA: Dict[str, float] = {
        "LACOSTE": 1.05,
        "GREYSON": 1.05,
        "GREYSON CLOTHIERS": 1.10,
        "LULULEMON": 0.95,
        "PATAGONIA": 0.95,
        "OTRAS MARCAS": 1.10,  # Default para cualquier otra marca
    }

    # WIPs disponibles (basado en análisis previo)
    WIPS_TEXTILES = ["16", "14", "19a", "19c", "24"]
    WIPS_MANUFACTURA = ["34", "40", "44", "37", "45", "49"]

    # ✅ NUEVO: Mapeo de nombres específicos de WIPs
    NOMBRES_WIPS = {
        # WIPs Textiles
        "16": "WIP 16 - Hilado",
        "14": "WIP 14 - Teñido",
        "19a": "WIP 19a - Acabados",
        "19c": "WIP 19c - Despacho",
        "24": "WIP 24 - Control",
        # WIPs Manufactura
        "34": "WIP 34 - Corte",
        "40": "WIP 40 - Confección",
        "44": "WIP 44 - Bordado",
        "37": "WIP 37 - Acabado",
        "45": "WIP 45 - Planchado",
        "49": "WIP 49 - Empaque",
    }

    # Rangos de seguridad por componente (validación experta)
    RANGOS_SEGURIDAD: Factores = {
        "costo_textil": {"min": 0.05, "max": 10},
        "costo_manufactura": {"min": 0.05, "max": 10},
        "costo_materia_prima": {"min": 0.05, "max": 10},
        "costo_indirecto_fijo": {"min": 0.05, "max": 10},
        "gasto_administracion": {"min": 0.05, "max": 10},
        "gasto_ventas": {"min": 0.05, "max": 10},
        "costo_avios": {"min": 0.05, "max": 10},
    }

    @classmethod
    def categorizar_lote(cls, cantidad: int) -> tuple[str, float]:
        """Categoriza lote y retorna nombre y factor"""
        for categoria, config in cls.RANGOS_LOTE.items():
            if config["min"] <= cantidad <= config["max"]:
                return categoria, config["factor"]
        return "Lote Grande", 1.00  # Default

    @classmethod
    def obtener_factor_esfuerzo(cls, esfuerzo_total: int) -> tuple[str, float]:
        """Obtiene factor de esfuerzo basado en esfuerzo_total"""
        for categoria, config in cls.FACTORES_ESFUERZO.items():
            min_val, max_val = config["rango"]
            if min_val <= esfuerzo_total <= max_val:
                return categoria, config["factor"]
        return "Medio", 1.00  # Default

    @classmethod
    def obtener_factor_estilo(cls, categoria: str) -> float:
        """Obtiene factor de estilo"""
        return cls.FACTORES_ESTILO.get(categoria, {}).get("factor", 1.05)

    @classmethod
    def obtener_factor_marca(cls, cliente: str) -> float:
        """Obtiene factor de marca basado en cliente"""
        cliente_upper = cliente.upper().strip()

        # Buscar coincidencia exacta o parcial
        for marca_key, factor in cls.FACTORES_MARCA.items():
            if marca_key == "OTRAS MARCAS":
                continue
            if marca_key in cliente_upper or cliente_upper in marca_key:
                return factor

        # Si no encuentra coincidencia, usar "OTRAS MARCAS"
        return cls.FACTORES_MARCA["OTRAS MARCAS"]

    @classmethod
    def validar_rango_seguridad(
        cls, valor: float, componente: str
    ) -> tuple[float, bool]:
        """Valida y ajusta valor según rango de seguridad"""
        if componente not in cls.RANGOS_SEGURIDAD:
            return valor, False

        rango = cls.RANGOS_SEGURIDAD[componente]
        valor_original = valor

        if valor < rango["min"]:
            valor = rango["min"]
        elif valor > rango["max"]:
            valor = rango["max"]

        return valor, valor != valor_original


# =====================================================================
# CONFIGURACIÓN DE BASE DE DATOS
# =====================================================================


class DatabaseConfig:
    """Configuración de conexión a base de datos"""

    @staticmethod
    def get_connection_string(settings: Settings) -> str:
        """Genera string de conexión para SQL Server"""
        return (
            f"DRIVER={{SQL Server}};"
            f"SERVER={settings.db_server},{settings.db_port};"
            f"UID={settings.db_username};"
            f"PWD={settings.db_password};"
            f"DATABASE={settings.db_database};"
            f"TrustServerCertificate=yes;"
            f"Connection Timeout=30;"
            f"Command Timeout=60"
        )


# Instancia global de configuración
settings = Settings()
factores = FactoresTDV()
db_config = DatabaseConfig()
