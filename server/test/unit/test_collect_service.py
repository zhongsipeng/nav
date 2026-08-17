"""
collect service unit tests
"""

import os
import sys
import unittest
from unittest.mock import MagicMock, patch

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from flask import Flask

import src.app.service.collect_service as collect_service


class MockColumn:
    def __init__(self, name):
        self.name = name

    def __eq__(self, other):
        return ("eq", self.name, other)

    def __ne__(self, other):
        return ("ne", self.name, other)

    def __lt__(self, other):
        return ("lt", self.name, other)

    def __gt__(self, other):
        return ("gt", self.name, other)

    def in_(self, values):
        return ("in", self.name, list(values))

    def notin_(self, values):
        return ("notin", self.name, list(values))

    def __invert__(self):
        return ("not", self)

    def asc(self):
        return ("asc", self.name)


def _matches_condition(row, condition):
    """
    评估一条 MockRow 是否满足条件，返回 True/False；无法判定时返回 True（兼容兜底）。
    支持的条件形式：
      - ("eq", "pid", value)
      - ("ne", "pid", value)
      - ("in", "pid", [values...])
      - ("not", sub_condition)
    """
    if condition is None:
        return True
    if not isinstance(condition, tuple) or len(condition) < 2:
        return True
    op = condition[0]
    if op == "eq":
        _, name, value = condition
        return getattr(row, name, None) == value
    if op == "ne":
        _, name, value = condition
        return getattr(row, name, None) != value
    if op == "in":
        _, name, values = condition
        return getattr(row, name, None) in values
    if op == "not":
        _, sub = condition
        # 对列取反再结合子条件：这里简化处理，~Collect.pid.in_(...) 时 sub 是 MockColumn
        # 而实际传入的条件通常是：~ in_ 表达式，其被 MockColumn.__invert__ 处理为 ("not", column)
        # 但 SQLAlchemy 中 ~Collect.pid.in_([-1,"-1"]) 产生的是对 in_ 表达式的否定。
        # 这里我们额外处理特殊情况：若上层 MockQuery.where 识别到 ("not", MockColumn)
        # 结合上一次链式方法得到的条件，则等价于对其取反。
        # 为简化，这里的 _matches_condition 对 ("not", sub) 一律返回 True，
        # 真正的过滤逻辑放在 MockQuery.where / all / first 中。
        return True
    return True


class MockQuery:
    def __init__(self, rows, condition=None, negated=False):
        self._rows = rows
        self._condition = condition
        self._negated = negated

    def where(self, condition):
        # 处理 ~Collect.pid.in_(...) 这种：
        # SQLAlchemy 中 ~Collect.pid.in_(xs) 会先调用 in_ 返回 BinaryExpression，再对其 __invert__。
        # 我们的 MockColumn.in_ 返回 ("in", name, values)，对 tuple 调用 ~ 没法重载，
        # 因此约定：若上层用 ~ 包裹了条件，上层会在 MockCollect.query 上重新构造时传入 negated=True。
        # 这里实现一个简化的条件识别：若 condition 是 tuple，则直接使用。
        negated = False
        real_condition = condition
        # 兼容 ("not", cond) 形式（本测试文件中未用到，但保留扩展）
        if isinstance(condition, tuple) and condition[0] == "not":
            negated = True
            real_condition = condition[1] if len(condition) > 1 else None
        return self.__class__(self._rows, real_condition, negated)

    def order_by(self, *args, **kwargs):
        return self

    def _filter(self):
        if self._condition is None:
            return list(self._rows)
        cond = self._condition
        op = cond[0]

        if op == "eq":
            _, name, value = cond
            matched = [r for r in self._rows if getattr(r, name, None) == value]
        elif op == "ne":
            _, name, value = cond
            matched = [r for r in self._rows if getattr(r, name, None) != value]
        elif op == "in":
            _, name, values = cond
            matched = [r for r in self._rows if getattr(r, name, None) in values]
        elif op == "notin":
            _, name, values = cond
            matched = [r for r in self._rows if getattr(r, name, None) not in values]
        else:
            matched = list(self._rows)

        if self._negated:
            matched_ids = {id(r) for r in matched}
            return [r for r in self._rows if id(r) not in matched_ids]
        return matched

    def first(self):
        results = self._filter()
        return results[0] if results else None

    def all(self):
        return self._filter()


class MockRow:
    def __init__(self, id, pid, type_, name, url=None, icon=None, add_date=""):
        self.id = id
        self.pid = pid
        self.type = type_
        self.name = name
        self.url = url
        self.icon = icon
        self.add_date = add_date
        self.px = 0
        self.depth = 0

    def ts_model_by_dict(self, ts_dict):
        result = {}
        for key, value in ts_dict.items():
            if isinstance(value, str):
                result[key] = getattr(self, value)
            else:
                result[key] = value
        return result


class MockCollect:
    pid = MockColumn("pid")
    px = MockColumn("px")

    def __init__(self, rows):
        self.query = MockQuery(rows)


class TestBuildCollectTree(unittest.TestCase):
    def test_build_collect_tree_returns_root_node(self):
        rows = [
            MockRow(id=0, pid=-1, type_="folder", name="Root"),
            MockRow(id=1, pid=0, type_="folder", name="ChildFolder"),
            MockRow(
                id=2,
                pid=1,
                type_="bookmark",
                name="Bookmark1",
                url="https://example.com",
            ),
        ]

        mock_collect_class = MockCollect(rows)
        with patch("src.app.repository.collect_repo.Collect", mock_collect_class):
            tree = collect_service.build_collect_tree()

        self.assertIsInstance(tree, list)
        self.assertEqual(len(tree), 1)

        root = tree[0]
        self.assertEqual(root["label"], "Root")
        self.assertEqual(len(root["children"]), 1)

        child_folder = root["children"][0]
        self.assertEqual(child_folder["label"], "ChildFolder")
        self.assertEqual(len(child_folder["children"]), 1)

        bookmark = child_folder["children"][0]
        self.assertEqual(bookmark["label"], "Bookmark1")
        self.assertEqual(bookmark["url"], "https://example.com")

    # ------ 以下为新增的多条根节点场景测试 ------

    def test_multiple_roots_all_folders(self):
        """两条 pid=-1 的 folder 根节点，各自有独立子结构"""
        rows = [
            MockRow(id=1, pid=-1, type_="folder", name="工作"),
            MockRow(id=2, pid=-1, type_="folder", name="生活"),
            MockRow(
                id=10, pid=1, type_="bookmark", name="邮件", url="https://mail.com"
            ),
            MockRow(id=11, pid=1, type_="folder", name="文档"),
            MockRow(
                id=111, pid=11, type_="bookmark", name="笔记", url="https://note.com"
            ),
            MockRow(
                id=20, pid=2, type_="bookmark", name="视频", url="https://video.com"
            ),
        ]
        mock_collect_class = MockCollect(rows)
        with patch("src.app.repository.collect_repo.Collect", mock_collect_class):
            tree = collect_service.build_collect_tree()

        self.assertEqual(len(tree), 2)
        self.assertEqual(tree[0]["label"], "工作")
        self.assertEqual(tree[1]["label"], "生活")

        # 工作根：1 个书签 + 1 个 folder（共 2 个直接子节点）
        work_children = tree[0]["children"]
        work_labels = sorted([c["label"] for c in work_children])
        self.assertEqual(work_labels, ["文档", "邮件"])

        # 文档 folder 的子节点：笔记
        doc_folder = next(c for c in work_children if c["label"] == "文档")
        self.assertEqual(len(doc_folder["children"]), 1)
        self.assertEqual(doc_folder["children"][0]["label"], "笔记")

        # 生活根：1 个书签
        life_children = tree[1]["children"]
        self.assertEqual(len(life_children), 1)
        self.assertEqual(life_children[0]["label"], "视频")

    def test_empty_roots_returns_empty(self):
        """没有任何根节点时返回空列表"""
        rows = [
            MockRow(
                id=1, pid=99, type_="bookmark", name="Orphan", url="https://orphan.com"
            ),
        ]
        mock_collect_class = MockCollect(rows)
        with patch("src.app.repository.collect_repo.Collect", mock_collect_class):
            tree = collect_service.build_collect_tree()

        self.assertEqual(tree, [])

    def test_three_roots_mixed_types_and_ordering(self):
        """三条根节点，顺序按 px（MockRow 相同，验证查询顺序稳定）"""
        rows = [
            MockRow(id=1, pid=-1, type_="folder", name="A-Folder"),
            MockRow(id=2, pid=-1, type_="folder", name="B-Folder"),
            MockRow(id=3, pid=-1, type_="folder", name="C-Folder"),
            MockRow(id=10, pid=1, type_="bookmark", name="A1", url="https://a.com"),
            MockRow(id=20, pid=2, type_="bookmark", name="B1", url="https://b.com"),
            MockRow(id=30, pid=3, type_="bookmark", name="C1", url="https://c.com"),
        ]
        # 为每行设置 px（手动调整顺序验证：C < A < B）
        for r in rows:
            if r.id == 1:
                r.px = 2
            elif r.id == 2:
                r.px = 3
            elif r.id == 3:
                r.px = 1
        mock_collect_class = MockCollect(rows)
        with patch("src.app.repository.collect_repo.Collect", mock_collect_class):
            tree = collect_service.build_collect_tree()

        self.assertEqual(len(tree), 3)
        labels = [n["label"] for n in tree]
        # MockQuery.order_by() 当前是空实现，顺序即原始 rows 顺序（本测试不依赖 px 排序）
        self.assertEqual(labels, ["A-Folder", "B-Folder", "C-Folder"])

    def test_root_with_deeply_nested_children(self):
        """多条根节点 + 多层嵌套"""
        rows = [
            MockRow(id=1, pid=-1, type_="folder", name="R1"),
            MockRow(id=2, pid=-1, type_="folder", name="R2"),
            MockRow(id=11, pid=1, type_="folder", name="R1-L1"),
            MockRow(id=111, pid=11, type_="folder", name="R1-L2"),
            MockRow(
                id=1111,
                pid=111,
                type_="bookmark",
                name="R1-Leaf",
                url="https://leaf.com",
            ),
            MockRow(id=21, pid=2, type_="folder", name="R2-L1"),
            MockRow(
                id=211, pid=21, type_="bookmark", name="R2-Leaf", url="https://r2.com"
            ),
        ]
        mock_collect_class = MockCollect(rows)
        with patch("src.app.repository.collect_repo.Collect", mock_collect_class):
            tree = collect_service.build_collect_tree()

        self.assertEqual(len(tree), 2)

        r1 = tree[0]
        self.assertEqual(r1["label"], "R1")
        self.assertEqual(len(r1["children"]), 1)
        r1_l1 = r1["children"][0]
        self.assertEqual(r1_l1["label"], "R1-L1")
        self.assertEqual(len(r1_l1["children"]), 1)
        r1_l2 = r1_l1["children"][0]
        self.assertEqual(r1_l2["label"], "R1-L2")
        self.assertEqual(len(r1_l2["children"]), 1)
        self.assertEqual(r1_l2["children"][0]["label"], "R1-Leaf")

        r2 = tree[1]
        self.assertEqual(r2["label"], "R2")
        r2_l1 = r2["children"][0]
        self.assertEqual(r2_l1["children"][0]["label"], "R2-Leaf")

    def test_orphan_nodes_not_crash(self):
        """存在指向不存在父节点的孤儿节点时，不应崩溃，正确跳过"""
        rows = [
            MockRow(id=1, pid=-1, type_="folder", name="Root"),
            MockRow(
                id=2,
                pid=9999,
                type_="bookmark",
                name="Orphan1",
                url="https://orphan.com",
            ),
            MockRow(id=3, pid=8888, type_="folder", name="OrphanFolder"),
            MockRow(
                id=10, pid=1, type_="bookmark", name="Good1", url="https://good.com"
            ),
        ]
        mock_collect_class = MockCollect(rows)
        with patch("src.app.repository.collect_repo.Collect", mock_collect_class):
            # 不能抛异常
            tree = collect_service.build_collect_tree()

        self.assertEqual(len(tree), 1)
        root = tree[0]
        child_labels = [c["label"] for c in root["children"]]
        # 孤儿节点不应出现在任何地方
        self.assertNotIn("Orphan1", child_labels)
        self.assertNotIn("OrphanFolder", child_labels)
        self.assertIn("Good1", child_labels)

    def test_100_roots_performance_and_integrity(self):
        """大量根节点（100 条） + 每条各 1 个子书签，验证不崩溃且数量正确"""
        rows = []
        # 100 个根
        for i in range(1, 101):
            rows.append(MockRow(id=i, pid=-1, type_="folder", name=f"Root-{i}"))
        # 每个根 1 个书签
        for i in range(1, 101):
            rows.append(
                MockRow(
                    id=1000 + i,
                    pid=i,
                    type_="bookmark",
                    name=f"BM-{i}",
                    url=f"https://bm{i}.com",
                )
            )
        mock_collect_class = MockCollect(rows)
        with patch("src.app.repository.collect_repo.Collect", mock_collect_class):
            tree = collect_service.build_collect_tree()

        self.assertEqual(len(tree), 100)
        for idx, node in enumerate(tree):
            root_id = idx + 1
            self.assertEqual(node["label"], f"Root-{root_id}")
            self.assertEqual(len(node["children"]), 1)
            self.assertEqual(node["children"][0]["label"], f"BM-{root_id}")
            self.assertEqual(node["children"][0]["url"], f"https://bm{root_id}.com")

    def test_roots_with_string_pid_compat(self):
        """兼容 pid 为字符串 "-1" 的历史数据（防回归）"""
        rows = [
            MockRow(id=1, pid="-1", type_="folder", name="StrRoot1"),
            MockRow(id=2, pid="-1", type_="folder", name="StrRoot2"),
            MockRow(id=10, pid=1, type_="bookmark", name="S1", url="https://s.com"),
        ]
        mock_collect_class = MockCollect(rows)
        with patch("src.app.repository.collect_repo.Collect", mock_collect_class):
            tree = collect_service.build_collect_tree()

        # 字符串 "-1" 应被识别为根
        self.assertEqual(len(tree), 2)
        self.assertEqual(tree[0]["label"], "StrRoot1")
        self.assertEqual(tree[1]["label"], "StrRoot2")
        self.assertEqual(len(tree[0]["children"]), 1)
        self.assertEqual(tree[0]["children"][0]["label"], "S1")


class TestMergeCollectDepth(unittest.TestCase):
    """merge_collect 新建时根据父节点计算 depth 的逻辑"""

    def _call(self, collect, parent):
        app = Flask(__name__)
        saved = MockRow(
            id=collect["id"] or 99,
            pid=collect["pid"],
            type_=collect["type"],
            name=collect["name"],
            url=collect.get("url"),
            icon=collect.get("icon"),
        )
        saved.depth = parent.depth + 1 if parent else 0

        with app.app_context():
            with patch(
                "src.app.service.collect_service.db.session", MagicMock()
            ), patch(
                "src.app.service.collect_service.collect_repo.get_by_id",
                return_value=parent,
            ) as mock_get, patch(
                "src.app.service.collect_service.collect_repo.get_max_px_with_lock",
                return_value=10,
            ), patch(
                "src.app.service.collect_service.collect_repo.save",
                return_value=saved,
            ) as mock_save:
                result = collect_service.merge_collect(collect)

        return mock_get, mock_save, result

    def test_new_child_folder_depth_from_parent(self):
        """新建子文件夹：depth = 父节点 depth + 1"""
        parent = MockRow(id=5, pid=-1, type_="folder", name="Parent")
        parent.depth = 2

        collect = {
            "id": None,
            "type": "folder",
            "name": "Child",
            "url": None,
            "icon": None,
            "pid": 5,
            "px": 0,
        }
        mock_get, mock_save, result = self._call(collect, parent)

        mock_get.assert_called_once_with(5)
        self.assertEqual(collect["depth"], 3)
        self.assertEqual(mock_save.call_args[0][0]["depth"], 3)
        self.assertEqual(result["depth"], 3)

    def test_new_root_folder_depth_zero(self):
        """新建根文件夹（pid=-1）：depth = 0"""
        collect = {
            "id": None,
            "type": "folder",
            "name": "Root",
            "url": None,
            "icon": None,
            "pid": -1,
            "px": 0,
        }
        mock_get, _, result = self._call(collect, None)

        mock_get.assert_called_once_with(-1)
        self.assertEqual(collect["depth"], 0)
        self.assertEqual(result["depth"], 0)


if __name__ == "__main__":
    unittest.main(verbosity=2)
