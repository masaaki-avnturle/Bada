import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from editor import BadaVim, INSERT, NORMAL
from app import SilentVimSession


class TestEditorCore(unittest.TestCase):
    def test_insert_escape_and_type(self):
        ed = BadaVim()
        ed.apply_command("INSERT")
        self.assertEqual(ed.mode, INSERT)
        ed.type_text("say 1")
        ed.apply_command("ESCAPE")
        self.assertEqual(ed.mode, NORMAL)
        self.assertEqual(ed.text(), "say 1")

    def test_newline_and_delete(self):
        ed = BadaVim()
        ed.type_text("abc")          # auto-enters insert
        ed.apply_command("ESCAPE")
        ed.cx = 0
        ed.apply_command("DELETE")   # removes 'a'
        self.assertEqual(ed.text(), "bc")

    def test_movement_clamps(self):
        ed = BadaVim(lines=["hello"])
        ed.apply_command("RIGHT")
        ed.apply_command("RIGHT")
        self.assertEqual(ed.cx, 2)
        for _ in range(10):
            ed.apply_command("LEFT")
        self.assertEqual(ed.cx, 0)

    def test_save_and_open(self):
        with tempfile.TemporaryDirectory() as d:
            p = os.path.join(d, "x.bada")
            ed = BadaVim(filename=p)
            ed.type_text("print 21 * 2")
            ed.apply_command("SAVE")
            ed2 = BadaVim.open(p)
        self.assertEqual(ed2.text(), "print 21 * 2")

    def test_run_buffer_captures_output(self):
        ed = BadaVim()
        ed.type_text("print 21 * 2")
        ed.apply_command("RUN")
        self.assertEqual(ed.output, ["42"])

    def test_run_reports_errors(self):
        ed = BadaVim()
        ed.type_text("print 1 / 0")
        ed.apply_command("RUN")
        self.assertTrue(any("zero" in line for line in ed.output))


class TestSilentVimSession(unittest.TestCase):
    def test_dictate_and_run_program(self):
        sess = SilentVimSession()
        sess.feed_words([
            "AI",                # INSERT
            "EI", "IA", "OU", "IE",   # print [ 42 ]
            "AO",                # newline
            "EA", "UE", "OE", "UE",   # say " hello "
            "UO",                # ESCAPE
            "OA",                # RUN
        ])
        self.assertEqual(sess.buffer_text(), 'print [42]\nsay "hello"')
        self.assertEqual(sess.ed.output, ["[42]", "hello"])

    def test_escape_works_from_insert(self):
        sess = SilentVimSession()
        sess.feed_words(["AI", "UO"])    # INSERT then ESCAPE
        self.assertEqual(sess.ed.mode, NORMAL)


if __name__ == "__main__":
    unittest.main()
