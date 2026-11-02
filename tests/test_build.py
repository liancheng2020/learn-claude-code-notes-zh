"""构建脚本的安全边界测试（不触碰真实站点）。"""
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import build  # noqa: E402


class OutPathTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.src = Path(self.tmp.name) / "upstream"
        (self.src / "s01_agent_loop").mkdir(parents=True)
        (self.src / "s01_agent_loop" / "code.py").write_text("print(1)\n", encoding="utf-8")

    def tearDown(self):
        self.tmp.cleanup()

    def test_rejects_project_root(self):
        with self.assertRaises(SystemExit):
            build.validate_out(str(ROOT), self.src)

    def test_rejects_project_ancestor(self):
        with self.assertRaises(SystemExit):
            build.validate_out(str(ROOT.parent), self.src)

    def test_rejects_upstream_and_inside(self):
        for p in (self.src, self.src / "site"):
            with self.assertRaises(SystemExit):
                build.validate_out(str(p), self.src)

    def test_rejects_home_and_root(self):
        for p in (Path.home(), Path("/")):
            with self.assertRaises(SystemExit):
                build.validate_out(str(p), self.src)

    def test_rejects_non_build_directory(self):
        d = Path(self.tmp.name) / "random"
        d.mkdir()
        (d / "keep.txt").write_text("x", encoding="utf-8")
        with self.assertRaises(SystemExit):
            build.validate_out(str(d), self.src)

    def test_accepts_empty_and_marked(self):
        empty = Path(self.tmp.name) / "empty"
        empty.mkdir()
        self.assertEqual(build.validate_out(str(empty), self.src), empty.resolve())
        marked = Path(self.tmp.name) / "marked"
        marked.mkdir()
        (marked / build.MARKER).write_text("x", encoding="utf-8")
        self.assertEqual(build.validate_out(str(marked), self.src), marked.resolve())


class UpstreamTests(unittest.TestCase):
    def _repo(self, commit=True, dirty=False):
        d = tempfile.TemporaryDirectory()
        root = Path(d.name)
        (root / "s01_agent_loop").mkdir()
        (root / "s01_agent_loop" / "code.py").write_text("print(1)\n", encoding="utf-8")
        run = lambda *a: subprocess.run(["git", "-C", str(root), *a], check=True,
                                        capture_output=True, text=True)
        if commit:
            run("init", "-q")
            run("add", ".")
            run("-c", "user.name=t", "-c", "user.email=t@example.com",
                "commit", "-qm", "init")
        if dirty:
            (root / "s01_agent_loop" / "code.py").write_text("print(2)\n", encoding="utf-8")
        return d, root

    def test_wrong_commit_rejected(self):
        d, root = self._repo()
        try:
            with self.assertRaises(SystemExit):
                build.verify_upstream(root)
        finally:
            d.cleanup()

    def test_missing_source_rejected(self):
        with self.assertRaises(SystemExit):
            build.verify_upstream(Path(tempfile.gettempdir()) / "does-not-exist-lcc")

    def test_dirty_worktree_rejected(self):
        d, root = self._repo(dirty=True)
        try:
            # 先伪造 HEAD 与固定版本相同，确保失败原因是 dirty
            old = build.COMMIT
            build.COMMIT = subprocess.run(
                ["git", "-C", str(root), "rev-parse", "HEAD"],
                capture_output=True, text=True, check=True).stdout.strip()
            self.addCleanup(setattr, build, "COMMIT", old)
            with self.assertRaises(SystemExit):
                build.verify_upstream(root)
        finally:
            d.cleanup()


class ReplaceTests(unittest.TestCase):
    def test_failed_swap_keeps_old_site(self):
        with tempfile.TemporaryDirectory() as td:
            out = Path(td) / "site"
            out.mkdir()
            (out / build.MARKER).write_text("old", encoding="utf-8")
            (out / "index.html").write_text("old", encoding="utf-8")
            missing_tmp = Path(td) / "missing"
            with self.assertRaises(OSError):
                build.install_output(missing_tmp, out)
            self.assertEqual((out / "index.html").read_text(encoding="utf-8"), "old")


if __name__ == "__main__":
    unittest.main()
