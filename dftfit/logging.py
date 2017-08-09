"""Implements a logger for dftfit

"""
from __future__ import absolute_import

from logging import (
    getLogger,
    FileHandler,
    StreamHandler,
    Formatter,
    DEBUG,
    INFO,
    WARNING
)


def create_logger(log_filename, debug=False):
    """Creates a logger for dftfit

    Using the python logging module greatly imporoves debugging
    capabilities along with providing a well establised api

    """
    logger = getLogger('dftfit')

    if debug == True:
        logger.setLevel(DEBUG)
    else:
        logger.setLevel(INFO)

    file_handler = FileHandler(log_filename, mode='w')
    file_handler.setLevel(DEBUG)

    stream_handler = StreamHandler()
    stream_handler.setLevel(INFO)

    formatter = Formatter('%(levelname)s: %(message)s')
    file_handler.setFormatter(formatter)
    stream_handler.setFormatter(formatter)

    logger.addHandler(file_handler)
    logger.addHandler(stream_handler)

    return logger
