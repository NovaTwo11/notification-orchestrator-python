import logging
import sys
from pythonjsonlogger import jsonlogger

def setup_logging():
    """Configura el logging con formato JSON"""
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)

    # Handler para stdout
    handler = logging.StreamHandler(sys.stdout)

    # Formato JSON
    formatter = jsonlogger.JsonFormatter(
        '%(asctime)s %(name)s %(levelname)s %(message)s'
    )
    handler.setFormatter(formatter)

    logger.addHandler(handler)