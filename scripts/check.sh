#!/usr/bin/env bash
# This repo's own gate: it must pass from this repo's root, with no sibling repo cloned except
# lib_bespok3d. Eight tag decoders live side by side here, so most checks are per decoder. Exits
# non-zero on any failure.
set -uo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
# The shared gate helpers and the detectors that enforce a workspace-wide rule live in one place.
# See lib_bespok3d/tooling/README.md. This is the only line that knows where they are.
B3D_TOOLING="${B3D_TOOLING:-$REPO_ROOT/lib_bespok3d/tooling}"
# shellcheck source=/dev/null
. "$B3D_TOOLING/gate-lib.sh"

cd "$REPO_ROOT" || exit 1

DECODERS=(rfid-generic-ndef rfid-opentag rfid-elegoo rfid-bambu rfid-creality rfid-tigertag
          rfid-openprinttag rfid-anycubic)
EXTRAS="files/klipper/klippy/extras"
OPENPRINTTAG_EX="rfid-openprinttag/$EXTRAS/rfid-tags/openprinttag"

echo ""
echo "all-the-tags gate"

b3d_python_tools

# Each decoder runs pytest in its own process: every decoder ships a tests/conftest.py that inserts
# its own extras dir on sys.path, and pytest's prepend import mode dedupes same-named conftests, so
# a single combined run would only honor the first decoder's path insert.
for decoder in "${DECODERS[@]}"; do
    run_check "pytest ($decoder)"  pytest_in_dir "$REPO_ROOT/$decoder" tests
done

# One ruff pass from the repo root: the shared config's per-file-ignores match on paths relative to
# the working directory, and every decoder's tree is relative to here.
run_check "ruff"    ruff_in_dir "$REPO_ROOT" \
    rfid-generic-ndef/files rfid-generic-ndef/tests rfid-opentag/files rfid-opentag/tests \
    rfid-elegoo/files rfid-elegoo/tests rfid-bambu/files rfid-bambu/tests \
    rfid-creality/files rfid-creality/tests rfid-tigertag/files rfid-tigertag/tests \
    rfid-openprinttag/files rfid-openprinttag/tests rfid-anycubic/files rfid-anycubic/tests

run_check "mypy"    mypy_in_dir "$REPO_ROOT" \
    "rfid-generic-ndef/$EXTRAS/rfid-tags/generic-ndef/generic_ndef_fields.py" \
    "rfid-opentag/$EXTRAS/rfid-tags/opentag/opentag_fields.py" \
    "rfid-elegoo/$EXTRAS/rfid-tags/elegoo/elegoo_fields.py" \
    "rfid-bambu/$EXTRAS/rfid-tags/bambu/bambu_keys.py" \
    "rfid-bambu/$EXTRAS/rfid-tags/bambu/bambu_fields.py" \
    "rfid-creality/$EXTRAS/rfid-tags/creality/aes_min.py" \
    "rfid-creality/$EXTRAS/rfid-tags/creality/creality_keys.py" \
    "rfid-creality/$EXTRAS/rfid-tags/creality/creality_fields.py" \
    "rfid-tigertag/$EXTRAS/rfid-tags/tigertag/tigertag_fields.py" \
    "rfid-anycubic/$EXTRAS/rfid-tags/anycubic/anycubic_fields.py"

# openprinttag_fields.py relatively imports its cbor_min sibling (from . import cbor_min), which
# resolves at runtime as a flat klippy.extras package member; mypy needs the package parent (the
# rfid-tags dir) on MYPYPATH plus explicit package bases to see it the same way the tests' conftest
# does, so it runs as its own package-aware check.
export MYPYPATH="$REPO_ROOT/rfid-openprinttag/$EXTRAS/rfid-tags"
run_check "mypy (openprinttag)"  mypy_in_dir "$REPO_ROOT" --explicit-package-bases \
    --namespace-packages "$OPENPRINTTAG_EX/cbor_min.py" "$OPENPRINTTAG_EX/openprinttag_fields.py"
unset MYPYPATH

workflow_pinning_check "$REPO_ROOT"
em_dash_check "$REPO_ROOT"
shellcheck_repo "$REPO_ROOT"

gate_summary || exit 1
