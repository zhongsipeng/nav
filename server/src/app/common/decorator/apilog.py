import functools
import logging
import time
import traceback
from collections.abc import Awaitable, Callable
from typing import TypeVar

api_logger = logging.getLogger("api_log")

# 类型变量，用于保留原函数的类型提示
T = TypeVar("T")


def log_request(
    logger: logging.Logger | None = api_logger,
    log_args: bool = True,
    log_body: bool = False,  # 是否记录 body（可能包含敏感信息，谨慎开启）
    log_headers: bool = False,
    log_response: bool = False,
) -> Callable[[Callable[..., Awaitable[T]]], Callable[..., Awaitable[T]]]:
    """
    异步请求日志装饰器

    :param logger: 自定义 logger，默认使用类的名称
    :param log_args: 是否记录请求参数（params, data, json）
    :param log_body: 是否记录请求体内容（可能很大，谨慎）
    :param log_headers: 是否记录请求头（可能包含敏感信息，建议脱敏后使用）
    :param log_response: 是否记录响应内容（可能很大，谨慎）
    """

    def decorator(func: Callable[..., Awaitable[T]]) -> Callable[..., Awaitable[T]]:
        @functools.wraps(func)
        async def wrapper(self, *args, **kwargs) -> T:
            _logger = logger

            # 提取关键参数（兼容位置参数和关键字参数）
            method = kwargs.get("method") or (args[0] if args else None)
            url = kwargs.get("url") or (args[1] if len(args) > 1 else None)
            params = kwargs.get("params")
            data = kwargs.get("data")
            json_data = kwargs.get("json")
            headers = kwargs.get("headers")

            # 构建日志前缀
            log_prefix = f"[{method} {url}]"

            # 记录请求开始
            _logger.info(f"{log_prefix} 开始请求")

            # 记录额外参数（调试级别）
            if log_args:
                _logger.debug(f"{log_prefix} params={params}")
                if log_body:
                    _logger.debug(f"{log_prefix} data={data}, json={json_data}")
                if log_headers:
                    # 注意：headers 可能包含 Authorization，建议脱敏
                    safe_headers = {
                        k: v if k.lower() != "authorization" else "***"
                        for k, v in (headers or {}).items()
                    }
                    _logger.debug(f"{log_prefix} headers={safe_headers}")

            start = time.perf_counter()
            try:
                result = await func(self, *args, **kwargs)
                elapsed = time.perf_counter() - start
                _logger.info(f"{log_prefix} 请求成功，耗时 {elapsed:.3f}s")

                if log_response:
                    # 如果返回的是文本或字节，可以截断记录
                    if isinstance(result, str):
                        _logger.debug(
                            f"{log_prefix} 响应内容（前200字符）: {result[:200]}..."
                        )
                    elif isinstance(result, bytes):
                        _logger.debug(
                            f"{log_prefix} 响应内容（二进制，大小 {len(result)} 字节）"
                        )
                return result
            except Exception as e:
                elapsed = time.perf_counter() - start
                _logger.error(
                    f"{log_prefix} 请求失败，耗时 {elapsed:.3f}s，异常: {type(e).__name__}: {e}"
                )
                # 可选：记录完整堆栈（级别 DEBUG 或 ERROR）
                _logger.debug(
                    f"{log_prefix} 堆栈:\n{''.join(traceback.format_exception(type(e), e, e.__traceback__))}"
                )
                raise

        return wrapper

    return decorator
