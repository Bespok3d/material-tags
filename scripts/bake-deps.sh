#!/bin/sh
# Bake each plugin's Python dependencies into its files/ so the printer never runs pip (ADR-0036).
# Two modes, chosen by which requirements file a plugin ships:
#   requirements.txt          -> wheels for the plugin's OWN service venv. The daemon installs them
#                                offline (pip install --no-index --find-links files/wheels) into a
#                                per-plugin venv. We fetch the full closure as wheels into files/wheels.
#   klipper_requirements.txt  -> unpacked packages for a Klipper/Moonraker EXTRA that must import the
#                                lib in THAT (system) interpreter. The daemon symlinks each top-level
#                                package into the system site-packages. We unzip the wheels into
#                                files/site-packages (a wheel is a zip; unzipping gives a flat
#                                importable tree).
#
# We fetch wheels for the PRINTER's platform (Snapmaker U1: aarch64, glibc/manylinux2014, CPython
# 3.11), NOT the build runner's, so a compiled dependency is correct on the device even when this
# runs on an x86 CI runner. pip resolves the full closure and picks the aarch64 wheel for compiled
# packages and the universal py3-none-any wheel for pure-Python ones.
#
# --only-binary=:all: makes the bake FAIL LOUDLY if any package in the closure has no compatible
# prebuilt wheel (sdist-only, or no aarch64 build): that is the signal to publish an arm64 wheel for
# that dependency (built once on an arm64 runner) rather than ship a broken .b3 to the printer.
#
# Requires: python3 with pip.
set -e

# The printer's interpreter. Keep in sync with the U1 runtime (jinni paths.json / the daemon venv).
TARGET_PLATFORM="manylinux2014_aarch64"
TARGET_PYTHON="3.11"
TARGET_IMPL="cp"

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO_DIR="$(dirname "$SCRIPT_DIR")"

# Download the closure of a requirements file as wheels for the printer's platform. The three --abi
# values let one pass collect both compiled (cp311) and universal (none / abi3) wheels.
download_wheels() {  # requirements_file dest_dir
  python3 -m pip download -r "$1" -d "$2" \
    --only-binary=:all: \
    --platform "$TARGET_PLATFORM" \
    --python-version "$TARGET_PYTHON" \
    --implementation "$TARGET_IMPL" \
    --abi cp311 --abi abi3 --abi none
}

for dir in "$REPO_DIR"/*/; do
  [ -f "${dir}manifest.json" ] || continue
  if [ -f "${dir}requirements.txt" ]; then
    mkdir -p "${dir}files/wheels"
    download_wheels "${dir}requirements.txt" "${dir}files/wheels"
    echo "Baked wheels for ${dir}"
  fi
  if [ -f "${dir}klipper_requirements.txt" ]; then
    mkdir -p "${dir}files/site-packages"
    wheel_dir="$(mktemp -d)"
    download_wheels "${dir}klipper_requirements.txt" "$wheel_dir"
    for wheel in "$wheel_dir"/*.whl; do
      python3 -m zipfile -e "$wheel" "${dir}files/site-packages"
    done
    rm -rf "$wheel_dir"
    echo "Baked site-packages for ${dir}"
  fi
done
