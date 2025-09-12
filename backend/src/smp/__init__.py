import logging
import sys
import os

from pathlib import Path


__version__ = "0.1.0"

# CONFIGURAR LOGGING SIN EMOJIS Y CON UTF-8
APP = "tdv_cotizador"
WIN = sys.platform.startswith("win")
HOME = Path.home()
BASE = (
    Path(
        os.environ.get("LOCALAPPDATA")
        or os.environ.get("APPDATA")
        or HOME / "AppData" / "Local"
    )
    if WIN
    else Path(
        os.environ.get("XDG_STATE_HOME")
        or os.environ.get("XDG_DATA_HOME")
        or HOME / ".local" / "state"
    )
)
LOGDIR = BASE / APP / ("Logs" if WIN else "logs")
LOGDIR.mkdir(parents=True, exist_ok=True)
LOGFILE = LOGDIR / f"{APP}.log"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler(LOGFILE),
        logging.StreamHandler(sys.stdout if WIN else sys.stderr),
    ],
)
