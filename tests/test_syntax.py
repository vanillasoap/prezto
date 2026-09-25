from support import REPO, ZSH, ShellTestCase


class SyntaxTests(ShellTestCase):
    def test_repository_shell_files_parse(self):
        tracked = self.git(REPO, "ls-files", "-z").split("\0")
        for name in tracked:
            path = REPO / name
            if not path.is_file() or path.is_symlink() or path.suffix == ".md":
                continue
            if name.endswith(".zsh") or "/functions/" in name or name.startswith("runcoms/"):
                with self.subTest(file=name):
                    self.success(self.command([ZSH, "-n", str(path)], check=False))
