# Native tool completions

The completion module loads Zsh and Homebrew completion providers. Check those
before adding another provider for the same command.

For pnpm and pip, generate completion scripts using the installed tools:

```zsh
prezto-completions-update
```

This defaults to both tools. To update only selected tools, pass their names:

```zsh
prezto-completions-update pnpm pip
```

Scripts are stored in `${XDG_DATA_HOME:-$HOME/.local/share}/prezto/completions`.
Each script is checked for successful generation, nonempty output and valid Zsh
syntax before replacing its previous version. A missing tool or failed script
returns a failure status while preserving that tool's previous script. Other
requested tools can still update successfully.

The pip script receives one compatibility correction: completion candidates
beginning with `--` are passed as data to Zsh's `compadd`, so pip options such as
`--outdated` complete correctly.

Add this block after Prezto initialization in your personal shell configuration
(for example, `.zshrc.local` if your `.zshrc` sources it):

```zsh
for _prezto_program in pnpm pip; do
  _prezto_completion="${XDG_DATA_HOME:-$HOME/.local/share}/prezto/completions/$_prezto_program.zsh"
  if (( $+commands[$_prezto_program] )) && [[ -r $_prezto_completion ]]; then
    source "$_prezto_completion"
  fi
done
unset _prezto_program _prezto_completion
```

Only the saved scripts load at startup. Completion itself calls the selected
tool when you press Tab. Run `prezto-completions-update` after updating these
tools, then open a new shell. These explicitly installed scripts take precedence
over other registrations for their commands; remove the corresponding script if
you switch to another provider.

Add additional completion directories to `fpath` **before** Prezto initializes.
For example, Docker Desktop's `~/.docker/completions` belongs there. Prezto owns
`compinit`; do not run it again after loading the native scripts, because that
can discard their registrations.

Sources: [pnpm completion](https://pnpm.io/completion),
and [pip command completion](https://pip.pypa.io/en/stable/user_guide/#command-completion).
