from pathlib import Path
from types import SimpleNamespace

from flask import current_app

from ..core.config import settings


def path_info(full_path):
    """拆分路径为目录、文件名、扩展名"""
    path = Path(full_path)
    return SimpleNamespace(
        **{
            "full_path": str(path),
            "directory": str(path.parent),
            "filename": path.name,
            "stem": path.stem,
            "suffix": path.suffix,
            "is_file": path.is_file(),  # 可选：检查是否是文件
        }
    )


def path_info(path: Path):
    return SimpleNamespace(
        **{
            "full_path": str(path),
            "directory": str(path.parent),
            "filename": path.name,
            "stem": path.stem,
            "suffix": path.suffix,
            "is_file": path.is_file(),  # 可选：检查是否是文件
        }
    )


def network_path(path: Path):
    baseurl = current_app.config.get("APP_ROOT")
    info = path_info(path)
    url = info.full_path.replace(path_info(settings.file_path).full_path, "").replace(
        "\\", "/"
    )
    if url[0] == "/":
        url = url[1:]
    return f"{baseurl}{url}"
