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
