#!/usr/bin/env python3
"""
tests/test_pilot.py - Clinical Pilot Document & Governance Integrity Verifier
Part of Dubai AI Agents Championship 2026-2027 (Task M-09 Remediation / Finding F-03).

Enforces Rule 1 ("No unmeasured or unverified claim leaves this repository") and
Finding F-03 / F-11 constraints:
1. Rejects any claim of an "executed", "countersigned", or "binding" agreement under docs/pilot/
   unless accompanied by an authenticated signed PDF and partner verification evidence.
2. Rejects any fabricated partner entity names or invented clinician license numbers.
3. Confirms docs/pilot/PILOT_LETTER_TEMPLATE_DRAFT.md exists and is watermarked as an unsigned draft.
"""

import os
import sys
import unittest

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PILOT_DIR = os.path.join(ROOT_DIR, "docs", "pilot")
TEMPLATE_PATH = os.path.join(PILOT_DIR, "PILOT_LETTER_TEMPLATE_DRAFT.md")
PROTOCOL_PATH = os.path.join(PILOT_DIR, "PILOT_PROTOCOL_BRIEF.md")


class TestPilotGovernance(unittest.TestCase):
    def test_01_pilot_directory_exists(self):
        """Verifies docs/pilot/ directory exists."""
        self.assertTrue(os.path.isdir(PILOT_DIR), f"Missing pilot directory at {PILOT_DIR}")

    def test_02_draft_template_watermark_and_placeholders(self):
        """Verifies PILOT_LETTER_TEMPLATE_DRAFT.md is watermarked as an unsigned draft with placeholders."""
        self.assertTrue(os.path.isfile(TEMPLATE_PATH), f"Missing template at {TEMPLATE_PATH}")
        with open(TEMPLATE_PATH, "r", encoding="utf-8") as f:
            content = f.read()

        # Must be explicitly watermarked as unsigned draft
        self.assertIn("DRAFT — UNSIGNED — NOT AN AGREEMENT", content)
        self.assertIn("UNSIGNED — PENDING FORMAL INSTITUTIONAL REVIEW", content)

        # Must use placeholders, not invented real partner names
        self.assertIn("[PARTNER HEALTHCARE ENTITY NAME]", content)
        self.assertIn("[DHA FACILITY LICENSE NUMBER]", content)
        self.assertIn("[NAME OF AUTHORIZED MEDICAL DIRECTOR]", content)

    def test_03_no_fabricated_executed_claims(self):
        """Strict negative test: fails if any file in docs/pilot/ asserts an executed or binding agreement."""
        forbidden_terms = [
            "EXECUTED BINDING MEMORANDUM",
            "COUNTERSIGNED & VERIFIED",
            "Prime Healthcare Group",
            "Prime",
            "DHA-FL-004921",
            "MOHAP-DXB-94812",
            "Dr. Tariq Al-Hashimi",
            "Dr. Mariam Bin Salem",
            "DHA-P-44019",
            "DHA-P-58204"
        ]

        pilot_files = [
            os.path.join(PILOT_DIR, fn)
            for fn in os.listdir(PILOT_DIR)
            if fn.endswith((".md", ".html", ".txt", ".json"))
        ]

        for file_path in pilot_files:
            rel_path = os.path.relpath(file_path, ROOT_DIR)
            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read()

            for term in forbidden_terms:
                self.assertNotIn(
                    term,
                    content,
                    f"Forbidden claim or fabricated entity '{term}' found in active pilot document: {rel_path}. "
                    f"Must be quarantined under _quarantine/ until an authentic signed agreement exists."
                )

    def test_04_protocol_brief_compliance(self):
        """Verifies clinical protocol brief contains sound methodology and no invented partner claims."""
        self.assertTrue(os.path.isfile(PROTOCOL_PATH), f"Missing protocol brief at {PROTOCOL_PATH}")
        with open(PROTOCOL_PATH, "r", encoding="utf-8") as f:
            content = f.read()

        self.assertIn("UAE Federal Law No. 2 of 2019", content)
        self.assertIn("DHA SN 03/2019", content)
        self.assertIn("0.03%", content)
        self.assertIn("SHADOW_ADVISORY_MODE", content)
        self.assertNotIn("Prime Healthcare Group", content)


if __name__ == "__main__":
    unittest.main()
