# Reuse a supplied SSH agent, or share one local agent between Prezto shells.
() {
  emulate -L zsh
  local socket="${XDG_CACHE_HOME:-$HOME/.cache}/prezto/ssh/agent.sock"
  local identity
  local -a identities

  if [[ -z $SSH_AUTH_SOCK || $SSH_AUTH_SOCK == $socket ]]; then
    (( $+commands[ssh-agent] && $+commands[ssh-add] )) || return 1
    # A kernel lock serializes startup and disappears if a shell is interrupted.
    # No executable environment cache or process-name/PID matching is needed.
    (
      umask 077
      command mkdir -p -- "$socket:h" || exit
      [[ -O $socket:h && ! -L $socket:h ]] || exit 1
      command chmod -- 700 "$socket:h" || exit
      zmodload -F zsh/system b:zsystem || exit
      : >> "$socket.lock" || exit
      local lock_fd
      zsystem flock -t 5 -f lock_fd "$socket.lock" || exit
      export SSH_AUTH_SOCK=$socket
      command ssh-add -l > /dev/null 2>&1
      local agent_status=$?
      if (( agent_status == 2 )); then
        # Remove only our stale endpoint; preserve any unexpected regular file.
        [[ ! -e $socket || -S $socket || -L $socket ]] || exit 1
        command rm -f -- "$socket" || exit
        command ssh-agent -s -a "$socket" > /dev/null || exit
        [[ -S $socket ]] || exit 1
      elif (( agent_status != 0 && agent_status != 1 )); then
        exit 1
      fi
    ) || return 1
    export SSH_AUTH_SOCK=$socket
    unset SSH_AGENT_PID
  fi

  # An external agent (forwarding, keychain, 1Password, GPG) owns its identities.
  # Add keys only when the user has explicitly requested them, with no globbing.
  if zstyle -a ':prezto:module:ssh:load' identities identities && (( $#identities )); then
    (( $+commands[ssh-add] )) || return 1
    for identity in "$identities[@]"; do
      [[ $identity == /* ]] || identity="$HOME/.ssh/$identity"
      if [[ -n $DISPLAY && -x $SSH_ASKPASS ]]; then
        command ssh-add "$identity" < /dev/null || return
      else
        command ssh-add "$identity" || return
      fi
    done
  fi
  return 0
}
