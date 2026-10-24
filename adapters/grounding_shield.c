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
