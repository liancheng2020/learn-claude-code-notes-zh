#!/usr/bin/env python3
"""Build the static site.

- index.html : the complete tutorial in one page (sidebar + all 17 chapters)
- sNN.html   : one page per chapter (deep links, sidebar + prev/next)
- LICENSE.html, 404.html

Usage:
    python3 build.py --src /path/to/learn-claude-code [--out site]

The code shown on the pages is read from the upstream checkout, so line
numbers always match the pinned commit below.
"""
import argparse
import html
import shutil
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

from content.content_a import INTRO, CH_A          # noqa: E402
from content.content_b import CH_B                 # noqa: E402
from content.content_c import CH_C, OUTRO          # noqa: E402

COMMIT = "7226f555d48900076eba126acf37c9ed5f002b5d"
COMMIT_SHORT = COMMIT[:7]
COMMIT_DATE = "2026-10-27"
REPO = "https://github.com/shareAI-lab/learn-claude-code"
CHAPTERS = CH_A + CH_B + CH_C


def esc(s: str) -> str:
    return html.escape(s, quote=False)


class Source:
    def __init__(self, root: Path):
        self.root = root
        self.cache: dict[str, list[str]] = {}

    def lines(self, rel: str) -> list[str]:
        if rel not in self.cache:
            self.cache[rel] = (self.root / rel).read_text(encoding="utf-8").splitlines()
        return self.cache[rel]

    @staticmethod
    def find(lines: list[str], needle: str) -> int:
        hits = [i for i, line in enumerate(lines, 1) if needle in line]
        if len(hits) != 1:
            raise SystemExit(f"[anchor] {needle!r} -> {len(hits)} hits at {hits[:8]}")
        return hits[0]

    @staticmethod
    def find_in(lines: list[str], needle: str, lo: int, hi: int) -> int:
        hits = [i for i, line in enumerate(lines, 1) if needle in line and lo <= i <= hi]
        if len(hits) != 1:
            raise SystemExit(f"[anchor] {needle!r} in {lo}-{hi} -> {len(hits)} hits {hits[:8]}")
        return hits[0]


def gh_link(ch: dict, a: int, b: int) -> str:
    return f"{REPO}/blob/{COMMIT}/{ch['rel']}#L{a}-L{b}"


def render_rows(src: Source, cid: str, lines: list[str], start: int, end: int,
                notes: list[dict]) -> str:
    anchors = [(Source.find_in(lines, n["at"], start, end), n["text"]) for n in notes]
    anchors.sort(key=lambda x: x[0])
    by_pos: dict[int, list[str]] = {}
    for pos, text in anchors:
        by_pos.setdefault(pos, []).append(text)

    out, prev = [], start
    for i in range(start, end + 1):
        tx = esc(lines[i - 1]) if lines[i - 1].strip() else "&nbsp;"
        out.append(f'<div class="row" data-line="{i}"><span class="ln">{i}</span>'
                   f'<span class="tx">{tx}</span></div>')
        for text in by_pos.get(i, []):
            out.append(
                f'<div class="ann" data-from="{prev}" data-to="{i}" role="button" tabindex="0" '
                f'aria-pressed="false" aria-label="讲解，第 {prev} 到 {i} 行，回车固定高亮">'
                f'<span class="ic">注</span><p>{text}</p></div>')
            prev = i + 1
    return f'<div class="code" id="{cid}">' + "".join(out) + "</div>"


def render_code(src: Source, ch: dict) -> str:
    blocks = ch.get("blocks") or []
    if not blocks:
        return ""
    lines = src.lines(ch["rel"])
    parts = []
    spans = ([(1, len(lines), blocks[0]["notes"])] if blocks[0].get("full")
             else [(Source.find(lines, b["from"]), Source.find(lines, b["to"]), b["notes"])
                   for b in blocks])
    for idx, (a, z, notes) in enumerate(spans):
        if a > z:
            raise SystemExit(f"[range] {ch['id']}: from after to")
        parts.append(
            f'<div class="code-wrap"><div class="code-head">'
            f'<span class="dot r"></span><span class="dot y"></span><span class="dot g"></span>'
            f'<span class="file">{esc(ch["rel"])} · L{a}–{z}</span>'
            f'<a href="{gh_link(ch, a, z)}" target="_blank" rel="noreferrer">GitHub 原文 ↗</a></div>'
            + render_rows(src, f"{ch['id']}-{idx}", lines, a, z, notes) + "</div>")
    return "\n".join(parts)


def kind_of(ch: dict) -> tuple[str, str]:
    if ch.get("full"):
        return "完整源码 · 逐行", "ok"
    if ch.get("advanced"):
        return "进阶 · 关键片段", ""
    return "核心节选 · 逐行", ""


def chapter_fragment(src: Source, ch: dict, level: str = "h1") -> str:
    idea = "".join(f"<li>{esc(x)}</li>" for x in ch.get("idea", []))
    points = "".join(f'<div class="point"><b>{esc(t)}</b><p>{esc(d)}</p></div>'
                     for t, d in ch.get("points", []))
    pitfalls = "".join(f"<li>{esc(x)}</li>" for x in ch.get("pitfalls", []))
    label, cls = kind_of(ch)
    return f"""
<article class="ch" id="{ch['id']}">
  <div class="ch-head">
    <span class="num">{ch['no']}</span>
    <div class="ch-title">
      <span class="flag {cls}">{label}</span>
      <{level}>{esc(ch['title'])}<small>{esc(ch['sub'])}</small></{level}>
      <p class="quote">{esc(ch['quote'])}</p>
    </div>
  </div>
  <p class="problem"><b>解决什么问题 · </b>{esc(ch['problem'])}</p>
  {f'<div class="idea"><h2>思路</h2><ol>{idea}</ol></div>' if idea else ''}
  {render_code(src, ch)}
  {f'<div class="points"><h2>记住这几条</h2><div class="point-grid">{points}</div></div>' if points else ''}
  {f'<div class="pitfalls"><h2>容易踩的坑</h2><ul>{pitfalls}</ul></div>' if pitfalls else ''}
  {f'<div class="try"><h2>动手改一改</h2><p>{esc(ch["try"])}</p></div>' if ch.get('try') else ''}
</article>"""


def nav_anchors() -> str:
    items = ['<a href="#top"><span>00</span>导读</a>']
    for ch in CHAPTERS:
        items.append(f'<a href="#{ch["id"]}"><span>{ch["no"]}</span>{esc(ch["title"])}</a>')
    items.append('<a href="#outro"><span>18</span>学完之后</a>')
    return "\n".join(items)


def nav_files(current: str | None) -> str:
    items = ['<a href="./index.html"><span>00</span>导读</a>']
    for ch in CHAPTERS:
        cur = ' aria-current="page"' if ch["id"] == current else ""
        items.append(f'<a href="./{ch["id"]}.html"{cur}><span>{ch["no"]}</span>'
                     f'{esc(ch["title"])}</a>')
    items.append('<a href="./index.html#outro"><span>18</span>学完之后</a>')
    return "\n".join(items)


def drawer_html(nav: str) -> str:
    return f"""
<div class="toc-panel" id="tocPanel" hidden>
  <div class="toc-sheet" role="dialog" aria-modal="true" aria-label="章节目录">
    <button class="close" id="tocClose" aria-label="关闭目录">×</button>
    <h2>目录</h2>
    <nav aria-label="章节目录（移动端）">{nav}</nav>
  </div>
</div>"""


FOOTER = (
    f'<footer>本教程基于 <a href="{REPO}/tree/{COMMIT}" target="_blank" rel="noreferrer">'
    f'shareAI-lab/learn-claude-code</a> @ <code>{COMMIT_SHORT}</code>（{COMMIT_DATE}，MIT License）。'
    f'代码片段版权归原作者，讲解文字为本站新增。'
    f'<a href="./LICENSE.html">许可与来源</a>。</footer>'
)


def page(title: str, desc: str, body: str, nav: str | None = None,
         body_class: str = "") -> str:
    sidebar = ""
    if nav:
        sidebar = (f'<aside class="side"><h2>章节目录</h2><nav aria-label="章节目录">'
                   f'{nav}</nav></aside>')
    cls = "layout" + (" no-side" if not nav else "")
    return f"""<!doctype html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">
<meta name="description" content="{esc(desc)}">
<meta name="color-scheme" content="light dark">
<title>{esc(title)}</title>
<link rel="icon" href="data:,">
<link rel="stylesheet" href="./assets/style.css">
</head>
<body class="{body_class}">
<a id="top"></a>
<header class="topbar">
  <a class="brand" href="./index.html"><span class="b1">Learn Claude Code</span><span class="b2"> · 大白话教程</span></a>
  <button class="toc-btn" id="tocBtn" aria-expanded="false" aria-controls="tocPanel">目录</button>
  <span class="spacer"></span>
  <a class="plain" href="{REPO}" target="_blank" rel="noreferrer">原仓库 ↗</a>
</header>
<div class="{cls}">
{sidebar}
<main>
{body}
</main>
</div>
{drawer_html(nav or nav_anchors())}
<script src="./assets/app.js" defer></script>
</body>
</html>
"""


def build_index(src: Source) -> str:
    cards = []
    for ch in CHAPTERS:
        label, cls = kind_of(ch)
        cards.append(
            f'<a class="card" href="#{ch["id"]}"><span class="no">CH {ch["no"]}</span>'
            f'<h3>{esc(ch["title"])}</h3><p>{esc(ch["quote"])}</p>'
            f'<div class="kind {cls}">{label}</div></a>')
    chapters = "\n".join(chapter_fragment(src, ch, level="h2") for ch in CHAPTERS)
    body = f"""
<header class="hero">
  <div class="kicker">Learn Claude Code · 大白话版</div>
  <h1>看懂一个 AI 编程 Agent<br>是怎么造出来的</h1>
  <p class="lead">{esc(INTRO['lead'])}</p>
  <div class="meta"><span>17 章</span><span>Python</span>
    <span>基于 commit {COMMIT_SHORT}</span><span>逐行 + 分段讲解</span></div>
</header>
{INTRO['html']}
<h2 class="sec-title">逐章阅读</h2>
<div class="cards">{''.join(cards)}</div>
{chapters}
<section class="outro" id="outro">{OUTRO}</section>
{FOOTER}"""
    return page("Learn Claude Code · 大白话逐行教程",
                f"按 commit {COMMIT_SHORT} 逐行讲解 learn-claude-code 的 17 章，单页完整阅读。",
                body, nav=nav_anchors(), body_class="full")


def build_chapter(src: Source, idx: int, ch: dict) -> str:
    prev = CHAPTERS[idx - 1] if idx > 0 else None
    nxt = CHAPTERS[idx + 1] if idx + 1 < len(CHAPTERS) else None
    pager = ['<nav class="pager" aria-label="上下章">']
    pager.append(f'<a href="./{prev["id"]}.html"><span class="lbl">上一章</span>'
                 f'{prev["no"]} {esc(prev["title"])}</a>' if prev else "<span></span>")
    pager.append(f'<a href="./{nxt["id"]}.html" style="text-align:right"><span class="lbl">下一章</span>'
                 f'{nxt["no"]} {esc(nxt["title"])}</a>' if nxt else
                 '<a href="./index.html" style="text-align:right"><span class="lbl">回到</span>完整教程</a>')
    pager.append("</nav>")
    body = chapter_fragment(src, ch) + "".join(pager) + FOOTER
    return page(f"{ch['no']} {ch['title']} · Learn Claude Code 大白话教程",
                ch["problem"][:120], body, nav=nav_files(ch["id"]))


def build_license() -> str:
    body = f"""
<article class="ch">
  <div class="ch-head"><span class="num">§</span>
    <div class="ch-title"><h1>许可与来源</h1><p class="quote">代码 MIT，讲解文字 CC BY 4.0</p></div>
  </div>
  <p class="problem">本站在 <a href="{REPO}" target="_blank" rel="noreferrer">shareAI-lab/learn-claude-code</a>
  的基础上做中文逐行讲解。代码片段逐字取自上游 commit <code>{COMMIT_SHORT}</code>（{COMMIT_DATE}），
  版权归原作者，按 MIT License 使用；讲解文字为本站新增，按 CC BY 4.0 发布。</p>
  <h2 class="sec-title">上游 MIT 许可全文</h2>
  <pre class="license">MIT License

Copyright (c) 2024 shareAI Lab

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.</pre>
  <p class="problem">本站不是上游官方文档；上游的每章 README（英文/中文/日文）仍是权威来源。</p>
</article>
{FOOTER}"""
    return page("许可与来源 · Learn Claude Code 大白话教程",
                "上游 MIT 许可全文与本站内容许可说明。", body, nav=nav_files(None))


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--src", default="../learn-claude-code", help="upstream checkout")
    ap.add_argument("--out", default="site")
    args = ap.parse_args()

    src_root = Path(args.src)
    if not (src_root / "s01_agent_loop" / "code.py").exists():
        raise SystemExit(f"upstream checkout not found: {src_root}")
    out = Path(args.out)
    if not out.is_absolute():
        out = HERE / out
    if out.exists():
        shutil.rmtree(out)
    (out / "assets").mkdir(parents=True)
    for f in ("style.css", "app.js"):
        shutil.copy2(HERE / "assets" / f, out / "assets" / f)

    src = Source(src_root)
    pages = {"index.html": build_index(src)}
    for i, ch in enumerate(CHAPTERS):
        pages[f"{ch['id']}.html"] = build_chapter(src, i, ch)
    pages["LICENSE.html"] = build_license()
    pages["404.html"] = pages["index.html"]

    for name, doc in pages.items():
        (out / name).write_text(doc, encoding="utf-8")
    (out / ".nojekyll").write_text("", encoding="utf-8")
    (out / "robots.txt").write_text("User-agent: *\nAllow: /\n", encoding="utf-8")

    print(f"built {len(pages)} pages + assets into {out}")
    print(f"pinned {COMMIT}")


if __name__ == "__main__":
    main()
