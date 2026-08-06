#!/usr/bin/env bash
# Clones the ahit-corpus data repository if it isn't already present.
#
# vahiy-engine itself never depends on git or on this script at runtime — it
# only reads plain files under AHIT_CORPUS_ROOT (see src/vahiy_engine/config.py
# and src/vahiy_engine/sources/ahit/client.py). This script is purely a
# convenience for populating that directory in development, Docker, CI, and
# Codespaces. Production environments that already have a checkout can skip
# it entirely and just set AHIT_CORPUS_ROOT to point at it.
#
# Configuration (all optional, matching config.py's own env var names):
#   AHIT_CORPUS_ROOT      Where to clone/find the corpus.
#                          Default: <repo root>/external/ahit-corpus
#   AHIT_CORPUS_REPO_URL  Git URL to clone.
#                          Default: https://github.com/a234sty/ahit-corpus.git
#   AHIT_CORPUS_REF       Branch or tag to check out. Default: repo's default branch.
#
# Safe to run repeatedly: if the target directory already exists and is
# non-empty, this script does nothing (no re-clone, no network access).

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(dirname "$SCRIPT_DIR")"

REPO_URL="${AHIT_CORPUS_REPO_URL:-https://github.com/a234sty/ahit-corpus.git}"
TARGET_DIR="${AHIT_CORPUS_ROOT:-$REPO_ROOT/external/ahit-corpus}"
REF="${AHIT_CORPUS_REF:-}"

if [ -d "$TARGET_DIR" ] && [ -n "$(ls -A "$TARGET_DIR" 2>/dev/null)" ]; then
  echo "ahit-corpus already present at $TARGET_DIR — skipping clone."
  exit 0
fi

echo "Cloning ahit-corpus into $TARGET_DIR ..."
mkdir -p "$(dirname "$TARGET_DIR")"

if [ -n "$REF" ]; then
  git clone --depth 1 --branch "$REF" "$REPO_URL" "$TARGET_DIR"
else
  git clone --depth 1 "$REPO_URL" "$TARGET_DIR"
fi

echo "Done. AHIT_CORPUS_ROOT=$TARGET_DIR"
