#!/usr/bin/env bash
#
# pre_render_check.sh — Audit all .usda shot files for common VFX issues.
# Usage: ./pre_render_check.sh [shots_dir]
#   Default shots_dir: vfx_project_alpha/shots

set -euo pipefail

SHOTS_DIR="${1:-vfx_project_alpha/shots}"
ERRORS=0

check_file() {
    local usda="$1"
    local dir
    dir="$(dirname "$usda")"
    local label="${usda#"$SHOTS_DIR"/}"

    # 1. Check asset references resolve
    while IFS= read -r asset_path; do
        resolved="$dir/$asset_path"
        if [ ! -f "$resolved" ]; then
            echo "  FAIL [$label]: Missing asset — $asset_path"
            ERRORS=$((ERRORS + 1))
        fi
    done < <(grep -oP '@\K[^@]+(?=@)' "$usda" 2>/dev/null || true)

    # 2. Check focalLength > 0
    while IFS= read -r fl; do
        if awk "BEGIN{exit !($fl <= 0)}"; then
            echo "  FAIL [$label]: focalLength is $fl (must be > 0)"
            ERRORS=$((ERRORS + 1))
        fi
    done < <(grep -oP 'float focalLength\s*=\s*\K[\d.]+' "$usda" 2>/dev/null || true)

    # 3. Check visibility is not "hidden"
    if grep -qP 'visibility\s*=\s*"hidden"' "$usda" 2>/dev/null; then
        echo "  FAIL [$label]: Mesh visibility set to \"hidden\""
        ERRORS=$((ERRORS + 1))
    fi
}

echo "=== Pre-Render Check ==="
echo "Scanning: $SHOTS_DIR"
echo ""

FILE_COUNT=0
while IFS= read -r usda_file; do
    FILE_COUNT=$((FILE_COUNT + 1))
    check_file "$usda_file"
done < <(find "$SHOTS_DIR" -name '*.usda' -type f)

echo ""
if [ "$FILE_COUNT" -eq 0 ]; then
    echo "WARNING: No .usda files found in $SHOTS_DIR"
    exit 1
elif [ "$ERRORS" -eq 0 ]; then
    echo "SUCCESS: $FILE_COUNT file(s) checked, 0 issues found."
else
    echo "FAILED: $FILE_COUNT file(s) checked, $ERRORS issue(s) found."
    exit 1
fi
