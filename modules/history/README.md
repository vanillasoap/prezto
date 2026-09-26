# History

Sets [history][1] options and defines history aliases.

History defaults to _`${ZDOTDIR:-$HOME}/.zsh_history`_. Existing files are not
renamed or migrated. To keep an older `.zhistory` file, set `HISTFILE` to that
path before loading Prezto, or use the `histfile` style below.

## Options

- `BANG_HIST` treats the **!** character specially during expansion.
- `EXTENDED_HISTORY` writes the history file in the _:start:elapsed;command_
  format.
- `SHARE_HISTORY` shares history between all sessions. Note that
  `SHARE_HISTORY`, `INC_APPEND_HISTORY`, and `INC_APPEND_HISTORY_TIME` are
  mutually exclusive; this module clears the latter two when selecting sharing.
- `HIST_EXPIRE_DUPS_FIRST` expires a duplicate event first when trimming history.
- `HIST_IGNORE_ALL_DUPS` deletes an old recorded event if a new event is a
  duplicate.
- `HIST_FIND_NO_DUPS` does not display a previously found event.
- `HIST_IGNORE_SPACE` does not record an event starting with a space.
- `HIST_SAVE_NO_DUPS` does not write a duplicate event to the history file.
- `HIST_VERIFY` does not execute immediately upon history expansion.
- `HIST_BEEP` beeps when accessing non-existent history.

Sharing makes commands from other sessions available immediately. It does not
record accurate command durations, because entries are written before execution
finishes. To keep each session's navigation independent and record durations,
add this **after** loading Prezto in `.zshrc`:

```sh
unsetopt SHARE_HISTORY INC_APPEND_HISTORY
setopt INC_APPEND_HISTORY_TIME
```

`HIST_IGNORE_ALL_DUPS` already covers adjacent duplicates, so the narrower
`HIST_IGNORE_DUPS` option is unnecessary. Leading-space commands are removed
from saved history, but remain briefly available in the current editing session;
history filtering is not a secret-management mechanism.

## Variables

- `HISTFILE` stores the path to the history file.
- `HISTSIZE` stores the maximum number of events to save in the internal history.
- `SAVEHIST` stores the maximum number of events to save in the history file.

## Aliases

Aliases are enabled by default. To disable them, add the following to
_`${ZDOTDIR:-$HOME}/.zpreztorc`_.

```sh
zstyle ':prezto:module:history:alias' skip 'yes'
```

- `history-stat` lists the ten most used commands

## Settings

### histfile

Can be configured either by setting HISTFILE manually before loading this
module or by using zstyle:

```sh
zstyle ':prezto:module:history' histfile "<file_name>"
```

defaults to "${ZDOTDIR:-$HOME}/.zsh_history".

### histsize

```sh
zstyle ':prezto:module:history' histsize <number>
```

defaults to 10000.

### savehist

```sh
zstyle ':prezto:module:history' savehist <number>
```

defaults to histsize

## Authors

_The authors of this module should be contacted via the [issue tracker][2]._

- [Robby Russell](https://github.com/robbyrussell)
- [Sorin Ionescu](https://github.com/sorin-ionescu)
- [Indrajit Raychaudhuri](https://github.com/indrajitr)

[1]: https://zsh.sourceforge.net/Guide/zshguide02.html#l16
[2]: https://github.com/sorin-ionescu/prezto/issues
