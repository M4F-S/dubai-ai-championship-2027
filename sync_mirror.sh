#!/usr/bin/env bash
# sync_mirror.sh - Tri-Mirror Synchronization for Dubai Master Coordination Plane
# Syncs: 1. Local Workspace, 2. Google Drive Mirror, 3. GitHub Remote

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "=================================================================="
echo " DUBAI MASTER PLANE: TRI-MIRROR SYNCHRONIZATION"
echo "=================================================================="

# 1. Clean local build artifacts before syncing
echo "[1/3] Cleaning local build artifacts..."
make clean >/dev/null 2>&1 || true

# Check for residual untracked artifacts
ARTIFACTS="$(git status --porcelain | grep -E '\.(dylib|so)$|^build/|^__pycache__/' || true)"
if [[ -n "$ARTIFACTS" ]]; then
    echo "[-] Error: Untracked build/test artifacts detected after make clean:" >&2
    echo "$ARTIFACTS" >&2
    echo "Please remove them before syncing." >&2
    exit 1
fi

# 2. Sync to Google Drive Mirror
GDRIVE_ROOT="${GDRIVE_ROOT:-}"
if [[ -z "$GDRIVE_ROOT" ]]; then
    for cand in ~/Library/CloudStorage/GoogleDrive-*; do
        if [[ -d "$cand/My Drive" ]]; then
            GDRIVE_ROOT="$cand/My Drive"
            break
        fi
    done
fi

if [[ -n "$GDRIVE_ROOT" && -d "$GDRIVE_ROOT" ]]; then
    TARGET_DIR="$GDRIVE_ROOT/Dubai_AI_Championship_2027"
    echo "[2/3] Mirroring to Google Drive ($TARGET_DIR)..."
    mkdir -p "$TARGET_DIR"

    RSYNC_OPTS=(-av \
        --exclude=".git" \
        --exclude="build" \
        --exclude="*.dylib" \
        --exclude="*.so" \
        --exclude="*.jsonl" \
        --exclude="__pycache__" \
        --exclude="node_modules" \
        --exclude=".next" \
        --exclude="qala-agent" \
        --exclude="nibras-agent" \
        --exclude="taryaq-agent")

    if [[ "${SYNC_DELETE:-0}" == "1" ]]; then
        RSYNC_OPTS+=(--delete)
    fi

    rsync "${RSYNC_OPTS[@]}" "$SCRIPT_DIR/" "$TARGET_DIR/"
    echo "[PASS] Google Drive mirror updated."
else
    echo "[WARN] Google Drive root not found or not mounted. Skipping cloud sync."
fi

# 3. Commit and Push to Current Git Branch
echo "[3/3] Checking Git status and pushing to GitHub..."
CURRENT_BRANCH="$(git rev-parse --abbrev-ref HEAD)"

git add -u
git add src/ adapters/ tests/ tools/ Makefile sync_mirror.sh 2>/dev/null || true
if [[ -d .github ]]; then
    git add .github/
fi

if ! git diff --cached --quiet; then
    COMMIT_MSG="${1:-feat(core): synchronize hardened round-1 adapters, tests, and hmac verification across master plane}"
    git commit -m "$COMMIT_MSG"
    git push origin "$CURRENT_BRANCH"
    echo "[PASS] GitHub remote ($CURRENT_BRANCH) updated."
else
    echo "[INFO] Git index clean. Nothing new to commit."
fi

echo "=================================================================="
echo " [SUCCESS] Tri-Mirror Synchronization Complete!"
echo "=================================================================="
