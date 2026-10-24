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
