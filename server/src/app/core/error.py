class BusinessError(Exception):
    def __init__(self, message="Business Error", details=None):
        self.message = message
        self.details = details


class UserNoLoginError(Exception):
    def __init__(self, message="user no login", details=None):
        self.message = message
        self.details = details


class RequestValidationError(Exception):
    """请求参数（输入）校验失败"""

    def __init__(self, errors):
        self.errors = errors


class ResponseValidationError(Exception):
    """响应数据（输出）校验失败"""

    def __init__(self, errors):
        self.errors = errors


def raise_business_msg(msg):
    raise BusinessError(message=msg)
