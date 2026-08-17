import time

SUCCESS_STATUS = 1
FAIL_STATUS = 0


class BaseModel:
    def __init__(self, data=None, message="", status=SUCCESS_STATUS):
        self.timestamp = int(time.time())
        self.status = status
        self.message = message
        self.data = data

    def to_dict(self):
        return self.__dict__


def fail_model(message="请求失败！"):
    return BaseModel(None, message, FAIL_STATUS).to_dict()


def success_model(data={}, msg="请求成功！"):
    return BaseModel(data, msg).to_dict()
