import logging
import time
from logging.handlers import RotatingFileHandler
from pathlib import Path

from .config import settings


def get_log_handler():
    # 日志地址
    # 文件名，以日期作为文件名
    log_file_name = (
        "logger-" + time.strftime("%Y-%m-%d", time.localtime(time.time())) + ".log"
    )
    # 创建日志文件
    log_file_folder = Path(settings.log_path)
    log_file_str = log_file_folder / log_file_name

    # 创建日志记录器，指明日志保存路径,每个日志的大小，保存日志的上限
    file_log_handler = RotatingFileHandler(
        log_file_str, maxBytes=1024 * 1024, backupCount=10, encoding="UTF-8"
    )
    # 设置日志的格式                   发生时间    日志等级     调用的文件名          函数名          行数        日志信息
    formatter = logging.Formatter(
        "%(asctime)s - %(levelname)s - %(filename)s - %(funcName)s - %(lineno)s - %(message)s"
    )
    # 将日志记录器指定日志的格式
    file_log_handler.setFormatter(formatter)
    logging.basicConfig(level=logging.INFO, handlers=[file_log_handler])

    return file_log_handler
