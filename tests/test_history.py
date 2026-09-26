from support import ShellTestCase


class HistoryTests(ShellTestCase):
    def test_shared_history_clears_conflicting_write_modes(self):
        output = self.success(self.zsh('''
setopt INC_APPEND_HISTORY INC_APPEND_HISTORY_TIME
source "$PREZTO_TEST_REPO/modules/history/init.zsh"
print -r -- $options[sharehistory] $options[incappendhistory] $options[incappendhistorytime]
'''))
        self.assertEqual(output.strip(), "on off off")

    def test_configured_storage_and_limits_are_preserved(self):
        output = self.success(self.zsh('''
zstyle ':prezto:module:history' histfile "$ZDOTDIR/my history"
zstyle ':prezto:module:history' histsize 12000
zstyle ':prezto:module:history' savehist 10000
source "$PREZTO_TEST_REPO/modules/history/init.zsh"
print -r -- "$HISTFILE" "$HISTSIZE" "$SAVEHIST"
'''))
        self.assertEqual(output.strip(), str(self.config / "my history") + " 12000 10000")
