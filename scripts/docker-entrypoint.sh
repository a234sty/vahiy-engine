#!/usr/bin/env bash
# Best-effort corpus setup on container start, then run the given command.
#
# If AHIT_CORPUS_ROOT already points at an existing checkout (e.g. a mounted
# volume in production), setup_corpus.sh does nothing and this is instant. If
# cloning fails for any reason (no network, etc.), the app still starts —
# it works fine with only the bundled KJV sample data.

set -e

if ! /app/scripts/setup_corpus.sh; then
  echo "ahit-corpus setup skipped or failed; continuing with bundled sample data only." >&2
fi

exec "$@"
