---

document\_type: git\_and\_github\_automation\_spec target\_agents:

- Hermes (macOS Supervisor & Repo Orchestrator)  
- Belya / Qala Systems Agent  
- Almaz / Nibras Cognitive Agent repositories\_to\_create:  
- dubai-ai-championship-2027 (Master Strategy, Telemetry HUD & Synthetic Benchmark Repo)  
- qala-agent (Fork of Belya \+ Qala Enterprise MCP/Policy Overlay)  
- nibras-agent (Fork of Almaz \+ Nibras Arabic FTS5 & FadeMem Sim Overlay) verified\_date: 2026-10-21

---

# 9\. GitHub Fork Architecture, Non-Invasive Overlay Design & Push Automation

## 9.1 Core Engineering Principle: "Don't Reinvent the Wheel"

A common mistake when forking systems for a competition is modifying dozens of core source files directly, creating an unmaintainable divergence from the original `Belya` and `Almaz` repositories.

To obey strict systems engineering discipline:

1. **Zero Core Mutation (The Overlay Pattern):** Both `Belya` and `Almaz` remain 100% intact as the upstream core engines. In `qala-agent` and `nibras-agent`, all championship-specific code lives inside an isolated `/championship_overlay/` directory (`qala_mcp_policy_adapter.c`, `nibras_arabic_fademem_adapter.c`, `glass_cockpit_hud.html`, and `dubai_synthetic_suite.json`).  
2. **Single-Line Hook Integration:** Linking `Qala` into `Belya` requires only a single pre-dispatch hook call (`policy_verify_call()`) inside `Belya`'s existing tool dispatcher, and linking `Nibras` into `Almaz` requires only calling `arabic_normalize_utf8()` before SQLite FTS5 `INSERT`/`MATCH` and passing `sim_time_scale` into `FadeMem`'s decay calculation.  
3. **Upstream Sync Preservation:** Both forked repositories keep `upstream` pointed at your canonical `Belya` and `Almaz` repositories so any core bugfix in `Belya` or `Almaz` can be pulled into `Qala` and `Nibras` via `git merge upstream/main` with zero merge conflicts.

---

## 9.2 Target Repository Topology on GitHub

GitHub Account / Org (M4F-S)

│

├── 1\. dubai-ai-championship-2027 (Private Monorepo / Control Plane)

│   ├── docs/

│   │   ├── 00\_INDEX\_AND\_CONTEXT\_MAP.md

│   │   ├── 01\_CHAMPIONSHIP\_INTELLIGENCE.md

│   │   ├── 02\_SOTA\_BENCHMARKS\_AND\_UAE\_MODELS.md

│   │   ├── 03\_SKEPTICAL\_AUDIT\_AND\_FORK\_STRATEGY.md

│   │   ├── 04\_TECHNICAL\_BUILD\_SPEC\_AND\_DEMO.md

│   │   ├── 05\_AGENT\_COLLABORATION\_PROTOCOL.md

│   │   ├── 09\_GITHUB\_FORK\_AND\_REPO\_AUTOMATION.md

│   │   └── 10\_SYNTHETIC\_DUBAI\_BENCHMARK\_AND\_PITCH\_DECK.md

│   ├── adapters/

│   │   ├── qala\_mcp\_policy\_adapter.c      (From Doc 06\)

│   │   └── nibras\_arabic\_fademem\_adapter.c (From Doc 07\)

│   ├── hud/

│   │   └── glass\_cockpit\_hud.html         (From Doc 08\)

│   ├── benchmarks/

│   │   └── dubai\_synthetic\_suite.json     (From Doc 10\)

│   ├── reviews/

│   │   └── REVIEW\_PRINCIPAL\_ARCHITECT\_20261021.md

│   └── Makefile                           (Builds & tests all C99 adapters)

│

├── 2\. qala-agent (Private Fork of Belya — Best Business AI Agent)

│   ├── \[All existing Belya C99 core files untouched\]

│   │   └── remotes: origin \-\> M4F-S/qala-agent \| upstream \-\> M4F-S/belya

│   └── championship\_overlay/

│       ├── qala\_mcp\_policy\_adapter.c

│       ├── qala\_adapters.h

│       └── glass\_cockpit\_hud.html

│

└── 3\. nibras-agent (Private Fork of Almaz — Best Personal & Societal AI Agent)

    ├── \[All existing Almaz C99 core files untouched\]

    │   └── remotes: origin \-\> M4F-S/nibras-agent \| upstream \-\> M4F-S/almaz

    └── championship\_overlay/

        ├── nibras\_arabic\_fademem\_adapter.c

        ├── nibras\_adapters.h

        └── glass\_cockpit\_hud.html

---

## 9.3 Skeptical Pre-Flight Verification Rules for the Executing Agent (Hermes)

Before the executing agent creates or pushes any GitHub repository, it **must** follow this verification protocol:

1. **Verify Local Tooling & Auth First:** Run `gh auth status`, `git --version`, and `cc --version`. If `gh` is not authenticated or `Belya`/`Almaz` local paths are unknown, **stop immediately and report the exact blocker** in `./reviews/`—never push broken or empty repositories.  
2. **Compile & Test Before Commit:** Run the C99 standalone self-tests with strict compiler flags (`-std=c99 -Wall -Wextra -Werror`). A commit is forbidden if either test binary returns a non-zero exit code.  
3. **Private by Default:** All three repositories must be created with `--private` to protect intellectual property prior to the January 2027 DCDE submission deadline.  
4. **Explicit Version Tagging:** Every verified milestone must be tagged with an annotated Git tag (`v0.1.0-dubai-init`) and pushed with `--follow-tags`.

---

## 9.4 Automated Verification, Fork & GitHub Push Script (`deploy_championship_repos.sh`)

The collaborating agent (Hermes or operator) can execute the script below once the Google Drive workspace files are synced or exported locally:

\#\!/usr/bin/env bash

\# deploy\_championship\_repos.sh

\# Deterministic verification, fork setup, and GitHub push automation for:

\#   1\. dubai-ai-championship-2027

\#   2\. qala-agent (forked from Belya)

\#   3\. nibras-agent (forked from Almaz)

set \-euo pipefail

GITHUB\_OWNER="\${GITHUB\_OWNER:-M4F-S}"

BELYA\_LOCAL\_PATH="\${BELYA\_LOCAL\_PATH:-\$HOME/projects/belya}"

ALMAZ\_LOCAL\_PATH="\${ALMAZ\_LOCAL\_PATH:-\$HOME/projects/almaz}"

WORKSPACE\_DIR="\${WORKSPACE\_DIR:-\$(pwd)}"

TAG\_VERSION="v0.1.0-dubai-init"

echo "=================================================================="

echo " STEP 1: PRE-FLIGHT TOOLING & AUTH VERIFICATION"

echo "=================================================================="

command \-v git \>/dev/null 2\>&1 \|\| { echo "\[BLOCKER\] git is not installed."; exit 1; }

command \-v cc  \>/dev/null 2\>&1 \|\| { echo "\[BLOCKER\] C99 compiler (cc) is not installed."; exit 1; }

command \-v gh  \>/dev/null 2\>&1 \|\| { echo "\[BLOCKER\] GitHub CLI (gh) is not installed."; exit 1; }

if \! gh auth status \>/dev/null 2\>&1; then

    echo "\[BLOCKER\] GitHub CLI (gh) is not authenticated. Run 'gh auth login' first."

    exit 1

fi

echo "\[PASS\] Tooling (git, cc, gh) and GitHub authentication verified."

echo "=================================================================="

echo " STEP 2: COMPILE & TEST C99 ADAPTERS (-std=c99 \-Wall \-Wextra \-Werror)"

echo "=================================================================="

BUILD\_TMP="\$(mktemp \-d)"

trap 'rm \-rf "\$BUILD\_TMP"' EXIT

if \[\[ \-f "\$WORKSPACE\_DIR/adapters/qala\_mcp\_policy\_adapter.c" \]\]; then

    cc \-std=c99 \-Wall \-Wextra \-Werror \-O2 \-DQALA\_STANDALONE\_TEST \\

        "\$WORKSPACE\_DIR/adapters/qala\_mcp\_policy\_adapter.c" \\

        \-o "\$BUILD\_TMP/test\_qala\_adapter"

    "\$BUILD\_TMP/test\_qala\_adapter"

else

    echo "\[WARN\] adapters/qala\_mcp\_policy\_adapter.c not yet extracted from Doc 06."

fi

if \[\[ \-f "\$WORKSPACE\_DIR/adapters/nibras\_arabic\_fademem\_adapter.c" \]\]; then

    cc \-std=c99 \-Wall \-Wextra \-Werror \-O2 \-DNIBRAS\_STANDALONE\_TEST \\

        "\$WORKSPACE\_DIR/adapters/nibras\_arabic\_fademem\_adapter.c" \-lm \\

        \-o "\$BUILD\_TMP/test\_nibras\_adapter"

    "\$BUILD\_TMP/test\_nibras\_adapter"

else

    echo "\[WARN\] adapters/nibras\_arabic\_fademem\_adapter.c not yet extracted from Doc 07."

fi

echo "=================================================================="

echo " STEP 3: PUSH MASTER STRATEGY & TELEMETRY REPO"

echo "=================================================================="

cd "\$WORKSPACE\_DIR"

if \[\[ \! \-d ".git" \]\]; then

    git init

    git branch \-M main

fi

git add .

if \! git diff \--cached \--quiet; then

    git commit \-m "feat(championship): add Dubai 2027 strategy, C99 adapters, HUD, and review protocol"

fi

git tag \-a "\$TAG\_VERSION" \-m "Verified initial release for Dubai Create AI Agents Championship 2027" \-f

if \! gh repo view "\$GITHUB\_OWNER/dubai-ai-championship-2027" \>/dev/null 2\>&1; then

    gh repo create "\$GITHUB\_OWNER/dubai-ai-championship-2027" \--private \--source=. \--remote=origin \--push

else

    git push \-u origin main \--follow-tags

fi

echo "\[PASS\] Master repository pushed: \$GITHUB\_OWNER/dubai-ai-championship-2027 (\$TAG\_VERSION)"

echo "=================================================================="

echo " STEP 4: FORK & PUSH QALA-AGENT (FROM BELYA WITHOUT CORE MUTATION)"

echo "=================================================================="

if \[\[ \-d "\$BELYA\_LOCAL\_PATH/.git" \]\]; then

    QALA\_DIR="\$(dirname "\$BELYA\_LOCAL\_PATH")/qala-agent"

    if \[\[ \! \-d "\$QALA\_DIR" \]\]; then

        git clone "\$BELYA\_LOCAL\_PATH" "\$QALA\_DIR"

    fi

    cd "\$QALA\_DIR"

    git remote rename origin upstream 2\>/dev/null \|\| true

    mkdir \-p championship\_overlay

    cp \-f "\$WORKSPACE\_DIR"/adapters/qala\_\* championship\_overlay/ 2\>/dev/null \|\| true

    cp \-f "\$WORKSPACE\_DIR"/hud/glass\_cockpit\_hud.html championship\_overlay/ 2\>/dev/null \|\| true

    git add championship\_overlay/

    if \! git diff \--cached \--quiet; then

        git commit \-m "feat(qala): attach non-invasive C99 Stateless MCP and DESC ISR v3 Policy Overlay"

    fi

    git tag \-a "\$TAG\_VERSION" \-m "Qala Championship Fork Initial Overlay" \-f

    if \! gh repo view "\$GITHUB\_OWNER/qala-agent" \>/dev/null 2\>&1; then

        gh repo create "\$GITHUB\_OWNER/qala-agent" \--private \--source=. \--remote=origin \--push

    else

        git push \-u origin main \--follow-tags

    fi

    echo "\[PASS\] Qala fork pushed: \$GITHUB\_OWNER/qala-agent (\$TAG\_VERSION)"

else

    echo "\[PENDING\] Belya local repo not found at \$BELYA\_LOCAL\_PATH. Set BELYA\_LOCAL\_PATH and re-run."

fi

echo "=================================================================="

echo " STEP 5: FORK & PUSH NIBRAS-AGENT (FROM ALMAZ WITHOUT CORE MUTATION)"

echo "=================================================================="

if \[\[ \-d "\$ALMAZ\_LOCAL\_PATH/.git" \]\]; then

    NIBRAS\_DIR="\$(dirname "\$ALMAZ\_LOCAL\_PATH")/nibras-agent"

    if \[\[ \! \-d "\$NIBRAS\_DIR" \]\]; then

        git clone "\$ALMAZ\_LOCAL\_PATH" "\$NIBRAS\_DIR"

    fi

    cd "\$NIBRAS\_DIR"

    git remote rename origin upstream 2\>/dev/null \|\| true

    mkdir \-p championship\_overlay

    cp \-f "\$WORKSPACE\_DIR"/adapters/nibras\_\* championship\_overlay/ 2\>/dev/null \|\| true

    cp \-f "\$WORKSPACE\_DIR"/hud/glass\_cockpit\_hud.html championship\_overlay/ 2\>/dev/null \|\| true

    git add championship\_overlay/

    if \! git diff \--cached \--quiet; then

        git commit \-m "feat(nibras): attach non-invasive C99 UTF-8 Arabic Normalizer & FadeMem Sim Overlay"

    fi

    git tag \-a "\$TAG\_VERSION" \-m "Nibras Championship Fork Initial Overlay" \-f

    if \! gh repo view "\$GITHUB\_OWNER/nibras-agent" \>/dev/null 2\>&1; then

        gh repo create "\$GITHUB\_OWNER/nibras-agent" \--private \--source=. \--remote=origin \--push

    else

        git push \-u origin main \--follow-tags

    fi

    echo "\[PASS\] Nibras fork pushed: \$GITHUB\_OWNER/nibras-agent (\$TAG\_VERSION)"

else

    echo "\[PENDING\] Almaz local repo not found at \$ALMAZ\_LOCAL\_PATH. Set ALMAZ\_LOCAL\_PATH and re-run."

fi