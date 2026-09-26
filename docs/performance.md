# Performance

Run the repeatable benchmark from the repository root:

```sh
python3 -B tests/benchmark.py --runs 30
```

It uses disposable configuration and caches, preserves HOME, and does not read
personal shell startup files. Profiles run in shuffled order after warmups. The
JSON output includes raw samples, median, p95, Zsh version, locale and repository
commit. The portable harness uses `LC_ALL=C`.
The first sample includes a fresh completion cache; subsequent samples reuse it.
Filesystem caches are not flushed. This measures loading Prezto and exiting,
excluding the first prompt hook, terminal rendering and personal configuration.

## Baseline and current tradeoffs

Earlier audit measurements on x86_64 macOS with Zsh 5.9.2, September 25, 2026,
used `LANG=en_US.UTF-8` and 30 warm samples per profile. These are separate runs
on the same machine, not paired
measurements or cross-platform promises.

| Profile | Before core fixes | After core fixes |
| --- | ---: | ---: |
| Bare Zsh | 6.72 ms | 7.05 ms |
| Loader with no modules | 13.18 ms | 13.87 ms |
| Defaults with Pure | 63.97 ms | 85.29 ms |
| Pure without completion | 48.34 ms | 50.26 ms |
| Pure with suggestions and highlighting | 80.54 ms | 101.72 ms |
| Fresh completion cache, median of 10 | 583.14 ms | 629.46 ms |

The completion correctness fix adds roughly 20 ms to warm startup in these
measurements. It checks paths, filenames, modification times and directory
permissions, then reuses a compiled dump. New and replaced completion definitions
take effect immediately; cache builds recover after interruption and do not
depend on login shells. An initial implementation that rescanned inputs twice
cost about 47 ms extra and was replaced. Faster invalidation remains useful work.

The shipped harness subsequently measured commit `75f32d6` with `LC_ALL=C`:
Pure's warm median was 72.42 ms (p95 74.18 ms), and Pure with suggestions and
highlighting was 89.97 ms (p95 92.21 ms), across 30 samples each. Those figures
are a separate baseline; compare runs using the same harness and locale.

The language changes remove specific repeated work:

- Python and Ruby skip startup rehashing. Run `pyenv rehash` or `rbenv rehash`
  after installation if a new executable is missing from their shims.
- Node version information is queried only when a display format is configured.
- An already loaded nvm is preserved.
- Python project switching walks directories without invoking Git, activates a
  project environment once, and preserves manually selected environments.

These language modules are not enabled by the default benchmark profiles, so
their improvements do not offset the completion cost in the table. A separate
safe probe of installed pyenv 2.8.4 took about 50.5 ms to generate full init text
with `--no-rehash`; it did not evaluate that text or measure rehash savings.

## Interactive measurements

The PTY benchmark measures prompt output, command readiness, filename completion,
and a 256-character editing batch in disposable directories:

```sh
TEST_ZSH=/bin/zsh python3 -B tests/benchmark-interactive.py --runs 10
TEST_ZSH=/bin/zsh python3 -B tests/benchmark-interactive.py --installed --runs 10
```

The default uses isolated configuration with Pure, autosuggestions and syntax
highlighting. `--installed` reads your actual login files and requires the Pure
prompt. Both use disposable history, preserve HOME, and disable Pure's background
fetches. The Git workloads contain 100 or 10,000 tracked files, with up to 100
modified files. Completed filenames and typed buffers are checked without
executing the completed command. Results include raw samples and nearest-rank
p95 values. The first run is reported separately from warmed samples.

These measurements include terminal I/O and ZLE, but not GUI painting or the time
until asynchronous Git decorations settle. First-command time starts when input
is sent after the first prompt appears. The typing result measures a batch,
not latency for an individual physical keystroke. Ten samples provide only a
rough view of tail latency; timing is not a CI gate.

On the audited Intel Mac, September 26, 2026, Scaleway's generated completion
script ran a second `compinit` during startup. The explicit native completion
refresh now removes that bootstrap. Interleaved before/after/after/before runs
of copied personal startup files, with ten warm samples per workload and
`LC_ALL=en_US.UTF-8`, measured these median first-prompt times:

| Workload | Before | After | Reduction |
| --- | ---: | ---: | ---: |
| Outside Git | 1136 ms | 1088 ms | 48 ms |
| Git, 100 files | 1146 ms | 1090 ms | 56 ms |
| Git, 10,000 files | 1151 ms | 1107 ms | 44 ms |

This is about a 4–5% startup improvement for that configuration, not a universal
Prezto speedup. The earlier non-interleaved comparison suggested a larger gain;
the repeated comparison above is the more conservative result. After the change,
first-command readiness was 30–40 ms, warm filename completion about 5 ms in the
small workload and 59 ms in the large one, and the editing batch about 178–180 ms.
These interaction timings did not materially improve with the startup change.

## Compiling nvm's startup script

Zsh can read a compiled copy of nvm's script while keeping its normal version
selection. In a separate September 26 comparison using nvm 0.40.8 and Zsh 5.9,
compilation reduced median first-prompt time by 89–134 ms (about 5–8%). The
before/after/after/before sequence used copied personal startup files and ten
warm samples per workload:

| Workload | Source script | Compiled script | Reduction |
| --- | ---: | ---: | ---: |
| Outside Git | 1725.4 ms | 1591.5 ms | 133.9 ms |
| Git, 100 files | 1703.1 ms | 1613.8 ms | 89.3 ms |
| Git, 10,000 files | 1740.3 ms | 1610.8 ms | 129.5 ms |

These are paired results from a later session; compare within this table, not
against the earlier absolute timings. First-command, completion and editing
timings were materially unchanged. This is a local nvm optimization, not a
change to Prezto's module defaults.

After installing or updating nvm, run this once in the Zsh version you normally
use, with `NVM_DIR` set to your nvm installation:

```zsh
(umask 077; zcompile -UR -- "$NVM_DIR/nvm.sh")
```

Leave the existing `source "$NVM_DIR/nvm.sh"` line in place. Only parsing is
cached: nvm still selects the version, updates PATH and checks npm configuration
on every startup. The generated `nvm.sh.zwc` file is local and disposable; remove
it to undo the optimization. Zsh uses the source when it is newer than the
compiled file, and another Zsh version can fall back to the source. Regenerate
the cache after nvm updates to retain the speed benefit. If restoring an older
source file with its original timestamp, remove or regenerate the cache too.
See [Zsh's source and zcompile documentation][zcompile].

## Further speed improvements

1. Nvm's automatic version selection is the main remaining synchronous manager
   cost in the personal profile, even with its script compiled. Evaluate it
   separately before changing startup.
   Any deferred or cached alternative must preserve the default version, inherited
   PATH, `.nvmrc` behavior, `command node`, npm, child processes and completions.
   The current automatic Node selection remains enabled.
2. Investigate a cheaper completion fingerprint while retaining immediate
   discovery, provider precedence, security checks, interruption recovery and
   concurrent-shell tests. Compare warm startup and rebuild cost before accepting
   a change; do not remove correctness checks to meet a timing target.
3. Profile filename completion in large directories separately from prompt work.
   The 10,000-file workload shows that warm completion cost grows even when
   startup is unchanged. Preserve case-insensitive and approximate matching
   behavior before considering changes to completion policy.
4. Measure Pure and Sorin's repeated prompt work in large repositories. Preserve
   updates after commits, branch changes and edits made without changing directory.
   A cache keyed only by the current directory is insufficient.
5. Keep GPG's TTY refresh when GPG owns the SSH socket: different terminals share
   the agent, and SSH does not pass its current TTY. Ordinary GPG use now relies
   on native agent startup and does not install that per-command hook.

Behavioral and syntax checks run in CI. Timing thresholds are intentionally
excluded from shared runners; compare benchmark distributions on the same host.

[zcompile]: https://zsh.sourceforge.io/Doc/Release/Shell-Builtin-Commands.html
