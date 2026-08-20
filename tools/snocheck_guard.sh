#!/usr/bin/env bash
# snocheck_guard.sh -- refuse to hand a v2/v2p certificate to the frozen
# verified checker.
#
# WHY THIS EXISTS
#   The frozen snocheck reads the legacy (v1) container only. v1 has no magic:
#   its first four bytes are a u32 step count (docs/certificate-format-v2.md
#   sec.2). A v2/v2p file starts with the ASCII magic "SNOCERT2", so snocheck
#   reads "SNOC" as a step count of 0x434F4E53 = 1,129,270,867 and then tries
#   to walk a 4 + 12*step_count = 13.5 GB step table. That is the hazard
#   flagged in evidence/v3/prefixcert/report.md; it wedges the machine rather
#   than reporting an error.
#
#   snocheck itself is FROZEN and is never modified. This wrapper sits in
#   front of it.
#
# WHAT IT CHECKS, before exec'ing snocheck
#   1. magic     -- any argument that is a regular file whose first 8 bytes are
#                   "SNOCERT2" is refused. The file is identified as v2 or v2p
#                   from its format_version field so the message can say which.
#   2. layout    -- for a file that is not v2/v2p, the v1 invariant
#                   first_payload_offset == 4 + 12*step_count must hold, and the
#                   implied table must fit inside the file. This catches a
#                   truncated, empty or non-certificate file before snocheck
#                   attempts a huge read. Disable with --no-layout-check.
#   A file argument that fails either check aborts the whole invocation; no
#   partial run, no snocheck process started.
#
# USAGE
#   tools/snocheck_guard.sh -v path/to/proof.bin
#   tools/snocheck_guard.sh -v +RTS -N10 -RTS path/to/proof.bin
#   SNOCHECK=/path/to/snocheck tools/snocheck_guard.sh -v proof.bin
#   tools/snocheck_guard.sh --snocheck /path/to/snocheck -v proof.bin
#
#   Every argument other than --snocheck/--no-layout-check is passed through to
#   snocheck unchanged and in order, so +RTS blocks work exactly as before.
#
# EXIT CODES
#   0    snocheck ran; this is snocheck's own exit code
#   2    refused: a v2/v2p certificate was passed
#   3    refused: a file argument failed the v1 layout check
#   4    setup error (snocheck not found, bad usage)
#   otherwise: snocheck's own exit code
#
# A v2 or v2p certificate is checked with tools/cert_v2.py instead
# (`check` for v2, `prefix-check` for v2p). Those are UNVERIFIED; see
# docs/verified-checker-extension.md for what that costs.

set -euo pipefail

SELF_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SELF_DIR/.." && pwd)"

layout_check=1
snocheck_bin="${SNOCHECK:-}"
passthrough=()

while [ $# -gt 0 ]; do
  case "$1" in
    --snocheck)
      [ $# -ge 2 ] || { echo "snocheck_guard: --snocheck needs a path" >&2; exit 4; }
      snocheck_bin="$2"; shift 2 ;;
    --snocheck=*)
      snocheck_bin="${1#--snocheck=}"; shift ;;
    --no-layout-check)
      layout_check=0; shift ;;
    --)
      shift; passthrough+=("$@"); break ;;
    *)
      passthrough+=("$1"); shift ;;
  esac
done

# ---- locate the frozen checker -------------------------------------------
if [ -z "$snocheck_bin" ]; then
  # Prefer the most recent b3-toolchain build, then the pinned clone's
  # stack-work copy. Both are the frozen binary; neither is built here.
  for cand in \
    "$(ls -td "$REPO_ROOT"/.build/b3-toolchain/attempt-*/bin/snocheck 2>/dev/null | head -1)" \
    "$(ls -t "$REPO_ROOT"/.cache/third_party/sortnetopt/checker/snocheck/.stack-work/install/*/*/*/bin/snocheck 2>/dev/null | head -1)"
  do
    if [ -n "$cand" ] && [ -x "$cand" ]; then snocheck_bin="$cand"; break; fi
  done
fi

if [ -z "$snocheck_bin" ] || [ ! -x "$snocheck_bin" ]; then
  echo "snocheck_guard: cannot find the frozen snocheck binary." >&2
  echo "  set SNOCHECK=/path/to/snocheck or pass --snocheck /path/to/snocheck" >&2
  exit 4
fi

# ---- inspect every file argument -----------------------------------------
inspect() {
  # prints one of: OK | V2 <version> | LAYOUT <reason>
  python3 - "$1" <<'PY'
import sys, os
path = sys.argv[1]
size = os.path.getsize(path)
with open(path, "rb") as f:
    head = f.read(16)
if head[0:8] == b"SNOCERT2":
    ver = int.from_bytes(head[8:12], "little") if len(head) >= 12 else -1
    print("V2 %d" % ver)
    raise SystemExit(0)
if size < 16:
    print("LAYOUT file is %d bytes, too small to be a v1 certificate" % size)
    raise SystemExit(0)
step_count = int.from_bytes(head[0:4], "little")
if step_count < 1:
    print("LAYOUT step_count is 0")
    raise SystemExit(0)
table_end = 4 + 12 * step_count
if table_end > size:
    print("LAYOUT step_count %d implies a %d-byte step table but the file is "
          "only %d bytes" % (step_count, table_end, size))
    raise SystemExit(0)
first_off = int.from_bytes(head[4:12], "little")
if first_off != table_end:
    print("LAYOUT first payload offset is %d, expected 4 + 12*%d = %d"
          % (first_off, step_count, table_end))
    raise SystemExit(0)
print("OK")
PY
}

for arg in ${passthrough+"${passthrough[@]}"}; do
  # Only look at things that are actually regular files; flags and +RTS
  # tokens are passed through untouched.
  [ -f "$arg" ] || continue
  verdict="$(inspect "$arg")"
  case "$verdict" in
    "V2 2")
      echo "snocheck_guard: REFUSED -- $arg is a v2 wide-container certificate." >&2
      echo "  The frozen snocheck cannot read v2; it would misread the ASCII" >&2
      echo "  magic as a step count of 1,129,270,867 and attempt a ~13 GB read." >&2
      echo "  Check it with: python3 tools/cert_v2.py check $arg" >&2
      exit 2 ;;
    "V2 3")
      echo "snocheck_guard: REFUSED -- $arg is a v2p PREFIX-ROOTED certificate." >&2
      echo "  It proves a prefix bound, not a full-problem bound, and the frozen" >&2
      echo "  snocheck cannot read it (it would attempt a ~13 GB read)." >&2
      echo "  Check it with: python3 tools/cert_v2.py prefix-check $arg" >&2
      exit 2 ;;
    "V2 "*)
      echo "snocheck_guard: REFUSED -- $arg carries the SNOCERT2 magic with an" >&2
      echo "  unrecognised format_version (${verdict#V2 }). Not a v1 certificate." >&2
      exit 2 ;;
    LAYOUT*)
      if [ "$layout_check" -eq 1 ]; then
        echo "snocheck_guard: REFUSED -- $arg does not look like a v1 certificate:" >&2
        echo "  ${verdict#LAYOUT }" >&2
        echo "  Pass --no-layout-check to override." >&2
        exit 3
      fi ;;
    OK) ;;
    *)
      echo "snocheck_guard: internal error inspecting $arg: $verdict" >&2
      exit 4 ;;
  esac
done

exec "$snocheck_bin" ${passthrough+"${passthrough[@]}"}
