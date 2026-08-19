import time
from enum import StrEnum

from sqlalchemy import Enum as SA_Enum
from sqlalchemy.inspection import inspect
from sqlalchemy.orm import Mapped, mapped_column

from ..core.extensions import db


class FolderTypeEnum(StrEnum):
    FOLDER = "folder"
    BOOKMARK = "bookmark"


class BaseModelMixin:
    def to_dict(self, exclude=None):
        if exclude is None:
            exclude = []

        mapper = inspect(self.__class__)
        return {
            column.key: getattr(self, column.key)
            for column in mapper.attrs
            if column.key not in exclude
        }

    def ts_model_by_dict(self, ts_dict):
        data = {}
        for k, v in ts_dict.items():
            if isinstance(v, str):
                data[k] = getattr(self, v)
            else:
                data[k] = v
        return data

    @classmethod
    def filter_dict_by_model(cls, data_dict):
        inspector = inspect(cls)
        # 仅获取数据库列字段（排除关系属性）
        model_fields = {
            column.key for column in inspector.attrs if hasattr(column, "columns")
        }
        return {k: v for k, v in data_dict.items() if k in model_fields}


class Collect(db.Model, BaseModelMixin):
    __tablename__ = "collect"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.Text)
    type = db.Column(db.Text)
    type: Mapped[FolderTypeEnum] = mapped_column(
        SA_Enum(FolderTypeEnum, values_callable=lambda enum: [e.value for e in enum]),
        nullable=False,
    )
    url = db.Column(db.Text)
    icon = db.Column(db.Text)
    # 默认值为当前 Unix 时间戳（如 1768318968），与导入的 Netscape 书签 ADD_DATE 格式一致
    add_date = db.Column(db.Text, default=lambda: str(int(time.time())))
    tags = db.Column(db.Text)
    pid = db.Column(db.Integer)
    px = db.Column(db.Integer)
    details = db.Column(db.Text)
    valid = db.Column(db.Text, server_default=db.FetchedValue())
    depth = db.Column(db.Integer)
