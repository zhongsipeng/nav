import asyncio
import io
import time
from datetime import datetime

# from ..common.task.task import update_icon
from ..common.utils.bookmark_util import (
    allowed_bookmark_file,
    generate_bookmark_html,
    parse_bookmark_html,
    validate_file_size,
)
from ..common.utils.http_util import (
    batch_get_favicon_base64,
    get_favicon_as_base64,
    get_website_title,
)
from ..core.error import raise_business_msg
from ..core.extensions import db
from ..model.schemes.request_schemes import SaveCollectRequest
from ..repository import collect_repo

MAPPING = {
    "type": "type",
    "id": "id",
    "pid": "pid",
    "px": "px",
    "label": "name",
    "url": "url",
    "icon": "icon",
    "depth": "depth",
}


def build_collect_tree():
    """
    构建收藏树结构。

    支持多个根节点（pid=-1 的多条数据），将所有根节点返回为列表。
    根节点的 children 中包含：
      - 其 pid == 根节点.id 的文件夹（从 folder_bus 中取）
      - 其 pid == 根节点.id 的书签（直接构造节点）
    子文件夹的 children 中包含：
      - 所有 pid == 该文件夹.id 的文件夹和书签

    错误处理：
      - 若查询异常，向上抛出 SQLAlchemy 异常，由调用方统一处理
      - 若存在 pid 指向不存在父节点的孤儿节点，跳过不报错（容错）

    :return: List[Dict]，每个元素是一个根节点（可能为 folder 或其他类型）
    """
    folder_bus = {}
    root_nodes_data = collect_repo.get_root_nodes()

    if not root_nodes_data:
        return []

    # 查询所有非根节点（pid 不等于 -1 的）
    non_root_rows = collect_repo.get_non_root_nodes()

    # ----- 第一步：构建所有 folder 的映射（包含根节点中类型为 folder 的项） -----
    # 先处理非根节点中的 folder
    for item in non_root_rows:
        if item.type == "folder":
            node = item.ts_model_by_dict(MAPPING)
            node["children"] = []
            folder_bus[item.id] = node

    # 再处理根节点中的 folder（可能作为其他非根节点的父）
    root_ids = set()
    for root in root_nodes_data:
        # 统一 pid 类型做比较：将 root.id 转成 int 以便与子节点 pid 匹配
        try:
            root_ids.add(int(root.id))
        except (TypeError, ValueError):
            root_ids.add(root.id)
        if root.type == "folder":
            if root.id not in folder_bus:
                node = root.ts_model_by_dict(MAPPING)
                node["children"] = []
                folder_bus[root.id] = node

    # ----- 第二步：把非根节点挂到对应的父 folder 中 -----
    for item in non_root_rows:
        # 规范化 pid 类型：子节点 pid 存的是 Integer，根节点 id 也是 Integer
        parent_id = item.pid
        # 若 pid 是字符串 "-1"，说明该节点本该是根但被误写到非根里，跳过（不会挂到任何 folder）
        if parent_id in (-1, "-1"):
            continue
        if parent_id in folder_bus:
            if item.type == "folder":
                folder_bus[parent_id]["children"].append(folder_bus[item.id])
            else:
                node = item.ts_model_by_dict(MAPPING)
                folder_bus[parent_id]["children"].append(node)
        # 其他情况：pid 不在任何已知 folder 中（孤儿节点）→ 静默跳过（容错）

    # ----- 第三步：构建每个根节点的 children -----
    # 注意：第二步已把所有 pid 等于某个 folder.id 的子节点（folder 和非 folder）
    # 挂接到 folder_bus[parent_id]["children"] 中。根 folder 在第一步补录进了 folder_bus，
    # 因此根 folder 的 children 在第二步已经填充完成，这里直接复用即可，不可再次遍历追加，
    # 否则非 folder 子节点会重复（folder 子节点因有去重保护不会重复，但非 folder 没有）。
    result = []
    for root in root_nodes_data:
        if root.type == "folder" and root.id in folder_bus:
            # folder 根节点：children 已在第二步通过 folder_bus[parent_id] 完成挂接
            root_node = folder_bus[root.id]
        else:
            # 非 folder 根节点（罕见）：第二步因其不在 folder_bus 中而跳过，此处手动挂接子节点
            root_node = root.ts_model_by_dict(MAPPING)
            root_node["children"] = []
            for item in non_root_rows:
                try:
                    match = int(item.pid) == int(root.id)
                except (TypeError, ValueError):
                    match = item.pid == root.id
                if not match:
                    continue
                if item.type == "folder" and folder_bus.get(item.id):
                    # folder 子节点从 folder_bus 取（其自身的 children 已在第二步填好）
                    root_node["children"].append(folder_bus[item.id])
                else:
                    root_node["children"].append(item.ts_model_by_dict(MAPPING))

        result.append(root_node)

    return result


def batch_update(data):
    with db.session.begin():
        collect_repo.bulk_update(data)


def merge_collect(collect: SaveCollectRequest):

    # 新建且未传 name：根据 url 抓取网站标题
    if collect["type"] != "folder":
        # 新建
        if not collect["id"]:
            collect["icon"] = get_favicon_as_base64(collect["url"])
            time.sleep(1)
        # 业务规则：若未传 name，则尝试抓取网站标题作为 name
        if not collect.get("name"):
            web_title = get_website_title(collect["url"])
            collect["name"] = web_title or collect["name"]

    # 业务规则：px 为空时，取同 pid 下最大 px + 10 作为当前 px
    # 使用 SELECT ... FOR UPDATE 保证并发场景下的原子性（需 InnoDB 等支持行锁的引擎）
    # 注意：db.session.begin() 要求进入块时 session 尚未开始任何事务（autobegin），
    # 因此本方法内必须先于任何查询执行该上下文。
    with db.session.begin():
        # 新建时根据父节点计算 depth：根节点（pid=-1 或无父节点）为 0，否则为父节点 depth + 1
        if not collect["id"]:
            parent = collect_repo.get_by_id(collect["pid"])
            collect["depth"] = (
                parent.depth + 1 if parent and parent.depth is not None else 0
            )

            pid_value = collect.get("pid")
            # 加行锁查询同 pid 下的最大 px，防止并发插入产生重复 px
            max_px = collect_repo.get_max_px_with_lock(pid_value)
            collect["px"] = max_px + 10

        data = collect_repo.save(collect)
    return data.ts_model_by_dict(MAPPING)


def del_collect(ids):
    with db.session.begin():
        delete_count = collect_repo.delete_by_ids(ids)
        if delete_count != len(ids):
            raise_business_msg("删除失败")


def update_collect_icon():
    """更新所有书签图标（celery 任务暂时注释，先保持空操作）"""
    # data = collect_repo.get_non_folder_nodes()
    #
    # for item in data:
    #     update_icon.delay(item.id)


# ===== 书签导入/导出 =====


def import_collect(files):
    """
    导入书签文件:
        1. 校验文件类型与大小
        2. 解析 HTML 书签
        3. 清空原有 Collect 数据
        4. 批量插入新数据
    """

    if "file" not in files:
        raise_business_msg("未检测到上传文件")
    file = files["file"]
    if file.filename == "":
        raise_business_msg("未选择文件")
    filename = file.filename
    file_stream = file.stream
    if not allowed_bookmark_file(filename):
        raise_business_msg("仅支持 .html 或 .htm 书签文件")

    content = file_stream.read()
    try:
        validate_file_size(content)
    except ValueError as e:
        raise_business_msg(str(e))

    try:
        html_text = content.decode("utf-8", errors="ignore")
    except Exception:
        raise_business_msg("文件编码无法识别")

    data = parse_bookmark_html(html_text)
    if not data:
        raise_business_msg("未解析到任何书签数据，请检查文件格式")

    # 批量获取图标
    icon_urls = [item.get("url") for item in data if item.get("url")]
    icon_dict = {}
    icon_dict = asyncio.run(batch_get_favicon_base64(icon_urls, max_concurrent=100))

    with db.session.begin():
        # 清空原有数据
        collect_repo.clear_all()

        folder_bus = {}
        for item in data:
            m = {
                "name": item["title"],
                "type": item["type"],
                "url": item.get("url"),
                "icon": icon_dict.get(item.get("url")) or item.get("icon"),
                "add_date": item.get("add_date"),
                "tags": item.get("tags"),
                "depth": len(item["folder"].split("/")) if item["folder"] else 0,
            }
            if item["folder"] in folder_bus:
                m["pid"] = folder_bus[item["folder"]]["id"]
                m["px"] = folder_bus[item["folder"]]["px"]
                folder_bus[item["folder"]]["px"] += 1
            else:
                m["pid"] = "-1"
                m["px"] = 0
            obj = collect_repo.add_and_flush(m)

            if item["type"] == "folder":
                folder_path = (
                    "/".join([item["folder"], item["title"]])
                    if item["folder"]
                    else item["title"]
                )
                folder_bus[folder_path] = {"id": obj.id, "px": 1}

    return {"count": len(data)}


def export_collect():
    """
    导出书签为浏览器兼容的 Netscape Bookmark 格式 HTML。
    使用轻量级列查询替代完整 ORM 对象，大幅减少内存分配和对象创建开销。
    """
    # 轻量级列查询：只取需要的字段，返回 Row 对象而非完整 ORM 实例
    rows = collect_repo.get_export_rows()

    if not rows:
        raise_business_msg("暂无书签数据可导出")

    items = [
        {
            "id": r.id,
            "pid": r.pid,
            "name": r.name,
            "type": r.type,
            "url": r.url,
            "icon": r.icon,
            "add_date": r.add_date,
        }
        for r in rows
    ]
    html_content = generate_bookmark_html(items)
    if not html_content:
        raise_business_msg("暂无书签数据可导出")
    filename = f"bookmarks_{datetime.now().strftime('%Y_%m_%d')}.html"
    buffer = io.BytesIO(html_content.encode("utf-8"))
    buffer.seek(0)
    return buffer, filename
