from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def load_module(name: str, relative_path: str):
    spec = importlib.util.spec_from_file_location(name, ROOT / relative_path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


parser_module = load_module("x_article_parser", "scripts/parse_markdown.py")
upload_module = load_module("x_article_upload", "scripts/upload_markdown_to_x_article.py")
cookie_module = load_module("x_article_cookies", "scripts/export_x_cookies_from_chrome.py")


class MarkdownParserTests(unittest.TestCase):
    def test_parses_cover_body_images_and_safe_html(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            cover = root / "cover.png"
            body = root / "assets" / "chapter" / "body (1).png"
            cover.write_bytes(b"cover")
            body.parent.mkdir(parents=True)
            body.write_bytes(b"body")
            article = root / "2026-08-30-original-draft.md"
            article.write_text(
                "---\ntag: test\n---\n"
                "![cover](cover.png)\n\n"
                "# 文档标题\n\n"
                "开头 <script>alert(1)</script> **重点**。\n\n"
                "正文锚点 ![body](body%20(1).png) 之后文字。\n\n"
                "[危险链接](javascript:alert(1))\n",
                encoding="utf-8",
            )

            result = parser_module.prepare_article(str(article))

            self.assertEqual(result["title"], "original draft")
            self.assertEqual(result["cover_image"], str(cover.resolve()))
            self.assertEqual(result["expected_image_count"], 1)
            self.assertEqual(result["content_images"][0]["path"], str(body.resolve()))
            self.assertEqual(result["missing_images"], 0)
            self.assertIn("lifted 1 inline image", result["errors_fixed"][0])
            self.assertIn("&lt;script&gt;", result["html"])
            self.assertNotIn("javascript:", result["html"])
            self.assertIn("<strong>重点</strong>", result["html"])

    def test_does_not_search_unrelated_directories_for_missing_images(self):
        with tempfile.TemporaryDirectory() as directory:
            article = Path(directory) / "note.md"
            article.write_text("![missing](private.png)\n\n正文", encoding="utf-8")
            result = parser_module.prepare_article(str(article))
            self.assertFalse(result["cover_exists"])
            self.assertEqual(result["missing_images"], 1)

    def test_cli_reads_environment_and_returns_json(self):
        with tempfile.TemporaryDirectory() as directory:
            article = Path(directory) / "sample.md"
            article.write_text("# 标题\n\n短正文", encoding="utf-8")
            completed = subprocess.run(
                [sys.executable, str(ROOT / "scripts/parse_markdown.py")],
                env={"MARKDOWN_FILE": str(article)},
                capture_output=True,
                text=True,
                check=True,
            )
            self.assertEqual(json.loads(completed.stdout)["content_title"], "标题")


class UploadPlanningTests(unittest.TestCase):
    def test_frontmatter_is_skipped_when_inspecting_cover(self):
        with tempfile.TemporaryDirectory() as directory:
            article = Path(directory) / "sample.md"
            article.write_text("---\ntitle: x\n---\n\n![cover](cover.png)\n", encoding="utf-8")
            self.assertTrue(upload_module.inspect_leading_cover(article)["starts_with_image"])

    def test_text_checkpoints_work_for_short_articles(self):
        start, end = upload_module.text_checkpoints("一篇很短但有效的文章")
        self.assertEqual(start, "一篇很短但有效的文章")
        self.assertEqual(end, start)

    def test_integrated_dry_run_never_needs_browser_or_cookies(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "cover.png").write_bytes(b"cover")
            (root / "body.png").write_bytes(b"body")
            article = root / "article.md"
            article.write_text(
                "![cover](cover.png)\n\n# 标题\n\n正文锚点\n\n![body](body.png)\n",
                encoding="utf-8",
            )
            completed = subprocess.run(
                [sys.executable, str(ROOT / "scripts/upload_markdown_to_x_article.py"), str(article), "--dry-run"],
                capture_output=True,
                text=True,
                check=True,
            )
            plan = json.loads(completed.stdout)
            self.assertTrue(plan["cover_upload"])
            self.assertEqual(plan["expected_body_images"], 1)
            self.assertEqual(plan["anchors"][0]["anchor"], "正文锚点")


class CookieBoundaryTests(unittest.TestCase):
    def test_domain_match_uses_dns_boundary(self):
        self.assertTrue(cookie_module.host_matches_domain(".x.com", "x.com"))
        self.assertTrue(cookie_module.host_matches_domain("api.twitter.com", "twitter.com"))
        self.assertFalse(cookie_module.host_matches_domain("notx.com", "x.com"))
        self.assertFalse(cookie_module.host_matches_domain("twitter.com.example.org", "twitter.com"))


if __name__ == "__main__":
    unittest.main()
