from support import ShellTestCase


class LanguageTests(ShellTestCase):
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
