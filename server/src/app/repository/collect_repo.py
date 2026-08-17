"""收藏数据访问层"""

from sqlalchemy import func

from ..core.extensions import db
from ..model.entities import Collect


def get_root_nodes():
    """查询所有根节点（pid=-1），兼容历史字符串 "-1" 数据"""
    rows = (
        Collect.query.where(Collect.pid == -1).order_by(Collect.px.asc()).all()
    )
    if not rows:
        rows = (
            Collect.query.where(Collect.pid == "-1")
            .order_by(Collect.px.asc())
            .all()
        )
    return rows


def get_non_root_nodes():
    """查询所有非根节点（pid 不等于 -1）"""
    return (
        Collect.query.where(Collect.pid.notin_([-1, "-1"]))
        .order_by(Collect.px.asc())
        .all()
    )


def get_non_folder_nodes():
    """查询所有非 folder 类型节点"""
    return Collect.query.where(Collect.type != "folder").all()


def get_max_px_with_lock(pid):
    """加行锁查询同 pid 下的最大 px，防止并发插入产生重复 px"""
    row = (
        db.session.query(func.max(Collect.px))
        .filter(Collect.pid == pid)
        .with_for_update()
        .one()
    )
    return row[0] if row and row[0] is not None else 0


def get_by_id(id):
    """按主键查询"""
    return Collect.query.get(id)


def bulk_update(items):
    """批量更新（只做数据操作，事务由 service 提交）"""
    db.session.bulk_update_mappings(
        Collect, [Collect.filter_dict_by_model(x) for x in items]
    )


def save(data):
    """合并保存单条数据（只做数据操作，事务由 service 提交）"""
    obj = Collect(**Collect.filter_dict_by_model(data))
    return db.session.merge(obj)


def delete_by_ids(ids):
    """按 id 列表删除并返回删除条数（只做数据操作，事务由 service 提交）"""
    return (
        db.session.query(Collect)
        .filter(Collect.id.in_(ids))
        .delete(synchronize_session="fetch")
    )


def clear_all():
    """清空全部数据（不提交，配合导入流程）"""
    db.session.query(Collect).delete(synchronize_session="fetch")


def add_and_flush(data):
    """新增一条并 flush（返回对象以取得自增 id，不提交）"""
    obj = Collect(**Collect.filter_dict_by_model(data))
    db.session.add(obj)
    db.session.flush()
    return obj


def get_export_rows():
    """轻量级列查询，返回 Row 对象"""
    return (
        db.session.query(
            Collect.id,
            Collect.pid,
            Collect.name,
            Collect.type,
            Collect.url,
            Collect.icon,
            Collect.add_date,
        )
        .order_by(Collect.px.asc())
        .all()
    )
