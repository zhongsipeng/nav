import asyncio
import logging
from typing import Any

import aiohttp
import requests
from aiohttp import ClientError, ClientTimeout
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from ..decorator.apilog import log_request

logger = logging.getLogger("api_log")
# 默认请求头（可根据实际需要修改）
DEFAULT_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
    "Accept-Language": "zh-CN,zh;q=0.8,en-US;q=0.5,en;q=0.3",
    "Accept-Encoding": "gzip, deflate",
    "Connection": "keep-alive",
}


class AsyncHttpClient:
    """轻量级异步 HTTP 客户端封装"""

    def __init__(
        self,
        base_url: str | None = None,
        timeout: int = 30,
        default_headers: dict[str, str] | None = DEFAULT_HEADERS,
        max_retries: int = 0,  # 0 表示不重试
        retry_delay: float = 1.0,
    ):
        """
        :param base_url: 所有请求的基础 URL（可选）
        :param timeout: 请求超时时间（秒）
        :param default_headers: 默认请求头
        :param max_retries: 最大重试次数（仅对 5xx 和连接错误生效）
        :param retry_delay: 重试间隔（秒）
        """
        self.base_url = base_url or None
        self.timeout = ClientTimeout(total=timeout)
        self.default_headers = default_headers or {}
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self._session: aiohttp.ClientSession | None = None

    async def __aenter__(self):
        """支持 async with 上下文"""
        self._session = aiohttp.ClientSession(
            base_url=self.base_url,
            headers=self.default_headers,
            timeout=self.timeout,
        )
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """退出时关闭会话"""
        await self.close()

    async def close(self):
        """主动关闭会话"""
        if self._session and not self._session.closed:
            await self._session.close()

    @log_request()
    async def _request(
        self,
        method: str,
        url: str,
        params: dict | None = None,
        data: Any = None,
        json: Any = None,
        headers: dict[str, str] | None = None,
        as_bytes: bool = False,  # 新增参数
        **kwargs,
    ) -> str | bytes:
        """内部请求方法，支持返回文本或字节"""
        full_url = url if self.base_url == "" else url
        headers = {**self.default_headers, **(headers or {})}

        for attempt in range(self.max_retries + 1):
            try:
                if self._session is None or self._session.closed:
                    async with aiohttp.ClientSession(
                        base_url=self.base_url,
                        headers=self.default_headers,
                        timeout=self.timeout,
                    ) as session:
                        async with session.request(
                            method=method,
                            url=url,
                            params=params,
                            data=data,
                            json=json,
                            headers=headers,
                            **kwargs,
                        ) as resp:
                            resp.raise_for_status()
                            content = None
                            if as_bytes:
                                content = await resp.read()  # 返回字节

                            else:
                                content = await resp.text()  # 返回文本

                            return {
                                "content": content,
                                "headers": dict(resp.headers),
                                "status": resp.status,
                            }
                else:
                    async with self._session.request(
                        method=method,
                        url=url,
                        params=params,
                        data=data,
                        json=json,
                        headers=headers,
                        **kwargs,
                    ) as resp:
                        resp.raise_for_status()
                        content = None
                        if as_bytes:
                            content = await resp.read()
                        else:
                            content = await resp.text()
                        return {
                            "content": content,
                            "headers": dict(resp.headers),
                            "status": resp.status,
                        }
            except (TimeoutError, ClientError):
                # current_app.logger.error(
                #     f"请求失败 (尝试 {attempt + 1}/{self.max_retries + 1}): {e}"
                # )
                if attempt == self.max_retries:
                    raise
                await asyncio.sleep(self.retry_delay * (attempt + 1))

    # 快捷方法也加上 as_bytes 参数
    async def get(
        self, url: str, params: dict | None = None, as_bytes: bool = False, **kwargs
    ) -> str | bytes:
        return await self._request(
            "GET", url, params=params, as_bytes=as_bytes, **kwargs
        )

    async def post(
        self, url: str, data=None, json=None, as_bytes: bool = False, **kwargs
    ) -> str | bytes:
        return await self._request(
            "POST", url, data=data, json=json, as_bytes=as_bytes, **kwargs
        )

    # put, delete, patch 同理，加上 as_bytes 参数


class HttpClient:
    """简单封装的 HTTP 客户端，支持重试、自动编码修正"""

    def __init__(self, headers=None, timeout=10, retries=3, backoff_factor=1):
        self.session = requests.Session()
        # 设置默认请求头
        self.session.headers.update(headers or DEFAULT_HEADERS)
        self.timeout = timeout

        # 配置重试策略（对连接错误、超时、5xx 状态码重试）
        retry_strategy = Retry(
            total=retries,
            connect=retries,
            read=retries,
            backoff_factor=backoff_factor,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["GET", "POST"],
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)

    # 新增：进入 with 块时返回自身
    def __enter__(self):
        return self

    # 新增：退出 with 块时关闭 session
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.session.close()
        # 如果希望吞掉异常，可以返回 True，一般返回 None（默认）即可
        # 如果返回 True，异常会被抑制；这里不抑制，让上层处理
        return False

    def _fix_encoding(self, response):
        """修正响应编码，防止乱码"""
        # 优先使用 requests 的 apparent_encoding（需安装 chardet）
        if hasattr(response, "apparent_encoding") and response.apparent_encoding:
            response.encoding = response.apparent_encoding
        elif not response.encoding:
            response.encoding = "utf-8"  # 兜底
        return response

    def get(self, url, params=None, headers=None, timeout=None, **kwargs):
        """GET 请求，自动处理编码和重试"""
        try:
            response = self.session.get(
                url,
                params=params,
                headers=headers,
                timeout=timeout or self.timeout,
                **kwargs,
            )
            response.raise_for_status()  # 非 2xx 抛出异常
            self._fix_encoding(response)
            return response
        except requests.exceptions.RequestException as e:
            logger.error(f"GET {url} 失败: {e}")
            return None  # 或根据需求抛出自定义异常
        finally:
            logger.info(f"GET {url} : {response.content}")

    def post(self, url, data=None, json=None, headers=None, timeout=None, **kwargs):
        """POST 请求，支持表单和 JSON"""
        try:
            response = self.session.post(
                url,
                data=data,
                json=json,
                headers=headers,
                timeout=timeout or self.timeout,
                **kwargs,
            )
            response.raise_for_status()
            self._fix_encoding(response)
            return response
        except requests.exceptions.RequestException as e:
            logger.error(f"POST {url} 失败: {e}")
            return None
