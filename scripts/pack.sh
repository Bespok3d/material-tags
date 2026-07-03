#!/bin/sh
# Pack every plugin in this co-repo into a .b3 under dist/. Each plugin lives in its own
# <plugin-id>/ dir (manifest.json + files/ + optional doc/). A slim port of the monorepo's
# pack-plugins.sh pack step: per-file sha256 + mode go into the manifest files[] array, then
# manifest + files/ + doc/ are zipped. Always-repack (no lockfile/auto-bump); bump a plugin's
# manifest.json version manually to cut a new release.
#
# Requires: zip, jq, and shasum (macOS) or sha256sum (Linux).
set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO_DIR="$(dirname "$SCRIPT_DIR")"
DIST_DIR="$REPO_DIR/dist"

for cmd in zip jq; do
  command -v "$cmd" >/dev/null 2>&1 || { echo "ERROR: '$cmd' is required." >&2; exit 1; }
done
command -v shasum >/dev/null 2>&1 || command -v sha256sum >/dev/null 2>&1 \
  || { echo "ERROR: shasum or sha256sum is required." >&2; exit 1; }

file_sha256() {
  if command -v shasum >/dev/null 2>&1; then shasum -a 256 "$1" | awk '{print $1}'
  else sha256sum "$1" | awk '{print $1}'; fi
}

file_mode() { stat -f "%OLp" "$1" 2>/dev/null || stat -c "%a" "$1" 2>/dev/null; }

# A plugin's Python-dep declaration (ADR-0036) lives at the plugin root, not under files/, but the
# daemon reads it from the unpacked plugin dir to provision the venv / system-site links, so it must
# ship in the .b3 and be listed in the manifest files[] alongside the files/ tree.
dep_declaration_paths() {
  plugin_dir="$1"
  for req in requirements.txt klipper_requirements.txt; do
    [ -f "$plugin_dir/$req" ] && printf '%s\n' "$plugin_dir/$req"
  done
}

# LC_ALL=C forces a byte-order sort so the file list is identical regardless of locale.
build_files_array() {
  plugin_dir="$1"
  { find "$plugin_dir/files" -type f \
      ! -path '*/__pycache__/*' ! -name '*.pyc' ! -name '.DS_Store'
    dep_declaration_paths "$plugin_dir"
  } | LC_ALL=C sort | while read -r fpath; do
    relpath="${fpath#"$plugin_dir/"}"
    sha=$(file_sha256 "$fpath")
    mode=$(file_mode "$fpath")
    case "$mode" in *7*) mode="755" ;; *) mode="644" ;; esac
    printf '{"path":"%s","sha256":"%s","mode":"%s"}\n' "$relpath" "$sha" "$mode"
  done
}

pack_one() {
  plugin_dir="$1"
  name=$(jq -r '.name' "$plugin_dir/manifest.json")
  version=$(jq -r '.version' "$plugin_dir/manifest.json")
  output="$DIST_DIR/$name-$version.b3"
  tmp_dir=$(mktemp -d)
  files_json=$(build_files_array "$plugin_dir" | jq -s '.')
  jq --argjson files "$files_json" '.files = $files' "$plugin_dir/manifest.json" > "$tmp_dir/manifest.json"
  rm -f "$output"
  (
    cd "$plugin_dir"
    zip -qr "$output" files/ -x '*/__pycache__/*' '*.pyc' '*.DS_Store'
    if [ -d doc ]; then zip -qr "$output" doc/ -x '*.DS_Store'; fi
    for req in requirements.txt klipper_requirements.txt; do
      [ -f "$req" ] && zip -q "$output" "$req"
    done
    cd "$tmp_dir"
    zip -q "$output" manifest.json
  )
  rm -rf "$tmp_dir"
  echo "Packed: $output"
  echo "  sha256: $(file_sha256 "$output")"
}

mkdir -p "$DIST_DIR"
packed=0
collections=0
for dir in "$REPO_DIR"/*/; do
  [ -f "${dir}manifest.json" ] || continue
  # A collection (kind:collection) is index-only orchestration metadata with no files/ and no .b3;
  # the atom/assemble tooling carries it, but there is nothing to archive here, so skip it.
  if [ "$(jq -r '.kind // "plugin"' "${dir}manifest.json")" = "collection" ]; then
    echo "Skip (collection, index-only): ${dir%/}"
    collections=$((collections + 1))
    continue
  fi
  pack_one "${dir%/}"
  packed=$((packed + 1))
done

if [ "$packed" -eq 0 ] && [ "$collections" -eq 0 ]; then
  echo "ERROR: no plugins found (expected <plugin-id>/manifest.json dirs)." >&2
  exit 1
fi
echo ""
echo "Packed $packed plugin(s), skipped $collections collection(s)."
