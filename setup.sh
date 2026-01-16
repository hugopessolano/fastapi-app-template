#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SKILLS_DIR="${ROOT_DIR}/skills"

mkdir -p "${ROOT_DIR}/.cursor" "${ROOT_DIR}/.claude"
ln -sfn "${SKILLS_DIR}" "${ROOT_DIR}/.cursor/rules"
ln -sfn "${SKILLS_DIR}" "${ROOT_DIR}/.claude/skills"

echo "Symlinks created:"
echo "  .cursor/rules -> ${SKILLS_DIR}"
echo "  .claude/skills -> ${SKILLS_DIR}"
