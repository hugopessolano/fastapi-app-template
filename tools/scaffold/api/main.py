from pathlib import Path

from tools.scaffold.api.app import create_api_app


def default_root() -> Path:
    return Path(__file__).resolve().parents[1]


app = create_api_app(default_root())
