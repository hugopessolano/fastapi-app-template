---
name: skill-creator
description: Guidance for creating new skills in this repository.
metadata:
  scope: root
  auto_invoke: "Creating a new skill"
---

# Skill Creator

## Purpose
Provide a repeatable way to add new skills under `skills/`.

## Steps
1. Create a new folder under `skills/` using a clear, kebab-case name (example: `skills/fastapi-core/`).
2. Add `skill.md` in that folder.
3. Use YAML frontmatter at the top of `skill.md` with:
   - `name`: short skill id.
   - `description`: one-line summary.
   - `metadata.scope`: `root` for global, or a folder name for scoped skills.
   - `metadata.auto_invoke`: when this skill should be used.
4. In the body, document:
   - When to use the skill.
   - Key conventions or rules.
   - Any required commands or files.
5. After creating or updating a skill, run the sync script (see `skills/skill-sync/skill.md`).
