# GnuPG owns its agent lifecycle; ordinary GPG commands start it on demand.
(( $+commands[gpgconf] && $+commands[gpg-agent] )) || return 1

[[ -z $TTY ]] || export GPG_TTY=$TTY
[[ -z $SSH_CONNECTION ]] || export PINENTRY_USER_DATA='USE_CURSES=1'

() {
  emulate -L zsh
  local configuration socket
  configuration="$(command gpgconf --list-options gpg-agent)" || return
  # gpgconf resolves the active configuration, including alternate GNUPGHOME.
  [[ ${(M)${(f)configuration}:#enable-ssh-support:*:1} ]] || return 0
  socket="$(command gpgconf --list-dirs agent-ssh-socket)" || return
  [[ -n $socket ]] || return 1

  # Preserve forwarding and independently configured password-manager agents.
  [[ -z $SSH_AUTH_SOCK || $SSH_AUTH_SOCK == $socket ]] || return 0
  (( $+commands[gpg-connect-agent] )) || return 1
  command gpg-connect-agent /bye > /dev/null || return
  [[ -S $socket ]] || return 1
  export SSH_AUTH_SOCK=$socket
  unset SSH_AGENT_PID

  # SSH cannot tell GPG which terminal to use. Refresh before commands while
  # this shell uses GPG's socket, since another shell may have changed the TTY.
  typeset -g _gpg_agent_ssh_socket=$socket
  function _gpg-agent-update-tty {
    [[ -n $TTY && $SSH_AUTH_SOCK == $_gpg_agent_ssh_socket ]] || return 0
    export GPG_TTY=$TTY
    command gpg-connect-agent UPDATESTARTUPTTY /bye > /dev/null
  }
  autoload -Uz add-zsh-hook
  add-zsh-hook preexec _gpg-agent-update-tty
  pmodload 'ssh'
}
