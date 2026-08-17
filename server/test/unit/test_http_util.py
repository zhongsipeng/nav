"""http_util 网页标题与图标获取单元测试"""

from unittest.mock import patch

from src.app.common.utils.http_util import get_favicon_as_base64, get_website_title


class FakeResponse:
    def __init__(self, content=b"", text="", content_type=""):
        self.content = content
        self.text = text
        self.headers = {"content-type": content_type}

    def raise_for_status(self):
        return None


class TestGetWebsiteTitle:
    def test_title_tag(self):
        html = "<html><head><title>  My Site  </title></head></html>"
        with patch(
            "src.app.common.utils.http_util.requests.get",
            return_value=FakeResponse(text=html),
        ):
            assert get_website_title("https://example.com/") == "My Site"

    def test_og_title_fallback(self):
        html = '<html><head><meta property="og:title" content="OG Title"></head></html>'
        with patch(
            "src.app.common.utils.http_util.requests.get",
            return_value=FakeResponse(text=html),
        ):
            assert get_website_title("https://example.com/") == "OG Title"

    def test_failure_returns_none(self):
        with patch(
            "src.app.common.utils.http_util.requests.get",
            side_effect=Exception("boom"),
        ):
            assert get_website_title("https://example.com") is None


class TestGetFaviconAsBase64:
    def test_root_favicon_first(self):
        """优先请求根目录 /favicon.ico，成功则不再抓取页面"""
        icon = b"\x00\x00\x01\x00fakeico"

        def fake_get(url, headers=None, timeout=None):
            return FakeResponse(content=icon, content_type="image/x-icon")

        with patch(
            "src.app.common.utils.http_util.requests.get", side_effect=fake_get
        ) as mock_get:
            result = get_favicon_as_base64("https://example.com/page")

        assert result.startswith("data:image/x-icon;base64,")
        assert len(mock_get.call_args_list) == 1
        assert mock_get.call_args_list[0].args[0] == "https://example.com/favicon.ico"

    def test_fallback_to_page_link(self):
        """根目录失败（返回 HTML）时抓取页面解析 <link rel="icon">"""
        page_html = '<html><head><link rel="icon" href="/static/fav.png"></head></html>'
        icon = b"\x89PNG\r\n\x1a\nfake"
        responses = {
            "https://example.com/favicon.ico": FakeResponse(
                content=b"<html>error page</html>", content_type="text/html"
            ),
            "https://example.com/a": FakeResponse(text=page_html, content_type="text/html"),
            "https://example.com/static/fav.png": FakeResponse(content=icon),
        }

        def fake_get(url, headers=None, timeout=None):
            return responses[url]

        with patch(
            "src.app.common.utils.http_util.requests.get", side_effect=fake_get
        ) as mock_get:
            result = get_favicon_as_base64("https://example.com/a")

        assert result.startswith("data:image/png;base64,")
        urls = [c.args[0] for c in mock_get.call_args_list]
        assert urls == [
            "https://example.com/favicon.ico",
            "https://example.com/a",
            "https://example.com/static/fav.png",
        ]

    def test_all_fail_returns_none(self):
        def fake_get(url, headers=None, timeout=None):
            raise Exception("down")

        with patch(
            "src.app.common.utils.http_util.requests.get", side_effect=fake_get
        ):
            assert get_favicon_as_base64("https://example.com") is None
