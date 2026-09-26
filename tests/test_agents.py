import socket
import concurrent.futures
import os
import re
import shlex
import shutil
import signal
import tempfile
from pathlib import Path

from support import ShellTestCase


class AgentTests(ShellTestCase):
    def setUp(self):
        super().setUp()
        self.env["GNUPGHOME"] = str(self.root / "gnupg")
        (self.root / "gnupg").mkdir()
        self.calls = self.root / "calls"
        self.env["AGENT_CALLS"] = str(self.calls)
        self.env["LIST_STATUS"] = "2"
        self.stub("ssh-agent", 'echo start-ssh >> "$AGENT_CALLS"; exit 7')
        self.stub("ssh-add", '''
printf 'ssh-add %s\\n' "$*" >> "$AGENT_CALLS"
[ "$1" != -l ] || exit "${LIST_STATUS:-1}"
''')
        self.stub("gpg-agent", 'echo old-gpg-start >> "$AGENT_CALLS"')
        self.stub("gpgconf", '''
printf 'gpgconf %s\\n' "$*" >> "$AGENT_CALLS"
case "$1" in
  --list-options) printf 'enable-ssh-support:0:0:SSH:0:0::::%s\\n' "${GPG_SSH:-}";;
  --list-dirs) printf '%s\\n' "$GPG_SOCKET";;
esac
''')
        self.stub("gpg-connect-agent", 'echo connect-gpg >> "$AGENT_CALLS"; exit "${GPG_STATUS:-0}"')

    def socket(self, name):
        path = self.root / name
        sock = socket.socket(socket.AF_UNIX)
        self.addCleanup(sock.close)
        sock.bind(str(path))
        return str(path)

    def load(self, module, script=""):
        return self.zsh('''
pmodload() { print -r -- "module $*" >> "$AGENT_CALLS"; }
source "$PREZTO_TEST_REPO/modules/''' + module + '''/init.zsh" || exit
''' + script)

    def log(self):
        return self.calls.read_text() if self.calls.exists() else ""

    def test_ssh_preserves_external_socket_without_loading_default_keys(self):
        self.env["SSH_AUTH_SOCK"] = self.socket("external.sock")
        self.assertEqual(self.success(self.load("ssh", 'print -r -- "$SSH_AUTH_SOCK"')).strip(),
                         self.env["SSH_AUTH_SOCK"])
        self.assertNotIn("start-ssh", self.log())
        self.assertNotIn("ssh-add \n", self.log())

    def test_explicit_identities_are_literal_arguments(self):
        self.env["SSH_AUTH_SOCK"] = self.socket("external.sock")
        result = self.zsh('''
zstyle ':prezto:module:ssh:load' identities 'test key' 'id_*'
source "$PREZTO_TEST_REPO/modules/ssh/init.zsh"
''')
        self.success(result)
        self.assertIn("/test key", self.log())
        self.assertIn("/id_*", self.log())

    def test_ssh_start_failure_propagates_without_sourcing_legacy_cache(self):
        cache = self.root / "cache" / "prezto"
        cache.mkdir(parents=True)
        (cache / "ssh-agent.env").write_text('print legacy-cache-was-executed\n')
        result = self.load("ssh")
        self.assertNotEqual(result.returncode, 0)
        self.assertNotIn("legacy-cache-was-executed", result.stdout)
        self.assertIn("start-ssh", self.log())

    def test_real_ssh_agent_recovers_stale_socket_and_serializes_startup(self):
        agent = shutil.which("ssh-agent", path=os.defpath)
        add = shutil.which("ssh-add", path=os.defpath)
        if not agent or not add:
            self.skipTest("OpenSSH agent tools unavailable")
        # Unix socket paths must stay below the platform's short length limit.
        with tempfile.TemporaryDirectory(prefix="prezto-agent-", dir="/tmp") as directory:
            self.env["XDG_CACHE_HOME"] = directory
            endpoint = Path(directory) / "prezto" / "ssh" / "agent.sock"
            endpoint.parent.mkdir(parents=True)
            stale = socket.socket(socket.AF_UNIX)
            stale.bind(str(endpoint))
            stale.close()
            output = self.root / "agent-output"
            self.stub("ssh-agent", f'{shlex.quote(agent)} "$@" | tee {shlex.quote(str(output))}')
            self.stub("ssh-add", f'exec {shlex.quote(add)} "$@"')
            try:
                with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
                    results = list(pool.map(lambda _: self.load("ssh", 'print -r -- "$SSH_AUTH_SOCK"'), range(4)))
                for result in results:
                    self.assertEqual(self.success(result).strip(), str(endpoint))
                before = output.read_bytes()
                self.success(self.load("ssh"))
                self.assertEqual(output.read_bytes(), before)
                self.assertEqual(endpoint.parent.stat().st_mode & 0o777, 0o700)
            finally:
                if output.exists():
                    match = re.search(r"SSH_AGENT_PID=(\d+)", output.read_text())
                    if match:
                        os.kill(int(match[1]), signal.SIGTERM)

    def test_gpg_defers_startup_for_normal_gpg_usage(self):
        cache = self.root / "cache" / "prezto"
        cache.mkdir(parents=True)
        (cache / "gpg-agent.env").write_text('print legacy-cache-was-executed\n')
        result = self.load("gpg")
        self.success(result)
        self.assertNotIn("legacy-cache-was-executed", result.stdout)
        self.assertNotIn("old-gpg-start", self.log())
        self.assertNotIn("connect-gpg", self.log())

    def test_gpg_ssh_uses_reported_socket_and_updates_tty(self):
        self.env.update(GPG_SSH="1", GPG_SOCKET=self.socket("gpg.sock"))
        result = self.load("gpg", '''
print -r -- "$SSH_AUTH_SOCK"
print -r -- "${preexec_functions[@]}"
TTY=/dev/prezto-test
_gpg-agent-update-tty
SSH_AUTH_SOCK=/other-agent
_gpg-agent-update-tty
''')
        output = self.success(result)
        self.assertIn(self.env["GPG_SOCKET"], output)
        self.assertIn("_gpg-agent-update-tty", output)
        self.assertEqual(self.log().count("connect-gpg"), 2)

    def test_gpg_preserves_forwarded_or_password_manager_agent(self):
        self.env.update(GPG_SSH="1", GPG_SOCKET=self.socket("gpg.sock"),
                        SSH_AUTH_SOCK=self.socket("forwarded.sock"))
        output = self.success(self.load("gpg", 'print -r -- "$SSH_AUTH_SOCK"'))
        self.assertEqual(output.strip(), self.env["SSH_AUTH_SOCK"])
        self.assertNotIn("connect-gpg", self.log())
        self.assertNotIn("module ssh", self.log())

    def test_failed_gpg_start_does_not_select_an_unusable_socket(self):
        self.env.update(GPG_SSH="1", GPG_SOCKET=str(self.root / "absent.sock"), GPG_STATUS="9")
        result = self.load("gpg")
        self.assertNotEqual(result.returncode, 0)
        self.assertNotIn("module ssh", self.log())
