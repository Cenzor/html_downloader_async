import logging
from logging import Formatter
from logging.handlers import RotatingFileHandler


def configure_logger(module_name: str) -> logging.RootLogger:
    """
    Функция конфигурирует и возвращает логгер
    """
    logger = logging.getLogger(module_name)
    logger.setLevel(logging.DEBUG)
    formatter = Formatter("%(asctime)s - [%(levelname)s] - %(name)s "
                          "(%(filename)s).%(funcName)s(%(lineno)d): "
                          "%(message)s")
    # configure file log
    filename = 'html_downloader.log'
    fh = RotatingFileHandler(filename, maxBytes=30000000, backupCount=10)
    fh.setLevel(logging.DEBUG)
    fh.setFormatter(formatter)
    logger.addHandler(fh)
    # configure console log
    ch = logging.StreamHandler()
    ch.setLevel(logging.CRITICAL)
    ch.setFormatter(formatter)
    logger.addHandler(ch)
    return logger
