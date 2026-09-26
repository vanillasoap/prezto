import json
import shlex
import sys

from support import ShellTestCase, ZSH


class OSXTests(ShellTestCase):
    load = '''
fpath=("$PREZTO_TEST_REPO/modules/osx/functions" $fpath)
autoload -Uz ofd tab split_tab vsplit_tab
'''

    def setUp(self):
        super().setUp()
        capture = self.root / "capture.py"
        capture.write_text(
            "import json,sys\nfrom pathlib import Path\n"
            "Path('call.json').write_text(json.dumps({'arguments':sys.argv[1:], 'script':sys.stdin.read()}))\n"
        )
        self.stub("osascript", f"exec {shlex.quote(sys.executable)} {shlex.quote(str(capture))} \"$@\"")
        self.stub("open", f"exec {shlex.quote(sys.executable)} {shlex.quote(str(capture))} \"$@\" </dev/null")

    def test_finder_preserves_paths_and_defaults_to_current_directory(self):
        self.success(self.zsh(self.load + "ofd"))
        self.assertEqual(json.loads((self.root / "call.json").read_text())["arguments"], ["-a", "Finder", str(self.root)])
        names = ['quotes " and spaces', "--dash", "line\nbreak"]
        for name in names:
            (self.root / name).mkdir()
        self.success(self.zsh(self.load + "ofd " + shlex.join(names)))
        self.assertEqual(json.loads((self.root / "call.json").read_text())["arguments"], ["-a", "Finder", *[str(self.root / name) for name in names]])

    def test_finder_invalid_operand_prevents_partial_open(self):
        self.assertNotEqual(self.zsh(self.load + "ofd . missing").returncode, 0)
        self.assertFalse((self.root / "call.json").exists())

    def test_terminal_arguments_round_trip_without_shell_expansion(self):
        directory = self.root / 'dir "quote\' $()\nø'
        directory.mkdir()
        self.env["PREZTO_DIRECTORY"] = str(directory)
        args = ['space argument', '"quote\'', '$(touch injected)', 'line\nbreak', '']
        for terminal in ("ghostty", "iTerm.app", "Apple_Terminal"):
            for entry in ("tab", "split_tab", "vsplit_tab"):
                if terminal == "Apple_Terminal" and entry != "tab":
                    continue
                with self.subTest(terminal=terminal, entry=entry):
                    self.env["TERM_PROGRAM"] = terminal
                    self.success(self.zsh(self.load + 'cd "$PREZTO_DIRECTORY"\n' + entry + " print -rl -- " + shlex.join(args)))
                    call = json.loads((directory / "call.json").read_text())
                    self.assertEqual(call["arguments"][:3], ["-", entry, str(directory)])
                    self.assertNotIn(str(directory), call["script"])
                    result = self.command([ZSH, "-dfc", call["arguments"][3]])
                    self.assertEqual(result.stdout, "\n".join(args) + "\n")
                    self.assertFalse((directory / "injected").exists())

    def test_terminal_rejects_unsupported_splits_and_remote_sessions(self):
        self.env["TERM_PROGRAM"] = "Apple_Terminal"
        self.assertNotEqual(self.zsh(self.load + "split_tab").returncode, 0)
        self.assertFalse((self.root / "call.json").exists())
        self.env.update(TERM_PROGRAM="ghostty", SSH_CONNECTION="test")
        self.assertNotEqual(self.zsh(self.load + "tab").returncode, 0)
        self.assertFalse((self.root / "call.json").exists())

    def test_terminal_failure_is_returned(self):
        self.env["TERM_PROGRAM"] = "ghostty"
        self.stub("osascript", "exit 7")
        self.assertEqual(self.zsh(self.load + "tab").returncode, 7)

    def test_module_registers_all_public_helpers(self):
        result = self.zsh('''
source "$PREZTO_TEST_REPO/init.zsh"
zstyle ':prezto:module:helper' loaded yes
is-darwin() { return 0; }
pmodload osx || exit
for helper in ofd tab split_tab vsplit_tab; do
  (( $+functions[$helper] )) || exit 1
done
(( $+aliases[showfiles] && $+aliases[hidefiles] ))
''')
        self.success(result)

    def test_finder_is_not_restarted_after_preference_write_failure(self):
        self.stub("defaults", "exit 7")
        self.stub("killall", 'touch "$TMPDIR/restarted"')
        result = self.zsh('''
pmodload() { :; }
is-darwin() { return 0; }
source "$PREZTO_TEST_REPO/modules/osx/init.zsh"
eval showfiles
''')
        self.assertEqual(result.returncode, 7)
        self.assertFalse((self.root / "restarted").exists())
