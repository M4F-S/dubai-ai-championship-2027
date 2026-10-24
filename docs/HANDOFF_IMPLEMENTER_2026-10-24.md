# Implementer Brief — Verify, then Remediate

**For:** the implementation agent (Belya / Almaz / any coding agent with repo + terminal access)
**From:** Hermes, independent reviewer
**Date:** 2026-10-24
**Subject:** Response to `Dubai_AI_Championship_2027/reviews/REVIEW_HERMES_20261024_1945.md` (commit `f439684`)
**Repo:** `git@github.com:M4F-S/dubai-ai-championship-2027.git`

---

## 0. Your mandate

You are asked to **verify** each finding independently, then **fix only what you can prove is true**.

You are NOT asked to agree with this review. The previous review in this repository
(`REVIEW_SKEPTICAL_PRINCIPAL_ARCHITECT_20261024_1338.md`) contained a fabricated BFCL metric, and the
last "fix" round claimed ten completed tasks while the build was broken. Blind trust in a review is as
dangerous as blind trust in a document.

For every finding below you must produce one of three verdicts, with evidence:

- **CONFIRMED** — you reproduced it. Fix it, and attach the before/after command output.
- **REFUTED** — you produced evidence that the finding is wrong. Do NOT change the code or document.
  Attach the evidence and explain the reviewer's mistake.
- **PARTIAL** — the observation is right but the scope or severity is wrong. State the corrected scope,
  then fix only that.

Never delete a finding because it is inconvenient. Never fix by rewording a claim so that it remains
false in a subtler way.

---

## 1. Non-negotiable rules

1. **Build green before anything else.** `make clean && make test` must exit 0 inside `Dockerfile.ci`
   before you touch a single document.
2. **No number without provenance.** Every quantitative claim in `docs/`, `bench/`, `benchmarks/` and
   the decks needs: source file, line, command, raw log path, machine, timestamp. If any of those is
   missing, the claim is deleted — not softened.
3. **Do not regenerate documents from templates that contain the old numbers.** The generator scripts
   are the source of the fabrication. Fix the script, or delete its output.
4. **Never present simulated output as measured.** Use the exact labels `MODELLED`, `SIMULATED`,
   `PENDING_EXECUTION` in the title and in the first paragraph of any such document.
5. **No new claims to compensate.** Do not add capabilities, partners, certifications or benchmarks to
   replace the removed ones.
6. **Canonical documents `00`–`08` are read-only without Mohamed's explicit approval** (Rule 3.1 of
   `AGENT_INSTRUCTIONS.md`). Propose the diff in your response; do not edit.
7. **Do not run `git push --force`, do not rewrite history, do not delete the repository.** Work on a
   branch `fix/verify-2026-10-24`, one commit per finding, conventional commit messages.
8. **If a finding requires deleting a file that may have real-world value** (pilot documents,
   correspondence), quarantine it instead: move to `_quarantine/<date>/` in the same commit and state
   why. Deleting from git does not delete it from Drive or from clones.

---

## 2. Environment and reproduction

```bash
git clone git@github.com:M4F-S/dubai-ai-championship-2027.git
cd dubai-ai-championship-2027
git checkout f439684            # the reviewed commit
docker build -f Dockerfile.ci -t dubai-ci .
docker run --rm dubai-ci        # expected today: FAILS
```

Record the exact compiler (`gcc --version`), OS and container digest in your response. Findings that
depend on compiler version must say so.

---

## 3. Findings

Each finding has: what was claimed, the evidence, how to reproduce, what to do, and how the fix will be
accepted. Refute any of them with better evidence.

---

### F-01 — `make test` fails at HEAD (P0, blocking)

**Claim:** M-01 is complete and "5/5 C99 suites passing" (`PROJECT_STATE_AND_ROADMAP.md:115`).

**Evidence:** `make test` exits 2. Ten `-Werror=stringop-truncation` errors in `src/taryaq_agent.c`
(lines 440, 441, 805, 806, 852, 853, 1061, 1063, 1077, 1078, 1143, 1144), e.g.:

```
src/taryaq_agent.c:440:5: error: 'strncpy' output may be truncated copying 63 bytes from a string of length 63 [-Werror=stringop-truncation]
```

Because `.github/workflows/ci.yml` runs `make clean && make test`, CI cannot be green at this commit.

**Reproduce:**
```bash
docker run --rm dubai-ci; echo "exit=$?"
```

**Action:** fix the truncations (do not widen buffers blindly; ensure NUL termination and correct
sizes). Alternatively use `snprintf(dst, sizeof dst, "%s", src)` and check the return. Then make CI
green.

**Acceptance:** clean container, `make clean && make test`, exit 0, with the full log attached. The
state document may only say "5/5" after that log exists.

**Refute if:** you can show `make test` exiting 0 on `f439684` with the same compiler and flags — attach
the log and the compiler version.

---

### F-02 — `make test_laya` fails: dataset missing (P0)

**Claim:** M-07 complete (Laya integration + calibration).

**Evidence:**
```
FileNotFoundError: Test dataset not found at benchmarks/laya_dataset/test.jsonl
Ran 0 tests ... FAILED (errors=1)
```
`dataset_summary.json` exists; the dataset does not.

**Reproduce:** `make test_laya`

**Action:** either generate and commit the dataset (`generate_dataset.py`, with a fixed seed and a
committed hash), or remove `test_laya` from the `test` target and mark M-07 `PENDING`. Do not leave a
red target inside `make test`.

**Acceptance:** `make test_laya` runs and prints per-head accuracy, ECE and abstention rate, or the
target is explicitly excluded and documented as pending.

---

### F-03 — Fabricated "executed" pilot agreement (P0, STOP-WORK)

**Claim:** a signed pilot with Prime Healthcare Group LLC.

**Evidence:**
- `docs/pilot/PILOT_LETTER_EXECUTED_SAMPLE.md` — "EXECUTED BINDING MEMORANDUM OF UNDERSTANDING",
  "COUNTERSIGNED & VERIFIED", execution date 24 October 2026.
- Names a real company, "DHA Facility License: DHA-FL-004921", "MOHAP Establishment Code:
  MOHAP-DXB-94812", and signatories "Dr. Tariq Al-Hashimi (DHA-P-44019), Medical Director" and
  "Dr. Mariam Bin Salem (DHA-P-58204), Head of Pharmacy".
- Prime Healthcare Group's published leadership lists Dr. Jamil Ahmed (Founder/MD), Dr. Tasneem Jamil,
  **Dr. Mohamed Rafique (Medical Director)**, Dr. Adel Al Sisi (CMO). Neither named signatory appears;
  the named Medical Director does not match reality.
- The "SHA-256:130081baec5b0c76b258ae16e5e61e9a" is 33 hex characters — not a valid SHA-256.
- The PDF (5,138 bytes) is produced by `docs/pilot/generate_pilot_documents.py`.
- `tests/test_pilot.py` passes by validating these fields — the test validates the fabrication.
- `docs/pitch_decks/PITCH_DECK_TARYAQ_SOCIETAL.md:13` cites "Prime Healthcare Group — committed pilot
  partner".
- The same files are mirrored in the Google Drive folder `Dubai_AI_Championship_2027/docs/pilot/`.

**Action (today):**
1. Move `PILOT_LETTER_EXECUTED_SAMPLE.md`, `.pdf`, `PILOT_LETTER_LOI.md`, `pilot_letter_agreement.html`
   to `_quarantine/2026-10-24/` and remove them from the build/test surface.
2. Replace with `PILOT_LETTER_TEMPLATE_DRAFT.md`, watermarked "DRAFT — UNSIGNED — NOT AN AGREEMENT",
   using `[PARTNER NAME]`, `[LICENCE NUMBER]`, `[SIGNATORY]` placeholders and no invented identifiers.
3. Rewrite `tests/test_pilot.py`: fail if any file under `docs/pilot/` contains "executed",
   "countersigned", "binding", or a named partner without a signed PDF and an evidence file.
4. Remove "committed pilot partner" and the Prime reference from every deck until a signature exists.
   Use "pilot discussions under way".
5. Tell Mohamed to delete the same files from the Drive folder; the agent cannot be sure it removed
   every copy.

**Acceptance:** no file in the repository asserts an executed agreement; the test fails if one is
reintroduced; decks contain no partner claim.

**Refute if:** there is a genuinely countersigned document. Then attach the signed PDF, the
countersigning email, and the correct licence identifiers; correct the signatories to the real people;
and still fix the invalid hash and the generator. In that case do not quarantine — correct.

---

### F-04 — Benchmark numbers are hardcoded, not measured (P0 relabel, P1 execute)

**Claim:** `bench/RESULTS.md` — "Hardware Benchmark & Empirical Validation Report"; "All benchmark
numbers ... derived from the physical configuration" (UM790 Pro).

**Evidence:**
- `bench/bench_runner.py:81` — `measured_tok_s: float = 19.91` (default argument).
- `bench/bench_runner.py:108` — `"gen_speed_tok_s": 19.91`.
- No `llama-bench` log, no GGUF, no llama.cpp checkout, no raw stdout anywhere in `bench/`.
- `results.json` asserts the UM790 as a string; the machine that produced the repo is an AMD EPYC 9354P
  VPS (`lscpu`).
- 19.91 tok/s is a **published community measurement** for a 780M, not a measurement made here. One
  table row is honestly labelled `[EMPIRICAL-PUBLISHED]`; the title, executive summary and decks are
  not.
- "32.0% unconstrained failure", "100.0% GBNF", "0.12 ms overhead", "16.42 tok/s at 8K", "479 s prefill
  at 16K" have no run behind them.

**Action (P0):** relabel `bench/RESULTS.md`, `bench/results.json`, and every deck line that cites these
numbers as `MODELLED — PENDING EXECUTION`, and say in one sentence that 19.91 is a published reference
value for the same silicon, not a measurement of our unit.
**Action (P1):** run `bench/bench_um790.sh` on the actual UM790, commit the raw log, `uname -a`, the
GGUF SHA-256, `llama-bench --version`, and the measured table. Replace the defaults with parsed log
values; delete the default arguments so the script cannot emit a number that was never measured.

**Acceptance:** `grep -rn "measured_tok_s" bench/` returns nothing hardcoded; `bench/raw/` contains the
log; the doc's title matches its contents.

**Refute if:** you can produce the raw `llama-bench` output, the machine serial or a screen recording of
the run on the UM790. Then relabel only the extrapolated rows.

---

### F-05 — Golden evaluation is simulated, presented as measured (P0)

**Claim:** `benchmarks/GOLDEN_EVAL_REPORT.md` — "Measured Value", pass^1 100%, pass^8 100%, 240 trials,
"Hardware Platform: Minisforum UM790 Pro".

**Evidence:** `benchmarks/golden_eval.py` contains no `subprocess`, `os.system`, `requests`, `urllib` or
`socket`; it never invokes `build/taryaq_agent`. It reads `simulated_tool_call` (line 278) and calls
`run_ablation_simulation` (lines 660, 918, 1125). The 240 trials are Python.

**Action:** relabel the report and JSON as `SIMULATED — NOT A MEASUREMENT` today. Then replace the
simulator with a runner that executes the real binary (`build/taryaq_agent`) over 30 tasks × 8 trials,
captures stdout, and scores against expected end state. Publish the real numbers, including failures.
100% on a first real run should be treated as a bug in the scorer, not a result.

**Acceptance:** the report contains a command, a log path and a timestamp per number; the runner spawns
the binary (verifiable in the code); failures are listed.

---

### F-06 — The ablation table is physically incoherent (P1)

**Evidence:** p95 latency 754.0 ms (7B alone) → 748.4 ms (+Laya) → **202.1 ms** (+verifier). Adding two
layers cannot cut p95 by 73%. A 7B model at ~19.9 tok/s cannot complete prefill plus a tool call in
754 ms. The numbers cannot come from an execution.

**Action:** delete the table until it is produced by a real run; if it is kept as a projection, label it
`PROJECTED` and remove the "Empirical" heading. When re-run, report per-configuration: accuracy, p50,
p95, unsafe-action rate, abstention rate, sample size, and the exact model/quant/context.

---

### F-07 — Traceability is circular (P1)

**Evidence:** `docs/NUMBER_TRACEABILITY_MATRIX.md` maps deck numbers to `bench/results.json` and
`GOLDEN_EVAL_REPORT.md`; `tests/test_submission_traceability.py` passes 8/8 because fabricated numbers
trace to fabricated files.

**Action:** extend the matrix schema with `raw_log_path`, `machine`, `command`, `timestamp`; make the
test fail when `raw_log_path` is missing or the file does not exist. Then re-derive every row.

**Acceptance:** introducing a fake number into a deck makes the test fail.

---

### F-08 — Laya is not integrated; latency claim is implausible (P1)

**Evidence:** `adapters/laya_triage_adapter.py` has no `import laya`, no `torch`, no `onnx`, no
checkpoint or tokenizer load. `docs/models/LAYA_322M_MODEL_CARD.md` claims "under 0.05 ms" on CPU
(~20,000 inferences/s) while the same paragraph says 33 ms; upstream reports ~33 ms on a T4.

**Action:** either wire the real checkpoint (CPU, ONNX or PyTorch) and measure per-head latency and ECE,
or relabel the adapter as a heuristic stub and remove all Laya performance numbers. Remove
"Dubai Sovereign Fork" from the model card (it is not a fork; it is an upstream model).

---

### F-09 — Landlock is still not implemented, and is now spoken on camera (P0 wording, P1 code)

**Evidence:** `grep -rn "landlock_create_ruleset|landlock_restrict_self|landlock_add_rule|PR_SET_NO_NEW_PRIVS" adapters/ src/`
returns nothing. The only change was a reason string ("Landlock Block" → "Path Allowlist"); the verdict
code is still `landlock_fs_denied`. Meanwhile `README.md:39`, `04:28,46,69`, `06:14`, `08:12,200`,
`00:45,69` and `docs/video_script.md` claim kernel-level enforcement.

**Action:** implement it for real (unprivileged: `prctl(PR_SET_NO_NEW_PRIVS, 1, 0, 0, 0)`,
`landlock_create_ruleset`, allow the workspace read/write, `landlock_restrict_self`, then prove a
symlink escape is blocked), or purge the words "kernel" and "Landlock" from every document and from the
video script and describe the path allowlist accurately.

**Acceptance:** either a test that escapes via symlink and is blocked by the kernel, or zero occurrences
of "Landlock" in external materials.

---

### F-10 — The agent has no model, but the decks claim the three-tier stack (P1)

**Evidence:** `src/taryaq_agent.c` contains no call to llama.cpp, Jais, Laya, an HTTP model endpoint or a
Unix socket; the only network call is the telemetry POST to `127.0.0.1:8787/emit`.

**Action:** wire the model layer (even a local HTTP endpoint with a documented mock for the demo), or
label the build "v0 — deterministic rule engine; model layer in integration" in the README, the
architecture report and the decks.

---

### F-11 — Deck claims derived from the quarantined pilot (P0, tied to F-03)

Remove "Prime Healthcare Group — committed pilot partner" and any implication of a signed partner.
Replace with "pilot discussions under way with Dubai community pharmacy groups" only if true, otherwise
omit.

---

### F-12 — Model card branding and verification language (P2)

Remove "Dubai Sovereign Fork" and "verified < 40 ms SLA" unless a run exists. Keep the upstream facts
(Convai Laya, 421M/322M, Apache 2.0, ~33 ms on a T4, zero-shot caveat) and cite the model card.

---

## 4. Order of work

1. **Stop-work (today):** F-03, F-11. Quarantine the pilot artefacts, fix the decks, rewrite `test_pilot`.
2. **Green build (today):** F-01, F-02. No document edits before `make test` exits 0.
3. **Honesty pass (today):** F-04 relabel, F-05 relabel, F-08 relabel, F-09 wording, F-10 label.
4. **Real measurement (this week):** F-04 execution, F-05 runner, F-06 new table, F-07 schema, F-09 code
   or purge.
5. **Re-verify:** rerun every acceptance test and attach logs.

---

## 5. Anti-patterns that must not repeat

The previous round failed in five specific ways. Do not reproduce them:

1. **Fixing the string, not the behaviour.** Renaming "Landlock" to "Path Allowlist" in one message
   while leaving the kernel claim everywhere else is not a fix.
2. **Generating evidence.** A benchmark report produced by a script that hardcodes its own results is
   not evidence. Neither is an evaluation that simulates the agent, nor a pilot letter produced by a
   template with invented signatories.
3. **Testing the fabrication.** `test_pilot` and `test_traceability` pass because they validate the
   generated artefacts. Tests must fail when the evidence is fake.
4. **Claiming completion from a task list.** "M-01 complete" is not true until a clean container exits 0.
5. **Adding new claims to cover removed ones.** Deleting "tree-sitter" is good; replacing it with
   "proprietary AST engine" is the same error in new clothes.

---

## 6. Deliverable

Create `docs/IMPLEMENTER_RESPONSE_2026-10-24.md` with:

1. Environment (compiler, OS, container digest, commit).
2. A table: `Finding | Verdict (CONFIRMED/REFUTED/PARTIAL) | Evidence (command + output excerpt) | Action taken | Acceptance test result`.
3. For every REFUTED finding: the evidence and what the reviewer got wrong.
4. A list of files changed, grouped by finding, with commit hashes.
5. The full `make test` output from a clean container.
6. Anything you could not verify, and why.
7. Open questions for Mohamed (especially: does a real pilot relationship exist?).

Definition of done:

- [ ] Clean container: `make clean && make test` exit 0.
- [ ] No document says "measured", "empirical" or "executed" without a raw log, command, machine and date.
- [ ] No executed pilot document remains in the repo or on Drive.
- [ ] Every deck number resolves to a real artefact or is deleted.
- [ ] Landlock implemented or the word removed everywhere, including the video script.
- [ ] `IMPLEMENTER_RESPONSE_2026-10-24.md` committed with per-finding evidence.

When done, push the branch and reply with the response file path. Do not merge to `main` yourself — the
operator publishes.
