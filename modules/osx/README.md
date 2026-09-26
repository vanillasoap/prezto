# OSX

Defines [macOS][1] aliases and functions.

This module must be loaded _before_ the [_`completion`_][2] module so that the
provided completion definitions are loaded automatically by _`completion`_
module.

## Settings

### Dash Keyword

To change the keyword used by `mand` to open man pages in [_Dash.app_][3] from
its default value of 'manpages', add the following line in
_`${ZDOTDIR:-$HOME}/.zpreztorc`_ and replace the **keyword** with the one
configured in [_Dash.app_][3].

```sh
zstyle ':prezto:module:osx:man' dash-keyword 'keyword'
```

## Aliases

- `cdf` changes the current working director to the current _Finder_ directory.
- `pushdf` pushes the current working directory onto the directory queue and
  changes the current working director to the current _Finder_ directory.
- `showfiles` shows hidden files in Finder and restarts Finder.
- `hidefiles` hides hidden files in Finder and restarts Finder.

## Functions

- `mand` opens _man_ pages in [_Dash.app_][3].
- `manp` opens _man_ pages in _Preview.app_.
- `pfd` prints the current _Finder_ directory.
- `pfs` prints the current _Finder_ selection.
- `ofd [directory ...]` opens directories in Finder, defaulting to the current
  directory.
- `tab [command [argument ...]]` creates a new tab in the current directory in
  Terminal, [iTerm2][4], or [Ghostty 1.3+][6].
- `split_tab [command [argument ...]]` creates a pane below the current pane in
  iTerm2 or Ghostty.
- `vsplit_tab [command [argument ...]]` creates a pane beside the current pane in
  iTerm2 or Ghostty.
- `ql` previews files in Quick Look.
- `osx-rm-dir-metadata` deletes _`.DS_Store`_, _`__MACOSX`_ cruft.
- `osx-ls-download-history` displays the macOS download history.
- `osx-rm-download-history` deletes the macOS download history.
- `trash` moves files and directories to the Finder Trash.

Tab and split helpers preserve the current directory and command arguments:

```sh
tab nvim 'notes with spaces.md'
split_tab pnpm dev
vsplit_tab zsh -c 'git status; git log -5 --oneline'
```

Arguments are treated literally; use `zsh -c` explicitly for shell expressions.
The helpers select the terminal from `TERM_PROGRAM`, falling back to the
frontmost app, and operate on that app's front window. They do not run over SSH.
macOS may request Automation permission when first called. Terminal.app's tab
shortcut additionally needs Accessibility permission; it has no independent
split-session API. iTerm2 and Ghostty use their scripting dictionaries.

Ghostty tabs need a window configuration that supports native tabs. In
particular, `macos-titlebar-style = hidden` prevents ordinary tab grouping;
Ghostty 1.3.1's native tab command can fail or create a separate window in this
configuration. Use `split_tab` or `vsplit_tab`, or select a visible titlebar in
Ghostty if tabs are wanted. Prezto does not change terminal appearance settings.

## Authors

_The authors of this module should be contacted via the [issue tracker][5]._

- [Sorin Ionescu](https://github.com/sorin-ionescu)

[1]: https://www.apple.com/macos/
[2]: ../completion#readme
[3]: https://kapeli.com/dash
[4]: https://www.iterm2.com/
[5]: https://github.com/sorin-ionescu/prezto/issues
[6]: https://ghostty.org/docs/features/applescript
