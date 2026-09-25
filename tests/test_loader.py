import shutil

from support import REPO, ShellTestCase


class LoaderTests(ShellTestCase):
    def setUp(self):
        super().setUp()
        self.prezto = self.root / "prezto [test]"
        self.prezto.mkdir()
        shutil.copy2(REPO / "init.zsh", self.prezto / "init.zsh")

    def module(self, name, init="", function="print works"):
        directory = self.prezto / "modules" / name
        (directory / "functions").mkdir(parents=True)
        (directory / "init.zsh").write_text(init)
        (directory / "functions" / "sample-function").write_text(function)
        return directory

    def test_relative_installation_keeps_functions_available_after_cd(self):
        self.module("sample")
        result = self.zsh('''
source './prezto [test]/init.zsh'
pmodload sample
cd /
sample-function
''')
        self.assertEqual(self.success(result).strip(), "works")

    def test_failed_module_cleans_literal_path_and_can_be_retried(self):
        self.module("sample", "[[ -e $ZDOTDIR/ready ]]\n")
        result = self.zsh('''
source './prezto [test]/init.zsh'
pmodload sample
print "failed:$?"
print -l -- $fpath
touch "$ZDOTDIR/ready"
pmodload sample || exit
sample-function
''')
        output = self.success(result)
        self.assertIn("failed:1\n", output)
        self.assertNotIn(str(self.prezto / "modules/sample/functions"), output)
        self.assertTrue(output.endswith("works\n"), output)

    def test_missing_module_is_reported_on_stderr(self):
        result = self.zsh("source './prezto [test]/init.zsh'; pmodload nonexistent")
        self.assertEqual(result.returncode, 1)
        self.assertEqual(result.stdout, "")
        self.assertIn("no such module: nonexistent", result.stderr)

    def test_initialization_reports_failed_configured_modules(self):
        (self.config / ".zpreztorc").write_text("zstyle ':prezto:load' pmodule nonexistent\n")
        result = self.zsh("source './prezto [test]/init.zsh'")
        self.assertEqual(result.returncode, 1)

    def test_relative_extra_modules_keep_paths_and_do_not_leak_variables(self):
        extra = self.root / "extra/sample/functions"
        extra.mkdir(parents=True)
        (extra / "sample-function").write_text("print extra")
        result = self.zsh('''
zstyle ':prezto:load' pmodule-dirs extra
source './prezto [test]/init.zsh'
pmodload sample
cd /
sample-function
print "leaked:${+user_pmodule_dirs}:${+user_dir}"
''')
        self.assertEqual(self.success(result), "extra\nleaked:0:0\n")

    def test_module_dependency_cycle_fails_without_recursing(self):
        self.module("sample", "pmodload sample\n")
        result = self.zsh("source './prezto [test]/init.zsh'; pmodload sample")
        self.assertEqual(result.returncode, 1)
        self.assertIn("circular module dependency: sample", result.stderr)
