# Master Makefile for Dubai Create AI Agents Championship 2026-2027 Adapters
# Systems: Qala (Business), Nibras Executive (Personal), Taryaq (Societal)

CC ?= cc
CFLAGS ?= -std=c99 -Wall -Wextra -Werror -O2 -Iadapters
LDFLAGS ?= -lm

BUILD_DIR = build
ADAPTERS_DIR = adapters

QALA_SRC = $(ADAPTERS_DIR)/qala_mcp_policy_adapter.c
NIBRAS_SRC = $(ADAPTERS_DIR)/nibras_arabic_fademem_adapter.c
TARYAQ_SRC = $(ADAPTERS_DIR)/taryaq_clinical_adapter.c

QALA_BIN = $(BUILD_DIR)/test_qala_adapter
NIBRAS_BIN = $(BUILD_DIR)/test_nibras_adapter
TARYAQ_BIN = $(BUILD_DIR)/test_taryaq_adapter

.PHONY: all test test_qala test_nibras test_taryaq clean

all: $(QALA_BIN) $(NIBRAS_BIN) $(TARYAQ_BIN)

$(BUILD_DIR):
	mkdir -p $(BUILD_DIR)

$(QALA_BIN): $(QALA_SRC) $(ADAPTERS_DIR)/qala_adapters.h | $(BUILD_DIR)
	$(CC) $(CFLAGS) -DQALA_STANDALONE_TEST $< $(LDFLAGS) -o $@

$(NIBRAS_BIN): $(NIBRAS_SRC) $(ADAPTERS_DIR)/nibras_adapters.h | $(BUILD_DIR)
	$(CC) $(CFLAGS) -DNIBRAS_STANDALONE_TEST $< $(LDFLAGS) -o $@

$(TARYAQ_BIN): $(TARYAQ_SRC) $(ADAPTERS_DIR)/taryaq_adapters.h | $(BUILD_DIR)
	$(CC) $(CFLAGS) -DTARYAQ_STANDALONE_TEST $< $(LDFLAGS) -o $@

test: all
	@echo "=================================================================="
	@echo " RUNNING ALL CHAMPIONSHIP C99 ADAPTER TESTS (-Wall -Wextra -Werror)"
	@echo "=================================================================="
	@./$(QALA_BIN)
	@./$(NIBRAS_BIN)
	@./$(TARYAQ_BIN)
	@echo "=================================================================="
	@echo " [SUCCESS] All 3 C99 Championship Adapters Passed 100% Deterministically!"
	@echo "=================================================================="

test_qala: $(QALA_BIN)
	@./$(QALA_BIN)

test_nibras: $(NIBRAS_BIN)
	@./$(NIBRAS_BIN)

test_taryaq: $(TARYAQ_BIN)
	@./$(TARYAQ_BIN)

clean:
	rm -rf $(BUILD_DIR)
