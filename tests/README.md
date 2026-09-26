# Tests

Run the repository's behavioral regression tests from its root:

```sh
python3 -B -m unittest discover -s tests -v
```

The same suite runs on macOS and Linux in GitHub Actions, plus a Linux build of
the minimum supported Zsh 5.3.1. It includes a syntax
check of repository-owned shell files, excluding external submodule source.
To measure isolated startup time separately, run `python3 -B tests/benchmark.py`;
see [the performance guide](../docs/performance.md) for scope and limitations.
`tests/benchmark-interactive.py` adds PTY prompt, completion and editing
measurements; its `--installed` mode explicitly opts into personal login files.

The tests use Python's standard library, Zsh, Git, and system archive tools.
Select another Zsh with `TEST_ZSH=/bin/zsh`. They use disposable directories,
isolated configuration/cache paths, local Git repositories, and harmless
command substitutes for failure cases. They do not source personal startup
files or change the user's Git configuration.

Tests exercise public commands and hooks. Filesystem operations must preserve
inputs on failure, and Git helpers must preserve local work and history.
