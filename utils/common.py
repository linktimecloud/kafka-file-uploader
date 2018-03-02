import codecs
import logging
import re
import os

from logging import Formatter

UTF_8 = 'utf-8'
DEFAULT_LOGGER_NAME = "default"
DEFAULT_LOGGER_LEVEL = logging.DEBUG
DEBUG_LOG_FORMAT = (
    '-' * 80 + '\n' +
    '%(levelname)s in %(module)s [%(pathname)s:%(lineno)d]:\n' +
    '%(message)s\n' +
    '-' * 80
)
PROD_LOG_FORMAT = '[%(asctime)s] %(levelname)s in %(module)s: %(message)s'


def get_logger(logger_name=DEFAULT_LOGGER_NAME, level=DEFAULT_LOGGER_LEVEL):
    _logger = logging.getLogger(logger_name)
    _handler = logging.StreamHandler()
    _logger.addHandler(_handler)
    try:
        _logger.setLevel(level)
    except Exception:
        _logger.setLevel(DEFAULT_LOGGER_LEVEL)
    if level == logging.DEBUG:
        _handler.setFormatter(Formatter(DEBUG_LOG_FORMAT))
    else:
        _handler.setFormatter(Formatter(PROD_LOG_FORMAT))
    return _logger


def read_file(filename):
    logger = get_logger()
    try:
        with codecs.open(filename, 'r', encoding=UTF_8) as fp:
            return fp.readlines()
    except Exception as e:
        logger.exception(str(e))
        return None


def secure_file_name(filename):
    """Ensure user submitted string not contains '/' or multi '-'.
    Args:
        filename: submitted string
    Returns:
        replaced slash string
    """
    name, extension = os.path.splitext(filename)
    name = re.sub('[" "/\--.]+', '-', name)
    name = re.sub(r':-', ':', name)
    name = re.sub(r'^-|-$', '', name)
    return "".join((name, extension))
