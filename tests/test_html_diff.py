import pathlib
import re
import unittest

from html_diff import __version__
from html_diff import diff
from html_diff.check import old_from_diff
from html_diff.check import new_from_diff
from html_diff.config import config



test_diffs = (
    (
        "<ul><li>ax</li><li>b</li><li>c</li></ul>",
        "<ul><li>a</li><li>by</li><li>c</li></ul>",
        "<ul><li>a<del>x</del></li><li>b<ins>y</ins></li><li>c</li></ul>",
        "<ul><li><del>ax</del><ins>a</ins></li><li><del>b</del><ins>by</ins></li><li>c</li></ul>",
    ),
    (
        "<em>a</em><em>bb</em>",
        "<em>bb</em><em>a</em>",
        "<del><em>a</em></del><em>bb</em><ins><em>a</em></ins>",
        "<del><em>a</em></del><em>bb</em><ins><em>a</em></ins>",
    ),
)


class TestHTMLDiff(unittest.TestCase):
    def test_version(self):
        with open(pathlib.Path(__file__).parent.parent / "pyproject.toml") as fi:
            version_match = re.search(r'version\s*=\s*"(.+?)"', fi.read())
        self.assertNotEqual(version_match, None)
        self.assertEqual(version_match.group(1), __version__)
    def test_diff(self):
        for old, new, diff_cuttable, diff_uncuttable in test_diffs:
            for df, cuttable in zip((diff_cuttable, diff_uncuttable), (True, False)):
                config.cuttable_words = cuttable
                d = diff(old, new)
                self.assertEqual(d, df)
                self.assertEqual(old, old_from_diff(d))
                self.assertEqual(new, new_from_diff(d))


if __name__ == "__main__":
    unittest.main()

