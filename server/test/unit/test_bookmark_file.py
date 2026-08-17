"""
bookmark_file.py 导出功能单元测试

重点测试 generate_bookmark_html:
    1. 空列表
    2. 仅书签无文件夹
    3. 嵌套文件夹 + 书签
    4. HTML 特殊字符转义
    5. 往返测试: 生成 -> 解析 -> 验证数据一致
    6. 完整浏览器书签格式校验
"""

import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.app.common.utils.bookmark_util import (
    MAX_BOOKMARK_FILE_SIZE,
    allowed_bookmark_file,
    generate_bookmark_html,
    parse_bookmark_html,
    validate_file_size,
)


class TestGenerateBookmarkHtml(unittest.TestCase):
    """generate_bookmark_html 测试集"""

    # ------------------------------------------------------------------
    # 1. 空列表
    # ------------------------------------------------------------------
    def test_empty_list_returns_empty(self):
        result = generate_bookmark_html([])
        self.assertEqual(result, "")

    # ------------------------------------------------------------------
    # 2. 仅书签无文件夹
    # ------------------------------------------------------------------
    def test_flat_bookmarks_only(self):
        items = [
            {
                "id": 1,
                "pid": "-1",
                "name": "Google",
                "type": "bookmark",
                "url": "https://google.com",
                "icon": "",
                "add_date": "1700000000",
            },
            {
                "id": 2,
                "pid": "-1",
                "name": "GitHub",
                "type": "bookmark",
                "url": "https://github.com",
                "icon": "",
                "add_date": "1700000001",
            },
        ]
        result = generate_bookmark_html(items)
        self.assertIn("Google", result)
        self.assertIn("https://google.com", result)
        self.assertIn("GitHub", result)
        self.assertIn("https://github.com", result)
        self.assertIn("<!DOCTYPE NETSCAPE-Bookmark-file-1>", result)

    def test_flat_bookmarks_numeric_negative_pid(self):
        items = [
            {
                "id": 1,
                "pid": -1,
                "name": "Google",
                "type": "bookmark",
                "url": "https://google.com",
                "icon": "",
                "add_date": "1700000000",
            },
            {
                "id": 2,
                "pid": -1,
                "name": "GitHub",
                "type": "bookmark",
                "url": "https://github.com",
                "icon": "",
                "add_date": "1700000001",
            },
        ]
        result = generate_bookmark_html(items)
        self.assertIn("Google", result)
        self.assertIn("https://google.com", result)
        self.assertIn("GitHub", result)
        self.assertIn("https://github.com", result)
        self.assertIn("<!DOCTYPE NETSCAPE-Bookmark-file-1>", result)

    # ------------------------------------------------------------------
    # 3. 嵌套文件夹 + 书签
    # ------------------------------------------------------------------
    def test_nested_folders_with_bookmarks(self):
        items = [
            {
                "id": 1,
                "pid": "-1",
                "name": "开发",
                "type": "folder",
                "url": None,
                "icon": None,
                "add_date": "",
            },
            {
                "id": 2,
                "pid": 1,
                "name": "GitHub",
                "type": "bookmark",
                "url": "https://github.com",
                "icon": "",
                "add_date": "1700000000",
            },
            {
                "id": 3,
                "pid": 1,
                "name": "Stack Overflow",
                "type": "bookmark",
                "url": "https://stackoverflow.com",
                "icon": "",
                "add_date": "1700000001",
            },
            {
                "id": 4,
                "pid": "-1",
                "name": "工具",
                "type": "folder",
                "url": None,
                "icon": None,
                "add_date": "",
            },
            {
                "id": 5,
                "pid": 4,
                "name": "Google",
                "type": "bookmark",
                "url": "https://google.com",
                "icon": "",
                "add_date": "1700000002",
            },
        ]
        result = generate_bookmark_html(items)

        # 验证文件夹
        self.assertIn("<H3", result)
        self.assertIn("开发", result)
        self.assertIn("工具", result)

        # 验证书签
        self.assertIn("GitHub", result)
        self.assertIn("https://github.com", result)
        self.assertIn("Stack Overflow", result)
        self.assertIn("Google", result)

        # 验证嵌套结构: 文件夹的 <DL> 内包含书签
        dev_idx = result.index("开发")
        github_idx = result.index("GitHub")
        self.assertGreater(github_idx, dev_idx, "GitHub 应在开发文件夹之后")

    # ------------------------------------------------------------------
    # 4. HTML 特殊字符转义
    # ------------------------------------------------------------------
    def test_html_special_characters_escaped(self):
        items = [
            {
                "id": 1,
                "pid": "-1",
                "name": "<Test & Co>",
                "type": "bookmark",
                "url": "https://example.com?a=1&b=2",
                "icon": "",
                "add_date": "",
            },
        ]
        result = generate_bookmark_html(items)

        # < > & 应被转义
        self.assertIn("&lt;Test &amp; Co&gt;", result)
        self.assertIn("https://example.com?a=1&amp;b=2", result)
        # 不应包含未转义的原始字符
        self.assertNotIn("<Test & Co>", result)

    # ------------------------------------------------------------------
    # 5. 往返测试: 生成 -> 解析 -> 验证数据一致
    # ------------------------------------------------------------------
    def test_roundtrip_generate_then_parse(self):
        items = [
            {
                "id": 1,
                "pid": "-1",
                "name": "文件夹A",
                "type": "folder",
                "url": None,
                "icon": None,
                "add_date": "1700000000",
            },
            {
                "id": 2,
                "pid": 1,
                "name": "书签1",
                "type": "bookmark",
                "url": "https://example1.com",
                "icon": "icon1",
                "add_date": "1700000001",
            },
            {
                "id": 3,
                "pid": 1,
                "name": "子文件夹B",
                "type": "folder",
                "url": None,
                "icon": None,
                "add_date": "1700000002",
            },
            {
                "id": 4,
                "pid": 3,
                "name": "书签2",
                "type": "bookmark",
                "url": "https://example2.com",
                "icon": "icon2",
                "add_date": "1700000003",
            },
        ]
        html = generate_bookmark_html(items)
        parsed = parse_bookmark_html(html)

        # 验证解析出的数据数量
        self.assertEqual(len(parsed), 4)

        # 验证文件夹
        folders = [x for x in parsed if x["type"] == "folder"]
        self.assertEqual(len(folders), 2)
        folder_names = [f["title"] for f in folders]
        self.assertIn("文件夹A", folder_names)
        self.assertIn("子文件夹B", folder_names)

        # 验证书签
        bookmarks = [x for x in parsed if x["type"] == "bookmark"]
        self.assertEqual(len(bookmarks), 2)

        # 验证书签1
        b1 = next(b for b in bookmarks if b["title"] == "书签1")
        self.assertEqual(b1["url"], "https://example1.com")
        self.assertEqual(b1["icon"], "icon1")

        # 验证书签2
        b2 = next(b for b in bookmarks if b["title"] == "书签2")
        self.assertEqual(b2["url"], "https://example2.com")

        # 验证文件夹层级关系
        sub_folder = next(f for f in folders if f["title"] == "子文件夹B")
        self.assertIn("文件夹A", sub_folder["folder"])

    # ------------------------------------------------------------------
    # 6. 完整浏览器书签格式校验
    # ------------------------------------------------------------------
    def test_netscape_bookmark_format(self):
        items = [
            {
                "id": 1,
                "pid": "-1",
                "name": "Test",
                "type": "bookmark",
                "url": "https://test.com",
                "icon": "icon_data",
                "add_date": "123",
            },
        ]
        result = generate_bookmark_html(items)

        # 验证 Netscape Bookmark 格式头
        self.assertTrue(result.startswith("<!DOCTYPE NETSCAPE-Bookmark-file-1>"))
        self.assertIn(
            '<META HTTP-EQUIV="Content-Type" CONTENT="text/html; charset=UTF-8">',
            result,
        )
        self.assertIn("<TITLE>Bookmarks</TITLE>", result)
        self.assertIn("<H1>Bookmarks</H1>", result)

        # 验证 <DL> 标签闭合
        dl_open = result.count("<DL>")
        dl_close = result.count("</DL>")
        self.assertEqual(dl_open, dl_close, "<DL> 标签未正确闭合")

        # 验证 <A> 标签属性
        self.assertIn('HREF="https://test.com"', result)
        self.assertIn('ADD_DATE="123"', result)
        self.assertIn('ICON="icon_data"', result)


class TestAllowedBookmarkFile(unittest.TestCase):
    """文件类型校验测试"""

    def test_valid_html_extension(self):
        self.assertTrue(allowed_bookmark_file("bookmarks.html"))

    def test_valid_htm_extension(self):
        self.assertTrue(allowed_bookmark_file("bookmarks.htm"))

    def test_invalid_extension(self):
        self.assertFalse(allowed_bookmark_file("bookmarks.txt"))
        self.assertFalse(allowed_bookmark_file("bookmarks.json"))
        self.assertFalse(allowed_bookmark_file("bookmarks.csv"))

    def test_no_extension(self):
        self.assertFalse(allowed_bookmark_file("bookmarks"))

    def test_empty_filename(self):
        self.assertFalse(allowed_bookmark_file(""))
        self.assertFalse(allowed_bookmark_file(None))

    def test_case_insensitive(self):
        self.assertTrue(allowed_bookmark_file("Bookmarks.HTML"))
        self.assertTrue(allowed_bookmark_file("Bookmarks.HTM"))


class TestValidateFileSize(unittest.TestCase):
    """文件大小校验测试"""

    def test_empty_content_raises(self):
        with self.assertRaises(ValueError) as ctx:
            validate_file_size(b"")
        self.assertIn("为空", str(ctx.exception))

    def test_valid_size_passes(self):
        validate_file_size(b"valid content")

    def test_oversized_content_raises(self):
        oversized = b"x" * (MAX_BOOKMARK_FILE_SIZE + 1)
        with self.assertRaises(ValueError) as ctx:
            validate_file_size(oversized)
        self.assertIn("过大", str(ctx.exception))


class TestParseBookmarkHtml(unittest.TestCase):
    """书签解析测试"""

    def test_parse_simple_html(self):
        html = (
            "<!DOCTYPE NETSCAPE-Bookmark-file-1>"
            "<DL><p>"
            '<DT><A HREF="https://example.com" ADD_DATE="123">Example</A>'
            "</DL><p>"
        )
        result = parse_bookmark_html(html)
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["title"], "Example")
        self.assertEqual(result[0]["url"], "https://example.com")
        self.assertEqual(result[0]["add_date"], "123")

    def test_parse_with_nested_folders(self):
        html = (
            "<DL><p>"
            "<DT><H3>Folder1</H3>"
            "<DL><p>"
            '<DT><A HREF="https://a.com">A</A>'
            "</DL><p>"
            "</DL><p>"
        )
        result = parse_bookmark_html(html)
        self.assertEqual(len(result), 2)
        folder = next(x for x in result if x["type"] == "folder")
        self.assertEqual(folder["title"], "Folder1")
        bookmark = next(x for x in result if x["type"] == "bookmark")
        self.assertEqual(bookmark["title"], "A")
        self.assertEqual(bookmark["folder"], "Folder1")


if __name__ == "__main__":
    unittest.main(verbosity=2)
