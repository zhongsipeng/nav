"""
导出功能性能基准测试

测试不同数据量下 generate_bookmark_html 的执行时间，
并验证输出结果的正确性。

运行方式:
    python -m unittest app.test.test_export_performance -v
"""

import os
import sys
import time
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.app.common.utils.bookmark_util import (
    generate_bookmark_html,
    parse_bookmark_html,
)


def generate_test_data(folder_count, bookmarks_per_folder, nested_depth=1):
    """
    生成测试用书签数据。

    参数:
        folder_count: 顶层文件夹数量
        bookmarks_per_folder: 每个文件夹下的书签数量
        nested_depth: 嵌套深度 (1=无嵌套, 2=一层子文件夹, ...)

    返回:
        扁平化的书签字典列表
    """
    items = []
    current_id = 1

    def build_folder(pid, depth):
        nonlocal current_id
        folder_id = current_id
        current_id += 1
        items.append(
            {
                "id": folder_id,
                "pid": pid,
                "name": f"文件夹_{folder_id}",
                "type": "folder",
                "url": None,
                "icon": None,
                "add_date": str(folder_id),
            }
        )

        # 添加书签
        for i in range(bookmarks_per_folder):
            current_id += 1
            items.append(
                {
                    "id": current_id,
                    "pid": folder_id,
                    "name": f"书签_{current_id}",
                    "type": "bookmark",
                    "url": f"https://example{current_id}.com/path?q={i}",
                    "icon": f"data:image/png;base64,AAAA{current_id}",
                    "add_date": str(current_id),
                }
            )

        # 递归添加子文件夹
        if depth > 1:
            for _ in range(2):  # 每层 2 个子文件夹
                current_id += 1
                build_folder(folder_id, depth - 1)

    for _ in range(folder_count):
        current_id += 1
        build_folder("-1", nested_depth)

    return items


class TestExportPerformance(unittest.TestCase):
    """导出性能基准测试"""

    def measure(self, items, label=""):
        """测量 generate_bookmark_html 执行时间"""
        start = time.perf_counter()
        html = generate_bookmark_html(items)
        elapsed = time.perf_counter() - start

        # 验证输出正确性
        self.assertTrue(html.startswith("<!DOCTYPE NETSCAPE-Bookmark-file-1>"))
        dl_open = html.count("<DL>")
        dl_close = html.count("</DL>")
        self.assertEqual(dl_open, dl_close, "DL 标签未正确闭合")

        print(
            f"  [{label}] {len(items):>6} 条数据: {elapsed * 1000:.2f} ms, "
            f"HTML 大小: {len(html) / 1024:.1f} KB"
        )
        return elapsed, html

    def test_small_dataset_100(self):
        """110 条数据 (10 个顶层文件夹 x 10 书签)"""
        items = generate_test_data(10, 10)
        self.assertEqual(len(items), 110)  # 10 个顶层文件夹 + 100 个书签
        elapsed, html = self.measure(items, "100条")
        self.assertLess(elapsed, 0.05, "100条数据应在 50ms 内完成")

    def test_medium_dataset_1000(self):
        """~1000 条数据 (50 文件夹 x 20 书签)"""
        items = generate_test_data(50, 20)
        elapsed, html = self.measure(items, "1000条")
        self.assertLess(elapsed, 0.2, "1000条数据应在 200ms 内完成")

    def test_large_dataset_5000(self):
        """~5000 条数据 (100 文件夹 x 50 书签)"""
        items = generate_test_data(100, 50)
        elapsed, html = self.measure(items, "5000条")
        self.assertLess(elapsed, 1.0, "5000条数据应在 1s 内完成")

    def test_very_large_dataset_10000(self):
        """~10000 条数据 (200 文件夹 x 50 书签)"""
        items = generate_test_data(200, 50)
        elapsed, html = self.measure(items, "10000条")
        self.assertLess(elapsed, 2.0, "10000条数据应在 2s 内完成")

    def test_nested_structure(self):
        """深层嵌套结构测试 (3层嵌套)"""
        items = generate_test_data(10, 5, nested_depth=3)
        elapsed, html = self.measure(items, "嵌套3层")
        self.assertLess(elapsed, 0.1, "嵌套3层应在 100ms 内完成")

        # 验证嵌套结构正确
        parsed = parse_bookmark_html(html)
        folders = [x for x in parsed if x["type"] == "folder"]
        # 应有顶层 + 每层2个子文件夹
        self.assertGreater(len(folders), 10)

    def test_roundtrip_large_dataset(self):
        """大数据量往返测试: 生成 -> 解析 -> 验证数据一致"""
        items = generate_test_data(20, 10, nested_depth=2)
        html = generate_bookmark_html(items)

        parsed = parse_bookmark_html(html)
        original_bookmarks = [x for x in items if x["type"] == "bookmark"]
        parsed_bookmarks = [x for x in parsed if x["type"] == "bookmark"]

        self.assertEqual(
            len(original_bookmarks), len(parsed_bookmarks), "往返后书签数量应一致"
        )

        # 验证第一个书签的 URL 完整保留
        first_original = original_bookmarks[0]
        first_parsed = next(
            x for x in parsed_bookmarks if x["title"] == first_original["name"]
        )
        self.assertEqual(first_original["url"], first_parsed["url"])

    def test_empty_and_single_item(self):
        """边界情况: 空列表和单条数据"""
        # 空列表
        self.assertEqual(generate_bookmark_html([]), "")

        # 单条书签
        single = [
            {
                "id": 1,
                "pid": "-1",
                "name": "Test",
                "type": "bookmark",
                "url": "https://test.com",
                "icon": "",
                "add_date": "123",
            }
        ]
        html = generate_bookmark_html(single)
        self.assertIn("Test", html)
        self.assertIn("https://test.com", html)

    def test_special_characters_in_large_dataset(self):
        """大数据量中包含特殊字符的性能测试"""
        items = []
        for i in range(500):
            items.append(
                {
                    "id": i + 1,
                    "pid": "-1",
                    "name": f'<Test & Co> #{i} "quotes"',
                    "type": "bookmark",
                    "url": f"https://example.com?a={i}&b=<tag>",
                    "icon": "",
                    "add_date": str(i),
                }
            )
        elapsed, html = self.measure(items, "特殊字符500条")
        self.assertLess(elapsed, 0.1)

        # 验证转义正确
        self.assertIn("&lt;Test &amp; Co&gt;", html)
        self.assertNotIn("<Test & Co>", html)


if __name__ == "__main__":
    unittest.main(verbosity=2)
