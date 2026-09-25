from support import ShellTestCase


class DoctorTests(ShellTestCase):
    def setUp(self):
        super().setUp()
        self.project = self.root / "project"
        self.init_git(self.project)
        self.env["PREZTO_DOCTOR_DIR"] = str(self.project)

    def test_reports_current_shell_without_writing_files(self):
        before = self.git(self.project, "status", "--porcelain")
        result = self.zsh('''
source "$PREZTO_TEST_REPO/init.zsh"
ZPREZTODIR=$PREZTO_DOCTOR_DIR
zprezto-doctor
''')
        output = self.success(result)
        self.assertIn("Zsh:", output)
        self.assertIn("Prezto:", output)
        self.assertIn("Submodules: pins match", output)
        self.assertEqual(self.git(self.project, "status", "--porcelain"), before)
        self.assertFalse((self.root / "cache").exists())

    def test_reports_failed_configured_module(self):
        result = self.zsh('''
source "$PREZTO_TEST_REPO/init.zsh"
ZPREZTODIR=$PREZTO_DOCTOR_DIR
zstyle ':prezto:load' pmodule missing
zprezto-doctor
''')
        self.assertEqual(result.returncode, 1)
        self.assertIn("Module missing: not loaded", result.stdout)

    def test_reports_uninitialized_submodule(self):
        dependency = self.root / "dependency"
        self.init_git(dependency)
        self.git(dependency, "commit", "--allow-empty", "-qm", "initial")
        revision = self.git(dependency, "rev-parse", "HEAD")
        (self.project / ".gitmodules").write_text(
            '[submodule "library"]\n\tpath = library\n\turl = ' + str(dependency) + '\n')
        self.git(self.project, "add", ".gitmodules")
        self.git(self.project, "update-index", "--add", "--cacheinfo", "160000," + revision + ",library")
        self.git(self.project, "commit", "-qm", "dependency")
        result = self.zsh('''
source "$PREZTO_TEST_REPO/init.zsh"
ZPREZTODIR=$PREZTO_DOCTOR_DIR
zprezto-doctor
''')
        self.assertEqual(result.returncode, 1)
        self.assertIn("Submodules: 1 missing", result.stdout)
