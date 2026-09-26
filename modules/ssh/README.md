# SSH

Provides for an easier use of [SSH][1] by setting up [_ssh-agent_][2].

A supplied `SSH_AUTH_SOCK` is preserved, including forwarded agents, the macOS
keychain, 1Password, and GPG. The supplier owns that agent's availability.
Without a supplied socket, Prezto shares a local agent at
`${XDG_CACHE_HOME:-$HOME/.cache}/prezto/ssh/agent.sock`. Startup is serialized
between shells, and a stale socket is replaced after a failed connection.
The old `ssh-agent.env` cache is no longer read; an existing agent is not killed.

## Settings

### Identities

Keys are loaded at startup only when explicitly configured. To load identities,
add the following line to
_`${ZDOTDIR:-$HOME}/.zpreztorc`_:

```sh
zstyle ':prezto:module:ssh:load' identities 'id_ed25519' 'id_github'
```

Names are relative to `~/.ssh`; absolute paths also work. Paths are literal and
do not expand wildcards. Loading a key may prompt for its passphrase. Omit this
setting when your password manager or another agent manages the keys, or use
OpenSSH's `AddKeysToAgent` setting to load keys when first used by SSH.

## Authors

_The authors of this module should be contacted via the [issue tracker][3]._

[Sorin Ionescu](https://github.com/sorin-ionescu)

[1]: https://www.openssh.com
[2]: https://www.openbsd.org/cgi-bin/man.cgi?query=ssh-agent&sektion=1
[3]: https://github.com/sorin-ionescu/prezto/issues
