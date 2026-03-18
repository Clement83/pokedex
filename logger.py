"""
Module de logging partagé – écrit dans debug.log à la racine du projet.
Usage :
    from logger import log
    log("mon message")
"""
import logging
import os
from pathlib import Path

LOG_PATH = Path(__file__).parent / "debug.log"

logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s  %(levelname)-7s  %(message)s",
    datefmt="%H:%M:%S",
    handlers=[
        logging.FileHandler(LOG_PATH, encoding="utf-8"),
        logging.StreamHandler(),   # garde aussi l'affichage console
    ],
)

_logger = logging.getLogger("launcher")


def log(msg: str, level: str = "info"):
    getattr(_logger, level.lower(), _logger.info)(msg)
    # Forcer l'écriture immédiate sur disque (utile sur Odroid)
    for h in _logger.handlers + logging.root.handlers:
        h.flush()
