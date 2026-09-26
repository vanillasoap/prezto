from support import ZSH, ShellTestCase


class FasdTests(ShellTestCase):
    def setUp(self):
        super().setUp()
        self.env.update(XDG_CONFIG_HOME=str(self.config), _FASD_TRACK_PWD="0",
                        _FASD_ONLY_VCS="0")
        config = self.config / "fasd"
        config.mkdir()
        (config / "config").write_text("# Isolated configuration\n")
        self.folder = self.root / "example directory"
        self.folder.mkdir()

    def load(self, script=""):
        return self.command([ZSH, "-d", "-f", "-i", "-c", '''
pmodload() { :; }
source "$PREZTO_TEST_REPO/modules/fasd/init.zsh" || exit
''' + script], check=False)

    def test_first_add_survives_a_missing_database_and_parent(self):
        database = self.root / "new directory" / "database"
        self.env["_FASD_DATA"] = str(database)
        self.success(self.load('fasd --add "$PWD/example directory"'))
        self.assertIn(str(self.folder) + "|1|", database.read_text())
        self.assertEqual(database.stat().st_mode & 0o777, 0o600)

    def test_default_database_records_first_add(self):
        self.success(self.load('fasd --add "$PWD/example directory"'))
        database = self.root / "cache" / "fasd"
        self.assertIn(str(self.folder) + "|1|", database.read_text())

    def test_existing_database_is_preserved(self):
        database = self.root / "database"
        database.write_text(str(self.folder) + "|4|1000000000\n")
        self.env["_FASD_DATA"] = str(database)
        self.success(self.load())
        self.assertEqual(database.read_text(), str(self.folder) + "|4|1000000000\n")

    def test_readonly_mode_does_not_create_database(self):
        database = self.root / "readonly" / "database"
        self.env.update(_FASD_DATA=str(database), _FASD_RO="1")
        self.success(self.load())
        self.assertFalse(database.parent.exists())

    def test_external_installation_keeps_ownership_of_its_database(self):
        database = self.root / "external" / "database"
        self.env["_FASD_DATA"] = str(database)
        self.stub("fasd", "printf '# External initialization\\n'")
        self.success(self.load())
        self.assertFalse(database.parent.exists())
