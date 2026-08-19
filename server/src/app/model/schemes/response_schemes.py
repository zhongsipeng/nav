"""响应体 Pydantic 模型定义"""

from __future__ import annotations

from pydantic import BaseModel, Field

from ..entities import FolderTypeEnum


class BookmarkNode(BaseModel):
    children: list[BookmarkNode] = Field(default_factory=list, description="子节点列表")
    depth: int
    icon: str | None = None  # 图标可能为 null
    id: int  # 根据你的数据，id 是整数
    label: str
    pid: int  # 父节点 ID，-1 表示根
    px: int  # 位置或排序序号
    type: FolderTypeEnum  # 例如 "folder"
    url: str | None = None  # 书签 URL，文件夹则为 null


GetCollectResponse = list[BookmarkNode]


class SaveCollectResponse(BaseModel):
    """saveCollect 接口响应数据"""

    type: str
    id: int
    pid: int
    px: int
    label: str
    url: str | None = None
    icon: str | None = None
    depth: int | None = None


class ImportCollectResponse(BaseModel):
    """importCollect 接口响应数据"""

    count: int
