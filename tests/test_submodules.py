from support import ShellTestCase


LOAD = '''
source "$PREZTO_TEST_REPO/modules/helper/init.zsh"
fpath=("$PREZTO_TEST_REPO/modules/git/functions" $fpath)
autoload -Uz git-root git-dir git-submodule-remove git-submodule-move
'''


class SubmoduleTests(ShellTestCase):
    def setUp(self):
        super().setUp()
        source = self.root / "source"
        self.init_git(source)
        (source / "tracked").write_text("original\n")
        self.git(source, "add", "tracked")
        self.git(source, "commit", "-qm", "initial")
        self.project = self.root / "project"
        self.init_git(self.project)
        self.git(self.project, "-c", "protocol.file.allow=always", "submodule",
                 "add", "--name", "library", str(source), "library")
        self.git(self.project, "commit", "-qam", "add dependency")

    def test_removal_rejects_dirty_submodule_and_preserves_metadata(self):
        tracked = self.project / "library/tracked"
        tracked.write_text("local edits\n")
        before = (self.project / ".gitmodules").read_bytes()
        result = self.zsh(LOAD + "git-submodule-remove library", self.project)
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(tracked.read_text(), "local edits\n")
        self.assertEqual((self.project / ".gitmodules").read_bytes(), before)

    def test_move_preserves_dirty_files_and_local_commit(self):
        library = self.project / "library"
        (library / "tracked").write_text("local commit\n")
        self.git(library, "commit", "-qam", "local only")
        revision = self.git(library, "rev-parse", "HEAD")
        (library / "untracked").write_text("untracked work\n")
        result = self.zsh(LOAD + "git-submodule-move library 'nested/new library'", self.project)
        self.success(result)
        destination = self.project / "nested/new library"
        self.assertEqual(self.git(destination, "rev-parse", "HEAD"), revision)
        self.assertEqual((destination / "untracked").read_text(), "untracked work\n")
        self.assertEqual(self.git(self.project, "config", "-f", ".gitmodules",
                                  "--get", "submodule.library.path"), "nested/new library")

    def test_failed_move_preserves_source(self):
        (self.project / "occupied").write_text("destination")
        result = self.zsh(LOAD + "git-submodule-move library occupied", self.project)
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual((self.project / "library/tracked").read_text(), "original\n")
        self.assertEqual((self.project / "occupied").read_text(), "destination")

    def test_remove_handles_distinct_name_and_retains_local_history(self):
        self.git(self.project, "config", "-f", ".gitmodules", "--rename-section",
                 "submodule.library", "submodule.named")
        self.git(self.project, "commit", "-qam", "rename module")
        library = self.project / "library"
        (library / "tracked").write_text("local commit\n")
        self.git(library, "commit", "-qam", "local only")
        revision = self.git(library, "rev-parse", "HEAD")
        gitdir = self.git(library, "rev-parse", "--absolute-git-dir")
        self.git(self.project, "add", "library")
        self.git(self.project, "commit", "-qm", "record local pin")
        result = self.zsh(LOAD + "git-submodule-remove library", self.project)
        self.success(result)
        self.assertFalse(library.exists())
        retained = self.git(self.project, "--git-dir=" + gitdir,
                            "--work-tree=" + str(self.project), "cat-file", "-t", revision)
        self.assertEqual(retained, "commit")

    def test_helpers_reject_ordinary_files(self):
        (self.project / "ordinary").write_text("keep")
        self.git(self.project, "add", "ordinary")
        self.git(self.project, "commit", "-qm", "ordinary file")
        for command in ("git-submodule-remove ordinary", "git-submodule-move ordinary other"):
            with self.subTest(command=command):
                result = self.zsh(LOAD + command, self.project)
                self.assertNotEqual(result.returncode, 0)
                self.assertEqual((self.project / "ordinary").read_text(), "keep")
