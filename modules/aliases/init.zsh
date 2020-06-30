#
# Aliases
#


# Misc
alias crop='python3 /Volumes/Raid/Dropbox/BAS/2020/Moving\ through/Webpage/Content/Chosen/crop.py'

# Group images based on similarity
alias groupimg='python3 /Users/so/Git/groupImg/cli/groupimg.py'

# Image organizer
alias imgo='python3 /Users/so/Git/imgo/imgo.py'

# ls on steroids
alias ls='exa'

# macOS
alias refreshbrew='brew outdated4 while read cask; do brew upgrade $cask; done' # refresh brew by upgrading all outdated casks
alias apps='mdfind "kMDItemAppStoreHasReceipt=1"' # alias to show all Mac App store apps
alias today='calendar -A 0 -f /usr/share/calendar/calendar.mark4 sort'
alias oo='open .' # open current directory in OS X Finder
alias ql='qlmanage -p 2>/dev/null' # OS X Quick Look

# Volume
alias vol0='sudo osascript -e "set Volume 0"'
alias vol1='sudo osascript -e "set Volume 1"'
alias vol2='sudo osascript -e "set Volume 2"'
alias vol3='sudo osascript -e "set Volume 3"'
alias vol4='sudo osascript -e "set Volume 4"'
alias vol6='sudo osascript -e "set Volume 6"'
alias vol8='sudo osascript -e "set Volume 8"'

# homebrew 
alias brews='brew list -1'
alias bubo='brew update && brew outdated'
alias bubc='brew upgrade && brew cleanup'
alias bubu='bubo && bubc'

# Apps
alias nf='neofetch'
alias lønsj='lunchy --restart'

# Network
alias myip='curl ifconfig.co'						# myip:				Public facing IP Address
alias netCons='lsof -i'								# netCons:			Show all open TCP/IP sockets
alias flushDNS='dscacheutil -flushcache'			# flushDNS:			Flush out the DNS Cache
alias lsock='sudo /usr/sbin/lsof -i -P'				# lsock:			Display open sockets
alias lsockU='sudo /usr/sbin/lsof -nP4 grep UDP'	# lsockU:			Display only open UDP sockets
alias lsockT='sudo /usr/sbin/lsof -nP4 grep TCP'	# lsockT:			Display only open TCP sockets
alias ipInfo0='ipconfig getpacket en0'				# ipInfo0:			Get info on connections for en0
alias ipInfo1='ipconfig getpacket en1'				# ipInfo1:			Get info on connections for en1
alias openPorts='sudo lsof -i4 grep LISTEN'			# openPorts:		All listening connections
alias showBlocked='sudo ipfw list'					# showBlocked:		All ipfw rules inc/ blocked IPs

# ii:  display useful host related informaton
ii() {
    echo -e "\nYou are logged on $fg[red]$HOST"
    echo -e "\nAdditionnal information:$NC " ; uname -a
    echo -e "\n${fg[red]}${bg[black]}Users logged on:$NC " ; w -h
    echo -e "\n$FG[red]Current date :$NC " ; date
    echo -e "\n$fg[red]Machine stats :$NC " ; uptime
    echo -e "\n$fg[red]Current network location :$NC " ; scselect
    echo -e "\n$fg[red]Public facing IP Address :$NC " ; myip
    #echo -e "\n$fg[red]DNS Configuration:$NC " ; scutil --dns
    echo
}

# Extract:  Extract most know archives with one command
extract () {
    if [ -f $1 ] ; then
      case $1 in
        *.tar.bz2)   tar xjf $1     ;;
        *.tar.gz)    tar xzf $1     ;;
        *.bz2)       bunzip2 $1     ;;
        *.rar)       unrar e $1     ;;
        *.gz)        gunzip $1      ;;
        *.tar)       tar xf $1      ;;
        *.tbz2)      tar xjf $1     ;;
        *.tgz)       tar xzf $1     ;;
        *.zip)       unzip $1       ;;
        *.Z)         uncompress $1  ;;
        *.7z)        7z x $1        ;;
        *)     echo "'$1' cannot be extracted via extract()" ;;
         esac
     else
         echo "'$1' is not a valid file"
     fi
}

# Searching
alias qfind="find . -name "                 # qfind:    Quickly search for file
ff () { /usr/bin/find . -name "$@" ; }      # ff:       Find file under the current directory
ffs () { /usr/bin/find . -name "$@"'*' ; }  # ffs:      Find file whose name starts with a given string
ffe () { /usr/bin/find . -name '*'"$@" ; }  # ffe:      Find file whose name ends with a given string

#   spotlight: Search for a file using MacOS Spotlight's metadata
#   -----------------------------------------------------------
spotlight () { mdfind "kMDItemDisplayName == '$@'wc"; }
