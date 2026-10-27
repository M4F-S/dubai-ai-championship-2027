# Master Makefile for Dubai Create AI Agents Championship 2026-2027 Adapters
# Systems: Qala (Business), Nibras Executive (Personal), Taryaq (Societal)

CC ?= cc
CFLAGS ?= -std=c99 -Wall -Wextra -Werror -O2 -Iadapters -Isrc
LDFLAGS ?= -lm -lsqlite3

BUILD_DIR = build
ADAPTERS_DIR = adapters
TESTS_DIR = tests
SRC_DIR = src

QALA_SRC = $(ADAPTERS_DIR)/qala_mcp_policy_adapter.c
NIBRAS_SRC = $(ADAPTERS_DIR)/nibras_arabic_fademem_adapter.c
TARYAQ_SRC = $(ADAPTERS_DIR)/taryaq_clinical_adapter.c
GROUNDING_SRC = $(ADAPTERS_DIR)/grounding_shield.c
CJSON_SRC = $(ADAPTERS_DIR)/cJSON.c
MCP_CURL_SRC = $(ADAPTERS_DIR)/mcp_curl_client.c
INTEROP_SRC = $(TESTS_DIR)/test_mcp_interop.c
MOCK_SERVER = $(TESTS_DIR)/mcp_mock_server.py
HUD_TEST = $(TESTS_DIR)/test_hud_telemetry.py
TARYAQ_AGENT_SRC = $(SRC_DIR)/taryaq_agent.c
QALA_AGENT_SRC = $(SRC_DIR)/qala_agent.c
QALA_CASE_SRC = $(SRC_DIR)/qala_case_memory.c
NIBRAS_AGENT_SRC = $(SRC_DIR)/nibras_agent.c
NIBRAS_STORE_SRC = $(ADAPTERS_DIR)/nibras_memory_store.c
TARYAQ_ACCEPTANCE_TEST = $(TESTS_DIR)/test_taryaq_acceptance.py
BENCH_RUNNER = bench/bench_runner.py
LAYA_TEST = $(TESTS_DIR)/test_laya_triage.py
PILOT_TEST = tests/test_pilot.py
TRACEABILITY_TEST = $(TESTS_DIR)/test_submission_traceability.py
BRIDGE_TEST = $(TESTS_DIR)/test_openrouter_bridge.py

UNAME_S := $(shell uname -s)
ifeq ($(UNAME_S),Darwin)
    LIB_EXT = dylib
else
    LIB_EXT = so
endif

QALA_BIN = $(BUILD_DIR)/test_qala_adapter
NIBRAS_BIN = $(BUILD_DIR)/test_nibras_adapter
TARYAQ_BIN = $(BUILD_DIR)/test_taryaq_adapter
GROUNDING_BIN = $(BUILD_DIR)/test_grounding_shield
MCP_CURL_BIN = $(BUILD_DIR)/test_mcp_curl_client
INTEROP_BIN = $(BUILD_DIR)/test_mcp_interop
TARYAQ_AGENT_BIN = $(BUILD_DIR)/taryaq_agent
QALA_AGENT_BIN = $(BUILD_DIR)/qala_agent
NIBRAS_AGENT_BIN = $(BUILD_DIR)/nibras_agent
NIBRAS_SUITE_BIN = $(BUILD_DIR)/test_nibras_suite
CASE_MEMORY_TEST_BIN = $(BUILD_DIR)/test_case_memory
LIB_ADAPTERS = $(BUILD_DIR)/libdubai_adapters.$(LIB_EXT)

.PHONY: all test test_qala test_nibras test_taryaq test_grounding test_mcp_curl test_interop test_hud test_bench test_laya test_golden eval_golden test_pilot test_traceability test_bridge test_gomaa taryaq_agent qala_agent nibras_agent timeline-demo clean

all: $(QALA_BIN) $(NIBRAS_BIN) $(TARYAQ_BIN) $(GROUNDING_BIN) $(MCP_CURL_BIN) $(INTEROP_BIN) $(TARYAQ_AGENT_BIN) $(QALA_AGENT_BIN) $(NIBRAS_AGENT_BIN) $(NIBRAS_SUITE_BIN) $(CASE_MEMORY_TEST_BIN) $(LIB_ADAPTERS)

$(BUILD_DIR):
	mkdir -p $(BUILD_DIR)

$(QALA_BIN): $(QALA_SRC) $(GROUNDING_SRC) $(ADAPTERS_DIR)/qala_adapters.h $(ADAPTERS_DIR)/grounding_shield.h | $(BUILD_DIR)
	$(CC) $(CFLAGS) -DQALA_STANDALONE_TEST $(QALA_SRC) $(GROUNDING_SRC) $(LDFLAGS) -o $@

$(NIBRAS_BIN): $(NIBRAS_SRC) $(ADAPTERS_DIR)/nibras_adapters.h | $(BUILD_DIR)
	$(CC) $(CFLAGS) -DNIBRAS_STANDALONE_TEST $< $(LDFLAGS) -o $@

$(TARYAQ_BIN): $(TARYAQ_SRC) $(ADAPTERS_DIR)/taryaq_adapters.h | $(BUILD_DIR)
	$(CC) $(CFLAGS) -DTARYAQ_STANDALONE_TEST $< $(LDFLAGS) -o $@

$(GROUNDING_BIN): $(GROUNDING_SRC) $(ADAPTERS_DIR)/grounding_shield.h | $(BUILD_DIR)
	$(CC) $(CFLAGS) -DGROUNDING_STANDALONE_TEST $< $(LDFLAGS) -o $@

$(MCP_CURL_BIN): $(MCP_CURL_SRC) $(CJSON_SRC) $(ADAPTERS_DIR)/mcp_curl_client.h $(ADAPTERS_DIR)/cJSON.h | $(BUILD_DIR)
	$(CC) $(CFLAGS) -DMCP_CURL_STANDALONE_TEST $(MCP_CURL_SRC) $(CJSON_SRC) $(LDFLAGS) -lcurl -o $@

$(INTEROP_BIN): $(INTEROP_SRC) $(MCP_CURL_SRC) $(CJSON_SRC) $(ADAPTERS_DIR)/mcp_curl_client.h $(ADAPTERS_DIR)/cJSON.h | $(BUILD_DIR)
	$(CC) $(CFLAGS) $(INTEROP_SRC) $(MCP_CURL_SRC) $(CJSON_SRC) $(LDFLAGS) -lcurl -o $@

$(TARYAQ_AGENT_BIN): $(TARYAQ_AGENT_SRC) $(TARYAQ_SRC) $(NIBRAS_SRC) $(GROUNDING_SRC) $(QALA_SRC) \
                     $(ADAPTERS_DIR)/taryaq_adapters.h $(ADAPTERS_DIR)/nibras_adapters.h \
                     $(ADAPTERS_DIR)/grounding_shield.h $(ADAPTERS_DIR)/qala_adapters.h | $(BUILD_DIR)
	$(CC) $(CFLAGS) $(TARYAQ_AGENT_SRC) $(TARYAQ_SRC) $(NIBRAS_SRC) $(GROUNDING_SRC) $(QALA_SRC) $(LDFLAGS) -lcurl -o $@

$(QALA_AGENT_BIN): $(QALA_AGENT_SRC) $(QALA_CASE_SRC) $(QALA_SRC) $(GROUNDING_SRC) $(MCP_CURL_SRC) $(CJSON_SRC) | $(BUILD_DIR)
	$(CC) $(CFLAGS) $^ $(LDFLAGS) -lcurl -o $@

$(CASE_MEMORY_TEST_BIN): $(TESTS_DIR)/test_case_memory.c $(QALA_CASE_SRC) $(CJSON_SRC) | $(BUILD_DIR)
	$(CC) $(CFLAGS) $^ $(LDFLAGS) -lcurl -o $@

$(NIBRAS_AGENT_BIN): $(NIBRAS_AGENT_SRC) $(NIBRAS_SRC) $(GROUNDING_SRC) $(NIBRAS_STORE_SRC) | $(BUILD_DIR)
	$(CC) $(CFLAGS) $^ $(LDFLAGS) -o $@

$(NIBRAS_SUITE_BIN): $(TESTS_DIR)/test_nibras_suite.c $(NIBRAS_SRC) $(GROUNDING_SRC) $(NIBRAS_STORE_SRC) | $(BUILD_DIR)
	$(CC) $(CFLAGS) $^ $(LDFLAGS) -o $@

$(LIB_ADAPTERS): $(QALA_SRC) $(GROUNDING_SRC) $(NIBRAS_SRC) $(TARYAQ_SRC) | $(BUILD_DIR)
	$(CC) $(CFLAGS) -fPIC -shared $^ $(LDFLAGS) -o $@

taryaq_agent: $(TARYAQ_AGENT_BIN)
qala_agent: $(QALA_AGENT_BIN)
nibras_agent: $(NIBRAS_AGENT_BIN)

timeline-demo: $(TARYAQ_AGENT_BIN)
	@./$(TARYAQ_AGENT_BIN) --timeline-demo

test: all test_interop test_hud test_bench test_laya test_golden test_pilot test_traceability test_bridge test_gomaa
	@echo "=================================================================="
	@echo " RUNNING ALL CHAMPIONSHIP C99 ADAPTER TESTS (-Wall -Wextra -Werror)"
	@echo "=================================================================="
	@./$(QALA_BIN)
	@./$(CASE_MEMORY_TEST_BIN)
	@./$(NIBRAS_BIN)
	@./$(NIBRAS_SUITE_BIN)
	@./$(TARYAQ_BIN)
	@./$(GROUNDING_BIN)
	@./$(MCP_CURL_BIN)
	@echo "=================================================================="
	@echo " RUNNING AGENT DAEMON ACCEPTANCE BATTERIES (Taryaq, Qala, Nibras)"
	@echo "=================================================================="
	@./$(TARYAQ_AGENT_BIN) --test
	@python3 $(TARYAQ_ACCEPTANCE_TEST)
	@python3 tests/test_audit_tamper.py
	@python3 tests/test_patient_timeline.py
	@./$(QALA_AGENT_BIN) --test
	@./$(NIBRAS_AGENT_BIN) --demo
	@echo "=================================================================="
	@echo " [SUCCESS] All Championship Adapters, Interop, HUD, Taryaq, Qala, Nibras, Bench, Laya, Golden, Traceability & Bridge Tests Passed!"
	@echo "=================================================================="

test_bridge: $(LIB_ADAPTERS)
	@echo "=================================================================="
	@echo " RUNNING SOVEREIGN OPENROUTER AGENT BRIDGE VERIFICATION SUITE"
	@echo "=================================================================="
	@python3 $(BRIDGE_TEST)

test_gomaa: $(LIB_ADAPTERS)
	@echo "=================================================================="
	@echo " RUNNING NIBRAS GOMAA 4-QUADRANT MEMORY OS TEST SUITE"
	@echo "=================================================================="
	@python3 tests/test_nibras_gomaa.py
	@echo "=================================================================="
	@echo " RUNNING TARYAQ GOMAA LONGITUDINAL PATIENT MEMORY SUITE"
	@echo "=================================================================="
	@python3 tests/test_taryaq_gomaa.py
	@echo "=================================================================="
	@echo " RUNNING QALA PROMPT INJECTION DEFENSE SUITE"
	@echo "=================================================================="
	@python3 tests/test_qala_injection_defense.py

test_traceability:
	@echo "=================================================================="
	@echo " RUNNING SUBMISSION NUMBER TRACEABILITY VERIFIER (M-10)"
	@echo "=================================================================="
	@python3 $(TRACEABILITY_TEST)

test_golden: $(LIB_ADAPTERS)
	@echo "=================================================================="
	@echo " RUNNING GOLDEN BENCHMARK SMOKE VERIFICATION (M-08)"
	@echo "=================================================================="
	@python3 benchmarks/golden_eval.py --smoke

eval_golden: all $(LIB_ADAPTERS)
	@echo "=================================================================="
	@echo " RUNNING FULL GOLDEN EVALUATION & SECTION 5.4 ABLATION (M-08)"
	@echo "=================================================================="
	@python3 benchmarks/golden_eval.py --full

test_pilot:
	@echo "=================================================================="
	@echo " RUNNING CLINICAL PILOT LOI & PROTOCOL VERIFICATION (M-09)"
	@echo "=================================================================="
	@python3 $(PILOT_TEST)

test_laya:
	@echo "=================================================================="
	@echo " RUNNING LAYA MULTILINGUAL 322M CALIBRATED TRIAGE BATTERY (M-07)"
	@echo "=================================================================="
	@python3 $(LAYA_TEST)

test_bench:
	@echo "=================================================================="
	@echo " RUNNING UM790 HARDWARE BENCHMARK & GBNF GRAMMAR VERIFIER (M-06)"
	@echo "=================================================================="
	@python3 $(BENCH_RUNNER) --verify

test_interop: $(INTEROP_BIN)
	@echo "=================================================================="
	@echo " STARTING MCP MOCK SERVER & RUNNING INTEROP TEST SUITE"
	@echo "=================================================================="
	@python3 $(MOCK_SERVER) > /dev/null 2>&1 & \
	SERVER_PID=$$!; \
	trap 'kill -9 $$SERVER_PID 2>/dev/null || true' EXIT INT TERM; \
	READY=0; \
	for i in 1 2 3 4 5 6 7 8 9 10 11 12 13 14 15 16 17 18 19 20; do \
		if curl -s http://127.0.0.1:8765/health > /dev/null 2>&1; then \
			READY=1; \
			break; \
		fi; \
		sleep 0.1; \
	done; \
	if [ $$READY -ne 1 ]; then \
		echo "[-] Fatal: MCP mock server failed to bind to 127.0.0.1:8765 within 2 seconds" >&2; \
		kill -9 $$SERVER_PID 2>/dev/null || true; \
		exit 1; \
	fi; \
	./$(INTEROP_BIN); \
	TEST_STATUS=$$?; \
	curl -s -X POST http://127.0.0.1:8765/shutdown > /dev/null 2>&1 || true; \
	wait $$SERVER_PID 2>/dev/null || true; \
	exit $$TEST_STATUS

test_hud:
	@echo "=================================================================="
	@echo " RUNNING HUD TELEMETRY BRIDGE VERIFICATION SUITE"
	@echo "=================================================================="
	@python3 $(HUD_TEST)

test_qala: $(QALA_BIN)
	@./$(QALA_BIN)

test_nibras: $(NIBRAS_BIN)
	@./$(NIBRAS_BIN)

test_taryaq: $(TARYAQ_BIN) $(TARYAQ_AGENT_BIN)
	@./$(TARYAQ_BIN)
	@./$(TARYAQ_AGENT_BIN) --test
	@python3 $(TARYAQ_ACCEPTANCE_TEST)

test_grounding: $(GROUNDING_BIN)
	@./$(GROUNDING_BIN)

test_mcp_curl: $(MCP_CURL_BIN)
	@./$(MCP_CURL_BIN)

clean:
	rm -rf $(BUILD_DIR)
	rm -f taryaq_audit.jsonl qala-audit.jsonl taryaq_encounters.jsonl build/qala_test_audit.jsonl build/qala_case_memory.db
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true
