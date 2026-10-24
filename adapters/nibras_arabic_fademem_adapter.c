/* nibras_arabic_fademem_adapter.c
 * Hardened C99 Implementation of:
 *   1. Zero-Allocation UTF-8 Arabic & Gulf Dialect Normalizer for SQLite FTS5 BM25
 *   2. Procedural Friction Appraisal & Time-Gated FadeMem Engine (--sim-time-scale)
 */

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <stdint.h>
#include <stdbool.h>
#include <math.h>

#include "nibras_adapters.h"

/* Zero-allocation UTF-8 Arabic & Gulf Dialect Normalizer */
size_t arabic_normalize_utf8_hardened(const char *src, char *dst, size_t dst_cap) {
    if (!src || !dst || dst_cap == 0) return 0;

    const unsigned char *s = (const unsigned char *)src;
    unsigned char *d = (unsigned char *)dst;
    size_t out_idx = 0;

    while (*s != '\0' && (out_idx + 4) < dst_cap) {
        /* Check for Zero-Width Non-Joiner (U+200C: E2 80 8C) or Joiner (U+200D: E2 80 8D) */
        if (s[0] == 0xE2 && s[1] == 0x80 && (s[2] == 0x8C || s[2] == 0x8D)) {
            s += 3;
            continue;
        }

        /* Check for 2-byte UTF-8 Arabic & Extended Arabic blocks (0xD8, 0xD9, 0xDB) */
        if ((s[0] == 0xD8 || s[0] == 0xD9 || s[0] == 0xDB) && s[1] != '\0') {
            unsigned char b0 = s[0];
            unsigned char b1 = s[1];

            if (b0 == 0xD8) {
                /* Unify Alef variants:
                 * U+0622 (آ 0xD8 0xA2), U+0623 (أ 0xD8 0xA3), U+0625 (إ 0xD8 0xA5)
                 * -> U+0627 (ا 0xD8 0xA7)
                 */
                if (b1 == 0xA2 || b1 == 0xA3 || b1 == 0xA5) {
                    d[out_idx++] = 0xD8;
                    d[out_idx++] = 0xA7;
                    s += 2;
                    continue;
                }

                /* Fold Ta Marbuta U+0629 (ة 0xD8 0xA9) -> Heh U+0647 (ه 0xD9 0x87) */
                if (b1 == 0xA9) {
                    d[out_idx++] = 0xD9;
                    d[out_idx++] = 0x87;
                    s += 2;
                    continue;
                }
            } else if (b0 == 0xD9) {
                /* Strip Tatweel / Kashida U+0640 (ـ 0xD9 0x80) */
                if (b1 == 0x80) {
                    s += 2;
                    continue;
                }

                /* Strip Tashkeel diacritics U+064B..U+065F (0xD9 0x8B .. 0xD9 0x9F) */
                if (b1 >= 0x8B && b1 <= 0x9F) {
                    s += 2;
                    continue;
                }

                /* Unify Alef Maksura U+0649 (ى 0xD9 0x89) -> Ya U+064A (ي 0xD9 0x8A) */
                if (b1 == 0x89) {
                    d[out_idx++] = 0xD9;
                    d[out_idx++] = 0x8A;
                    s += 2;
                    continue;
                }

                /* Unify Alef Wasla U+0671 (ٱ 0xD9 0xB1) -> Alef U+0627 (ا 0xD8 0xA7) */
                if (b1 == 0xB1) {
                    d[out_idx++] = 0xD8;
                    d[out_idx++] = 0xA7;
                    s += 2;
                    continue;
                }

                /* Fold Eastern Arabic digits U+0660..U+0669 (٠-٩: 0xD9 0xA0..0xA9) -> ASCII '0'..'9' */
                if (b1 >= 0xA0 && b1 <= 0xA9) {
                    d[out_idx++] = (unsigned char)('0' + (b1 - 0xA0));
                    s += 2;
                    continue;
                }
            } else if (b0 == 0xDB) {
                /* Fold Extended/Persian Arabic digits U+06F0..U+06F9 (۰-۹: 0xDB 0xB0..0xB9) -> ASCII '0'..'9' */
                if (b1 >= 0xB0 && b1 <= 0xB9) {
                    d[out_idx++] = (unsigned char)('0' + (b1 - 0xB0));
                    s += 2;
                    continue;
                }
            }
        }

        /* Copy standard character unchanged */
        d[out_idx++] = *s++;
    }

    d[out_idx] = '\0';
    return out_idx;
}

/* Time-gated FadeMem step function with time-acceleration */
void nibras_fademem_step_hardened(
    nibras_memory_node_t        *nodes,
    size_t                       count,
    uint64_t                     now_utc,
    double                       half_life_sec,
    double                       sim_time_scale,
    double                       consolidation_window_sec,
    nibras_telemetry_snapshot_t *out_snap
) {
    if (!nodes || !out_snap || half_life_sec <= 0.0) return;
    memset(out_snap, 0, sizeof(*out_snap));
    if (sim_time_scale <= 0.0) sim_time_scale = 1.0;

    double friction_sum = 0.0;
    size_t friction_count = 0;

    for (size_t i = 0; i < count; ++i) {
        out_snap->total_raw_tokens += nodes[i].token_cost;

        double raw_dt = (now_utc > nodes[i].created_utc)
                      ? (double)(now_utc - nodes[i].created_utc)
                      : 0.0;
        double effective_dt = raw_dt * sim_time_scale;
        double exponent = -(effective_dt / half_life_sec);
        nodes[i].current_intensity = nodes[i].initial_intensity * pow(2.0, exponent);

        /* Time-Gated Rule Promotion: high salience nodes promote only after consolidation window */
        if (effective_dt >= consolidation_window_sec &&
            nodes[i].initial_intensity >= 0.80 &&
            nodes[i].valence != 0) {
            nodes[i].state = TRAJ_DISTILLED_RULE;
            nodes[i].current_intensity = 1.0; /* Permanent procedural rule */
            out_snap->distilled_rules_count++;
            out_snap->active_tokens_after_prune += (nodes[i].token_cost / 6);
        }
        /* Prune noise below 0.25 threshold unless valence inverted */
        else if (nodes[i].current_intensity < 0.25 && !nodes[i].valence_inverted) {
            nodes[i].state = TRAJ_NOISE_PRUNED;
        } else {
            nodes[i].state = nodes[i].valence_inverted ? TRAJ_RECOVERY_VECTOR : TRAJ_ACTIVE_EPISODIC;
            out_snap->active_tokens_after_prune += nodes[i].token_cost;
        }

        if (nodes[i].valence < 0 && nodes[i].state != TRAJ_NOISE_PRUNED) {
            friction_sum += nodes[i].current_intensity;
            friction_count++;
        }
    }

    if (out_snap->total_raw_tokens > 0 &&
        out_snap->active_tokens_after_prune <= out_snap->total_raw_tokens) {
        uint32_t saved = out_snap->total_raw_tokens - out_snap->active_tokens_after_prune;
        out_snap->tokens_saved_pct = (saved * 100U) / out_snap->total_raw_tokens;
    }

    out_snap->cognitive_friction_index = (friction_count > 0)
                                       ? (friction_sum / (double)friction_count)
                                       : 0.0;
}

#ifdef NIBRAS_STANDALONE_TEST
#include <assert.h>

int main(void) {
    /* Test 1: Arabic UTF-8 Normalization with both 0xD9 and 0xDB digits */
    const char *raw_arabic = "إدارة الأزمات في دبي ٢٠٢٧ و ۰۹۸۷۶ - مدرسةٌ ذكية";
    char norm_buf[256];
    arabic_normalize_utf8_hardened(raw_arabic, norm_buf, sizeof(norm_buf));

    /* Check that both Eastern digits (2027) and Extended digits (09876) folded to ASCII */
    assert(strstr(norm_buf, "2027") != NULL);
    assert(strstr(norm_buf, "09876") != NULL);
    assert(strstr(norm_buf, "اداره الازمات في دبي 2027 و 09876 - مدرسه ذكيه") != NULL);

    /* Test 2: FadeMem 7-Day Time-Acceleration with Consolidation Window */
    nibras_memory_node_t nodes[3] = {
        { .id = 1, .summary = "Routine calendar ping", .valence = 0, .initial_intensity = 0.40,
          .created_utc = 1000, .token_cost = 1200, .valence_inverted = false },
        { .id = 2, .summary = "Transient compilation log", .valence = 0, .initial_intensity = 0.55,
          .created_utc = 1000, .token_cost = 1800, .valence_inverted = false },
        { .id = 3, .summary = "Thorn: DIFC API requires UTC timestamp", .valence = -1,
          .initial_intensity = 0.92, .created_utc = 1000, .token_cost = 600, .valence_inverted = false }
    };

    nibras_telemetry_snapshot_t snap;
    /* 60 seconds wall clock at 10080x = 604,800 virtual seconds (7 full days) */
    nibras_fademem_step_hardened(nodes, 3, 1060, 86400.0, 10080.0, 86400.0, &snap);

    assert(nodes[0].state == TRAJ_NOISE_PRUNED);
    assert(nodes[1].state == TRAJ_NOISE_PRUNED);
    assert(nodes[2].state == TRAJ_DISTILLED_RULE);
    assert(snap.tokens_saved_pct >= 90);

    printf("[PASS] All Nibras C99 Hardened Arabic Normalizer & FadeMem tests passed! (Tokens saved: %u%%)\n",
           snap.tokens_saved_pct);
    return 0;
}
#endif
