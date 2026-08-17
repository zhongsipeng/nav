import base64
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup

DEFAULT_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
}
REQUEST_TIMEOUT = 10


def _root_favicon_url(url):
    parsed = urlparse(url)
    return f"{parsed.scheme}://{parsed.netloc}/favicon.ico"


def _download(url):
    response = requests.get(url, headers=DEFAULT_HEADERS, timeout=REQUEST_TIMEOUT)
    response.raise_for_status()
    return response


def _looks_like_html(content):
    """粗略判断内容是否为 HTML（防止 /favicon.ico 返回的是错误页）"""
    return content[:512].lstrip()[:1] == b"<"


def _guess_content_type(icon_url, content_type):
    if "image" in content_type:
        return content_type
    if icon_url.endswith(".png"):
        return "image/png"
    if icon_url.endswith(".jpg") or icon_url.endswith(".jpeg"):
        return "image/jpeg"
    if icon_url.endswith(".svg"):
        return "image/svg+xml"
    return "image/x-icon"


def _to_data_uri(content, content_type):
    icon_base64 = base64.b64encode(content).decode("utf-8")
    return f"data:{content_type};base64,{icon_base64}"


def get_website_title(url):
    """获取网页标题（优先 <title>，失败回退 og:title）；获取失败返回 None"""
    try:
        response = _download(url)
        soup = BeautifulSoup(response.text, "html.parser")
        if soup.title and soup.title.string:
            return soup.title.string.strip() or None
        og = soup.find("meta", property="og:title")
        if og and og.get("content"):
            return og["content"].strip() or None
        return None
    except Exception as e:
        print(f"获取网站标题失败: {e}")
        return None


def get_favicon_as_base64(url):
    """获取网站图标并返回 base64 data URI；获取失败返回 None。

    获取顺序：
    1. 先尝试网站根目录的 /favicon.ico（请求少、更快）；
    2. 失败后再抓取页面解析 <link rel="icon"> 等标签；
    3. 均失败返回 None。
    """
    try:
        # 1. 根目录 favicon.ico
        root_icon = _root_favicon_url(url)
        try:
            resp = _download(root_icon)
            if not _looks_like_html(resp.content):
                content_type = _guess_content_type(root_icon, resp.headers.get("content-type", ""))
                return _to_data_uri(resp.content, content_type)
        except Exception:
            pass

        # 2. 抓取页面，解析 <link rel="icon">
        page = _download(url)
        soup = BeautifulSoup(page.text, "html.parser")
        icon_link = None
        for rel in ("icon", "shortcut icon", "apple-touch-icon"):
            tag = soup.find("link", rel=rel)
            if tag and tag.get("href"):
                icon_link = urljoin(url, tag["href"])
                break
        if not icon_link:
            icon_link = root_icon

        resp = _download(icon_link)
        if _looks_like_html(resp.content):
            return None
        content_type = _guess_content_type(icon_link, resp.headers.get("content-type", ""))
        return _to_data_uri(resp.content, content_type)
    except Exception as e:
        print(f"获取图标失败: {e}")
        return None
