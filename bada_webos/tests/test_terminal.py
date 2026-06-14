import os
import sys
import unittest

_HERE = os.path.dirname(os.path.abspath(__file__))
_PKG = os.path.dirname(_HERE)
_ROOT = os.path.dirname(_PKG)
for p in (_PKG, _ROOT, os.path.join(_ROOT, "bada_silent_vim")):
    if p not in sys.path:
        sys.path.insert(0, p)

from terminal import Terminal, VFS, VFSError
from terminal.shell import Shell


class TestVFS(unittest.TestCase):
    def test_write_read_ls_cd(self):
        v = VFS()
        v.write("a.txt", "hi")
        self.assertEqual(v.read("a.txt"), "hi")
        self.assertIn("a.txt", v.listdir())
        v.mkdir("sub")
        v.chdir("sub")
        self.assertTrue(v.cwd.endswith("/sub"))

    def test_missing_file_raises(self):
        with self.assertRaises(VFSError):
            VFS().read("nope.txt")


class TestBash(unittest.TestCase):
    def setUp(self):
        self.t = Terminal()

    def test_echo_redirect_and_cat(self):
        self.t.bash("echo hello world > f.txt")
        self.assertEqual(self.t.bash("cat f.txt"), "hello world\n")

    def test_append_redirect(self):
        self.t.bash("echo one > f.txt")
        self.t.bash("echo two >> f.txt")
        self.assertEqual(self.t.bash("cat f.txt"), "one\ntwo\n")

    def test_pipe_grep_wc(self):
        self.t.bash("echo alpha > f.txt")
        self.t.bash("echo beta >> f.txt")
        self.assertEqual(self.t.bash("cat f.txt | grep beta"), "beta\n")
        self.assertEqual(self.t.bash("cat f.txt | wc").strip(), "2 2 11")

    def test_mkdir_cd_pwd(self):
        self.t.bash("mkdir proj")
        self.t.bash("cd proj")
        self.assertEqual(self.t.bash("pwd").strip(), "/home/bada/proj")

    def test_unknown_command(self):
        self.assertIn("command not found", self.t.bash("frobnicate"))

    def test_run_bada_program(self):
        self.t.bash('echo print 21 * 2 > p.bada')
        self.assertEqual(self.t.bash("bada p.bada"), "42\n")

    def test_help_lists_editors(self):
        out = self.t.bash("help")
        self.assertIn("vim", out)
        self.assertIn("emacs", out)


class TestEditors(unittest.TestCase):
    def setUp(self):
        self.t = Terminal()

    def test_vim_creates_and_saves_to_vfs(self):
        v = self.t.open_vim("poem.txt",
                            ["i", "line one", "ESC", "o", "line two",
                             "ESC", ":wq"])
        self.assertEqual(v.text(), "line one\nline two")
        self.assertEqual(self.t.vfs.read("poem.txt"), "line one\nline two")

    def test_emacs_edits_existing_vfs_file(self):
        self.t.bash("echo hello > note.txt")     # -> "hello\n"
        e = self.t.open_emacs("note.txt",
                              ["C-e", " world", "C-x C-s", "C-x C-c"])
        self.assertFalse(e.alive)
        self.assertEqual(self.t.vfs.read("note.txt"), "hello world\n")

    def test_emacs_kill_and_yank(self):
        self.t.bash("echo abcdef > k.txt")
        e = self.t.open_emacs("k.txt", ["C-a", "C-f", "C-f", "C-k"])
        self.assertEqual(e.text().splitlines()[0], "ab")
        self.assertEqual(e.killring, "cdef")

    def test_vim_then_emacs_same_file(self):
        self.t.open_vim("shared.txt", ["i", "from vim", "ESC", ":wq"])
        self.t.open_emacs("shared.txt",
                          ["C-e", " + emacs", "C-x C-s", "C-x C-c"])
        self.assertEqual(self.t.vfs.read("shared.txt"), "from vim + emacs")


class TestRender(unittest.TestCase):
    def test_html_render_has_prompt_and_output(self):
        t = Terminal()
        t.bash("echo hi > x.txt")
        t.bash("cat x.txt")
        html = t.render_html()
        self.assertIn("webos:", html)
        self.assertIn("hi", html)


if __name__ == "__main__":
    unittest.main()
