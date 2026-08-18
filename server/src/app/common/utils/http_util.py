import asyncio
import base64
import traceback
from urllib.parse import urljoin, urlparse

from bs4 import BeautifulSoup
from flask import current_app

from .client_util import AsyncHttpClient, HttpClient

REQUEST_TIMEOUT = 2
domain_mapping = {}


def _get_domain(url: str) -> str:
    """
    从给定的 URL 中提取网站域名（主机名，包含子域名和端口）。

    参数:
        url (str): 完整的 URL（如 'https://www.example.com:8080/path'）
                   或没有协议的地址（如 'example.com'）。

    返回:
        str: 提取的主机名，若解析失败则返回空字符串。
             例如：'www.example.com' 或 'example.com:8080'。
    """
    # 如果没有协议，添加一个占位协议以便 urlparse 正确解析
    if not url.startswith(("http://", "https://")):
        url = "//" + url

    parsed = urlparse(url)
    # netloc 包含主机名和端口（如果有）
    return parsed.netloc or ""


def _root_favicon_url(url):
    parsed = urlparse(url)
    return f"{parsed.scheme}://{parsed.netloc}/favicon.ico"


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
    try:
        with HttpClient(timeout=REQUEST_TIMEOUT) as client:
            response = client.get(url)
            # 关键改动：使用 response.content（字节流）而不是 response.text
            soup = BeautifulSoup(response.content, "html.parser")
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
        with HttpClient(timeout=REQUEST_TIMEOUT) as client:
            try:
                resp = client.get(root_icon)
                if not _looks_like_html(resp.content):
                    content_type = _guess_content_type(
                        root_icon, resp.headers.get("content-type", "")
                    )
                    return _to_data_uri(resp.content, content_type)
            except Exception:
                pass

            # 2. 抓取页面，解析 <link rel="icon">
            page = client.get(url)
            soup = BeautifulSoup(page.text, "html.parser")
            icon_link = None
            for rel in ("icon", "shortcut icon", "apple-touch-icon"):
                tag = soup.find("link", rel=rel)
                if tag and tag.get("href"):
                    icon_link = urljoin(url, tag["href"])
                    break
            if not icon_link:
                icon_link = root_icon

            resp = client.get(icon_link)
            if _looks_like_html(resp.content):
                return None
            content_type = _guess_content_type(
                icon_link, resp.headers.get("content-type", "")
            )
            return _to_data_uri(resp.content, content_type)
    except Exception as e:
        print(f"获取图标失败: {e}")
        return None


def _get_icon_base64(response, icon_link) -> str | None:
    if isinstance(response, Exception):
        return response
    content_type = _guess_content_type(
        icon_link, response.get("headers", {}).get("content-type", "")
    )
    return _to_data_uri(response.get("content"), content_type)


async def get_favicon_as_base64_async(url, client) -> str | None:
    # 维护一个同域名网站图标映射，防止重复请求
    try:
        icon_link = _root_favicon_url(url)
        task1, task2 = (
            asyncio.create_task(client.get(icon_link, as_bytes=True)),
            asyncio.create_task(client.get(url)),
        )
        resp1, resp2 = await asyncio.gather(task1, task2, return_exceptions=True)
        icon_base64 = _get_icon_base64(resp1, icon_link)
        if not isinstance(resp1, Exception):  # 获取根目录图标成功直接返回
            return icon_base64

        if isinstance(resp2, Exception) or not resp2.get("content"):  # 抓取页面失败
            return resp2
        soup = BeautifulSoup(resp2.get("content"), "html.parser")
        icon_link = None
        for rel in ("icon", "shortcut icon", "apple-touch-icon"):
            tag = soup.find("link", rel=rel)
            if tag and tag.get("href"):
                icon_link = urljoin(url, tag["href"])
                break
        if not icon_link:  # 没有找到图标链接，返回 None
            return None
        try:
            resp = await client.get(icon_link, as_bytes=True)
        except Exception as e:
            resp = e
        icon_base64 = _get_icon_base64(resp, icon_link)

        return icon_base64
    except ExceptionGroup as eg:
        for exc in eg.exceptions:
            tb_str = "".join(
                traceback.format_exception(type(exc), exc, exc.__traceback__)
            )
            print(f"子异常:\n{tb_str}")
            # print(f"子异常: {type(exc).__name__}: {exc}")
        return None
    except Exception as e:
        tb_str = "".join(traceback.format_exception(type(e), e, e.__traceback__))
        print(f"其他异常: {tb_str}")
        # print(f"其他异常: {e}")
        return None


async def batch_get_favicon_base64(
    urls: list[str], max_concurrent: int = 20
) -> dict[str, str | None]:
    """批量获取网站图标，返回 {url: base64} 字典"""
    results = {}

    sem = asyncio.Semaphore(max_concurrent)
    async with AsyncHttpClient(timeout=REQUEST_TIMEOUT) as client:

        async def limited_fetch(url: str):

            async with sem:
                domain = _get_domain(url)
                if domain in domain_mapping:  # 已获取过该域名的图标，直接返回
                    current_app.logger.info(f"已获取过 {domain} 的图标，直接返回缓存")
                    res = await domain_mapping[domain]
                else:
                    task = asyncio.create_task(get_favicon_as_base64_async(url, client))
                    domain_mapping[domain] = task
                    res = await task

                if res is None:
                    current_app.logger.info(f"未获取到图标: {url}")
                elif isinstance(res, Exception):
                    current_app.logger.error(f"获取图标时发生错误: {url} - 错误：{res}")
                    res = None
                else:
                    current_app.logger.info(f"获取图标成功: {url}" + res[:30] + "...")
                return res

        tasks = [limited_fetch(url) for url in urls]
        results = await asyncio.gather(*tasks)
    return dict(zip(urls, results))
