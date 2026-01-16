from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable, List


@dataclass(frozen=True)
class SkillEntry:
    name: str
    description: str
    scopes: List[str]
    rel_path: str


ROOT_SCOPE = "root"
SKILLS_MARKER_START = "<!-- SKILLS-LIST-START -->"
SKILLS_MARKER_END = "<!-- SKILLS-LIST-END -->"


def main() -> None:
    root = Path(__file__).resolve().parents[1]
    skills = collect_skills(root)
    root_skills = [skill for skill in skills if ROOT_SCOPE in skill.scopes]
    scoped_skills = group_scoped_skills(skills)

    root_agents_path = root / "AGENTS.md"
    root_content = root_agents_path.read_text(encoding="utf-8")
    updated_root = inject_skills(
        root_content, build_rows(root_skills, scope_label="Root")
    )
    root_agents_path.write_text(updated_root, encoding="utf-8")

    setup_block = extract_section(updated_root, "## Setup commands")
    style_block = extract_section(updated_root, "## Code style")

    for scope, entries in scoped_skills.items():
        target = root / scope / "AGENTS.md"
        if not target.exists():
            target.write_text(
                build_scoped_agents(scope, setup_block, style_block), encoding="utf-8"
            )
        scoped_content = target.read_text(encoding="utf-8")
        scoped_rows = build_rows(entries, scope_label=scope)
        updated_scoped = inject_skills(scoped_content, scoped_rows)
        target.write_text(updated_scoped, encoding="utf-8")


def collect_skills(root: Path) -> List[SkillEntry]:
    skills_dir = root / "skills"
    entries: List[SkillEntry] = []
    if not skills_dir.exists():
        return entries
    for path in sorted(skills_dir.rglob("*.md")):
        frontmatter = parse_frontmatter(path)
        name = str(frontmatter.get("name") or path.parent.name)
        description = str(frontmatter.get("description") or "")
        scopes = normalize_scopes(frontmatter.get("metadata", {}).get("scope"))
        if not scopes:
            scopes = [ROOT_SCOPE]
        rel_path = path.relative_to(root).as_posix()
        entries.append(
            SkillEntry(
                name=name,
                description=description,
                scopes=scopes,
                rel_path=rel_path,
            )
        )
    return entries


def normalize_scopes(value: object) -> List[str]:
    if value is None:
        return []
    if isinstance(value, list):
        return [str(item).strip() for item in value if str(item).strip()]
    raw = str(value).strip()
    if raw.startswith("[") and raw.endswith("]"):
        inner = raw[1:-1]
        parts = [part.strip() for part in inner.split(",")]
        return [part for part in parts if part]
    return [raw]


def group_scoped_skills(skills: Iterable[SkillEntry]) -> Dict[str, List[SkillEntry]]:
    scoped: Dict[str, List[SkillEntry]] = {}
    for entry in skills:
        for scope in entry.scopes:
            if scope == ROOT_SCOPE:
                continue
            scoped.setdefault(scope, []).append(entry)
    return scoped


def build_rows(entries: Iterable[SkillEntry], scope_label: str) -> List[str]:
    rows = []
    for entry in sorted(entries, key=lambda item: item.name.lower()):
        rows.append(
            f"| [{entry.name}](./{entry.rel_path}) | {entry.description} | {scope_label} |"
        )
    return rows


def inject_skills(content: str, rows: Iterable[str]) -> str:
    if SKILLS_MARKER_START not in content or SKILLS_MARKER_END not in content:
        raise ValueError("Skills markers not found in AGENTS.md")
    before, rest = content.split(SKILLS_MARKER_START, 1)
    _, after = rest.split(SKILLS_MARKER_END, 1)
    rows_block = "\n".join(rows)
    return f"{before}{SKILLS_MARKER_START}\n{rows_block}\n{SKILLS_MARKER_END}{after}"


def extract_section(content: str, header: str) -> str:
    lines = content.splitlines()
    start_index = None
    for idx, line in enumerate(lines):
        if line.strip() == header:
            start_index = idx
            break
    if start_index is None:
        return ""
    collected = [lines[start_index]]
    for line in lines[start_index + 1 :]:
        if line.startswith("## "):
            break
        collected.append(line)
    return "\n".join(collected).strip()


def build_scoped_agents(scope: str, setup_block: str, style_block: str) -> str:
    blocks = [
        "# AGENTS.md",
        "A simple, open format for guiding coding agents on this project.",
        "",
        setup_block or "## Setup commands",
        "",
        style_block or "## Code style",
        "",
        "## Available Skills",
        "| Skill | Description | Scope |",
        "|-------|-------------|-------|",
        SKILLS_MARKER_START,
        SKILLS_MARKER_END,
        "",
        "*Note: The table is empty for now. The sync script will populate it.*",
    ]
    return "\n".join(blocks).replace("{scope}", scope).strip() + "\n"


def parse_frontmatter(path: Path) -> dict:
    text = path.read_text(encoding="utf-8-sig")
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        return {}
    data: dict = {}
    current_key = None
    for line in lines[1:]:
        if line.strip() == "---":
            break
        if not line.strip():
            continue
        if line.startswith("  ") and current_key:
            key, value = split_key_value(line.strip())
            if key:
                data.setdefault(current_key, {})[key] = parse_value(value)
            continue
        key, value = split_key_value(line)
        if not key:
            continue
        if value == "":
            current_key = key
            data[key] = {}
            continue
        data[key] = parse_value(value)
        current_key = None
    return data


def split_key_value(line: str) -> tuple[str, str]:
    if ":" not in line:
        return "", ""
    key, value = line.split(":", 1)
    return key.strip(), value.strip()


def parse_value(value: str) -> object:
    if not value:
        return ""
    if value.startswith('"') and value.endswith('"'):
        return value[1:-1]
    if value.startswith("'") and value.endswith("'"):
        return value[1:-1]
    if value.startswith("[") and value.endswith("]"):
        inner = value[1:-1]
        parts = [part.strip() for part in inner.split(",")]
        return [part for part in parts if part]
    return value


if __name__ == "__main__":
    main()
