from flask import Flask

# from .common.task.task_app import celery_init_app
from .core.appinit.init_db import ensure_database_initialized
from .core.config import settings
from .core.extensions import db
from .core.logger import setup_loggers


def create_app():
    app = Flask(
        __name__,
        instance_path=settings.instance_path,
        static_folder=settings.web_folder,
        static_url_path="",
    )

    # 从默认配置对象中加载配置
    # 将配置对象的key转成大写后加载到app.config
    app.config.update({k.upper(): v for k, v in settings.model_dump().items()})
    app.json.ensure_ascii = False
    db.init_app(app)

    from .core.appinit.handlers import register_handlers

    register_handlers(app)  # 集中注册所有处理器
    setup_loggers(app)

    ensure_database_initialized(app)  # create database
    from ..app.api import routes

    app.register_blueprint(routes.root)
    app.register_blueprint(routes.api)

    # celery_init_app(app)
    return app
