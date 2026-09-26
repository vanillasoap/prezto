from support import ShellTestCase


class LanguageTests(ShellTestCase):
    def test_node_preserves_and_exports_custom_installation_prefix(self):
        self.stub("node", "exit 0")
        result = self.zsh('''
nvm() { :; }
N_PREFIX="$TMPDIR/custom node"
source "$PREZTO_TEST_REPO/init.zsh"
pmodload node || exit
sh -c 'printf "%s\\n" "$N_PREFIX"'
''')
        self.assertEqual(self.success(result).strip(), str(self.root / "custom node"))

    def test_conda_hook_runs_only_when_enabled(self):
        self.env["PYENV_ROOT"] = str(self.root / "no-pyenv")
        self.stub("conda", '''
printf '%s\\n' "$*" >> "$TMPDIR/conda-calls"
if [ "$*" = 'shell.zsh hook' ]; then
  printf '%s\\n' 'conda() { print -r -- "activated:$*"; }'
fi
''')
        for setting in ("off", None, "on"):
            with self.subTest(setting=setting):
                calls = self.root / "conda-calls"
                calls.unlink(missing_ok=True)
                setup = '' if setting is None else f"zstyle ':prezto:module:python' conda-init {setting}\n"
                result = self.zsh(setup + '''
source "$PREZTO_TEST_REPO/init.zsh"
pmodload python || exit
if (( $+functions[conda] )); then conda activate project; fi
''')
                self.success(result)
                if setting == "on":
                    self.assertEqual(result.stdout, "activated:activate project\n")
                    self.assertEqual(calls.read_text(), "shell.zsh hook\n")
                else:
                    self.assertFalse(calls.exists())

    def test_failed_conda_hook_is_not_evaluated(self):
        self.env["PYENV_ROOT"] = str(self.root / "no-pyenv")
        self.stub("conda", '''
echo 'touch "$TMPDIR/partial-hook"'
exit 7
''')
        result = self.zsh('''
zstyle ':prezto:module:python' conda-init on
source "$PREZTO_TEST_REPO/init.zsh"
pmodload python
''')
        self.assertNotEqual(result.returncode, 0)
        self.assertFalse((self.root / "partial-hook").exists())

    def test_python_display_runs_an_available_interpreter(self):
        for available in ("python3", "python"):
            with self.subTest(available=available):
                for name in ("python3", "python"):
                    (self.bin / name).unlink(missing_ok=True)
                self.stub(available, "echo Python 3.13.0")
                result = self.zsh('''
zmodload zsh/zutil
fpath=("$PREZTO_TEST_REPO/modules/python/functions" $fpath)
autoload -Uz python-info
zstyle ':prezto:module:python:info:version' format 'Python %v'
path=("$TMPDIR/bin")
python-info
print -r -- "$python_info[version]"
''')
                self.assertEqual(self.success(result), "Python 3.13.0\n")
                (self.bin / available).unlink()

    def test_bundler_install_sets_project_path_without_removed_flag(self):
        self.env["RBENV_ROOT"] = str(self.root / "rbenv")
        self.stub("rbenv", "echo ':'")
        self.stub("ruby", "exit 0")
        self.stub("bundle", 'printf "%s\\n" "$*" >> "$TMPDIR/bundle-calls"')
        result = self.zsh('''
source "$PREZTO_TEST_REPO/init.zsh"
pmodload ruby || exit
eval 'rbbi --jobs 2'
''')
        self.success(result)
        self.assertEqual((self.root / "bundle-calls").read_text(),
                         "config set --local path vendor/bundle\ninstall --jobs 2\n")

    def test_node_version_is_not_queried_without_display_format(self):
        self.stub("node", 'echo called >> "$TMPDIR/node-calls"; echo v24.0.0')
        result = self.zsh('''
zmodload zsh/zutil
fpath=("$PREZTO_TEST_REPO/modules/node/functions" $fpath)
autoload -Uz node-info
node-info
node-info
print -r -- "${node_info[version]-}"
''')
        self.assertEqual(self.success(result), "\n")
        self.assertFalse((self.root / "node-calls").exists())

    def test_node_version_display_is_preserved(self):
        self.stub("node", "echo v24.0.0")
        result = self.zsh('''
zmodload zsh/zutil
fpath=("$PREZTO_TEST_REPO/modules/node/functions" $fpath)
autoload -Uz node-info
zstyle ':prezto:module:node:info:version' format 'Node %v'
node-info
print -r -- "$node_info[version]"
''')
        self.assertEqual(self.success(result), "Node 24.0.0\n")

    def test_loaded_nvm_is_not_initialized_again(self):
        nvm = self.root / "nvm"
        nvm.mkdir()
        (nvm / "nvm.sh").write_text('print sourced >> "$TMPDIR/nvm-calls"\n')
        self.env["NVM_DIR"] = str(nvm)
        result = self.zsh('''
nvm() { print existing; }
source "$PREZTO_TEST_REPO/init.zsh"
pmodload node
nvm
''')
        self.assertEqual(self.success(result), "existing\n")
        self.assertFalse((self.root / "nvm-calls").exists())

    def test_python_and_ruby_initialization_do_not_rehash(self):
        for module, manager in (("python", "pyenv"), ("ruby", "rbenv")):
            with self.subTest(module=module):
                self.env[manager.upper() + "_ROOT"] = str(self.root / manager)
                self.stub(manager, '''
case " $* " in
  *" --no-rehash "*) echo ':' ;;
  *) echo 'touch "$TMPDIR/rehash"' ;;
esac
''')
                self.stub(module, "exit 0")
                result = self.zsh('source "$PREZTO_TEST_REPO/init.zsh"; pmodload ' + module)
                self.success(result)
                self.assertFalse((self.root / "rehash").exists())

    def python_project(self):
        self.env["PYENV_ROOT"] = str(self.root / "pyenv")
        self.stub("pyenv", "echo ':'")
        self.stub("python", "exit 0")
        project = self.root / "project with spaces"
        (project / ".venv/bin").mkdir(parents=True)
        (project / "child").mkdir()
        (project / ".venv/bin/activate").write_text('''
export VIRTUAL_ENV=${0:A:h:h}
print -r -- "$VIRTUAL_ENV" >> "$TMPDIR/activations"
deactivate() {
  print deactivated >> "$TMPDIR/deactivations"
  unset VIRTUAL_ENV
}
''')
        self.env["PREZTO_PROJECT"] = str(project)
        return '''
source "$PREZTO_TEST_REPO/init.zsh"
zstyle ':prezto:module:python:virtualenv' auto-switch yes
zstyle ':prezto:module:python:virtualenv' initialize no
pmodload python || exit
'''

    def test_directory_changes_activate_once_and_deactivate_on_exit(self):
        result = self.zsh(self.python_project() + '''
cd "$PREZTO_PROJECT"
cd child
cd ..
cd "$TMPDIR"
print "active:${VIRTUAL_ENV-unset}"
''')
        self.assertEqual(self.success(result), "active:unset\n")
        self.assertEqual(len((self.root / "activations").read_text().splitlines()), 1)
        self.assertEqual((self.root / "deactivations").read_text(), "deactivated\n")

    def test_manually_selected_environment_is_preserved(self):
        setup = self.python_project()
        result = self.zsh(setup + '''
export VIRTUAL_ENV="$TMPDIR/manual"
cd "$PREZTO_PROJECT"
cd "$TMPDIR"
print -r -- "$VIRTUAL_ENV"
''')
        self.assertEqual(self.success(result).strip(), str(self.root / "manual"))
        self.assertFalse((self.root / "activations").exists())

    def test_manual_replacement_of_automatic_environment_is_preserved(self):
        result = self.zsh(self.python_project() + '''
cd "$PREZTO_PROJECT"
export VIRTUAL_ENV="$TMPDIR/manual"
cd "$TMPDIR"
print -r -- "$VIRTUAL_ENV"
''')
        self.assertEqual(self.success(result).strip(), str(self.root / "manual"))
        self.assertFalse((self.root / "deactivations").exists())

    def test_named_virtualenv_uses_workon_once(self):
        setup = self.python_project()
        project = self.root / "project with spaces"
        workon_home = self.root / "environments"
        workon_home.mkdir()
        (project / ".venv").rename(workon_home / "named")
        (project / ".venv").write_text("named\n")
        self.env["WORKON_HOME"] = str(workon_home)
        result = self.zsh(setup + '''
workon() {
  print workon >> "$TMPDIR/workon-calls"
  source "$WORKON_HOME/$1/bin/activate"
}
cd "$PREZTO_PROJECT"
cd child
print -r -- "$VIRTUAL_ENV"
''')
        self.assertEqual(self.success(result).strip(), str(workon_home / "named"))
        self.assertEqual((self.root / "workon-calls").read_text(), "workon\n")
