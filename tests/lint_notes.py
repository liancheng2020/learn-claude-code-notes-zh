#!/usr/bin/env python3
"""注解体检：代码段长度、单条字数、绝对化措辞、裸术语。

用法：
    python3 tests/lint_notes.py --src ../learn-claude-code
"""
import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import build

ABSOLUTE = ["一定", "永远", "必然", "绝对不会", "所有情况下"]
TERMS = ["幂等", "闭包", "原子", "状态机", "序列化", "并发"]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--src", default="/tmp/lcc", help="固定版本上游 checkout")
    ap.add_argument("--seg-warn", type=int, default=22)
    ap.add_argument("--seg-error", type=int, default=35)
    ap.add_argument("--note-warn", type=int, default=80)
    ap.add_argument("--note-error", type=int, default=120)
    args = ap.parse_args()

    src = build.Source(Path(args.src))
    errors, warns = [], []
    print(f"{'章节':<5}{'注解':>5}{'最长段':>7}{'>12 段':>7}")
    total_notes = 0
    for ch in build.CHAPTERS:
        segs, notes = [], 0
        for a, z, ns in build.spans_for(src, ch):
            notes += len(ns)
            groups = build.annotated(ns, src.lines(ch["rel"]), a, z)
            for s, e, _ in groups:
                segs.append((s, e, e - s + 1))
            if groups and groups[-1][1] < z:
                segs.append((groups[-1][1] + 1, z, z - groups[-1][1]))
        total_notes += notes
        print(f"{ch['id']:<5}{notes:>5}{max(x[2] for x in segs):>7}{sum(1 for x in segs if x[2] > args.seg_warn):>7}")
        for s, e, length in segs:
            if length > args.seg_error:
                errors.append(f"{ch['id']} L{s}–{e}：连续 {length} 行没有讲解（上限 {args.seg_error}）")
            elif length > args.seg_warn:
                warns.append(f"{ch['id']} L{s}–{e}：连续 {length} 行（建议 ≤{args.seg_warn}）")
        for b in ch.get("blocks") or []:
            for n in b["notes"]:
                t = n["text"]
                if len(t) > args.note_error:
                    errors.append(f"{ch['id']} L{n['at'][:24]}：注解 {len(t)} 字（上限 {args.note_error}）")
                elif len(t) > args.note_warn:
                    warns.append(f"{ch['id']}：注解 {len(t)} 字（建议 ≤{args.note_warn}）：{t[:30]}…")
                for w in ABSOLUTE:
                    if w in t:
                        errors.append(f"{ch['id']}：绝对化措辞「{w}」：{t[:30]}…")
                for term in TERMS:
                    if term in t and "（" not in t:
                        warns.append(f"{ch['id']}：术语「{term}」未就地解释：{t[:30]}…")

    print(f"\n共 {total_notes} 条注解；{len(errors)} 个错误，{len(warns)} 个提醒")
    for w in warns[:30]:
        print("WARN", w)
    if len(warns) > 30:
        print(f"… 另有 {len(warns) - 30} 条提醒")
    for e in errors:
        print("FAIL", e)
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
