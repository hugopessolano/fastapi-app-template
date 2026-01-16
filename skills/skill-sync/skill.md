---
name: skill-sync
description: Sync skills into AGENTS.md files after changes.
metadata:
  scope: root
  auto_invoke: "After creating or modifying a skill"
---

# Skill Sync

## Purpose
Keep `AGENTS.md` files updated with the skills registry.

## Steps
1. Run the sync script after adding or editing any skill:
   - `python scripts/sync_agents.py`
2. Verify:
   - Root `AGENTS.md` includes global skills under the skills table.
   - Any scoped folders have their own `AGENTS.md` with scoped skills.
3. Commit the updated `AGENTS.md` files together with skill changes.
