import pathlib
import re
import unittest

from html_diff import __version__
from html_diff import diff
from html_diff.legacy import diff as ldiff
from html_diff.check import old_from_diff
from html_diff.check import new_from_diff
from html_diff.config import Config
from html_diff.config import config



test_diffs_legacy = (
    (
        "<ul><li>ax</li><li>b</li><li>c</li></ul>",
        "<ul><li>a</li><li>by</li><li>c</li></ul>",
        (
            "<ul><li>a<del>x</del></li><li>b<ins>y</ins></li><li>c</li></ul>",
            "<ul><li><del>ax</del><ins>a</ins></li><li><del>b</del><ins>by</ins></li><li>c</li></ul>",
            "<ul><li><del>ax</del><ins>a</ins></li><li><del>b</del><ins>by</ins></li><li>c</li></ul>",
        ),
    ),
    (
        "<em>a</em><em>bb</em>",
        "<em>bb</em><em>a</em>",
        (
            "<del><em>a</em></del><em>bb</em><ins><em>a</em></ins>",
            "<del><em>a</em></del><em>bb</em><ins><em>a</em></ins>",
            "<del><em>a</em></del><em>bb</em><ins><em>a</em></ins>",
        ),
    ),
    (
        "OlyExams",
        "ExamTools",
        (
            "<del>Oly</del>Exam<ins>Tool</ins>s",
            "<del>OlyExams</del><ins>ExamTools</ins>",
            "<del>OlyExams</del><ins>ExamTools</ins>",
        ),
    ),
    (
        "abcdef<br/>ghifjk",
        "abcdef ghifjk",
        (
            "abcdef<ins> ghifjk</ins><del><br/>ghifjk</del>",
            "abcdef<ins> ghifjk</ins><del><br/>ghifjk</del>",
            "abcdef<del><br/></del><ins> </ins>ghifjk",
        ),
    ),
)


test_diffs = (
    (
        "<ul><li>ax</li><li>b</li><li>c</li></ul>",
        "<ul><li>a</li><li>by</li><li>c</li></ul>",
        "<ul><li><del>ax</del><ins>a</ins></li><li><del>b</del><ins>by</ins></li><li>c</li></ul>",
    ),
    (
        "<em>a</em><em>bb</em>",
        "<em>bb</em><em>a</em>",
        "<em><del>a</del><ins>bb</ins></em><em><del>bb</del><ins>a</ins></em>",
    ),
    (
        "OlyExams",
        "ExamTools",
        "<del>OlyExams</del><ins>ExamTools</ins>",
    ),
    (
        "abcdef<br/>ghifjk",
        "abcdef ghifjk",
        "abcdef<del><br/></del><ins> </ins>ghifjk",
    ),
)


class TestHTMLDiff(unittest.TestCase):
    def test_version(self):
        with open(pathlib.Path(__file__).parent.parent / "pyproject.toml") as fi:
            version_match = re.search(r'version\s*=\s*"(.+?)"', fi.read())
        self.assertNotEqual(version_match, None)
        self.assertEqual(version_match.group(1), __version__)
    def test_legacy_diff(self):
        for old, new, diffs in test_diffs_legacy:
            for df, cuttable_mode in zip(diffs, Config.CuttableWordsMode):
                config.cuttable_words_mode = cuttable_mode
                d = ldiff(old, new)
                self.assertEqual(d, df)
                self.assertEqual(old, old_from_diff(d))
                self.assertEqual(new, new_from_diff(d))
    def test_diff(self):
        for old, new, di in test_diffs:
            d = diff(old, new)
            self.assertEqual(d, di)
            self.assertEqual(old, old_from_diff(d))
            self.assertEqual(new, new_from_diff(d))


if __name__ == "__main__":
    unittest.main()

