from datetime import datetime
from pathlib import Path

from pydantic_settings import (
    BaseSettings,
    SettingsConfigDict,
)

ROOT_PATH = Path(__file__).resolve().parent.parent.parent.parent

"""
优先级 构造函数参数（最高优先级）> 环境变量 > .env 文件 > 字段默认值（最低优先级）
"""


class Settings(BaseSettings):
    app_base_path: str = str(ROOT_PATH)
    log_path: str = str(Path(app_base_path) / "log")
    web_folder: str = str(Path(app_base_path) / "web")

    instance_path: str = str(Path(app_base_path) / "data")
    file_path: str = str(Path(app_base_path) / "file")

    upload_folder: str = str(Path(file_path) / "upload")
    temp_folder: str = str(Path(file_path) / "temp")
    date_temp_folder: str = str(
        Path(file_path) / "temp" / Path(f"{datetime.now().strftime('%Y/%m/%d')}")
    )
    """
    应用配置项
    """
    app_name: str = "DefaultApp"
    debug: bool = False
    testing: bool = False
    sqlalchemy_database_uri: str = "sqlite:///database.db"
    sqlalchemy_track_modifications: bool = False

    # 使用新的 SettingsConfigDict（推荐）
    model_config = SettingsConfigDict(
        env_file=ROOT_PATH / "configs" / ".env",
        env_file_encoding="utf-8",
        case_sensitive=False,  # 环境变量不区分大小写
        extra="forbid",  # 禁止额外字段
    )

    # 初始化
    Path(instance_path).mkdir(parents=True, exist_ok=True, mode=0o750)
    Path(file_path).mkdir(parents=True, exist_ok=True)
    Path(log_path).mkdir(parents=True, exist_ok=True)
    Path(upload_folder).mkdir(parents=True, exist_ok=True)
    Path(temp_folder).mkdir(parents=True, exist_ok=True)
    Path(date_temp_folder).mkdir(parents=True, exist_ok=True)


settings = Settings()
