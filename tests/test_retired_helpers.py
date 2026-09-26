from support import ShellTestCase


class RetiredHelperTests(ShellTestCase):
    def test_git_io_reports_retirement_without_making_a_request(self):
        self.stub("curl", 'touch "$TMPDIR/network-request"')
        result = self.zsh('''
fpath=("$PREZTO_TEST_REPO/modules/git/functions" $fpath)
autoload -Uz git-hub-shorten-url
git-hub-shorten-url https://github.com/vanillasoap/prezto
''')
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("retired", result.stderr)
        self.assertFalse((self.root / "network-request").exists())
