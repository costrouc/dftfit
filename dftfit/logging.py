import logging

LOG_LEVELS = {'DEBUG', 'INFO', 'WARNING', 'CRITICAL', 'ERROR'}

# Possibly add file handler
def init_logging(level='WARNING'):
    handler = logging.StreamHandler()
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)
    logging.basicConfig(handlers=[handler], level=level.upper())
