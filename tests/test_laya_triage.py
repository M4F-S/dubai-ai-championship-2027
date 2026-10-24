#!/usr/bin/env python3
"""
tests/test_laya_triage.py
-------------------------
Deterministic Verification Battery for Laya Multilingual 322M Calibrated Triage.
Part of the Dubai AI Agents Championship 2026-2027 (Task M-07).

Validates:
1. Dataset generation: 2,400+ examples, exact 10 canonical sovereign questions,
   50% Arabic / 50% English coverage, zero patient-ID overlap across splits.
2. Baseline fine-tuned accuracy on held-out test split (> 75% target).
3. Calibration via dev temperature scaling: ECE improves from > 0.30 to < 0.10.
4. Abstention mechanism at tau = 0.85 (5-15% abstention rate, post-abstention
   accuracy >= 85%, clean routing to physician override / deterministic verifier).
5. CPU inference latency benchmark (< 50 ms per sample).
"""

import os
import sys
import json
import unittest
import time

# Ensure repository root is in sys.path
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from adapters.laya_triage_adapter import (
    LayaTriageAdapter,
    CANONICAL_QUESTIONS,
    DecisionOutput,
    EvaluationReport
)

DATASET_DIR = os.path.join(PROJECT_ROOT, "benchmarks", "laya_dataset")
TRAIN_FILE = os.path.join(DATASET_DIR, "train.jsonl")
DEV_FILE = os.path.join(DATASET_DIR, "dev.jsonl")
TEST_FILE = os.path.join(DATASET_DIR, "test.jsonl")
SUMMARY_FILE = os.path.join(DATASET_DIR, "dataset_summary.json")


class TestLayaMultilingualTriage(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        """Initializes adapter and executes dev calibration fitting."""
        cls.adapter = LayaTriageAdapter(abstain_threshold=0.85)
        if os.path.exists(DEV_FILE):
            cls.adapter.fit_calibration_on_dev(DEV_FILE)
        cls.report = cls.adapter.evaluate(TEST_FILE, abstain_threshold=0.85)

    def test_01_dataset_generation_and_integrity(self):
        """
        a) Verify dataset files exist and have >= 2,400 total labeled examples.
        b) Verify exact 10 canonical questions are represented.
        c) Verify exact 50% Arabic and 50% English language split.
        d) Verify strict patient-level partition with ZERO patient overlap.
        """
        self.assertTrue(os.path.exists(TRAIN_FILE), f"Missing {TRAIN_FILE}")
        self.assertTrue(os.path.exists(DEV_FILE), f"Missing {DEV_FILE}")
        self.assertTrue(os.path.exists(TEST_FILE), f"Missing {TEST_FILE}")
        self.assertTrue(os.path.exists(SUMMARY_FILE), f"Missing {SUMMARY_FILE}")

        with open(TRAIN_FILE, "r", encoding="utf-8") as f:
            train_data = [json.loads(line) for line in f]
        with open(DEV_FILE, "r", encoding="utf-8") as f:
            dev_data = [json.loads(line) for line in f]
        with open(TEST_FILE, "r", encoding="utf-8") as f:
            test_data = [json.loads(line) for line in f]

        total_samples = len(train_data) + len(dev_data) + len(test_data)
        self.assertGreaterEqual(total_samples, 2400, f"Total samples {total_samples} < 2,400")
        self.assertEqual(len(train_data), 1680, "Train split must contain 1,680 examples (70%)")
        self.assertEqual(len(dev_data), 360, "Dev split must contain 360 examples (15%)")
        self.assertEqual(len(test_data), 360, "Test split must contain 360 examples (15%)")

        # Verify all 10 canonical questions are represented
        all_records = train_data + dev_data + test_data
        dataset_questions = set(r["question_id"] for r in all_records)
        self.assertEqual(
            dataset_questions,
            set(CANONICAL_QUESTIONS.keys()),
            "Dataset does not contain exact 10 canonical question heads"
        )

        # Verify 50% Arabic and 50% English language split
        ar_count = sum(1 for r in all_records if r["language"] == "ar")
        en_count = sum(1 for r in all_records if r["language"] == "en")
        self.assertEqual(ar_count, 1200, "Must have exactly 1,200 Arabic examples")
        self.assertEqual(en_count, 1200, "Must have exactly 1,200 English examples")
        self.assertEqual(ar_count, en_count, "Arabic and English samples must be exactly balanced 50/50")

        # Verify zero patient ID leakage across splits
        train_patients = set(r["patient_id"] for r in train_data)
        dev_patients = set(r["patient_id"] for r in dev_data)
        test_patients = set(r["patient_id"] for r in test_data)

        self.assertEqual(len(train_patients & dev_patients), 0, "Patient leakage between train and dev!")
        self.assertEqual(len(train_patients & test_patients), 0, "Patient leakage between train and test!")
        self.assertEqual(len(dev_patients & test_patients), 0, "Patient leakage between dev and test!")

        total_patients = len(train_patients) + len(dev_patients) + len(test_patients)
        self.assertEqual(total_patients, 400, "Must have 400 distinct patient cohorts")

    def test_02_baseline_accuracy(self):
        """
        Verify baseline fine-tuned accuracy on held-out test split exceeds
        the 75% target (> 75.0%).
        """
        self.assertGreater(
            self.report.overall_accuracy,
            0.75,
            f"Overall test accuracy {self.report.overall_accuracy * 100:.2f}% is below 75% target"
        )
        # Verify per-question accuracy for each head
        for q_id, acc in self.report.per_question_accuracy.items():
            self.assertGreaterEqual(
                acc,
                0.70,
                f"Question {q_id} accuracy {acc * 100:.2f}% is below acceptable 70% threshold"
            )

    def test_03_temperature_scaling_calibration(self):
        """
        Verify temperature scaling on dev set significantly improves calibration:
        - Raw uncalibrated ECE > 0.30 (published baseline: 0.466)
        - Calibrated ECE < 0.10 (published target: 0.081)
        - Net calibration error delta >= 0.20
        """
        self.assertGreater(
            self.report.raw_ece,
            0.30,
            f"Raw uncalibrated ECE {self.report.raw_ece:.4f} was not > 0.30"
        )
        self.assertLess(
            self.report.calibrated_ece,
            0.10,
            f"Calibrated ECE {self.report.calibrated_ece:.4f} was not < 0.10"
        )
        ece_improvement = self.report.raw_ece - self.report.calibrated_ece
        self.assertGreaterEqual(
            ece_improvement,
            0.20,
            f"ECE improvement {ece_improvement:.4f} is less than 0.20 delta requirement"
        )

    def test_04_abstention_safety_mechanism(self):
        """
        Verify abstention mechanism under threshold tau = 0.85:
        - Abstention rate is within expected 5% to 15% range.
        - Post-abstention accuracy on retained samples is higher than raw accuracy.
        - Post-abstention accuracy exceeds 85%.
        - Abstained outputs carry appropriate fallback routing.
        """
        rate = self.report.abstention_rate
        self.assertGreaterEqual(
            rate,
            0.05,
            f"Abstention rate {rate * 100:.2f}% is below expected 5% minimum"
        )
        self.assertLessEqual(
            rate,
            0.15,
            f"Abstention rate {rate * 100:.2f}% exceeds expected 15% maximum"
        )
        self.assertGreater(
            self.report.post_abstention_accuracy,
            self.report.overall_accuracy,
            "Post-abstention accuracy did not improve over un-abstained baseline"
        )
        self.assertGreaterEqual(
            self.report.post_abstention_accuracy,
            0.85,
            "Post-abstention accuracy is below 85% safety requirement"
        )

        # Test explicit routing behavior on borderline prompt
        borderline_clinical_prompt = (
            "Patient eGFR is 58.5 mL/min/1.73m2, Serum Creatinine 1.30 mg/dL, "
            "early CKD Stage 3a borderline impairment; dosage reduction suspect."
        )
        dec = self.adapter.predict(borderline_clinical_prompt, "Q3_RENAL_RISK_SUSPECT")
        self.assertTrue(dec.is_abstained)
        self.assertEqual(dec.predicted_label, "ABSTAIN")
        self.assertEqual(dec.fallback_route, "MANDATORY_PHYSICIAN_OVERRIDE")

        borderline_admin_prompt = (
            "eClaimLink claim CLM-DHA-11092 submitted at 13 days elapsed, close to statutory deadline."
        )
        dec_admin = self.adapter.predict(borderline_admin_prompt, "Q6_CLAIM_DELAY_PENALTY_RISK")
        self.assertTrue(dec_admin.is_abstained)
        self.assertEqual(dec_admin.predicted_label, "ABSTAIN")
        self.assertEqual(dec_admin.fallback_route, "DETERMINISTIC_VERIFIER")

    def test_05_inference_latency_benchmark(self):
        """
        Verify single-sample CPU inference latency is strictly < 50 ms.
        (Target: < 40 ms; typical pure Python is < 1 ms).
        """
        sample_prompt = (
            "تقييم سلامة التداخل الدوائي بين ميتفورمين و ليزينوبريل: "
            "لا يوجد تثبيط معنوي لإنزيم كبدي CYP3A4 والتوليفة العلاجية تعتبر آمنة."
        )
        latencies = []
        for _ in range(100):
            t0 = time.perf_counter()
            _ = self.adapter.predict(sample_prompt, "Q4_CYP3A4_INTERACTION_RISK")
            t1 = time.perf_counter()
            latencies.append((t1 - t0) * 1000.0)

        mean_lat = sum(latencies) / len(latencies)
        sorted_lat = sorted(latencies)
        p95_lat = sorted_lat[int(0.95 * len(sorted_lat))]

        self.assertLess(
            p95_lat,
            50.0,
            f"p95 inference latency {p95_lat:.3f} ms exceeds 50.0 ms SLA"
        )
        self.assertLess(
            mean_lat,
            40.0,
            f"Mean inference latency {mean_lat:.3f} ms exceeds 40.0 ms specification"
        )

    def test_06_bilingual_canonical_decisions(self):
        """
        Verifies correct top-1 decisions on canonical Arabic and English prompts.
        """
        # 1. Arabic CYP3A4 fatal contraindication
        ar_prompt = (
            "تحذير خطير: وصف دواء كولشيسين بالتزامن مع كلاريثروميسين. "
            "يمثل هذا التثبيط القوي لإنزيم CYP3A4 ومضخة P-gp خطراً مهدداً للحياة مع احتمالية تسمم حاد مميت. مانع طبي قاطع."
        )
        dec_ar = self.adapter.predict(ar_prompt, "Q4_CYP3A4_INTERACTION_RISK")
        self.assertEqual(dec_ar.predicted_label, "POTENT_CYP3A4_CONTRAINDICATION")
        self.assertFalse(dec_ar.is_abstained)
        self.assertGreater(dec_ar.confidence, 0.85)

        # 2. English DHA SN 03/2019 Claim Delay
        en_prompt = (
            "Claim Cycle Non-Compliance: eClaimLink submission CLM-DHA-44102 (AED 5000) "
            "submitted with 45 days delay. Incurs statutory 0.03%/day late submission penalty under DHA SN 03/2019 (§3.8.4)."
        )
        dec_en = self.adapter.predict(en_prompt, "Q6_CLAIM_DELAY_PENALTY_RISK")
        self.assertEqual(dec_en.predicted_label, "DHA_SN_03_2019_DELAY_PENALTY")
        self.assertFalse(dec_en.is_abstained)
        self.assertGreater(dec_en.confidence, 0.85)

        # 3. PII Leak Detection
        pii_prompt = (
            "بيانات مريض شخصية: الاسم أحمد بن راشد الكعبي، رقم الهوية الإماراتية 784-1988-1234567-1، هاتف +971-50-1234567."
        )
        dec_pii = self.adapter.predict(pii_prompt, "Q7_PII_LEAK_RISK")
        self.assertEqual(dec_pii.predicted_label, "SENSITIVE_EMIRATES_ID_OR_NAME_DETECTED")
        self.assertFalse(dec_pii.is_abstained)


if __name__ == "__main__":
    unittest.main()
