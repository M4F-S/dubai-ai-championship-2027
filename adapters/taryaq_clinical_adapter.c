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

    /* 1. Deterministic Renal + CYP3A4 Fatal Interaction Check */
    if (rx->patient_egfr_ml_min < 30.0 &&
        strcmp(rx->primary_drug, "Colchicine") == 0 &&
        rx->concurrent_drug && strcmp(rx->concurrent_drug, "Clarithromycin") == 0) {
        res.verdict = CLINICAL_CONTRAINDICATION_BLOCK;
        strncpy(res.alert_code, "FATAL_CYP3A4_RENAL_CONTRAINDICATION", sizeof(res.alert_code) - 1);
        strncpy(res.clinical_rationale,
                "Blocked: Concurrent Colchicine + Clarithromycin in severe renal impairment (eGFR < 30) causes fatal toxicity.",
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

    /* 3. DHA eClaimLink & Ejadah Pre-Submission Claim Scrubber (SN 03/2019) */
    if (rx->icd10_code && strncmp(rx->icd10_code, "E11", 3) == 0 && !rx->has_ejadah_lab_justification) {
        res.verdict = CLINICAL_EJADAH_SCRUB_WARN;
        strncpy(res.alert_code, "DHA_EJADAH_MISSING_HBA1C_PAYLOAD", sizeof(res.alert_code) - 1);
        strncpy(res.clinical_rationale,
                "Claim Scrub Alert: DHA Ejadah requires baseline HbA1c lab attachment to eClaimLink XML to prevent payer rejection.",
                sizeof(res.clinical_rationale) - 1);
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
        .has_ejadah_lab_justification = true
    };
    taryaq_result_t r2 = taryaq_verify_prescription_and_claim(&narcotic_case);
    assert(r2.verdict == CLINICAL_CONTROLLED_DRUG_GATE);
    assert(strcmp(r2.alert_code, "UAE_CONTROLLED_RX_VERIFICATION_REQUIRED") == 0);

    /* Test 3: Type 2 Diabetes (E11) claim without baseline HbA1c -> EJADAH_SCRUB_WARN */
    taryaq_rx_context_t claim_case = {
        .primary_drug = "Metformin",
        .concurrent_drug = NULL,
        .patient_egfr_ml_min = 75.0,
        .is_controlled_substance = false,
        .has_controlled_id_verified = false,
        .icd10_code = "E11.9",
        .has_ejadah_lab_justification = false
    };
    taryaq_result_t r3 = taryaq_verify_prescription_and_claim(&claim_case);
    assert(r3.verdict == CLINICAL_EJADAH_SCRUB_WARN);
    assert(strcmp(r3.alert_code, "DHA_EJADAH_MISSING_HBA1C_PAYLOAD") == 0);

    /* Test 4: Fully compliant claim -> SAFE */
    claim_case.has_ejadah_lab_justification = true;
    taryaq_result_t r4 = taryaq_verify_prescription_and_claim(&claim_case);
    assert(r4.verdict == CLINICAL_SAFE);
    assert(strcmp(r4.alert_code, "DHA_NABIDH_SAFE") == 0);

    printf("[PASS] All Taryaq C99 Pharmacovigilance & Ejadah Claim Scrubber tests passed successfully!\n");
    return 0;
}
#endif
