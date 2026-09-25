from support import ShellTestCase


class UpdateTests(ShellTestCase):
    def setUp(self):
        super().setUp()
        self.dependency = self.root / "dependency"
        self.init_git(self.dependency)
        (self.dependency / "content").write_text("version one\n")
        self.git(self.dependency, "add", "content")
        self.git(self.dependency, "commit", "-qm", "initial")
        self.upstream = self.root / "upstream"
        self.init_git(self.upstream)
        self.git(self.upstream, "branch", "-m", "master")
        self.git(self.upstream, "-c", "protocol.file.allow=always", "submodule",
                 "add", str(self.dependency), "library")
        self.git(self.upstream, "commit", "-qm", "initial")
        self.project = self.root / "project"
        self.git(self.root, "clone", "-q", str(self.upstream), str(self.project))
        self.env.update(GIT_CONFIG_COUNT="1", GIT_CONFIG_KEY_0="protocol.file.allow",
                        GIT_CONFIG_VALUE_0="always", PREZTO_UPDATE_DIR=str(self.project))

    def update(self):
        return self.zsh('''
source "$PREZTO_TEST_REPO/init.zsh"
ZPREZTODIR=$PREZTO_UPDATE_DIR
zprezto-update
local result=$?
[[ $PWD == $TMPDIR ]] || exit 99
exit $result
''')

    def test_up_to_date_parent_repairs_missing_submodule(self):
        self.success(self.update())
        self.assertEqual((self.project / "library/content").read_text(), "version one\n")

    def test_updates_configured_branch_and_new_submodule_pin(self):
        self.git(self.project, "branch", "-m", "custom")
        (self.dependency / "content").write_text("version two\n")
        self.git(self.dependency, "commit", "-qam", "second")
        self.git(self.upstream / "library", "fetch")
        self.git(self.upstream / "library", "checkout", "-q", "origin/main")
        self.git(self.upstream, "commit", "-qam", "update pin")
        self.success(self.update())
        self.assertEqual(self.git(self.project, "branch", "--show-current"), "custom")
        self.assertEqual((self.project / "library/content").read_text(), "version two\n")

    def test_refuses_diverged_branch(self):
        (self.project / "local").write_text("local work")
        self.git(self.project, "add", "local")
        self.git(self.project, "commit", "-qm", "local")
        before = self.git(self.project, "rev-parse", "HEAD")
        (self.upstream / "remote").write_text("remote work")
        self.git(self.upstream, "add", "remote")
        self.git(self.upstream, "commit", "-qm", "remote")
        self.assertNotEqual(self.update().returncode, 0)
        self.assertEqual(self.git(self.project, "rev-parse", "HEAD"), before)

    def test_refuses_dirty_submodule(self):
        self.success(self.update())
        content = self.project / "library/content"
        content.write_text("local edits")
        self.assertNotEqual(self.update().returncode, 0)
        self.assertEqual(content.read_text(), "local edits")

    def test_reports_missing_upstream(self):
        self.git(self.project, "branch", "--unset-upstream")
        result = self.update()
        self.assertEqual(result.returncode, 1)
        self.assertIn("configured upstream", result.stderr)
