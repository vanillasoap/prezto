import io
import shlex
import shutil
import tarfile

from support import ShellTestCase


LOAD = '''
fpath=("$PREZTO_TEST_REPO/modules/archive/functions" $fpath)
autoload -Uz archive lsarchive unarchive
'''


class ArchiveTests(ShellTestCase):
    def tar_fixture(self, name):
        with tarfile.open(self.root / name, "w") as archive:
            member = tarfile.TarInfo("marker.txt")
            member.size = 7
            archive.addfile(member, io.BytesIO(b"payload"))

    def test_failed_deb_extraction_preserves_input_and_working_directory(self):
        archive = self.root / "broken.deb"
        archive.write_text("archive payload")
        self.stub("ar", "touch control.tar.gz data.tar.gz debian-binary")
        self.stub("tar", "exit 2")
        result = self.zsh(LOAD + '''
unarchive -r broken.deb
local result=$?
print -r -- "$PWD"
return $result
''')
        self.assertTrue(archive.exists(), "failed extraction removed its input")
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(result.stdout.strip(), str(self.root))

    def test_listing_lzma_fallback_does_not_extract(self):
        self.tar_fixture("sample.tlz")
        directory = self.root / "listing"
        directory.mkdir()
        tar = shlex.quote(shutil.which("tar"))
        self.stub("tar", f'[ "$1" = --lzma ] && exit 1\nexec {tar} "$@"')
        self.stub("lzcat", 'exec cat "$@"')
        result = self.zsh(LOAD + "lsarchive ../sample.tlz", cwd=directory)
        self.success(result)
        self.assertEqual(list(directory.iterdir()), [], "listing wrote archive members")
        self.assertIn("marker.txt", result.stdout)

    def test_listing_reports_invalid_and_unsupported_inputs(self):
        (self.root / "unknown.format").write_text("payload")
        for name in ("missing.tar", "unknown.format"):
            with self.subTest(name=name):
                result = self.zsh(LOAD + f"lsarchive {name}")
                self.assertNotEqual(result.returncode, 0)

    def test_lzma_tar_suffixes_list_and_extract_the_tar_payload(self):
        tar = shlex.quote(shutil.which("tar"))
        self.stub("tar", f'[ "$1" = --lzma ] && exit 1\nexec {tar} "$@"')
        self.stub("lzcat", 'exec cat "$@"')
        for suffix in ("tar.lzma", "tar.zma", "tlz"):
            with self.subTest(suffix=suffix):
                self.tar_fixture("sample." + suffix)
                directory = self.root / suffix
                directory.mkdir()
                self.assertIn("marker.txt", self.success(self.zsh(
                    LOAD + "lsarchive ../sample." + suffix, cwd=directory)))
                self.assertEqual(list(directory.iterdir()), [])
                self.success(self.zsh(LOAD + "unarchive ../sample." + suffix, cwd=directory))
                self.assertEqual((directory / "marker.txt").read_text(), "payload")

    def test_unix_compress_suffix_is_recognized(self):
        (self.root / "sample.Z").write_text("compressed payload")
        self.stub("uncompress", 'printf "%s\\n" "$@" > uncompress-arguments')
        self.success(self.zsh(LOAD + "unarchive sample.Z"))
        self.assertEqual((self.root / "uncompress-arguments").read_text(), "sample.Z\n")

    def test_archive_preserves_operand_boundaries_and_output_directory(self):
        (self.root / "dir with space").mkdir()
        (self.root / "dir with space/data").write_text("payload")
        (self.root / "output").mkdir()
        result = self.zsh(LOAD + "archive output/result.tar 'dir with space'")
        self.success(result)
        with tarfile.open(self.root / "output/result.tar") as archive:
            self.assertIn("dir with space/data", archive.getnames())

    def test_failed_decompressor_preserves_archive_even_if_tar_succeeds(self):
        self.tar_fixture("sample.tlz")
        tar = shlex.quote(shutil.which("tar"))
        self.stub("tar", f'[ "$1" = --lzma ] && exit 1\nexec {tar} "$@"')
        self.stub("lzcat", 'cat "$@"\nexit 2')
        result = self.zsh(LOAD + "unarchive -r sample.tlz")
        self.assertNotEqual(result.returncode, 0)
        self.assertTrue((self.root / "sample.tlz").exists())

    def test_successful_extraction_removes_only_requested_archive(self):
        self.tar_fixture("sample.tar")
        result = self.zsh(LOAD + "unarchive -r sample.tar")
        self.success(result)
        self.assertEqual((self.root / "marker.txt").read_text(), "payload")
        self.assertFalse((self.root / "sample.tar").exists())
