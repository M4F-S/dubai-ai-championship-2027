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
