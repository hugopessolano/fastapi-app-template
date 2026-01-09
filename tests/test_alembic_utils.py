import os
import unittest


class TestAlembicUtils(unittest.TestCase):
    def setUp(self) -> None:
        self._original_database_url = os.environ.get("DATABASE_URL")

    def tearDown(self) -> None:
        if self._original_database_url is None:
            os.environ.pop("DATABASE_URL", None)
        else:
            os.environ["DATABASE_URL"] = self._original_database_url

    def test_get_migration_database_url_uses_env(self) -> None:
        os.environ["DATABASE_URL"] = "sqlite:///./test.db"
        from app.database.alembic_utils import get_migration_database_url

        self.assertEqual(get_migration_database_url(), "sqlite:///./test.db")
