from support import ShellTestCase


class DockerTests(ShellTestCase):
    def setUp(self):
        super().setUp()
        self.stub("docker", "exit 0")
        self.stub("docker-machine", "exit 0")
        self.storage = self.root / "docker state"
        (self.storage / "machines/target").mkdir(parents=True)
        self.env["MACHINE_STORAGE_PATH"] = str(self.storage)
        self.load = 'source "$PREZTO_TEST_REPO/modules/docker/init.zsh"\n'

    def test_missing_storage_cannot_modify_the_callers_directory(self):
        (self.root / "target").mkdir()
        self.env["MACHINE_STORAGE_PATH"] = str(self.root / "missing")
        result = self.zsh(self.load + '''
pushd() { return 1; }
dkmd target
''')
        self.assertNotEqual(result.returncode, 0)
        self.assertFalse((self.root / "default").is_symlink())

    def test_default_selection_preserves_working_directory(self):
        result = self.zsh(self.load + '''
dkmd target || exit
print -r -- "$PWD"
''')
        self.assertEqual(self.success(result).strip(), str(self.root))
        self.assertEqual((self.storage / "machines/default").readlink().as_posix(), "target")

    def test_default_directory_is_never_removed(self):
        protected = self.storage / "machines/default"
        protected.mkdir()
        (protected / "state").write_text("preserve")
        result = self.zsh(self.load + 'dkmd target')
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual((protected / "state").read_text(), "preserve")

    def test_existing_default_link_can_be_replaced_but_not_linked_to_itself(self):
        default = self.storage / "machines/default"
        default.symlink_to("target")
        (self.storage / "machines/other machine").mkdir()
        self.success(self.zsh(self.load + "dkmd 'other machine'"))
        self.assertEqual(default.readlink().as_posix(), "other machine")
        self.success(self.zsh(self.load + "dkmd default"))
        self.assertEqual(default.readlink().as_posix(), "other machine")

    def test_link_failure_is_returned_without_explicitly_removing_old_link(self):
        default = self.storage / "machines/default"
        default.symlink_to("target")
        self.stub("ln", "exit 7")
        self.assertEqual(self.zsh(self.load + "dkmd target").returncode, 7)
        self.assertEqual(default.readlink().as_posix(), "target")

    def test_environment_failure_is_not_evaluated(self):
        self.stub("docker-machine", 'echo \'touch "$TMPDIR/partial-env"\'; exit 7')
        result = self.zsh(self.load + 'dkme target')
        self.assertNotEqual(result.returncode, 0)
        self.assertFalse((self.root / "partial-env").exists())
