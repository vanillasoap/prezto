#
# Enables local Python package installation.
#
# Authors:
#   Sorin Ionescu <sorin.ionescu@gmail.com>
#   Sebastian Wiesner <lunaryorn@googlemail.com>
#   Patrick Bos <egpbos@gmail.com>
#   Indrajit Raychaudhuri <irc@indrajit.com>
#

#
# Options
#

setopt EXTENDED_GLOB

# Load dependencies.
pmodload 'helper'

# Load manually installed or package manager installed pyenv into the shell
# session.
if [[ -s "${local_pyenv::=${PYENV_ROOT:-$HOME/.pyenv}/bin/pyenv}" ]] \
      || (( $+commands[pyenv] )); then

  # Ensure manually installed pyenv is added to path when present.
  [[ -s $local_pyenv ]] && path=($local_pyenv:h $path)

  # Load pyenv into the shell session.
  eval "$(pyenv init - --no-rehash zsh)"

# Prepend PEP 370 per user site packages directory, which defaults to
# ~/Library/Python on macOS and ~/.local elsewhere, to PATH. The
# path can be overridden using PYTHONUSERBASE.
else
  if [[ -n "$PYTHONUSERBASE" ]]; then
    path=($PYTHONUSERBASE/bin(N) $path)
  elif is-darwin; then
    path=($HOME/Library/Python/*/bin(N) $path)
  else
    # This is subject to change.
    path=($HOME/.local/bin(N) $path)
  fi
fi

unset local_pyenv

# Return if requirements are not found.
if (( ! $+commands[(i)python[0-9.]#] && ! $+functions[pyenv] && ! $+commands[conda] )); then
  return 1
fi

function _python-workon-cwd {
  local project_root="$PWD:A" env_name env_dir use_workon=0
  # A .git file is also a project boundary (worktrees and submodules).
  while [[ $project_root != / && ! -e $project_root/.venv && ! -e $project_root/.git ]]; do
    project_root=$project_root:h
  done

  if [[ -f $project_root/.venv ]]; then
    env_name="$(<$project_root/.venv)"
  elif [[ -f $project_root/.venv/bin/activate ]]; then
    env_name="$project_root/.venv"
  elif [[ $project_root != / ]]; then
    env_name=$project_root:t
  fi

  if [[ -n $env_name ]]; then
    if [[ $env_name != /* && -n $WORKON_HOME && -f $WORKON_HOME/$env_name/bin/activate ]]; then
      env_dir="$WORKON_HOME/$env_name"
      (( $+functions[workon] )) && use_workon=1
    elif [[ $env_name == /* && -f $env_name/bin/activate ]]; then
      env_dir=$env_name
    elif [[ -f $project_root/$env_name/bin/activate ]]; then
      env_dir="$project_root/$env_name"
    fi
    [[ -z $env_dir ]] || env_dir=$env_dir:A
  fi

  # Own only environments activated by this hook. A manual replacement releases
  # that ownership, so changing directory cannot deactivate the user's choice.
  if [[ -n $CD_VIRTUAL_ENV && ( -z $VIRTUAL_ENV || $VIRTUAL_ENV:A != $CD_VIRTUAL_ENV ) ]]; then
    unset CD_VIRTUAL_ENV
  fi
  if [[ -n $CD_VIRTUAL_ENV && $env_dir != $CD_VIRTUAL_ENV ]]; then
    deactivate || return
    unset CD_VIRTUAL_ENV
  fi
  [[ -z $VIRTUAL_ENV && -n $env_dir ]] || return 0

  if (( use_workon )); then
    workon "$env_name" || return
  else
    source "$env_dir/bin/activate" || return
  fi
  export CD_VIRTUAL_ENV="$env_dir"
}

# Load auto workon cwd hook.
if zstyle -t ':prezto:module:python:virtualenv' auto-switch; then
  # Auto workon when changing directory.
  autoload -Uz add-zsh-hook
  add-zsh-hook chpwd _python-workon-cwd
fi

# Load virtualenvwrapper into the shell session, if pre-requisites are met
# and unless explicitly requested not to
if (( $+VIRTUALENVWRAPPER_VIRTUALENV || $+commands[virtualenv] )) \
      && zstyle -T ':prezto:module:python:virtualenv' initialize ; then
  # Set the directory where virtual environments are stored.
  export WORKON_HOME="${WORKON_HOME:-$HOME/.virtualenvs}"

  # Disable the virtualenv prompt. Note that we use the magic value used by the
  # pure prompt because there's some additional logic in that prompt which tries
  # to figure out if a user set this variable and disable the python portion of
  # that prompt based on it which is the exact opposite of what we want to do.
  export VIRTUAL_ENV_DISABLE_PROMPT=20

  # Create a sorted array of available virtualenv related 'pyenv' commands to
  # look for plugins of interest. Scanning shell '$path' isn't enough as they
  # can exist in 'pyenv' synthesized paths (e.g., '~/.pyenv/plugins') instead.
  local -a pyenv_plugins
  local pyenv_virtualenvwrapper_plugin_found
  if (( $+commands[pyenv] )); then
    pyenv_plugins=(${(@oM)${(f)"$(pyenv commands --no-sh 2> /dev/null)"}:#virtualenv*})

    # Optionally activate 'virtualenv-init' plugin when available.
    if (( $pyenv_plugins[(i)virtualenv-init] <= $#pyenv_plugins )); then
      eval "$(pyenv virtualenv-init - zsh)"
    fi

    # Optionally activate 'virtualenvwrapper' plugin when available.
    if (( $pyenv_plugins[(i)virtualenvwrapper(_lazy|)] <= $#pyenv_plugins )); then
      pyenv "$pyenv_plugins[(R)virtualenvwrapper(_lazy|)]"
      pyenv_virtualenvwrapper_plugin_found="true"
    fi

    unset pyenv_plugins
  fi

  if [[ $pyenv_virtualenvwrapper_plugin_found != "true" ]]; then
    # Fallback to standard 'virtualenvwrapper' if 'python' is available in '$path'.
    if (( ! $+VIRTUALENVWRAPPER_PYTHON )) && (( $+commands[(i)python[0-9.]#] )); then
      VIRTUALENVWRAPPER_PYTHON=$commands[(i)python[0-9.]#]
    fi

    virtualenvwrapper_sources=(
      ${(@Ov)commands[(I)virtualenvwrapper(_lazy|).sh]}
      /usr/share/virtualenvwrapper/virtualenvwrapper(_lazy|).sh(OnN)
    )
    if (( $#virtualenvwrapper_sources )); then
      source "$virtualenvwrapper_sources[1]"
    fi

    unset virtualenvwrapper_sources
  fi

  unset pyenv_virtualenvwrapper_plugin_found
fi

# Load conda into the shell session, if requested.
zstyle -T ':prezto:module:python' conda-init
if (( $? && $+commands[conda] )); then
  if (( $(conda ..changeps1) )); then
    echo "To make sure Conda doesn't change your prompt (should do that in the prompt module) run:\n  conda config --set changeps1 false"
    # TODO:
    # We could just run this ourselves. In an exit hook
    # (add zsh-hook zshexit [(anonymous) function]) we could then set it back
    # to the way it was before we changed it. However, I'm not sure if this is
    # exception safe, so left it like this for now.
  fi
fi

#
# Aliases
#

if ! zstyle -t ':prezto:module:python:alias' skip; then
  alias py='python'
  alias py2='python2'
  alias py3='python3'
fi
