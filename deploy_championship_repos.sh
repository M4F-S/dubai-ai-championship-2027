#!/usr/bin/env bash
# deploy_championship_repos.sh
# Deterministic verification, build, and GitHub repository automation for:
#   1. dubai-ai-championship-2027 (Master Control Plane & Benchmark Repo)
#   2. qala-agent (Best Business AI Agent)
#   3. nibras-agent (Best Personal AI Agent)
#   4. taryaq-agent (Best Societal AI Agent)

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" >/dev/null 2>&1 && pwd)"
GITHUB_OWNER="${GITHUB_OWNER:-M4F-S}"
WORKSPACE_DIR="${WORKSPACE_DIR:-$SCRIPT_DIR}"
TAG_VERSION="v0.1.0-dubai-init"

echo "=================================================================="
echo " STEP 1: PRE-FLIGHT TOOLING & AUTH VERIFICATION"
echo "=================================================================="
command -v git >/dev/null 2>&1 || { echo "[BLOCKER] git is not installed."; exit 1; }
command -v cc  >/dev/null 2>&1 || { echo "[BLOCKER] C99 compiler (cc) is not installed."; exit 1; }
command -v make >/dev/null 2>&1 || { echo "[BLOCKER] make is not installed."; exit 1; }

echo "[PASS] Tooling (git, cc, make) verified."

echo "=================================================================="
echo " STEP 2: COMPILE & TEST C99 ADAPTERS (-std=c99 -Wall -Wextra -Werror)"
echo "=================================================================="
make -C "$WORKSPACE_DIR" test

echo "=================================================================="
echo " STEP 3: GIT INITIALIZATION & VERSION TAGGING"
echo "=================================================================="
cd "$WORKSPACE_DIR"

if [[ ! -d ".git" ]]; then
    git init
    git branch -M main
fi

git add adapters/ hud/ benchmarks/ Makefile deploy_championship_repos.sh Dubai_AI_Championship_2027/
if ! git diff --cached --quiet; then
    git commit -m "feat(championship): add hardened C99 adapters, HUD, synthetic suite, and master plan"
fi

git tag -a "$TAG_VERSION" -m "Verified initial release for Dubai Create AI Agents Championship 2027" -f
echo "[PASS] Local git repository initialized and tagged: $TAG_VERSION"

echo "=================================================================="
echo " STEP 4: GITHUB PUSH VERIFICATION"
echo "=================================================================="
if command -v gh >/dev/null 2>&1 && gh auth status >/dev/null 2>&1; then
    echo "[INFO] gh CLI is authenticated. Ready to push to GitHub ($GITHUB_OWNER)."
else
    echo "[NOTICE] GitHub CLI (gh) not yet authenticated on this host. Run 'gh auth login' to push to remote."
fi

echo "=================================================================="
echo " CHAMPIONSHIP INITIALIZATION COMPLETE"
echo "=================================================================="
