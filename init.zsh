#
# Initializes Prezto.
#
# Authors:
#   Sorin Ionescu <sorin.ionescu@gmail.com>
#

#
# Version Check
#

# Check for the minimum supported version.
min_zsh_version='5.3.1'
if ! autoload -Uz is-at-least || ! is-at-least "$min_zsh_version"; then
  printf "prezto: old shell detected, minimum required: %s\n" "$min_zsh_version" >&2
  return 1
fi
unset min_zsh_version

# zprezto convenience updater
# The function is surrounded by ( ) instead of { } so it starts in a subshell
# and won't affect the environment of the calling shell
function zprezto-update {
  (
    builtin cd -q -- "$ZPREZTODIR" || return 1
    local upstream
    upstream="$(command git rev-parse --abbrev-ref --symbolic-full-name '@{upstream}' 2> /dev/null)" || {
      print -u2 -- "zprezto-update: the current branch needs a configured upstream"
      return 1
    }

    # Refuse local edits before changing either the parent or its dependencies.
    command git diff --quiet --ignore-submodules=all &&
      command git diff --cached --quiet --ignore-submodules=all &&
      command git submodule foreach --quiet --recursive '
        git diff --quiet && git diff --cached --quiet &&
        test -z "$(git ls-files --others --exclude-standard)"
      ' || {
        print -u2 -- "zprezto-update: commit or stash local changes before updating"
        return 1
      }

    command git fetch || return
    command git merge --ff-only "$upstream" || {
      print -u2 -- "zprezto-update: cannot fast-forward; resolve the branch manually"
      return 1
    }

    # Always reconcile pins, even after an interrupted update whose parent
    # checkout already reached upstream. Never force a submodule checkout.
    command git submodule sync --recursive || return
    command git submodule update --init --recursive
  )
}
# Report the current shell's configuration without changing it or fetching updates.
function zprezto-doctor {
  emulate -L zsh
  local result=0 pmodule upstream submodules line
  local -a pmodules
  print -r -- "Zsh: $ZSH_VERSION"
  print -r -- "Prezto: $ZPREZTODIR"

  zstyle -a ':prezto:load' pmodule pmodules
  for pmodule in "$pmodules[@]"; do
    if zstyle -t ":prezto:module:$pmodule" loaded; then
      print -r -- "Module $pmodule: loaded"
    else
      print -r -- "Module $pmodule: not loaded (check requirements and startup errors)"
      result=1
    fi
  done

  if zstyle -t ':prezto:module:completion' loaded; then
    local dump="${XDG_CACHE_HOME:-$HOME/.cache}/prezto/zcompdump-$ZSH_VERSION"
    if [[ -s $dump ]]; then
      print -r -- "Completion cache: $dump"
      [[ -s $dump.zwc ]] && print 'Compiled completion cache: present'
    else
      print 'Completion cache: unavailable (completion can run without a cache)'
    fi
  fi

  if ! (( $+commands[git] )); then
    print 'Git: unavailable; update and submodule checks require Git'
    return 1
  fi
  if ! command git -C "$ZPREZTODIR" rev-parse --git-dir > /dev/null 2>&1; then
    print 'Git: this installation has no repository metadata'
    return $result
  fi
  upstream="$(command git -C "$ZPREZTODIR" rev-parse --abbrev-ref --symbolic-full-name '@{upstream}' 2> /dev/null)"
  print -r -- "Update upstream: ${upstream:-not configured}"
  if submodules="$(command git -C "$ZPREZTODIR" submodule status --recursive 2> /dev/null)"; then
    local mismatched=0
    for line in "${(@f)submodules}"; do
      [[ $line == [-+U]* ]] && (( ++mismatched ))
    done
    if (( mismatched )); then
      print -r -- "Submodules: $mismatched missing, mismatched or conflicted pins; run zprezto-update after saving local work"
      result=1
    else
      print 'Submodules: pins match'
    fi
  else
    print 'Submodules: unable to inspect repository metadata'
    result=1
  fi
  return $result
}

#
# Module Loader
#

# Loads Prezto modules.
function pmodload {
  local -a pmodules
  local -a pmodule_dirs
  local -a locations
  local -a user_pmodule_dirs
  local user_dir
  local pmodule
  local pmodule_location
  local result=0
  local pfunction_glob='^([_.]*|prompt_*_setup|README*|*~)(-.N:t)'

  # Load in any additional directories and warn if they don't exist
  zstyle -a ':prezto:load' pmodule-dirs 'user_pmodule_dirs'
  for user_dir in "$user_pmodule_dirs[@]"; do
    if [[ ! -d "$user_dir" ]]; then
      print -u2 -- "$0: Missing user module dir: $user_dir"
    fi
  done
  user_pmodule_dirs=("${(@)user_pmodule_dirs:A}")

  pmodule_dirs=("$ZPREZTODIR/modules" "$ZPREZTODIR/contrib" "$user_pmodule_dirs[@]")

  # $argv is overridden in the anonymous function.
  pmodules=("$argv[@]")

  # Load Prezto modules.
  for pmodule in "$pmodules[@]"; do
    if zstyle -t ":prezto:module:$pmodule" loaded; then
      continue
    elif zstyle -t ":prezto:module:$pmodule" loading; then
      print -u2 -- "$0: circular module dependency: $pmodule"
      result=1
      continue
    else
      locations=(${pmodule_dirs:+${^pmodule_dirs}/$pmodule(-/FN)})
      if (( ${#locations} > 1 )); then
        if ! zstyle -t ':prezto:load' pmodule-allow-overrides 'yes'; then
          print -u2 -- "$0: conflicting module locations: $locations"
          result=1
          continue
        fi
      elif (( ${#locations} < 1 )); then
        print -u2 -- "$0: no such module: $pmodule"
        result=1
        continue
      fi

      # Grab the full path to this module
      pmodule_location=${locations[-1]}

      # Add functions to $fpath.
      fpath=(${pmodule_location}/functions(-/FN) $fpath)

      function {
        local pfunction

        # Extended globbing is needed for listing autoloadable function directories.
        setopt LOCAL_OPTIONS EXTENDED_GLOB

        # Load Prezto functions.
        for pfunction in ${pmodule_location}/functions/$~pfunction_glob; do
          autoload -Uz "$pfunction"
        done
      }

      zstyle ":prezto:module:$pmodule" loading 'yes'
      local module_result=0
      if [[ -s "${pmodule_location}/init.zsh" ]]; then
        source "${pmodule_location}/init.zsh"
        module_result=$?
      elif [[ -s "${pmodule_location}/${pmodule}.plugin.zsh" ]]; then
        source "${pmodule_location}/${pmodule}.plugin.zsh"
        module_result=$?
      fi
      zstyle -d ":prezto:module:$pmodule" loading

      if (( module_result == 0 )); then
        zstyle ":prezto:module:$pmodule" loaded 'yes'
      else
        # Remove the $fpath entry.
        fpath[(r)${(b)pmodule_location}/functions]=()

        function {
          local pfunction

          # Extended globbing is needed for listing autoloadable function
          # directories.
          setopt LOCAL_OPTIONS EXTENDED_GLOB

          # Unload Prezto functions.
          for pfunction in ${pmodule_location}/functions/$~pfunction_glob; do
            unfunction "$pfunction"
          done
        }

        zstyle ":prezto:module:$pmodule" loaded 'no'
        result=1
      fi
    fi
  done
  return $result
}

#
# Prezto Initialization
#

# This finds the directory prezto is installed to so plugin managers don't need
# to rely on dirty hacks to force prezto into a directory. Additionally, it
# needs to be done here because inside the pmodload function ${0:h} evaluates to
# the current directory of the shell rather than the prezto dir.
ZPREZTODIR=${0:A:h}

# Source the Prezto configuration file.
if [[ -s "${ZDOTDIR:-$HOME}/.zpreztorc" ]]; then
  source "${ZDOTDIR:-$HOME}/.zpreztorc"
fi

# Disable color and theme in dumb terminals.
if [[ $TERM == dumb ]]; then
  zstyle ':prezto:*:*' color 'no'
  zstyle ':prezto:module:prompt' theme 'off'
fi

# Load Zsh modules.
zstyle -a ':prezto:load' zmodule 'zmodules'
for zmodule ("$zmodules[@]") zmodload "zsh/${(z)zmodule}"
unset zmodule{s,}

# Load more specific 'run-help' function from $fpath.
(( $+aliases[run-help] )) && unalias run-help && autoload -Uz run-help

# Autoload Zsh functions.
zstyle -a ':prezto:load' zfunction 'zfunctions'
for zfunction ("$zfunctions[@]") autoload -Uz "$zfunction"
unset zfunction{s,}

# Load Prezto modules.
function {
  local -a pmodules
  zstyle -a ':prezto:load' pmodule 'pmodules'
  pmodload "$pmodules[@]"
}
