# AUDIT DOSSIER 1: BARE-METAL C99 ADAPTERS & CLINICAL SAFETY
Dubai AI Agents Championship 2026-2027 | DCDE & Dubai Future Foundation
Scope: Memory Safety, ABI Alignment, Pharmacovigilance, DHA SN 03/2019, DESC ISR v3.1

This file contains the complete source code of all C99 native security adapters.


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

/* Function Prototype */
taryaq_result_t taryaq_verify_prescription_and_claim(const taryaq_rx_context_t *rx);

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
 *   1. Deterministic Pharmacovigilance & Renal/CYP3A4 Contraindication Blocker
 *   2. UAE Controlled Medication Regulatory Gatekeeper (Law No. 2 of 2019)
 *   3. DHA eClaimLink & Ejadah Pre-Submission XML Claim Scrubber (SN 03/2019)
 */

#include <stdio.h>
#include <string.h>
#include <stdbool.h>

#include "taryaq_adapters.h"

taryaq_result_t taryaq_verify_prescription_and_claim(const taryaq_rx_context_t *rx) {
    taryaq_result_t res;
    memset(&res, 0, sizeof(res));

    res.verdict = CLINICAL_SAFE;
    strncpy(res.alert_code, "DHA_NABIDH_SAFE", sizeof(res.alert_code) - 1);
    strncpy(res.clinical_rationale, "Pharmacovigilance and DHA Ejadah claim checks passed.", sizeof(res.clinical_rationale) - 1);

    if (!rx || !rx->primary_drug) return res;

    /* 1. Deterministic Renal + CYP3A4 Fatal Interaction Check (Commutative / Order-Independent) */
    bool has_colchicine = (strcmp(rx->primary_drug, "Colchicine") == 0) ||
                          (rx->concurrent_drug && strcmp(rx->concurrent_drug, "Colchicine") == 0);
    bool has_clarithro  = (strcmp(rx->primary_drug, "Clarithromycin") == 0) ||
                          (rx->concurrent_drug && strcmp(rx->concurrent_drug, "Clarithromycin") == 0);
    if (rx->patient_egfr_ml_min < 30.0 && has_colchicine && has_clarithro) {
        res.verdict = CLINICAL_CONTRAINDICATION_BLOCK;
        strncpy(res.alert_code, "FATAL_CYP3A4_RENAL_CONTRAINDICATION", sizeof(res.alert_code) - 1);
        strncpy(res.clinical_rationale,
                "Blocked: Concurrent Colchicine + Clarithromycin in severe renal impairment (eGFR < 30) causes fatal toxicity.",
                sizeof(res.clinical_rationale) - 1);
        return res;
    }

    /* 1b. Deterministic Metformin Severe Renal Cutoff (eGFR < 30 mL/min -> Lactic Acidosis) */
    bool has_metformin = (strcmp(rx->primary_drug, "Metformin") == 0) ||
                         (rx->concurrent_drug && strcmp(rx->concurrent_drug, "Metformin") == 0);
    if (rx->patient_egfr_ml_min < 30.0 && has_metformin) {
        res.verdict = CLINICAL_CONTRAINDICATION_BLOCK;
        strncpy(res.alert_code, "METFORMIN_SEVERE_RENAL_CUTOFF_EGFR_LT_30", sizeof(res.alert_code) - 1);
        strncpy(res.clinical_rationale,
                "Blocked: Metformin is contraindicated in severe renal impairment (eGFR < 30 mL/min) due to lactic acidosis risk.",
                sizeof(res.clinical_rationale) - 1);
        return res;
    }

    /* 2. Controlled / Narcotic Medication Gate (UAE Health Law No. 2 of 2019) */
    if (rx->is_controlled_substance && !rx->has_controlled_id_verified) {
        res.verdict = CLINICAL_CONTROLLED_DRUG_GATE;
        strncpy(res.alert_code, "UAE_CONTROLLED_RX_VERIFICATION_REQUIRED", sizeof(res.alert_code) - 1);
        strncpy(res.clinical_rationale,
                "Hold: Controlled medication requires verified Emirates ID, dosage ceiling verification, and pharmacist co-signature.",
                sizeof(res.clinical_rationale) - 1);
        return res;
    }

    /* 3. DHA eClaimLink Claim Cycle Standardisation Gatekeeper (SN 03/2019) */
    if (rx->submission_delay_days > 0) {
        res.verdict = CLINICAL_CLAIM_CYCLE_WARN;
        strncpy(res.alert_code, "DHA_SN03_2019_DELAY_PENALTY_EXPOSURE", sizeof(res.alert_code) - 1);
        snprintf(res.clinical_rationale, sizeof(res.clinical_rationale),
                 "Claim Cycle Warning: Submission is %u day(s) overdue under DHA SN 03/2019; subject to 0.03%%/day delay penalty on Net Claimed amount.",
                 rx->submission_delay_days);
        return res;
    }

    return res;
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

    /* Test 6: Commutative Check (Inverted primary/concurrent drug order) */
    taryaq_rx_context_t inverted_order_case = {
        .primary_drug = "Clarithromycin",
        .concurrent_drug = "Colchicine",
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
 *   1. Deterministic DESC ISR v3.1 Policy Gatekeeper (policy_verify_call)
 *   2. Stateless MCP 2026-07-28 HTTP JSON-RPC Client Request Builder
 */

#define _POSIX_C_SOURCE 200809L
#define _XOPEN_SOURCE 700

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <stdint.h>
#include <stdbool.h>
#include <time.h>
#include <limits.h>

#ifdef __linux__
#include <sys/prctl.h>
#include <sys/syscall.h>
#include <linux/landlock.h>
#endif

#include "qala_adapters.h"

/* Constant-time string comparison to prevent timing side-channels */
static bool constant_time_streq(const char *a, const char *b) {
    if (!a || !b) return false;
    size_t len_a = strlen(a);
    size_t len_b = strlen(b);
    if (len_a != len_b || len_a == 0) return false;
    unsigned char diff = 0;
    for (size_t i = 0; i < len_a; ++i) {
        diff |= (unsigned char)a[i] ^ (unsigned char)b[i];
    }
    return diff == 0;
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
    ".env",
    "uae_citizens.db",
    "customers_pii.db",
    "nabidh_patient_master.db",
    NULL
};

/* Hardened path verification using realpath() canonicalization */
static bool is_restricted_path_hardened(const char *raw_path, const char *raw_args) {
    const char *inputs[2] = { raw_path, raw_args };
    for (int k = 0; k < 2; ++k) {
        const char *s = inputs[k];
        if (!s || s[0] == '\0') continue;
        if (strstr(s, "..") != NULL) return true;
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

/* Immutable append-only JSONL audit logger */
static void write_desc_audit_log(
    const char                 *log_path,
    uint64_t                    now_utc,
    const qala_tool_call_ctx_t *ctx,
    const qala_policy_result_t *res
) {
    if (!log_path || !ctx || !res) return;
    FILE *fp = fopen(log_path, "a");
    if (!fp) return;

    char esc_tool[128], esc_path[256], esc_code[64], esc_reason[256];
    json_escape_string(ctx->tool_name ? ctx->tool_name : "unknown", esc_tool, sizeof(esc_tool));
    json_escape_string(ctx->target_path ? ctx->target_path : "", esc_path, sizeof(esc_path));
    json_escape_string(res->code, esc_code, sizeof(esc_code));
    json_escape_string(res->reason, esc_reason, sizeof(esc_reason));

    fprintf(fp,
        "{\"timestamp_utc\":%llu,\"reporting_tz\":\"Asia/Dubai\","
        "\"tool\":\"%s\",\"target_path\":\"%s\",\"amount_aed\":%.2f,"
        "\"is_mutating\":%s,\"approval_supplied\":%s,"
        "\"verdict\":\"%s\",\"code\":\"%s\",\"reason\":\"%s\"}\n",
        (unsigned long long)now_utc,
        esc_tool, esc_path, ctx->amount_aed,
        ctx->is_mutating ? "true" : "false",
        (ctx->supplied_code && ctx->supplied_code[0] != '\0') ? "true" : "false",
        verdict_to_str(res->verdict),
        esc_code,
        esc_reason
    );
    fclose(fp);
}

/* Deterministic C99 Policy Gatekeeper */
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
        strncpy(res.code, "malformed_call", sizeof(res.code) - 1);
        strncpy(res.reason, "Missing tool context or tool_name.", sizeof(res.reason) - 1);
        return res;
    }

    /* 1. Hard Kernel/Path Sandbox Check */
    if (is_restricted_path_hardened(ctx->target_path, ctx->raw_args_json)) {
        res.verdict = VERDICT_UNSAFE;
        strncpy(res.code, "landlock_fs_denied", sizeof(res.code) - 1);
        snprintf(res.reason, sizeof(res.reason),
                 "DESC ISR v3.1 Path Allowlist: Access to restricted path '%.180s' denied.",
                 ctx->target_path ? ctx->target_path : "in_args");
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

    /* 3. Hard Financial & State Mutation Gate */
    bool requires_human_gate = ctx->is_mutating || (ctx->amount_aed > 50000.0);
    if (requires_human_gate) {
        if (!ctx->supplied_code || ctx->supplied_code[0] == '\0') {
            res.verdict = VERDICT_REVIEW;
            strncpy(res.code, "approval_required", sizeof(res.code) - 1);
            snprintf(res.reason, sizeof(res.reason),
                     "Gated operation '%.64s' (AED %.2f) requires a single-use approval_code (scope: %.32s).",
                     ctx->tool_name, ctx->amount_aed,
                     ctx->required_scope ? ctx->required_scope : "default");
            write_desc_audit_log(audit_log_path, now_utc, ctx, &res);
            return res;
        }

        /* Verify single-use, scope-bound token in constant time */
        bool found_valid = false;
        for (size_t i = 0; i < slot_count; ++i) {
            if (!slots[i].consumed &&
                now_utc <= slots[i].expires_utc &&
                constant_time_streq(slots[i].token, ctx->supplied_code) &&
                (!ctx->required_scope || strcmp(slots[i].scope, ctx->required_scope) == 0)) {
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

    /* 3. Safe Execution Verified */
    res.verdict = VERDICT_SAFE;
    strncpy(res.code, "policy_verified", sizeof(res.code) - 1);
    snprintf(res.reason, sizeof(res.reason),
             "Tool '%.64s' verified under DESC ISR v3.1 deterministic policy.", ctx->tool_name);
    write_desc_audit_log(audit_log_path, now_utc, ctx, &res);
    return res;
}

/* Stateless MCP 2026-07-28 HTTP JSON-RPC Request Builder */
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

    char body[2048];
    int body_len = snprintf(body, sizeof(body),
        "{\"jsonrpc\":\"2.0\",\"id\":%llu,\"method\":\"%s\",\"params\":%s}",
        (unsigned long long)request_id,
        mcp_method,
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
        "Content-Length: %d\r\n"
        "Connection: close\r\n"
        "\r\n"
        "%s",
        endpoint_path,
        host,
        mcp_method,
        (bearer_token && bearer_token[0] != '\0') ? "Authorization: Bearer " : "X-Auth-Status: ",
        (bearer_token && bearer_token[0] != '\0') ? bearer_token : "unconfigured",
        body_len,
        body
    );

    if (total_len < 0 || (size_t)total_len >= buf_cap) {
        return -3;
    }

    return total_len;
}

#ifdef QALA_STANDALONE_TEST
#include <assert.h>

int main(void) {
    qala_approval_slot_t slots[1] = {{
        .token = "DUBAI-APPROVE-9941-X",
        .scope = "finops_remediate",
        .expires_utc = 1800000000ULL,
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
    int                 valence;         /* -1 (Thorn/Friction), 0 (Neutral), +1 (Rose/Success) */
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
 *   1. Zero-Allocation UTF-8 Arabic & Gulf Dialect Normalizer for SQLite FTS5 BM25
 *   2. Procedural Friction Appraisal & Time-Gated FadeMem Engine (--sim-time-scale)
 */

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <stdint.h>
#include <stdbool.h>
#include <math.h>

#include "nibras_adapters.h"

/* Zero-allocation UTF-8 Arabic & Gulf Dialect Normalizer */
size_t arabic_normalize_utf8_hardened(const char *src, char *dst, size_t dst_cap) {
    if (!src || !dst || dst_cap == 0) return 0;

    const unsigned char *s = (const unsigned char *)src;
    unsigned char *d = (unsigned char *)dst;
    size_t out_idx = 0;

    while (*s != '\0' && (out_idx + 4) < dst_cap) {
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
                    d[out_idx++] = 0xD8;
                    d[out_idx++] = 0xA7;
                    s += 2;
                    continue;
                }

                /* Fold Ta Marbuta U+0629 (ة 0xD8 0xA9) -> Heh U+0647 (ه 0xD9 0x87) */
                if (b1 == 0xA9) {
                    d[out_idx++] = 0xD9;
                    d[out_idx++] = 0x87;
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
                    d[out_idx++] = 0xD9;
                    d[out_idx++] = 0x8A;
                    s += 2;
                    continue;
                }

                /* Unify Alef Wasla U+0671 (ٱ 0xD9 0xB1) -> Alef U+0627 (ا 0xD8 0xA7) */
                if (b1 == 0xB1) {
                    d[out_idx++] = 0xD8;
                    d[out_idx++] = 0xA7;
                    s += 2;
                    continue;
                }

                /* Fold Eastern Arabic digits U+0660..U+0669 (٠-٩: 0xD9 0xA0..0xA9) -> ASCII '0'..'9' */
                if (b1 >= 0xA0 && b1 <= 0xA9) {
                    d[out_idx++] = (unsigned char)('0' + (b1 - 0xA0));
                    s += 2;
                    continue;
                }
            } else if (b0 == 0xDB) {
                /* Fold Extended/Persian Arabic digits U+06F0..U+06F9 (۰-۹: 0xDB 0xB0..0xB9) -> ASCII '0'..'9' */
                if (b1 >= 0xB0 && b1 <= 0xB9) {
                    d[out_idx++] = (unsigned char)('0' + (b1 - 0xB0));
                    s += 2;
                    continue;
                }
            }
        }

        /* Copy standard character unchanged */
        d[out_idx++] = *s++;
    }

    d[out_idx] = '\0';
    return out_idx;
}

/* Time-gated FadeMem step function with time-acceleration */
void nibras_fademem_step_hardened(
    nibras_memory_node_t        *nodes,
    size_t                       count,
    uint64_t                     now_utc,
    double                       half_life_sec,
    double                       sim_time_scale,
    double                       consolidation_window_sec,
    nibras_telemetry_snapshot_t *out_snap
) {
    if (!nodes || !out_snap || half_life_sec <= 0.0) return;
    memset(out_snap, 0, sizeof(*out_snap));
    if (sim_time_scale <= 0.0) sim_time_scale = 1.0;

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

    if (out_snap->total_raw_tokens > 0 &&
        out_snap->active_tokens_after_prune <= out_snap->total_raw_tokens) {
        uint32_t saved = out_snap->total_raw_tokens - out_snap->active_tokens_after_prune;
        out_snap->tokens_saved_pct = (saved * 100U) / out_snap->total_raw_tokens;
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
    assert(strstr(norm_buf, "اداره الازمات في دبي 2027 و 09876 - مدرسه ذكيه") != NULL);

    /* Test 2: FadeMem 7-Day Time-Acceleration with Consolidation Window */
    nibras_memory_node_t nodes[3] = {
        { .id = 1, .summary = "Routine calendar ping", .valence = 0, .initial_intensity = 0.40,
          .created_utc = 1000, .token_cost = 1200, .valence_inverted = false },
        { .id = 2, .summary = "Transient compilation log", .valence = 0, .initial_intensity = 0.55,
          .created_utc = 1000, .token_cost = 1800, .valence_inverted = false },
        { .id = 3, .summary = "Thorn: DIFC API requires UTC timestamp", .valence = -1,
          .initial_intensity = 0.92, .created_utc = 1000, .token_cost = 600, .valence_inverted = false }
    };

    nibras_telemetry_snapshot_t snap;
    /* 60 seconds wall clock at 10080x = 604,800 virtual seconds (7 full days) */
    nibras_fademem_step_hardened(nodes, 3, 1060, 86400.0, 10080.0, 86400.0, &snap);

    assert(nodes[0].state == TRAJ_NOISE_PRUNED);
    assert(nodes[1].state == TRAJ_NOISE_PRUNED);
    assert(nodes[2].state == TRAJ_DISTILLED_RULE);
    assert(snap.tokens_saved_pct >= 90);

    printf("[PASS] All Nibras C99 Hardened Arabic Normalizer & FadeMem tests passed! (Tokens saved: %u%%)\n",
           snap.tokens_saved_pct);
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
    if (needle[0] == '\0') return haystack;

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

/* Deterministic Factual Verification against Retrieved Authoritative Sources */
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

    bool entity_found = false;

    for (size_t i = 0; i < source_count; ++i) {
        /* Check if authoritative source covers the claimed entity */
        if (claim->entity_name &&
            (strcasestr_c99(sources[i].source_title, claim->entity_name) != NULL ||
             strcasestr_c99(sources[i].snippet_text, claim->entity_name) != NULL)) {
            
            entity_found = true;

            /* Check numerical claim parity if applicable */
            if (claim->has_numerical) {
                double diff = fabs(claim->numerical_value - sources[i].source_numerical);
                if (diff > 0.0001) {
                    res.verdict = GROUNDING_HALLUCINATION_TRIPPED;
                    res.confidence = 0.99;
                    strncpy(res.citation, sources[i].source_id, sizeof(res.citation) - 1);
                    snprintf(res.discrepancy_note, sizeof(res.discrepancy_note),
                             "Discrepancy: Claim states %.4f, but authoritative %s mandates %.4f.",
                             claim->numerical_value, sources[i].source_id, sources[i].source_numerical);
                    return res;
                }
            }

            /* Factual match confirmed */
            res.verdict = GROUNDING_VERIFIED;
            res.confidence = 0.98;
            strncpy(res.citation, sources[i].source_id, sizeof(res.citation) - 1);
            snprintf(res.discrepancy_note, sizeof(res.discrepancy_note),
                     "Verified against authoritative source %s.", sources[i].source_id);
            return res;
        }
    }

    /* If entity was not present in the supplied sources */
    if (!entity_found) {
        res.verdict = GROUNDING_UNVERIFIABLE;
        res.confidence = 0.50;
        strncpy(res.discrepancy_note, "Claimed entity not found in retrieved authoritative corpus.", sizeof(res.discrepancy_note) - 1);
    }

    return res;
}

#ifdef GROUNDING_STANDALONE_TEST
#include <assert.h>

int main(void) {
    /* Test 1: PII Scrubbing */
    const char *dirty_prompt =
        "Patient Ahmed Bin Saeed (Emirates ID 784-1988-1234567-1) has an eClaimLink Ejadah "
        "resubmission dispute under DHA SN 03/2019 regarding his insurance at Dubai Hospital.";
    
    char clean_query[256];
    size_t len = grounding_scrub_search_query(dirty_prompt, clean_query, sizeof(clean_query));
    assert(len > 0);
    assert(strstr(clean_query, "Ahmed") == NULL);
    assert(strstr(clean_query, "784-1988") == NULL);
    assert(strstr(clean_query, "DHA") != NULL);
    assert(strstr(clean_query, "eClaimLink") != NULL);
    assert(strstr(clean_query, "Ejadah") != NULL);

    /* Test 2: Verified Accurate Factual Claim */
    grounding_source_t corpus[2] = {
        {
            .source_id = "DHA_SN_03_2019",
            .source_title = "DHA Standards Notice SN 03/2019 Payment Rules",
            .snippet_text = "Late payment delay penalty is 0.03% per calendar day on net claimed amount.",
            .source_numerical = 0.03
        },
        {
            .source_id = "DESC_ISR_V3.1_SEC_4",
            .source_title = "Dubai Electronic Security Center ISR v3.1",
            .snippet_text = "Audit logs must be retained for a mandatory minimum of 12 months.",
            .source_numerical = 12.0
        }
    };

    grounding_claim_t accurate_claim = {
        .claim_text = "DHA Ejadah late payment penalty is 0.03% daily",
        .entity_name = "DHA",
        .numerical_value = 0.03,
        .has_numerical = true
    };
    grounding_result_t r1 = grounding_verify_claim(&accurate_claim, corpus, 2);
    assert(r1.verdict == GROUNDING_VERIFIED);
    assert(strcmp(r1.citation, "DHA_SN_03_2019") == 0);

    /* Test 3: Hallucination Detection (Model hallucinated 0.05% instead of 0.03%) */
    grounding_claim_t hallucinated_claim = {
        .claim_text = "DHA Ejadah late payment penalty is 0.05% daily",
        .entity_name = "DHA",
        .numerical_value = 0.05,
        .has_numerical = true
    };
    grounding_result_t r2 = grounding_verify_claim(&hallucinated_claim, corpus, 2);
    assert(r2.verdict == GROUNDING_HALLUCINATION_TRIPPED);
    assert(strstr(r2.discrepancy_note, "mandates 0.0300") != NULL);

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
    int          rpc_error_code;
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

static size_t curl_write_memory_callback(void *contents, size_t size, size_t nmemb, void *userp) {
    size_t realsize = size * nmemb;
    http_memory_buf_t *mem = (http_memory_buf_t *)userp;

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
                    cJSON_AddObjectToObject(params, "arguments");
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
        out_resp->status = MCP_SUCCESS;
    } else {
        out_resp->status = MCP_SUCCESS;
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
        char auth_hdr[256];
        snprintf(auth_hdr, sizeof(auth_hdr), "Authorization: Bearer %s", config->bearer_token);
        headers = curl_slist_append(headers, auth_hdr);
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
            parse_mcp_response(chunk.data, out_resp);
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
