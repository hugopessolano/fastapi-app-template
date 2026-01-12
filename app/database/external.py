from typing import Generator

from app.database.external_registry import external_db_dependency


def get_external_db(name: str = "default") -> Generator:
    return external_db_dependency(name)()
