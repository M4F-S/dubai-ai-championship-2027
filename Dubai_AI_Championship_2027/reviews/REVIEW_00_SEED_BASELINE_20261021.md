---

## agent\_name: "Principal\_AI\_Research\_Architect" model\_backbone: "Gemini" timestamp\_utc: "2026-10-21T18:18:00Z" target\_system: "Both (Qala & Nibras)" verdict: "CAUTION"

# Initial Seed Audit & Definition-of-Done Checklist for Collaborating Agents

This seed review initializes the `./reviews/` directory inside the **Dubai Agents** workspace. Subsequent reviewing agents (`Belya`, `Almaz`, `Hermes`, or external MCP reviewers) must create a new file named `REVIEW_<AGENT_NAME>_<YYYYMMDD_HHMM>.md` in this folder without overwriting this baseline record.

---

## 1\. Verified Capability State (Baseline as of 2026-10-21)

| Capability / Module | Status | Verified State & Remaining Integration Work |
| :---- | :---: | :---- |
| **Core `Belya` C99 Engine** | ✅ | 41 native C99 tools, POSIX PTY subshells, Linux Landlock LSM, Tree-sitter AST index, and Telegram/Slack/Discord gateways exist in base repository. |
| **Core `Almaz` C99 Engine** | ✅ | SARSI self-model, VIGIL appraisal (`appraise_event()`), FadeMem exponential decay, and CORAL dual-stream SQLite/FTS5 memory exist in base repository. |
| **Stateless MCP `2026-07-28` Bridge (`06_IMPL`)** | 🟠 | C99 reference implementation (`mcp_stateless_build_request`) written and unit-testable; pending hook into `Qala` fork tool dispatcher. |
| **DESC ISR v3 Policy Gatekeeper (`06_IMPL`)** | 🟠 | C99 reference implementation (`policy_verify_call`) with constant-time single-use approval token verification written; pending hook into `Qala` tool execution loop. |
| **Arabic UTF-8 FTS5 Normalizer (`07_IMPL`)** | 🟠 | Zero-allocation C99 normalizer (`arabic_normalize_utf8`) written; pending hook before SQLite FTS5 `INSERT` and `MATCH` queries in `Nibras` and `Qala`. |
| **`FadeMem` `--sim-time-scale` Flag (`07_IMPL`)** | 🟠 | C99 time-acceleration math (`nibras_fademem_step`) written; pending CLI flag wiring and WebSocket broadcast in `Nibras`. |
| **3-Panel Glass Cockpit HUD (`08_IMPL`)** | ✅ | Self-contained HTML/JS/CSS dashboard complete with interactive stage simulation buttons (`simLandlockAttack`, `simTimeFastForward`, `simTelegramApproval`). |
| **Local UAE Model Binding (`Falcon 3` / `Jais 3`)** | 🔴 | Pending local GGUF download and `AF_UNIX` socket binding on the target presentation hardware. |
| **Synthetic Dubai Enterprise Test Dataset** | 🔴 | Pending creation of 50 sanitized bilingual (Arabic/English) logistics/banking records for the 200-trial \$\\text{pass}^8\$ benchmark run. |

---

## 2\. Specific Tasks Assigned to Collaborating Agents

### Task A — For `Belya` / `Qala` Systems Agent

1. Inspect the `Belya` source tree and identify the exact C source file and function where tool calls are dispatched after LLM parsing.  
2. Specify the exact `#include` and struct wiring needed to call `policy_verify_call()` before any native tool or POSIX PTY subshell executes.  
3. Verify how `mcp_stateless_build_request()` will route external ERP/gov tool calls over a local socket without breaking Landlock LSM rules.

### Task B — For `Almaz` / `Nibras` Cognitive Agent

1. Inspect the `Almaz` SQLite FTS5 initialization and query routines.  
2. Specify where `arabic_normalize_utf8()` must wrap both incoming episodic memories and incoming user search queries so BM25 lexical matching succeeds across MSA and Emirati dialects.  
3. Verify the exact JSON telemetry payload needed to stream `nibras_telemetry_snapshot_t` to the Glass Cockpit HUD every 500ms during `--sim-time-scale 10080x`.

### Task C — For `Hermes` Supervisor / Strategy Agent

1. Generate the 50-record **100% synthetic Dubai Logistics & FinOps dataset** (ensuring zero real customer or corporate data is used, per Championship rules).  
2. Draft the exact **DCDE Summary Report** table mapping each C99 architectural module of `Qala` and `Nibras` to the Championship evaluation rubric.