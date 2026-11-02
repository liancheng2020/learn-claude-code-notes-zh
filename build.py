#!/usr/bin/env python3
"""Build the static site.

- index.html : the complete tutorial in one page (sidebar + all 17 chapters)
- sNN.html   : one page per chapter (deep links)
- LICENSE.html, 404.html

Usage:
    python3 build.py --src /path/to/learn-claude-code [--out site]

Safety rules for --out:
  * the path is resolved (.. and symlinks included) and checked against the
    project root, the upstream checkout, their ancestors, $HOME and /;
  * an existing non-empty directory is only replaced when it carries the
    .lcc-build marker written by this script;
  * the site is generated into a temporary directory first and swapped in
    only after validation, so a failed build keeps the previous site.

The code shown on the pages is read from the pinned upstream checkout, whose
git HEAD and tracked-file cleanliness are verified before any rendering.
"""
import argparse
import html
import io
import keyword
import os
import re
import shutil
import subprocess
import sys
import tempfile
import tokenize
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

from content.content_a import INTRO, CH_A          # noqa: E402
from content.content_b import CH_B                 # noqa: E402
from content.content_c import CH_C, OUTRO          # noqa: E402

COMMIT = "7226f555d48900076eba126acf37c9ed5f002b5d"
COMMIT_SHORT = COMMIT[:7]
COMMIT_DATE = "2026-10-27"
UPSTREAM = "https://github.com/shareAI-lab/learn-claude-code"
TUTORIAL_REPO = "https://github.com/liancheng2020/learn-claude-code-notes-zh"
PAGES = ["index.html", "LICENSE.html", "404.html"]
MARKER = ".lcc-build"
CHAPTERS = CH_A + CH_B + CH_C


def esc(s: str) -> str:
    return html.escape(s, quote=False)


def die(msg: str) -> "NoReturn":  # type: ignore[valid-type]
    raise SystemExit(f"error: {msg}")


# --------------------------------------------------------------------------
# upstream checkout verification
# --------------------------------------------------------------------------

def git(src: Path, *args: str) -> str:
    try:
        r = subprocess.run(["git", "-C", str(src), *args],
                           capture_output=True, text=True)
    except FileNotFoundError:
        die("找不到 git，无法校验上游版本")
    if r.returncode != 0:
        die(f"git {' '.join(args)} 失败：{r.stderr.strip()}")
    return r.stdout.strip()


def verify_upstream(src_root: Path) -> None:
    if not src_root.is_dir():
        die(f"上游源码目录不存在：{src_root}")
    if not (src_root / "s01_agent_loop" / "code.py").is_file():
        die(f"看起来不是 learn-claude-code 仓库：{src_root}")
    if not (src_root / ".git").exists():
        die(f"上游源码缺少 .git，无法确认固定版本：{src_root}")
    head = git(src_root, "rev-parse", "HEAD")
    if head != COMMIT:
        die(f"上游版本不符：HEAD={head[:12]}，要求 {COMMIT_SHORT}。"
            f"请执行 git -C {src_root} checkout {COMMIT}")
    dirty = git(src_root, "status", "--porcelain", "--untracked-files=no")
    if dirty:
        die("上游工作区有未提交改动，拒绝生成「固定版本」教程：\n" + dirty)


# --------------------------------------------------------------------------
# output path safety
# --------------------------------------------------------------------------

def validate_out(out_arg: str, src_root: Path) -> Path:
    raw = Path(out_arg).expanduser()
    if not raw.is_absolute():
        raw = Path.cwd() / raw
    try:
        out = raw.resolve(strict=False)
    except OSError as exc:
        die(f"无法解析输出路径 {raw}：{exc}")

    root = HERE.resolve()
    src = src_root.resolve()
    forbidden = {root, src, Path("/"), Path.home()}
    for p in list(root.parents) + list(src.parents):
        forbidden.add(p)
    if out in forbidden:
        die(f"拒绝写入危险路径：{out}")
    if root.is_relative_to(out) or src.is_relative_to(out):
        die(f"输出目录不能是项目或上游源码的祖先：{out}")
    if out.is_relative_to(src):
        die(f"输出目录不能位于上游源码内：{out}")
    if not out.parent.exists():
        die(f"输出目录的父目录不存在：{out.parent}")

    if out.exists():
        if not out.is_dir():
            die(f"输出路径已存在且不是目录：{out}")
        entries = list(out.iterdir())
        if entries and not (out / MARKER).exists():
            die(f"拒绝覆盖非构建产物目录（缺少 {MARKER} 标记）：{out}\n"
                f"请换一个目录，或确认后手动删除该目录")
    return out


def install_output(tmp: Path, out: Path) -> None:
    """Swap tmp into out atomically; restore the old site on failure."""
    if not out.exists():
        tmp.rename(out)
        return
    backup = out.with_name(f".{out.name}.bak-{os.getpid()}")
    if backup.exists():
        shutil.rmtree(backup, ignore_errors=True)
    out.rename(backup)
    try:
        tmp.rename(out)
    except Exception:
        backup.rename(out)
        raise
    shutil.rmtree(backup, ignore_errors=True)


# --------------------------------------------------------------------------
# source parsing & highlighting
# --------------------------------------------------------------------------

KEYWORDS = set(keyword.kwlist) | {"self", "cls", "True", "False", "None"}
TOKEN_CLASS = {
    tokenize.STRING: "str",
    tokenize.COMMENT: "com",
    tokenize.NUMBER: "num",
}


def build_highlights(text: str) -> dict[int, list[tuple[int, int, str]]]:
    spans: dict[int, list[tuple[int, int, str]]] = {}
    try:
        for tok in tokenize.generate_tokens(io.StringIO(text).readline):
            if tok.type in (tokenize.ENCODING, tokenize.ENDMARKER,
                            tokenize.NEWLINE, tokenize.NL,
                            tokenize.INDENT, tokenize.DEDENT):
                continue
            srow, scol = tok.start
            erow, ecol = tok.end
            if srow != erow:          # multi-line strings: leave unstyled
                continue
            cls = TOKEN_CLASS.get(tok.type)
            if tok.type == tokenize.NAME and tok.string in KEYWORDS:
                cls = "kw"
            if cls:
                spans.setdefault(srow, []).append((scol, ecol, cls))
    except (tokenize.TokenError, IndentationError):
        return {}
    return spans


class Source:
    def __init__(self, root: Path):
        self.root = root
        self.cache: dict[str, list[str]] = {}
        self.highlights: dict[str, dict[int, list[tuple[int, int, str]]]] = {}

    def lines(self, rel: str) -> list[str]:
        if rel not in self.cache:
            text = (self.root / rel).read_text(encoding="utf-8")
            self.cache[rel] = text.splitlines()
            self.highlights[rel] = build_highlights(text)
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
    return f"{UPSTREAM}/blob/{COMMIT}/{ch['rel']}#L{a}-L{b}"


def spans_for(src: Source, ch: dict) -> list[tuple[int, int, list[dict]]]:
    blocks = ch.get("blocks") or []
    if not blocks:
        return []
    lines = src.lines(ch["rel"])
    if blocks[0].get("full"):
        return [(1, len(lines), blocks[0]["notes"])]
    out = []
    for b in blocks:
        a = Source.find(lines, b["from"])
        z = Source.find(lines, b["to"])
        if a > z:
            raise SystemExit(f"[range] {ch['id']}: from after to")
        out.append((a, z, b["notes"]))
    return out


def annotated(notes: list[dict], lines: list[str], a: int, z: int) -> list[tuple[int, int, str]]:
    items = sorted(((Source.find_in(lines, n["at"], a, z), n["text"]) for n in notes),
                   key=lambda x: x[0])
    rows, prev = [], a
    for pos, text in items:
        start = min(prev, pos)      # 注解顺序错乱时退化为单行，避免 from > to
        rows.append((start, pos, text))
        prev = pos + 1
    return rows


def chapter_stats(src: Source, ch: dict) -> dict:
    total = note_count = covered = 0
    for a, z, notes in spans_for(src, ch):
        total += z - a + 1
        note_count += len(notes)
        covered += sum(z2 - a2 + 1 for a2, z2, _ in annotated(notes, src.lines(ch["rel"]), a, z))
    return {"total": total, "notes": note_count, "covered": covered}


def render_text(line: str, spans: list[tuple[int, int, str]]) -> str:
    if not spans:
        return esc(line)
    out, pos = [], 0
    for s, e, cls in sorted(spans):
        if s < pos:
            continue
        out.append(esc(line[pos:s]))
        out.append(f'<span class="tok {cls}">{esc(line[s:e])}</span>')
        pos = e
    out.append(esc(line[pos:]))
    return "".join(out)


def render_code(src: Source, ch: dict) -> str:
    spans = spans_for(src, ch)
    if not spans:
        return ""
    lines = src.lines(ch["rel"])
    hl = src.highlights.get(ch["rel"], {})
    parts = []
    for idx, (a, z, notes) in enumerate(spans):
        cid = f"{ch['id']}-{idx}"
        groups = annotated(notes, lines, a, z)
        segments = [(s, e, [t]) for s, e, t in groups]
        if groups and groups[-1][1] < z:
            segments.append((groups[-1][1] + 1, z, []))
        if not groups:
            segments = [(a, z, [])]

        seg_html = []
        for si, (s, e, texts) in enumerate(segments):
            sid = f"{cid}-{si}"
            rows = []
            for i in range(s, e + 1):
                text = lines[i - 1]
                body = "&nbsp;" if not text.strip() else render_text(text, hl.get(i, []))
                rows.append(f'<div class="row" data-line="{i}"><span class="ln">{i}</span>'
                            f'<span class="tx">{body}</span></div>')
            ann_html = "".join(
                f'<div class="ann" data-code="{sid}" data-from="{s}" data-to="{e}" '
                f'role="button" tabindex="0" aria-pressed="false" '
                f'aria-label="第 {s} 到 {e} 行，回车固定高亮">'
                f'<span class="lnref">L{s}–{e}</span><p>{t}</p></div>' for t in texts)
            seg_html.append(
                f'<div class="seg"><div class="code-scroll"><div class="code" id="{sid}">'
                f'{"".join(rows)}</div></div><div class="anns">{ann_html}</div></div>')

        parts.append(f"""
<div class="code-wrap" data-cid="{cid}">
  <div class="code-head">
    <span class="dot r"></span><span class="dot y"></span><span class="dot g"></span>
    <span class="file">{esc(ch['rel'])} · L{a}–{z}</span>
    <button class="copy" type="button" data-copy="{cid}">复制</button>
    <a href="{gh_link(ch, a, z)}" target="_blank" rel="noreferrer">GitHub 原文 ↗</a>
  </div>
  {''.join(seg_html)}
</div>""")
    return "\n".join(parts)


def kind_label(ch: dict, stats: dict) -> tuple[str, str]:
    if ch.get("full"):
        kind, cls = "完整源码", "ok"
    elif ch.get("advanced"):
        kind, cls = "关键片段", ""
    else:
        kind, cls = "核心节选", ""
    if stats["notes"] == 0:
        detail = "无注解"
    else:
        detail = f"{stats['notes']} 处注解"
    return f"{kind} · {detail}", cls


def chapter_fragment(src: Source, ch: dict, level: str = "h1") -> str:
    stats = chapter_stats(src, ch)
    label, cls = kind_label(ch, stats)
    idea = "".join(f"<li>{esc(x)}</li>" for x in ch.get("idea", []))
    points = "".join(f'<div class="point"><b>{esc(t)}</b><p>{esc(d)}</p></div>'
                     for t, d in ch.get("points", []))
    pitfalls = "".join(f"<li>{esc(x)}</li>" for x in ch.get("pitfalls", []))
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


# --------------------------------------------------------------------------
# pages
# --------------------------------------------------------------------------

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


def drawer(nav: str) -> str:
    return f"""
<div class="toc-panel" id="tocPanel" hidden>
  <div class="toc-sheet" role="dialog" aria-modal="true" aria-labelledby="tocTitle">
    <button class="close" id="tocClose" type="button" aria-label="关闭目录">×</button>
    <h2 id="tocTitle">目录</h2>
    <nav aria-label="章节目录（移动端）">{nav}</nav>
  </div>
</div>"""


FOOTER = (
    f'<footer>本教程基于 <a href="{UPSTREAM}/tree/{COMMIT}" target="_blank" rel="noreferrer">'
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
<link rel="icon" href="./assets/favicon.ico" sizes="any">
<link rel="icon" href="./assets/favicon.svg" type="image/svg+xml">
<link rel="apple-touch-icon" href="./assets/apple-touch-icon.png">
<script>try{{var t=localStorage.getItem('lcc-theme');if(t==='light'||t==='dark')document.documentElement.dataset.theme=t;}}catch(e){{}}</script>
<link rel="stylesheet" href="./assets/style.css">
</head>
<body class="{body_class}">
<a id="top"></a>
<header class="topbar">
  <div class="topbar-inner">
    <a class="brand" href="./index.html"><span class="b1">Learn Claude Code</span><span class="b2"> · 大白话教程</span></a>
    <button class="toc-btn" id="tocBtn" type="button" aria-expanded="false" aria-controls="tocPanel">目录</button>
    <div class="actions">
      <a class="plain" href="{TUTORIAL_REPO}" target="_blank" rel="noreferrer">本站源码</a>
      <a class="plain" href="{UPSTREAM}" target="_blank" rel="noreferrer">原仓库</a>
      <button class="theme-btn" id="themeBtn" type="button" aria-label="切换主题">◐</button>
    </div>
  </div>
</header>
<div class="{cls}">
{sidebar}
<main>
{body}
</main>
</div>
{drawer(nav or nav_anchors())}
<script src="./assets/app.js" defer></script>
</body>
</html>
"""


def build_index(src: Source) -> str:
    cards = []
    for ch in CHAPTERS:
        label, cls = kind_label(ch, chapter_stats(src, ch))
        cards.append(
            f'<a class="card" href="#{ch["id"]}"><span class="no">CH {ch["no"]}</span>'
            f'<h3>{esc(ch["title"])}</h3><p>{esc(ch["quote"])}</p>'
            f'<div class="kind {cls}">{esc(label)}</div></a>')
    chapters = "\n".join(chapter_fragment(src, ch, level="h2") for ch in CHAPTERS)
    body = f"""
<header class="hero">
  <div class="kicker">Learn Claude Code · 大白话教程</div>
  <h1>看懂一个 AI 编程 Agent<br>是怎么造出来的</h1>
  <p class="lead">{esc(INTRO['lead'])}</p>
  <div class="cta">
    <a class="btn primary" href="#s01">开始第 1 章</a>
    <a class="btn" href="#toc">查看目录</a>
  </div>
  <div class="meta"><span>17 章</span><span>Python</span>
    <span>固定版本 {COMMIT_SHORT}</span><span>关键行注解</span></div>
</header>
{INTRO['html']}
<section class="toc-block" id="toc">
  <h2 class="sec-title">目录</h2>
  <div class="cards">{''.join(cards)}</div>
</section>
{chapters}
<section class="outro" id="outro">{OUTRO}</section>
{FOOTER}"""
    return page("Learn Claude Code · 大白话教程",
                f"基于 learn-claude-code 的非官方中文教程：用大白话讲解关键源码、运行机制与动手练习。代码固定于 commit {COMMIT_SHORT}。",
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
  <p class="problem">本站在 <a href="{UPSTREAM}" target="_blank" rel="noreferrer">shareAI-lab/learn-claude-code</a>
  的基础上做中文讲解。代码片段逐字取自上游 commit <code>{COMMIT_SHORT}</code>（{COMMIT_DATE}），
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


# --------------------------------------------------------------------------
# build
# --------------------------------------------------------------------------

def write_site(out: Path, src_root: Path) -> None:
    src = Source(src_root)
    (out / "assets").mkdir(parents=True)
    for f in ("style.css", "app.js", "favicon.ico", "favicon.svg", "apple-touch-icon.png"):
        shutil.copy2(HERE / "assets" / f, out / "assets" / f)

    pages = {"index.html": build_index(src)}
    for i, ch in enumerate(CHAPTERS):
        pages[f"{ch['id']}.html"] = build_chapter(src, i, ch)
    pages["LICENSE.html"] = build_license()
    pages["404.html"] = pages["index.html"]

    for name, doc in pages.items():
        (out / name).write_text(doc, encoding="utf-8")
    (out / ".nojekyll").write_text("", encoding="utf-8")
    (out / "robots.txt").write_text("User-agent: *\nAllow: /\n", encoding="utf-8")
    (out / MARKER).write_text(f"{COMMIT}\n", encoding="utf-8")


def validate_site(out: Path) -> None:
    required = ["index.html", "LICENSE.html", "404.html",
                "assets/style.css", "assets/app.js", MARKER]
    required += [f"{ch['id']}.html" for ch in CHAPTERS]
    missing = [n for n in required if not (out / n).is_file()]
    if missing:
        die(f"生成结果不完整，缺少：{missing}")
    index = (out / "index.html").read_text(encoding="utf-8")
    if index.count('class="ch" id="') != len(CHAPTERS):
        die("index.html 章节数量不符")


def build(out_arg: str, src_arg: str) -> None:
    src_root = Path(src_arg).expanduser()
    if not src_root.is_absolute():
        src_root = (Path.cwd() / src_root)
    src_root = src_root.resolve()
    verify_upstream(src_root)
    out = validate_out(out_arg, src_root)

    tmp = Path(tempfile.mkdtemp(prefix=".lcc-build-", dir=str(out.parent)))
    try:
        write_site(tmp, src_root)
        validate_site(tmp)
        install_output(tmp, out)
    finally:
        if tmp.exists():
            shutil.rmtree(tmp, ignore_errors=True)
    print(f"built {len(CHAPTERS) + 3} pages into {out}")
    print(f"pinned {COMMIT}")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--src", default="../learn-claude-code", help="upstream checkout")
    ap.add_argument("--out", default="site")
    args = ap.parse_args()
    build(args.out, args.src)


if __name__ == "__main__":
    main()
