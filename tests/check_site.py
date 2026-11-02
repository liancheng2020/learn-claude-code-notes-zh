#!/usr/bin/env python3
"""产物检查：链接、章节、代码与固定源码一致性。

用法：
    python3 tests/check_site.py site [--src ../learn-claude-code]
"""
import argparse
import html
import re
import sys
from html.parser import HTMLParser
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

CHAPTERS = [f"s{i:02d}" for i in range(1, 18)]
REQUIRED = ["index.html", "LICENSE.html", "404.html", ".lcc-build",
            "assets/style.css", "assets/app.js", "robots.txt"]


class Rows(HTMLParser):
    """收集每个 .code 块的行号与文本。"""

    def __init__(self):
        super().__init__()
        self.blocks = {}
        self.cur = None
        self.row = None
        self.in_ln = 0

    def handle_starttag(self, tag, attrs):
        d = dict(attrs)
        if tag == "div" and d.get("class") == "code":
            self.cur = d.get("id")
            self.blocks[self.cur] = []
        elif tag == "div" and d.get("class") == "row" and self.cur:
            self.row = {"line": int(d["data-line"]), "text": ""}
        elif tag == "span" and d.get("class") == "ln":
            self.in_ln += 1

    def handle_endtag(self, tag):
        if tag == "span" and self.in_ln:
            self.in_ln -= 1
        if tag == "div" and self.row is not None:
            self.blocks[self.cur].append(self.row)
            self.row = None

    def handle_data(self, data):
        if self.cur and self.row is not None and not self.in_ln:
            self.row["text"] += data


def fail(msg):
    print("FAIL:", msg)
    return 1


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("site", nargs="?", default="site")
    ap.add_argument("--src", default=None, help="上游 checkout，用于逐行比对")
    args = ap.parse_args()
    root = Path(args.site)
    errors = 0

    for name in REQUIRED + [f"{c}.html" for c in CHAPTERS]:
        if not (root / name).is_file():
            errors += fail(f"缺少 {name}")
    if errors:
        return 1

    html_files = list(root.glob("*.html"))
    for page in html_files:
        doc = page.read_text(encoding="utf-8")
        if page.name == "index.html":
            if doc.count('class="ch" id="') != 17:
                errors += fail("index.html 章节数不是 17")
        for href in re.findall(r'href="([^"]+)"', doc):
            if href.startswith("./") and not href.startswith("./#"):
                target = (root / href[2:].split("#")[0])
                if not target.exists():
                    errors += fail(f"{page.name} 链接不存在：{href}")
        if '<script src="./assets/app.js"' not in doc:
            errors += fail(f"{page.name} 缺少 app.js")
        for tag, attr in (("script", "src"), ("link", "href"), ("img", "src")):
            for url in re.findall(rf'<{tag}[^>]*\b{attr}="([^"]+)"', doc):
                if url.startswith("http"):
                    errors += fail(f"{page.name} 引用了外部资源：{url}")
        if "逐行" in re.search(r"<title>(.*?)</title>", doc, re.S).group(1):
            errors += fail(f"{page.name} 标题仍在宣称逐行")
        ids = set(re.findall(r'<div class="code" id="([^"]+)"', doc))
        for ref in re.findall(r'data-code="([^"]+)"', doc):
            if ref not in ids:
                errors += fail(f"{page.name} 注释指向不存在的代码块：{ref}")
        if page.name == "index.html":
            for cta in ('href="#s01"', 'href="#toc"'):
                if cta not in doc:
                    errors += fail(f"index.html 缺少入口 {cta}")
            if len(re.findall(r'class="card"', doc)) != 17:
                errors += fail("index.html 目录卡片不是 17 个")
        if page.name not in ("index.html", "LICENSE.html", "404.html"):
            if 'class="pager"' not in doc:
                errors += fail(f"{page.name} 缺少上一章/下一章")
            if page.name != "s01.html" and "上一章" not in doc:
                errors += fail(f"{page.name} 缺少上一章链接")
            if page.name != "s17.html" and "下一章" not in doc:
                errors += fail(f"{page.name} 缺少下一章链接")
        if 'data-copy="' in doc:
            ids = re.findall(r'<div class="code" id="([^"]+)"', doc)
            if len(ids) != len(set(ids)):
                errors += fail(f"{page.name} 代码块 id 重复")
        for m in re.finditer(r'class="ann"[^>]*data-from="(\d+)"[^>]*data-to="(\d+)"', doc):
            if int(m.group(1)) > int(m.group(2)):
                errors += fail(f"{page.name} 注释区间反向：{m.group(0)[:60]}")

    if args.src:
        src_root = Path(args.src)
        parser = Rows()
        parser.feed((root / "index.html").read_text(encoding="utf-8"))
        chapter_files = {}
        for cid, rows in parser.blocks.items():
            chapter = cid.split("-")[0]
            chapter_files.setdefault(chapter, rows)
        rels = {}
        from content.content_a import CH_A
        from content.content_b import CH_B
        from content.content_c import CH_C
        for ch in CH_A + CH_B + CH_C:
            rels[ch["id"]] = ch["rel"]
        for chapter, rows in chapter_files.items():
            rel = rels[chapter]
            lines = (src_root / rel).read_text(encoding="utf-8").splitlines()
            nums = [r["line"] for r in rows]
            if nums != list(range(nums[0], nums[0] + len(nums))):
                errors += fail(f"{chapter} 行号不连续")
                continue
            for r in rows:
                want = lines[r["line"] - 1].rstrip()
                got = html.unescape(r["text"]).replace("\u00a0", "").rstrip()
                if got != want:
                    errors += fail(f"{chapter} L{r['line']} 与源码不一致")
                    break

    if errors:
        print(f"{errors} 项失败")
        return 1
    print(f"OK：{len(html_files)} 个页面，链接、章节、行号检查通过")
    return 0


if __name__ == "__main__":
    sys.exit(main())
