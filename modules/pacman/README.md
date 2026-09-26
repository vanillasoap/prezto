# Pacman

Provides aliases and functions for the [Pacman][1] package manager and
frontends.

## Settings

It is possible to use a Pacman frontend with the pacman aliases provided by this
package as long as that frontend supports the same command line options (The
[AUR Helpers][2] page has a good comparison which lists if the command line
options are pacman compatible).

Please note that installing packages with an AUR Helper is not officially
supported by Archlinux. It is currently recommended to manually build AUR
packages using the [provided instructions][3]. The [aurutils][4] project has a
set of small utilities to make this easier.

To enable a different Pacman frontend, add the following to
_`${ZDOTDIR:-$HOME}/.zpreztorc`_, and replace `'<frontend>'` with the name
of the preferred frontend.

```sh
zstyle ':prezto:module:pacman' frontend '<frontend>'
```

For example, select an installed [paru][6] or [yay][7] executable:

```sh
zstyle ':prezto:module:pacman' frontend 'paru'
```

The module calls the selected helper directly, allowing it to manage privilege
escalation. With no setting, an unavailable helper, or an explicit `pacman`
setting, mutation commands use `sudo pacman`. Queries do not use `sudo`.
Normal package-manager confirmation prompts remain enabled.

Load `pacman` before `completion` in the Arch host's module list. Pacman and
helper packages provide their own Zsh completions; no Oh My Zsh plugin is needed.

## Aliases

### Pacman

- `pac` is short for `pacman`.
- `paci` installs packages from repositories.
- `pacI` installs packages from files.
- `pacx` removes packages.
- `pacX` removes packages, their configuration, and unneeded dependencies.
- `pacq` displays information about a package from the repositories.
- `pacQ` displays information about a package from the local database.
- `pacs` searches for packages in the repositories.
- `pacS` searches for packages in the local database.
- `pacown` identifies the installed package that owns a file.
- `pacls` lists the files installed by a package.
- `pacfiles` searches repository package contents, including uninstalled packages.
- `pacfileupg` refreshes the repository file database used by `pacfiles`.
- `pacu` refreshes package metadata only; it does not upgrade installed packages.
- `pacU` synchronizes the local package database against the repositories then
  upgrades outdated packages.
- `pacman-list-orphans` lists orphan packages.
- `pacman-remove-orphans` removes orphan packages.

Prefer `pacU` for routine updates, keeping metadata refresh and system upgrade
together. The old implicit `asp update` step has been removed: Arch [replaced
asp with pkgctl][8]. To obtain official package sources, use `pkgctl repo clone
<package>` separately.

Examples:

```sh
pacown /usr/bin/zsh
pacls zsh
pacfileupg
pacfiles bin/zsh
```

## Functions

- `aurget` clone an aur package.
- `pacman-list-explicit` lists explicitly installed pacman packages.
- `pacman-list-disowned` lists pacman disowned files.

## Authors

_The authors of this module should be contacted via the [issue tracker][5]._

- [Benjamin Boudreau](https://github.com/dreur)
- [Sorin Ionescu](https://github.com/sorin-ionescu)

[1]: https://www.archlinux.org/pacman/
[2]: https://wiki.archlinux.org/title/AUR_helpers#Comparison_tables
[3]: https://wiki.archlinux.org/title/Arch_User_Repository#Installing_and_upgrading_packages
[4]: https://github.com/AladW/aurutils
[5]: https://github.com/sorin-ionescu/prezto/issues
[6]: https://github.com/Morganamilo/paru
[7]: https://github.com/Jguer/yay
[8]: https://archlinux.org/news/git-migration-completed/
