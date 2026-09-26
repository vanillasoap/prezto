import json
import shlex
import sys

from support import ShellTestCase


class TrashTests(ShellTestCase):
    load = '''
fpath=("$PREZTO_TEST_REPO/modules/osx/functions" $fpath)
autoload -Uz trash
'''

    def setUp(self):
        super().setUp()
        capture = self.root / "capture.py"
        capture.write_text(
            "import json,sys\n"
            "from pathlib import Path\n"
            "Path('finder-call.json').write_text(json.dumps({"
            "'arguments': sys.argv[1:], 'script': sys.stdin.read()}))\n"
        )
        self.stub("osascript", f"exec {shlex.quote(sys.executable)} {shlex.quote(str(capture))} \"$@\"")

    def test_paths_are_data_and_symlinks_are_not_followed(self):
        names = ['a"b', "back\\slash", "line\nbreak", "unicode-ø", "--dash", "a directory"]
        for name in names[:-1]:
            (self.root / name).touch()
        (self.root / names[-1]).mkdir()
        (self.root / "link").symlink_to(names[0])
        names += ["link"]
        self.success(self.zsh(self.load + "trash " + shlex.join(names)))
        call = json.loads((self.root / "finder-call.json").read_text())
        self.assertEqual(call["arguments"], ["-", *[str(self.root / name) for name in names]])
        self.assertNotIn(str(self.root), call["script"], "paths were interpolated into AppleScript")
        self.assertTrue((self.root / "link").is_symlink())

    def test_dangling_symlink_is_an_existing_operand(self):
        (self.root / "broken link").symlink_to("missing target")
        self.success(self.zsh(self.load + "trash 'broken link'"))
        call = json.loads((self.root / "finder-call.json").read_text())
        self.assertEqual(call["arguments"], ["-", str(self.root / "broken link")])

    def test_missing_operand_prevents_partial_trashing(self):
        (self.root / "exists").touch()
        result = self.zsh(self.load + "trash exists missing")
        self.assertNotEqual(result.returncode, 0)
        self.assertFalse((self.root / "finder-call.json").exists())

    def test_finder_failure_is_returned(self):
        (self.root / "exists").touch()
        self.stub("osascript", "exit 7")
        self.assertEqual(self.zsh(self.load + "trash exists").returncode, 7)


class SubstitutionTests(ShellTestCase):
    def test_combined_flags_are_independent_of_order(self):
        for flags in ("gis", "sgi", "isg"):
            with self.subTest(flags=flags):
                source = self.root / "sample.txt"
                source.write_text("Aa aA\n")
                self.success(self.zsh('''
fpath=("$PREZTO_TEST_REPO/modules/utility/functions" $fpath)
autoload -Uz psub
''' + f"psub -{flags} a X sample.txt"))
                self.assertEqual(source.read_text(), "XX XX\n")
                self.assertEqual((self.root / "sample.txt.orig").read_text(), "Aa aA\n")
