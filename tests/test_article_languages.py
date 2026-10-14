"""Check language coverage, stable navigation, and shared experiment evidence."""
import importlib.util
from html.parser import HTMLParser
from pathlib import Path
import re
import unittest
from urllib.parse import unquote, urlsplit

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("article_build", ROOT / "tutorial/build.py")
builder = importlib.util.module_from_spec(spec)
spec.loader.exec_module(builder)


class Page(HTMLParser):
    def __init__(self, text):
        super().__init__()
        self.ids, self.links, self.text = [], [], []
        self.hidden = 0
        self.feed(text)

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag in ("script", "style"):
            self.hidden += 1
        if "id" in attrs:
            self.ids.append(attrs["id"])
        if tag == "a" and "href" in attrs:
            self.links.append(attrs["href"])

    def handle_endtag(self, tag):
        if tag in ("script", "style"):
            self.hidden -= 1

    def handle_data(self, text):
        if not self.hidden:
            self.text.append(text)


class ArticleLanguageTests(unittest.TestCase):
    def test_default_english_and_matching_navigation(self):
        en, zh = builder.build(), builder.build("zh-CN")
        self.assertIn('<html lang="en">', en)
        self.assertIn('<html lang="zh-CN">', zh)
        a, b = Page(en), Page(zh)
        self.assertEqual(a.ids, b.ids)
        self.assertEqual(len(a.ids), len(set(a.ids)))
        self.assertEqual(len(re.findall(r'<section id="ch\d+"', en)), 12)
        self.assertIn("guide.zh-CN.html", a.links)
        self.assertIn("guide.html", b.links)
        self.assertFalse(re.search(r"[\u4e00-\u9fff]", "".join(a.text).replace("简体中文", "")))
        for filename, page in (("guide.html", en), ("guide.zh-CN.html", zh)):
            self.assertEqual((ROOT / filename).read_text(encoding="utf-8"), page)

    def test_both_versions_include_the_same_code_and_experiment_views(self):
        for i in range(1, 13):
            zh = (ROOT / "tutorial" / f"{i:02d}.html").read_text(encoding="utf-8")
            en = (ROOT / "tutorial/en" / f"{i:02d}.html").read_text(encoding="utf-8")
            self.assertEqual(re.findall(r"\{\{(?:code|experiment):[^}]+\}\}", zh),
                             re.findall(r"\{\{(?:code|experiment):[^}]+\}\}", en), i)
            self.assertEqual(zh.count("<h3>"), en.count("<h3>"), i)
        for language in ("en", "zh-CN"):
            page = Page(builder.build(language))
            for link in page.links:
                parsed = urlsplit(link)
                if parsed.scheme:
                    continue
                if parsed.path:
                    self.assertTrue((ROOT / unquote(parsed.path)).exists(), link)
                elif parsed.fragment:
                    self.assertIn(unquote(parsed.fragment), page.ids)

    def test_readme_defaults_to_english_with_reciprocal_links(self):
        en = (ROOT / "README.md").read_text(encoding="utf-8")
        zh = (ROOT / "README.zh-CN.md").read_text(encoding="utf-8")
        self.assertIn("[简体中文](README.zh-CN.md)", en)
        self.assertIn("[English](README.md)", zh)
        self.assertIn("[English HTML](guide.html)", en)
        self.assertIn("[中文 HTML](guide.zh-CN.html)", zh)
