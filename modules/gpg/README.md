# GPG

Provides for an easier use of [GPG][1] by setting up [gpg-agent][2].

Requires GnuPG 2.2 or newer, including `gpgconf`. GnuPG starts its agent on demand
for ordinary signing and decryption. Prezto sets `GPG_TTY` for pinentry and does
not source the obsolete `gpg-agent.env` cache or use `GPG_AGENT_INFO`.

## Settings

### SSH

To enable OpenSSH Agent protocol emulation, and make `gpg-agent` a drop-in
replacement for `ssh-agent`, add the following line to
_`$GNUPGHOME/gpg-agent.conf`_ or _`$HOME/.gnupg/gpg-agent.conf`_:

```conf
enable-ssh-support
```

When enabled and no different `SSH_AUTH_SOCK` is supplied, Prezto starts GPG's
agent using `gpg-connect-agent`, selects the socket reported by `gpgconf`, and
loads the SSH module. Load `gpg` before `ssh` in your module list to select GPG
as the agent. Forwarded and password-manager sockets remain selected.

While GPG supplies the SSH socket, a pre-command hook updates the pinentry TTY.
This remains necessary because other terminals can change the shared agent's
TTY and SSH cannot pass it with each request. It does not run when another
socket has been selected. No such hook is installed for ordinary GPG usage.

## Authors

_The authors of this module should be contacted via the [issue tracker][3]._

- [Sorin Ionescu](https://github.com/sorin-ionescu)

[1]: https://www.gnupg.org
[2]: https://www.gnupg.org/documentation/manuals/gnupg/Invoking-GPG_002dAGENT.html
[3]: https://github.com/sorin-ionescu/prezto/issues
