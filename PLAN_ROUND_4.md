# PLAN — Round 4: close the three gaps and make them stay closed

**Status:** proposed, for review. Nothing here is started.
**Basis:** `H_round_verification_review.md` — every item below was verified by execution against `qala-agent 0b15006`, `nibras-agent 28b0dd7`, `taryaq-agent 56619c6`, umbrella `271e2dd`.
**Themes:** (1) a strict build that CI catches but nobody blocks on, (2) an integration lane that didn't adopt the new contract, (3) a drift guard that was specified and never written.
**Scope:** four repos. Each task names its owner; the integration lane owns this repo.

---

## 0. Ownership (unchanged except one ruling)

| Path | Owner |
|---|---|
| `qala-agent/adapters/qala_*`, `adapters/grounding_shield.*` | **Qala** |
| `nibras-agent/adapters/nibras_*` | **Nibras** |
| `taryaq-agent/adapters/taryaq_*`, `src/taryaq_agent.c` | **Taryaq** |
| everything in this repo | **Integration lane** |

**Ruling needed (X-1):** `grounding_shield.*` now belongs to **Qala** — it was extended there in round 3 (`doc_id`, `section`, `page`, `passage_sha256`). Nibras and Taryaq vendor it and must not edit it. If you prefer Nibras to own it (it is used there for PII), say so before R4-06 starts; the resync direction flips.

---

## 1. Work items

### R4-01 · Qala: fix the four build errors — **Qala agent** · 30 min · blocks everything

`src/qala_policy_rag.c:226,228,230,232`. Four `-Wformat-truncation` errors: a ~1 KB line buffer copied with `%s` into 64/128-byte fields.

Add one helper and use it at all four sites:

```c
static void copy_field(char *dst, size_t cap, const char *src) {
    size_t n = strlen(src);
    if (n >= cap) n = cap - 1;
    memcpy(dst, src, n);
    dst[n] = '\0';
}
```
```c
copy_field(cur_doc_id,          sizeof cur_doc_id,          line + 8);
copy_field(cur_doc_title,       sizeof cur_doc_title,       line + 11);
copy_field(cur_section,         sizeof cur_section,         line + 9);
copy_field(cur_section_title,   sizeof cur_section_title,   line + 15);
```

**Accept:** `make clean && make all` exit 0 at `-O2 -Werror`; `make test` exit 0; the `build-and-test` check green on `main`.

### R4-02 · Branch protection on all four repos — **repo admin** · 10 min · blocks recurrence

Today: Qala merged run `40526841879`, which failed on exactly these four errors. The workflow exists; nothing enforces it.

For each repo (`qala-agent`, `nibras-agent`, `taryaq-agent`, umbrella):
- Require a pull request before merging to `main`.
- Require the CI check (`build-and-test` / `build-and-verify`) to pass.
- Disallow force-pushes and deletions.

```bash
for r in qala-agent nibras-agent taryaq-agent dubai-ai-championship-2027; do
  gh api -X PUT "repos/M4F-S/$r/branches/main/protection" \
    -H "Accept: application/vnd.github+json" \
    -f "required_status_checks[strict]=true" \
    -f "required_status_checks[contexts][]=build-and-test" \
    -F "enforce_admins=true" \
    -F "required_pull_request_reviews[required_approving_review_count]=0" \
    -F "restrictions=" 2>&1 | head -3
done
```
(Adjust the context name per repo; confirm with `gh run list`.)

**Accept:** pushing a deliberately broken commit to `main` is rejected; a PR with a red check cannot merge.

### R4-03 · Umbrella: adopt the HMAC verifier — **integration lane** · 1 h

Today `/api/audit/verify` reports `chain_intact: false`, `"Signature mismatch at record 0"`, `total_records: 1` on a genuine ledger of 2 records — it still recomputes `sha256(json minus signature)`.

1. Copy `taryaq-agent/tools/verify_audit.py` → `tools/verify_audit.py` (single source: it is Taryaq's contract).
2. In `bridge/server.py::_serve_audit_verify`, replace the recompute block: for each record require `canonical`, `prev_sha256`, `mac`; verify `HMAC-SHA256(key, prev || "\n" || canonical)` with `hmac.compare_digest`; verify `prev` equals the previous record's `mac` (first = 64 zeros).
3. Key from `TARYAQ_AUDIT_KEY`. **If unset, return HTTP 503 with `{"status": "AUDIT_KEY_MISSING"}` — never "verified".**
4. Any missing field is a failure (fail closed). Do not keep a legacy path that "skips unsigned" — that is the bug this replaces.

**Accept:** genuine ledger → `{"chain_intact": true, "total_records": 2, "status": "VERIFIED"}`; tampered field → `false` + HTTP 400 naming the line; no key → 503. Three tests in `tests/`.

### R4-04 · Umbrella: resync and rebuild — **integration lane** · 30 min

After R4-01:
- Copy the current `qala-agent/adapters/{qala_mcp_policy_adapter.c,qala_adapters.h,grounding_shield.*}`, `nibras-agent/adapters/{nibras_*}` and the new modules (`qala_case_memory.*`, `qala_policy_rag.*`, `nibras_rag.*`, `taryaq_rag_engine.*`, `tools/build_corpus_index.py`).
- Rebuild and run the full suite.

**Accept:** `make clean && make all` exit 0 at `-O2 -Werror`; `make test` exit 0.

### R4-05 · Drift guard + manifest determinism — **integration lane** · 1 h

Two mechanisms, because the guard cannot clone sibling repos in CI without tokens:

**(a) Vendored manifest (CI-enforceable).** `VENDORED.md` + `corpus/vendored.sha256`, listing each vendored file with `owner@commit` and its SHA-256. `scripts/check_vendored.sh` recomputes and fails on mismatch. Add to CI.

**(b) Cross-repo check (local + integration lane).** `scripts/check_drift.sh`: compares this repo's adapters against `../qala-agent`, `../nibras-agent`, `../taryaq-agent`, **including headers** and three-way for Taryaq's copies. (Prototype tested in round 3: reports exactly the four divergent files, exit 1.)

**(c) Build determinism.** `corpus/taryaq_manifest.sha256` currently hashes `taryaq_corpus.db`, which is regenerated on every build and is not byte-stable — so `make all` dirties a tracked file and the "provenance manifest" changes for no semantic reason. Remove the `.db` line; hash only the source texts (`dha_sn_03_2019.txt`, `drug_monographs.txt`, `uae_controlled_substances.txt`) and the chunk metadata.

**Accept:** clean tree after `make all`; deliberate edit to one vendored file → guard exit 1 naming it; clean tree → exit 0.

### R4-06 · Taryaq: resync after Qala — **Taryaq agent** · 1 h · blocked on R4-01

Taryaq is behind Qala by 149 lines (`qala_mcp_policy_adapter.c`), 34 (`qala_adapters.h`), 50 (`grounding_shield.c`), 10 (`grounding_shield.h`). Same header name, two different `grounding_source_t` layouts.

1. Copy the four files from `qala-agent` (after R4-01 is merged and green).
2. Rebuild; confirm its RAG engine still consumes the new struct fields correctly (it may already assume the old layout).
3. Re-run the full suite and the three-consecutive-runs idempotence check.

**Accept:** `diff -q` clean for all four; `make test` exit 0; three consecutive `--test` runs exit 0; clinical probes unchanged (Colchicine+Ketoconazole → UNVERIFIED, Simvastatin+Clarithromycin → BLOCKED, Warfarin+Amiodarone → BLOCKED).

### R4-07 · Umbrella README + licence — **integration lane** · 45 min

`README.md:36-47` still claims "100 % Sovereign Air-Gapped Inference … over `AF_UNIX` sockets", "`Jais 3 7B`", "`Laya 322M` … IPC harness". The three agent READMEs were cleaned; this one was not. There is no LICENSE and no NOTICE.

- Rewrite the intro as **what this repo is**: the integration plane (cockpit, HUD, bridge, corpora, docs) for three separately submitted agents.
- Delete the AF_UNIX / Jais / Laya claims, or move them to a clearly-labelled "future work".
- Add a claims table with a proof command per row (reuse the agents' rows).
- Add `LICENSE` (Apache-2.0) and `NOTICE`.

**Accept:** `grep -rniE "AF_UNIX|Jais 3|Laya 322M|tamper-evident|< ?0\.02 ?ms" README.md` → no hits.

### R4-08 · Build prerequisites in Nibras and Taryaq — **their agents** · 10 min

`libsqlite3-dev` is now required and only Qala documents it (`README.md:64`). A clean machine dies on `fatal error: sqlite3.h`.

Add to both READMEs:
```
Debian/Ubuntu: sudo apt-get install -y build-essential libsqlite3-dev   # Taryaq also: libcurl4-openssl-dev
macOS:         brew install sqlite
```

**Accept:** fresh `ubuntu:24.04` container following only the README builds and tests.

### R4-09 · One command that proves the whole thing — **integration lane** · 45 min

`scripts/verify_all.sh`:
1. Build the umbrella at `-O2 -Werror` and run its suite.
2. Generate a ledger with `taryaq-agent`'s binary (key set), start the bridge, assert `/api/audit/verify` returns `chain_intact: true` with the correct record count.
3. Tamper one record, assert `false` + 400.
4. Run the drift guard and the vendored manifest check.

**Accept:** one command, exit 0, prints a per-check PASS line. This is the artefact to show a judge or a reviewer instead of prose.

---

## 2. Sequence

```
R4-01 (Qala build) ──┬─→ R4-02 (branch protection)
                     ├─→ R4-04 (umbrella resync) ─→ R4-03 (verifier) ─→ R4-09
                     └─→ R4-06 (Taryaq resync)
R4-05 (guard + manifest) ─────────────────────────→ R4-09
R4-07, R4-08 (docs) ──────────────────────────────→ R4-09
```

Day 1: R4-01, R4-02, R4-04, R4-03. Day 2: R4-05, R4-06, R4-07, R4-08, R4-09.

**Total ≈ 5 h.**

---

## 3. Definition of done (round 4)

1. All four repos: `make clean && make test` exit 0 at `-O2 -Werror`, twice.
2. CI green on `main` in all four, **and** branch protection preventing a red merge.
3. `/api/audit/verify` returns `chain_intact: true` on a genuine ledger and `false` on a tampered one; 503 when the key is absent.
4. Drift guard green; deliberate edit turns it red; `make all` leaves the tree clean.
5. No banned claim in any README; LICENSE + NOTICE in all four.
6. `scripts/verify_all.sh` exits 0.

---

## 4. Decisions for review

- **X-1** `grounding_shield.*` owner: Qala (recommended, it extended it) or Nibras.
- **X-2** Audit key in the demo: the bridge must receive `TARYAQ_AUDIT_KEY`. Do we document a demo key in `README`/`docker-compose`, or generate one at first run and print it? (Recommended: generate + print, never commit.)
- **X-3** Branch protection `enforce_admins=true`? Recommended yes — the red merge came from an admin path.
- **X-4** Keep the `corpus/*.db` build step in `make all`, or make it an explicit `make corpus`? (Recommended: explicit, so `make all` is deterministic and fast.)

---

## 5. What not to do

- Do not hand-copy files between repos again without the manifest in place (R4-05 first, then R4-06).
- Do not "fix" the verifier by loosening it to skip records without `mac` — that restores the exact bug.
- Do not merge on a red check "because it builds locally": clang on macOS does not emit these GCC warnings, which is why H-1 happened.
- Do not regenerate the corpus manifest on every build and commit it; that noise trains people to ignore a dirty tree.
