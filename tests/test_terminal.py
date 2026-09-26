from urllib.parse import quote

from support import ShellTestCase


class TerminalTests(ShellTestCase):
    def test_resumed_job_title_contains_its_command(self):
        result = self.zsh('''
unsetopt BG_NICE
source "$PREZTO_TEST_REPO/modules/terminal/init.zsh"
set-tab-title() { print -r -- "tab=$*"; }
set-window-title() { print -r -- "window=$*"; }
sleep 1 &
_terminal-set-titles-with-command fg fg
wait
''')
        output = self.success(result)
        self.assertIn("tab=sleep\n", output)
        self.assertIn("window=sleep\n", output)

    def test_terminal_directory_uri_encodes_reserved_and_utf8_bytes(self):
        directory = self.root / "folder #fragment%20?query-ø"
        directory.mkdir()
        self.env.update(TERM_PROGRAM="Apple_Terminal", PREZTO_DIRECTORY=str(directory))
        result = self.zsh('''
HOST=testhost
unset STY TMUX DVTM
source "$PREZTO_TEST_REPO/modules/terminal/init.zsh"
cd "$PREZTO_DIRECTORY"
_terminal-set-terminal-app-proxy-icon
''')
        self.assertEqual(self.success(result), "\x1b]7;file://testhost" + quote(str(directory)) + "\x07")
