"""内容一致性回归：覆盖范围声明、关键练习、章节标签。"""
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import build  # noqa: E402


class ContentTests(unittest.TestCase):
    def test_s02_is_full_source(self):
        ch = next(c for c in build.CHAPTERS if c["id"] == "s02")
        self.assertTrue(ch.get("full"))
        label, _ = build.kind_label(ch, {"notes": 17, "covered": 100, "total": 208})
        self.assertIn("完整源码", label)

    def test_no_line_by_line_claim(self):
        for ch in build.CHAPTERS:
            stats = {"notes": 5, "covered": 40, "total": 100}
            label, _ = build.kind_label(ch, stats)
            self.assertNotIn("逐行", label)
            self.assertIn("处注解", label)

    def test_s16_modes_documented(self):
        ch = next(c for c in build.CHAPTERS if c["id"] == "s16")
        text = " ".join([ch["problem"], ch["try"]] + [a + " " + b for a, b in ch["points"]])
        for word in ("MockAgentRunner", "demo", "resume", "install_workflow_tool", "AnthropicAgentRunner"):
            self.assertIn(word, text)
        self.assertNotIn("把 RUNNER_FACTORY 换成 AnthropicAgentRunner", ch["try"])

    def test_s10_exercise_claims_before_complete(self):
        ch = next(c for c in build.CHAPTERS if c["id"] == "s10")
        try_text = ch["try"]
        self.assertLess(try_text.index("claim_task(A)"), try_text.index("complete_task(A)"))
        self.assertIn("claim_task(D)", try_text)
        self.assertIn(".tasks/", try_text)

    def test_reading_scope_wording(self):
        intro = build.INTRO["html"]
        self.assertIn("不是每章都", intro)
        self.assertNotIn("每一行都有注解", intro)


if __name__ == "__main__":
    unittest.main()
