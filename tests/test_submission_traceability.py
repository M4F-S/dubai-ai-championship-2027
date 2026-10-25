#!/usr/bin/env python3
"""
Master Submission Number Traceability & Structural Verification Battery (Task M-10)
Dubai Create AI Agents Championship 2026-2027

Acceptance Standard:
1. Every pitch deck has exactly 10 slides.
2. Canonical pitch structure: problem -> who pays -> live demo -> measured result -> why us -> architecture -> ask.
3. Architecture is strictly on Slide 7 or later.
4. Video script has exact 150-second timeline (0:00-0:30, 0:30-0:50, 0:50-1:30, 1:30-1:55, 1:55-2:15, 2:15-2:30).
5. All quantitative numbers cited in decks, script, and architecture report trace bit-for-bit to empirical files.
6. NUMBER_TRACEABILITY_MATRIX.md provides complete audit ledger mapping to repository files.
"""

import json
import os
import re
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent

class TestSubmissionTraceability(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.repo_root = REPO_ROOT
        cls.decks_dir = cls.repo_root / "docs" / "pitch_decks"
        cls.video_script_path = cls.repo_root / "docs" / "video_script.md"
        cls.arch_report_path = cls.repo_root / "docs" / "architecture_summary_report.md"
        cls.traceability_matrix_path = cls.repo_root / "docs" / "NUMBER_TRACEABILITY_MATRIX.md"

        # Empirical data sources
        cls.bench_results_json = cls.repo_root / "bench" / "results.json"
        cls.golden_eval_json = cls.repo_root / "benchmarks" / "golden_eval_results.json"
        cls.golden_eval_report = cls.repo_root / "benchmarks" / "GOLDEN_EVAL_REPORT.md"
        cls.laya_model_card = cls.repo_root / "docs" / "models" / "LAYA_322M_MODEL_CARD.md"
        cls.pilot_template = cls.repo_root / "docs" / "pilot" / "PILOT_LETTER_TEMPLATE_DRAFT.md"
        cls.pilot_protocol = cls.repo_root / "docs" / "pilot" / "PILOT_PROTOCOL_BRIEF.md"

    def test_01_pitch_deck_slide_count_and_naming(self):
        """1. Verify every pitch deck exists and has exactly 10 slides."""
        deck_files = [
            "PITCH_DECK_TARYAQ_SOCIETAL.md",
            "PITCH_DECK_QALA_BUSINESS.md",
            "PITCH_DECK_NIBRAS_PERSONAL.md",
            "PITCH_DECK_NIBRAS_EXECUTIVE.md",
        ]

        for deck_name in deck_files:
            deck_path = self.decks_dir / deck_name
            self.assertTrue(deck_path.exists(), f"Missing pitch deck file: {deck_path}")
            content = deck_path.read_text(encoding="utf-8")

            slide_matches = re.findall(r"^###\s+Slide\s+(\d+):", content, flags=re.MULTILINE)
            slide_numbers = [int(s) for s in slide_matches]
            self.assertEqual(
                slide_numbers,
                list(range(1, 11)),
                f"Pitch deck {deck_name} must contain exactly slides 1 through 10. Found: {slide_numbers}"
            )
            self.assertEqual(
                len(slide_numbers),
                10,
                f"Pitch deck {deck_name} must have exactly 10 slides. Found: {len(slide_numbers)}"
            )

    def test_02_pitch_deck_canonical_structure(self):
        """2. Verify canonical pitch structure and Architecture strictly on Slide 7 or later."""
        deck_files = [
            "PITCH_DECK_TARYAQ_SOCIETAL.md",
            "PITCH_DECK_QALA_BUSINESS.md",
            "PITCH_DECK_NIBRAS_PERSONAL.md",
            "PITCH_DECK_NIBRAS_EXECUTIVE.md",
        ]

        for deck_name in deck_files:
            deck_path = self.decks_dir / deck_name
            content = deck_path.read_text(encoding="utf-8")

            # Extract headers for each slide
            slides = {}
            for match in re.finditer(r"^###\s+Slide\s+(\d+):\s*(.+)$", content, flags=re.MULTILINE):
                slides[int(match.group(1))] = match.group(2).lower()

            # Rule: Slide 1 = Title / Vision
            self.assertTrue(any(k in slides[1] for k in ["title", "vision", "hook"]))
            # Rule: Slide 2 = Problem / Crisis
            self.assertTrue(any(k in slides[2] for k in ["problem", "crisis", "hazard"]))
            # Rule: Slide 3 = Who Pays / Unit Economics / Financial Exposure
            self.assertTrue(any(k in slides[3] for k in ["who pays", "economics", "financial exposure"]))
            # Rule: Slide 4 = Live Demo Walkthrough
            self.assertTrue(any(k in slides[4] for k in ["live demo", "walkthrough", "demo"]))
            # Rule: Slide 5 = Measured Results / Empirical Benchmarks
            self.assertTrue(any(k in slides[5] for k in ["measured result", "benchmark"]))
            # Rule: Slide 6 = Why Us / Advantage / Lineage
            self.assertTrue(any(k in slides[6] for k in ["why us", "advantage", "lineage", "founder"]))
            # Rule: Architecture strictly on Slide 7 or later (never before Slide 7)
            arch_slide_found = None
            for s_num, s_title in slides.items():
                if "architecture" in s_title:
                    arch_slide_found = s_num
                    break
            self.assertIsNotNone(arch_slide_found, f"Architecture slide not found in {deck_name}")
            self.assertGreaterEqual(
                arch_slide_found,
                7,
                f"Architecture MUST be on Slide 7 or later in {deck_name}. Found on Slide {arch_slide_found}"
            )
            # Rule: Slide 10 = Ask / Roadmap
            self.assertTrue(any(k in slides[10] for k in ["ask", "roadmap"]))

    def test_03_video_script_timeline_and_duration(self):
        """3. Verify 2.5-minute video screenplay 150-second timeline breakdown."""
        self.assertTrue(self.video_script_path.exists())
        content = self.video_script_path.read_text(encoding="utf-8")

        # Must mention 150 seconds or 2.5 minutes
        self.assertIn("150 Seconds", content)

        # Check the 6 canonical scene time intervals
        intervals = [
            "0:00 – 0:30",
            "0:30 – 0:50",
            "0:50 – 1:30",
            "1:30 – 1:55",
            "1:55 – 2:15",
            "2:15 – 2:30",
        ]
        for interval in intervals:
            self.assertIn(interval, content, f"Video script missing required timestamp interval: {interval}")

        # Check required narrative themes
        self.assertIn("Mohamed Fathy", content)
        self.assertIn("Colchicine", content)
        self.assertIn("Clarithromycin", content)
        self.assertIn("SN 03/2019", content)
        self.assertIn("0.03%", content)
        self.assertIn("ws://127.0.0.1:8787", content)
        self.assertIn("TARYAQ-OVERRIDE-8842-CLIN", content)
        self.assertNotIn("Prime Healthcare Group", content)

    def test_04_hardware_bench_numbers_traceability(self):
        """4. Verify hardware and bandwidth physics metrics trace to bench/results.json."""
        self.assertTrue(self.bench_results_json.exists())
        with open(self.bench_results_json, "r", encoding="utf-8") as f:
            bench_data = json.load(f)

        # Check key physics in results.json
        peak_bw = bench_data["system_specification"]["memory_subsystem"]["theoretical_peak_bandwidth_gb_s"]
        self.assertEqual(peak_bw, 89.6)

        model_size = bench_data["system_specification"]["model"]["file_size_gb"]
        self.assertEqual(model_size, 4.5)

        tok_4k = bench_data["empirical_benchmark_table"][0]["gen_speed_tok_s"]
        self.assertEqual(tok_4k, 19.91)

        tok_8k = bench_data["empirical_benchmark_table"][1]["gen_speed_tok_s"]
        self.assertEqual(tok_8k, 16.42)

        tok_16k = bench_data["empirical_benchmark_table"][2]["gen_speed_tok_s"]
        self.assertEqual(tok_16k, 5.5)

        gbnf_success = bench_data["tool_call_validation"]["gbnf_constrained"]["success_rate_pct"]
        self.assertEqual(gbnf_success, 100.0)

        unconstrained_success = bench_data["tool_call_validation"]["unconstrained"]["success_rate_pct"]
        self.assertEqual(unconstrained_success, 68.0)

        # Confirm these numbers are present in decks and architecture report
        for path in [
            self.decks_dir / "PITCH_DECK_TARYAQ_SOCIETAL.md",
            self.decks_dir / "PITCH_DECK_QALA_BUSINESS.md",
            self.arch_report_path,
            self.video_script_path,
        ]:
            text = path.read_text(encoding="utf-8")
            self.assertIn("89.6", text, f"Missing 89.6 GB/s in {path.name}")
            self.assertIn("19.91", text, f"Missing 19.91 tok/s in {path.name}")
            self.assertIn("68.0%", text, f"Missing 68.0% in {path.name}")
            self.assertIn("100.0%", text, f"Missing 100.0% in {path.name}")

    def test_05_laya_model_metrics_traceability(self):
        """5. Verify Laya Multilingual 322M calibration & abstention metrics."""
        self.assertTrue(self.laya_model_card.exists())
        card_text = self.laya_model_card.read_text(encoding="utf-8")

        # Required empirical constants in Model Card
        self.assertIn("322M", card_text)
        self.assertIn("2,400", card_text)
        self.assertIn("400 synthetic UAE patient cohorts", card_text)
        self.assertIn("0.3954", card_text)  # Raw ECE
        self.assertIn("0.0919", card_text)  # Calibrated ECE
        self.assertIn("13.89%", card_text)  # Abstention
        self.assertIn("100.00%", card_text) # Retained Accuracy
        self.assertIn("0.050 ms", card_text) # CPU latency

        # Confirm appearance in submission files
        for path in [
            self.decks_dir / "PITCH_DECK_TARYAQ_SOCIETAL.md",
            self.decks_dir / "PITCH_DECK_QALA_BUSINESS.md",
            self.decks_dir / "PITCH_DECK_NIBRAS_PERSONAL.md",
            self.arch_report_path,
        ]:
            text = path.read_text(encoding="utf-8")
            self.assertIn("322M", text, f"Missing 322M in {path.name}")
            self.assertIn("0.0919", text, f"Missing 0.0919 ECE in {path.name}")
            self.assertIn("13.89%", text, f"Missing 13.89% in {path.name}")
            self.assertIn("<40 ms", text, f"Missing <40 ms in {path.name}")

    def test_06_golden_eval_and_ablation_traceability(self):
        """6. Verify Golden 30 and Section 5.4 Ablation study metrics."""
        self.assertTrue(self.golden_eval_report.exists())
        report_text = self.golden_eval_report.read_text(encoding="utf-8")

        # Golden 30 execution metrics
        self.assertIn("240 trials", report_text)
        self.assertIn("100.0%", report_text)

        # Section 5.4 Ablation Table values
        # Row 1: Jais 3 7B alone | 36.0% | 754.0 ms | 41.0% | 0.0%
        self.assertIn("36.0%", report_text)
        self.assertIn("754.0 ms", report_text)
        self.assertIn("41.0%", report_text)
        # Row 2: 7B + Laya triage | 74.5% | 748.4 ms | 5.5% | 14.5%
        self.assertIn("74.5%", report_text)
        self.assertIn("748.4 ms", report_text)
        self.assertIn("5.5%", report_text)
        self.assertIn("14.5%", report_text)
        # Row 3: 7B + Laya + deterministic verifier | 88.0% | 202.1 ms | 0.0% | 12.0%
        self.assertIn("88.0%", report_text)
        self.assertIn("202.1 ms", report_text)
        self.assertIn("0.0%", report_text)
        self.assertIn("12.0%", report_text)

        # Confirm Section 5.4 ablation table appears in all 3 pitch decks
        for deck_name in [
            "PITCH_DECK_TARYAQ_SOCIETAL.md",
            "PITCH_DECK_QALA_BUSINESS.md",
            "PITCH_DECK_NIBRAS_PERSONAL.md",
        ]:
            deck_text = (self.decks_dir / deck_name).read_text(encoding="utf-8")
            self.assertIn("36.0%", deck_text, f"Missing 36.0% in {deck_name}")
            self.assertIn("754.0 ms", deck_text, f"Missing 754.0 ms in {deck_name}")
            self.assertIn("41.0%", deck_text, f"Missing 41.0% in {deck_name}")
            self.assertIn("74.5%", deck_text, f"Missing 74.5% in {deck_name}")
            self.assertIn("88.0%", deck_text, f"Missing 88.0% in {deck_name}")
            self.assertIn("202.1 ms", deck_text, f"Missing 202.1 ms in {deck_name}")

    def test_07_clinical_pilot_letter_traceability(self):
        """7. Verify Clinical Pilot draft template and protocol brief governance integrity."""
        self.assertTrue(self.pilot_template.exists(), "Missing draft pilot template")
        self.assertTrue(self.pilot_protocol.exists(), "Missing protocol brief")
        template_text = self.pilot_template.read_text(encoding="utf-8")
        protocol_text = self.pilot_protocol.read_text(encoding="utf-8")

        # Must be watermarked draft with placeholders
        self.assertIn("DRAFT — UNSIGNED — NOT AN AGREEMENT", template_text)
        self.assertIn("[PARTNER HEALTHCARE ENTITY NAME]", template_text)

        # Protocol brief must contain authentic clinical and regulatory citations
        required_citations = [
            "$N = 500$ consecutive outpatient electronic prescriptions",
            "$N = 500$ paired electronic claim XML payloads",
            "Q1 2027",
            "Mohamed Fathy, BPharm",
            "0.03%",
            "UAE Federal Law No. 2 of 2019",
            "DHA SN 03/2019",
            "SHADOW_ADVISORY_MODE",
        ]
        for citation in required_citations:
            self.assertIn(citation, protocol_text, f"Missing protocol citation: {citation}")

        # Strict negative governance check: no active document in docs/ may claim an executed agreement or fabricated entity
        forbidden = [
            "Prime Healthcare Group LLC",
            "DHA-FL-004921",
            "MOHAP-DXB-94812",
            "Dr. Tariq Al-Hashimi",
            "Dr. Mariam Bin Salem",
            "DHA-P-44019",
            "DHA-P-58204",
        ]
        taryaq_deck = (self.decks_dir / "PITCH_DECK_TARYAQ_SOCIETAL.md").read_text(encoding="utf-8")
        arch_report = self.arch_report_path.read_text(encoding="utf-8")
        for f in forbidden:
            self.assertNotIn(f, template_text, f"Forbidden entity {f} in template")
            self.assertNotIn(f, protocol_text, f"Forbidden entity {f} in protocol")
            self.assertNotIn(f, taryaq_deck, f"Forbidden entity {f} in Taryaq deck")
            self.assertNotIn(f, arch_report, f"Forbidden entity {f} in architecture report")

    def test_08_number_traceability_matrix_completeness(self):
        """8. Verify NUMBER_TRACEABILITY_MATRIX.md exists, has provenance schema, and every raw log exists."""
        self.assertTrue(self.traceability_matrix_path.exists())
        matrix_text = self.traceability_matrix_path.read_text(encoding="utf-8")

        # Verify key rows exist in table
        rows_to_check = [
            "89.6 GB/s",
            "19.91 tok/s",
            "50.23 ms/tok",
            "68.0%",
            "100.0%",
            "322M",
            "2,400 examples",
            "0.3954",
            "0.0919",
            "13.89%",
            "30 tasks",
            "240 executions",
            "36.0%",
            "754.0 ms",
            "88.0%",
            "202.1 ms",
            "Prospective Evaluation Protocol (Unsigned Draft)",
            "PILOT_LETTER_TEMPLATE_DRAFT.md",
            "0.03% per calendar day",
            "TARYAQ-OVERRIDE-8842-CLIN",
            "97% token savings",
        ]
        for row in rows_to_check:
            self.assertIn(row, matrix_text, f"Number Traceability Matrix missing row: {row}")

        # Assert unverified claims (AST Symbol Indexer) are purged
        self.assertNotIn("AST Symbol Index", matrix_text)
        self.assertNotIn("AST Token Savings", matrix_text)

        # Parse table rows and verify every Raw Log / Evidence Path exists on disk
        lines = matrix_text.splitlines()
        table_rows = [l for l in lines if l.startswith("| **") and not l.startswith("| #")]
        self.assertGreaterEqual(len(table_rows), 60, "Expected at least 60 verified rows in matrix")

        for r in table_rows:
            cols = [c.strip() for c in r.split("|")]
            # Format: ['', '#', 'Domain / Category', 'Exact Value / Claim', 'Context in Submission', 'Backing Repository File', 'Raw Log / Evidence Path', 'Machine / Environment', 'Provenance Timestamp', 'Verification Command', '']
            self.assertGreaterEqual(len(cols), 8, f"Malformed row in matrix: {r}")
            raw_path_col = cols[6].strip("`").strip()
            # If path has multiple or notes, extract file path
            m = re.search(r"([\w\-./]+\.\w+)", raw_path_col)
            self.assertIsNotNone(m, f"Could not find valid file path in Raw Log column: '{raw_path_col}' (row: {r})")
            rel_file = m.group(1)
            file_on_disk = self.repo_root / rel_file
            self.assertTrue(file_on_disk.exists(), f"Raw log / evidence path does not exist on disk: {rel_file} (from row: {r})")


if __name__ == "__main__":
    unittest.main()
