import os
from concurrent.futures import ThreadPoolExecutor

from support import ShellTestCase


class CompletionTests(ShellTestCase):
    def setUp(self):
        super().setUp()
        self.provider = self.root / "completions"
        self.provider.mkdir()
        self.env["PREZTO_COMPLETIONS"] = str(self.provider)

    def complete(self, command):
        self.env["PREZTO_COMPLETE_COMMAND"] = command
        return self.zsh('''
fpath=("$PREZTO_COMPLETIONS" $fpath)
source "$PREZTO_TEST_REPO/init.zsh"
pmodload completion || exit
print -r -- "${_comps[$PREZTO_COMPLETE_COMMAND]-missing}"
''')

    def test_new_completion_is_discovered_before_cache_expires(self):
        self.assertEqual(self.success(self.complete("prezto-test")), "missing\n")
        (self.provider / "_prezto_test").write_text("#compdef prezto-test\n_arguments '*:file:_files'\n")
        self.assertEqual(self.success(self.complete("prezto-test")), "_prezto_test\n")

    def test_replaced_completion_is_discovered_with_same_file_count(self):
        old = self.provider / "_old"
        old.write_text("#compdef old-command\n")
        self.assertEqual(self.success(self.complete("old-command")), "_old\n")
        old.unlink()
        (self.provider / "_new").write_text("#compdef new-command\n")
        self.assertEqual(self.success(self.complete("new-command")), "_new\n")
        self.assertEqual(self.success(self.complete("old-command")), "missing\n")

    def test_changed_registration_is_discovered(self):
        completion = self.provider / "_test"
        completion.write_text("#compdef before\n")
        self.success(self.complete("before"))
        completion.write_text("#compdef after\n")
        os.utime(completion, (completion.stat().st_atime, completion.stat().st_mtime + 2))
        self.assertEqual(self.success(self.complete("after")), "_test\n")

    def test_warm_cache_is_reused_and_compiled_without_a_login_shell(self):
        self.success(self.complete("git"))
        cache = self.root / "cache/prezto"
        dumps = [p for p in cache.glob("zcompdump-*") if p.suffix not in (".zwc", ".files", ".lock")]
        self.assertEqual(len(dumps), 1)
        dump = dumps[0]
        before = dump.stat().st_mtime_ns
        self.assertTrue(dump.with_name(dump.name + ".zwc").is_file())
        self.assertEqual(self.success(self.complete("git")), "_git\n")
        self.assertEqual(dump.stat().st_mtime_ns, before)

    def test_unicode_providers_keep_precedence_and_caller_locale(self):
        preferred = self.root / "preferred café"
        preferred.mkdir()
        (preferred / "_café").write_text("#compdef unicode-command\n")
        (self.provider / "_fallback").write_text("#compdef unicode-command\n")
        self.env["PREZTO_PREFERRED"] = str(preferred)
        result = self.zsh('''
export LC_ALL=POSIX
fpath=("$PREZTO_PREFERRED" "$PREZTO_COMPLETIONS" $fpath)
source "$PREZTO_TEST_REPO/init.zsh"
pmodload completion || exit
print -r -- "${_comps[unicode-command]}:$LC_ALL"
''')
        self.assertEqual(self.success(result), "_café:POSIX\n")

    def test_insecure_provider_is_ignored_even_with_a_warm_cache(self):
        (self.provider / "_test").write_text("#compdef private-command\n")
        self.assertEqual(self.success(self.complete("private-command")), "_test\n")
        self.provider.chmod(0o777)
        self.assertEqual(self.success(self.complete("private-command")), "missing\n")

    def test_simultaneous_shells_get_usable_completion(self):
        self.env["PREZTO_COMPLETE_COMMAND"] = "git"
        with ThreadPoolExecutor(max_workers=3) as executor:
            results = list(executor.map(lambda _: self.complete("git"), range(3)))
        for result in results:
            self.assertEqual(self.success(result), "_git\n")
        self.assertEqual(self.success(self.complete("git")), "_git\n")

    def test_unwritable_cache_does_not_disable_completion(self):
        unavailable = self.root / "not-a-directory"
        unavailable.write_text("keep")
        self.env["XDG_CACHE_HOME"] = str(unavailable)
        self.assertEqual(self.success(self.complete("git")), "_git\n")
