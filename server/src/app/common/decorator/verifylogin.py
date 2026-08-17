# 用于验证接收的json数据格式
from functools import wraps

from ...core.error import UserNoLoginError
from ..session import userinfo


def validate_login():
    def decorator(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            if not userinfo():
                raise UserNoLoginError()
            else:
                return f(*args, **kwargs)

        return wrapper

    return decorator
