from support import ShellTestCase


LOAD = '''
fpath=("$PREZTO_TEST_REPO/modules/prompt/functions" $fpath)
autoload -Uz async
async
'''


class AsyncTests(ShellTestCase):
    def test_worker_results_survive_a_read_split_after_delimiter(self):
        result = self.zsh(LOAD + r'''
local null=$'\0'
local first=${null}"jobA 0 outA 1.0 ''"${null}
local stream=$first${null}"jobB 0 outB 1.0 ''"${null}
local -a chunks names
chunks=("${stream[1,${#first}+2]}" "${stream[${#first}+3,-1]}")
zpty() {
  (( ${#chunks} )) || return 1
  data=$chunks[1]
  shift chunks
}
callback() { names+=("$1"); }
async_process_results test callback direct
print -r -- "${(j: :)names}"
''')
        self.assertEqual(self.success(result).strip(), "jobA jobB")

    def test_empty_worker_read_reports_failure_without_spinning(self):
        result = self.zsh(LOAD + '''
local reads=0 received=
zpty() {
  (( ++reads <= 3 )) || return 1
  data=''
}
callback() { received="$2:$6:$5"; }
async_process_results test callback trap
print -r -- "$reads:$received"
''')
        self.assertTrue(self.success(result).startswith("1:2:0:"), result.stdout)
        self.assertIn("empty read from worker test", result.stdout)

    def test_real_worker_survives_prompt_switching(self):
        result = self.zsh('''
source "$PREZTO_TEST_REPO/init.zsh"
pmodload prompt
prompt pure
prompt sorin
prompt pure
local output= attempts=0
callback() { output=$3; }
async_start_worker test
async_job test print 'worker result'
until [[ -n $output ]] || (( ++attempts > 100 )); do
  async_process_results test callback direct
  sleep 0.01
done
async_stop_worker test
print -r -- "$output"
''')
        self.assertEqual(self.success(result).strip(), "worker result")
