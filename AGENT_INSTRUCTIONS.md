# Agent Instructions & Collaboration Protocol
**Target Readers:** All Collaborating Agents (`Hermes`, `Belya`, `Almaz`, external LLMs) and Human Engineers  
**Workspace:** `dubai-ai-championship-2027`  
**Standard:** Strict Systems Engineering Discipline  

---

## 1. Onboarding & First Actions

Whenever you begin a session in this repository:
1. **Read `PROJECT_RULES_AND_CRITERIA.md`:** Review all statutory constraints (DESC ISR v3.1, Law No. 2 of 2019, anti-leakage rules).
2. **Inspect `PROJECT_STATE_AND_ROADMAP.md`:** Check the **Active Workstream Claim & Lock Register** to see what tasks are currently in progress.
3. **Verify Local Build Health:** Always run `make test` first. If any test fails, resolve the blocker before writing new code.

---

## 2. Anti-Collision Workstream Claim Protocol

> [!CAUTION]  
> Never start implementing a task without claiming it first in `PROJECT_STATE_AND_ROADMAP.md`.

Before writing any new feature or modifying any file:
1. Open `PROJECT_STATE_AND_ROADMAP.md`.
2. Find the relevant Workstream ID (or create a new one if not listed).
3. Set **Lock Status** to `🔒 LOCKED`, record your **Agent / Owner Name**, and list the **Affected Files**.
4. Once your work is implemented, tested with `make test`, and committed, update the status to `✅ COMPLETED`.

---

## 3. Rules of Engagement (Mandatory)

1. **Read-Only on Canonical Specs by Default:** Do not overwrite or mutate files in `Dubai_AI_Championship_2027/00` through `08` without explicit operator confirmation from Mohamed.
2. **Append-Only Reviews in `Dubai_AI_Championship_2027/reviews/`:** All architectural critiques, red-team teardowns, and benchmark logs must be written as standalone files matching the naming convention:
   ```
   Dubai_AI_Championship_2027/reviews/REVIEW_<AGENT_NAME>_<YYYYMMDD_HHMM>.md
   ```
3. **Never Fabricate, Extrapolate, or Guess a Metric:** If a benchmark run, token count, or latency measurement has not been physically measured by running code on this machine, mark it as `⏳ PENDING_EXECUTION` or `🟠 UNVERIFIED_IN_PROD`.
4. **Zero Cloud Exfiltration:** All agent communication must assume an air-gapped environment. Never echo API secrets, Telegram bot tokens, or private customer records.
5. **Strict C99 Standards:** All new C code must compile cleanly with `-std=c99 -Wall -Wextra -Werror -O2`.
6. **Mandatory Subagent Delegation for Context Hygiene:** Whenever conducting codebase searches, documentation audits, deep research, or running multi-step diagnostics, you MUST spawn isolated subagents. Never dump raw grep outputs, directory scans, or multi-page tool outputs into the primary agent context. The main context is reserved for high-level reasoning and synthesis. Subagents must return distilled, actionable findings and terminate within bounded turns.

---

## 4. Verification & Testing Checklist Before Pushing

Before pushing any commit to `origin main`:
- [ ] Run `make clean && make test`. All 3 adapter binaries must exit with code 0.
- [ ] Run `git status` to ensure no temporary test binaries or dirty files are left in the tree.
- [ ] Update `PROJECT_STATE_AND_ROADMAP.md` release lock.
- [ ] Include an annotated git tag if a new release milestone is reached.
