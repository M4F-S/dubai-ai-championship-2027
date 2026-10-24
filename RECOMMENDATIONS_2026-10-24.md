# Recommendations — Independent Review & Winning Plan

**Author:** Hermes (external review, independent of the project's own documents)
**Date:** 2026-10-24
**Status:** Working document for the whole team. Supersedes the unverified metrics in
`REVIEW_SKEPTICAL_PRINCIPAL_ARCHITECT_20261024_1338.md` and in `02_SOTA_BENCHMARKS_AND_UAE_MODELS.md`.
**Scope:** competition strategy, technical credibility, product scope, model stack, 10-week execution.

> Read section 0 if you read nothing else. Sections 2 and 3 contain corrections that must land before
> any deck, video or report is sent to the organiser.

---

## 0. TL;DR

1. The competition is real; the rules are broadly as the project assumes. Multiple entries are
   explicitly allowed (FAQ), but the agent "must not be copied or taken from an existing repository" —
   which constrains the fork strategy (section 4.4).
2. The two engines are real and tested (Belya 49/49, Almaz 62/62 in a clean container). They are the
   strongest asset in the project and are currently under-sold.
3. The competition layer is **not** a working product yet: five standalone test binaries, no runnable
   agent, a build that fails at HEAD, and no telemetry server behind the HUD.
4. Six load-bearing claims are false or unverifiable and must be corrected before submission
   (section 3). A jury with TII/MBZUAI/G42 people will catch them.
5. **Keep all three entries — but as one platform with three buyers, not three unrelated products.**
   Mohamed is a pharmacist; that is the unfair advantage. Lead with Taryaq (societal), then Qala
   (business), then Nibras (personal).
6. **No GPU is required.** The Minisforum UM790 Pro runs a 7B Q4 model at ~19 tok/s; the demo must stay
   at 4–8K context because generation collapses to ~5.5 tok/s at 16K.
7. Model stack: Jais 3 7B (generator) + **Laya multilingual 322M (fast calibrated triage/abstention)**
   + deterministic verifier + optional cloud escalation for <5% of cases.
8. Do **not** use basal-omni: NVIDIA-only (16–80 GB), Polish/English only, and it is a decision model,
   not a generator. It cannot run on our hardware and cannot read Arabic.
9. Winning is decided by completeness, one measured number, one named Dubai pilot, and a live demo that
   works offline — not by architecture. Most entrants never finish; finishing is the differentiator.
10. 14-day sprint and 10-week plan with owners and acceptance tests are in section 8.

---

## 1. Verified competition ground truth

Checked against the organiser's own pages, the 7 October press release, WAM, The National, Euronews and
Khaleej Times on 2026-10-24.

| Fact | Status |
|---|---|
| "Create AI Agents Championship", launched 7 Oct 2026 by Dubai Chamber of Digital Economy (DCDE) under H.H. Sheikh Hamdan | Verified |
| 4 categories: Best Societal, Best Personal, Best Business, Best Youth (<21) | Verified |
| AED 550,000 (~USD 150,000) per category winner; one of the four also becomes "AI Agent of the Year" with AED 1,000,000 | Verified (press release) |
| Total pool "exceeds AED 2.5M"; programme page separately states USD 750,000 in grants | Verified but internally inconsistent — do not build a financial plan on the AED 1M figure |
| 24 semi-finalists → 12 finalists → Grand Final, first week of May 2027 | Verified |
| Teams up to 6; each member registers individually; entries from idea to early MVP | Verified |
| **Multiple applications allowed without registering twice** | Verified — FAQ: "During the submission stage (Nov–Jan), you can submit more than one application." |
| All registration and submission materials in English | Verified |
| Finalists must demonstrate a fully functional agent live — "not an MVP" | Verified |
| Entry "must not be copied or taken from an existing repository" | Verified — this is the fork risk |
| Registration deadline | **Contradictory:** press release says December 2026; programme page and FAQ say January 2027 |
| Semi-finalist announcement | **Contradictory:** timeline says January 2027; FAQ says February 2027 |
| Dubai trade licence and UAE security clearance required for finalists | **Unverified** — appears only in our own documents. Confirm with the organiser before relying on it. |
| Judging weights | **Not published.** Published criteria: identify a real problem, build, prove customer need, business potential, measurable impact. Independent jury. |

**Actions:** register every team member now (do not wait for a deadline the organiser cannot state
consistently); confirm the trade-licence/payout path with DCDE this month; stop treating the AED 1M as
a certainty in planning.

---

## 2. Verified technical state

Measured by cloning the three repositories, building them in a clean `gcc:13` container, and running
the suites. Nothing in this section is taken from the project's own documents.

| Item | Result |
|---|---|
| Belya | Apache-2.0, ~18.1k LOC C99, 41 tools, SQLite FTS5, MCP client, Telegram/Discord/Slack gateway, **real Landlock enforcement** in `belya_harness.c` (`landlock_create_ruleset` / `landlock_add_rule` / `landlock_restrict_self`) |
| Belya tests | **49/49 pass** in a clean container (requires `git config --global --add safe.directory '*'`; without it the worktree test aborts on git ownership — environment artefact, not a code defect) |
| Almaz | Apache-2.0, ~21.4k LOC C99, FadeMem, CORAL, VIGIL, watchdog, timeline anomaly detection |
| Almaz tests | **62/62 + 65/65 holdout pass** in the same harness |
| `dubai-ai-championship-2027` build | **`make` FAILS at HEAD**: `adapters/qala_mcp_policy_adapter.c:183` triggers `-Wformat-truncation` which `-Werror` promotes to an error. The `mcp_curl_client` target also needs `libcurl` dev headers, absent from a default image. |
| Runnable agents in this repo | **None.** The only `main()` functions are the five adapter test harnesses. |
| `qala-agent`, `nibras-agent`, `taryaq-agent` | **404** on GitHub — they do not exist yet. |
| HUD telemetry | The HUD connects to `ws://127.0.0.1:8787/telemetry`; **no server in the repo implements it**. The roadmap itself still has "[ ] Build end-to-end telemetry bridge". The HUD currently works only as a click-driven simulation. |
| Internal document consistency | WS-06 and WS-07 are marked COMPLETED while the same document's Phase 2 lists both as unchecked. "Add PR_SET_NO_NEW_PRIVS" is ticked, but the syscall appears nowhere in `adapters/`. |

**What this means:** we can credibly claim "a working sovereign agent runtime". We cannot yet claim
"three competition agents". That gap is closable in ten weeks, but only if we stop describing it as
already closed.

---

## 3. Claim ledger — corrections required before any external material

Every number that reaches a deck, video, report or repository README must be either measured by us or
cited to a primary source. The following are the load-bearing errors found.

| # | Where | Current claim | Verdict and replacement |
|---|---|---|---|
| 1 | `PROJECT_STATE_AND_ROADMAP.md`, commit messages | "Adapters compile clean, `make test` passes" | **False at HEAD.** Fix the build (M-01) before repeating the claim. |
| 2 | `03`, `06`, `11`, adapter code | "Linux Landlock LSM sandboxing in the Policy Gate" | **False in the adapter.** Zero Landlock syscalls; it is a substring blacklist plus `realpath()` matching, and the verdict code is nonetheless `landlock_fs_denied`. Either implement real Landlock (drop privileges, `prctl(PR_SET_NO_NEW_PRIVS)`, ruleset on the workspace, test with a symlink escape) or say: "path allowlist and canonicalisation in the adapter; kernel Landlock enforcement in the engine (`belya_harness.c`)". |
| 3 | `02_SOTA_BENCHMARKS...` | "Pure-C Tree-sitter CST parser + PageRank impact graph" | **False.** Zero occurrences of `tree_sitter`, `ts_parser`, `pagerank` in any repo. Say "custom C symbol index" or delete. |
| 4 | Master plan, decks | "GBNF turns a 26.35% model into 99%+ deterministic dispatch" | **Conceptually wrong and unmeasured.** Grammar-constrained decoding guarantees *syntax*, not *correct tool choice*. Replace with a measured ablation (section 6, M-07). |
| 5 | `02`, decks | Falcon3-10B "86.3 on BFCL, #1 under 13B" | **Wrong number.** BFCL: **47.30 overall, 84.62 AST, 90.91 exec, 5.00 multi-turn**, irrelevance 31.89. The honest framing is stronger: multi-turn is 5.0, which is *why* the deterministic gate exists. |
| 5b | `REVIEW_SKEPTICAL_PRINCIPAL_ARCHITECT_20261024_1338.md` | "Falcon3-10B BFCL overall is 26.35%" | **Also wrong.** That review was written to catch fabrications and contains one; do not cite it as evidence. |
| 6 | All materials | "DESC ISR v3.1 compliant" | **Category error.** ISR v3.1 applies to Dubai Government Entities and is explicitly technology-neutral; a private vendor cannot "be compliant" and no attestation exists. Say: "designed to help a Dubai Government entity meet its ISR v3.1 obligations; not certified." |
| 7 | `07`, `11`, Taryaq adapter, decks | "DHA SN 03/2019 requires baseline HbA1c attachment; Ejadah claim scrubber" | **Invented rule.** SN 03/2019 is *Claim Cycle Standardisation* — submission/resubmission timelines, resubmission caps, remittance. Full text contains zero references to HbA1c or laboratory attachments. The 0.03%/day delay fee **is** real (§3.8.4, §3.9.3) and should be used instead. "EJADA" is DHA's value-based outcomes framework, not a claim validator. |
| 8 | `adapters/mcp_curl_client.c`, `qala_mcp_policy_adapter.c` | "Stateless MCP 2026-07-28 compliant client" | **Non-conformant.** Missing the required `Mcp-Name` header; `_meta` placed at JSON-RPC root instead of inside `params`; required `clientCapabilities` omitted; `Accept: text/event-stream` advertised but SSE frames are never parsed. A conformant server returns 400 `HeaderMismatch`. |
| 9 | `08`, `PROJECT_STATE` | "HUD verified / live telemetry" | **Simulation only.** No WebSocket server exists. Label it a stage visual until the bridge is built. |
| 10 | `02`, `03` | "Jais 3 / Falcon 34B local inference, 512K context" on the demo machine | **Not feasible** on the target hardware. 512K context on shared DDR5 is impossible; a 34B dense model runs at a few tokens/second. Scope to 7B at 4–8K context (section 5). |

**Verified as correct — do not "fix":** the `Authorization: Bearer %s` line in `mcp_curl_client.c:201`
is correct. It only *appears* broken because display tooling redacts secret-shaped strings. Confirm at
byte level before touching it (`sed -n '201p' adapters/mcp_curl_client.c | od -c`).

**Verified as correct and worth keeping in the pitch:** Jais 3 facts (launched 15 Oct 2026, six models
0.9B–375B, 512K context, Apache 2.0, vLLM/SGLang), the 0.03%/day DHA delay fee, the historical
conversion funnel (15,564 applications, ~1,700 prototypes, 140+ launches), and the multiple-entry rule.

---

## 4. Strategy — one platform, three buyers

### 4.1 The thesis

We are not entering three competitions with three agents. We are entering **one medication-safety
platform** with three products for three buyers. Mohamed is a pharmacist; that is the advantage no
other team in the room has, and the portfolio should make it obvious in every deck.

```
                     MEDICATION GRAPH  (drugs, doses, interactions, claim rules, Arabic terms)
                                        |
             +--------------------------+--------------------------+
             |                          |                          |
        TARYAQ (Societal)          QALA (Business)           NIBRAS (Personal)
        the pharmacist             the operator              the patient
        catches errors             recovers money            remembers and understands
        before dispensing          before submission         across doctors and languages
```

Shared core (build once): agent runtime, Arabic normaliser, Laya triage layer, deterministic policy
gate, append-only audit, HUD with real telemetry, evaluation harness, synthetic dataset.

### 4.2 Entry 1 — Taryaq (Best Societal AI Agent) — **lead entry**

- **User:** community pharmacist in a high-volume Dubai pharmacy; clinic dispensing team.
- **Job:** before dispensing, catch contraindicated combinations, renal/hepatic dose errors, duplicate
  therapy, and controlled-substance gaps; explain why, in the pharmacist's language.
- **Demo (2.5 min):** a prescription arrives in Arabic; the agent extracts it, flags a
  colchicine + clarithromycin interaction in severe renal impairment, shows the source and the rule,
  blocks the dispense, requires pharmacist override with a reason, writes an audit line.
- **Metric:** errors caught per 1,000 prescriptions; seconds per check; override rate; false-positive
  rate on a 200-case set reviewed by Mohamed.
- **Why it wins:** patient safety, 200 nationalities, Arabic-first, works offline on a mini PC in the
  back office. A pharmacist founder telling one real story beats any benchmark.

### 4.3 Entry 2 — Qala (Best Business AI Agent)

- **User:** operations manager of a pharmacy group or clinic network.
- **Job:** predict and prevent eClaimLink rejections before submission; track resubmissions and the
  0.03%/day delay exposure; flag controlled-drug compliance gaps; produce an audit trail.
- **Demo:** load 500 synthetic claims; the agent ranks the 60 most likely to be rejected, explains the
  rule breached, fixes the payload, and shows AED recovered and days of delay avoided.
- **Metric:** rejection rate before/after on a held-out claim set; AED recovered per 1,000 claims;
  resubmission cycles avoided.
- **Why it wins:** it is the money story, and it uses the one regulation we can cite correctly.

### 4.4 Entry 3 — Nibras (Best Personal AI Agent)

- **User:** a patient or family caregiver managing 4–8 chronic medications across 2–3 doctors.
- **Job:** remember the regimen, explain interactions in the user's language, prepare questions for the
  pharmacist, flag missed doses and duplicate therapies. **Never diagnoses.**
- **Demo:** six medications, three prescribers, two languages; the agent reconstructs the timeline,
  finds a therapeutic duplication, and produces a one-page brief for the pharmacist.
- **Metric:** comprehension quiz before/after; duplicate therapies detected; time saved per review.
- **Why it wins:** the consumer story and the funnel into the other two. Weakest as a standalone
  product; strongest as the third face of the platform.

### 4.5 The originality problem (must be handled deliberately)

The rule says the agent "must not be copied or taken from an existing repository", and Belya/Almaz are
public Apache-2.0 repositories with full history. Do not hide the lineage and do not rebrand a fork.

- Submit **new product repositories** (`taryaq`, `qala`, `nibras`) whose code is net-new: product
  shell, medication graph, Laya integration, gate, UI, eval harness.
- Vendor the engine as a **clearly attributed dependency** ("built on Belya, our Apache-2.0 agent
  engine, public since 2025"), with the licence text and a NOTICE file.
- Every deck gets one line: *"What is new: the medication graph, the clinician-reviewed rule set, the
  calibrated triage layer, and the workflow integration. The engine underneath is ours and open."*
- Never present a fork as a new agent. The jury may not check; the risk is not worth it, and the truth
  is a better story anyway.

---

## 5. Model stack and hardware

### 5.1 Hardware reality (Minisforum UM790 Pro)

Ryzen 9 7940HS, Radeon 780M, dual-channel DDR5-5600 ≈ 89.6 GB/s, 64 GB max. Token generation is
bandwidth-bound: tokens/s ≈ bandwidth ÷ bytes streamed per token.

| Model class | Size (Q4) | Expected generation | Verdict |
|---|---|---|---|
| 7B dense (e.g. Jais 3 7B) | ~4.5 GB | ~19 tok/s (published: 19.91 on this exact chip, Vulkan) | **Use this** |
| 7B at 16K context | — | ~5.5 tok/s (published) | Avoid for live demo; use 4–8K |
| ~28–30B MoE, ~4B active | ~14–18 GB | ~19–20 tok/s (community, 64 GB) | Candidate if Jais 3 36B-A4B gets a GGUF |
| 27–32B dense | 14–24 GB | 3–6 tok/s | Unusable live |
| 34B+ / 512K context | — | — | Not feasible on this machine |

**Rules:** no GPU rental; benchmark on the actual unit before committing (M-06); keep the stage demo at
4–8K context with short outputs; pre-warm the prompt; stream tokens so the audience sees progress.

### 5.2 The three layers

1. **Generator / planner — Jais 3 7B** (Apache 2.0, Arabic-native, 512K capable but we use 8K), Q4_K_M,
   llama.cpp Vulkan, GBNF grammar on tool calls. If GGUF is not yet published, convert from the HF
   weights and record the exact command in the repo.
2. **Triage / abstention — Laya multilingual 322M** (Convai, Apache 2.0, Sept 2026). Non-autoregressive
   typed decisions: given a state and a set of options, returns calibrated probabilities in ~33 ms on
   CPU, no text generation, <1 GB. Runs on the UM790's CPU alongside the 7B on the iGPU.
   - Use for: intent routing, urgency, claim-rejection risk, contradiction checks, "should a human see
     this?".
   - **It must be fine-tuned.** Zero-shot typed decisions are ~0.36 (near the 0.318 random baseline);
     the headline 0.766 belongs to a checkpoint fine-tuned on that benchmark's own split. Treat it as a
     fast base to specialise, not a ready decision engine.
   - Recalibrate per question type (published ECE improves from 0.466 to 0.081 after temperature
     fitting). Never quote a raw probability as if calibrated.
   - The multilingual checkpoint has a 322M encoder and ~1K context — perfect for short states, not for
     whole documents.
   - Our advantage: Mohamed can label 2,000–5,000 real decision examples. Nobody else in this
     competition has a pharmacist to produce that dataset.
3. **Verifier — deterministic, not a model.** Drug interaction table, dose ceilings by renal function,
   claim edit rules, citation grounding. This is where safety is actually enforced. The LLM proposes;
   the table disposes.

Optional fourth layer: **cloud escalation** for the <5% of cases where Laya's confidence is below
threshold and the 7B's answer fails the verifier. Switchable off for the air-gapped demo. This is a
feature, not a compromise: "we only leave the building when the case is hard and the pharmacist says
yes."

### 5.3 Do not use basal-omni

Verified on 2026-10-24: it is a Gemma 4-based *decision* model (not a generator), **NVIDIA-only in eager
mode** (16 GB mini / 24 GB max / 80 GB ultra), with no GGUF, MLX or FP8 path for the omni line, trained
on **Polish and English** only. It cannot run on a 780M and cannot read Arabic. `basal-2.0` (text) does
have GGUF, but is also Polish/English. Skip both.

### 5.4 The ablation that must appear in the deck

On the same 200-task set, measure and report:

| Configuration | Task accuracy | p95 latency | Unsafe-action rate | Abstention rate |
|---|---|---|---|---|
| Jais 3 7B alone | | | | |
| 7B + Laya triage | | | | |
| 7B + Laya + deterministic verifier | | | | |

This table is the technical slide that survives Q&A. Numbers must come from a run on our hardware, with
the command and the dataset hash committed.

---

## 6. What to build (with acceptance tests)

Nothing below is "done" until its acceptance test passes on a clean clone.

- **M-01 Fix the build.** Fix the truncation at `qala_mcp_policy_adapter.c:183` (precision or a larger
  buffer); add a `Dockerfile.ci` with `libcurl4-openssl-dev` and `libsqlite3-dev`; add a GitHub Action
  running `make clean && make test` in it.
  *Accept:* green CI on a fresh clone; `make test` exits 0 in the container.
- **M-02 Claim ledger.** Apply every correction in section 3 across docs, decks, video script and
  READMEs.
  *Accept:* `grep -ri "tree-sitter\|pagerank\|ISR v3.1 compliant\|HbA1c\|86.3" .` returns only the
  corrected, sourced statements.
- **M-03 MCP conformance.** Add `Mcp-Name`, move `_meta` into `params`, add
  `io.modelcontextprotocol/clientCapabilities`, parse `text/event-stream` frames, keep the honest
  401/403 vs network distinction.
  *Accept:* an interop test against the official MCP SDK server completes `tools/list` and `tools/call`;
  the test runs in CI.
- **M-04 HUD telemetry bridge.** A ~150-line C or Python WebSocket server that streams real events
  (`task_started`, `tool_call`, `gate_verdict`, `approval_required`, `state_committed`) to the existing
  HUD. Remove the "simulation" label only when it is real.
  *Accept:* HUD shows a real run; killing the server shows the documented offline state.
- **M-05 One runnable agent (Taryaq v0).** One binary/daemon: task intake (text + Arabic), medication
  graph lookup, 5 tools, policy gate, human approval, append-only audit, rollback.
  *Accept:* cold start → prescription → blocked interaction → override with reason → audit line, in
  under 3 minutes, with the network cable unplugged.
- **M-06 Hardware benchmark.** On the actual UM790: tok/s and prefill at 4K/8K/16K; tool-call accuracy
  with and without GBNF; memory footprint.
  *Accept:* `bench/RESULTS.md` with commands, dates and raw output committed.
- **M-07 Laya integration + fine-tune.** Ten decision questions, 2,000+ labelled examples (synthetic
  first, pharmacist-reviewed second), train/dev/test split by patient, calibration fitted on dev.
  *Accept:* per-question accuracy, ECE, abstention rate on test; model card committed.
- **M-08 Golden evaluation set.** 30 Dubai workflow tasks with expected end state (DB rows, audit
  lines), plus a τ²-bench or BFCL subset for external comparability.
  *Accept:* `pass^1` and `pass^8` reported, failures included, reproducible with one command.
- **M-09 Pilot letter.** One Dubai pharmacy group or clinic; one page; three signatures: "we will pilot
  this in Q1 2027 and share anonymised results."
  *Accept:* signed PDF in the repo (or a redacted copy) and named in the deck.
- **M-10 Submission package.** Deck (10 slides), 2.5-minute video, architecture report, working
  prototype link, all English, all numbers traceable to M-06/M-07/M-08.
  *Accept:* an independent reviewer can trace every number on every slide to a file in this repo.

---

## 7. Judging strategy by stage

**To reach the top 24 (January):** completeness and clarity. Every required artefact, English, no
broken links, no unmeasured claims, a video that shows the agent working. Most entrants fail here.

**To reach the top 12 (March):** a live demo that works, one hard number, and a named pilot. The jury
must be able to say "this pharmacist found a real problem, measured it, and a Dubai pharmacy will use
it".

**To win (May):** the story. Thirty seconds from Mohamed: a medication error he personally caught, what
it would have cost, and the agent doing the same check in under a second. Then the number. Then the
architecture, last.

Pitch order for every deck and video: **problem → who pays → live demo → measured result → why us →
architecture → ask.** Architecture never before 1:00.

Demo rules: offline by default; pre-recorded fallback for the submission video; live only with a tested
laptop and a rehearsed failure path ("here is what it refuses to do" is the most persuasive segment).

---

## 8. Execution plan

### 8.1 14-day sprint (2026-10-27 → 2026-11-09)

| Day | Work | Owner | Done when |
|---|---|---|---|
| 1–2 | M-01 build + CI; M-02 claim ledger; M-03 MCP headers | Engine | CI green; ledger applied; interop test passes |
| 3–4 | Laya on the UM790; define 10 decision questions; label 200 examples | Clinical + Engine | baseline accuracy and ECE recorded |
| 5–7 | Jais 3 7B via Vulkan; M-06 benchmark; GBNF tool-call test | Engine | `bench/RESULTS.md` committed |
| 8–10 | M-05 Taryaq v0 end to end, Arabic input, audit, override | Engine + Clinical | 3-minute offline run recorded |
| 11–12 | M-08 30-task golden set; pass^8; 7B/Laya/gate ablation | Engine | ablation table with real numbers |
| 13–14 | 60-second internal demo; go/no-go on Qala and Nibras shells | Lead | decision recorded in this file |

### 8.2 Ten weeks to submission

- W1–2: sprint above. Freeze the architecture.
- W3–4: M-07 fine-tune; Qala shell (claims) and Nibras shell (patient) on the shared core; M-09 pilot.
- W5: measure everything; write the one number per entry.
- W6: decks and architecture report; video script.
- W7: record final videos on the demo machine; rehearse offline.
- W8: **submit early.** The organiser's own deadline statements disagree by a month.
- W9–10: buffer, then semi-final preparation only after submission.

### 8.3 Owners

- **Lead / clinical:** Mohamed — rule set, labelling, pilot, founder story, final calls.
- **Engine:** build, CI, agent runtime, MCP, Laya integration, benchmarks.
- **Product/demo:** HUD, workflows, synthetic data, video capture.
- **Pitch:** decks, report, number traceability.

---

## 9. Team rules

1. **No unmeasured number leaves this repository.** Mark `PENDING_EXECUTION` until it ran.
2. **No regulatory claim without the primary text.** Cite the document, section and date.
3. **No fork presented as a new agent.** Attribute the engine; make the product code net-new.
4. **No architecture before the problem in any external material.**
5. **Every claim has an owner and a test.** If it cannot be tested, it is marketing — label it as such.
6. **Patient data never leaves the building.** Synthetic data in all demos, always. This is both a rule
   and the product's selling point.
7. **The demo must work offline.** If it needs the network, it is not a sovereignty product.

---

## 10. Risks and open decisions

| Risk | Impact | Mitigation |
|---|---|---|
| Originality rule read strictly against forked engines | Disqualification | New product repos + explicit attribution + net-new product code (4.5) |
| Three entries perceived as one product split three ways | Credibility | Distinct user, demo and metric per entry; present the platform openly |
| Registration deadline ambiguity | Missed entry | Register now; submit by the first week of December |
| Grant requires a Dubai entity / trade licence (unverified) | Prize not receivable | Confirm with DCDE this month; decide entity/partner before December |
| Local model too weak in multi-turn | Demo failure | Laya triage + deterministic verifier + GBNF + cloud escalation option |
| 16K context collapses speed on the iGPU | Demo drags | Cap at 4–8K, short outputs, streaming, pre-warmed prompts |
| Clinical claims without validation | Regulatory and reputational | Non-diagnostic framing, pharmacist sign-off, cited rules only, no autonomous action |

**Open decisions:**
1. Confirm Taryaq as the lead entry (recommended) — it uses Mohamed's profession as the differentiator.
2. Confirm the Dubai entity/partner path for grant receipt.
3. Confirm the pilot target (pharmacy group vs clinic network) by 2026-11-09.

---

## 11. Sources

- `dubaichamberdigital.com/en/create-ai-agents` — programme page, FAQ, rules (page updated 15 Oct 2026)
- Dubai Chambers press release, 7 Oct 2026; WAM; The National; Euronews (13 Oct 2026); Khaleej Times
- `modelcontextprotocol.io/specification/2026-07-28` — stateless core, required headers, `Mcp-Name`
- `gorilla.cs.berkeley.edu/leaderboard.html` — BFCL: Falcon3-10B-Instruct 47.30 / AST 84.62 / multi-turn 5.00
- `ifm.ai/blog/jais3`, MBZUAI release 15 Oct 2026 — Jais 3 sizes, 512K context, Apache 2.0, vLLM/SGLang
- `isahd.ae` SN 03/2019 full text — claim cycle standardisation, 0.03%/day delay fee, no lab requirement
- `desc.gov.ae` ISR v3.1 — scope limited to Dubai Government Entities
- `dha.gov.ae` EJADA programme — value-based outcomes framework
- `huggingface.co/convaiinnovations/laya` — 421M/322M decision model, Apache 2.0, zero-shot caveat
- `basal.si5.pl` — basal-omni hardware requirements and language coverage
- Measured locally: Belya 49/49, Almaz 62/62 (clean `gcc:13` container); `make` failure at HEAD
