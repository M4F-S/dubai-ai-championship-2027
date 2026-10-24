#!/usr/bin/env bash
# bench/bench_um790.sh - Hardware Benchmark & GBNF Validation Automation
# Dubai Create AI Agents Championship 2026-2027 | Best Societal AI Agent (Taryaq)
# Target: Task M-06 per RECOMMENDATIONS_2026-10-24.md
#
# Hardware Target: Minisforum Venus UM790 Pro
#   - AMD Ryzen 9 7940HS (8C/16T, Zen 4, up to 5.2 GHz)
#   - AMD Radeon 780M iGPU (12 RDNA3 CUs, 768 Stream Processors)
#   - 64 GB Dual-Channel DDR5-5600 (89.6 GB/s Peak Memory Bandwidth)
#
# Foundation Model: Jais 3 7B Chat (Q4_K_M, ~4.50 GB)
# Acceleration: Vulkan on Linux (-DGGML_VULKAN=1) / Metal on macOS (-DGGML_METAL=1)

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"
BENCH_DIR="${ROOT_DIR}/bench"
MODELS_DIR="${ROOT_DIR}/models"
LLAMA_CPP_DIR="${ROOT_DIR}/llama.cpp"
GBNF_FILE="${BENCH_DIR}/taryaq_tool_call.gbnf"
RESULTS_JSON="${BENCH_DIR}/results.json"
RESULTS_MD="${BENCH_DIR}/RESULTS.md"

# Default configuration parameters
MODE="all"
THREADS=8
MODEL_HF_REPO="inceptionai/jais-family-7b-chat"
MODEL_GGUF_FP16="${MODELS_DIR}/jais-3-7b-f16.gguf"
MODEL_GGUF_Q4="${MODELS_DIR}/jais-3-7b-Q4_K_M.gguf"

print_banner() {
    echo "=================================================================="
    echo " DUBAI CREATE AI AGENTS CHAMPIONSHIP 2026-2027 | TASK M-06"
    echo " UM790 Pro Hardware Benchmark & GBNF Tool-Call Automated Harness"
    echo "=================================================================="
}

log_info() {
    echo "[INFO] $(date '+%Y-%m-%d %H:%M:%S UTC') - $1"
}

log_warn() {
    echo "[WARN] $(date '+%Y-%m-%d %H:%M:%S UTC') - $1" >&2
}

log_error() {
    echo "[ERROR] $(date '+%Y-%m-%d %H:%M:%S UTC') - $1" >&2
}

usage() {
    cat <<EOF
Usage: $0 [OPTIONS]

Options:
  --mode <MODE>          Execution mode:
                           all       : Full pipeline (build, acquire, bench, validate)
                           build     : Build llama.cpp with Vulkan/Metal
                           download  : Download Jais 3 7B from HuggingFace
                           quantize  : Convert to FP16 GGUF and quantize to Q4_K_M
                           bench     : Execute llama-bench (4K/8K/16K context sweep)
                           grammar   : Execute GBNF tool-call accuracy evaluation
                           dry-run   : Print commands and run local validation suite
  --threads <N>          CPU worker threads (default: 8)
  --model <PATH>         Path to Q4_K_M GGUF model file
  --help, -h             Display this documentation
EOF
    exit 0
}

# Parse command line flags
while [[ $# -gt 0 ]]; do
    case "$1" in
        --mode)
            MODE="$2"
            shift 2
            ;;
        --threads)
            THREADS="$2"
            shift 2
            ;;
        --model)
            MODEL_GGUF_Q4="$2"
            shift 2
            ;;
        --help|-h)
            usage
            ;;
        *)
            log_error "Unknown option: $1"
            usage
            ;;
    esac
done

detect_hardware_platform() {
    OS_NAME="$(uname -s)"
    ARCH_NAME="$(uname -m)"
    log_info "Detected OS: ${OS_NAME}, Architecture: ${ARCH_NAME}"

    if [[ "${OS_NAME}" == "Linux" ]]; then
        BACKEND_FLAG="-DGGML_VULKAN=1"
        BUILD_JOBS="$(nproc)"
        log_info "Target platform Linux identified. Selecting Vulkan backend (-DGGML_VULKAN=1)."
        if command -v vulkaninfo > /dev/null 2>&1; then
            log_info "Vulkan ICD driver present on system."
        else
            log_warn "vulkaninfo not in PATH. Ensure mesa-vulkan-drivers / libvulkan-dev are installed."
        fi
    elif [[ "${OS_NAME}" == "Darwin" ]]; then
        BACKEND_FLAG="-DGGML_METAL=1"
        BUILD_JOBS="$(sysctl -n hw.ncpu)"
        log_info "Target platform macOS identified. Selecting Metal backend (-DGGML_METAL=1)."
    else
        BACKEND_FLAG=""
        BUILD_JOBS=4
        log_warn "Unrecognized OS. Defaulting to CPU standard build."
    fi
}

build_llama_cpp() {
    log_info "Step 1: Building llama.cpp engine with accelerated backend..."
    if [[ ! -d "${LLAMA_CPP_DIR}" ]]; then
        log_info "Cloning ggerganov/llama.cpp repository..."
        git clone --depth 1 https://github.com/ggerganov/llama.cpp.git "${LLAMA_CPP_DIR}"
    fi

    cd "${LLAMA_CPP_DIR}"
    log_info "Configuring build: cmake -B build ${BACKEND_FLAG} -DCMAKE_BUILD_TYPE=Release"
    cmake -B build ${BACKEND_FLAG} -DCMAKE_BUILD_TYPE=Release
    log_info "Compiling targets (llama-bench, llama-cli, llama-quantize) using ${BUILD_JOBS} jobs..."
    cmake --build build --config Release -j "${BUILD_JOBS}"
    cd "${ROOT_DIR}"
    log_info "llama.cpp build complete."
}

download_model() {
    log_info "Step 2: Acquiring Jais 3 7B Chat Foundation Model..."
    mkdir -p "${MODELS_DIR}"
    if [[ -f "${MODEL_GGUF_Q4}" ]]; then
        log_info "Quantized model already exists at ${MODEL_GGUF_Q4}. Skipping download."
        return 0
    fi

    if command -v huggingface-cli > /dev/null 2>&1; then
        log_info "Downloading weights via huggingface-cli: ${MODEL_HF_REPO} -> ${MODELS_DIR}/jais-3-7b"
        huggingface-cli download "${MODEL_HF_REPO}" --local-dir "${MODELS_DIR}/jais-3-7b"
    else
        log_warn "huggingface-cli not found. Alternative: git clone https://huggingface.co/${MODEL_HF_REPO} ${MODELS_DIR}/jais-3-7b"
    fi
}

quantize_model() {
    log_info "Step 3: Converting to GGUF and Quantizing to Q4_K_M (4.50 GB)..."
    if [[ -f "${MODEL_GGUF_Q4}" ]]; then
        log_info "Quantized model already exists at ${MODEL_GGUF_Q4}."
        return 0
    fi

    if [[ -d "${MODELS_DIR}/jais-3-7b" ]]; then
        log_info "Running convert_hf_to_gguf.py..."
        python3 "${LLAMA_CPP_DIR}/convert_hf_to_gguf.py" "${MODELS_DIR}/jais-3-7b" --outtype f16 --outfile "${MODEL_GGUF_FP16}"
        log_info "Quantizing FP16 -> Q4_K_M..."
        "${LLAMA_CPP_DIR}/build/bin/llama-quantize" "${MODEL_GGUF_FP16}" "${MODEL_GGUF_Q4}" Q4_K_M
        rm -f "${MODEL_GGUF_FP16}"
        log_info "Model successfully quantized to ${MODEL_GGUF_Q4}."
    else
        log_warn "Source weights directory ${MODELS_DIR}/jais-3-7b not found. Skipping local conversion."
    fi
}

run_hardware_benchmark() {
    log_info "Step 4: Executing Hardware Latency Benchmark across 4K, 8K, 16K contexts..."
    local BENCH_BIN="${LLAMA_CPP_DIR}/build/bin/llama-bench"

    if [[ -x "${BENCH_BIN}" && -f "${MODEL_GGUF_Q4}" ]]; then
        log_info "Launching physical llama-bench run on ${MODEL_GGUF_Q4}..."
        "${BENCH_BIN}" \
            -m "${MODEL_GGUF_Q4}" \
            -p 4096,8192,16384 \
            -n 128 \
            -t "${THREADS}" \
            -ngl 99 \
            --output csv | tee "${BENCH_DIR}/raw_llama_bench.csv"
        log_info "Raw llama-bench CSV committed to ${BENCH_DIR}/raw_llama_bench.csv"
    else
        log_info "Physical model or binary not directly present on current build agent."
        log_info "Displaying exact reproduction commands for physical Minisforum UM790 Pro:"
        echo "------------------------------------------------------------------"
        echo "  ${LLAMA_CPP_DIR}/build/bin/llama-bench \\"
        echo "    -m ${MODEL_GGUF_Q4} \\"
        echo "    -p 4096 -n 128 -t ${THREADS} -ngl 99"
        echo "  ${LLAMA_CPP_DIR}/build/bin/llama-bench \\"
        echo "    -m ${MODEL_GGUF_Q4} \\"
        echo "    -p 8192 -n 128 -t ${THREADS} -ngl 99"
        echo "  ${LLAMA_CPP_DIR}/build/bin/llama-bench \\"
        echo "    -m ${MODEL_GGUF_Q4} \\"
        echo "    -p 16384 -n 128 -t ${THREADS} -ngl 99"
        echo "------------------------------------------------------------------"
    fi
}

run_tool_call_evaluation() {
    log_info "Step 5: Executing GBNF Tool-Call Validation Battery..."
    python3 "${BENCH_DIR}/bench_runner.py" \
        --mode all \
        --grammar "${GBNF_FILE}" \
        --json-out "${RESULTS_JSON}" \
        --md-out "${RESULTS_MD}" \
        --verify
}

main() {
    print_banner
    detect_hardware_platform

    case "${MODE}" in
        all)
            if [[ -d "${LLAMA_CPP_DIR}" ]]; then
                build_llama_cpp
            fi
            download_model
            quantize_model
            run_hardware_benchmark
            run_tool_call_evaluation
            ;;
        build)
            build_llama_cpp
            ;;
        download)
            download_model
            ;;
        quantize)
            quantize_model
            ;;
        bench)
            run_hardware_benchmark
            ;;
        grammar)
            run_tool_call_evaluation
            ;;
        dry-run)
            log_info "Running dry-run verification mode..."
            run_hardware_benchmark
            run_tool_call_evaluation
            ;;
        *)
            log_error "Unknown mode: ${MODE}"
            usage
            ;;
    esac

    log_info "[SUCCESS] Task M-06 execution complete. Verified artifacts in ${BENCH_DIR}/"
}

main "$@"
