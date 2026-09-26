"""Measure Zsh interaction through a PTY, without executing completed commands."""

import argparse
import fcntl
import json
import os
import pty
import random
import math
import select
import signal
import statistics
import struct
import termios
import time

from support import REPO, ZSH, ShellTestCase

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("--runs", type=int, default=10)
parser.add_argument("--installed", action="store_true", help="Read your actual login files; requires the Pure prompt")
args = parser.parse_args()
if args.runs < 3:
    parser.error("--runs must be at least 3")

READY = b"\x1b]777;ready\x07"
BUFFER = b"\x1b]777;buffer:"
FIRST = b"\x1b]777;command\x07"
bootstrap = r"""HISTFILE=/dev/null; bindkey -e; autoload -Uz add-zle-hook-widget; _prezto_bench_ready() { printf '\033]777;ready\007'; }; _prezto_bench_buffer() { printf '\033]777;buffer:%s\007' "$BUFFER"; }; zle -N _prezto_bench_buffer; bindkey '^X^P' _prezto_bench_buffer; add-zle-hook-widget line-init _prezto_bench_ready"""


class Terminal:
    def __init__(self, command, env, cwd):
        self.pending = b""
        self.started = time.perf_counter_ns()
        self.pid, self.fd = pty.fork()
        if not self.pid:
            os.chdir(cwd)
            os.execve(command[0], command, env)
        fcntl.ioctl(self.fd, termios.TIOCSWINSZ, struct.pack("HHHH", 40, 160, 0, 0))

    def send(self, data):
        os.write(self.fd, data)

    def until(self, marker, timeout=30):
        deadline = time.monotonic() + timeout
        while marker not in self.pending:
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                raise RuntimeError("PTY timed out waiting for the expected Pure prompt or widget")
            if select.select([self.fd], [], [], remaining)[0]:
                chunk = os.read(self.fd, 65536)
                if not chunk:
                    raise RuntimeError("Shell exited before the measurement finished")
                self.pending += chunk
        end = self.pending.index(marker) + len(marker)
        result, self.pending = self.pending[:end], self.pending[end:]
        return result

    def buffer(self):
        self.send(b"\x18\x10")
        self.until(BUFFER)
        return self.until(b"\x07")[:-1].decode()

    def close(self):
        # History is disposable. HUP also cleans up the shell's async workers.
        try:
            os.kill(self.pid, signal.SIGHUP)
        except ProcessLookupError:
            pass
        os.close(self.fd)
        os.waitpid(self.pid, 0)


def elapsed(start):
    return (time.perf_counter_ns() - start) / 1_000_000


fixture = ShellTestCase()
fixture.setUp()
try:
    modules = "environment terminal editor history directory spectrum utility git completion syntax-highlighting history-substring-search autosuggestions prompt"
    (fixture.config / ".zpreztorc").write_text(
        "zstyle ':prezto:load' pmodule " + modules + "\n"
        "zstyle ':prezto:module:prompt' theme pure\n"
        "zstyle ':prezto:module:editor' key-bindings emacs\n"
        "zstyle ':prezto:*:*' color yes\n")
    (fixture.config / ".zshrc").write_text('source "$PREZTO_TEST_REPO/init.zsh"\n')
    env = dict(fixture.env, LC_ALL="en_US.UTF-8", PURE_GIT_PULL="0")
    command = [ZSH, "-d", "-i"]
    if args.installed:
        env.pop("ZDOTDIR")
        env.pop("XDG_CACHE_HOME")
        # Login files choose the usual PATH. Do not inherit credentials or agents.
        command = [ZSH, "-i", "-l"]

    directories = {}
    for name, count in [("outside_git", 0), ("small_git", 100), ("large_git", 10000)]:
        directory = fixture.root / name
        directory.mkdir()
        (directory / "completion-target").touch()
        if count:
            fixture.init_git(directory)
            for n in range(count):
                (directory / f"file-{n:05}").write_text("baseline\n")
            fixture.git(directory, "add", ".")
            fixture.git(directory, "commit", "-qm", "benchmark fixture")
            for n in range(min(count, 100)):
                (directory / f"file-{n:05}").write_text("modified\n")
        directories[name] = directory

    def measure(directory):
        terminal = Terminal(command, env, directory)
        try:
            terminal.until("❯".encode())
            result = {"first_prompt_ms": elapsed(terminal.started)}
            start = time.perf_counter_ns()
            terminal.send(b" printf '\\033]777;command\\007'\n")
            terminal.until(FIRST)
            result["first_command_ms"] = elapsed(start)
            terminal.send((" " + bootstrap + "\n").encode())
            terminal.until(READY)
            start = time.perf_counter_ns()
            terminal.send(b" :\n")
            terminal.until(READY)
            result["next_prompt_ms"] = elapsed(start)
            for phase in ("first", "warm"):
                terminal.send(b"cat completion-targ")
                if terminal.buffer() != "cat completion-targ":
                    raise RuntimeError("Typed completion prefix was not preserved")
                start = time.perf_counter_ns()
                terminal.send(b"\t")
                completed = terminal.buffer()
                result[phase + "_tab_ms"] = elapsed(start)
                if completed != "cat completion-target ":
                    raise RuntimeError("Tab did not complete the fixture filename")
                terminal.send(b"\x15")
            text = ": " + "abcdefgh" * 32
            start = time.perf_counter_ns()
            terminal.send(text.encode())
            if terminal.buffer() != text:
                raise RuntimeError("Typed buffer was corrupted")
            result["type_256_ms"] = elapsed(start)
            return result
        finally:
            terminal.close()

    # Prime filesystem and completion caches; report the first run separately.
    first = {name: measure(directory) for name, directory in directories.items()}
    samples = {name: [] for name in directories}
    order = list(directories)
    random.seed(42)
    for _ in range(args.runs):
        random.shuffle(order)
        for name in order:
            samples[name].append(measure(directories[name]))
    print(json.dumps({
        "commit": fixture.git(REPO, "rev-parse", "HEAD"),
        "zsh": fixture.command([ZSH, "--version"]).stdout.strip(),
        "configuration": "installed login files" if args.installed else "isolated Prezto with Pure, suggestions and highlighting",
        "locale": env["LC_ALL"],
        "runs": args.runs,
        "scope": "PTY output and ZLE completion/readiness; excludes GUI rendering and waiting for async Git decorations. Typing is a 256-character batch, not per-key latency.",
        "first_run": first,
        "profiles": {name: {
            "metrics": {key: {"median_ms": statistics.median(row[key] for row in rows),
                              "p95_ms": sorted(row[key] for row in rows)[math.ceil(.95 * len(rows)) - 1]}
                        for key in rows[0]},
            "samples": rows,
        } for name, rows in samples.items()},
    }, indent=2))
finally:
    fixture.doCleanups()
