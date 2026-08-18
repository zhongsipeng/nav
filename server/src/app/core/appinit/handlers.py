from flask import current_app, g, jsonify, request, session

from ...common.result_model import fail_model, success_model
from ...common.session import active_sessions, get_session
from ..error import (
    BusinessError,
    RequestValidationError,
    ResponseValidationError,
    UserNoLoginError,
)


def _validation_path(loc) -> str:
    """将 pydantic 错误路径渲染为 data[1].id 形式"""
    parts: list[str] = []
    for part in loc:
        if isinstance(part, int):
            if parts:
                parts[-1] = f"{parts[-1]}[{part}]"
            else:
                parts.append(f"[{part}]")
        else:
            parts.append(str(part))
    return ".".join(parts) if parts else "数据"


def _validation_message(error: dict) -> str:
    """将 pydantic 错误转为中文提示"""
    err_type = error["type"]
    path = _validation_path(error.get("loc", ()))

    if err_type == "missing":
        return f"缺少必须字段: {path}"
    if err_type in ("int_type", "int_parsing", "float_type", "float_parsing"):
        return f"字段 {path} 应该是 Number 类型"
    if err_type == "string_type":
        return f"字段 {path} 应该是 String 类型"
    if err_type == "bool_type":
        return f"字段 {path} 应该是 Boolean 类型"
    if err_type == "list_type":
        return f"字段 {path} 应该是 Array 类型"
    if err_type == "dict_type":
        return f"字段 {path} 应该是 Object 类型"
    if err_type == "model_type":
        return (
            "请求体应为 JSON 对象"
            if not error.get("loc")
            else f"字段 {path} 应该是 Object 类型"
        )
    if err_type == "string_pattern_mismatch":
        return f"字段 {path} 不符合格式要求"
    return f"字段 {path} 校验失败: {error['msg']}"


def _request_hook(app):
    @app.before_request
    def before_request():
        app.logger.info(
            f"【请求方法】{request.method}【请求路径】{request.path}【请求地址】{request.remote_addr}"
        )
        userid = get_session("login_userid")
        session_id = get_session("login_session_id")
        if userid in active_sessions and active_sessions.get(userid) != session_id:
            session.clear()

        g.exception_occurred = False

    @app.errorhandler(BusinessError)
    def handle_business_error(e):
        g.exception_occurred = True
        response = jsonify(fail_model(e.message))
        return response

    @app.errorhandler(RequestValidationError)
    def handle_request_validation_error(e):
        g.exception_occurred = True
        first_error = e.errors[0]
        response = jsonify(
            fail_model("请求参数错误：" + _validation_message(first_error))
        )
        return response

    @app.errorhandler(ResponseValidationError)
    def handle_response_validation_error(e):
        g.exception_occurred = True
        current_app.logger.error("响应数据校验失败: %s", e.errors)
        first_error = e.errors[0]
        response = jsonify(
            fail_model("响应数据错误：" + _validation_message(first_error))
        )
        return response

    @app.errorhandler(UserNoLoginError)
    def handle_login_error(e):
        g.exception_occurred = True
        # if(isinstance(e, BusinessError)):
        response = jsonify(fail_model(e.message))
        # else:
        #     response = jsonify(failModel("系统异常"))
        return response

    @app.after_request
    def wrap_response(response):
        if g.get("exception_occurred", True):
            return response
        if response.content_type != "application/json":
            return response
        try:
            data = response.get_json()
            wrapped = success_model(data, msg=g.get("success_msg", "请求成功！"))
            response.data = jsonify(wrapped).data
        except Exception as e:
            current_app.logger.exception("响应包装失败: %s", e)

        return response


def register_handlers(app):
    _request_hook(app)
