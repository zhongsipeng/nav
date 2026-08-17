"""请求体 Pydantic 模型定义"""

from pydantic import BaseModel, Field


class SaveCollectRequest(BaseModel):
    """saveCollect 接口请求体"""

    id: int | None = None
    name: str | None = None
    type: str
    url: str = Field(pattern=r"^https?://")
    pid: int


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
