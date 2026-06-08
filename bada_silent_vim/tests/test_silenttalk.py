import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from silenttalk import (SilentTalkDecoder, classify_viseme, draw_viseme,
                        lip_features, load_lexicon, read_pgm, synth_stream,
                        write_frames, write_pgm)
from silenttalk.lipfeatures import parse_pgm


class TestLipFeatures(unittest.TestCase):
    def test_each_viseme_classifies_to_itself(self):
        for v in ("C", "A", "I", "U", "O", "E"):
            feat = lip_features(draw_viseme(v))
            self.assertEqual(classify_viseme(feat), v,
                             f"viseme {v} misclassified as "
                             f"{classify_viseme(feat)} ({feat})")

    def test_pgm_round_trip_ascii(self):
        pix = draw_viseme("A")
        with tempfile.TemporaryDirectory() as d:
            p = os.path.join(d, "a.pgm")
            write_pgm(p, pix)
            back = read_pgm(p)
        self.assertEqual(pix, back)

    def test_parse_p5_binary(self):
        data = b"P5\n2 2\n255\n" + bytes([0, 255, 255, 0])
        self.assertEqual(parse_pgm(data), [[0, 255], [255, 0]])


class TestDecoder(unittest.TestCase):
    def setUp(self):
        self.dec = SilentTalkDecoder()

    def test_full_lexicon_round_trip(self):
        lex = load_lexicon()
        words = list(lex["commands"]) + list(lex["text"])
        frames = synth_stream(words, hold=3)
        toks = self.dec.decode_frames(frames)
        self.assertEqual([t.visemes for t in toks], words)

    def test_command_and_text_resolution(self):
        toks = self.dec.decode_frames(synth_stream(["AI", "EA"], hold=3))
        self.assertEqual(toks[0].command, "INSERT")
        self.assertEqual(toks[1].text, "say ")

    def test_band_in_range(self):
        toks = self.dec.decode_frames(synth_stream(["A"], hold=3))
        self.assertTrue(0 <= toks[0].band <= 6)

    def test_decode_from_disk(self):
        with tempfile.TemporaryDirectory() as d:
            write_frames(synth_stream(["AI", "UO"], hold=2), d)
            toks = self.dec.decode_dir(d)
        self.assertEqual([t.command for t in toks], ["INSERT", "ESCAPE"])


if __name__ == "__main__":
    unittest.main()
