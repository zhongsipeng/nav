"""请求体 Pydantic 模型定义"""

import re

from pydantic import BaseModel, model_validator

from ..entities import FolderTypeEnum


class SaveCollectRequest(BaseModel):
    id: int | None = None
    name: str | None = None
    type: FolderTypeEnum  # 直接使用枚举类型
    url: str | None = None
    pid: int

    @model_validator(mode="after")
    def validate_url_for_bookmark(self):
        if self.type == FolderTypeEnum.BOOKMARK:
            if not self.url:
                raise ValueError('url is required when type is "bookmark"')
            if not re.match(r"^https?://", self.url):
                raise ValueError("url must start with http:// or https://")
        # folder 情况下 url 可为空，无需额外校验
        return self


class BatchUpdateItem(BaseModel):
    """batchUpdate 接口单条数据"""

    id: int
    px: int
    pid: int


class BatchUpdateRequest(BaseModel):
    """batchUpdate 接口请求体"""

    data: list[BatchUpdateItem]


class DeleteCollectRequest(BaseModel):
    """delCollect 接口请求体"""

    ids: list[int]
