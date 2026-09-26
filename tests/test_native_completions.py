from support import ShellTestCase


class NativeCompletionTests(ShellTestCase):
    def setUp(self):
        super().setUp()
        self.data = self.root / "data with spaces"
        self.env["XDG_DATA_HOME"] = str(self.data)
        self.destination = self.data / "prezto/completions"

    def update(self, arguments=""):
        return self.zsh('''
fpath=("$PREZTO_TEST_REPO/modules/completion/functions" $fpath)
autoload -Uz prezto-completions-update
prezto-completions-update ''' + arguments)

    def test_generates_native_scripts_without_evaluating_them(self):
        for program in ("pnpm", "pip"):
            self.stub(program, '''
printf '%s\\n' "$*" > "$TMPDIR/$(basename "$0").arguments"
printf 'touch "$TMPDIR/should-not-execute"\\n'
''')
        self.success(self.update())
        for program in ("pnpm", "pip"):
            expected = "completion --zsh\n" if program == "pip" else "completion zsh\n"
            self.assertEqual((self.root / (program + ".arguments")).read_text(), expected)
            script = self.destination / (program + ".zsh")
            self.assertEqual(script.read_text(), 'touch "$TMPDIR/should-not-execute"\n')
            self.assertEqual(script.stat().st_mode & 0o777, 0o600)
        self.assertFalse((self.root / "should-not-execute").exists())

    def test_failed_empty_and_invalid_output_preserve_previous_script(self):
        self.destination.mkdir(parents=True)
        saved = self.destination / "pnpm.zsh"
        saved.write_text("# previous completion\n")
        for body in ("printf partial; exit 1", "exit 0", "printf 'if then\\n'"):
            with self.subTest(body=body):
                self.stub("pnpm", body)
                self.assertNotEqual(self.update("pnpm").returncode, 0)
                self.assertEqual(saved.read_text(), "# previous completion\n")
                self.assertEqual(list(self.destination.iterdir()), [saved])

    def test_pip_option_candidates_are_passed_as_data(self):
        for separator in ("", "-- "):
            with self.subTest(already_corrected=bool(separator)):
                self.stub("pip", '''
if [ -n "$PIP_AUTO_COMPLETE" ]; then
  printf '%s\\n' --outdated
  exit 1
fi
cat <<'SCRIPT'
__pip() { compadd ''' + separator + '''$(PIP_AUTO_COMPLETE=1 pip); }
compdef __pip -P 'pip[0-9.]#'
SCRIPT
''')
                self.success(self.update("pip"))
                result = self.zsh('''
compdef() { :; }
compadd() { [[ $1 == -- && $# == 2 ]] && print -r -- "$2"; }
source "$XDG_DATA_HOME/prezto/completions/pip.zsh"
__pip
''')
                self.assertEqual(self.success(result), "--outdated\n")

    def test_missing_tool_fails_without_replacing_its_script(self):
        self.destination.mkdir(parents=True)
        saved = self.destination / "pnpm.zsh"
        saved.write_text("# previous completion\n")
        self.assertNotEqual(self.update("pnpm").returncode, 0)
        self.assertEqual(saved.read_text(), "# previous completion\n")

    def test_scaleway_keeps_registration_without_reinitializing_completion(self):
        self.stub("scw", '''
printf '%s\\n' "$*" > "$TMPDIR/scw.arguments"
cat <<'SCRIPT'
autoload -U compinit && compinit
_scw() { compadd -- instance; }
compdef _scw scw
SCRIPT
''')
        self.success(self.update("scw"))
        self.assertEqual((self.root / "scw.arguments").read_text(), "autocomplete script shell=zsh\n")
        result = self.zsh('''
compinit() { print unexpected-reinitialization; }
compdef() { print -r -- "$*"; }
source "$XDG_DATA_HOME/prezto/completions/scw.zsh"
''')
        self.assertEqual(self.success(result), "_scw scw\n")

    def test_unknown_tool_is_rejected_before_generation(self):
        self.stub("pnpm", 'touch "$TMPDIR/should-not-execute"')
        self.assertNotEqual(self.update("pnpm unknown").returncode, 0)
        self.assertFalse((self.root / "should-not-execute").exists())
        self.assertFalse(self.destination.exists())

    def test_partial_failure_does_not_block_other_tools_or_change_caller(self):
        self.stub("pnpm", "exit 1")
        self.stub("pip", "printf '# native pip completion\\n'")
        result = self.zsh('''
fpath=("$PREZTO_TEST_REPO/modules/completion/functions" $fpath)
autoload -Uz prezto-completions-update
before_pwd=$PWD
before_umask=$(umask)
prezto-completions-update pnpm pip && exit 1
[[ $PWD == $before_pwd && $(umask) == $before_umask ]]
''')
        self.success(result)
        self.assertEqual((self.destination / "pip.zsh").read_text(), "# native pip completion\n")
        self.assertFalse((self.destination / "pnpm.zsh").exists())
