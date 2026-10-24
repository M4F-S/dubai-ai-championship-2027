---

## document\_type: agent\_protocol protocol\_version: 1.0 write\_policy: append\_only\_per\_agent currency\_convention: AED timezone\_convention: Asia/Dubai (API/Audit timestamps in UTC)

# 5\. Multi-Agent Review & Collaboration Protocol

When a collaborating agent (`Belya`, `Almaz`, `Hermes`, or an external MCP copilot/CLI) inspects this **Dubai Agents** workspace, this document defines the strict rules of engagement, division of labour, honesty contract, and review output format.

---

## 5.1 Division of Labour & Domain Boundaries

* **Boundary Statement:** *"No single agent owns the entire championship submission. You do not overwrite canonical strategy files (`00`–`08`) without explicit operator approval from Mohamed, and you do not fabricate benchmark numbers or unverified integration claims. You read, verify against actual source code, report blockers honestly, and write structured review files into `./reviews/`."*

| Agent / Persona | Owned Domain | Primary Deliverable in `./reviews/` |
| :---- | :---- | :---- |
| **`Belya` / `Qala` Systems Agent** | C99 runtime, 41 native tools, POSIX PTY subshells, Linux Landlock LSM / POSIX path allowlists, C99 AST symbol index, `mcp_bridge.c`, `policy_gate.c`. | `REVIEW_QALA_SYSTEMS_<YYYYMMDD>.md` — Exact C struct/file hook locations for the MCP bridge and policy gatekeeper, plus memory/latency verification. |
| **`Almaz` / `Nibras` Cognitive Agent** | CORAL dual-stream SQLite/FTS5 memory, `VIGIL` (`appraise_event()`), `FadeMem` exponential decay, SARSI self-model, `arabic_norm.c`, `fademem_sim.c`. | `REVIEW_NIBRAS_COGNITIVE_<YYYYMMDD>.md` — Schema integration audit for UTF-8 Arabic FTS5 normalization and the `--sim-time-scale` WebSocket telemetry stream. |
| **`Hermes` Supervisor / Strategy Agent** | Dubai enterprise alignment, DESC ISR v3 audit logging, Telegram/Slack single-use approval code flow, pitch deck & video synthesis. | `REVIEW_HERMES_STRATEGY_<YYYYMMDD>.md` — Commercial red-team critique, synthetic Dubai dataset design, and DCDE Business Matching readiness checklist. |
| **External / Red-Team Reviewer** | Adversarial prompt injection testing, \$\\tau^3\$-Banking policy stress-testing, and VC pitch tear-downs. | `REVIEW_REDTEAM_<AGENT>_<YYYYMMDD>.md` — Adversarial failure cases and edge-case audit. |

---

## 5.2 Rules of Engagement (Mandatory & Imperative)

1. **Read-Only on Canonical Docs (`00`–`08`) by Default:** Do not mutate or overwrite `00_INDEX_AND_CONTEXT_MAP.md` through `08_IMPL_GLASS_COCKPIT_HUD.md` unless explicitly instructed by Mohamed.  
2. **Append-Only Reviews in `./reviews/`:** Write every critique, code integration diff, or benchmark log as a standalone Markdown file inside the `reviews` subfolder using the naming convention: `REVIEW_<AGENT_NAME>_<YYYYMMDD_HHMM>.md`  
3. **Never Fabricate, Estimate, or Carry Forward a Metric:** If a benchmark run (`pass^8`, TTFT latency, VRAM footprint, or Landlock block test) has not been physically executed on the target machine yet, mark its status as `⏳ PENDING_EXECUTION` or `🟠 UNVERIFIED_IN_PROD`. Never report projected numbers as measured facts.  
4. **Never Echo Secrets or Credentials:** Audit logs, review files, and MCP health payloads must report credential presence booleans only (`"configured": true`), never raw API tokens, Telegram bot tokens, or SSH keys.  
5. **Report the Blocker, Don't Route Around It:** If a local model weight (`Jais 3 7B`, `Laya 322M`) or C library dependency (`libcurl`, `sqlite3`) is missing or fails to compile, output the exact compiler/runtime blocker in the Verified State table.  
6. **Currency & Timezone Conventions:** All commercial and policy threshold examples must use **AED** (United Arab Emirates Dirham). Human-facing reports use `Asia/Dubai` (`UTC+4`); all JSONL audit logs and SQLite timestamps use strict ISO-8601 **UTC**.

---

## 5.3 Required Template for Agent Review Files in `./reviews/`

Every file created by a reviewing agent inside `./reviews/` must begin with this exact YAML frontmatter and include the **Verified Capability State Table**:

\---

agent\_name: "\<Belya \| Almaz \| Hermes \| ReviewerID\>"

model\_backbone: "\<Underlying LLM / Version\>"

timestamp\_utc: "2026-10-21T20:15:00Z"

target\_system: "\<Qala \| Nibras \| Both\>"

verdict: "\<APPROVE \| CAUTION \| BLOCKED\>"

\---

\# Architectural & Integration Review: \<Target System\>

\#\# 1\. Verified Capability State

\| Capability / Module \| Status (✅ / 🟠 / 🔴) \| Verified Behavior or Exact Blocker \|

\| :--- \| :---: \| :--- \|

\| Stateless MCP \`2026-07-28\` Bridge (\`mcp\_bridge.c\`) \| 🟠 \| Code spec verified in \`06\_IMPL\`; awaiting compilation link into \`Belya\` tool dispatcher. \|

\| DESC ISR v3 Policy Gate (\`policy\_gate.c\`) \| 🟠 \| Single-use approval token logic verified; needs Telegram callback wiring. \|

\| Arabic UTF-8 FTS5 Normalizer (\`arabic\_norm.c\`) \| ✅ \| Zero-allocation UTF-8 byte transformations verified against MSA & Gulf test strings. \|

\| Glass Cockpit Telemetry HUD (\`08\_IMPL\`) \| ✅ \| Standalone simulation and WebSocket event contract verified. \|

\#\# 2\. Codebase Integration Hook Points

\- \*\*Exact Source Files to Modify:\*\* ...

\- \*\*Struct / Header Signatures:\*\* ...

\#\# 3\. Skeptical Red-Team Findings & Edge Cases

\- ...

\#\# 4\. Owner Action Checklist (For Mohamed)

1\. ...