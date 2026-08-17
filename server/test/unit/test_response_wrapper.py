"""统一响应包装与校验异常区分的测试"""

import logging

import pytest
from flask import Flask

from src.app.common.decorator.validate import validate_api
from src.app.core.appinit.handlers import register_handlers
from src.app.core.error import RequestValidationError
from src.app.model.schemes.response_schemes import SaveCollectResponse


@pytest.fixture
def app():
    flask_app = Flask(__name__)
    register_handlers(flask_app)
    return flask_app


class TestResponseWrapper:
    def test_dict_return_wrapped(self, app):
        @app.route("/data")
        def data():
            return {"a": 1}

        resp = app.test_client().get("/data")
        body = resp.get_json()
        assert resp.status_code == 200
        assert body["status"] == 1
        assert body["message"] == "请求成功！"
        assert body["data"] == {"a": 1}

    def test_msg_from_decorator(self, app):
        @app.route("/data")
        @validate_api(msg="自定义成功")
        def data():
            return {"a": 1}

        resp = app.test_client().get("/data")
        assert resp.get_json()["message"] == "自定义成功"

    def test_callable_msg(self, app):
        @app.route("/data")
        @validate_api(msg=lambda r: f"count={r['count']}")
        def data():
            return {"count": 3}

        resp = app.test_client().get("/data")
        assert resp.get_json()["message"] == "count=3"

    def test_none_result_wrapped_as_null(self, app):
        @app.route("/data")
        @validate_api(msg="无数据")
        def data():
            return None

        resp = app.test_client().get("/data")
        body = resp.get_json()
        assert resp.status_code == 200
        assert body["status"] == 1
        assert body["data"] is None
        assert body["message"] == "无数据"

    def test_non_json_response_not_wrapped(self, app):
        @app.route("/text")
        def text():
            return "plain"

        resp = app.test_client().get("/text")
        assert resp.get_data(as_text=True) == "plain"
        assert resp.content_type.startswith("text/html")


class TestValidationErrorHandlers:
    def test_request_validation_error_prefixed(self, app):
        @app.route("/bad")
        def bad():
            raise RequestValidationError(
                [{"type": "missing", "loc": ("url",), "msg": "Field required"}]
            )

        resp = app.test_client().get("/bad")
        body = resp.get_json()
        assert resp.status_code == 200
        assert body["status"] == 0
        assert body["message"] == "请求参数错误：缺少必须字段: url"

    def test_response_validation_error_prefixed_and_logged(self, app, caplog):
        @app.route("/save", methods=["POST"])
        @validate_api(response_model=SaveCollectResponse)
        def save():
            return {"type": "bookmark", "id": 1}

        with caplog.at_level(logging.ERROR):
            resp = app.test_client().post("/save")

        body = resp.get_json()
        assert resp.status_code == 200
        assert body["status"] == 0
        assert body["message"].startswith("响应数据错误：")
        assert "响应数据校验失败" in caplog.text

    def test_wrapper_skips_error_responses(self, app):
        @app.route("/bad")
        def bad():
            raise RequestValidationError(
                [{"type": "missing", "loc": ("url",), "msg": "Field required"}]
            )

        resp = app.test_client().get("/bad")
        body = resp.get_json()
        assert body["status"] == 0
        assert body["message"].startswith("请求参数错误")
        assert body["data"] is None
