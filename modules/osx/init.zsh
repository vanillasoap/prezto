#
# Defines macOS aliases and functions.
#
# Authors:
#   Sorin Ionescu <sorin.ionescu@gmail.com>
#

# Load dependencies.
pmodload 'helper'

# Return if requirements are not found.
if ! is-darwin; then
  return 1
fi

#
# Aliases
#

# Changes directory to the current Finder directory.
alias cdf='cd "$(pfd)"'

# Pushes directory to the current Finder directory.
alias pushdf='pushd "$(pfd)"'

# Finder reloads its visibility preference when restarted.
alias showfiles='command defaults write com.apple.finder AppleShowAllFiles -bool true && command killall Finder'
alias hidefiles='command defaults write com.apple.finder AppleShowAllFiles -bool false && command killall Finder'
