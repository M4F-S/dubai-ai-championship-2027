# Master Makefile for Dubai Create AI Agents Championship 2026-2027 Adapters
# Systems: Qala (Business), Nibras Executive (Personal), Taryaq (Societal)

CC ?= cc
CFLAGS ?= -std=c99 -Wall -Wextra -Werror -O2 -Iadapters
LDFLAGS ?= -lm

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
TARYAQ_ACCEPTANCE_TEST = $(TESTS_DIR)/test_taryaq_acceptance.py
BENCH_RUNNER = bench/bench_runner.py

QALA_BIN = $(BUILD_DIR)/test_qala_adapter
NIBRAS_BIN = $(BUILD_DIR)/test_nibras_adapter
TARYAQ_BIN = $(BUILD_DIR)/test_taryaq_adapter
GROUNDING_BIN = $(BUILD_DIR)/test_grounding_shield
MCP_CURL_BIN = $(BUILD_DIR)/test_mcp_curl_client
INTEROP_BIN = $(BUILD_DIR)/test_mcp_interop
TARYAQ_AGENT_BIN = $(BUILD_DIR)/taryaq_agent

.PHONY: all test test_qala test_nibras test_taryaq test_grounding test_mcp_curl test_interop test_hud test_bench taryaq_agent clean

all: $(QALA_BIN) $(NIBRAS_BIN) $(TARYAQ_BIN) $(GROUNDING_BIN) $(MCP_CURL_BIN) $(INTEROP_BIN) $(TARYAQ_AGENT_BIN)

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

taryaq_agent: $(TARYAQ_AGENT_BIN)

test: all test_interop test_hud test_bench
	@echo "=================================================================="
	@echo " RUNNING ALL CHAMPIONSHIP C99 ADAPTER TESTS (-Wall -Wextra -Werror)"
	@echo "=================================================================="
	@./$(QALA_BIN)
	@./$(NIBRAS_BIN)
	@./$(TARYAQ_BIN)
	@./$(GROUNDING_BIN)
	@./$(MCP_CURL_BIN)
	@echo "=================================================================="
	@echo " RUNNING TARYAQ RUNNABLE AGENT ACCEPTANCE BATTERY (M-05)"
	@echo "=================================================================="
	@./$(TARYAQ_AGENT_BIN) --test
	@python3 $(TARYAQ_ACCEPTANCE_TEST)
	@echo "=================================================================="
	@echo " [SUCCESS] All Championship Adapters, Interop, HUD, Taryaq & Bench Tests Passed!"
	@echo "=================================================================="

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
