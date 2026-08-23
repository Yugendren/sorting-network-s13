#!/usr/bin/env bash
# Build (i.e. re-check) Ambient_Collapse.thy -- the mechanized collapse theorem.
#
# This is INDEPENDENT of build.sh.  It touches no frozen theory, needs no
# pinned clone, no GHC, and no Sorting_Networks heap: Ambient_Collapse imports
# Main only.  A cold run needs an Isabelle2020 with a prebuilt HOL heap
# (the macOS/Linux bundles ship one); the session itself builds in ~2 s.
#
#   ISABELLE=/path/to/isabelle tools/verified/build_ambient.sh
#
# Exit 0 means: every proof in the theory was checked, with no sorry and no
# oops (Isabelle would print "Theory ... contains sorry" and this script
# greps for it as a belt-and-braces check).

set -euo pipefail
SELF_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ISABELLE="${ISABELLE:-isabelle}"

if grep -nE '\b(sorry|oops|axiomatization|quick_and_dirty)\b' "$SELF_DIR/Ambient_Collapse.thy" \
     | grep -v 'No sorry'; then
  echo "build_ambient.sh: FORBIDDEN construct found in Ambient_Collapse.thy" >&2
  exit 1
fi

"$ISABELLE" build -d "$SELF_DIR/ambient" Ambient_Collapse
echo "build_ambient.sh: Ambient_Collapse verified (no sorry, no oops)."
