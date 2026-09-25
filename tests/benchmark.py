"""Measure isolated source-init time; never read personal shell configuration."""

import argparse
import json
import random
import statistics
import time

from support import REPO, ZSH, ShellTestCase


parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("--runs", type=int, default=30)
args = parser.parse_args()
if args.runs < 3:
    parser.error("--runs must be at least 3")

fixture = ShellTestCase()
fixture.setUp()
modules = "environment terminal editor history directory spectrum utility completion history-substring-search prompt"
profiles = {
    "bare": "",
    "loader": "",
    "pure": modules,
    "pure_with_suggestions_and_highlighting": modules.replace(
        " prompt", " autosuggestions syntax-highlighting prompt"),
}
cases = {}

try:
    for name, configured in profiles.items():
        config = fixture.root / name
        config.mkdir()
        (config / ".zpreztorc").write_text(
            "zstyle ':prezto:load' pmodule " + configured + "\n"
            "zstyle ':prezto:module:prompt' theme pure\n"
            "zstyle ':prezto:module:editor' key-bindings emacs\n"
            "zstyle ':prezto:*:*' color yes\n"
            "zstyle ':prezto:module:terminal' auto-title no\n")
        env = dict(fixture.env, ZDOTDIR=str(config), XDG_CACHE_HOME=str(config / "cache"),
                   PURE_GIT_PULL="0")
        code = "exit" if name == "bare" else 'source "$PREZTO_TEST_REPO/init.zsh"'
        cases[name] = ([ZSH, "-d", "-f", "-i", "-c", code], env)

    def measure(name):
        command, env = cases[name]
        start = time.perf_counter_ns()
        result = fixture.command(command, env=env, check=False)
        if result.returncode or result.stderr:
            raise RuntimeError(f"{name}: exit {result.returncode}: {result.stdout}{result.stderr}")
        return (time.perf_counter_ns() - start) / 1_000_000

    first = {name: measure(name) for name in cases}
    for name in cases:
        for _ in range(3):
            measure(name)
    samples = {name: [] for name in cases}
    order = list(cases)
    random.seed(42)
    for _ in range(args.runs):
        random.shuffle(order)
        for name in order:
            samples[name].append(measure(name))
    print(json.dumps({
        "zsh": fixture.command([ZSH, "--version"]).stdout.strip(),
        "commit": fixture.git(REPO, "rev-parse", "HEAD"),
        "scope": "Isolated source-init only; excludes first precmd and terminal rendering",
        "runs": args.runs,
        "profiles": {
            name: {
                "first_ms": first[name],
                "median_ms": statistics.median(values),
                "p95_ms": sorted(values)[int(.95 * (len(values) - 1))],
                "samples_ms": values,
            } for name, values in samples.items()
        },
    }, indent=2))
finally:
    fixture.doCleanups()
