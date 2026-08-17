from pathlib import Path

from sqlalchemy.exc import OperationalError

from ..extensions import db


def _create_all_safe():
    """建表并容忍多 worker 并发启动时的“表已存在”竞态"""
    try:
        db.create_all()
    except OperationalError:
        db.session.rollback()


def ensure_database_initialized(app):
    from ...model.entities import Collect

    """确保数据库和核心表存在，否则自动创建"""
    db_path = app.config.get("SQLALCHEMY_DATABASE_URI", "").replace("sqlite:///", "")
    # 1. 检查文件是否存在（快速过滤）
    file_path = Path(app.instance_path) / Path(db_path)
    if not file_path.exists():
        print("📁 数据库文件不存在，正在自动创建...")
        with app.app_context():
            _create_all_safe()
        print("✅ 数据库及表结构创建成功！")
        return

    # 2. 文件存在，但检查核心表是否建好（防止空文件或手动删表的情况）
    with app.app_context():
        # 用 Inspector 检查核心模型（如 User 表）是否存在
        from sqlalchemy import inspect

        inspector = inspect(db.engine)
        if not inspector.has_table(Collect.__tablename__):
            print("⚠️ 数据库存在但缺少核心表，正在自动修补...")
            _create_all_safe()
            print("✅ 表结构修补完成！")
        else:
            print("✅ 数据库已就绪，直接启动应用。")
