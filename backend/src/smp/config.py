"""
=====================================================================
CONFIGURACIN Y FACTORES - BACKEND TDV COTIZADOR v2.0
=====================================================================
Configuracin centralizada basada en anlisis real de TDV
"""

from typing import Any, Dict, Optional
from pydantic_settings import BaseSettings
from pydantic import ConfigDict, model_validator


class Settings(BaseSettings):
    """Configuracin principal de la aplicacin"""

    model_config = ConfigDict(env_file=".env", extra="ignore")

    # Base de datos
    db_host: str = "127.0.0.1"
    db_port: int
    db_user: str
    db_password: str
    db_name: str
    db_schema: str

    # Connection string or params dict
    connection_string: Optional[str | dict] = None
    connection_driver: Optional[str] = None

    # PostgreSQL SSL settings
    pgsslmode: Optional[str] = None
    pgsslcert: Optional[str] = None
    pgsslkey: Optional[str] = None
    pgsslrootcert: Optional[str] = None

    @model_validator(mode="after")
    def _build(self):
        #  DETECTAR PostgreSQL por puerto (5432) o por variables de entorno
        is_postgres = self.db_port == 5432 or self.pgsslmode is not None

        if not self.connection_driver:
            self.connection_driver = "psycopg2" if is_postgres else "{SQL Server}"

        if not self.connection_string:
            if is_postgres:
                # PostgreSQL: usar diccionario de parmetros en lugar de DSN string
                # Esto evita problemas con espacios en rutas de certificados
                self.connection_string = {
                    'dbname': self.db_name,
                    'user': self.db_user,
                    'host': self.db_host,
                    'port': self.db_port,
                }

                if self.db_password:
                    self.connection_string['password'] = self.db_password

                # Agregar SSL settings
                if self.pgsslmode:
                    self.connection_string['sslmode'] = self.pgsslmode
                else:
                    self.connection_string['sslmode'] = 'disable'

                if self.pgsslcert:
                    self.connection_string['sslcert'] = self.pgsslcert
                if self.pgsslkey:
                    self.connection_string['sslkey'] = self.pgsslkey
                if self.pgsslrootcert:
                    self.connection_string['sslrootcert'] = self.pgsslrootcert
            else:
                # SQL Server connection string
                self.connection_string = (
                    f"DRIVER={self.connection_driver};"
                    f"SERVER={self.db_host},{self.db_port};"
                    f"UID={self.db_user};"
                    f"PWD={self.db_password};"
                    f"DATABASE={self.db_name};"
                    f"TrustServerCertificate=yes;"
                    f"Connection Timeout=30;"
                    f"Command Timeout=60"
                )
        return self

    # API
    api_title: str = "Cotizador TDV Expert"
    api_version: str = "2.0"
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    debug: bool = True
    log_level: str = "INFO"

    # CORS
    cors_origins: str = "http://localhost:3000,http://localhost:3001,http://localhost:3002,http://127.0.0.1:3000,http://127.0.0.1:3001,http://127.0.0.1:3002"

    # Cache
    cache_ttl: int = 3600


# =====================================================================
# FACTORES DE AJUSTE (BASADOS EN IMGENES PROPORCIONADAS)
# =====================================================================

Factores = Dict[str, Dict[str, Any]]


class FactoresTDV:
    """Factores de ajuste basados en anlisis TDV real"""

    # Rangos de lote (cantidad de prendas)
    RANGOS_LOTE: Factores = {
        "Micro Lote": {"min": 1, "max": 50, "factor": 1.15},
        "Lote Pequeo": {"min": 51, "max": 500, "factor": 1.10},
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
            "descripcion": "Ms de 4,000 prendas fabricadas",
            "factor": 0.95,
        },
        "Recurrente": {
            "descripcion": "Menos de 4,000 prendas fabricadas",
            "factor": 1.00,
        },
        "Nuevo": {"descripcion": "Estilo que an no ha sido fabricado", "factor": 1.05},
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

    # WIPs disponibles (basado en anlisis previo)
    WIPS_TEXTILES = ["10c", "14", "16", "19a", "19c", "24"]
    WIPS_MANUFACTURA = ["34", "37", "40", "43", "44", "45", "49", "50"]

    #  NUEVO: Mapeo de nombres especficos de WIPs (de tabla costos_procesos_tdv)
    NOMBRES_WIPS = {
        # WIPs Textiles
        "10c": "Abastecimiento de Hilo",
        "14": "Teido de Hilado",
        "16": "Tejido de Tela y Rectilneos",
        "19a": "Teido",
        "19c": "Despacho",
        "24": "Estampado Tela",
        # WIPs Manufactura
        "34": "Corte",
        "37": "Bordado Pieza",
        "40": "Costura",
        "43": "Bordado Prenda",
        "44": "Estampado Prendas",
        "45": "Lavado en Prenda (Despus de estampar)",
        "49": "Acabado",
        "50": "Movimiento Logstico",
    }

    # Rangos de seguridad por componente (validacin experta)
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
        """Valida y ajusta valor segn rango de seguridad"""
        # Validar y convertir valor a float si es necesario
        try:
            if valor is None:
                valor = 0.0
            else:
                valor = float(valor)
        except (ValueError, TypeError):
            # Si no se puede convertir, retornar 0.0
            return 0.0, False

        if componente not in cls.RANGOS_SEGURIDAD:
            return valor, False

        rango = cls.RANGOS_SEGURIDAD[componente]
        valor_original = valor

        if valor < rango["min"]:
            valor = rango["min"]
        elif valor > rango["max"]:
            valor = rango["max"]

        return valor, valor != valor_original


# Instancia global de configuracin
settings = Settings()
factores = FactoresTDV()
