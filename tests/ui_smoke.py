#!/usr/bin/env python3
"""浏览器回归：复制失败/成功、目录焦点隔离、320px 许可页。

没有可用 Chrome 时打印 SKIP 并以 0 退出（CI 可安全调用）。
"""
import argparse
import json
import re
import shutil
import subprocess
import sys
import tempfile
import urllib.parse
from pathlib import Path

CHROME_CANDIDATES = [
    "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
    "google-chrome", "google-chrome-stable", "chromium", "chromium-browser",
]


def find_chrome():
    for c in CHROME_CANDIDATES:
        path = shutil.which(c) if "/" not in c else (c if Path(c).exists() else None)
        if path:
            return path
    return None


def dump(chrome, page: Path, js: str, budget=5000):
    src = page.read_text(encoding="utf-8")
    test = page.with_name("_ui_" + page.name)
    test.write_text(src.replace("</body>", f"<script>{js}</script></body>"), encoding="utf-8")
    try:
        out = subprocess.run(
            [chrome, "--headless=new", "--disable-gpu", "--no-sandbox",
             f"--user-data-dir={tempfile.mkdtemp(prefix='lcc-ui-')}",
             f"--virtual-time-budget={budget}", "--dump-dom", test.as_uri()],
            capture_output=True, text=True, timeout=60,
        ).stdout
    finally:
        test.unlink(missing_ok=True)
    m = re.search(r"<title>UI (.*?)</title>", out, re.S)
    if not m:
        raise AssertionError(f"未拿到结果：{out[:300]}")
    return json.loads(m.group(1))


COPY_JS = r"""
window.addEventListener('load',function(){setTimeout(function(){
 var o={}, btn=document.querySelector('.copy'), ok=false;
 document.execCommand=function(){return ok};
 try{Object.defineProperty(navigator,'clipboard',{configurable:true,
   value:{writeText:function(t){window.__c=t;return Promise.reject(new Error('denied'));}}});}catch(e){}
 btn.click();
 setTimeout(function(){
  o.fail=btn.textContent; o.failState=btn.dataset.state;
  ok=true; btn.click();
  setTimeout(function(){
   o.ok=btn.textContent; o.okState=btn.dataset.state;
   o.first=(window.__c||'').split('\n')[0];
   o.hasAnn=(window.__c||'').indexOf('建任务')>=0;
   o.hasLine=/^\s*\d+\b/.test(window.__c||'');
   document.title='UI '+JSON.stringify(o);
  },300);
 },300);
},300)});
"""

TOC_JS = r"""
window.addEventListener('load',function(){setTimeout(function(){
 var o={}, btn=document.getElementById('tocBtn'), p=document.getElementById('tocPanel');
 btn.click();
 o.inertTop=document.querySelector('.topbar').inert;
 o.inertLayout=document.querySelector('.layout').inert;
 o.focusIn=p.contains(document.activeElement);
 o.lock=document.body.classList.contains('toc-open');
 p.dispatchEvent(new KeyboardEvent('keydown',{key:'Escape',bubbles:true}));
 o.closed=p.hidden; o.inertAfter=document.querySelector('.layout').inert;
 o.back=document.activeElement===btn; o.overflow=getComputedStyle(document.body).overflow;
 document.title='UI '+JSON.stringify(o);
},300)});
"""

THEME_JS = r"""
window.addEventListener('load',function(){setTimeout(function(){
 var th=document.getElementById('themeBtn');
 var sysDark=window.matchMedia&&window.matchMedia('(prefers-color-scheme: dark)').matches;
 var o={sys:sysDark?'dark':'light'};
 th.click(); o.t1=document.documentElement.dataset.theme; o.i1=th.textContent;
 th.click(); o.t2=document.documentElement.dataset.theme; o.i2=th.textContent;
 document.title='UI '+JSON.stringify(o);
},300)});
"""

W320_JS = r"""
window.addEventListener('load',function(){setTimeout(function(){
 parent.postMessage({w:document.documentElement.clientWidth,
                     docW:document.documentElement.scrollWidth},'*');
},300)});
"""


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--site", default="site")
    args = ap.parse_args()
    chrome = find_chrome()
    if not chrome:
        print("SKIP: 未找到 Chrome/Chromium")
        return 0

    site = Path(args.site).resolve()
    tmp = Path(tempfile.mkdtemp(prefix="lcc-ui-site-"))
    try:
        work = tmp / "site"
        shutil.copytree(site, work)
        errors = []

        r = dump(chrome, work / "s05.html", COPY_JS)
        if r["fail"] != "复制失败" or r["failState"] != "err":
            errors.append(f"复制失败路径异常：{r}")
        if r["ok"] != "已复制" or r["okState"] != "ok":
            errors.append(f"复制成功路径异常：{r}")
        if r["hasLine"] or r["hasAnn"] or not r["first"].startswith("class TodoManager:"):
            errors.append(f"复制内容不纯：{r}")

        r = dump(chrome, work / "s05.html", THEME_JS)
        want = "light" if r["sys"] == "dark" else "dark"
        if r.get("t1") != want or r.get("t2") != r["sys"]:
            errors.append(f"主题切换不是一次生效：{r}")

        r = dump(chrome, work / "index.html", TOC_JS)
        for key in ("inertTop", "inertLayout", "focusIn", "lock", "closed", "back"):
            if not r.get(key):
                errors.append(f"目录交互失败 {key}：{r}")
        if r.get("inertAfter") or r.get("overflow") != "visible":
            errors.append(f"目录关闭未恢复：{r}")

        probe = work / "_license_probe.html"
        probe.write_text(
            (work / "LICENSE.html").read_text(encoding="utf-8")
            .replace("</body>", f"<script>{W320_JS}</script></body>"),
            encoding="utf-8")
        inner = urllib.parse.quote(str(probe))
        wrapper = work / "_w320.html"
        wrapper.write_text(
            '<!doctype html><style>body{margin:0}iframe{border:0;width:320px;height:900px}</style>'
            f'<iframe src="file://{inner}"></iframe>'
            '<script>addEventListener("message",function(e){document.title="UI "+JSON.stringify(e.data)});</script>',
            encoding="utf-8")
        out = subprocess.run(
            [chrome, "--headless=new", "--disable-gpu", "--no-sandbox",
             f"--user-data-dir={tempfile.mkdtemp(prefix='lcc-ui-')}",
             "--virtual-time-budget=4000", "--dump-dom", wrapper.as_uri()],
            capture_output=True, text=True, timeout=60).stdout
        m = re.search(r"<title>UI (.*?)</title>", out, re.S)
        r = json.loads(m.group(1)) if m else {}
        if not r.get("w") or r.get("docW", 9999) > r["w"]:
            errors.append(f"320px 许可页溢出：{r}")

        if errors:
            print("FAIL")
            for e in errors:
                print(" -", e)
            return 1
        print("OK：复制失败/成功、目录焦点隔离、主题一次切换、320px 许可页")
        return 0
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


if __name__ == "__main__":
    sys.exit(main())
