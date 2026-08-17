from flask import (
    Blueprint,
    current_app,
    request,
    send_file,
    send_from_directory,
)

from ..common.decorator.validate import validate_api
# from ..common.task.task import example_task
from ..model.schemes.request_schemes import (
    BatchUpdateRequest,
    DeleteCollectRequest,
    SaveCollectRequest,
)
from ..model.schemes.response_schemes import (
    GetCollectResponse,
    ImportCollectResponse,
    SaveCollectResponse,
)
from ..service import collect_service

root = Blueprint("root", __name__)
api = Blueprint("api", __name__, url_prefix="/api")


# 前端文件
@root.route("/", defaults={"path": ""})
@root.route("/<path:path>")
def serve_spa(path):
    try:
        return send_from_directory(current_app.static_folder, path)
    except Exception:
        return send_from_directory(current_app.static_folder, "index.html")


# @root.route("/task_test")
# def task_test():
#     task = example_task.delay()
#     return {"tackid": task.id}
#
#
# @root.route("/task_status/<task_id>")
# def task_status(task_id):
#     result = current_app.extensions["celery"].AsyncResult(task_id)
#
#     return {
#         "ready": result.ready(),
#         "successful": result.successful(),
#         "value": result.result if result.ready() else None,
#     }


@root.route("/updateCollectIocn")
@validate_api(msg="正在更新...")
def update_collect_icon():
    return collect_service.update_collect_icon()


@api.route("/getCollect", methods=["POST"])
@validate_api(response_model=GetCollectResponse)
def get_collect():
    return collect_service.build_collect_tree()


@api.route("/saveCollect", methods=["POST"])
@validate_api(
    SaveCollectRequest,
    response_model=SaveCollectResponse,
    msg="保存成功！",
)
def save_collect(params):
    return collect_service.merge_collect(params)


@api.route("/batchUpdate", methods=["POST"])
@validate_api(BatchUpdateRequest, msg="更新成功！")
def batch_up(params):
    return collect_service.batch_update(params.get("data"))


@api.route("/delCollect", methods=["POST"])
@validate_api(DeleteCollectRequest, msg="删除成功！")
def delete_collect(params):
    return collect_service.del_collect(params.get("ids"))


@api.route("/importCollect", methods=["POST"])
@validate_api(
    response_model=ImportCollectResponse,
    msg=lambda r: f"导入成功，共 {r['count']} 条书签",
)
def import_collect():
    """书签导入接口：接收单个 HTML 书签文件，解析后清空原数据并入库"""
    return collect_service.import_collect(request.files)


@api.route("/exportCollect", methods=["GET"])
def export_collect():
    """书签导出接口：生成浏览器兼容的 Netscape Bookmark 格式 HTML 文件"""
    buffer, filename = collect_service.export_collect()
    return send_file(
        buffer, as_attachment=True, download_name=filename, mimetype="text/html"
    )
