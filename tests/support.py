"""Run public Prezto commands against disposable files and local Git repos."""

import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest


REPO = Path(__file__).resolve().parents[1]
ZSH = os.environ.get("TEST_ZSH") or shutil.which("zsh")


class ShellTestCase(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix="prezto-test-")
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name).resolve()
        self.bin = self.root / "bin"
        self.bin.mkdir()
        self.config = self.root / "config"
        self.config.mkdir()
        self.env = {
            key: value for key, value in os.environ.items()
            if key in ("HOME", "USER", "LOGNAME", "SYSTEMROOT")
        }
        self.env.update(
            PATH=str(self.bin) + os.pathsep + os.defpath,
            ZDOTDIR=str(self.config),
            XDG_CACHE_HOME=str(self.root / "cache"),
            TMPDIR=str(self.root),
            HISTFILE=str(self.root / "history"),
            TERM="xterm-256color",
            LC_ALL="C",
            PREZTO_TEST_REPO=str(REPO),
            GIT_CONFIG_NOSYSTEM="1",
            GIT_CONFIG_GLOBAL=os.devnull,
            GIT_AUTHOR_NAME="Prezto Test",
            GIT_AUTHOR_EMAIL="prezto-test@example.invalid",
            GIT_COMMITTER_NAME="Prezto Test",
            GIT_COMMITTER_EMAIL="prezto-test@example.invalid",
        )

    def command(self, argv, cwd=None, check=True, env=None):
        return subprocess.run(
            argv, cwd=cwd or self.root, env=env or self.env,
            text=True, capture_output=True, timeout=30, check=check,
        )

    def zsh(self, script, cwd=None):
        return self.command([ZSH, "-d", "-f", "-c", script], cwd, check=False)

    def success(self, result):
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        return result.stdout

    def stub(self, name, body):
        path = self.bin / name
        path.write_text("#!/bin/sh\n" + body + "\n")
        path.chmod(0o755)

    def git(self, directory, *args):
        return self.command(["git", "-C", str(directory), *args]).stdout.strip()

    def init_git(self, directory):
        directory.mkdir(parents=True, exist_ok=True)
        self.git(directory, "init", "-q")
        self.git(directory, "symbolic-ref", "HEAD", "refs/heads/main")
        self.git(directory, "config", "commit.gpgsign", "false")
        self.git(directory, "config", "core.hooksPath", os.devnull)
