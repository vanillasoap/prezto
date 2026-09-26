# Prezto — Instantly Awesome Zsh

Prezto is the configuration framework for [Zsh][1]; it enriches the command line
interface environment with sane defaults, aliases, functions, auto completion,
and prompt themes.

## Installation

### Manual

Prezto will work with any recent release of Zsh, but the minimum required
version is **4.3.11**.

01. Launch Zsh:

    ```console
    zsh
    ```

02. Clone the repository:

    ```console
    git clone --recursive https://github.com/vanillasoap/prezto.git "${ZDOTDIR:-$HOME}/.zprezto"
    ```

    <details>
      <summary><em>Optional: Installing in <code>$XDG_CONFIG_HOME</code></em></summary>

      Optionally, if you already have `$XDG_CONFIG_HOME` configured (usually as
      _`$HOME/.config`_ by default) and intend to install Prezto under
      _`$XDG_CONFIG_HOME/zsh`_ instead, you can clone the repository there and
      configure `$ZDOTDIR` separately if not already configured.

      - Clone the repository:

        ```console
        git clone --recursive https://github.com/vanillasoap/prezto.git "${ZDOTDIR:-${XDG_CONFIG_HOME:-$HOME/.config}/zsh}/.zprezto"
        ```

      - Configure `$XDG_CONFIG_HOME` and `$ZDOTDIR` in _`$HOME/.zshenv`_:

        ```sh
        export XDG_CONFIG_HOME="${XDG_CONFIG_HOME:=$HOME/.config}"
        [[ -d $XDG_CONFIG_HOME/zsh ]] && export ZDOTDIR="$XDG_CONFIG_HOME/zsh"
        source "$ZDOTDIR/.zshenv"
        ```

    </details>

03. Create a new Zsh configuration by copying/linking the Zsh configuration
    files provided:

    ```console
    setopt EXTENDED_GLOB
    for rcfile in "${ZDOTDIR:-$HOME}"/.zprezto/runcoms/^README.md(.N); do
      ln -s "$rcfile" "${ZDOTDIR:-$HOME}/.${rcfile:t}"
    done
    ```

    **Note:** If you already have any of the given configuration files, `ln` in
    the above operation will cause an error. In simple cases, you can load
    Prezto by adding the line `source "${ZDOTDIR:-$HOME}/.zprezto/init.zsh"` to
    the bottom of your _`${ZDOTDIR:-$HOME}/.zshrc`_ and keep the rest of your
    Zsh configuration intact. For more complicated setups, we recommend that you
    back up your original configs and replace them with the provided Prezto
    [_`runcoms`_][10].

04. Set Zsh as your default shell:

    ```console
    chsh -s /bin/zsh
    ```

05. Open a new Zsh terminal window or tab.

### Troubleshooting

If you are not able to find certain commands after switching to Prezto, modify
the `PATH` variable in _`${ZDOTDIR:-$HOME}/.zprofile`_ then open a new Zsh
terminal window or tab.

## Updating

Run `zprezto-update` to fast-forward the current branch to its configured Git
upstream and update its submodules. Commit or stash local edits first. Diverged
branches require manual resolution. Running the command again retries an
interrupted submodule update even when the parent repository is already current.

To pull the latest changes and update submodules manually:

```console
cd $ZPREZTODIR
git pull
git submodule sync --recursive
git submodule update --init --recursive
```

## Usage

Prezto has many features disabled by default. Read the source code and the
accompanying README files to learn about what is available.

Run `zprezto-doctor` in an initialized shell to inspect loaded modules, completion
cache availability, the update upstream and submodule pins. It does not change
configuration, repair files or contact the network. A nonzero status means a
configured module did not load or a dependency check found a problem.

See [performance measurements and the improvement plan](docs/performance.md) for
the isolated startup benchmark and its limits.

### Project environments with direnv

[Direnv](https://direnv.net/) is an optional way to load and unload project
environment variables. After installing it, add its
[official Zsh hook](https://direnv.net/docs/hook.html) at the end of `.zshrc`, after
Prezto initialization:

```sh
eval "$(direnv hook zsh)"
```

Review each project's `.envrc` before authorizing it with `direnv allow`. If
direnv manages the same Python or Ruby environment, disable the competing Prezto
auto-switch hook in `.zpreztorc`:

```sh
zstyle ':prezto:module:python:virtualenv' auto-switch 'no'
zstyle ':prezto:module:ruby:chruby' auto-switch 'no'
```

Version managers can remain installed to provide interpreters. Direnv adds work
to prompt and directory-change hooks, so measure a trial before expecting a speed
improvement. Prezto does not install or enable it automatically.

### Modules

01. Browse [_`modules`_][9] to see what is available.
02. Load the modules you need in _`${ZDOTDIR:-$HOME}/.zpreztorc`_ and then open
    a new Zsh terminal window or tab.

### Themes

01. For a list of themes, type `prompt -l`.
02. To preview a theme, type `prompt -p name`.
03. Load the theme you like in _`${ZDOTDIR:-$HOME}/.zpreztorc`_ and then
    open a new Zsh terminal window or tab.

    ![sorin theme][2]
    Note that the [_`git`_][11] module may be required for special symbols to
    appear, such as those on the right of the above image. Add `'git'` to the
    `pmodule` list (under `zstyle ':prezto:load' pmodule \` in your
    _`${ZDOTDIR:-$HOME}/.zpreztorc`_) to enable this module.

### External Modules

01. By default modules will be loaded from [_`/modules`_][9] and _`/contrib`_.
02. Additional module directories can be added to the
    `:prezto:load:pmodule-dirs` setting in _`${ZDOTDIR:-$HOME}/.zpreztorc`_.

    Note that module names need to be unique or they will cause an error when
    loading.

    ```sh
    zstyle ':prezto:load' pmodule-dirs $HOME/.zprezto-contrib
    ```

## Customization

The project is managed via [Git][3]. We highly recommend that you fork this
project so that you can commit your changes and push them to your fork on
[GitHub][4] to preserve them. If you do not know how to use Git, follow this
[tutorial][5] and bookmark this [reference][6].

## Resources

The [Zsh Reference Card][7] and the [zsh-lovers][8] man page are indispensable.

## License

This project is licensed under the MIT License.

[1]: https://www.zsh.org
[2]: https://i.imgur.com/nrGV6pg.png "sorin theme"
[3]: https://git-scm.com
[4]: https://github.com
[5]: https://gitimmersion.com
[6]: https://git.github.io/git-reference/
[7]: http://www.bash2zsh.com/zsh_refcard/refcard.pdf
[8]: https://grml.org/zsh/zsh-lovers.html
[9]: modules#readme
[10]: runcoms#readme
[11]: modules/git#readme
