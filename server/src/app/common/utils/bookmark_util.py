"""
书签文件操作工具集

负责浏览器书签 HTML 文件的解析与生成，不涉及数据库操作。
支持 Netscape Bookmark 格式 (Chrome / Firefox / Edge 兼容)。
"""

import html as html_lib
from datetime import datetime
from typing import Any

from bs4 import BeautifulSoup

# 允许的书签文件扩展名
ALLOWED_BOOKMARK_EXTENSIONS = {".html", ".htm"}

# 最大文件大小 10MB
MAX_BOOKMARK_FILE_SIZE = 10 * 1024 * 1024


def allowed_bookmark_file(filename: str) -> bool:
    """校验文件扩展名是否为书签文件"""
    if not filename or "." not in filename:
        return False
    ext = filename.rsplit(".", 1)[-1].lower()
    return f".{ext}" in ALLOWED_BOOKMARK_EXTENSIONS


def validate_file_size(content: bytes) -> None:
    """校验文件内容大小，超限抛出 ValueError"""
    if len(content) > MAX_BOOKMARK_FILE_SIZE:
        raise ValueError(
            f"文件过大，最大支持 {MAX_BOOKMARK_FILE_SIZE // 1024 // 1024}MB"
        )
    if not content:
        raise ValueError("文件内容为空")


def parse_bookmark_html(html_text: str) -> list[dict[str, Any]]:
    """
    解析浏览器书签 HTML 文本，返回扁平化的书签数据列表。

    返回结构:
        [
            {"type": "folder", "title": "...", "folder": "父路径"},
            {"type": "bookmark", "title": "...", "url": "...", "icon": "...", "add_date": "...", "tags": "...", "folder": "父路径"},
            ...
        ]
    """
    text = html_text.replace("<dt>", "").replace("<DT>", "").replace("<p>", "")
    soup = BeautifulSoup(text, "html.parser")

    folder_stack = []
    data = []

    def parse(dl):
        if not dl:
            return
        for sub_dl in dl.find_all("dl", recursive=False):
            title = sub_dl.find_previous("h3")
            if title:
                data.append(
                    {
                        "type": "folder",
                        "title": title.text,
                        "folder": "/".join(folder_stack),
                    }
                )
                folder_stack.append(title.text)
            parse(sub_dl)
        for a_tag in dl.find_all("a", recursive=False):
            data.append(
                {
                    "type": "bookmark",
                    "title": a_tag.text,
                    "url": a_tag.get("href", ""),
                    "icon": a_tag.get("icon", "") if a_tag.has_attr("icon") else None,
                    "add_date": a_tag.get("add_date", ""),
                    "tags": a_tag.get("tags", ""),
                    "folder": "/".join(folder_stack),
                }
            )
        if len(folder_stack) > 0:
            folder_stack.pop()

    parse(soup.find("dl"))
    return data


def html_escape(text: Any) -> str:
    """转义 HTML 特殊字符"""
    if not text:
        return ""
    return html_lib.escape(str(text))


def generate_bookmark_html(items: list[dict[str, Any]]) -> str:
    """
    根据扁平化的书签数据列表生成 Netscape Bookmark 格式 HTML。

    性能优化:
        - 使用列表累加器 + 单次 join 替代递归字符串拼接，减少中间字符串分配
        - 预取字段值，减少 dict.get 调用次数
        - 批量 HTML 转义

    参数:
        items: 书签数据列表，每个元素需包含以下字段:
            - name: 名称
            - type: "folder" 或 "bookmark"
            - url: URL (仅 bookmark)
            - icon: 图标 (仅 bookmark)
            - add_date: 添加时间戳
            - id: 节点ID
            - pid: 父节点ID (-1 或 None 表示根节点)

    返回:
        浏览器兼容的书签 HTML 字符串
    """
    if not items:
        return ""

    # 构建 id -> children 映射 (O(n))
    children_map: dict[Any, list[dict[str, Any]]] = {}
    root_items = []
    for item in items:
        pid = item.get("pid")
        if pid in ("-1", -1, None):
            root_items.append(item)
        else:
            children_map.setdefault(pid, []).append(item)

    # 列表累加器：避免递归中反复创建/拼接中间字符串
    parts: list[str] = []

    def build_node(item: dict[str, Any]) -> None:
        """将单个节点的 HTML 追加到 parts 列表"""
        name = html_escape(item.get("name") or "")
        add_date = html_escape(item.get("add_date") or "")
        if item.get("type") == "folder":
            parts.append(f'<DT><H3 ADD_DATE="{add_date}">{name}</H3>\n')
            parts.append("<DL><p>\n")
            for child in children_map.get(item.get("id"), []):
                build_node(child)
            parts.append("</DL><p>\n")
        else:
            url = html_escape(item.get("url") or "")
            icon = html_escape(item.get("icon") or "")
            parts.append(
                f'<DT><A HREF="{url}" ADD_DATE="{add_date}" ICON="{icon}">{name}</A>\n'
            )

    for item in root_items:
        build_node(item)
    body = "".join(parts)
    export_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    return (
        "<!DOCTYPE NETSCAPE-Bookmark-file-1>\n"
        '<META HTTP-EQUIV="Content-Type" CONTENT="text/html; charset=UTF-8">\n'
        "<TITLE>Bookmarks</TITLE>\n"
        "<H1>Bookmarks</H1>\n"
        f"<!-- 导出于 {export_time} -->\n"
        f"<DL><p>\n{body}</DL><p>\n"
    )
