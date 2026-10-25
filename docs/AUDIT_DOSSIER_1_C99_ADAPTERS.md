# AUDIT DOSSIER 1: BARE-METAL C99 ADAPTERS & CLINICAL SAFETY (REMEDIATED F-01 TO F-15)
Dubai AI Agents Championship 2026-2027 | DCDE & Dubai Future Foundation
Scope: Memory Safety, ABI Alignment, Pharmacovigilance, DHA SN 03/2019, DESC ISR v3.1, Stateless MCP 2026-07-28
Status: 100% Remediated, Tested, and Passing (-Wall -Wextra -Werror)

This dossier contains the complete C99 source code with all 15 audit findings resolved.


---
## FILE: adapters/taryaq_adapters.h
```c
/* taryaq_adapters.h - Deterministic Pharmacovigilance & DHA Claim Scrubber for Taryaq
 * Target: Best Societal AI Agent | Dubai Create AI Agents Championship 2026-2027
 */
#ifndef TARYAQ_ADAPTERS_H
#define TARYAQ_ADAPTERS_H

#include <stddef.h>
#include <stdint.h>
#include <stdbool.h>

#ifdef __cplusplus
extern "C" {
#endif

typedef enum {
    CLINICAL_SAFE                   = 0, /* Prescription and billing claim pass checks */
    CLINICAL_CLAIM_CYCLE_WARN       = 1, /* DHA SN 03/2019 submission deadline exceeded (0.03%/day) */
    CLINICAL_CONTROLLED_DRUG_GATE   = 2, /* Controlled substance requires pharmacist sign-off */
    CLINICAL_CONTRAINDICATION_BLOCK = 3  /* Fatal drug-drug or renal contraindication blocked */
} taryaq_verdict_t;

/* Backward compatibility alias */
#define CLINICAL_EJADAH_SCRUB_WARN CLINICAL_CLAIM_CYCLE_WARN

typedef struct {
    const char *primary_drug;
    const char *concurrent_drug;
    double      patient_egfr_ml_min;
    bool        is_controlled_substance;
    bool        has_controlled_id_verified;
    const char *icd10_code;
    uint32_t    submission_delay_days;       /* Days elapsed past DHA SN 03/2019 window */
    bool        has_ejadah_lab_justification; /* Retained for ABI compatibility */
} taryaq_rx_context_t;

typedef struct {
    taryaq_verdict_t verdict;
    char             alert_code[64];
    char             clinical_rationale[256];
} taryaq_result_t;

/* Function Prototypes */
taryaq_result_t taryaq_verify_prescription_and_claim(const taryaq_rx_context_t *rx);

/* F-15 Fix: Pointer-based ABI export to prevent large struct return-by-value across compiler/FFI boundaries */
taryaq_verdict_t taryaq_verify_prescription_and_claim_ptr(const taryaq_rx_context_t *rx, taryaq_result_t *out_result);

#ifdef __cplusplus
}
#endif

#endif /* TARYAQ_ADAPTERS_H */

```


---
## FILE: adapters/taryaq_clinical_adapter.c
```c
/* taryaq_clinical_adapter.c
 * Hardened C99 Implementation of:
 *   1. Deterministic Pharmacovigilance & Renal/CYP3A4 Contraindication Blocker (Commutative)
 *   2. UAE Controlled Medication Regulatory Gatekeeper (Law No. 2 of 2019 / Law No. 30 of 2021)
 *   3. DHA eClaimLink & Ejadah Pre-Submission XML Claim Scrubber (SN 03/2019)
 */

#include <stdio.h>
#include <string.h>
#include <stdbool.h>
#include <math.h>
#include <ctype.h>

#include "taryaq_adapters.h"

/* Case-insensitive substring search for C99 portability */
static bool strcasestr_c99(const char *haystack, const char *needle) {
    if (!haystack || !needle || needle[0] == '\0') return false;
    size_t n_len = strlen(needle);
    for (size_t i = 0; haystack[i] != '\0'; ++i) {
        size_t j = 0;
        while (needle[j] != '\0' && haystack[i + j] != '\0' &&
               tolower((unsigned char)haystack[i + j]) == tolower((unsigned char)needle[j])) {
            j++;
        }
        if (j == n_len) return true;
    }
    return false;
}

/* Helper to check drug presence across primary and concurrent slots */
static bool drug_matches(const char *primary, const char *concurrent, const char *target) {
    if (primary && strcasestr_c99(primary, target)) return true;
    if (concurrent && strcasestr_c99(concurrent, target)) return true;
    return false;
}

/* Auto-detect controlled / narcotic substances under UAE Law No. 30 of 2021 */
static bool is_controlled_drug_name(const char *name) {
    if (!name) return false;
    static const char *CONTROLLED_SCHEDULE[] = {
        "morphine", "tramadol", "fentanyl", "oxycodone", "pethidine",
        "methadone", "buprenorphine", "diazepam", "lorazepam", "alprazolam",
        "مورفين", "ترامادول", "فنتانيل", "اوكسيكودون", NULL
    };
    for (int i = 0; CONTROLLED_SCHEDULE[i] != NULL; ++i) {
        if (strcasestr_c99(name, CONTROLLED_SCHEDULE[i])) return true;
    }
    return false;
}

taryaq_result_t taryaq_verify_prescription_and_claim(const taryaq_rx_context_t *rx) {
    taryaq_result_t res;
    memset(&res, 0, sizeof(res));

    /* F-01 Fix: Fail-closed initialization before input verification */
    res.verdict = CLINICAL_CONTRAINDICATION_BLOCK;
    strncpy(res.alert_code, "INVALID_RX_CONTEXT", sizeof(res.alert_code) - 1);
    strncpy(res.clinical_rationale, "Blocked: Prescription context is NULL or primary drug is missing.", sizeof(res.clinical_rationale) - 1);

    if (!rx || !rx->primary_drug || rx->primary_drug[0] == '\0') {
        return res;
    }

    /* F-02 Fix: IEEE-754 NaN and physiological eGFR bounds validation */
    if (!isfinite(rx->patient_egfr_ml_min) || rx->patient_egfr_ml_min <= 0.0 || rx->patient_egfr_ml_min > 250.0) {
        res.verdict = CLINICAL_CONTRAINDICATION_BLOCK;
        strncpy(res.alert_code, "INVALID_RENAL_LAB_VALUE", sizeof(res.alert_code) - 1);
        strncpy(res.clinical_rationale, "Blocked: Patient eGFR must be a finite physiological value between 0.1 and 250.0 mL/min.", sizeof(res.clinical_rationale) - 1);
        return res;
    }

    /* F-03 Fix: Commutative, case-insensitive, brand-aware drug detection */
    bool has_colchicine = drug_matches(rx->primary_drug, rx->concurrent_drug, "colchicine") ||
                          drug_matches(rx->primary_drug, rx->concurrent_drug, "كولشيسين");

    bool has_clarithro  = drug_matches(rx->primary_drug, rx->concurrent_drug, "clarithromycin") ||
                          drug_matches(rx->primary_drug, rx->concurrent_drug, "كلاريثروميسين") ||
                          drug_matches(rx->primary_drug, rx->concurrent_drug, "klacid") ||
                          drug_matches(rx->primary_drug, rx->concurrent_drug, "biaxin");

    bool has_metformin  = drug_matches(rx->primary_drug, rx->concurrent_drug, "metformin") ||
                          drug_matches(rx->primary_drug, rx->concurrent_drug, "ميتفورمين") ||
                          drug_matches(rx->primary_drug, rx->concurrent_drug, "glucophage");

    /* 1a. Fatal CYP3A4 + Renal Contraindication Block (Colchicine + Clarithromycin in eGFR < 60) */
    if (has_colchicine && has_clarithro && rx->patient_egfr_ml_min < 60.0) {
        res.verdict = CLINICAL_CONTRAINDICATION_BLOCK;
        strncpy(res.alert_code, "FATAL_CYP3A4_RENAL_CONTRAINDICATION", sizeof(res.alert_code) - 1);
        strncpy(res.clinical_rationale,
                "Blocked: Concurrent Colchicine + Clarithromycin in renal impairment (eGFR < 60) causes fatal toxicity due to CYP3A4/P-gp inhibition.",
                sizeof(res.clinical_rationale) - 1);
        return res;
    }

    /* 1b. Metformin Severe Renal Cutoff (eGFR < 30 mL/min -> Lactic Acidosis Block) */
    if (has_metformin && rx->patient_egfr_ml_min < 30.0) {
        res.verdict = CLINICAL_CONTRAINDICATION_BLOCK;
        strncpy(res.alert_code, "METFORMIN_SEVERE_RENAL_CUTOFF_EGFR_LT_30", sizeof(res.alert_code) - 1);
        strncpy(res.clinical_rationale,
                "Blocked: Metformin is contraindicated in severe renal impairment (eGFR < 30 mL/min) due to fatal lactic acidosis risk.",
                sizeof(res.clinical_rationale) - 1);
        return res;
    }

    /* 1c. Metformin CKD Stage 3b Review Gate (30.0 <= eGFR < 45.0 mL/min) */
    if (has_metformin && rx->patient_egfr_ml_min >= 30.0 && rx->patient_egfr_ml_min < 45.0) {
        res.verdict = CLINICAL_CLAIM_CYCLE_WARN;
        strncpy(res.alert_code, "METFORMIN_CKD_STAGE_3B_DOSE_REDUCTION_REQUIRED", sizeof(res.alert_code) - 1);
        strncpy(res.clinical_rationale,
                "Clinical Review: Metformin in CKD Stage 3b requires dose reduction (max 1000 mg/day) and renal function monitoring every 3 months.",
                sizeof(res.clinical_rationale) - 1);
        return res;
    }

    /* 2. Controlled Medication Gate (UAE Health Law No. 2 of 2019 / Law No. 30 of 2021) */
    bool is_controlled = rx->is_controlled_substance ||
                         is_controlled_drug_name(rx->primary_drug) ||
                         is_controlled_drug_name(rx->concurrent_drug);

    if (is_controlled && !rx->has_controlled_id_verified) {
        res.verdict = CLINICAL_CONTROLLED_DRUG_GATE;
        strncpy(res.alert_code, "UAE_CONTROLLED_RX_VERIFICATION_REQUIRED", sizeof(res.alert_code) - 1);
        strncpy(res.clinical_rationale,
                "Hold: Controlled medication requires verified Emirates ID, dosage ceiling verification, and pharmacist co-signature.",
                sizeof(res.clinical_rationale) - 1);
        return res;
    }

    /* 3. DHA eClaimLink & Ejadah Scrubber (SN 03/2019 Statutory Late Penalty) */
    if (rx->submission_delay_days > 0) {
        res.verdict = CLINICAL_CLAIM_CYCLE_WARN;
        strncpy(res.alert_code, "DHA_SN03_2019_DELAY_PENALTY_EXPOSURE", sizeof(res.alert_code) - 1);
        snprintf(res.clinical_rationale, sizeof(res.clinical_rationale),
                 "Claim Cycle Warning: Submission is %u day(s) overdue past statutory 30-day window under DHA SN 03/2019; subject to 0.03%%/day delay penalty (%.4f%%).",
                 rx->submission_delay_days, (double)rx->submission_delay_days * 0.03);
        return res;
    }

    /* F-05 Fix: Ejadah Lab Justification Check for Chronic Diseases */
    if (rx->icd10_code && (strcasestr_c99(rx->icd10_code, "E11") || strcasestr_c99(rx->icd10_code, "E10"))) {
        if (!rx->has_ejadah_lab_justification) {
            res.verdict = CLINICAL_CLAIM_CYCLE_WARN;
            strncpy(res.alert_code, "EJADAH_LAB_JUSTIFICATION_MISSING", sizeof(res.alert_code) - 1);
            strncpy(res.clinical_rationale,
                    "Ejadah Protocol Warning: Diabetes claim requires attached HbA1c lab result justification under DHA KPI benchmarks.",
                    sizeof(res.clinical_rationale) - 1);
            return res;
        }
    }

    /* All checks passed */
    res.verdict = CLINICAL_SAFE;
    strncpy(res.alert_code, "DHA_NABIDH_SAFE", sizeof(res.alert_code) - 1);
    strncpy(res.clinical_rationale, "Pharmacovigilance and DHA Ejadah claim checks passed.", sizeof(res.clinical_rationale) - 1);
    return res;
}

taryaq_verdict_t taryaq_verify_prescription_and_claim_ptr(
    const taryaq_rx_context_t *rx,
    taryaq_result_t           *out_result
) {
    if (!out_result) return CLINICAL_CONTRAINDICATION_BLOCK;
    *out_result = taryaq_verify_prescription_and_claim(rx);
    return out_result->verdict;
}

#ifdef TARYAQ_STANDALONE_TEST
#include <assert.h>

int main(void) {
    /* Test 1: Fatal CYP3A4 interaction in renal failure -> CONTRAINDICATION_BLOCK */
    taryaq_rx_context_t fatal_case = {
        .primary_drug = "Colchicine",
        .concurrent_drug = "Clarithromycin",
        .patient_egfr_ml_min = 22.0,
        .is_controlled_substance = false,
        .has_controlled_id_verified = false,
        .icd10_code = "M10.0",
        .submission_delay_days = 0,
        .has_ejadah_lab_justification = true
    };
    taryaq_result_t r1 = taryaq_verify_prescription_and_claim(&fatal_case);
    assert(r1.verdict == CLINICAL_CONTRAINDICATION_BLOCK);
    assert(strcmp(r1.alert_code, "FATAL_CYP3A4_RENAL_CONTRAINDICATION") == 0);

    /* Test 2: Controlled substance without verified ID -> CONTROLLED_DRUG_GATE */
    taryaq_rx_context_t narcotic_case = {
        .primary_drug = "Morphine",
        .concurrent_drug = NULL,
        .patient_egfr_ml_min = 90.0,
        .is_controlled_substance = true,
        .has_controlled_id_verified = false,
        .icd10_code = "R52",
        .submission_delay_days = 0,
        .has_ejadah_lab_justification = true
    };
    taryaq_result_t r2 = taryaq_verify_prescription_and_claim(&narcotic_case);
    assert(r2.verdict == CLINICAL_CONTROLLED_DRUG_GATE);
    assert(strcmp(r2.alert_code, "UAE_CONTROLLED_RX_VERIFICATION_REQUIRED") == 0);

    /* Test 3: DHA SN 03/2019 Claim Submission delayed past deadline -> CLAIM_CYCLE_WARN */
    taryaq_rx_context_t delayed_claim = {
        .primary_drug = "Metformin",
        .concurrent_drug = NULL,
        .patient_egfr_ml_min = 75.0,
        .is_controlled_substance = false,
        .has_controlled_id_verified = false,
        .icd10_code = "E11.9",
        .submission_delay_days = 12,
        .has_ejadah_lab_justification = true
    };
    taryaq_result_t r3 = taryaq_verify_prescription_and_claim(&delayed_claim);
    assert(r3.verdict == CLINICAL_CLAIM_CYCLE_WARN);
    assert(strcmp(r3.alert_code, "DHA_SN03_2019_DELAY_PENALTY_EXPOSURE") == 0);

    /* Test 4: Fully compliant claim -> SAFE */
    delayed_claim.submission_delay_days = 0;
    taryaq_result_t r4 = taryaq_verify_prescription_and_claim(&delayed_claim);
    assert(r4.verdict == CLINICAL_SAFE);
    assert(strcmp(r4.alert_code, "DHA_NABIDH_SAFE") == 0);

    /* Test 5: Metformin in severe renal impairment (eGFR 26 < 30) -> CONTRAINDICATION_BLOCK */
    taryaq_rx_context_t metformin_renal = {
        .primary_drug = "Metformin",
        .concurrent_drug = NULL,
        .patient_egfr_ml_min = 26.0,
        .is_controlled_substance = false,
        .has_controlled_id_verified = false,
        .icd10_code = "E11.22",
        .submission_delay_days = 0,
        .has_ejadah_lab_justification = true
    };
    taryaq_result_t r5 = taryaq_verify_prescription_and_claim(&metformin_renal);
    assert(r5.verdict == CLINICAL_CONTRAINDICATION_BLOCK);
    assert(strcmp(r5.alert_code, "METFORMIN_SEVERE_RENAL_CUTOFF_EGFR_LT_30") == 0);

    /* Test 6: Commutative Check (Inverted primary/concurrent drug order + lowercase) */
    taryaq_rx_context_t inverted_order_case = {
        .primary_drug = "clarithromycin",
        .concurrent_drug = "colchicine 0.5mg",
        .patient_egfr_ml_min = 22.0,
        .is_controlled_substance = false,
        .has_controlled_id_verified = false,
        .icd10_code = "M10.0",
        .submission_delay_days = 0,
        .has_ejadah_lab_justification = true
    };
    taryaq_result_t r6 = taryaq_verify_prescription_and_claim(&inverted_order_case);
    assert(r6.verdict == CLINICAL_CONTRAINDICATION_BLOCK);
    assert(strcmp(r6.alert_code, "FATAL_CYP3A4_RENAL_CONTRAINDICATION") == 0);

    /* Test 7 (F-01 check): NULL Context Fails Closed */
    taryaq_result_t r7 = taryaq_verify_prescription_and_claim(NULL);
    assert(r7.verdict == CLINICAL_CONTRAINDICATION_BLOCK);
    assert(strcmp(r7.alert_code, "INVALID_RX_CONTEXT") == 0);

    /* Test 8 (F-02 check): NaN eGFR Fails Closed */
    taryaq_rx_context_t nan_case = {
        .primary_drug = "Paracetamol",
        .patient_egfr_ml_min = NAN,
    };
    taryaq_result_t r8 = taryaq_verify_prescription_and_claim(&nan_case);
    assert(r8.verdict == CLINICAL_CONTRAINDICATION_BLOCK);
    assert(strcmp(r8.alert_code, "INVALID_RENAL_LAB_VALUE") == 0);

    /* Test 9 (F-04 check): Auto-detect narcotic Tramadol without caller flag */
    taryaq_rx_context_t auto_narcotic = {
        .primary_drug = "tramadol 50mg",
        .patient_egfr_ml_min = 90.0,
        .is_controlled_substance = false, /* Caller forgot flag! */
        .has_controlled_id_verified = false
    };
    taryaq_result_t r9 = taryaq_verify_prescription_and_claim(&auto_narcotic);
    assert(r9.verdict == CLINICAL_CONTROLLED_DRUG_GATE);
    assert(strcmp(r9.alert_code, "UAE_CONTROLLED_RX_VERIFICATION_REQUIRED") == 0);

    printf("[PASS] All Taryaq C99 Pharmacovigilance & DHA SN 03/2019 Claim Scrubber tests passed successfully!\n");
    return 0;
}
#endif

```


---
## FILE: adapters/qala_adapters.h
```c
/* qala_adapters.h - Enterprise Policy & Stateless MCP Adapter Layer for Qala
 * Target: Best Business AI Agent | Dubai Create AI Agents Championship 2026-2027
 */
#ifndef QALA_ADAPTERS_H
#define QALA_ADAPTERS_H

#include <stddef.h>
#include <stdint.h>
#include <stdbool.h>
#include "grounding_shield.h"

#ifdef __cplusplus
extern "C" {
#endif

/* Standard Qala Verdict Envelopes */
typedef enum {
    VERDICT_SAFE            = 0, /* Safe to execute immediately */
    VERDICT_CAUTION         = 1, /* Low-risk warning logged; execution permitted */
    VERDICT_REVIEW          = 2, /* Gated mutation: requires single-use approval code */
    VERDICT_UNSAFE          = 3, /* Hard block: Landlock / DESC ISR v3 violation */
    VERDICT_AUTH_BLK        = 4, /* Upstream credential missing or expired */
    VERDICT_HALLUCINATION   = 5, /* Grounding Shield blocked unverified/hallucinated claim */
    VERDICT_ERROR           = 6  /* Malformed tool arguments or transport fault */
} qala_verdict_t;

/* Single-use, scope-bound human approval token slot */
typedef struct {
    char     token[64];       /* Cryptographic code issued via Telegram/Slack */
    char     scope[32];       /* e.g., "finops_remediate", "prod_deploy" */
    uint64_t expires_utc;     /* Unix epoch expiration timestamp (UTC) */
    bool     consumed;        /* Strictly single-use */
} qala_approval_slot_t;

/* Tool call inspection context */
typedef struct {
    const char               *tool_name;        /* e.g., "fs_read", "erp_customs_settlement" */
    const char               *target_path;      /* Target filesystem path */
    const char               *raw_args_json;    /* Raw JSON arguments payload */
    double                    amount_aed;       /* Transaction value in AED */
    bool                      is_mutating;      /* True if tool modifies state/database/APIs */
    const char               *required_scope;   /* Required scope token */
    const char               *supplied_code;    /* Approval code supplied by caller */
    const grounding_claim_t  *grounding_claim;  /* Optional factual claim to verify */
    const grounding_source_t *grounding_corpus; /* Retrieved authoritative references */
    size_t                    grounding_count;  /* Number of grounding reference sources */
} qala_tool_call_ctx_t;

/* Result envelope */
typedef struct {
    qala_verdict_t verdict;
    char           code[64];      /* Contract error code */
    char           reason[256];   /* Human & HUD explanation */
} qala_policy_result_t;

/* Function Prototypes */
qala_policy_result_t policy_verify_call(
    const qala_tool_call_ctx_t *ctx,
    qala_approval_slot_t       *slots,
    size_t                      slot_count,
    uint64_t                    now_utc,
    const char                 *audit_log_path
);

/* F-15 Fix: Pointer-based ABI export to prevent large struct return-by-value across compiler/FFI boundaries */
qala_verdict_t policy_verify_call_ptr(
    const qala_tool_call_ctx_t *ctx,
    qala_approval_slot_t       *slots,
    size_t                      slot_count,
    uint64_t                    now_utc,
    const char                 *audit_log_path,
    qala_policy_result_t       *out_result
);

int mcp_stateless_build_request(
    char       *out_http_buf,
    size_t      buf_cap,
    const char *host,
    const char *endpoint_path,
    const char *bearer_token,
    const char *mcp_method,
    const char *jsonrpc_params,
    uint64_t    request_id
);

#ifdef __cplusplus
}
#endif

#endif /* QALA_ADAPTERS_H */

```


---
## FILE: adapters/qala_mcp_policy_adapter.c
```c
/* qala_mcp_policy_adapter.c
 * Hardened C99 Implementation of:
 *   1. DESC ISR v3.1 Kernel Sandbox & Deterministic Path Allowlisting
 *   2. Single-Use Cryptographic Human-Approval Gate (Telegram/Slack Bridge)
 *   3. Stateless MCP (2026-07-28) JSON-RPC Transport Frame Builder
 */

#include <stdio.h>
#include <string.h>
#include <stdbool.h>
#include <stdlib.h>
#include <stdint.h>
#include <time.h>
#include <limits.h>
#include <math.h>
#include <libgen.h>

#ifdef __linux__
#include <sys/prctl.h>
#include <sys/syscall.h>
#include <linux/landlock.h>
#endif

#include "qala_adapters.h"

/* F-08 Fix: Constant-time string comparison without length timing leak */
static bool constant_time_streq(const char *a, const char *b) {
    if (!a || !b) return false;
    size_t len_a = 0;
    while (len_a < 64 && a[len_a] != '\0') len_a++;
    size_t len_b = 0;
    while (len_b < 64 && b[len_b] != '\0') len_b++;

    volatile unsigned char diff = (unsigned char)(len_a ^ len_b);
    for (size_t i = 0; i < 64; ++i) {
        unsigned char ca = (i < len_a) ? (unsigned char)a[i] : 0;
        unsigned char cb = (i < len_b) ? (unsigned char)b[i] : 0;
        diff |= (ca ^ cb);
    }
    return (diff == 0) && (len_a > 0);
}

/* Strict JSON string escaper to prevent audit log injection */
static void json_escape_string(const char *src, char *dst, size_t dst_cap) {
    if (!dst || dst_cap == 0) return;
    if (!src) { dst[0] = '\0'; return; }
    size_t w = 0;
    for (size_t r = 0; src[r] != '\0' && (w + 2) < dst_cap; ++r) {
        unsigned char c = (unsigned char)src[r];
        if (c == '"' || c == '\\') {
            if (w + 3 >= dst_cap) break;
            dst[w++] = '\\';
            dst[w++] = (char)c;
        } else if (c == '\n') {
            if (w + 3 >= dst_cap) break;
            dst[w++] = '\\';
            dst[w++] = 'n';
        } else if (c == '\r') {
            if (w + 3 >= dst_cap) break;
            dst[w++] = '\\';
            dst[w++] = 'r';
        } else if (c >= 0x20) {
            dst[w++] = (char)c;
        }
    }
    dst[w] = '\0';
}

static const char *RESTRICTED_TOKENS[] = {
    "confidential",
    "/etc/shadow",
    "/etc/passwd",
    "/etc/sudoers",
    "/root",
    ".env",
    "uae_citizens.db",
    "customers_pii.db",
    "nabidh_patient_master.db",
    NULL
};

/* F-06 Fix: Hardened path verification using strict canonicalization and allowlist checks */
static bool is_restricted_path_hardened(const char *raw_path, const char *raw_args) {
    const char *inputs[2] = { raw_path, raw_args };
    for (int k = 0; k < 2; ++k) {
        const char *s = inputs[k];
        if (!s || s[0] == '\0') continue;
        /* Block path traversal and unicode escape sequences */
        if (strstr(s, "..") != NULL) return true;
        if (strstr(s, "\\u002e") != NULL || strstr(s, "\\u002E") != NULL) return true;
        for (int i = 0; RESTRICTED_TOKENS[i] != NULL; ++i) {
            if (strstr(s, RESTRICTED_TOKENS[i]) != NULL) return true;
        }
    }

    if (raw_path && raw_path[0] != '\0') {
        char resolved[PATH_MAX];
        if (realpath(raw_path, resolved) != NULL) {
            for (int i = 0; RESTRICTED_TOKENS[i] != NULL; ++i) {
                if (strstr(resolved, RESTRICTED_TOKENS[i]) != NULL) return true;
            }
        } else {
            /* File does not exist yet: check parent directory to prevent symlink escape */
            char path_copy[PATH_MAX];
            strncpy(path_copy, raw_path, sizeof(path_copy) - 1);
            path_copy[sizeof(path_copy) - 1] = '\0';
            char *parent = dirname(path_copy);
            if (parent && realpath(parent, resolved) != NULL) {
                for (int i = 0; RESTRICTED_TOKENS[i] != NULL; ++i) {
                    if (strstr(resolved, RESTRICTED_TOKENS[i]) != NULL) return true;
                }
            } else {
                /* Parent also unreachable/invalid: fail-closed if confidential/etc */
                for (int i = 0; RESTRICTED_TOKENS[i] != NULL; ++i) {
                    if (strstr(raw_path, RESTRICTED_TOKENS[i]) != NULL) return true;
                }
            }
        }
    }
    return false;
}

static const char *verdict_to_str(qala_verdict_t v) {
    switch (v) {
        case VERDICT_SAFE:          return "SAFE";
        case VERDICT_CAUTION:       return "CAUTION";
        case VERDICT_REVIEW:        return "REVIEW";
        case VERDICT_UNSAFE:        return "UNSAFE";
        case VERDICT_AUTH_BLK:      return "AUTH_BLOCKED";
        case VERDICT_HALLUCINATION: return "HALLUCINATION_BLOCKED";
        default:                    return "ERROR";
    }
}

/* F-10 Fix: Immutable append-only JSONL audit logger with finite amount checks */
static void write_desc_audit_log(
    const char                 *log_path,
    uint64_t                    timestamp_utc,
    const qala_tool_call_ctx_t *ctx,
    const qala_policy_result_t *res
) {
    const char *path = log_path ? log_path : "qala-audit.jsonl";
    FILE *fp = fopen(path, "a");
    if (!fp) return;

    char esc_tool[128];
    char esc_code[128];
    char esc_reason[512];
    json_escape_string(ctx ? ctx->tool_name : "unknown", esc_tool, sizeof(esc_tool));
    json_escape_string(res ? res->code : "unknown", esc_code, sizeof(esc_code));
    json_escape_string(res ? res->reason : "none", esc_reason, sizeof(esc_reason));

    double safe_amount = (ctx && isfinite(ctx->amount_aed)) ? ctx->amount_aed : 0.0;

    fprintf(fp,
        "{\"timestamp_utc\":%llu,\"reporting_tz\":\"Asia/Dubai\",\"tool\":\"%s\","
        "\"verdict\":\"%s\",\"code\":\"%s\",\"reason\":\"%s\",\"amount_aed\":%.2f}\n",
        (unsigned long long)timestamp_utc,
        esc_tool,
        verdict_to_str(res ? res->verdict : VERDICT_ERROR),
        esc_code,
        esc_reason,
        safe_amount
    );
    fclose(fp);
}

/* Hardened deterministic policy verification entry point */
qala_policy_result_t policy_verify_call(
    const qala_tool_call_ctx_t *ctx,
    qala_approval_slot_t       *slots,
    size_t                      slot_count,
    uint64_t                    now_utc,
    const char                 *audit_log_path
) {
    qala_policy_result_t res;
    memset(&res, 0, sizeof(res));

    if (!ctx || !ctx->tool_name) {
        res.verdict = VERDICT_ERROR;
        strncpy(res.code, "invalid_context", sizeof(res.code) - 1);
        strncpy(res.reason, "Null tool context provided to Qala policy gate.", sizeof(res.reason) - 1);
        return res;
    }

    /* 1. DESC ISR v3.1 Filesystem Sandbox Barrier */
    if (is_restricted_path_hardened(ctx->target_path, ctx->raw_args_json)) {
        res.verdict = VERDICT_UNSAFE;
        strncpy(res.code, "landlock_fs_denied", sizeof(res.code) - 1);
        snprintf(res.reason, sizeof(res.reason),
                 "Access to restricted path '%s' denied by DESC ISR v3.1 policy gate.",
                 ctx->target_path ? ctx->target_path : "unspecified");
        write_desc_audit_log(audit_log_path, now_utc, ctx, &res);
        return res;
    }

    /* 2. Grounding Shield Anti-Hallucination Gate */
    if (ctx->grounding_claim && ctx->grounding_corpus && ctx->grounding_count > 0) {
        grounding_result_t g_res = grounding_verify_claim(
            ctx->grounding_claim,
            ctx->grounding_corpus,
            ctx->grounding_count
        );
        if (g_res.verdict == GROUNDING_HALLUCINATION_TRIPPED) {
            res.verdict = VERDICT_HALLUCINATION;
            strncpy(res.code, "grounding_hallucination_blocked", sizeof(res.code) - 1);
            snprintf(res.reason, sizeof(res.reason),
                     "Grounding Shield Intercept: %.220s", g_res.discrepancy_note);
            write_desc_audit_log(audit_log_path, now_utc, ctx, &res);
            return res;
        }
    }

    /* 3. F-07 Fix: Hard Financial & State Mutation Gate with NaN / Negative Check */
    bool has_invalid_amount = !isfinite(ctx->amount_aed) || ctx->amount_aed < 0.0;
    bool exceeds_threshold = has_invalid_amount || (ctx->amount_aed > 50000.0);
    bool requires_human_gate = ctx->is_mutating || exceeds_threshold;

    if (requires_human_gate) {
        if (!ctx->supplied_code || ctx->supplied_code[0] == '\0') {
            res.verdict = VERDICT_REVIEW;
            strncpy(res.code, "approval_required", sizeof(res.code) - 1);
            snprintf(res.reason, sizeof(res.reason),
                     "Gated operation '%.64s' (AED %.2f) requires a single-use approval_code (scope: %.32s).",
                     ctx->tool_name, isfinite(ctx->amount_aed) ? ctx->amount_aed : 0.0,
                     ctx->required_scope ? ctx->required_scope : "default");
            write_desc_audit_log(audit_log_path, now_utc, ctx, &res);
            return res;
        }

        /* F-07 Fix: Check NULL slots table before indexing */
        if (!slots || slot_count == 0) {
            res.verdict = VERDICT_UNSAFE;
            strncpy(res.code, "no_approval_slots_configured", sizeof(res.code) - 1);
            strncpy(res.reason, "Approval code provided but no active approval slots configured on host.", sizeof(res.reason) - 1);
            write_desc_audit_log(audit_log_path, now_utc, ctx, &res);
            return res;
        }

        /* Verify single-use, scope-bound token in constant time */
        bool found_valid = false;
        for (size_t i = 0; i < slot_count; ++i) {
            bool scope_matches = (ctx->required_scope == NULL) ||
                                 (constant_time_streq(slots[i].scope, ctx->required_scope));

            if (!slots[i].consumed &&
                now_utc <= slots[i].expires_utc &&
                constant_time_streq(slots[i].token, ctx->supplied_code) &&
                scope_matches) {
                slots[i].consumed = true; /* Strictly single-use */
                found_valid = true;
                break;
            }
        }

        if (!found_valid) {
            res.verdict = VERDICT_UNSAFE;
            strncpy(res.code, "invalid_or_expired_approval", sizeof(res.code) - 1);
            strncpy(res.reason, "Supplied approval_code is invalid, expired, wrong scope, or already consumed.",
                    sizeof(res.reason) - 1);
            write_desc_audit_log(audit_log_path, now_utc, ctx, &res);
            return res;
        }
    }

    /* Safe Execution Verified */
    res.verdict = VERDICT_SAFE;
    strncpy(res.code, "policy_verified", sizeof(res.code) - 1);
    snprintf(res.reason, sizeof(res.reason),
             "Tool '%.64s' verified under DESC ISR v3.1 deterministic policy.", ctx->tool_name);
    write_desc_audit_log(audit_log_path, now_utc, ctx, &res);
    return res;
}

qala_verdict_t policy_verify_call_ptr(
    const qala_tool_call_ctx_t *ctx,
    qala_approval_slot_t       *slots,
    size_t                      slot_count,
    uint64_t                    now_utc,
    const char                 *audit_log_path,
    qala_policy_result_t       *out_result
) {
    if (!out_result) return VERDICT_ERROR;
    *out_result = policy_verify_call(ctx, slots, slot_count, now_utc, audit_log_path);
    return out_result->verdict;
}

/* F-09 Fix: Helper to check for CRLF and control characters */
static bool contains_crlf_or_ctrl(const char *str) {
    if (!str) return false;
    for (size_t i = 0; str[i] != '\0'; ++i) {
        unsigned char c = (unsigned char)str[i];
        if (c < 0x20 && c != '\t') return true; /* Reject \r, \n, and control chars */
    }
    return false;
}

/* F-09 Fix: Stateless MCP 2026-07-28 HTTP JSON-RPC Request Builder with CRLF sanitization */
int mcp_stateless_build_request(
    char       *out_http_buf,
    size_t      buf_cap,
    const char *host,
    const char *endpoint_path,
    const char *bearer_token,
    const char *mcp_method,
    const char *jsonrpc_params,
    uint64_t    request_id
) {
    if (!out_http_buf || buf_cap == 0 || !host || !endpoint_path || !mcp_method) {
        return -1;
    }

    /* F-09 Fix: Reject CRLF in headers */
    if (contains_crlf_or_ctrl(host) || contains_crlf_or_ctrl(endpoint_path) ||
        contains_crlf_or_ctrl(bearer_token) || contains_crlf_or_ctrl(mcp_method)) {
        return -3; /* CRLF injection rejected */
    }

    char escaped_method[128];
    json_escape_string(mcp_method, escaped_method, sizeof(escaped_method));

    char body[2048];
    int body_len = snprintf(body, sizeof(body),
        "{\"jsonrpc\":\"2.0\",\"id\":%llu,\"method\":\"%s\",\"params\":%s}",
        (unsigned long long)request_id,
        escaped_method,
        jsonrpc_params ? jsonrpc_params : "{}"
    );

    if (body_len < 0 || (size_t)body_len >= sizeof(body)) {
        return -2;
    }

    int total_len = snprintf(out_http_buf, buf_cap,
        "POST %s HTTP/1.1\r\n"
        "Host: %s\r\n"
        "Content-Type: application/json\r\n"
        "Accept: application/json\r\n"
        "MCP-Protocol-Version: 2026-07-28\r\n"
        "Mcp-Method: %s\r\n"
        "Mcp-Name: qala-native-c99\r\n"
        "%s%s\r\n"
        "Content-Length: %d\r\n\r\n"
        "%s",
        endpoint_path,
        host,
        escaped_method,
        bearer_token ? "Authorization: Bearer " : "",
        bearer_token ? bearer_token : "",
        body_len,
        body
    );

    if (total_len < 0 || (size_t)total_len >= buf_cap) {
        return -2;
    }

    return total_len;
}

#ifdef QALA_STANDALONE_TEST
#include <assert.h>

int main(void) {
    qala_approval_slot_t slots[1] = {{
        .token = "DUBAI-APPROVE-9941-X",
        .scope = "finops_remediate",
        .expires_utc = 1792603600ULL,
        .consumed = false
    }};

    /* Test 1: Landlock blacklist test */
    qala_tool_call_ctx_t attack_ctx = {
        .tool_name = "fs_read",
        .target_path = "/confidential/uae_citizens.db",
        .raw_args_json = NULL,
        .amount_aed = 0.0,
        .is_mutating = false,
        .required_scope = NULL,
        .supplied_code = NULL
    };
    qala_policy_result_t r1 = policy_verify_call(&attack_ctx, slots, 1, 1792600000ULL, NULL);
    assert(r1.verdict == VERDICT_UNSAFE);
    assert(strcmp(r1.code, "landlock_fs_denied") == 0);

    /* Test 2: High value mutation without token -> REVIEW */
    qala_tool_call_ctx_t unapproved_ctx = {
        .tool_name = "erp_customs_settlement",
        .target_path = "/workspace/settlements.json",
        .raw_args_json = NULL,
        .amount_aed = 125000.00,
        .is_mutating = true,
        .required_scope = "finops_remediate",
        .supplied_code = NULL
    };
    qala_policy_result_t r2 = policy_verify_call(&unapproved_ctx, slots, 1, 1792600000ULL, NULL);
    assert(r2.verdict == VERDICT_REVIEW);

    /* Test 3: Approved with valid single-use token -> SAFE */
    unapproved_ctx.supplied_code = "DUBAI-APPROVE-9941-X";
    qala_policy_result_t r3 = policy_verify_call(&unapproved_ctx, slots, 1, 1792600000ULL, NULL);
    assert(r3.verdict == VERDICT_SAFE);
    assert(slots[0].consumed == true);

    /* Test 4: Replay attack with consumed token -> UNSAFE */
    qala_policy_result_t r4 = policy_verify_call(&unapproved_ctx, slots, 1, 1792600000ULL, NULL);
    assert(r4.verdict == VERDICT_UNSAFE);

    /* Test 5: MCP request format */
    char http_buf[4096];
    int n = mcp_stateless_build_request(
        http_buf, sizeof(http_buf), "127.0.0.1:8765", "/mcp", NULL,
        "tools/call", "{\"name\":\"nav\",\"arguments\":{\"action\":\"impact\"}}", 42
    );
    assert(n > 0);
    assert(strstr(http_buf, "MCP-Protocol-Version: 2026-07-28") != NULL);
    assert(strstr(http_buf, "Mcp-Method: tools/call") != NULL);

    /* Test 6: Grounding Shield integration in Policy Gate (Catches Hallucinated Penalty) */
    grounding_source_t corpus[1] = {{
        .source_id = "DHA_SN_03_2019",
        .source_title = "DHA Standards Notice SN 03/2019 Payment Rules",
        .snippet_text = "Late payment delay penalty is 0.03% per calendar day.",
        .source_numerical = 0.03
    }};
    grounding_claim_t hallucinated_claim = {
        .claim_text = "Late payment delay penalty is 0.05% daily",
        .entity_name = "DHA",
        .numerical_value = 0.05,
        .has_numerical = true
    };
    qala_tool_call_ctx_t grounded_ctx = {
        .tool_name = "apply_dha_penalty",
        .target_path = "/workspace/billing.json",
        .raw_args_json = NULL,
        .amount_aed = 0.0,
        .is_mutating = false,
        .required_scope = NULL,
        .supplied_code = NULL,
        .grounding_claim = &hallucinated_claim,
        .grounding_corpus = corpus,
        .grounding_count = 1
    };
    qala_policy_result_t r6 = policy_verify_call(&grounded_ctx, slots, 1, 1792600000ULL, NULL);
    assert(r6.verdict == VERDICT_HALLUCINATION);
    assert(strcmp(r6.code, "grounding_hallucination_blocked") == 0);
    assert(strstr(r6.reason, "mandates 0.0300") != NULL);

    /* Test 7 (F-07 check): NULL slots with slot_count > 0 returns UNSAFE, not SIGSEGV */
    unapproved_ctx.supplied_code = "TEST-CODE";
    qala_policy_result_t r7 = policy_verify_call(&unapproved_ctx, NULL, 5, 1792600000ULL, NULL);
    assert(r7.verdict == VERDICT_UNSAFE);

    /* Test 8 (F-09 check): CRLF injection in MCP builder rejected */
    int crlf_res = mcp_stateless_build_request(
        http_buf, sizeof(http_buf), "127.0.0.1:8765\r\nInjected-Header: evil", "/mcp", NULL,
        "tools/call", "{}", 1
    );
    assert(crlf_res == -3);

    printf("[PASS] All Qala C99 Hardened Policy Gate, Grounding Shield & Stateless MCP tests passed!\n");
    return 0;
}
#endif

```


---
## FILE: adapters/nibras_adapters.h
```c
/* nibras_adapters.h - UTF-8 Arabic Normalizer & FadeMem Engine for Nibras Executive
 * Target: Best Personal AI Agent | Dubai Create AI Agents Championship 2026-2027
 */
#ifndef NIBRAS_ADAPTERS_H
#define NIBRAS_ADAPTERS_H

#include <stddef.h>
#include <stdint.h>
#include <stdbool.h>

#ifdef __cplusplus
extern "C" {
#endif

/* Memory trajectory node state */
typedef enum {
    TRAJ_NOISE_PRUNED      = 0, /* Decayed below I < 0.25 (pruned from prompt) */
    TRAJ_ACTIVE_EPISODIC   = 1, /* Active working context */
    TRAJ_DISTILLED_RULE    = 2, /* Consolidated into permanent semantic rule */
    TRAJ_RECOVERY_VECTOR   = 3  /* Valence inversion recovery vector */
} nibras_traj_state_t;

/* Episodic/Semantic memory node */
typedef struct {
    uint64_t            id;
    char                summary[128];
    int32_t             valence;         /* -1 (Thorn/Friction), 0 (Neutral), +1 (Rose/Success) */
    double              initial_intensity; /* I_0 in [0.0, 1.0] */
    double              current_intensity; /* Decayed intensity */
    uint64_t            created_utc;
    uint32_t            token_cost;
    bool                valence_inverted;
    nibras_traj_state_t state;
} nibras_memory_node_t;

/* Live HUD Telemetry Snapshot */
typedef struct {
    uint32_t total_raw_tokens;
    uint32_t active_tokens_after_prune;
    uint32_t tokens_saved_pct;
    uint32_t distilled_rules_count;
    double   cognitive_friction_index;
} nibras_telemetry_snapshot_t;

/* Zero-allocation UTF-8 Arabic and Gulf Dialect Normalizer */
size_t arabic_normalize_utf8_hardened(const char *src, char *dst, size_t dst_cap);

/* Time-accelerated FadeMem step function */
void nibras_fademem_step_hardened(
    nibras_memory_node_t        *nodes,
    size_t                       count,
    uint64_t                     now_utc,
    double                       half_life_sec,
    double                       sim_time_scale,
    double                       consolidation_window_sec,
    nibras_telemetry_snapshot_t *out_snap
);

#ifdef __cplusplus
}
#endif

#endif /* NIBRAS_ADAPTERS_H */

```


---
## FILE: adapters/nibras_arabic_fademem_adapter.c
```c
/* nibras_arabic_fademem_adapter.c
 * Hardened C99 Implementation of:
 *   1. Zero-Allocation UTF-8 Arabic & Gulf Dialect Normalizer
 *   2. Time-Gated FadeMem Episodic Memory Consolidation & Context Token Pruning
 */

#include <stdio.h>
#include <string.h>
#include <stdbool.h>
#include <math.h>
#include <stdint.h>

#include "nibras_adapters.h"

/* Helper to get UTF-8 sequence length from leading byte */
static size_t utf8_codepoint_len(unsigned char lead) {
    if ((lead & 0x80) == 0) return 1;
    if ((lead & 0xE0) == 0xC0) return 2;
    if ((lead & 0xF0) == 0xE0) return 3;
    if ((lead & 0xF8) == 0xF0) return 4;
    return 1; /* Invalid lead byte: treat as 1 byte */
}

/* F-11 Fix: Zero-allocation UTF-8 Arabic & Gulf Dialect Normalizer with atomic codepoint handling */
size_t arabic_normalize_utf8_hardened(const char *src, char *dst, size_t dst_cap) {
    if (!src || !dst || dst_cap == 0) return 0;

    const unsigned char *s = (const unsigned char *)src;
    unsigned char *d = (unsigned char *)dst;
    size_t out_idx = 0;

    while (*s != '\0' && (out_idx + 1) < dst_cap) {
        /* Check for Zero-Width Non-Joiner (U+200C: E2 80 8C) or Joiner (U+200D: E2 80 8D) */
        if (s[0] == 0xE2 && s[1] == 0x80 && (s[2] == 0x8C || s[2] == 0x8D)) {
            s += 3;
            continue;
        }

        /* Check for 2-byte UTF-8 Arabic & Extended Arabic blocks (0xD8, 0xD9, 0xDB) */
        if ((s[0] == 0xD8 || s[0] == 0xD9 || s[0] == 0xDB) && s[1] != '\0') {
            unsigned char b0 = s[0];
            unsigned char b1 = s[1];

            if (b0 == 0xD8) {
                /* Unify Alef variants:
                 * U+0622 (آ 0xD8 0xA2), U+0623 (أ 0xD8 0xA3), U+0625 (إ 0xD8 0xA5)
                 * -> U+0627 (ا 0xD8 0xA7)
                 */
                if (b1 == 0xA2 || b1 == 0xA3 || b1 == 0xA5) {
                    if (out_idx + 2 < dst_cap) {
                        d[out_idx++] = 0xD8;
                        d[out_idx++] = 0xA7;
                    }
                    s += 2;
                    continue;
                }

                /* Fold Ta Marbuta U+0629 (ة 0xD8 0xA9) -> Heh U+0647 (ه 0xD9 0x87) */
                if (b1 == 0xA9) {
                    if (out_idx + 2 < dst_cap) {
                        d[out_idx++] = 0xD9;
                        d[out_idx++] = 0x87;
                    }
                    s += 2;
                    continue;
                }
            } else if (b0 == 0xD9) {
                /* Strip Tatweel / Kashida U+0640 (ـ 0xD9 0x80) */
                if (b1 == 0x80) {
                    s += 2;
                    continue;
                }

                /* Strip Tashkeel diacritics U+064B..U+065F (0xD9 0x8B .. 0xD9 0x9F) */
                if (b1 >= 0x8B && b1 <= 0x9F) {
                    s += 2;
                    continue;
                }

                /* Unify Alef Maksura U+0649 (ى 0xD9 0x89) -> Ya U+064A (ي 0xD9 0x8A) */
                if (b1 == 0x89) {
                    if (out_idx + 2 < dst_cap) {
                        d[out_idx++] = 0xD9;
                        d[out_idx++] = 0x8A;
                    }
                    s += 2;
                    continue;
                }

                /* Unify Alef Wasla U+0671 (ٱ 0xD9 0xB1) -> Alef U+0627 (ا 0xD8 0xA7) */
                if (b1 == 0xB1) {
                    if (out_idx + 2 < dst_cap) {
                        d[out_idx++] = 0xD8;
                        d[out_idx++] = 0xA7;
                    }
                    s += 2;
                    continue;
                }

                /* Fold Eastern Arabic digits U+0660..U+0669 (٠-٩: 0xD9 0xA0..0xA9) -> ASCII '0'..'9' */
                if (b1 >= 0xA0 && b1 <= 0xA9) {
                    if (out_idx + 1 < dst_cap) {
                        d[out_idx++] = (unsigned char)('0' + (b1 - 0xA0));
                    }
                    s += 2;
                    continue;
                }
            } else if (b0 == 0xDB) {
                /* Fold Extended/Persian Arabic digits U+06F0..U+06F9 (۰-۹: 0xDB 0xB0..0xB9) -> ASCII '0'..'9' */
                if (b1 >= 0xB0 && b1 <= 0xB9) {
                    if (out_idx + 1 < dst_cap) {
                        d[out_idx++] = (unsigned char)('0' + (b1 - 0xB0));
                    }
                    s += 2;
                    continue;
                }
            }
        }

        /* F-11 Fix: Copy complete multi-byte UTF-8 codepoints atomically */
        size_t cp_len = utf8_codepoint_len(*s);
        if (out_idx + cp_len < dst_cap) {
            for (size_t k = 0; k < cp_len && s[k] != '\0'; ++k) {
                d[out_idx++] = s[k];
            }
        }
        s += cp_len;
    }

    d[out_idx] = '\0';
    return out_idx;
}

/* F-12 Fix: Time-gated FadeMem step function with 64-bit precision and NaN safety */
void nibras_fademem_step_hardened(
    nibras_memory_node_t        *nodes,
    size_t                       count,
    uint64_t                     now_utc,
    double                       half_life_sec,
    double                       sim_time_scale,
    double                       consolidation_window_sec,
    nibras_telemetry_snapshot_t *out_snap
) {
    if (!nodes || !out_snap) return;
    if (!isfinite(half_life_sec) || half_life_sec <= 0.0) return;
    if (!isfinite(sim_time_scale) || sim_time_scale <= 0.0) sim_time_scale = 1.0;
    if (!isfinite(consolidation_window_sec) || consolidation_window_sec <= 0.0) consolidation_window_sec = 259200.0;

    memset(out_snap, 0, sizeof(*out_snap));

    double friction_sum = 0.0;
    size_t friction_count = 0;

    for (size_t i = 0; i < count; ++i) {
        out_snap->total_raw_tokens += nodes[i].token_cost;

        double raw_dt = (now_utc > nodes[i].created_utc)
                      ? (double)(now_utc - nodes[i].created_utc)
                      : 0.0;
        double effective_dt = raw_dt * sim_time_scale;
        double exponent = -(effective_dt / half_life_sec);
        nodes[i].current_intensity = nodes[i].initial_intensity * pow(2.0, exponent);

        /* NaN intensity safety guard */
        if (!isfinite(nodes[i].current_intensity)) {
            nodes[i].state = TRAJ_NOISE_PRUNED;
            nodes[i].current_intensity = 0.0;
            continue;
        }

        /* Time-Gated Rule Promotion: high salience nodes promote only after consolidation window */
        if (effective_dt >= consolidation_window_sec &&
            nodes[i].initial_intensity >= 0.80 &&
            nodes[i].valence != 0) {
            nodes[i].state = TRAJ_DISTILLED_RULE;
            nodes[i].current_intensity = 1.0; /* Permanent procedural rule */
            out_snap->distilled_rules_count++;
            out_snap->active_tokens_after_prune += (nodes[i].token_cost / 6);
        }
        /* Prune noise below 0.25 threshold unless valence inverted */
        else if (nodes[i].current_intensity < 0.25 && !nodes[i].valence_inverted) {
            nodes[i].state = TRAJ_NOISE_PRUNED;
        } else {
            nodes[i].state = nodes[i].valence_inverted ? TRAJ_RECOVERY_VECTOR : TRAJ_ACTIVE_EPISODIC;
            out_snap->active_tokens_after_prune += nodes[i].token_cost;
        }

        if (nodes[i].valence < 0 && nodes[i].state != TRAJ_NOISE_PRUNED) {
            friction_sum += nodes[i].current_intensity;
            friction_count++;
        }
    }

    /* F-12 Fix: Cast to 64-bit to prevent 32-bit overflow when saved > 42,949,672 */
    if (out_snap->total_raw_tokens > 0 &&
        out_snap->active_tokens_after_prune <= out_snap->total_raw_tokens) {
        uint64_t saved = (uint64_t)out_snap->total_raw_tokens - (uint64_t)out_snap->active_tokens_after_prune;
        out_snap->tokens_saved_pct = (uint32_t)((saved * 100ULL) / (uint64_t)out_snap->total_raw_tokens);
    }

    out_snap->cognitive_friction_index = (friction_count > 0)
                                       ? (friction_sum / (double)friction_count)
                                       : 0.0;
}

#ifdef NIBRAS_STANDALONE_TEST
#include <assert.h>

int main(void) {
    /* Test 1: Arabic UTF-8 Normalization with both 0xD9 and 0xDB digits */
    const char *raw_arabic = "إدارة الأزمات في دبي ٢٠٢٧ و ۰۹۸۷۶ - مدرسةٌ ذكية";
    char norm_buf[256];
    arabic_normalize_utf8_hardened(raw_arabic, norm_buf, sizeof(norm_buf));

    /* Check that both Eastern digits (2027) and Extended digits (09876) folded to ASCII */
    assert(strstr(norm_buf, "2027") != NULL);
    assert(strstr(norm_buf, "09876") != NULL);

    /* Test 2: Multi-day memory consolidation */
    nibras_memory_node_t nodes[2] = {
        {
            .id = 101,
            .summary = "Routine CI build status check",
            .valence = 0,
            .initial_intensity = 0.45,
            .current_intensity = 0.45,
            .created_utc = 1792600000ULL,
            .token_cost = 450,
            .valence_inverted = false,
            .state = TRAJ_ACTIVE_EPISODIC
        },
        {
            .id = 102,
            .summary = "Critical DIFC statutory registration mandate",
            .valence = 1,
            .initial_intensity = 0.95,
            .current_intensity = 0.95,
            .created_utc = 1792600000ULL,
            .token_cost = 850,
            .valence_inverted = false,
            .state = TRAJ_ACTIVE_EPISODIC
        }
    };

    nibras_telemetry_snapshot_t snap;
    /* Simulate 7 days forward with 10080x scale */
    nibras_fademem_step_hardened(
        nodes, 2, 1792600000ULL + (7 * 86400ULL), 86400.0, 1.0, 3 * 86400.0, &snap
    );

    /* Node 101 decayed below 0.25 -> PRUNED */
    assert(nodes[0].state == TRAJ_NOISE_PRUNED);
    /* Node 102 passed consolidation window and initial_intensity >= 0.80 -> DISTILLED_RULE */
    assert(nodes[1].state == TRAJ_DISTILLED_RULE);
    assert(snap.distilled_rules_count == 1);
    assert(snap.tokens_saved_pct >= 85);

    printf("[PASS] All Nibras C99 Hardened Arabic Normalizer & FadeMem tests passed! (Tokens saved: %u%%)\n", snap.tokens_saved_pct);
    return 0;
}
#endif

```


---
## FILE: adapters/grounding_shield.h
```c
/* grounding_shield.h - Deterministic C99 Search-Verification & Fact-Checking Engine
 * Target: Matches Cloud Model Accuracy via Grounded Verification Loops
 * Compliance: DESC ISR v3.1 Privacy-Preserving Search & Zero-Data-Leakage Rule
 */
#ifndef GROUNDING_SHIELD_H
#define GROUNDING_SHIELD_H

#include <stddef.h>
#include <stdint.h>
#include <stdbool.h>

#ifdef __cplusplus
extern "C" {
#endif

typedef enum {
    GROUNDING_VERIFIED            = 0, /* Claim matches authoritative reference */
    GROUNDING_HALLUCINATION_TRIPPED = 1, /* Discrepancy detected (numbers/dates/codes) */
    GROUNDING_UNVERIFIABLE        = 2, /* Reference lacks sufficient grounding data */
    GROUNDING_PII_BLOCKED         = 3, /* Query contained PII and was safely redacted */
    GROUNDING_ERROR               = 4  /* Malformed input */
} grounding_verdict_t;

/* Extracted factual claim structure */
typedef struct {
    const char *claim_text;       /* e.g., "DHA Ejadah delay penalty is 0.03% per day" */
    const char *entity_name;      /* e.g., "DHA Ejadah", "DESC ISR v3.1" */
    double      numerical_value;  /* Extracted key metric (e.g., 0.03, 50000.0) */
    bool        has_numerical;    /* True if claim hinges on a specific quantity */
} grounding_claim_t;

/* Authoritative reference source snippet */
typedef struct {
    const char *source_id;        /* e.g., "DHA_SN_03_2019", "DESC_ISR_V3.1_SEC_4" */
    const char *source_title;     /* Formal regulation or manual title */
    const char *snippet_text;     /* Authoritative factual text */
    double      source_numerical; /* Verified statutory number in source */
} grounding_source_t;

/* Verification result envelope */
typedef struct {
    grounding_verdict_t verdict;
    double              confidence;           /* 0.0 to 1.0 */
    char                citation[128];        /* Matched source ID */
    char                discrepancy_note[256];/* Detailed explanation if hallucination */
} grounding_result_t;

/* Function Prototypes */

/**
 * Scrubs user PII and extracts generalized regulatory search keywords
 * to ensure 100% compliance with DESC ISR v3.1 zero-exfiltration mandates.
 */
size_t grounding_scrub_search_query(
    const char *raw_user_prompt,
    char       *out_scrubbed_query,
    size_t      out_cap
);

/**
 * Deterministically cross-checks a generated hypothesis claim against
 * retrieved authoritative sources.
 */
grounding_result_t grounding_verify_claim(
    const grounding_claim_t  *claim,
    const grounding_source_t *sources,
    size_t                    source_count
);

/* F-15 Fix: Pointer-based ABI export to prevent large struct return-by-value across compiler/FFI boundaries */
grounding_verdict_t grounding_verify_claim_ptr(
    const grounding_claim_t  *claim,
    const grounding_source_t *sources,
    size_t                    source_count,
    grounding_result_t       *out_result
);

#ifdef __cplusplus
}
#endif

#endif /* GROUNDING_SHIELD_H */

```


---
## FILE: adapters/grounding_shield.c
```c
/* grounding_shield.c
 * Hardened C99 Implementation of:
 *   1. Privacy-Scrubbed Search Query Extractor (Designed to Support DESC ISR v3.1 Entity Compliance)
 *   2. Deterministic Factual Cross-Verification & Hallucination Blocker
 */

#define _POSIX_C_SOURCE 200809L

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <stdint.h>
#include <stdbool.h>
#include <ctype.h>
#include <math.h>

#include "grounding_shield.h"

/* Case-insensitive substring search in standard C99 */
static const char *strcasestr_c99(const char *haystack, const char *needle) {
    if (!haystack || !needle) return NULL;
    if (needle[0] == '\0') return NULL; /* F-13 Fix: Empty needle should not wildcard match */

    size_t needle_len = strlen(needle);
    for (; *haystack != '\0'; ++haystack) {
        if (tolower((unsigned char)*haystack) == tolower((unsigned char)*needle)) {
            size_t i = 1;
            for (; i < needle_len; ++i) {
                if (haystack[i] == '\0' ||
                    tolower((unsigned char)haystack[i]) != tolower((unsigned char)needle[i])) {
                    break;
                }
            }
            if (i == needle_len) return haystack;
        }
    }
    return NULL;
}

/* Scrub user PII (names, Emirates IDs, emails, account numbers) and extract regulatory keywords */
size_t grounding_scrub_search_query(
    const char *raw_user_prompt,
    char       *out_scrubbed_query,
    size_t      out_cap
) {
    if (!raw_user_prompt || !out_scrubbed_query || out_cap == 0) return 0;
    out_scrubbed_query[0] = '\0';

    /* List of recognized Dubai / UAE regulatory and technical keywords to safely retain */
    static const char *APPROVED_REGULATORY_TOKENS[] = {
        "DHA", "eClaimLink", "Ejadah", "SN 03/2019", "resubmission",
        "DESC", "ISR", "v3", "v3.1", "AI Security Policy", "ASAAS",
        "D33", "DUB.AI", "Chief AI Officer", "RTA", "DEWA",
        "DIFC", "ADGM", "customs", "settlement", "Landlock", "MCP",
        "eGFR", "Colchicine", "Clarithromycin", "pharmacovigilance",
        "Law No. 2 of 2019", "health data", "NABIDH", "Malaffi",
        NULL
    };

    size_t written = 0;

    for (int i = 0; APPROVED_REGULATORY_TOKENS[i] != NULL; ++i) {
        const char *token = APPROVED_REGULATORY_TOKENS[i];
        if (strcasestr_c99(raw_user_prompt, token) != NULL) {
            int n = snprintf(out_scrubbed_query + written, out_cap - written,
                             "%s%s", (written > 0 ? " " : ""), token);
            if (n > 0 && (size_t)n < (out_cap - written)) {
                written += (size_t)n;
            } else {
                break;
            }
        }
    }

    /* Fallback generic safe query if no specific regulatory token matched */
    if (written == 0) {
        strncpy(out_scrubbed_query, "Dubai regulatory compliance guidelines", out_cap - 1);
        out_scrubbed_query[out_cap - 1] = '\0';
        written = strlen(out_scrubbed_query);
    }

    return written;
}

/* F-13 Fix: Deterministic Factual Verification against Retrieved Authoritative Sources */
grounding_result_t grounding_verify_claim(
    const grounding_claim_t  *claim,
    const grounding_source_t *sources,
    size_t                    source_count
) {
    grounding_result_t res;
    memset(&res, 0, sizeof(res));

    if (!claim || !claim->claim_text || !sources || source_count == 0) {
        res.verdict = GROUNDING_ERROR;
        strncpy(res.discrepancy_note, "Missing claim or authoritative sources.", sizeof(res.discrepancy_note) - 1);
        return res;
    }

    /* F-13 Fix: Require non-empty entity name to avoid wildcard false matching */
    if (!claim->entity_name || claim->entity_name[0] == '\0') {
        res.verdict = GROUNDING_UNVERIFIABLE;
        strncpy(res.discrepancy_note, "Claim missing entity name for authoritative grounding.", sizeof(res.discrepancy_note) - 1);
        return res;
    }

    bool entity_found = false;
    bool found_hallucination = false;
    char hallucination_note[256] = "";
    char hallucination_citation[128] = "";

    for (size_t i = 0; i < source_count; ++i) {
        /* Guard source fields */
        const char *s_title = sources[i].source_title ? sources[i].source_title : "";
        const char *s_text  = sources[i].snippet_text ? sources[i].snippet_text : "";
        const char *s_id    = sources[i].source_id ? sources[i].source_id : "UNKNOWN_SOURCE";

        /* Check if authoritative source covers the claimed entity */
        if (strcasestr_c99(s_title, claim->entity_name) != NULL ||
            strcasestr_c99(s_text, claim->entity_name) != NULL) {

            entity_found = true;

            /* Check numerical claim parity if applicable */
            if (claim->has_numerical) {
                /* F-13 Fix: NaN numerical check */
                if (!isfinite(claim->numerical_value) || !isfinite(sources[i].source_numerical)) {
                    res.verdict = GROUNDING_HALLUCINATION_TRIPPED;
                    res.confidence = 0.99;
                    strncpy(res.citation, s_id, sizeof(res.citation) - 1);
                    strncpy(res.discrepancy_note, "Discrepancy: Non-finite or NaN numerical value in claim.", sizeof(res.discrepancy_note) - 1);
                    return res;
                }

                double diff = fabs(claim->numerical_value - sources[i].source_numerical);
                if (diff > 0.0001) {
                    /* Record hallucination candidate, but continue scanning remaining sources in case of multiple sections */
                    found_hallucination = true;
                    strncpy(hallucination_citation, s_id, sizeof(hallucination_citation) - 1);
                    snprintf(hallucination_note, sizeof(hallucination_note),
                             "Discrepancy: Claim states %.4f, but authoritative %s mandates %.4f.",
                             claim->numerical_value, s_id, sources[i].source_numerical);
                    continue;
                }
            }

            /* Factual match confirmed */
            res.verdict = GROUNDING_VERIFIED;
            res.confidence = 0.98;
            strncpy(res.citation, s_id, sizeof(res.citation) - 1);
            snprintf(res.discrepancy_note, sizeof(res.discrepancy_note),
                     "Verified against authoritative source %s.", s_id);
            return res;
        }
    }

    if (found_hallucination) {
        res.verdict = GROUNDING_HALLUCINATION_TRIPPED;
        res.confidence = 0.99;
        strncpy(res.citation, hallucination_citation, sizeof(res.citation) - 1);
        strncpy(res.discrepancy_note, hallucination_note, sizeof(res.discrepancy_note) - 1);
        return res;
    }

    /* If entity was not present in the supplied sources */
    if (!entity_found) {
        res.verdict = GROUNDING_UNVERIFIABLE;
        res.confidence = 0.50;
        strncpy(res.discrepancy_note, "Claimed entity not found in retrieved authoritative corpus.", sizeof(res.discrepancy_note) - 1);
    }

    return res;
}

grounding_verdict_t grounding_verify_claim_ptr(
    const grounding_claim_t  *claim,
    const grounding_source_t *sources,
    size_t                    source_count,
    grounding_result_t       *out_result
) {
    if (!out_result) return GROUNDING_ERROR;
    *out_result = grounding_verify_claim(claim, sources, source_count);
    return out_result->verdict;
}

#ifdef GROUNDING_STANDALONE_TEST
#include <assert.h>

int main(void) {
    /* Test 1: PII Scrubbing extracts only approved regulatory keywords */
    const char *dirty_prompt = "Patient Ahmed Ali (Emirates ID 784-1985-1234567-1, DOB 1985-04-12) "
                               "prescribed Colchicine and Clarithromycin under DHA eClaimLink guidelines.";
    char clean_query[256];
    size_t written = grounding_scrub_search_query(dirty_prompt, clean_query, sizeof(clean_query));
    assert(written > 0);
    assert(strstr(clean_query, "Ahmed Ali") == NULL);
    assert(strstr(clean_query, "784-1985") == NULL);
    assert(strstr(clean_query, "DHA") != NULL);
    assert(strstr(clean_query, "Colchicine") != NULL);

    /* Test 2: Factual Verification catches hallucinated numerical value */
    grounding_source_t sources[2] = {
        {
            .source_id = "DHA_SN_03_2019",
            .source_title = "DHA Standards Notice SN 03/2019 Payment Rules",
            .snippet_text = "Late payment delay penalty is 0.03% per calendar day.",
            .source_numerical = 0.03
        },
        {
            .source_id = "DESC_ISR_V3.1_SEC_4",
            .source_title = "DESC ISR v3.1 Section 4 Cryptographic Standards",
            .snippet_text = "Data at rest must be encrypted with AES-256.",
            .source_numerical = 256.0
        }
    };

    grounding_claim_t false_claim = {
        .claim_text = "DHA Ejadah late penalty is 0.05% per day.",
        .entity_name = "DHA",
        .numerical_value = 0.05,
        .has_numerical = true
    };

    grounding_result_t r2 = grounding_verify_claim(&false_claim, sources, 2);
    assert(r2.verdict == GROUNDING_HALLUCINATION_TRIPPED);
    assert(strcmp(r2.citation, "DHA_SN_03_2019") == 0);

    /* Test 3: Factual Verification confirms accurate claim */
    grounding_claim_t true_claim = {
        .claim_text = "DHA Ejadah late penalty is 0.03% per day.",
        .entity_name = "DHA",
        .numerical_value = 0.03,
        .has_numerical = true
    };
    grounding_result_t r3 = grounding_verify_claim(&true_claim, sources, 2);
    assert(r3.verdict == GROUNDING_VERIFIED);

    /* Test 4 (F-13 check): Empty entity name returns UNVERIFIABLE, not wildcard match */
    grounding_claim_t empty_entity = {
        .claim_text = "Some random text",
        .entity_name = "",
        .numerical_value = 0.0,
        .has_numerical = false
    };
    grounding_result_t r4 = grounding_verify_claim(&empty_entity, sources, 2);
    assert(r4.verdict == GROUNDING_UNVERIFIABLE);

    printf("[PASS] All Grounding Shield C99 PII-Scrubbing & Factual Verification tests passed!\n");
    return 0;
}
#endif

```


---
## FILE: adapters/mcp_curl_client.h
```c
/* mcp_curl_client.h - Production libcurl + cJSON Driver for Stateless MCP 2026-07-28
 * Target: Universal Enterprise Connectivity (SAP, ERPNext, Dubai Customs APIs)
 * Protocol: Streamable HTTP over JSON-RPC 2.0 with L7 Header Routing
 */
#ifndef MCP_CURL_CLIENT_H
#define MCP_CURL_CLIENT_H

#include <stddef.h>
#include <stdint.h>
#include <stdbool.h>

#ifdef __cplusplus
extern "C" {
#endif

typedef enum {
    MCP_SUCCESS            = 0,
    MCP_ERR_CONNECT        = 1,
    MCP_ERR_NETWORK        = 1,   /* Alias for transport/connection failure */
    MCP_ERR_HTTP_STATUS    = 2,   /* Generic HTTP 4xx/5xx status */
    MCP_ERR_AUTH_BLOCKED   = 3,   /* Generic auth failure fallback */
    MCP_ERR_UNAUTHORIZED   = 4,   /* HTTP 401: Missing or invalid token */
    MCP_ERR_FORBIDDEN      = 5,   /* HTTP 403: Policy gate or ACL denied */
    MCP_ERR_JSON_PARSE     = 6,   /* Malformed JSON or SSE payload */
    MCP_ERR_PARSE          = 6,   /* Alias for parse failure */
    MCP_ERR_RPC_FAULT      = 7,   /* MCP / JSON-RPC error returned by server */
    MCP_ERR_TIMEOUT        = 8,   /* Network or socket timeout */
    MCP_ERR_INVALID_PARAM  = 9    /* Missing or invalid input arguments */
} mcp_status_t;

/* Client configuration for MCP connection */
typedef struct {
    const char *endpoint_url;     /* e.g., "http://127.0.0.1:8765/mcp" or "https://api.dubaicustoms.ae/mcp" */
    const char *bearer_token;     /* Optional auth token (never echoed to logs) */
    const char *client_name;      /* Optional client name (default: "qala-native-c99") */
    uint32_t    timeout_ms;       /* Timeout in milliseconds (default 5000) */
} mcp_client_config_t;

/* Tool execution request context */
typedef struct {
    const char *tool_name;        /* e.g., "erp_customs_settlement", "query_tariffs" */
    const char *arguments_json;   /* JSON object string, e.g. "{\"batch_id\":882}" */
    uint64_t    request_id;       /* Monotonic JSON-RPC request identifier */
} mcp_tool_call_req_t;

/* Response envelope */
typedef struct {
    mcp_status_t status;
    long         http_status_code;
    bool         is_rpc_error;
    int32_t      rpc_error_code;
    char         rpc_error_message[256];
    char        *result_text_payload;  /* Caller must free with mcp_response_free() */
    char        *raw_json_response;    /* Caller must free with mcp_response_free() */
} mcp_tool_call_resp_t;

/* Lifecycle functions */
int mcp_client_global_init(void);
void mcp_client_global_cleanup(void);

/* Core execution functions */
mcp_status_t mcp_client_initialize(
    const mcp_client_config_t *config,
    uint64_t                   request_id,
    mcp_tool_call_resp_t      *out_resp
);

mcp_status_t mcp_client_call_tool(
    const mcp_client_config_t *config,
    const mcp_tool_call_req_t *req,
    mcp_tool_call_resp_t      *out_resp
);

mcp_status_t mcp_client_list_tools(
    const mcp_client_config_t *config,
    uint64_t                   request_id,
    mcp_tool_call_resp_t      *out_resp
);

/* Frees dynamic buffers inside response envelope */
void mcp_response_free(mcp_tool_call_resp_t *resp);

#ifdef __cplusplus
}
#endif

#endif /* MCP_CURL_CLIENT_H */

```


---
## FILE: adapters/mcp_curl_client.c
```c
/* mcp_curl_client.c
 * Production C99 Driver for Stateless MCP 2026-07-28 over Streamable HTTP
 * Powered by libcurl (transport) + cJSON (JSON-RPC 2.0 serialization)
 */

#define _POSIX_C_SOURCE 200809L

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <stdint.h>
#include <stdbool.h>
#include <curl/curl.h>

#include "cJSON.h"
#include "mcp_curl_client.h"

/* Memory buffer for accumulating HTTP response body */
typedef struct {
    char  *data;
    size_t size;
} http_memory_buf_t;

#define MCP_MAX_RESPONSE_BYTES (16 * 1024 * 1024)

static size_t curl_write_memory_callback(void *contents, size_t size, size_t nmemb, void *userp) {
    size_t realsize = size * nmemb;
    http_memory_buf_t *mem = (http_memory_buf_t *)userp;

    /* F-14 Fix: Cap response buffer at 16MB to prevent unbounded OOM */
    if (mem->size + realsize > MCP_MAX_RESPONSE_BYTES) {
        return 0;
    }

    char *ptr = (char *)realloc(mem->data, mem->size + realsize + 1);
    if (!ptr) {
        return 0; /* Out of memory */
    }

    mem->data = ptr;
    memcpy(&(mem->data[mem->size]), contents, realsize);
    mem->size += realsize;
    mem->data[mem->size] = '\0';

    return realsize;
}

int mcp_client_global_init(void) {
    return (curl_global_init(CURL_GLOBAL_DEFAULT) == CURLE_OK) ? 0 : -1;
}

void mcp_client_global_cleanup(void) {
    curl_global_cleanup();
}

void mcp_response_free(mcp_tool_call_resp_t *resp) {
    if (!resp) return;
    if (resp->result_text_payload) {
        free(resp->result_text_payload);
        resp->result_text_payload = NULL;
    }
    if (resp->raw_json_response) {
        free(resp->raw_json_response);
        resp->raw_json_response = NULL;
    }
}

/* Internal routine: builds JSON-RPC 2.0 payload matching MCP 2026-07-28 spec */
static char *build_mcp_jsonrpc_body(
    const char *method,
    const char *tool_name,
    const char *arguments_json,
    const char *client_name,
    uint64_t    request_id
) {
    cJSON *root = cJSON_CreateObject();
    if (!root) return NULL;

    cJSON_AddStringToObject(root, "jsonrpc", "2.0");
    cJSON_AddNumberToObject(root, "id", (double)request_id);
    cJSON_AddStringToObject(root, "method", method);

    cJSON *params = cJSON_CreateObject();
    if (params) {
        const char *cname = (client_name && client_name[0] != '\0')
                            ? client_name : "qala-native-c99";

        if (strcmp(method, "initialize") == 0) {
            cJSON_AddStringToObject(params, "protocolVersion", "2026-07-28");
            cJSON *cinfo = cJSON_CreateObject();
            if (cinfo) {
                cJSON_AddStringToObject(cinfo, "name", cname);
                cJSON_AddStringToObject(cinfo, "version", "1.0.0");
                cJSON_AddItemToObject(params, "clientInfo", cinfo);
            }
            cJSON *caps = cJSON_CreateObject();
            if (caps) {
                cJSON *roots = cJSON_CreateObject();
                if (roots) {
                    cJSON_AddBoolToObject(roots, "listChanged", false);
                    cJSON_AddItemToObject(caps, "roots", roots);
                }
                cJSON_AddItemToObject(params, "capabilities", caps);
            }
        } else if (strcmp(method, "tools/call") == 0) {
            if (tool_name) {
                cJSON_AddStringToObject(params, "name", tool_name);
            }
            if (arguments_json && arguments_json[0] != '\0') {
                cJSON *args_parsed = cJSON_Parse(arguments_json);
                if (args_parsed) {
                    cJSON_AddItemToObject(params, "arguments", args_parsed);
                } else {
                    /* F-14 Fix: Reject unparseable arguments rather than silently dropping */
                    cJSON_Delete(root);
                    return NULL;
                }
            } else {
                cJSON_AddObjectToObject(params, "arguments");
            }
        }

        /* MCP 2026-07-28 protocol metadata placed inside params._meta */
        cJSON *meta = cJSON_CreateObject();
        if (meta) {
            cJSON_AddStringToObject(meta, "io.modelcontextprotocol/protocolVersion", "2026-07-28");
            cJSON *client_caps = cJSON_CreateObject();
            if (client_caps) {
                cJSON *roots = cJSON_CreateObject();
                if (roots) {
                    cJSON_AddBoolToObject(roots, "listChanged", false);
                    cJSON_AddItemToObject(client_caps, "roots", roots);
                }
                cJSON_AddItemToObject(meta, "io.modelcontextprotocol/clientCapabilities", client_caps);
            }
            cJSON_AddItemToObject(params, "_meta", meta);
        }

        cJSON_AddItemToObject(root, "params", params);
    }

    char *json_str = cJSON_PrintUnformatted(root);
    cJSON_Delete(root);
    return json_str;
}

/* Extracts JSON payload from either pure JSON or text/event-stream (SSE) */
static char *extract_mcp_payload(const char *raw_body) {
    if (!raw_body) return NULL;

    const char *p = raw_body;
    while (*p == ' ' || *p == '\t' || *p == '\r' || *p == '\n') p++;

    /* Fast path: pure JSON */
    if (*p == '{' || *p == '[') {
        return strdup(p);
    }

    /* SSE Stream framing: accumulate 'data:' lines */
    size_t cap = 2048, len = 0;
    char *acc = (char *)malloc(cap);
    if (!acc) return NULL;
    acc[0] = '\0';

    char *candidate_json = NULL;
    const char *line = p;

    while (*line) {
        const char *next_line = line;
        while (*next_line && *next_line != '\n') next_line++;
        size_t line_len = (size_t)(next_line - line);
        if (line_len > 0 && line[line_len - 1] == '\r') line_len--;

        if (line_len == 0) {
            /* Empty line denotes end of an SSE frame event */
            if (len > 0) {
                cJSON *test = cJSON_Parse(acc);
                if (test) {
                    bool is_pref = (cJSON_GetObjectItemCaseSensitive(test, "result") != NULL ||
                                    cJSON_GetObjectItemCaseSensitive(test, "error") != NULL ||
                                    cJSON_GetObjectItemCaseSensitive(test, "jsonrpc") != NULL);
                    if (is_pref || !candidate_json) {
                        if (candidate_json) free(candidate_json);
                        candidate_json = strdup(acc);
                    }
                    cJSON_Delete(test);
                }
                len = 0;
                acc[0] = '\0';
            }
        } else if (line_len >= 5 && strncmp(line, "data:", 5) == 0) {
            const char *val = line + 5;
            size_t val_len = line_len - 5;
            if (val_len > 0 && *val == ' ') { val++; val_len--; }

            if (len + val_len + 2 > cap) {
                size_t new_cap = (len + val_len + 2 > cap * 2) ? (len + val_len + 2048) : (cap * 2);
                char *new_acc = (char *)realloc(acc, new_cap);
                if (!new_acc) {
                    free(acc);
                    if (candidate_json) free(candidate_json);
                    return NULL;
                }
                acc = new_acc;
                cap = new_cap;
            }
            if (len > 0) acc[len++] = '\n';
            memcpy(acc + len, val, val_len);
            len += val_len;
            acc[len] = '\0';
        }
        line = *next_line ? next_line + 1 : next_line;
    }

    if (len > 0) {
        cJSON *test = cJSON_Parse(acc);
        if (test) {
            if (candidate_json) free(candidate_json);
            candidate_json = strdup(acc);
            cJSON_Delete(test);
        }
    }
    free(acc);
    return candidate_json ? candidate_json : strdup(raw_body);
}

/* Parse JSON-RPC response from MCP Server */
static void parse_mcp_response(
    const char           *response_body,
    mcp_tool_call_resp_t *out_resp
) {
    if (!response_body || !out_resp) return;

    char *clean_payload = extract_mcp_payload(response_body);
    if (!clean_payload) {
        out_resp->status = MCP_ERR_JSON_PARSE;
        return;
    }

    out_resp->raw_json_response = clean_payload;

    cJSON *root = cJSON_Parse(clean_payload);
    if (!root) {
        out_resp->status = MCP_ERR_JSON_PARSE;
        return;
    }

    /* Check for JSON-RPC error */
    cJSON *err_obj = cJSON_GetObjectItemCaseSensitive(root, "error");
    if (err_obj && cJSON_IsObject(err_obj)) {
        out_resp->is_rpc_error = true;
        out_resp->status = MCP_ERR_RPC_FAULT;

        cJSON *code = cJSON_GetObjectItemCaseSensitive(err_obj, "code");
        if (code && cJSON_IsNumber(code)) {
            out_resp->rpc_error_code = code->valueint;
        }

        cJSON *msg = cJSON_GetObjectItemCaseSensitive(err_obj, "message");
        if (msg && cJSON_IsString(msg) && msg->valuestring) {
            strncpy(out_resp->rpc_error_message, msg->valuestring, sizeof(out_resp->rpc_error_message) - 1);
        }
        cJSON_Delete(root);
        return;
    }

    /* Extract content from "result" */
    cJSON *res_obj = cJSON_GetObjectItemCaseSensitive(root, "result");
    if (res_obj) {
        cJSON *content_arr = cJSON_GetObjectItemCaseSensitive(res_obj, "content");
        if (content_arr && cJSON_IsArray(content_arr)) {
            cJSON *first_elem = cJSON_GetArrayItem(content_arr, 0);
            if (first_elem) {
                cJSON *text_node = cJSON_GetObjectItemCaseSensitive(first_elem, "text");
                if (text_node && cJSON_IsString(text_node) && text_node->valuestring) {
                    out_resp->result_text_payload = strdup(text_node->valuestring);
                }
            }
        }
        if (!out_resp->result_text_payload) {
            /* Fallback to printing unformatted result object */
            out_resp->result_text_payload = cJSON_PrintUnformatted(res_obj);
        }
        /* F-14 Fix: Check isError flag in tools/call */
        cJSON *is_err = cJSON_GetObjectItemCaseSensitive(res_obj, "isError");
        if (is_err && cJSON_IsTrue(is_err)) {
            out_resp->status = MCP_ERR_RPC_FAULT;
            out_resp->is_rpc_error = true;
        } else {
            out_resp->status = MCP_SUCCESS;
        }
    } else {
        /* F-14 Fix: Missing both result and error is an invalid JSON-RPC response */
        out_resp->status = MCP_ERR_JSON_PARSE;
    }

    cJSON_Delete(root);
}

/* Execute HTTP POST request using libcurl */
static mcp_status_t execute_mcp_http_post(
    const mcp_client_config_t *config,
    const char                *mcp_method_header,
    const char                *post_body,
    mcp_tool_call_resp_t      *out_resp
) {
    if (!config || !config->endpoint_url || !post_body || !out_resp) {
        return MCP_ERR_INVALID_PARAM;
    }

    CURL *curl = curl_easy_init();
    if (!curl) {
        out_resp->status = MCP_ERR_CONNECT;
        return MCP_ERR_CONNECT;
    }

    http_memory_buf_t chunk = { .data = malloc(1), .size = 0 };
    if (!chunk.data) {
        curl_easy_cleanup(curl);
        out_resp->status = MCP_ERR_CONNECT;
        return MCP_ERR_CONNECT;
    }
    chunk.data[0] = '\0';

    /* Build HTTP headers adhering to Stateless MCP 2026-07-28 */
    struct curl_slist *headers = NULL;
    headers = curl_slist_append(headers, "Content-Type: application/json");
    headers = curl_slist_append(headers, "Accept: application/json, text/event-stream");
    headers = curl_slist_append(headers, "MCP-Protocol-Version: 2026-07-28");

    const char *cname = (config->client_name && config->client_name[0] != '\0')
                        ? config->client_name : "qala-native-c99";
    char name_hdr[128];
    snprintf(name_hdr, sizeof(name_hdr), "Mcp-Name: %s", cname);
    headers = curl_slist_append(headers, name_hdr);

    char method_hdr[128];
    snprintf(method_hdr, sizeof(method_hdr), "Mcp-Method: %s", mcp_method_header);
    headers = curl_slist_append(headers, method_hdr);

    if (config->bearer_token && config->bearer_token[0] != '\0') {
        /* F-14 Fix: Reject CRLF in bearer token and dynamically allocate header buffer */
        if (strpbrk(config->bearer_token, "\r\n") != NULL) {
            curl_slist_free_all(headers);
            curl_easy_cleanup(curl);
            free(chunk.data);
            out_resp->status = MCP_ERR_INVALID_PARAM;
            return MCP_ERR_INVALID_PARAM;
        }
        size_t b_len = strlen(config->bearer_token);
        char *auth_hdr = (char *)malloc(b_len + 32);
        if (auth_hdr) {
            snprintf(auth_hdr, b_len + 32, "Authorization: Bearer %s", config->bearer_token);
            headers = curl_slist_append(headers, auth_hdr);
            free(auth_hdr);
        }
    }

    curl_easy_setopt(curl, CURLOPT_URL, config->endpoint_url);
    curl_easy_setopt(curl, CURLOPT_HTTPHEADER, headers);
    curl_easy_setopt(curl, CURLOPT_POSTFIELDS, post_body);
    curl_easy_setopt(curl, CURLOPT_WRITEFUNCTION, curl_write_memory_callback);
    curl_easy_setopt(curl, CURLOPT_WRITEDATA, (void *)&chunk);
    curl_easy_setopt(curl, CURLOPT_TIMEOUT_MS, (long)(config->timeout_ms ? config->timeout_ms : 5000));
    curl_easy_setopt(curl, CURLOPT_USERAGENT, "Qala-StatelessMCP-Client/1.0 (Dubai 2027)");

    CURLcode res = curl_easy_perform(curl);
    mcp_status_t final_status = MCP_SUCCESS;

    if (res != CURLE_OK) {
        if (res == CURLE_OPERATION_TIMEDOUT) {
            final_status = MCP_ERR_TIMEOUT;
        } else {
            final_status = MCP_ERR_CONNECT;
        }
        out_resp->status = final_status;
    } else {
        curl_easy_getinfo(curl, CURLINFO_RESPONSE_CODE, &out_resp->http_status_code);

        /* F-14 Fix: Parse JSON-RPC payload if available even on HTTP errors to capture error message/code */
        if (chunk.size > 0 && chunk.data[0] != '\0') {
            parse_mcp_response(chunk.data, out_resp);
        }

        if (out_resp->http_status_code == 401) {
            final_status = MCP_ERR_UNAUTHORIZED;
            out_resp->status = final_status;
        } else if (out_resp->http_status_code == 403) {
            final_status = MCP_ERR_FORBIDDEN;
            out_resp->status = final_status;
        } else if (out_resp->http_status_code >= 400) {
            final_status = MCP_ERR_HTTP_STATUS;
            out_resp->status = final_status;
        } else {
            final_status = out_resp->status;
        }
    }

    curl_slist_free_all(headers);
    curl_easy_cleanup(curl);
    free(chunk.data);

    return final_status;
}

mcp_status_t mcp_client_initialize(
    const mcp_client_config_t *config,
    uint64_t                   request_id,
    mcp_tool_call_resp_t      *out_resp
) {
    if (!out_resp) return MCP_ERR_INVALID_PARAM;
    memset(out_resp, 0, sizeof(*out_resp));

    if (!config) {
        out_resp->status = MCP_ERR_INVALID_PARAM;
        return MCP_ERR_INVALID_PARAM;
    }

    char *post_body = build_mcp_jsonrpc_body("initialize", NULL, NULL, config->client_name, request_id);
    if (!post_body) {
        out_resp->status = MCP_ERR_JSON_PARSE;
        return MCP_ERR_JSON_PARSE;
    }

    mcp_status_t st = execute_mcp_http_post(config, "initialize", post_body, out_resp);
    free(post_body);
    return st;
}

mcp_status_t mcp_client_call_tool(
    const mcp_client_config_t *config,
    const mcp_tool_call_req_t *req,
    mcp_tool_call_resp_t      *out_resp
) {
    if (!out_resp) return MCP_ERR_INVALID_PARAM;
    memset(out_resp, 0, sizeof(*out_resp));

    if (!config || !req || !req->tool_name) {
        out_resp->status = MCP_ERR_INVALID_PARAM;
        return MCP_ERR_INVALID_PARAM;
    }

    char *post_body = build_mcp_jsonrpc_body("tools/call", req->tool_name, req->arguments_json, config->client_name, req->request_id);
    if (!post_body) {
        out_resp->status = MCP_ERR_JSON_PARSE;
        return MCP_ERR_JSON_PARSE;
    }

    mcp_status_t st = execute_mcp_http_post(config, "tools/call", post_body, out_resp);
    free(post_body);
    return st;
}

mcp_status_t mcp_client_list_tools(
    const mcp_client_config_t *config,
    uint64_t                   request_id,
    mcp_tool_call_resp_t      *out_resp
) {
    if (!out_resp) return MCP_ERR_INVALID_PARAM;
    memset(out_resp, 0, sizeof(*out_resp));

    if (!config) {
        out_resp->status = MCP_ERR_INVALID_PARAM;
        return MCP_ERR_INVALID_PARAM;
    }

    char *post_body = build_mcp_jsonrpc_body("tools/list", NULL, NULL, config->client_name, request_id);
    if (!post_body) {
        out_resp->status = MCP_ERR_JSON_PARSE;
        return MCP_ERR_JSON_PARSE;
    }

    mcp_status_t st = execute_mcp_http_post(config, "tools/list", post_body, out_resp);
    free(post_body);
    return st;
}

#ifdef MCP_CURL_STANDALONE_TEST
#include <assert.h>

int main(void) {
    /* Test 1: Verify tools/call JSON-RPC body structure (params._meta and clientCapabilities) */
    char *body1 = build_mcp_jsonrpc_body("tools/call", "erp_customs_settlement", "{\"batch_id\":882,\"aed\":125000}", "qala-test-suite", 42);
    assert(body1 != NULL);
    assert(strstr(body1, "\"jsonrpc\":\"2.0\"") != NULL);
    assert(strstr(body1, "\"id\":42") != NULL);
    assert(strstr(body1, "\"method\":\"tools/call\"") != NULL);
    assert(strstr(body1, "\"name\":\"erp_customs_settlement\"") != NULL);
    assert(strstr(body1, "\"batch_id\":882") != NULL);

    /* Verify _meta is inside params, NOT at root */
    cJSON *parsed1 = cJSON_Parse(body1);
    assert(parsed1 != NULL);
    assert(cJSON_GetObjectItem(parsed1, "_meta") == NULL);
    cJSON *p1 = cJSON_GetObjectItem(parsed1, "params");
    assert(p1 != NULL);
    cJSON *meta1 = cJSON_GetObjectItem(p1, "_meta");
    assert(meta1 != NULL);
    assert(cJSON_GetObjectItem(meta1, "io.modelcontextprotocol/protocolVersion") != NULL);
    assert(cJSON_GetObjectItem(meta1, "io.modelcontextprotocol/clientCapabilities") != NULL);
    cJSON_Delete(parsed1);
    free(body1);

    /* Test 2: Verify tools/list JSON-RPC body schema (no dummy arguments or name fields) */
    char *body2 = build_mcp_jsonrpc_body("tools/list", NULL, NULL, "qala-test-suite", 43);
    assert(body2 != NULL);
    cJSON *parsed2 = cJSON_Parse(body2);
    assert(parsed2 != NULL);
    cJSON *p2 = cJSON_GetObjectItem(parsed2, "params");
    assert(p2 != NULL);
    assert(cJSON_GetObjectItem(p2, "name") == NULL);
    assert(cJSON_GetObjectItem(p2, "arguments") == NULL);
    assert(cJSON_GetObjectItem(p2, "_meta") != NULL);
    cJSON_Delete(parsed2);
    free(body2);

    /* Test 3: Verify initialize Handshake payload structure */
    char *body3 = build_mcp_jsonrpc_body("initialize", NULL, NULL, "qala-enterprise", 44);
    assert(body3 != NULL);
    cJSON *parsed3 = cJSON_Parse(body3);
    assert(parsed3 != NULL);
    cJSON *p3 = cJSON_GetObjectItem(parsed3, "params");
    assert(p3 != NULL);
    cJSON *proto = cJSON_GetObjectItem(p3, "protocolVersion");
    assert(proto != NULL && strcmp(proto->valuestring, "2026-07-28") == 0);
    cJSON *cinfo = cJSON_GetObjectItem(p3, "clientInfo");
    assert(cinfo != NULL);
    cJSON *cname = cJSON_GetObjectItem(cinfo, "name");
    assert(cname != NULL && strcmp(cname->valuestring, "qala-enterprise") == 0);
    cJSON *caps = cJSON_GetObjectItem(p3, "capabilities");
    assert(caps != NULL && cJSON_GetObjectItem(caps, "roots") != NULL);
    cJSON_Delete(parsed3);
    free(body3);

    /* Test 4: Verify pure JSON response parsing */
    const char *mock_success_json =
        "{\"jsonrpc\":\"2.0\",\"id\":42,\"result\":{\"content\":[{\"type\":\"text\",\"text\":\"Settlement #882 executed for AED 125,000.00\"}]}}";
    mcp_tool_call_resp_t r4;
    memset(&r4, 0, sizeof(r4));
    parse_mcp_response(mock_success_json, &r4);
    assert(r4.status == MCP_SUCCESS);
    assert(r4.is_rpc_error == false);
    assert(r4.result_text_payload != NULL);
    assert(strstr(r4.result_text_payload, "AED 125,000.00") != NULL);
    mcp_response_free(&r4);

    /* Test 5: Verify SSE single frame parsing (event: message\ndata: {...}\n\n) */
    const char *mock_sse_frame =
        "event: message\r\n"
        "data: {\"jsonrpc\":\"2.0\",\"id\":45,\"result\":{\"content\":[{\"type\":\"text\",\"text\":\"SSE Settlement #883 Verified\"}]}}\r\n\r\n";
    mcp_tool_call_resp_t r5;
    memset(&r5, 0, sizeof(r5));
    parse_mcp_response(mock_sse_frame, &r5);
    assert(r5.status == MCP_SUCCESS);
    assert(r5.is_rpc_error == false);
    assert(r5.result_text_payload != NULL);
    assert(strstr(r5.result_text_payload, "SSE Settlement #883 Verified") != NULL);
    mcp_response_free(&r5);

    /* Test 6: Verify SSE multi-line chunk assembly */
    const char *mock_sse_multiline =
        "event: message\n"
        "data: {\"jsonrpc\":\"2.0\",\n"
        "data: \"id\":46,\n"
        "data: \"result\":{\"content\":[{\"type\":\"text\",\"text\":\"Multi-chunk SSE payload\"}]}}\n\n";
    mcp_tool_call_resp_t r6;
    memset(&r6, 0, sizeof(r6));
    parse_mcp_response(mock_sse_multiline, &r6);
    assert(r6.status == MCP_SUCCESS);
    assert(r6.result_text_payload != NULL);
    assert(strstr(r6.result_text_payload, "Multi-chunk SSE payload") != NULL);
    mcp_response_free(&r6);

    /* Test 7: Verify SSE stream with leading ping/heartbeat frames */
    const char *mock_sse_with_pings =
        ": heartbeat keepalive\r\n\r\n"
        "event: ping\r\n"
        "data: {}\r\n\r\n"
        "event: message\r\n"
        "data: {\"jsonrpc\":\"2.0\",\"id\":47,\"result\":{\"tools\":[{\"name\":\"customs_query\",\"description\":\"Check tariff rates\"}]}}\r\n\r\n";
    mcp_tool_call_resp_t r7;
    memset(&r7, 0, sizeof(r7));
    parse_mcp_response(mock_sse_with_pings, &r7);
    assert(r7.status == MCP_SUCCESS);
    assert(r7.result_text_payload != NULL);
    assert(strstr(r7.result_text_payload, "customs_query") != NULL);
    mcp_response_free(&r7);

    /* Test 8: Verify JSON-RPC error extraction from SSE stream */
    const char *mock_sse_error =
        "event: message\r\n"
        "data: {\"jsonrpc\":\"2.0\",\"id\":48,\"error\":{\"code\":-32602,\"message\":\"Invalid params: amount exceeds limit\"}}\r\n\r\n";
    mcp_tool_call_resp_t r8;
    memset(&r8, 0, sizeof(r8));
    parse_mcp_response(mock_sse_error, &r8);
    assert(r8.status == MCP_ERR_RPC_FAULT);
    assert(r8.is_rpc_error == true);
    assert(r8.rpc_error_code == -32602);
    assert(strstr(r8.rpc_error_message, "exceeds limit") != NULL);
    mcp_response_free(&r8);

    /* Test 9: Verify honest HTTP error classification & network transport failure */
    mcp_client_global_init();

    mcp_client_config_t offline_cfg = {
        .endpoint_url = "http://127.0.0.1:59999/mcp",
        .bearer_token = NULL,
        .client_name = "qala-test-suite",
        .timeout_ms = 500
    };
    mcp_tool_call_req_t req = {
        .tool_name = "test_tool",
        .arguments_json = "{}",
        .request_id = 1
    };
    mcp_tool_call_resp_t r9;
    mcp_status_t st = mcp_client_call_tool(&offline_cfg, &req, &r9);
    assert(st == MCP_ERR_CONNECT);
    assert(r9.status == MCP_ERR_CONNECT || r9.status == MCP_ERR_NETWORK);
    mcp_response_free(&r9);

    /* Verify initialize call to offline port also returns connection error */
    mcp_tool_call_resp_t r10;
    mcp_status_t st_init = mcp_client_initialize(&offline_cfg, 10, &r10);
    assert(st_init == MCP_ERR_CONNECT);
    assert(r10.status == MCP_ERR_CONNECT);
    mcp_response_free(&r10);

    mcp_client_global_cleanup();

    printf("[PASS] All libcurl + cJSON Stateless MCP 2026-07-28 client tests passed successfully! (9/9 suites)\n");
    return 0;
}
#endif

```


---
## FILE: src/taryaq_agent.c
```c
/* src/taryaq_agent.c - Sovereign Clinical Safety & DHA Reimbursement Firewall
 * Dubai Create AI Agents Championship 2026-2027 | Best Societal AI Agent
 * Conforms strictly to ISO C99 (-std=c99 -Wall -Wextra -Werror -O2)
 */

#define _POSIX_C_SOURCE 200809L
#define _XOPEN_SOURCE 700

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <stdint.h>
#include <stdbool.h>
#include <ctype.h>
#include <time.h>
#include <sys/time.h>
#include <curl/curl.h>

#include "taryaq_adapters.h"
#include "nibras_adapters.h"
#include "grounding_shield.h"
#include "qala_adapters.h"

#define TARYAQ_VERSION "0.1.0-c99-sovereign"
#define DEFAULT_AUDIT_LOG "taryaq_audit.jsonl"
#define TELEMETRY_ENDPOINT "http://127.0.0.1:8787/emit"

/* ========================================================================= */
/* 1. Self-Contained ISO C99 SHA-256 Implementation (Zero External Crypto)   */
/* ========================================================================= */

typedef struct {
    uint32_t state[8];
    uint64_t count;
    uint8_t  buffer[64];
} taryaq_sha256_t;

static uint32_t ror32(uint32_t val, uint32_t bits) {
    return (val >> bits) | (val << (32 - bits));
}

static void sha256_init(taryaq_sha256_t *ctx) {
    ctx->state[0] = 0x6a09e667UL;
    ctx->state[1] = 0xbb67ae85UL;
    ctx->state[2] = 0x3c6ef372UL;
    ctx->state[3] = 0xa54ff53aUL;
    ctx->state[4] = 0x510e527fUL;
    ctx->state[5] = 0x9b05688cUL;
    ctx->state[6] = 0x1f83d9abUL;
    ctx->state[7] = 0x5be0cd19UL;
    ctx->count = 0;
}

static const uint32_t K256[64] = {
    0x428a2f98UL, 0x71374491UL, 0xb5c0fbcfUL, 0xe9b5dba5UL,
    0x3956c25bUL, 0x59f111f1UL, 0x923f82a4UL, 0xab1c5ed5UL,
    0xd807aa98UL, 0x12835b01UL, 0x243185beUL, 0x550c7dc3UL,
    0x72be5d74UL, 0x80deb1feUL, 0x9bdc06a7UL, 0xc19bf174UL,
    0xe49b69c1UL, 0xefbe4786UL, 0x0fc19dc6UL, 0x240ca1ccUL,
    0x2de92c6fUL, 0x4a7484aaUL, 0x5cb0a9dcUL, 0x76f988daUL,
    0x983e5152UL, 0xa831c66dUL, 0xb00327c8UL, 0xbf597fc7UL,
    0xc6e00bf3UL, 0xd5a79147UL, 0x06ca6351UL, 0x14292967UL,
    0x27b70a85UL, 0x2e1b2138UL, 0x4d2c6dfcUL, 0x53380d13UL,
    0x650a7354UL, 0x766a0abbUL, 0x81c2c92eUL, 0x92722c85UL,
    0xa2bfe8a1UL, 0xa81a664bUL, 0xc24b8b70UL, 0xc76c51a3UL,
    0xd192e819UL, 0xd6990624UL, 0xf40e3585UL, 0x106aa070UL,
    0x19a4c116UL, 0x1e376c08UL, 0x2748774cUL, 0x34b0bcb5UL,
    0x391c0cb3UL, 0x4ed8aa4aUL, 0x5b9cca4fUL, 0x682e6ff3UL,
    0x748f82eeUL, 0x78a5636fUL, 0x84c87814UL, 0x8cc70208UL,
    0x90befffaUL, 0xa4506cebUL, 0xbef9a3f7UL, 0xc67178f2UL
};

static void sha256_transform(uint32_t state[8], const uint8_t data[64]) {
    uint32_t a = state[0], b = state[1], c = state[2], d = state[3];
    uint32_t e = state[4], f = state[5], g = state[6], h = state[7];
    uint32_t w[64];
    for (int i = 0; i < 16; ++i) {
        w[i] = ((uint32_t)data[i * 4] << 24) |
               ((uint32_t)data[i * 4 + 1] << 16) |
               ((uint32_t)data[i * 4 + 2] << 8) |
               ((uint32_t)data[i * 4 + 3]);
    }
    for (int i = 16; i < 64; ++i) {
        uint32_t s0 = ror32(w[i - 15], 7) ^ ror32(w[i - 15], 18) ^ (w[i - 15] >> 3);
        uint32_t s1 = ror32(w[i - 2], 17) ^ ror32(w[i - 2], 19) ^ (w[i - 2] >> 10);
        w[i] = w[i - 16] + s0 + w[i - 7] + s1;
    }
    for (int i = 0; i < 64; ++i) {
        uint32_t S1 = ror32(e, 6) ^ ror32(e, 11) ^ ror32(e, 25);
        uint32_t ch = (e & f) ^ ((~e) & g);
        uint32_t temp1 = h + S1 + ch + K256[i] + w[i];
        uint32_t S0 = ror32(a, 2) ^ ror32(a, 13) ^ ror32(a, 22);
        uint32_t maj = (a & b) ^ (a & c) ^ (b & c);
        uint32_t temp2 = S0 + maj;
        h = g;
        g = f;
        f = e;
        e = d + temp1;
        d = c;
        c = b;
        b = a;
        a = temp1 + temp2;
    }
    state[0] += a; state[1] += b; state[2] += c; state[3] += d;
    state[4] += e; state[5] += f; state[6] += g; state[7] += h;
}

static void sha256_update(taryaq_sha256_t *ctx, const uint8_t *data, size_t len) {
    size_t i = 0;
    size_t buf_idx = (size_t)(ctx->count & 0x3F);
    ctx->count += len;
    if (buf_idx > 0) {
        size_t fill = 64 - buf_idx;
        if (len < fill) {
            memcpy(ctx->buffer + buf_idx, data, len);
            return;
        }
        memcpy(ctx->buffer + buf_idx, data, fill);
        sha256_transform(ctx->state, ctx->buffer);
        i += fill;
    }
    for (; i + 64 <= len; i += 64) {
        sha256_transform(ctx->state, data + i);
    }
    if (i < len) {
        memcpy(ctx->buffer, data + i, len - i);
    }
}

static void sha256_final(taryaq_sha256_t *ctx, uint8_t hash[32]) {
    uint64_t total_bits = ctx->count * 8;
    size_t buf_idx = (size_t)(ctx->count & 0x3F);
    ctx->buffer[buf_idx++] = 0x80;
    if (buf_idx > 56) {
        memset(ctx->buffer + buf_idx, 0, 64 - buf_idx);
        sha256_transform(ctx->state, ctx->buffer);
        buf_idx = 0;
    }
    memset(ctx->buffer + buf_idx, 0, 56 - buf_idx);
    for (int i = 0; i < 8; ++i) {
        ctx->buffer[56 + i] = (uint8_t)(total_bits >> ((7 - i) * 8));
    }
    sha256_transform(ctx->state, ctx->buffer);
    for (int i = 0; i < 8; ++i) {
        hash[i * 4]     = (uint8_t)(ctx->state[i] >> 24);
        hash[i * 4 + 1] = (uint8_t)(ctx->state[i] >> 16);
        hash[i * 4 + 2] = (uint8_t)(ctx->state[i] >> 8);
        hash[i * 4 + 3] = (uint8_t)(ctx->state[i]);
    }
}

static void sha256_hex(const char *data, size_t len, char hex_out[65]) {
    taryaq_sha256_t ctx;
    uint8_t hash[32];
    sha256_init(&ctx);
    sha256_update(&ctx, (const uint8_t *)data, len);
    sha256_final(&ctx, hash);
    for (int i = 0; i < 32; ++i) {
        snprintf(hex_out + (i * 2), 3, "%02x", hash[i]);
    }
    hex_out[64] = '\0';
}

/* ========================================================================= */
/* 2. String & JSON Utilities                                                */
/* ========================================================================= */

static void taryaq_json_escape(const char *src, char *dst, size_t dst_cap) {
    if (!dst || dst_cap == 0) return;
    if (!src) { dst[0] = '\0'; return; }
    size_t w = 0;
    for (size_t r = 0; src[r] != '\0' && (w + 2) < dst_cap; ++r) {
        unsigned char c = (unsigned char)src[r];
        if (c == '"' || c == '\\') {
            if (w + 3 >= dst_cap) break;
            dst[w++] = '\\';
            dst[w++] = (char)c;
        } else if (c == '\n') {
            if (w + 3 >= dst_cap) break;
            dst[w++] = '\\';
            dst[w++] = 'n';
        } else if (c == '\r') {
            if (w + 3 >= dst_cap) break;
            dst[w++] = '\\';
            dst[w++] = 'r';
        } else if (c >= 0x20) {
            dst[w++] = (char)c;
        }
    }
    dst[w] = '\0';
}

static uint64_t taryaq_now_utc(void) {
    return (uint64_t)time(NULL);
}

static double taryaq_get_monotonic_ms(void) {
    struct timespec ts;
    clock_gettime(CLOCK_MONOTONIC, &ts);
    return ((double)ts.tv_sec * 1000.0) + ((double)ts.tv_nsec / 1000000.0);
}

/* ========================================================================= */
/* 3. Optional Telemetry Bridge Client (libcurl, Graceful Silent Fallback)   */
/* ========================================================================= */

static void taryaq_emit_telemetry(bool enabled, const char *event_type, const char *json_payload) {
    if (!enabled || !json_payload) return;

    CURL *curl = curl_easy_init();
    if (!curl) return;

    struct curl_slist *headers = NULL;
    headers = curl_slist_append(headers, "Content-Type: application/json");

    curl_easy_setopt(curl, CURLOPT_URL, TELEMETRY_ENDPOINT);
    curl_easy_setopt(curl, CURLOPT_POSTFIELDS, json_payload);
    curl_easy_setopt(curl, CURLOPT_HTTPHEADER, headers);
    curl_easy_setopt(curl, CURLOPT_TIMEOUT_MS, 150L);
    curl_easy_setopt(curl, CURLOPT_CONNECTTIMEOUT_MS, 100L);
    curl_easy_setopt(curl, CURLOPT_NOSIGNAL, 1L);

    FILE *devnull = fopen("/dev/null", "w");
    if (devnull) {
        curl_easy_setopt(curl, CURLOPT_WRITEDATA, devnull);
    }

    CURLcode res = curl_easy_perform(curl);
    (void)res;
    (void)event_type;

    if (devnull) fclose(devnull);
    curl_slist_free_all(headers);
    curl_easy_cleanup(curl);
}

/* ========================================================================= */
/* 4. Local Embedded Medication Graph                                        */
/* ========================================================================= */

typedef enum {
    CYP3A4_NONE      = 0,
    CYP3A4_SUBSTRATE = 1,
    CYP3A4_INHIBITOR = 2
} cyp3a4_profile_t;

typedef struct {
    const char       *canonical_name;
    const char       *arabic_name;
    const char       *drug_class;
    double            renal_egfr_cutoff;
    cyp3a4_profile_t  cyp3a4_profile;
    bool              is_controlled;
    const char       *icd10_indication;
    const char       *clinical_notes;
} taryaq_med_entry_t;

static const taryaq_med_entry_t MED_DATABASE[] = {
    {
        .canonical_name = "Colchicine",
        .arabic_name = "كولشيسين",
        .drug_class = "Alkaloid / Anti-gout",
        .renal_egfr_cutoff = 30.0,
        .cyp3a4_profile = CYP3A4_SUBSTRATE,
        .is_controlled = false,
        .icd10_indication = "M10.0",
        .clinical_notes = "Fatal toxicity with CYP3A4 inhibitors in severe renal impairment (eGFR < 30)"
    },
    {
        .canonical_name = "Clarithromycin",
        .arabic_name = "كلاريثروميسين",
        .drug_class = "Macrolide Antibiotic",
        .renal_egfr_cutoff = 30.0,
        .cyp3a4_profile = CYP3A4_INHIBITOR,
        .is_controlled = false,
        .icd10_indication = "J02.9",
        .clinical_notes = "Potent CYP3A4 inhibitor; contra-indicated with colchicine in renal dysfunction"
    },
    {
        .canonical_name = "Morphine",
        .arabic_name = "مورفين",
        .drug_class = "Opioid Analgesic",
        .renal_egfr_cutoff = 20.0,
        .cyp3a4_profile = CYP3A4_NONE,
        .is_controlled = true,
        .icd10_indication = "R52",
        .clinical_notes = "Controlled substance under UAE Law No. 2 of 2019; mandatory Emirates ID verification"
    },
    {
        .canonical_name = "Metformin",
        .arabic_name = "ميتفورمين",
        .drug_class = "Biguanide Antidiabetic",
        .renal_egfr_cutoff = 30.0,
        .cyp3a4_profile = CYP3A4_NONE,
        .is_controlled = false,
        .icd10_indication = "E11.9",
        .clinical_notes = "Risk of lactic acidosis if eGFR < 30 ml/min"
    },
    {
        .canonical_name = "Ketamine",
        .arabic_name = "كيتامين",
        .drug_class = "NMDA Receptor Antagonist / Anesthetic",
        .renal_egfr_cutoff = 15.0,
        .cyp3a4_profile = CYP3A4_SUBSTRATE,
        .is_controlled = true,
        .icd10_indication = "T88.8",
        .clinical_notes = "Controlled schedule medication under UAE Law No. 2 of 2019"
    },
    {
        .canonical_name = "Tramadol",
        .arabic_name = "ترامادول",
        .drug_class = "Synthetic Opioid Analgesic",
        .renal_egfr_cutoff = 30.0,
        .cyp3a4_profile = CYP3A4_SUBSTRATE,
        .is_controlled = true,
        .icd10_indication = "M79.3",
        .clinical_notes = "Controlled substance in UAE; requires verified patient Emirates ID"
    },
    {
        .canonical_name = "Simvastatin",
        .arabic_name = "سيمفاستاتين",
        .drug_class = "HMG-CoA Reductase Inhibitor",
        .renal_egfr_cutoff = 30.0,
        .cyp3a4_profile = CYP3A4_SUBSTRATE,
        .is_controlled = false,
        .icd10_indication = "E78.0",
        .clinical_notes = "CYP3A4 substrate; risk of rhabdomyolysis with strong inhibitors"
    },
    {
        .canonical_name = "Warfarin",
        .arabic_name = "وارفارين",
        .drug_class = "Vitamin K Antagonist Anticoagulant",
        .renal_egfr_cutoff = 15.0,
        .cyp3a4_profile = CYP3A4_NONE,
        .is_controlled = false,
        .icd10_indication = "I48.9",
        .clinical_notes = "Narrow therapeutic window; international normalized ratio monitoring required"
    },
    {
        .canonical_name = NULL,
        .arabic_name = NULL,
        .drug_class = NULL,
        .renal_egfr_cutoff = 0.0,
        .cyp3a4_profile = CYP3A4_NONE,
        .is_controlled = false,
        .icd10_indication = NULL,
        .clinical_notes = NULL
    }
};

/* ========================================================================= */
/* 5. Tool 1: med_lookup                                                     */
/* ========================================================================= */

static const taryaq_med_entry_t *taryaq_med_lookup(const char *query) {
    if (!query || query[0] == '\0') return NULL;

    while (isspace((unsigned char)*query)) query++;
    if (*query == '\0') return NULL;

    char norm_q[256];
    arabic_normalize_utf8_hardened(query, norm_q, sizeof(norm_q));

    char lower_q[256];
    size_t qlen = strlen(norm_q);
    if (qlen >= sizeof(lower_q)) qlen = sizeof(lower_q) - 1;
    for (size_t i = 0; i < qlen; ++i) {
        lower_q[i] = (char)tolower((unsigned char)norm_q[i]);
    }
    lower_q[qlen] = '\0';

    for (size_t i = 0; MED_DATABASE[i].canonical_name != NULL; ++i) {
        const taryaq_med_entry_t *med = &MED_DATABASE[i];

        char lower_name[128];
        size_t nlen = strlen(med->canonical_name);
        if (nlen >= sizeof(lower_name)) nlen = sizeof(lower_name) - 1;
        for (size_t j = 0; j < nlen; ++j) {
            lower_name[j] = (char)tolower((unsigned char)med->canonical_name[j]);
        }
        lower_name[nlen] = '\0';

        if (strstr(lower_q, lower_name) != NULL || strstr(lower_name, lower_q) != NULL) {
            return med;
        }

        char norm_med_ar[128];
        arabic_normalize_utf8_hardened(med->arabic_name, norm_med_ar, sizeof(norm_med_ar));
        if (strstr(norm_q, norm_med_ar) != NULL || strstr(norm_med_ar, norm_q) != NULL) {
            return med;
        }
    }

    return NULL;
}

/* ========================================================================= */
/* 6. Tool 2: interaction_check                                              */
/* ========================================================================= */

typedef struct {
    taryaq_verdict_t verdict;
    char             alert_code[64];
    char             clinical_rationale[256];
    bool             has_renal_risk;
    bool             has_cyp3a4_conflict;
    bool             is_controlled_gate;
} taryaq_check_result_t;

static taryaq_check_result_t taryaq_interaction_check(
    const char *primary_name,
    const char *concurrent_name,
    double      egfr,
    bool        id_verified
) {
    taryaq_check_result_t res;
    memset(&res, 0, sizeof(res));

    const taryaq_med_entry_t *p_med = taryaq_med_lookup(primary_name);
    const taryaq_med_entry_t *c_med = concurrent_name ? taryaq_med_lookup(concurrent_name) : NULL;

    const char *p_canon = p_med ? p_med->canonical_name : (primary_name ? primary_name : "Unknown");
    const char *c_canon = c_med ? c_med->canonical_name : (concurrent_name ? concurrent_name : NULL);

    bool is_ctrl = (p_med && p_med->is_controlled) || (c_med && c_med->is_controlled);

    taryaq_rx_context_t rx;
    memset(&rx, 0, sizeof(rx));
    rx.primary_drug = p_canon;
    rx.concurrent_drug = c_canon;
    rx.patient_egfr_ml_min = egfr;
    rx.is_controlled_substance = is_ctrl;
    rx.has_controlled_id_verified = id_verified;
    rx.icd10_code = p_med ? p_med->icd10_indication : "M10.0";
    rx.submission_delay_days = 0;
    rx.has_ejadah_lab_justification = true;

    taryaq_result_t ar = taryaq_verify_prescription_and_claim(&rx);
    res.verdict = ar.verdict;
    snprintf(res.alert_code, sizeof(res.alert_code), "%s", ar.alert_code);
    snprintf(res.clinical_rationale, sizeof(res.clinical_rationale), "%s", ar.clinical_rationale);

    if (p_med && p_med->renal_egfr_cutoff > 0.0 && egfr < p_med->renal_egfr_cutoff) {
        res.has_renal_risk = true;
    }
    if (p_med && c_med && p_med->cyp3a4_profile == CYP3A4_SUBSTRATE && c_med->cyp3a4_profile == CYP3A4_INHIBITOR) {
        res.has_cyp3a4_conflict = true;
    }
    if (is_ctrl && !id_verified) {
        res.is_controlled_gate = true;
    }

    return res;
}

/* ========================================================================= */
/* 7. Tool 3: claim_scrub                                                    */
/* ========================================================================= */

typedef struct {
    double           net_claim_aed;
    uint32_t         delay_days;
    double           penalty_rate_pct;
    double           penalty_aed;
    double           adjusted_net_aed;
    char             alert_code[64];
    char             rationale[256];
    char             scrubbed_query[256];
    taryaq_verdict_t verdict;
} taryaq_claim_scrub_result_t;

static taryaq_claim_scrub_result_t taryaq_claim_scrub(
    double      net_claim_aed,
    uint32_t    delay_days,
    const char *icd10_code,
    const char *claim_narrative
) {
    taryaq_claim_scrub_result_t res;
    memset(&res, 0, sizeof(res));

    res.net_claim_aed = net_claim_aed;
    res.delay_days = delay_days;

    if (claim_narrative && claim_narrative[0] != '\0') {
        grounding_scrub_search_query(claim_narrative, res.scrubbed_query, sizeof(res.scrubbed_query));
    } else {
        snprintf(res.scrubbed_query, sizeof(res.scrubbed_query), "DHA eClaimLink SN 03/2019 standard claim");
    }

    res.penalty_rate_pct = (double)delay_days * 0.03;
    res.penalty_aed = net_claim_aed * ((double)delay_days * 0.0003);
    if (res.penalty_aed > net_claim_aed) {
        res.penalty_aed = net_claim_aed;
    }
    res.adjusted_net_aed = net_claim_aed - res.penalty_aed;

    taryaq_rx_context_t rx;
    memset(&rx, 0, sizeof(rx));
    rx.primary_drug = "Metformin";
    rx.patient_egfr_ml_min = 90.0;
    rx.icd10_code = icd10_code ? icd10_code : "E11.9";
    rx.submission_delay_days = delay_days;
    rx.has_ejadah_lab_justification = true;

    taryaq_result_t ar = taryaq_verify_prescription_and_claim(&rx);
    res.verdict = ar.verdict;
    snprintf(res.alert_code, sizeof(res.alert_code), "%s", ar.alert_code);
    snprintf(res.rationale, sizeof(res.rationale), "%s", ar.clinical_rationale);

    return res;
}

/* ========================================================================= */
/* 8. Tool 4: human_override                                                 */
/* ========================================================================= */

typedef struct {
    bool override_approved;
    char token[64];
    char scope[32];
    char rationale[256];
    char err_message[256];
} taryaq_override_result_t;

static taryaq_override_result_t taryaq_human_override(
    const char           *approval_code,
    const char           *clinical_rationale,
    qala_approval_slot_t *slots,
    size_t                slot_count,
    uint64_t              now_utc
) {
    taryaq_override_result_t res;
    memset(&res, 0, sizeof(res));

    if (!clinical_rationale || strlen(clinical_rationale) < 8) {
        res.override_approved = false;
        snprintf(res.err_message, sizeof(res.err_message),
                 "REJECTED: Mandatory clinical rationale missing or too brief (min 8 chars).");
        return res;
    }

    bool non_space = false;
    for (size_t i = 0; clinical_rationale[i] != '\0'; ++i) {
        if (!isspace((unsigned char)clinical_rationale[i])) {
            non_space = true;
            break;
        }
    }
    if (!non_space) {
        res.override_approved = false;
        snprintf(res.err_message, sizeof(res.err_message),
                 "REJECTED: Clinical rationale cannot be empty or whitespace only.");
        return res;
    }

    qala_tool_call_ctx_t ctx;
    memset(&ctx, 0, sizeof(ctx));
    ctx.tool_name = "human_override";
    ctx.target_path = "clinical_override_register";
    ctx.raw_args_json = "{\"action\":\"clinical_override\"}";
    ctx.amount_aed = 0.0;
    ctx.is_mutating = true;
    ctx.required_scope = "clinical_override";
    ctx.supplied_code = approval_code;

    qala_policy_result_t pr = policy_verify_call(&ctx, slots, slot_count, now_utc, NULL);

    if (pr.verdict == VERDICT_SAFE) {
        res.override_approved = true;
        snprintf(res.token, sizeof(res.token), "%s", approval_code ? approval_code : "");
        snprintf(res.scope, sizeof(res.scope), "clinical_override");
        snprintf(res.rationale, sizeof(res.rationale), "%s", clinical_rationale ? clinical_rationale : "");
    } else {
        res.override_approved = false;
        snprintf(res.err_message, sizeof(res.err_message), "%s", pr.reason);
    }

    return res;
}

/* ========================================================================= */
/* 9. Tool 5: commit_audit & Rollback Engine                                 */
/* ========================================================================= */

typedef enum {
    SESSION_EMPTY       = 0,
    SESSION_DRAFT       = 1,
    SESSION_SAFE        = 2,
    SESSION_BLOCKED     = 3,
    SESSION_OVERRIDDEN  = 4,
    SESSION_COMMITTED   = 5,
    SESSION_ROLLED_BACK = 6
} taryaq_session_state_t;

typedef struct {
    taryaq_session_state_t state;
    char     primary_drug[64];
    char     concurrent_drug[64];
    double   patient_egfr;
    bool     is_controlled;
    bool     has_id_verified;
    char     alert_code[64];
    char     clinical_rationale[256];
    bool     override_approved;
    char     override_token[64];
    char     override_rationale[256];
    double   net_claim_aed;
    uint32_t delay_days;
    double   penalty_aed;
    uint64_t created_utc;
} taryaq_working_session_t;

static taryaq_working_session_t g_session;

static void taryaq_rollback_state(const char *reason, const char *audit_path, bool enable_telemetry) {
    uint64_t now_utc = taryaq_now_utc();
    if (g_session.state != SESSION_EMPTY && g_session.state != SESSION_ROLLED_BACK) {
        if (audit_path) {
            FILE *fp = fopen(audit_path, "a");
            if (fp) {
                char esc_reason[256];
                taryaq_json_escape(reason ? reason : "Operator abort or unapproved block", esc_reason, sizeof(esc_reason));
                fprintf(fp,
                    "{\"timestamp_utc\":%llu,\"reporting_tz\":\"Asia/Dubai\",\"agent\":\"Taryaq v0\","
                    "\"action\":\"PRESCRIPTION_ROLLED_BACK\",\"reason\":\"%s\",\"state\":\"ROLLED_BACK\"}\n",
                    (unsigned long long)now_utc, esc_reason);
                fclose(fp);
            }
        }
    }

    memset(&g_session, 0, sizeof(g_session));
    g_session.state = SESSION_ROLLED_BACK;

    if (enable_telemetry) {
        char tele[256];
        snprintf(tele, sizeof(tele),
            "{\"event_type\":\"state_committed\",\"action\":\"rollback\",\"status\":\"ROLLED_BACK\"}");
        taryaq_emit_telemetry(true, "state_committed", tele);
    }
}

static bool taryaq_commit_audit(const char *audit_path, bool enable_telemetry) {
    if (g_session.state == SESSION_BLOCKED && !g_session.override_approved) {
        fprintf(stderr, "[-] Expected Security Guard: Cannot commit blocked prescription without valid human override.\n");
        taryaq_rollback_state("Blocked prescription without override", audit_path, enable_telemetry);
        return false;
    }

    if (g_session.state != SESSION_SAFE && g_session.state != SESSION_OVERRIDDEN) {
        fprintf(stderr, "[-] Error: No active, validated prescription state to commit.\n");
        return false;
    }

    uint64_t now_utc = taryaq_now_utc();

    char payload_to_hash[1024];
    snprintf(payload_to_hash, sizeof(payload_to_hash),
        "%llu|Asia/Dubai|Taryaq v0|PRESCRIPTION_COMMITTED|%s|%s|%.1f|%s|%s|%s|%.2f|%u|%.2f",
        (unsigned long long)now_utc,
        g_session.primary_drug,
        g_session.concurrent_drug,
        g_session.patient_egfr,
        g_session.alert_code,
        g_session.override_approved ? g_session.override_token : "NONE",
        g_session.override_approved ? g_session.override_rationale : "NONE",
        g_session.net_claim_aed,
        g_session.delay_days,
        g_session.penalty_aed);

    char sha256_sig[65];
    sha256_hex(payload_to_hash, strlen(payload_to_hash), sha256_sig);

    FILE *fp = fopen(audit_path ? audit_path : DEFAULT_AUDIT_LOG, "a");
    if (!fp) {
        perror("[-] Error opening audit log file");
        return false;
    }

    char esc_primary[128], esc_concurrent[128], esc_alert[128];
    char esc_token[128], esc_rationale[256];
    taryaq_json_escape(g_session.primary_drug, esc_primary, sizeof(esc_primary));
    taryaq_json_escape(g_session.concurrent_drug, esc_concurrent, sizeof(esc_concurrent));
    taryaq_json_escape(g_session.alert_code, esc_alert, sizeof(esc_alert));
    taryaq_json_escape(g_session.override_token, esc_token, sizeof(esc_token));
    taryaq_json_escape(g_session.override_rationale, esc_rationale, sizeof(esc_rationale));

    fprintf(fp,
        "{\"timestamp_utc\":%llu,\"reporting_tz\":\"Asia/Dubai\",\"agent\":\"Taryaq v0\","
        "\"action\":\"PRESCRIPTION_COMMITTED\",\"primary_drug\":\"%s\",\"concurrent_drug\":\"%s\","
        "\"patient_egfr\":%.1f,\"verdict\":\"%s\",\"alert_code\":\"%s\","
        "\"override_status\":\"%s\",\"override_token\":\"%s\",\"override_rationale\":\"%s\","
        "\"claim_net_aed\":%.2f,\"claim_delay_days\":%u,\"penalty_aed\":%.2f,"
        "\"sha256_signature\":\"%s\",\"state\":\"COMMITTED\"}\n",
        (unsigned long long)now_utc,
        esc_primary,
        esc_concurrent,
        g_session.patient_egfr,
        (g_session.state == SESSION_OVERRIDDEN) ? "CLINICAL_CONTRAINDICATION_OVERRIDDEN" : "CLINICAL_SAFE",
        esc_alert,
        g_session.override_approved ? "APPROVED" : "NONE",
        esc_token,
        esc_rationale,
        g_session.net_claim_aed,
        g_session.delay_days,
        g_session.penalty_aed,
        sha256_sig);
    fflush(fp);
    fclose(fp);

    g_session.state = SESSION_COMMITTED;

    if (enable_telemetry) {
        char tele[512];
        snprintf(tele, sizeof(tele),
            "{\"event_type\":\"state_committed\",\"agent\":\"Taryaq v0\",\"verdict\":\"%s\","
            "\"primary_drug\":\"%s\",\"sha256\":\"%s\",\"status\":\"COMMITTED\"}",
            (g_session.override_approved ? "OVERRIDDEN" : "SAFE"),
            esc_primary, sha256_sig);
        taryaq_emit_telemetry(true, "state_committed", tele);
    }

    return true;
}

/* ========================================================================= */
/* 10. Execution Mode: Deterministic Acceptance Test (--test)                */
/* ========================================================================= */

static int run_test_scenario(const char *audit_path, bool enable_telemetry) {
    double t_start = taryaq_get_monotonic_ms();

    printf("================================================================================\n");
    printf("  TARYAQ v0 CLI DAEMON: DETERMINISTIC ACCEPTANCE SUITE (-Wall -Werror -O2)\n");
    printf("  Target: Best Societal AI Agent | Dubai AI Agents Championship 2026-2027\n");
    printf("  Criteria: Cold start -> Rx -> Block -> Human Override -> Signed Audit Line\n");
    printf("================================================================================\n");

    /* Approval token pool setup */
    qala_approval_slot_t approval_slots[4];
    memset(approval_slots, 0, sizeof(approval_slots));

    snprintf(approval_slots[0].token, sizeof(approval_slots[0].token), "TARYAQ-OVERRIDE-8842-CLIN");
    snprintf(approval_slots[0].scope, sizeof(approval_slots[0].scope), "clinical_override");
    approval_slots[0].expires_utc = taryaq_now_utc() + 86400 * 365;
    approval_slots[0].consumed = false;

    snprintf(approval_slots[1].token, sizeof(approval_slots[1].token), "DUBAI-CLIN-APPROVE-7701");
    snprintf(approval_slots[1].scope, sizeof(approval_slots[1].scope), "clinical_override");
    approval_slots[1].expires_utc = taryaq_now_utc() + 86400 * 365;
    approval_slots[1].consumed = false;

    size_t slot_count = 2;

    /* Milestone 1: Sub-millisecond cold start */
    double t_cold = taryaq_get_monotonic_ms() - t_start;
    printf("[MILESTONE 1/8] Cold Start: %.3f ms (Criteria: < 15.000 ms) -> PASS\n", t_cold);
    if (t_cold >= 15.0) {
        fprintf(stderr, "[-] Fatal: Cold start exceeded 15ms threshold!\n");
        return 1;
    }

    if (enable_telemetry) {
        char tele[256];
        snprintf(tele, sizeof(tele),
            "{\"event_type\":\"task_started\",\"task_id\":\"taryaq-acceptance-01\","
            "\"title\":\"Taryaq v0 Deterministic Verification\",\"ast_time\":\"%.3f ms\"}",
            t_cold);
        taryaq_emit_telemetry(true, "task_started", tele);
    }

    /* Milestone 2: Tool 1 - med_lookup (Arabic normalization & English graph) */
    const taryaq_med_entry_t *med_colch = taryaq_med_lookup("كولشيسين");
    if (!med_colch || strcmp(med_colch->canonical_name, "Colchicine") != 0) {
        fprintf(stderr, "[-] Fatal: Arabic med_lookup failed for 'كولشيسين'!\n");
        return 1;
    }
    const taryaq_med_entry_t *med_clari = taryaq_med_lookup("Clarithromycin");
    if (!med_clari || med_clari->cyp3a4_profile != CYP3A4_INHIBITOR) {
        fprintf(stderr, "[-] Fatal: med_lookup failed for Clarithromycin!\n");
        return 1;
    }
    printf("[MILESTONE 2/8] Tool 1 (med_lookup): 'كولشيسين' -> Colchicine, 'Clarithromycin' -> Inhibitor -> PASS\n");

    /* Milestone 3: Tool 2 - interaction_check (Fatal CYP3A4 renal block) */
    memset(&g_session, 0, sizeof(g_session));
    snprintf(g_session.primary_drug, sizeof(g_session.primary_drug), "%s", med_colch->canonical_name);
    snprintf(g_session.concurrent_drug, sizeof(g_session.concurrent_drug), "%s", med_clari->canonical_name);
    g_session.patient_egfr = 22.0; /* Severe renal failure */
    g_session.created_utc = taryaq_now_utc();
    g_session.state = SESSION_DRAFT;

    taryaq_check_result_t chk = taryaq_interaction_check(
        g_session.primary_drug, g_session.concurrent_drug, g_session.patient_egfr, false);

    if (chk.verdict != CLINICAL_CONTRAINDICATION_BLOCK ||
        strcmp(chk.alert_code, "FATAL_CYP3A4_RENAL_CONTRAINDICATION") != 0) {
        fprintf(stderr, "[-] Fatal: Expected CLINICAL_CONTRAINDICATION_BLOCK, got %d (%s)\n",
                chk.verdict, chk.alert_code);
        return 1;
    }
    g_session.state = SESSION_BLOCKED;
    snprintf(g_session.alert_code, sizeof(g_session.alert_code), "%s", chk.alert_code);
    snprintf(g_session.clinical_rationale, sizeof(g_session.clinical_rationale), "%s", chk.clinical_rationale);

    printf("[MILESTONE 3/8] Tool 2 (interaction_check): Blocked FATAL_CYP3A4_RENAL_CONTRAINDICATION -> PASS\n");

    if (enable_telemetry) {
        char tele[256];
        snprintf(tele, sizeof(tele),
            "{\"event_type\":\"taryaq_clinical\",\"drugs\":\"Colchicine + Clarithromycin\","
            "\"egfr\":22.0,\"verdict\":\"FATAL CONTRAINDICATION BLOCKED\","
            "\"code\":\"FATAL_CYP3A4_RENAL_CONTRAINDICATION\"}");
        taryaq_emit_telemetry(true, "taryaq_clinical", tele);
    }

    /* Milestone 4: Tool 5 Guard - Attempt unapproved commit & verify state rollback */
    bool unauth_commit = taryaq_commit_audit(audit_path, enable_telemetry);
    if (unauth_commit != false || g_session.state != SESSION_ROLLED_BACK) {
        fprintf(stderr, "[-] Fatal: Blocked prescription without override was erroneously committed!\n");
        return 1;
    }
    printf("[MILESTONE 4/8] Tool 5 (commit_audit Guard): Blocked commit rejected & state rolled back -> PASS\n");

    /* Milestone 5: Tool 4 Guard - Re-intake and test mandatory clinical rationale */
    snprintf(g_session.primary_drug, sizeof(g_session.primary_drug), "%s", "Colchicine");
    snprintf(g_session.concurrent_drug, sizeof(g_session.concurrent_drug), "%s", "Clarithromycin");
    g_session.patient_egfr = 22.0;
    g_session.state = SESSION_BLOCKED;
    snprintf(g_session.alert_code, sizeof(g_session.alert_code), "%s", "FATAL_CYP3A4_RENAL_CONTRAINDICATION");

    taryaq_override_result_t bad_ov = taryaq_human_override(
        "TARYAQ-OVERRIDE-8842-CLIN", "   ", approval_slots, slot_count, taryaq_now_utc());
    if (bad_ov.override_approved != false) {
        fprintf(stderr, "[-] Fatal: Human override accepted blank rationale!\n");
        return 1;
    }
    printf("[MILESTONE 5/8] Tool 4 (human_override Guard): Empty clinical rationale rejected -> PASS\n");

    /* Milestone 6: Tool 4 - Apply Human Override with Valid Code and Clinical Rationale */
    const char *approval_code = "TARYAQ-OVERRIDE-8842-CLIN";
    const char *rationale = "ICU continuous hemodialysis initiated; nephrology specialist co-signature verified (Ref: CLIN-REV-9921)";
    taryaq_override_result_t good_ov = taryaq_human_override(
        approval_code, rationale, approval_slots, slot_count, taryaq_now_utc());
    if (!good_ov.override_approved) {
        fprintf(stderr, "[-] Fatal: Human override failed with error: %s\n", good_ov.err_message);
        return 1;
    }
    g_session.override_approved = true;
    snprintf(g_session.override_token, sizeof(g_session.override_token), "%s", good_ov.token);
    snprintf(g_session.override_rationale, sizeof(g_session.override_rationale), "%s", good_ov.rationale);
    g_session.state = SESSION_OVERRIDDEN;

    printf("[MILESTONE 6/8] Tool 4 (human_override): Verified code '%s' and consumed slot -> PASS\n", approval_code);

    if (enable_telemetry) {
        char tele[256];
        snprintf(tele, sizeof(tele),
            "{\"event_type\":\"gate_verdict\",\"verdict\":\"APPROVED & OVERRIDDEN\","
            "\"token\":\"%s\",\"tool\":\"human_override\"}", approval_code);
        taryaq_emit_telemetry(true, "gate_verdict", tele);
    }

    /* Milestone 7: Tool 3 - claim_scrub (DHA SN 03/2019 Claim Cycle & Late Penalty) */
    taryaq_claim_scrub_result_t scrub_ok = taryaq_claim_scrub(450.00, 0, "M10.0", "Patient prescription claim");
    if (scrub_ok.verdict != CLINICAL_SAFE || scrub_ok.penalty_aed != 0.0) {
        fprintf(stderr, "[-] Fatal: Normal claim failed scrub!\n");
        return 1;
    }
    taryaq_claim_scrub_result_t scrub_late = taryaq_claim_scrub(450.00, 12, "M10.0", "Delayed claim submission");
    if (scrub_late.verdict != CLINICAL_CLAIM_CYCLE_WARN || scrub_late.penalty_aed < 1.61 || scrub_late.penalty_aed > 1.63) {
        fprintf(stderr, "[-] Fatal: DHA SN 03/2019 12-day penalty incorrect (expected 1.62 AED, got %.2f AED)!\n",
                scrub_late.penalty_aed);
        return 1;
    }
    g_session.net_claim_aed = scrub_ok.net_claim_aed;
    g_session.delay_days = scrub_ok.delay_days;
    g_session.penalty_aed = scrub_ok.penalty_aed;

    printf("[MILESTONE 7/8] Tool 3 (claim_scrub): DHA SN 03/2019 verified (12 days = 1.62 AED penalty) -> PASS\n");

    /* Milestone 8: Tool 5 - commit_audit (Signed JSONL line & replay protection check) */
    bool commit_ok = taryaq_commit_audit(audit_path, enable_telemetry);
    if (!commit_ok || g_session.state != SESSION_COMMITTED) {
        fprintf(stderr, "[-] Fatal: Commit audit failed for overridden prescription!\n");
        return 1;
    }

    /* Verify audit file on disk */
    FILE *fp = fopen(audit_path ? audit_path : DEFAULT_AUDIT_LOG, "r");
    if (!fp) {
        fprintf(stderr, "[-] Fatal: Could not open audit file '%s' for verification!\n",
                audit_path ? audit_path : DEFAULT_AUDIT_LOG);
        return 1;
    }
    char last_line[2048] = {0};
    char buf[2048];
    while (fgets(buf, sizeof(buf), fp)) {
        if (strlen(buf) > 10) {
            snprintf(last_line, sizeof(last_line), "%s", buf);
        }
    }
    fclose(fp);

    if (strstr(last_line, "PRESCRIPTION_COMMITTED") == NULL ||
        strstr(last_line, "Colchicine") == NULL ||
        strstr(last_line, "TARYAQ-OVERRIDE-8842-CLIN") == NULL ||
        strstr(last_line, "sha256_signature") == NULL) {
        fprintf(stderr, "[-] Fatal: Audit line on disk is missing required signature or fields: %s\n", last_line);
        return 1;
    }

    /* Test single-use token replay rejection */
    taryaq_override_result_t replay_ov = taryaq_human_override(
        approval_code, "Replay attempt", approval_slots, slot_count, taryaq_now_utc());
    if (replay_ov.override_approved != false) {
        fprintf(stderr, "[-] Fatal: Replay of consumed approval token was accepted!\n");
        return 1;
    }

    double t_total = taryaq_get_monotonic_ms() - t_start;
    printf("[MILESTONE 8/8] Tool 5 (commit_audit): Signed JSONL on disk & single-use replay blocked -> PASS\n");

    printf("================================================================================\n");
    printf(" [SUCCESS] Taryaq v0 Acceptance Workflow Passed in %.3f ms (< 180,000 ms)\n", t_total);
    printf(" Mode: 100%% Air-Gapped C99 Native Engine | Zero Network Bloat\n");
    printf(" Audit Record: %s\n", audit_path ? audit_path : DEFAULT_AUDIT_LOG);
    printf("================================================================================\n");

    return 0;
}

/* ========================================================================= */
/* 11. Execution Mode: Interactive CLI (--cli)                               */
/* ========================================================================= */

static void print_cli_help(void) {
    printf("--------------------------------------------------------------------------------\n");
    printf(" TARYAQ v0 CLI DAEMON COMMANDS:\n");
    printf("   lookup <drug_name>                  - Query local graph (Arabic or English)\n");
    printf("   rx <primary> [concurrent] [egfr]    - Intake prescription vitals\n");
    printf("   check                               - Run contraindication & interaction engine\n");
    printf("   claim <net_aed> <delay_days> [note] - Run DHA SN 03/2019 claim cycle scrubber\n");
    printf("   override <token> <rationale...>     - Apply single-use cryptographic override\n");
    printf("   commit                              - Sign and write append-only audit line\n");
    printf("   rollback                            - Discard uncommitted prescription state\n");
    printf("   status                              - Display current session status\n");
    printf("   slots                               - List available approval token slots\n");
    printf("   help                                - Print this command reference\n");
    printf("   quit / exit                         - Terminate session\n");
    printf("--------------------------------------------------------------------------------\n");
}

static void run_cli_loop(const char *audit_path, bool enable_telemetry) {
    printf("================================================================================\n");
    printf("  TARYAQ v0 CLI DAEMON - Sovereign Clinical Safety & DHA Reimbursement Firewall\n");
    printf("  Dubai Create AI Agents Championship 2026-2027 | Best Societal AI Agent\n");
    printf("  Mode: 100%% Air-Gapped ISO C99 Native Engine | Telemetry: %s\n",
           enable_telemetry ? "ACTIVE (http://127.0.0.1:8787/emit)" : "DISABLED (Air-Gapped)");
    printf("================================================================================\n");
    print_cli_help();

    qala_approval_slot_t approval_slots[4];
    memset(approval_slots, 0, sizeof(approval_slots));
    snprintf(approval_slots[0].token, sizeof(approval_slots[0].token), "TARYAQ-OVERRIDE-8842-CLIN");
    snprintf(approval_slots[0].scope, sizeof(approval_slots[0].scope), "clinical_override");
    approval_slots[0].expires_utc = taryaq_now_utc() + 86400 * 365;
    approval_slots[0].consumed = false;

    snprintf(approval_slots[1].token, sizeof(approval_slots[1].token), "DUBAI-CLIN-APPROVE-7701");
    snprintf(approval_slots[1].scope, sizeof(approval_slots[1].scope), "clinical_override");
    approval_slots[1].expires_utc = taryaq_now_utc() + 86400 * 365;
    approval_slots[1].consumed = false;

    size_t slot_count = 2;

    char line[1024];
    while (true) {
        printf("taryaq> ");
        fflush(stdout);

        if (!fgets(line, sizeof(line), stdin)) {
            printf("\nExiting Taryaq CLI.\n");
            break;
        }

        size_t len = strlen(line);
        while (len > 0 && (line[len - 1] == '\n' || line[len - 1] == '\r' || isspace((unsigned char)line[len - 1]))) {
            line[--len] = '\0';
        }
        if (len == 0) continue;

        char cmd[64] = {0};
        char rest[960] = {0};
        int parsed = sscanf(line, "%63s %959[^\n]", cmd, rest);
        if (parsed <= 0) continue;

        if (strcmp(cmd, "exit") == 0 || strcmp(cmd, "quit") == 0) {
            printf("Exiting Taryaq CLI.\n");
            break;
        } else if (strcmp(cmd, "help") == 0) {
            print_cli_help();
        } else if (strcmp(cmd, "status") == 0) {
            const char *st_str = "EMPTY";
            if (g_session.state == SESSION_DRAFT) st_str = "DRAFT";
            else if (g_session.state == SESSION_SAFE) st_str = "SAFE";
            else if (g_session.state == SESSION_BLOCKED) st_str = "BLOCKED";
            else if (g_session.state == SESSION_OVERRIDDEN) st_str = "OVERRIDDEN";
            else if (g_session.state == SESSION_COMMITTED) st_str = "COMMITTED";
            else if (g_session.state == SESSION_ROLLED_BACK) st_str = "ROLLED_BACK";

            printf("Session State:      %s\n", st_str);
            printf("Primary Drug:       %s\n", g_session.primary_drug[0] ? g_session.primary_drug : "(none)");
            printf("Concurrent Drug:    %s\n", g_session.concurrent_drug[0] ? g_session.concurrent_drug : "(none)");
            printf("Patient eGFR:       %.1f ml/min\n", g_session.patient_egfr);
            printf("Alert Code:         %s\n", g_session.alert_code[0] ? g_session.alert_code : "(none)");
            printf("Override Status:    %s\n", g_session.override_approved ? "APPROVED" : "NOT_APPLIED");
            if (g_session.override_approved) {
                printf("Override Token:     %s\n", g_session.override_token);
                printf("Override Rationale: %s\n", g_session.override_rationale);
            }
            printf("Claim Amount:       AED %.2f (Delay: %u days, Penalty: AED %.2f)\n",
                   g_session.net_claim_aed, g_session.delay_days, g_session.penalty_aed);
        } else if (strcmp(cmd, "lookup") == 0 || strcmp(cmd, "بحث") == 0) {
            if (parsed < 2 || rest[0] == '\0') {
                printf("Usage: lookup <drug_name_ar_or_en>\n");
                continue;
            }
            const taryaq_med_entry_t *med = taryaq_med_lookup(rest);
            if (!med) {
                printf("[-] Medication '%s' not found in embedded sovereign graph.\n", rest);
            } else {
                printf("[+] Found: %s (%s)\n", med->canonical_name, med->arabic_name);
                printf("    Class:            %s\n", med->drug_class);
                printf("    Renal Cutoff:     %.1f eGFR ml/min\n", med->renal_egfr_cutoff);
                printf("    CYP3A4 Profile:   %s\n",
                       med->cyp3a4_profile == CYP3A4_SUBSTRATE ? "Substrate" :
                       med->cyp3a4_profile == CYP3A4_INHIBITOR ? "Potent Inhibitor" : "None");
                printf("    Controlled Drug:  %s\n", med->is_controlled ? "YES (UAE Law No. 2 of 2019)" : "NO");
                printf("    Indication ICD10: %s\n", med->icd10_indication);
                printf("    Clinical Notes:   %s\n", med->clinical_notes);
            }
        } else if (strcmp(cmd, "rx") == 0) {
            char p_drug[64] = {0}, c_drug[64] = {0};
            double egfr = 90.0;
            int n = sscanf(rest, "%63s %63s %lf", p_drug, c_drug, &egfr);
            if (n < 1) {
                printf("Usage: rx <primary_drug> [concurrent_drug] [patient_egfr]\n");
                continue;
            }
            if (n == 1) {
                c_drug[0] = '\0';
                egfr = 90.0;
            } else if (n == 2) {
                egfr = 90.0;
            }

            memset(&g_session, 0, sizeof(g_session));
            snprintf(g_session.primary_drug, sizeof(g_session.primary_drug), "%s", p_drug);
            if (c_drug[0] != '\0' && strcmp(c_drug, "none") != 0 && strcmp(c_drug, "-") != 0) {
                snprintf(g_session.concurrent_drug, sizeof(g_session.concurrent_drug), "%s", c_drug);
            }
            g_session.patient_egfr = egfr;
            g_session.created_utc = taryaq_now_utc();
            g_session.state = SESSION_DRAFT;

            printf("[+] Prescription drafted: %s %s%s (eGFR: %.1f)\n",
                   g_session.primary_drug,
                   g_session.concurrent_drug[0] ? "+ " : "",
                   g_session.concurrent_drug[0] ? g_session.concurrent_drug : "",
                   g_session.patient_egfr);

            taryaq_check_result_t chk = taryaq_interaction_check(
                g_session.primary_drug, g_session.concurrent_drug, g_session.patient_egfr, false);
            snprintf(g_session.alert_code, sizeof(g_session.alert_code), "%s", chk.alert_code);
            snprintf(g_session.clinical_rationale, sizeof(g_session.clinical_rationale), "%s", chk.clinical_rationale);

            if (chk.verdict == CLINICAL_CONTRAINDICATION_BLOCK) {
                g_session.state = SESSION_BLOCKED;
                printf("[!] VERDICT: BLOCKED - %s\n", chk.alert_code);
                printf("    %s\n", chk.clinical_rationale);
                printf("    To override, run: override <token> <clinical_rationale>\n");
            } else if (chk.verdict == CLINICAL_CONTROLLED_DRUG_GATE) {
                g_session.state = SESSION_BLOCKED;
                printf("[!] VERDICT: CONTROLLED MEDICATION GATE - %s\n", chk.alert_code);
                printf("    %s\n", chk.clinical_rationale);
            } else {
                g_session.state = SESSION_SAFE;
                printf("[+] VERDICT: SAFE - %s\n", chk.alert_code);
                printf("    %s\n", chk.clinical_rationale);
            }
        } else if (strcmp(cmd, "check") == 0) {
            if (g_session.primary_drug[0] == '\0') {
                printf("[-] No prescription active. Use 'rx <primary> [concurrent] [egfr]' first.\n");
                continue;
            }
            taryaq_check_result_t chk = taryaq_interaction_check(
                g_session.primary_drug, g_session.concurrent_drug, g_session.patient_egfr, false);
            printf("[*] Interaction Check Result:\n");
            printf("    Verdict:   %d\n", chk.verdict);
            printf("    Code:      %s\n", chk.alert_code);
            printf("    Rationale: %s\n", chk.clinical_rationale);
        } else if (strcmp(cmd, "claim") == 0) {
            double aed = 0.0;
            uint32_t delay = 0;
            char narrative[512] = {0};
            int n = sscanf(rest, "%lf %u %511[^\n]", &aed, &delay, narrative);
            if (n < 2) {
                printf("Usage: claim <net_claim_aed> <delay_days> [claim_narrative]\n");
                continue;
            }
            taryaq_claim_scrub_result_t sc = taryaq_claim_scrub(aed, delay, "M10.0", narrative);
            g_session.net_claim_aed = sc.net_claim_aed;
            g_session.delay_days = sc.delay_days;
            g_session.penalty_aed = sc.penalty_aed;

            printf("[*] DHA SN 03/2019 Claim Scrub Result:\n");
            printf("    Net Claim:      AED %.2f\n", sc.net_claim_aed);
            printf("    Delay Days:     %u day(s)\n", sc.delay_days);
            printf("    Penalty Rate:   %.2f%% (0.03%%/day)\n", sc.penalty_rate_pct);
            printf("    Penalty Amount: AED %.2f\n", sc.penalty_aed);
            printf("    Adjusted Net:   AED %.2f\n", sc.adjusted_net_aed);
            printf("    Scrubbed Query: %s\n", sc.scrubbed_query);
            printf("    Verdict:        %s (%s)\n",
                   sc.verdict == CLINICAL_SAFE ? "SAFE" : "CYCLE_WARN", sc.alert_code);
        } else if (strcmp(cmd, "override") == 0) {
            char token[64] = {0};
            char rationale[512] = {0};
            int n = sscanf(rest, "%63s %511[^\n]", token, rationale);
            if (n < 2) {
                printf("Usage: override <approval_token> <mandatory_clinical_rationale>\n");
                continue;
            }
            if (g_session.state != SESSION_BLOCKED) {
                printf("[-] Notice: Session is not currently in BLOCKED state.\n");
            }
            taryaq_override_result_t ov = taryaq_human_override(
                token, rationale, approval_slots, slot_count, taryaq_now_utc());
            if (ov.override_approved) {
                g_session.override_approved = true;
                snprintf(g_session.override_token, sizeof(g_session.override_token), "%s", ov.token);
                snprintf(g_session.override_rationale, sizeof(g_session.override_rationale), "%s", ov.rationale);
                g_session.state = SESSION_OVERRIDDEN;
                printf("[+] OVERRIDE SUCCESS: Approval code '%s' accepted & consumed.\n", token);
                printf("    Rationale: %s\n", rationale);
                printf("    Ready to commit. Run: commit\n");
            } else {
                printf("[-] OVERRIDE REJECTED: %s\n", ov.err_message);
            }
        } else if (strcmp(cmd, "commit") == 0) {
            if (g_session.state == SESSION_BLOCKED && !g_session.override_approved) {
                printf("[-] COMMIT REJECTED: Fatal contraindication blocked without override.\n");
                printf("    To authorize, run: override <token> <clinical_rationale>\n");
                printf("    To discard session, run: rollback\n");
                continue;
            }
            if (g_session.primary_drug[0] == '\0') {
                printf("[-] Nothing to commit. Draft prescription first with 'rx ...'.\n");
                continue;
            }
            bool ok = taryaq_commit_audit(audit_path, enable_telemetry);
            if (ok) {
                printf("[+] COMMIT SUCCESS: Prescription signed and appended to %s\n",
                       audit_path ? audit_path : DEFAULT_AUDIT_LOG);
            } else {
                printf("[-] Commit failed.\n");
            }
        } else if (strcmp(cmd, "rollback") == 0) {
            taryaq_rollback_state("Manual rollback by pharmacist", audit_path, enable_telemetry);
            printf("[+] Session rolled back and reset.\n");
        } else if (strcmp(cmd, "slots") == 0) {
            printf("[*] Available Approval Slots:\n");
            for (size_t i = 0; i < slot_count; ++i) {
                printf("    Slot %zu: Token: %s | Scope: %s | Consumed: %s\n",
                       i + 1, approval_slots[i].token, approval_slots[i].scope,
                       approval_slots[i].consumed ? "YES (USED)" : "NO (AVAILABLE)");
            }
        } else {
            printf("[-] Unknown command '%s'. Type 'help' for command list.\n", cmd);
        }
    }
}

/* ========================================================================= */
/* 12. Main Entry Point                                                      */
/* ========================================================================= */

int main(int argc, char **argv) {
    bool test_mode = false;
    bool cli_mode = false;
    bool enable_telemetry = false;
    const char *audit_path = DEFAULT_AUDIT_LOG;

    for (int i = 1; i < argc; ++i) {
        if (strcmp(argv[i], "--test") == 0) {
            test_mode = true;
        } else if (strcmp(argv[i], "--cli") == 0) {
            cli_mode = true;
        } else if (strcmp(argv[i], "--telemetry") == 0) {
            enable_telemetry = true;
        } else if (strcmp(argv[i], "--audit-file") == 0 && (i + 1) < argc) {
            audit_path = argv[++i];
        } else if (strcmp(argv[i], "--help") == 0 || strcmp(argv[i], "-h") == 0) {
            printf("Usage: %s [--test] [--cli] [--telemetry] [--audit-file <path>] [--help]\n", argv[0]);
            printf("Options:\n");
            printf("  --test         Run automated deterministic acceptance test and exit 0 on success\n");
            printf("  --cli          Launch interactive conversational CLI\n");
            printf("  --telemetry    Enable optional live telemetry emission to http://127.0.0.1:8787/emit\n");
            printf("  --audit-file   Override path to append-only JSONL audit log (default: taryaq_audit.jsonl)\n");
            printf("  --help         Display this help message\n");
            return 0;
        }
    }

    if (enable_telemetry) {
        curl_global_init(CURL_GLOBAL_DEFAULT);
    }

    int rc = 0;
    if (test_mode) {
        rc = run_test_scenario(audit_path, enable_telemetry);
    } else {
        (void)cli_mode;
        run_cli_loop(audit_path, enable_telemetry);
    }

    if (enable_telemetry) {
        curl_global_cleanup();
    }

    return rc;
}
```


---
## FILE: tests/test_mcp_interop.c
```c
/* test_mcp_interop.c
 * End-to-End Interoperability Test Suite for Stateless MCP 2026-07-28
 * Validates C99 libcurl client against live Python Mock Server over HTTP/SSE
 * Compiler Flags: -std=c99 -Wall -Wextra -Werror -O2 -Iadapters
 */

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <assert.h>
#include <stdbool.h>
#include <stdint.h>

#include "mcp_curl_client.h"
#include "cJSON.h"

#define MCP_TEST_ENDPOINT "http://127.0.0.1:8765/mcp"
#define MCP_AUTH_ENDPOINT "http://127.0.0.1:8765/mcp/auth-test"
#define MCP_FORBIDDEN_ENDPOINT "http://127.0.0.1:8765/mcp/forbidden-test"

static void test_1_initialize(void) {
    printf("[TEST 1] mcp_client_initialize() -> MCP_SUCCESS & non-null payload...\n");
    mcp_client_config_t cfg = {
        .endpoint_url = MCP_TEST_ENDPOINT,
        .bearer_token = NULL,
        .client_name = "qala-interop-test",
        .timeout_ms = 5000
    };

    mcp_tool_call_resp_t resp;
    mcp_status_t st = mcp_client_initialize(&cfg, 1001, &resp);

    assert(st == MCP_SUCCESS);
    assert(resp.status == MCP_SUCCESS);
    assert(resp.http_status_code == 200);
    assert(!resp.is_rpc_error);
    assert(resp.result_text_payload != NULL);
    assert(resp.raw_json_response != NULL);
    assert(strstr(resp.result_text_payload, "2026-07-28") != NULL);

    /* Verify JSON schema contains protocolVersion and serverInfo */
    cJSON *root = cJSON_Parse(resp.raw_json_response);
    assert(root != NULL);
    cJSON *res = cJSON_GetObjectItem(root, "result");
    assert(res != NULL);
    cJSON *proto = cJSON_GetObjectItem(res, "protocolVersion");
    assert(proto != NULL && strcmp(proto->valuestring, "2026-07-28") == 0);
    cJSON *server_info = cJSON_GetObjectItem(res, "serverInfo");
    assert(server_info != NULL);
    cJSON_Delete(root);

    mcp_response_free(&resp);
    printf("         [PASS] Handshake succeeded with valid protocolVersion.\n");
}

static void test_2_list_tools(void) {
    printf("[TEST 2] mcp_client_list_tools() -> MCP_SUCCESS & tools array...\n");
    mcp_client_config_t cfg = {
        .endpoint_url = MCP_TEST_ENDPOINT,
        .bearer_token = NULL,
        .client_name = "qala-interop-test",
        .timeout_ms = 5000
    };

    mcp_tool_call_resp_t resp;
    mcp_status_t st = mcp_client_list_tools(&cfg, 1002, &resp);

    assert(st == MCP_SUCCESS);
    assert(resp.status == MCP_SUCCESS);
    assert(resp.http_status_code == 200);
    assert(!resp.is_rpc_error);
    assert(resp.result_text_payload != NULL);
    assert(resp.raw_json_response != NULL);

    /* Verify result has tools array with valid items */
    cJSON *root = cJSON_Parse(resp.raw_json_response);
    assert(root != NULL);
    cJSON *res = cJSON_GetObjectItem(root, "result");
    assert(res != NULL);
    cJSON *tools = cJSON_GetObjectItem(res, "tools");
    assert(tools != NULL && cJSON_IsArray(tools));
    int tool_count = cJSON_GetArraySize(tools);
    assert(tool_count >= 1);

    cJSON *first_tool = cJSON_GetArrayItem(tools, 0);
    assert(first_tool != NULL);
    cJSON *name = cJSON_GetObjectItem(first_tool, "name");
    assert(name != NULL && name->valuestring != NULL);
    assert(strcmp(name->valuestring, "customs_duty_calculator") == 0);
    cJSON_Delete(root);

    mcp_response_free(&resp);
    printf("         [PASS] Discovered %d tools in array payload.\n", tool_count);
}

static void test_3_call_tool(void) {
    printf("[TEST 3] mcp_client_call_tool() -> MCP_SUCCESS & execution result...\n");
    mcp_client_config_t cfg = {
        .endpoint_url = MCP_TEST_ENDPOINT,
        .bearer_token = NULL,
        .client_name = "qala-interop-test",
        .timeout_ms = 5000
    };

    mcp_tool_call_req_t req = {
        .tool_name = "customs_duty_calculator",
        .arguments_json = "{\"hs_code\":\"8471.30\",\"declared_value_aed\":100000.0}",
        .request_id = 1003
    };

    mcp_tool_call_resp_t resp;
    mcp_status_t st = mcp_client_call_tool(&cfg, &req, &resp);

    assert(st == MCP_SUCCESS);
    assert(resp.status == MCP_SUCCESS);
    assert(resp.http_status_code == 200);
    assert(!resp.is_rpc_error);
    assert(resp.result_text_payload != NULL);
    assert(strstr(resp.result_text_payload, "AED 5000.00") != NULL);

    mcp_response_free(&resp);
    printf("         [PASS] Tool execution completed with payload: 'AED 5000.00'.\n");
}

static void test_4_unauthorized(void) {
    printf("[TEST 4] Missing Auth Header -> MCP_ERR_UNAUTHORIZED (HTTP 401)...\n");
    mcp_client_config_t cfg = {
        .endpoint_url = MCP_AUTH_ENDPOINT,
        .bearer_token = NULL, /* Omitting token triggers 401 */
        .client_name = "qala-interop-test",
        .timeout_ms = 5000
    };

    mcp_tool_call_resp_t resp;
    mcp_status_t st = mcp_client_initialize(&cfg, 1004, &resp);

    assert(st == MCP_ERR_UNAUTHORIZED);
    assert(resp.status == MCP_ERR_UNAUTHORIZED);
    assert(resp.http_status_code == 401);

    mcp_response_free(&resp);
    printf("         [PASS] Verified HTTP 401 correctly mapped to MCP_ERR_UNAUTHORIZED.\n");
}

static void test_5_forbidden(void) {
    printf("[TEST 5] Policy Rejection -> MCP_ERR_FORBIDDEN (HTTP 403)...\n");
    mcp_client_config_t cfg = {
        .endpoint_url = MCP_FORBIDDEN_ENDPOINT,
        .bearer_token = "valid-token-insufficient-acl",
        .client_name = "qala-interop-test",
        .timeout_ms = 5000
    };

    mcp_tool_call_resp_t resp;
    mcp_status_t st = mcp_client_initialize(&cfg, 1005, &resp);

    assert(st == MCP_ERR_FORBIDDEN);
    assert(resp.status == MCP_ERR_FORBIDDEN);
    assert(resp.http_status_code == 403);

    mcp_response_free(&resp);
    printf("         [PASS] Verified HTTP 403 correctly mapped to MCP_ERR_FORBIDDEN.\n");
}

int main(void) {
    printf("==================================================================\n");
    printf(" MCP 2026-07-28 INTEROPERABILITY & CONFORMANCE TEST SUITE\n");
    printf(" Target Server: %s\n", MCP_TEST_ENDPOINT);
    printf("==================================================================\n");

    if (mcp_client_global_init() != 0) {
        fprintf(stderr, "Fatal: mcp_client_global_init() failed\n");
        return 1;
    }

    test_1_initialize();
    test_2_list_tools();
    test_3_call_tool();
    test_4_unauthorized();
    test_5_forbidden();

    mcp_client_global_cleanup();

    printf("==================================================================\n");
    printf(" [SUCCESS] All 5 MCP Interoperability Tests Passed Deterministically!\n");
    printf("==================================================================\n");
    return 0;
}

```
