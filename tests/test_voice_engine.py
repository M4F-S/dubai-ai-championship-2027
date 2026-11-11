#!/usr/bin/env python3
"""
tests/test_voice_engine.py - Bi-Directional Voice Engine Verification Suite (Dubai 2027)
Pillar 3: STT (whisper.cpp) + TTS (piper-tts) + Dialect Normalizer + Cockpit Loop
Milestone: SPRINT-14 (M-14)

Covers:
- Test 1: PCM audio format validation and whisper transcription parsing.
- Test 2: Gulf/Masri colloquial transcript normalization (e.g. 'عظامي بتوجعني وباخد كولشيسين').
- Test 3: TTS audio generation producing valid RIFF/WAV headers and non-zero audio bytes.
- Test 4: End-to-end HTTP endpoints /api/voice/transcribe and /api/voice/synthesize.
- Test 5: Full Voice Loop: Audio In -> STT -> C99 Safety Intercept -> Multi-Turn Synthesis -> TTS Audio Out.
"""

import os
import sys
import time
import json
import unittest
import threading
import urllib.request
import urllib.error

# Ensure project root is in python path
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(CURRENT_DIR)
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from bridge.sanitizer import (
    normalize_vernacular_voice_transcript,
    extract_vernacular_entities,
    strip_unauthorized_scripts,
    has_unauthorized_script
)
from bridge.voice_stt import (
    validate_wav_pcm,
    ensure_16k_mono_pcm,
    generate_synthetic_pcm_wav,
    parse_whisper_stdout,
    transcribe_audio,
    set_active_mock_transcript,
    register_mock_transcript,
    clear_mock_transcripts
)
from bridge.voice_tts import (
    synthesize_speech,
    validate_tts_wav,
    get_cached_audio,
    get_cache_key,
    VOICE_CACHE_DIR
)
from bridge.server import (
    ThreadingHTTPServer,
    ChampionshipRequestHandler,
    DEFAULT_HOST
)
from bridge.openrouter_client import (
    OpenRouterAgentEngine,
    _consumed_override_tokens
)


class TestBiDirectionalVoiceEngine(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Configure test audit key
        cls._orig_audit_key = os.environ.get("TARYAQ_AUDIT_KEY")
        os.environ["TARYAQ_AUDIT_KEY"] = "test-key-32-bytes-minimum-voice-sprint14"

        # Start ephemeral test HTTP server on port 8844
        cls.port = 8844
        cls.server = ThreadingHTTPServer((DEFAULT_HOST, cls.port), ChampionshipRequestHandler)
        cls.server_thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.server_thread.start()
        time.sleep(0.25)

    @classmethod
    def tearDownClass(cls):
        if hasattr(cls, "server"):
            cls.server.shutdown()
            cls.server.server_close()
        if getattr(cls, "_orig_audit_key", None) is None:
            os.environ.pop("TARYAQ_AUDIT_KEY", None)
        else:
            os.environ["TARYAQ_AUDIT_KEY"] = cls._orig_audit_key
        clear_mock_transcripts()

    def setUp(self):
        clear_mock_transcripts()
        _consumed_override_tokens.clear()

    # -------------------------------------------------------------------------
    # TEST 1: PCM Audio Format Validation & Whisper Transcription Parsing
    # -------------------------------------------------------------------------
    def test_01_pcm_audio_format_validation_and_parsing(self):
        """Verify strict 16kHz 16-bit mono WAV PCM audio validation and whisper.cpp parsing."""
        # 1. Valid 16kHz 16-bit mono WAV PCM
        valid_wav = generate_synthetic_pcm_wav("test_prompt", duration_sec=1.2, sample_rate=16000)
        meta = validate_wav_pcm(valid_wav)
        self.assertTrue(meta["valid"])
        self.assertEqual(meta["channels"], 1)
        self.assertEqual(meta["sample_rate"], 16000)
        self.assertEqual(meta["bits_per_sample"], 16)
        self.assertGreater(meta["frames"], 0)
        self.assertAlmostEqual(meta["duration_sec"], 1.2, delta=0.05)

        # 2. Corrupt audio must fail closed
        with self.assertRaises(ValueError):
            validate_wav_pcm(b"NOT_A_WAV_HEADER_CORRUPT_BYTES")

        with self.assertRaises(ValueError):
            validate_wav_pcm(b"")

        # 3. Resampling helper (ensure_16k_mono_pcm)
        resampled = ensure_16k_mono_pcm(valid_wav)
        self.assertEqual(len(resampled), len(valid_wav))

        # 4. Raw PCM bytes wrapped into standard WAV
        raw_pcm = b"\x00\x00" * 8000
        wrapped_wav = ensure_16k_mono_pcm(raw_pcm)
        wrapped_meta = validate_wav_pcm(wrapped_wav)
        self.assertTrue(wrapped_meta["valid"])
        self.assertEqual(wrapped_meta["sample_rate"], 16000)

        # 5. Whisper output parser: strips timestamps and timings
        sample_whisper_stdout = (
            "[00:00:00.000 --> 00:00:02.400]   عظامي بتوجعني وباخد كولشيسين\n"
            "[00:00:02.400 --> 00:00:04.100]   وفحص الكلى 22\n"
            "whisper_print_timings:     load time =    45.12 ms\n"
            "whisper_print_timings:    total time =   142.80 ms\n"
        )
        parsed = parse_whisper_stdout(sample_whisper_stdout)
        self.assertEqual(parsed, "عظامي بتوجعني وباخد كولشيسين وفحص الكلى 22")
        self.assertNotIn("whisper_print_timings", parsed)
        self.assertNotIn("[00:00:", parsed)

    # -------------------------------------------------------------------------
    # TEST 2: Gulf / Masri Colloquial Transcript Normalization
    # -------------------------------------------------------------------------
    def test_02_gulf_masri_colloquial_transcript_normalization(self):
        """Verify Gulf and Masri vernacular mapping to canonical clinical and statutory entities."""
        # Case A: Taryaq Clinical Gout & Colchicine
        raw_1 = "عظامي بتوجعني وباخد كولشيسين"
        norm_1 = normalize_vernacular_voice_transcript(raw_1)
        self.assertIn("كولشيسين (Colchicine)", norm_1)
        self.assertIn("ألم المفاصل والعظام", norm_1)
        self.assertIn("نقرس M10.9", norm_1)
        entities_1 = extract_vernacular_entities(raw_1)
        self.assertGreaterEqual(len(entities_1), 2)

        # Case B: Taryaq Acute Gout Flare + Dual Therapy
        raw_2 = "عظامي بتوجعني وعندي نقرس حاد وباخد حبة كولشيسين مع كلاريثرو"
        norm_2 = normalize_vernacular_voice_transcript(raw_2)
        self.assertIn("كولشيسين (Colchicine)", norm_2)
        self.assertIn("كلاريثروميسين (Clarithromycin)", norm_2)
        self.assertIn("نقرس حاد ICD-10 M10.9", norm_2)
        self.assertIn("جرعة", norm_2)

        # Case C: Renal Impairment Vernacular (eGFR 22)
        raw_3 = "كليتي تعبانة والفحص 22"
        norm_3 = normalize_vernacular_voice_transcript(raw_3)
        self.assertIn("قصور كلوي حاد", norm_3)
        self.assertIn("Renal Impairment eGFR 22 mL/min", norm_3)

        # Case D: Qala Customs & Mirsal II Tariff Vernacular
        raw_4 = "عايز ادخل شحنة موبايلات من المينا"
        norm_4 = normalize_vernacular_voice_transcript(raw_4)
        self.assertIn("HS 8517.13.00", norm_4)
        self.assertIn("هواتف ذكية", norm_4)
        self.assertIn("الميناء الجمركي (Mirsal II)", norm_4)

        # Case E: Nibras Civic & Ejari Decree 43/2013 Rent Dispute
        raw_5 = "صاحب الشقة رفع عليا الايجار 20%"
        norm_5 = normalize_vernacular_voice_transcript(raw_5)
        self.assertIn("المؤجر", norm_5)
        self.assertIn("مرسوم إيجاري 43/2013", norm_5)
        self.assertIn("20%", norm_5)

        # Case F: Script Leak Defense in Voice Transcripts
        raw_leak = "باخد حبة コルヒチン مع كلاريثرو"
        norm_leak = normalize_vernacular_voice_transcript(raw_leak)
        self.assertFalse(has_unauthorized_script(norm_leak))
        self.assertIn("كلاريثروميسين (Clarithromycin)", norm_leak)

    # -------------------------------------------------------------------------
    # TEST 3: TTS Audio Generation Producing Valid RIFF/WAV Headers
    # -------------------------------------------------------------------------
    def test_03_tts_audio_generation_and_caching(self):
        """Verify TTS engine generates valid 22.05 kHz WAV audio with non-zero bytes and SHA-256 caching."""
        test_phrase_ar = "تحذير سريري حاد: تداخل دوائي مميت بين كولشيسين وكلاريثروميسين"

        # 1. Synthesize Arabic Audio
        t0 = time.perf_counter()
        wav_bytes_ar = synthesize_speech(test_phrase_ar, language="ar")
        synth_latency_ms = (time.perf_counter() - t0) * 1000.0

        self.assertIsInstance(wav_bytes_ar, bytes)
        self.assertGreater(len(wav_bytes_ar), 1000)

        # 2. Validate RIFF/WAV parameters (22050 Hz, 16-bit Mono)
        meta_ar = validate_tts_wav(wav_bytes_ar)
        self.assertTrue(meta_ar["valid"])
        self.assertEqual(meta_ar["sample_rate"], 22050)
        self.assertEqual(meta_ar["channels"], 1)
        self.assertEqual(meta_ar["bits_per_sample"], 16)
        self.assertGreater(meta_ar["frames"], 5000)
        self.assertGreater(meta_ar["duration_sec"], 0.2)

        # 3. SHA-256 Voice Cache Verification (<10 ms instant retrieval)
        cache_key = get_cache_key(test_phrase_ar, "ar")
        cached_file = os.path.join(VOICE_CACHE_DIR, f"{cache_key}.wav")
        self.assertTrue(os.path.exists(cached_file))

        t_cache_0 = time.perf_counter()
        cached_audio = synthesize_speech(test_phrase_ar, language="ar")
        cache_latency_ms = (time.perf_counter() - t_cache_0) * 1000.0

        self.assertEqual(wav_bytes_ar, cached_audio)
        self.assertLess(cache_latency_ms, 10.0, f"Cache retrieval took {cache_latency_ms} ms (exceeded 10 ms)")

        # 4. Synthesize English Audio
        test_phrase_en = "CRITICAL WARNING: Fatal CYP3A4 interaction detected."
        wav_bytes_en = synthesize_speech(test_phrase_en, language="en")
        meta_en = validate_tts_wav(wav_bytes_en)
        self.assertTrue(meta_en["valid"])
        self.assertEqual(meta_en["sample_rate"], 22050)
        self.assertEqual(meta_en["channels"], 1)

    # -------------------------------------------------------------------------
    # TEST 4: End-to-End HTTP Endpoints (/api/voice/transcribe & /api/voice/synthesize)
    # -------------------------------------------------------------------------
    def test_04_http_voice_endpoints_lifecycle(self):
        """Verify HTTP endpoints POST /api/voice/transcribe and POST /api/voice/synthesize."""
        base_url = f"http://{DEFAULT_HOST}:{self.port}"

        # 1. POST /api/voice/transcribe with synthetic WAV
        utterance = "عظامي بتوجعني وباخد كولشيسين"
        test_audio = generate_synthetic_pcm_wav(cue=utterance, duration_sec=1.0)

        transcribe_url = f"{base_url}/api/voice/transcribe"
        req_stt = urllib.request.Request(
            transcribe_url,
            data=test_audio,
            headers={"Content-Type": "audio/wav"},
            method="POST"
        )
        with urllib.request.urlopen(req_stt) as resp:
            self.assertEqual(resp.status, 200)
            self.assertIn("application/json", resp.headers.get("Content-Type", ""))
            data = json.loads(resp.read().decode("utf-8"))

        self.assertEqual(data["status"], "SUCCESS")
        self.assertIn("transcript", data)
        self.assertIn("normalized", data)
        self.assertEqual(data["language"], "ar")
        self.assertIn("كولشيسين (Colchicine)", data["normalized"])

        # 2. POST /api/voice/synthesize with JSON
        synthesize_url = f"{base_url}/api/voice/synthesize"
        synth_payload = json.dumps({
            "text": "تحذير سريري: تداخل كولشيسين وكلاريثروميسين",
            "lang": "ar"
        }).encode("utf-8")

        req_tts = urllib.request.Request(
            synthesize_url,
            data=synth_payload,
            headers={"Content-Type": "application/json"},
            method="POST"
        )
        with urllib.request.urlopen(req_tts) as resp:
            self.assertEqual(resp.status, 200)
            self.assertEqual(resp.headers.get("Content-Type"), "audio/wav")
            audio_out = resp.read()

        meta_out = validate_tts_wav(audio_out)
        self.assertTrue(meta_out["valid"])
        self.assertEqual(meta_out["sample_rate"], 22050)
        self.assertGreater(meta_out["payload_bytes"], 1000)

        # 3. Verify Error Handling: Empty payload
        bad_req = urllib.request.Request(
            transcribe_url,
            data=b"",
            headers={"Content-Type": "audio/wav"},
            method="POST"
        )
        with self.assertRaises(urllib.error.HTTPError) as ctx:
            urllib.request.urlopen(bad_req)
        self.assertEqual(ctx.exception.code, 400)

    # -------------------------------------------------------------------------
    # TEST 5: Full Voice Loop: Audio In -> STT -> C99 Safety Intercept -> Multi-Turn Synthesis -> TTS Audio Out
    # -------------------------------------------------------------------------
    def test_05_full_bi_directional_voice_safety_loop(self):
        """Verify Full Bi-Directional Voice Loop:

        Audio In -> STT -> C99 Safety Intercept -> Turn 2 Synthesis -> TTS Audio Out
        """
        # Step A: Audio In with colloquial patient query
        voice_input_phrase = "عظامي بتوجعني وعندي نقرس حاد وباخد حبة كولشيسين مع كلاريثرو وكليتي تعبانة والفحص 22"
        audio_in = generate_synthetic_pcm_wav(cue=voice_input_phrase, duration_sec=1.5)

        # Step B: Voice STT Engine transcription & dialect normalization
        stt_result = transcribe_audio(audio_in)
        raw_transcript = stt_result["transcript"]
        normalized_prompt = stt_result["normalized"]

        self.assertIn("كولشيسين (Colchicine)", normalized_prompt)
        self.assertIn("كلاريثروميسين (Clarithromycin)", normalized_prompt)
        self.assertIn("eGFR 22", normalized_prompt)
        self.assertEqual(stt_result["language"], "ar")

        # Step C: Conversational Bridge with Native C99 Safety Intercept
        engine = OpenRouterAgentEngine(provider="deterministic")
        engine.set_agent("taryaq")

        stream_events = list(engine.process_chat(user_message=normalized_prompt))

        # Verify C99 safety intercept was triggered deterministically
        c99_event = next(
            (e for e in stream_events if e.get("type") == "c99_execution" and "is_blocked" in e.get("result", {})),
            None
        )
        self.assertIsNotNone(c99_event, "C99 execution event missing from stream")
        self.assertTrue(c99_event["result"]["is_blocked"], "Fatal drug interaction was not blocked by C99 kernel")
        self.assertEqual(c99_event["result"]["alert_code"], "FATAL_CYP3A4_RENAL_CONTRAINDICATION")
        self.assertLess(c99_event["result"]["execution_time_ms"], 1.0, "C99 execution exceeded sub-millisecond threshold")

        # Step D: Turn 2 Conversational Synthesis Token Stream
        token_events = [e for e in stream_events if e.get("type") == "token"]
        self.assertGreater(len(token_events), 0, "Turn 2 synthesis tokens were not emitted")
        full_synthesis_text = "".join(t["content"] for t in token_events)

        self.assertIn("CONTRAINDICATION", full_synthesis_text)
        self.assertIn("Colchicine", full_synthesis_text)
        self.assertIn("CYP3A4", full_synthesis_text)

        # Step E: Voice TTS Engine Synthesizes Turn 2 Output Audio
        audio_out = synthesize_speech(full_synthesis_text[:280], language="ar")
        out_meta = validate_tts_wav(audio_out)

        self.assertTrue(out_meta["valid"])
        self.assertEqual(out_meta["sample_rate"], 22050)
        self.assertEqual(out_meta["channels"], 1)
        self.assertGreater(out_meta["payload_bytes"], 5000)
        self.assertGreater(out_meta["duration_sec"], 0.3)


if __name__ == "__main__":
    unittest.main()
