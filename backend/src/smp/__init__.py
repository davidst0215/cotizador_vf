import logging
import sys

from pathlib import Path
from platformdirs import user_log_dir


__version__ = "0.1.0"

# log config
APP = "tdv_cotizador"
logfile = Path(user_log_dir(APP)) / f"{APP}.log"
logfile.parent.mkdir(parents=True, exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler(logfile),
        logging.StreamHandler(
            sys.stdout if sys.platform.startswith("win") else sys.stderr
        ),
    ],
)
