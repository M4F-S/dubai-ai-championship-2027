---

project: Dubai Create AI Agents Championship (2026-2027) organizer: Dubai Chamber of Digital Economy (DCDE) patronage: H.H. Sheikh Hamdan bin Mohammed bin Rashid Al Maktoum prize\_pool: AED 2,500,000+ (\$750,000+ USD) submission\_deadline: 2027-01 grand\_final: 2027-05 timezone: Asia/Dubai (UTC+4) systems\_under\_review:

- original: Belya competition\_fork: Qala (القلعة \- The Citadel) category: Best Business AI Agent  
- original: Almaz competition\_fork: Nibras (نبراس \- The Guiding Lamp) category: Best Personal AI Agent & Best Societal AI Agent (Almaz Civic) status: Architecture, Adapter Implementation & Multi-Agent Review Phase

---

# Master Context Map: Dubai Create AI Agents Championship (2026–2027)

Welcome, reviewing agent (`Belya`, `Almaz`, `Hermes`, or external MCP reviewer). This shared workspace inside **Dubai Agents** contains the complete deep-research intelligence, skeptical architectural teardown, C99 competition fork blueprints (`Qala` and `Nibras`), working reference implementations, and the multi-agent collaboration protocol for winning the **Create AI Agents Championship** in Dubai.

---

## 1\. Workspace Manifest & File Inventory

| File Name | Role & Contents | Target Reader |
| :---- | :---- | :---- |
| `00_INDEX_AND_CONTEXT_MAP.md` | Master index, architecture overview, division of labour, and workspace navigation map. | All Agents & Operators |
| `01_CHAMPIONSHIP_INTELLIGENCE.md` | Full intelligence report on DCDE rules, AED 2.5M+ prize structure, DUB.AI & D33 mandates, DESC ISR v3 compliance, jury composition, and past winner teardown (2023–2026). | Strategy & Pitch Agents |
| `02_SOTA_BENCHMARKS_AND_UAE_MODELS.md` | Late-2026 agentic benchmark analysis (`SWE-bench Verified`, `Tau-bench`, `Tau-2`, `Tau-3-Banking`, `GBA-Bench`), C99 structural advantages, and UAE sovereign open-weight models (`Falcon 3`, `Falcon3-Mamba-7B`, `Falcon-H1 Arabic`, `Jais 3`). | Systems & ML Engineers / Agents |
| `03_SKEPTICAL_AUDIT_AND_FORK_STRATEGY.md` | Unfiltered skeptical teardown of raw `Belya` and `Almaz`, identifying fatal pitch/demo flaws and defining the exact competition forks (`Qala` and `Nibras`). | Architecture & Product Reviewers |
| `04_TECHNICAL_BUILD_SPEC_AND_DEMO.md` | Detailed technical specifications for the 4 C99 adapter layers, the 5-minute Grand Final pitch script, and the 2-minute air-gapped stage demonstration choreography. | C99 Systems Agents (`Belya`/`Almaz`) |
| `05_AGENT_COLLABORATION_PROTOCOL.md` | **MANDATORY READING FOR AGENTS**: Rules of engagement, honesty rules, division of labour, and append-only review instructions inside `./reviews/`. | All Collaborating Agents |
| `06_IMPL_QALA_MCP_AND_POLICY_GATE.md` | Production-ready C99 source code (`mcp_bridge.c` \+ `policy_gate.c`) implementing the Stateless MCP `2026-07-28` client bridge and deterministic DESC ISR v3 policy gatekeeper with single-use approval codes. | `Belya` / `Qala` Build Agent |
| `07_IMPL_NIBRAS_ARABIC_AND_FADEMEM.md` | Production-ready C99 source code (`arabic_norm.c` \+ `fademem_sim.c`) implementing zero-allocation UTF-8 Arabic/Dialect FTS5 normalization and the `--sim-time-scale 10080x` trajectory decay engine. | `Almaz` / `Nibras` Build Agent |
| `08_IMPL_GLASS_COCKPIT_HUD.md` | Self-contained single-file HTML/JS/CSS 3-Panel WebSocket Telemetry HUD ("Glass Cockpit") with built-in live stage simulation for the 2-minute demo video and May 2027 Grand Final. | UI / Demo Operator |
| `reviews/` | Dedicated subfolder for append-only agent architectural audits, red-team critiques, and integration readiness reports. | Reviewing Agents |

---

## 2\. Executive Summary of the Dual-Fork Strategy

We do **not** rewrite the C99 cores of `Belya` or `Almaz`. Both engines already possess an 85%+ technical advantage over the 90%+ of competitors building fragile Python/n8n/Lovable prompt-wrappers over foreign cloud APIs. Instead, we fork both repositories and bolt thin **Enterprise, Policy, and Visual Adapter Layers** on top of the untouched C99 engines:

\========================================================================================

                        NEW COMPETITION LAYER (BUILT ON TOP)

\========================================================================================

  \[ WebSocket / Local UI Telemetry HUD \]        \[ Stateless MCP 2026-07-28 C-Bridge \]

  (Visualizes AST Graph, Security Blocks,       (Connects C99 Core to any Enterprise 

   & Memory Decay in real-time on stage)         ERP / Dubai Gov API via JSON-RPC)

                    │                                             │

                    ▼                                             ▼

  \[ Deterministic Policy Gatekeeper \]           \[ C99 UTF-8 Arabic Normalizer \]

  (Intercepts tool calls; enforces hard         (Unifies Alef/Ya, strips Tashkeel

   DESC ISR v3 & financial limits in C)          before SQLite FTS5 indexing)

\========================================================================================

                        EXISTING C99 CORE (KEEP 95% UNTOUCHED)

\========================================================================================

  \[ Belya \-\> Forked as Qala (القلعة) \]          \[ Almaz \-\> Forked as Nibras (نبراس) \]

  • 41 Native C99 Tools & POSIX PTY             • CORAL Dual-Stream Memory (SQLite+FTS5)

  • C99 Path Allowlist Sandbox Security         • VIGIL Appraisal (Reframed as Friction)

  • C99 AST Symbol Index                        • FadeMem Decay (Reframed as Token ROI)

  • Telegram / Slack / Discord Gateways         • Subconscious Mamba Background Daemon

\========================================================================================

                        LOCAL SOVEREIGN INFERENCE (AIR-GAPPED)

\========================================================================================

  • llama.cpp / vLLM over Unix Domain Socket (Jais 3 7B + Laya Multilingual 322M)