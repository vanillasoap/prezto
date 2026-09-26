#
# Defines Docker aliases.
#
# Author:
#   François Vantomme <akarzim@gmail.com>
#

# Return if requirements are not found.
if (( ! $+commands[docker] )); then
  return 1
fi

#
# Functions
#

# Set Docker Machine environment
function dkme {
  if (( ! $+commands[docker-machine] )); then
    return 1
  fi

  local machine_env
  machine_env="$(docker-machine env "$@")" || return
  eval "$machine_env"
}

# Set Docker Machine default machine
function dkmd {
  if (( ! $+commands[docker-machine] )); then
    return 1
  fi

  if (( $# != 1 )); then
    print -u2 -- 'usage: dkmd <machine>'
    return 1
  fi

  (
    builtin cd -q -- "${MACHINE_STORAGE_PATH:-$HOME/.docker/machine}/machines" || exit
    if [[ ! -d $1 ]]; then
      print -u2 -- "Docker machine '$1' does not exist."
      exit 1
    fi
    [[ $1 == default ]] && exit 0
    if [[ -e default && ! -L default ]]; then
      print -u2 -- "A file or directory named 'default' already exists."
      exit 1
    fi
    ln -sfn -- "$1" default
  )
}

# Source module files.
source "${0:h}/alias.zsh"
