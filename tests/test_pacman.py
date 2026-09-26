import json
import shlex
import sys

from support import ShellTestCase


class PacmanTests(ShellTestCase):
    def setUp(self):
        super().setUp()
        recorder = self.root / "record.py"
        recorder.write_text(
            "import json,os,sys\n"
            "print(json.dumps(sys.argv[1:]), flush=True)\n"
            "if sys.argv[1]=='sudo': os.execvp(sys.argv[2],sys.argv[2:])\n"
        )
        for program in ("pacman", "paru", "yay", "sudo", "asp"):
            self.stub(program, f"exec {shlex.quote(sys.executable)} {shlex.quote(str(recorder))} {program} \"$@\"")

    def run_aliases(self, script, frontend=None):
        setting = "" if frontend is None else "zstyle ':prezto:module:pacman' frontend " + shlex.quote(frontend) + "\n"
        result = self.zsh(setting + '''
source "$PREZTO_TEST_REPO/modules/pacman/init.zsh" || exit
''' + "eval " + shlex.quote(script))
        return [json.loads(line) for line in self.success(result).splitlines()]

    def test_native_and_missing_frontend_use_sudo_only_for_mutations(self):
        for frontend in (None, "pacman", "unavailable"):
            with self.subTest(frontend=frontend):
                calls = self.run_aliases("paci 'package name'; pacU; pacman-list-orphans", frontend)
                self.assertEqual(calls, [
                    ["sudo", "pacman", "--sync", "package name"],
                    ["pacman", "--sync", "package name"],
                    ["sudo", "pacman", "--sync", "--refresh", "--sysupgrade"],
                    ["pacman", "--sync", "--refresh", "--sysupgrade"],
                    ["pacman", "--query", "--deps", "--unrequired"],
                ])

    def test_yay_and_paru_run_without_wrapping_them_in_sudo(self):
        for frontend in ("yay", "paru"):
            with self.subTest(frontend=frontend):
                self.assertEqual(self.run_aliases("paci package; pacU; pacman-list-orphans", frontend), [
                    [frontend, "--sync", "package"],
                    [frontend, "--sync", "--refresh", "--sysupgrade"],
                    [frontend, "--query", "--deps", "--unrequired"],
                ])

    def test_file_queries_keep_paths_intact_and_do_not_elevate(self):
        for frontend in (None, "yay", "paru"):
            with self.subTest(frontend=frontend):
                command = frontend or "pacman"
                self.assertEqual(self.run_aliases("pacown 'path with spaces'; pacls zsh; pacfiles bin/zsh", frontend), [
                    [command, "--query", "--owns", "path with spaces"],
                    [command, "--query", "--list", "zsh"],
                    [command, "--files", "bin/zsh"],
                ])

    def test_file_database_refresh_uses_selected_frontend(self):
        self.assertEqual(self.run_aliases("pacfileupg"), [
            ["sudo", "pacman", "--files", "--refresh"],
            ["pacman", "--files", "--refresh"],
        ])
        self.assertEqual(self.run_aliases("pacfileupg", "paru"), [["paru", "--files", "--refresh"]])

    def test_legacy_refresh_does_not_run_retired_asp(self):
        self.assertEqual(self.run_aliases("pacu"), [
            ["sudo", "pacman", "--sync", "--refresh"],
            ["pacman", "--sync", "--refresh"],
        ])
