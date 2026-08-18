import logging
import time
from logging.handlers import RotatingFileHandler
from pathlib import Path

from .config import settings

log_folder = Path(settings.log_path)
log_folder.mkdir(parents=True, exist_ok=True)  # 确保目录存在


class InfoWarningFilter(logging.Filter):
    def filter(self, record):
        return record.levelno < logging.ERROR  # 只允许低于 ERROR 的级别


def _set_default_handler(logfile_prefix: str = "log"):
    formatter = logging.Formatter(
        "%(asctime)s - %(levelname)s - %(filename)s - %(funcName)s - %(lineno)s - %(message)s"
    )
    log_file = log_folder / f"{logfile_prefix}-{time.strftime('%Y-%m-%d')}.log"
    handler = RotatingFileHandler(
        log_file, maxBytes=1024 * 1024, backupCount=10, encoding="utf-8"
    )
    handler.setFormatter(formatter)
    handler.setLevel(logging.INFO)
    return handler


def setup_loggers(app):
    """配置日志器，将 INFO 及以上（不含 ERROR）写入 info.log，ERROR 及以上写入 error.log"""
    # ---------- 获取根日志器（或自定义 logger）并添加 handler ----------
    logger = logging.getLogger()  # 根 logger，也可用 logging.getLogger('myapp')
    logger.setLevel(logging.INFO)  # 全局最低级别，保证 info 能进入

    # ---------- INFO 级别日志文件 ----------
    info_handler = _set_default_handler("flask-info")
    info_handler.setLevel(logging.INFO)
    info_handler.addFilter(InfoWarningFilter())

    # ---------- ERROR 级别日志文件 ----------
    error_handler = _set_default_handler("flask-error")
    error_handler.setLevel(logging.ERROR)  # 只记录 ERROR 及以上

    # 如果传入了 app，则使用 app.logger；否则回退到 'flask.app'
    if app is not None:
        f_logger = app.logger
    else:
        f_logger = logging.getLogger("flask.app")  # 保留兼容性
    f_logger.handlers.clear()
    f_logger.propagate = False
    f_logger.setLevel(logging.INFO)
    f_logger.addHandler(error_handler)
    f_logger.addHandler(info_handler)
    api_logger = logging.getLogger("api_log")
    api_logger.propagate = False  # 关闭传播
    f_logger.setLevel(logging.INFO)
    api_handler = _set_default_handler("api-info")
    api_logger.addHandler(api_handler)
    # logger.propagate = False
