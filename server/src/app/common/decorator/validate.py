"""基于 Pydantic 的请求体/响应体校验装饰器"""

from collections.abc import Callable
from functools import wraps
from typing import Any, TypeVar

from flask import g, jsonify, request
from pydantic import BaseModel, TypeAdapter, ValidationError

from ...core.error import RequestValidationError, ResponseValidationError

T = TypeVar("T", bound=BaseModel)


def validate_api(
    request_model: type[T] | None = None,
    response_model: Any | None = None,
    msg: str | Callable[[Any], str] = "请求成功！",
) -> Callable[..., Any]:
    """校验请求 JSON 与视图返回值，并声明成功文案

    - request_model: 请求体模型；为 None 时不解析/校验 JSON（适合无 body 的路由）
    - response_model: 响应模型（BaseModel 或 list[...] 等类型）；为 None 时不做输出校验
    - msg: 成功文案，静态字符串或接收视图返回值的函数
    """

    def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            if request_model is not None:
                data = request.get_json()
                try:
                    validated = request_model.model_validate(data)
                except ValidationError as e:
                    raise RequestValidationError(e.errors()) from e
                result = func(validated.model_dump(), *args, **kwargs)
            else:
                result = func(*args, **kwargs)

            if response_model is not None:
                try:
                    TypeAdapter(response_model).validate_python(result)
                except ValidationError as e:
                    raise ResponseValidationError(e.errors()) from e

            g.success_msg = msg(result) if callable(msg) else msg
            # Flask 不允许视图返回 None，统一转为 JSON null 以保持 data 为 null
            return jsonify(None) if result is None else result

        return wrapper

    return decorator
