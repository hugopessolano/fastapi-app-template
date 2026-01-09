import json
import hashlib
from pathlib import Path


def manifest_path(root: Path) -> Path:
    return root / ".scaffold" / "manifest.json"


def load_manifest(root: Path) -> dict:
    path = manifest_path(root)
    if not path.exists():
        return {"version": 1, "resources": {}}
    return json.loads(path.read_text(encoding="utf-8"))


def save_manifest(root: Path, manifest: dict) -> None:
    path = manifest_path(root)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")


def hash_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def hash_file(path: Path) -> str:
    return hash_text(path.read_text(encoding="utf-8"))
