import logging
import sys

__version__ = "0.1.0"

# CONFIGURAR LOGGING SIN EMOJIS Y CON UTF-8
log_file = "logs/tdv_cotizador.log"
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler(log_file),
        logging.StreamHandler(sys.stdout)
        if sys.platform.startswith("win")
        else logging.StreamHandler(),
    ],
)
