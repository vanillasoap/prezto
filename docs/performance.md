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

## Next measurements and improvements

1. Profile the user's enabled modules, first prompt, repeated prompts and directory
   changes separately. Compare small and large repositories and a clean shell.
   Keep startup work separate from work deferred to the first command.
2. Investigate a cheaper completion fingerprint while retaining immediate
   discovery, provider precedence, security checks, interruption recovery and
   concurrent-shell tests. Compare warm startup and rebuild cost before accepting
   a change; do not remove correctness checks to meet a timing target.
3. Measure actual manager initialization before adding lazy loading or init-text
   caches. Any cache must handle manager upgrades, plugins, PATH changes and
   interpreter selection. Avoid a generic deferral framework without evidence.
4. Measure Pure and Sorin's repeated prompt work in large repositories. Preserve
   updates after commits, branch changes and edits made without changing directory.
   A cache keyed only by the current directory is insufficient.
5. If trialling direnv, measure empty directories, project entry/exit, an unchanged
   environment and watched-file reloads. Use one environment-switching owner for
   each language. Direnv has not been installed or enabled by these changes.

Behavioral and syntax checks run in CI. Timing thresholds are intentionally
excluded from shared runners; compare benchmark distributions on the same host.
