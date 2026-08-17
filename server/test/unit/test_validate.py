"""请求模型、中文错误映射与 validate_api 装饰器的单元测试"""

import pytest
from flask import Flask, g
from pydantic import TypeAdapter, ValidationError
from werkzeug.exceptions import UnsupportedMediaType

from src.app.common.decorator.validate import validate_api
from src.app.core.appinit.handlers import _validation_message
from src.app.core.error import RequestValidationError, ResponseValidationError
from src.app.model.schemes.request_schemes import (
    BatchUpdateRequest,
    DeleteCollectRequest,
    SaveCollectRequest,
)
from src.app.model.schemes.response_schemes import (
    BookmarkNode,
    GetCollectResponse,
    ImportCollectResponse,
    SaveCollectResponse,
)


class TestRequestModels:
    def test_save_collect_valid_and_coercion(self):
        model = SaveCollectRequest.model_validate(
            {
                "name": "首页",
                "type": "bookmark",
                "url": "https://example.com",
                "pid": "5",
            }
        )
        assert model.model_dump()["pid"] == 5

    def test_save_collect_missing_field(self):
        with pytest.raises(ValidationError) as exc:
            SaveCollectRequest.model_validate({})
        assert exc.value.errors()[0]["type"] == "missing"

    def test_save_collect_bad_url(self):
        with pytest.raises(ValidationError) as exc:
            SaveCollectRequest.model_validate(
                {"name": "x", "type": "b", "url": "ftp://x", "pid": 1}
            )
        assert exc.value.errors()[0]["type"] == "string_pattern_mismatch"

    def test_save_collect_unparsable_int(self):
        with pytest.raises(ValidationError) as exc:
            SaveCollectRequest.model_validate(
                {"name": "x", "type": "b", "url": "https://x", "pid": "abc"}
            )
        assert exc.value.errors()[0]["type"] == "int_parsing"

    def test_batch_update_item_missing_field(self):
        with pytest.raises(ValidationError) as exc:
            BatchUpdateRequest.model_validate(
                {"data": [{"id": 1, "px": 1, "pid": 1}, {"id": 2, "px": 2}]}
            )
        errors = exc.value.errors()
        assert errors[0]["type"] == "missing"
        assert errors[0]["loc"] == ("data", 1, "pid")

    def test_batch_update_item_not_dict(self):
        with pytest.raises(ValidationError) as exc:
            BatchUpdateRequest.model_validate({"data": ["nope"]})
        assert exc.value.errors()[0]["type"] == "model_type"

    def test_batch_update_data_not_list(self):
        with pytest.raises(ValidationError) as exc:
            BatchUpdateRequest.model_validate({"data": "nope"})
        assert exc.value.errors()[0]["type"] == "list_type"

    def test_delete_collect_ids_not_list(self):
        with pytest.raises(ValidationError) as exc:
            DeleteCollectRequest.model_validate({"ids": "nope"})
        assert exc.value.errors()[0]["type"] == "list_type"

    def test_delete_collect_ids_coerced(self):
        dumped = DeleteCollectRequest.model_validate({"ids": ["1", 2]}).model_dump()
        assert dumped["ids"] == [1, 2]

    def test_extra_keys_ignored(self):
        dumped = SaveCollectRequest.model_validate(
            {"name": "x", "type": "b", "url": "https://x", "pid": 1, "extra": True}
        ).model_dump()
        assert "extra" not in dumped


class TestResponseModels:
    def test_save_collect_response_valid(self):
        model = SaveCollectResponse.model_validate(
            {
                "type": "bookmark",
                "id": 1,
                "pid": 0,
                "px": 10,
                "label": "首页",
                "url": "https://example.com",
                "icon": "data:image/x-icon;base64,xx",
                "depth": 1,
            }
        )
        assert model.id == 1
        assert model.label == "首页"

    def test_save_collect_response_missing_field(self):
        with pytest.raises(ValidationError) as exc:
            SaveCollectResponse.model_validate({"type": "bookmark", "id": 1})
        assert exc.value.errors()[0]["type"] == "missing"

    def test_tree_node_recursive(self):
        node = BookmarkNode.model_validate(
            {
                "type": "folder",
                "id": 1,
                "pid": -1,
                "px": 0,
                "label": "root",
                "depth": 0,
                "children": [
                    {
                        "type": "bookmark",
                        "id": 2,
                        "pid": 1,
                        "px": 10,
                        "label": "bm",
                        "depth": 2,
                        "url": "https://x.com",
                    }
                ],
            }
        )
        assert node.children[0].url == "https://x.com"

    def test_tree_node_missing_children_defaults(self):
        # 书签节点没有 children 字段，应能通过校验（默认值不参与校验）
        node = BookmarkNode.model_validate(
            {
                "type": "bookmark",
                "id": 2,
                "pid": 1,
                "px": 10,
                "label": "bm",
                "depth": 2,
            }
        )
        assert node.children == []

    def test_get_collect_response_list(self):
        data = [
            {
                "type": "folder",
                "id": 1,
                "pid": -1,
                "px": 0,
                "label": "root",
                "depth": 0,
                "children": [],
            }
        ]
        result = TypeAdapter(GetCollectResponse).validate_python(data)
        assert result[0].label == "root"

    def test_import_collect_response(self):
        assert ImportCollectResponse.model_validate({"count": 3}).count == 3


class TestValidationMessage:
    @staticmethod
    def _error(err_type, loc, msg="input error"):
        return {"type": err_type, "loc": loc, "msg": msg}

    def test_missing(self):
        assert (
            _validation_message(self._error("missing", ("url",))) == "缺少必须字段: url"
        )

    def test_nested_missing_index(self):
        assert (
            _validation_message(self._error("missing", ("data", 1, "id")))
            == "缺少必须字段: data[1].id"
        )

    def test_number_type(self):
        assert (
            _validation_message(self._error("int_parsing", ("pid",)))
            == "字段 pid 应该是 Number 类型"
        )

    def test_string_type(self):
        assert (
            _validation_message(self._error("string_type", ("name",)))
            == "字段 name 应该是 String 类型"
        )

    def test_bool_type(self):
        assert (
            _validation_message(self._error("bool_type", ("flag",)))
            == "字段 flag 应该是 Boolean 类型"
        )

    def test_list_type(self):
        assert (
            _validation_message(self._error("list_type", ("ids",)))
            == "字段 ids 应该是 Array 类型"
        )

    def test_dict_type(self):
        assert (
            _validation_message(self._error("dict_type", ("meta",)))
            == "字段 meta 应该是 Object 类型"
        )

    def test_root_model_type(self):
        assert (
            _validation_message(self._error("model_type", ())) == "请求体应为 JSON 对象"
        )

    def test_nested_model_type(self):
        assert (
            _validation_message(self._error("model_type", ("data", 0)))
            == "字段 data[0] 应该是 Object 类型"
        )

    def test_pattern_mismatch(self):
        assert (
            _validation_message(self._error("string_pattern_mismatch", ("url",)))
            == "字段 url 不符合格式要求"
        )


class TestValidateJsonDecorator:
    def test_valid_payload_passes_dict(self):
        app = Flask(__name__)

        @app.route("/save", methods=["POST"])
        @validate_api(SaveCollectRequest)
        def save(params):
            return params

        with app.test_request_context(
            "/save",
            method="POST",
            json={"name": "x", "type": "b", "url": "https://x", "pid": "5"},
        ):
            assert save() == {
                "id": None,
                "name": "x",
                "type": "b",
                "url": "https://x",
                "pid": 5,
            }

    def test_invalid_payload_raises_request_error(self):
        app = Flask(__name__)

        @app.route("/save", methods=["POST"])
        @validate_api(SaveCollectRequest)
        def save(params):
            return params

        with app.test_request_context("/save", method="POST", json={"name": "x"}):
            with pytest.raises(RequestValidationError) as exc:
                save()
        assert exc.value.errors[0]["type"] == "missing"

    def test_missing_json_body_rejected(self):
        app = Flask(__name__)

        @app.route("/save", methods=["POST"])
        @validate_api(SaveCollectRequest)
        def save(params):
            return params

        with app.test_request_context("/save", method="POST", json=None):
            with pytest.raises(UnsupportedMediaType):
                save()

    def test_valid_output_returns_original(self):
        app = Flask(__name__)

        @app.route("/save", methods=["POST"])
        @validate_api(SaveCollectRequest, response_model=SaveCollectResponse)
        def save(params):
            return {
                "type": "bookmark",
                "id": 1,
                "pid": 0,
                "px": 10,
                "label": "x",
                "url": "https://x",
                "depth": 1,
                "extra_field": "保留",
            }

        with app.test_request_context(
            "/save",
            method="POST",
            json={"name": "x", "type": "b", "url": "https://x", "pid": 1},
        ):
            result = save()
        assert result["id"] == 1
        assert result["extra_field"] == "保留"

    def test_invalid_output_raises_response_error(self):
        app = Flask(__name__)

        @app.route("/save", methods=["POST"])
        @validate_api(SaveCollectRequest, response_model=SaveCollectResponse)
        def save(params):
            return {"type": "bookmark", "id": 1}

        with app.test_request_context(
            "/save",
            method="POST",
            json={"name": "x", "type": "b", "url": "https://x", "pid": 1},
        ):
            with pytest.raises(ResponseValidationError) as exc:
                save()
        assert exc.value.errors[0]["type"] == "missing"

    def test_no_request_model_skips_json_parsing(self):
        app = Flask(__name__)

        @app.route("/data", methods=["POST"])
        @validate_api(response_model=ImportCollectResponse)
        def data():
            return {"count": 3}

        with app.test_request_context(
            "/data", method="POST", data=b"not-json", content_type="text/plain"
        ):
            assert data() == {"count": 3}

    def test_static_msg_written_to_g(self):
        app = Flask(__name__)

        @app.route("/data")
        @validate_api(msg="保存成功！")
        def data():
            return {"a": 1}

        with app.test_request_context("/data"):
            assert data() == {"a": 1}
            assert g.success_msg == "保存成功！"

    def test_callable_msg_written_to_g(self):
        app = Flask(__name__)

        @app.route("/data")
        @validate_api(msg=lambda r: f"count={r['count']}")
        def data():
            return {"count": 3}

        with app.test_request_context("/data"):
            data()
            assert g.success_msg == "count=3"

    def test_default_msg(self):
        app = Flask(__name__)

        @app.route("/data")
        @validate_api()
        def data():
            return {"a": 1}

        with app.test_request_context("/data"):
            data()
            assert g.success_msg == "请求成功！"


class TestRouteValidationIntegration:
    def test_save_collect_invalid_returns_chinese_fail(self):
        from src.app import create_app

        app = create_app()
        client = app.test_client()
        resp = client.post("/api/saveCollect", json={"name": "x"})
        data = resp.get_json()
        assert resp.status_code == 200
        assert data["status"] == 0
        assert data["message"].startswith("请求参数错误：")
        assert "缺少必须字段" in data["message"]
