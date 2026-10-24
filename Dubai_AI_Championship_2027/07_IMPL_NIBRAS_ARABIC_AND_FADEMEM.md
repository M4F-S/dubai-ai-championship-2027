---

document\_type: c99\_reference\_implementation target\_fork: Nibras (Fork of Almaz \- Best Personal & Societal AI Agent) modules:

- arabic\_norm.c (Zero-Allocation UTF-8 Arabic & Gulf Dialect Normalizer for SQLite FTS5)  
- fademem\_sim.c (Procedural Friction Appraisal & \--sim-time-scale 10080x Decay Engine) standard: ISO C99 (-std=c99 \-Wall \-Wextra \-Werror) verified\_date: 2026-10-21

---

# 7\. Implementation: `Nibras` UTF-8 Arabic Normalizer & `FadeMem` Time-Accelerator (C99)

This file provides the production-ready C99 implementation for the two adapter modules required for **`Nibras` (نبراس)** (the competition fork of **`Almaz`**):

1. **`arabic_normalize_utf8()`**: Eliminates lexical retrieval failures across Modern Standard Arabic (MSA), Emirati/Gulf dialects, and bilingual code-switching prior to indexing into `Almaz`/`Nibras`'s CORAL SQLite FTS5 store—unifying Alef/Ya variants, folding Ta Marbuta, stripping Tashkeel diacritics and Tatweel, and converting Eastern Arabic numerals (`٠-٩`) into ASCII digits (`0-9`) with zero heap allocations.  
2. **`nibras_fademem_step()`**: Preserves the exact C99 mathematics of `VIGIL` (`appraise_event()`) and `FadeMem` exponential decay (\$I(t') \= I\_0 \\cdot 2^{-(t'-t)/\\tau\_{1/2}}\$), while reframing telemetry outputs as **Workflow Friction & Token-Budget ROI** and adding the **`--sim-time-scale 10080x`** time-compression multiplier so judges can watch 7 days of memory pruning and procedural rule distillation in 10 seconds live on stage.

---

## 7.1 Complete C99 Source (`nibras_arabic_fademem_adapter.c`)

Compile and run the self-test suite with: `cc -std=c99 -Wall -Wextra -Werror -O2 -DNIBRAS_STANDALONE_TEST nibras_arabic_fademem_adapter.c -lm -o test_nibras_adapter && ./test_nibras_adapter`

/\* nibras\_arabic\_fademem\_adapter.c

 \* 1\. Zero-allocation UTF-8 Arabic/Dialect Normalizer for SQLite FTS5 BM25

 \* 2\. Procedural Friction Appraisal & Time-Accelerated FadeMem Engine (--sim-time-scale)

 \*/

\#include \<stdio.h\>

\#include \<stdlib.h\>

\#include \<string.h\>

\#include \<stdint.h\>

\#include \<stdbool.h\>

\#include \<math.h\>

/\* \============================================================================

 \* PART 1: ZERO-ALLOCATION UTF-8 ARABIC & DIALECT NORMALIZER FOR SQLITE FTS5

 \* \============================================================================

 \* In UTF-8, standard Arabic characters (U+0600..U+06FF) are encoded as 2-byte

 \* sequences starting with lead bytes 0xD8, 0xD9, 0xDA, or 0xDB:

 \*   U+0621..U+063F \-\> 0xD8 \[0xA1..0xBF\]

 \*   U+0640..U+067F \-\> 0xD9 \[0x80..0xBF\]

 \*/

size\_t arabic\_normalize\_utf8(const char \*src, char \*dst, size\_t dst\_cap) {

    if (\!src \|\| \!dst \|\| dst\_cap \== 0\) return 0;

    const unsigned char \*s \= (const unsigned char \*)src;

    unsigned char \*d \= (unsigned char \*)dst;

    size\_t out\_idx \= 0;

    while (\*s \!= '\\0' && (out\_idx \+ 3\) \< dst\_cap) {

        unsigned char b0 \= s\[0\];

        /\* Check for 2-byte UTF-8 Arabic blocks (0xD8 and 0xD9) \*/

        if ((b0 \== 0xD8 \|\| b0 \== 0xD9) && s\[1\] \!= '\\0') {

            unsigned char b1 \= s\[1\];

            if (b0 \== 0xD8) {

                /\* Unify Alef variants:

                 \* U+0622 (آ 0xD8 0xA2), U+0623 (أ 0xD8 0xA3), U+0625 (إ 0xD8 0xA5)

                 \* \-\> U+0627 (ا 0xD8 0xA7)

                 \*/

                if (b1 \== 0xA2 \|\| b1 \== 0xA3 \|\| b1 \== 0xA5) {

                    d\[out\_idx++\] \= 0xD8;

                    d\[out\_idx++\] \= 0xA7;

                    s \+= 2;

                    continue;

                }

                /\* Fold Ta Marbuta U+0629 (ة 0xD8 0xA9) \-\> Heh U+0647 (ه 0xD9 0x87) \*/

                if (b1 \== 0xA9) {

                    d\[out\_idx++\] \= 0xD9;

                    d\[out\_idx++\] \= 0x87;

                    s \+= 2;

                    continue;

                }

            } else if (b0 \== 0xD9) {

                /\* Strip Tatweel / Kashida U+0640 (ـ 0xD9 0x80) \*/

                if (b1 \== 0x80) {

                    s \+= 2;

                    continue;

                }

                /\* Strip Tashkeel diacritics U+064B..U+065F (0xD9 0x8B .. 0xD9 0x9F) \*/

                if (b1 \>= 0x8B && b1 \<= 0x9F) {

                    s \+= 2;

                    continue;

                }

                /\* Unify Alef Maksura U+0649 (ى 0xD9 0x89) \-\> Ya U+064A (ي 0xD9 0x8A) \*/

                if (b1 \== 0x89) {

                    d\[out\_idx++\] \= 0xD9;

                    d\[out\_idx++\] \= 0x8A;

                    s \+= 2;

                    continue;

                }

                /\* Unify Alef Wasla U+0671 (ٱ 0xD9 0xB1) \-\> Alef U+0627 (ا 0xD8 0xA7) \*/

                if (b1 \== 0xB1) {

                    d\[out\_idx++\] \= 0xD8;

                    d\[out\_idx++\] \= 0xA7;

                    s \+= 2;

                    continue;

                }

                /\* Fold Eastern Arabic digits U+0660..U+0669 (٠-٩: 0xD9 0xA0..0xA9) \-\> ASCII '0'..'9' \*/

                if (b1 \>= 0xA0 && b1 \<= 0xA9) {

                    d\[out\_idx++\] \= (unsigned char)('0' \+ (b1 \- 0xA0));

                    s \+= 2;

                    continue;

                }

            }

        }

        /\* Copy standard byte unchanged \*/

        d\[out\_idx++\] \= \*s++;

    }

    d\[out\_idx\] \= '\\0';

    return out\_idx;

}

/\* \============================================================================

 \* PART 2: PROCEDURAL FRICTION APPRAISAL & TIME-ACCELERATED FADEMEM ENGINE

 \* \============================================================================

 \* Reframes Almaz's VIGIL \+ FadeMem into enterprise-grade "Procedural Context

 \* Intelligence & Autonomous Token-Budget Pruning" with a live stage time-scaler.

 \*/

typedef enum {

    TRAJ\_NOISE\_PRUNED      \= 0, /\* Decayed below I \< 0.25 noise floor (Token saved\!) \*/

    TRAJ\_ACTIVE\_EPISODIC   \= 1, /\* Active working context                            \*/

    TRAJ\_DISTILLED\_RULE    \= 2, /\* Promoted to Semantic Memory (Rose / Thorn rule)   \*/

    TRAJ\_RECOVERY\_VECTOR   \= 3  /\* Valence inversion (+0.4 recovery determination)   \*/

} nibras\_traj\_state\_t;

typedef struct {

    uint64\_t            id;

    char                summary\[128\];

    int                 valence;         /\* \-1 (Thorn/Friction), 0 (Neutral), \+1 (Rose/Success) \*/

    double              initial\_intensity; /\* I\_0 in \[0.0, 1.0\] \*/

    double              current\_intensity; /\* I(t') after exponential decay \*/

    uint64\_t            created\_utc;

    uint32\_t            token\_cost;      /\* Tokens occupied if kept in raw episodic prompt \*/

    bool                valence\_inverted;/\* True if event inverted prior event's valence \*/

    nibras\_traj\_state\_t state;

} nibras\_memory\_node\_t;

typedef struct {

    uint32\_t total\_raw\_tokens;

    uint32\_t active\_tokens\_after\_prune;

    uint32\_t tokens\_saved\_pct;

    uint32\_t distilled\_rules\_count;

    double   cognitive\_friction\_index; /\* Aggregate active negative intensity \*/

} nibras\_telemetry\_snapshot\_t;

/\* Compute decayed intensity: I(t') \= I\_0 \* 2^(-(t' \- t) \* sim\_time\_scale / half\_life\_sec) \*/

void nibras\_fademem\_step(

    nibras\_memory\_node\_t        \*nodes,

    size\_t                       count,

    uint64\_t                     now\_utc,

    double                       half\_life\_sec,

    double                       sim\_time\_scale, /\* 1.0 normal; 10080.0 fast-forwards 7d in 1m \*/

    nibras\_telemetry\_snapshot\_t \*out\_snap

) {

    if (\!nodes \|\| \!out\_snap \|\| half\_life\_sec \<= 0.0) return;

    memset(out\_snap, 0, sizeof(\*out\_snap));

    if (sim\_time\_scale \<= 0.0) sim\_time\_scale \= 1.0;

    double friction\_sum \= 0.0;

    size\_t friction\_count \= 0;

    for (size\_t i \= 0; i \< count; \++i) {

        out\_snap-\>total\_raw\_tokens \+= nodes\[i\].token\_cost;

        double raw\_dt \= (now\_utc \> nodes\[i\].created\_utc)

                      ? (double)(now\_utc \- nodes\[i\].created\_utc)

                      : 0.0;

        double effective\_dt \= raw\_dt \* sim\_time\_scale;

        double exponent \= \-(effective\_dt / half\_life\_sec);

        nodes\[i\].current\_intensity \= nodes\[i\].initial\_intensity \* pow(2.0, exponent);

        /\* High-salience Thorn/Rose promotion into permanent procedural rules (85% less tokens) \*/

        if (nodes\[i\].initial\_intensity \>= 0.80 && nodes\[i\].valence \!= 0\) {

            nodes\[i\].state \= TRAJ\_DISTILLED\_RULE;

            out\_snap-\>distilled\_rules\_count++;

            out\_snap-\>active\_tokens\_after\_prune \+= (nodes\[i\].token\_cost / 6);

        }

        /\* Deterministic Deposit & Pruning Policy: drop entries with I \< 0.25 unless valence\_inverted \*/

        else if (nodes\[i\].current\_intensity \< 0.25 && \!nodes\[i\].valence\_inverted) {

            nodes\[i\].state \= TRAJ\_NOISE\_PRUNED;

            /\* 0 tokens added to active prompt\! \*/

        } else {

            nodes\[i\].state \= nodes\[i\].valence\_inverted ? TRAJ\_RECOVERY\_VECTOR : TRAJ\_ACTIVE\_EPISODIC;

            out\_snap-\>active\_tokens\_after\_prune \+= nodes\[i\].token\_cost;

        }

        if (nodes\[i\].valence \< 0 && nodes\[i\].state \!= TRAJ\_NOISE\_PRUNED) {

            friction\_sum \+= nodes\[i\].current\_intensity;

            friction\_count++;

        }

    }

    if (out\_snap-\>total\_raw\_tokens \> 0 &&

        out\_snap-\>active\_tokens\_after\_prune \<= out\_snap-\>total\_raw\_tokens) {

        uint32\_t saved \= out\_snap-\>total\_raw\_tokens \- out\_snap-\>active\_tokens\_after\_prune;

        out\_snap-\>tokens\_saved\_pct \= (saved \* 100U) / out\_snap-\>total\_raw\_tokens;

    }

    out\_snap-\>cognitive\_friction\_index \= (friction\_count \> 0\)

                                       ? (friction\_sum / (double)friction\_count)

                                       : 0.0;

}

\#ifdef NIBRAS\_STANDALONE\_TEST

\#include \<assert.h\>

int main(void) {

    /\* Test 1: Arabic UTF-8 Normalization (Alef variants, Tashkeel, Ta Marbuta, Eastern Digits) \*/

    const char \*raw\_arabic \= "إدارة الأزمات في دبي ٢٠٢٧ \- مدرسةٌ ذكية";

    char norm\_buf\[256\];

    arabic\_normalize\_utf8(raw\_arabic, norm\_buf, sizeof(norm\_buf));

    /\* Verify Eastern digits ٢٠٢٧ became ASCII 2027 and Alef variants unified \*/

    assert(strstr(norm\_buf, "2027") \!= NULL);

    assert(strstr(norm\_buf, "اداره الازمات في دبي 2027 \- مدرسه ذكيه") \!= NULL);

    /\* Test 2: FadeMem 7-Day Time-Acceleration (--sim-time-scale 10080x) \*/

    nibras\_memory\_node\_t nodes\[3\] \= {

        { .id \= 1, .summary \= "Routine status ping", .valence \= 0, .initial\_intensity \= 0.40,

          .created\_utc \= 1000, .token\_cost \= 1200, .valence\_inverted \= false },

        { .id \= 2, .summary \= "Transient build log", .valence \= 0, .initial\_intensity \= 0.55,

          .created\_utc \= 1000, .token\_cost \= 1800, .valence\_inverted \= false },

        { .id \= 3, .summary \= "Thorn: ERP Invoice API requires UTC timestamp", .valence \= \-1,

          .initial\_intensity \= 0.92, .created\_utc \= 1000, .token\_cost \= 600, .valence\_inverted \= false }

    };

    nibras\_telemetry\_snapshot\_t snap;

    /\* Advance wall clock by only 60 seconds, with sim\_time\_scale \= 10080x (simulating 7 full days) \*/

    nibras\_fademem\_step(nodes, 3, 1060, 86400.0 /\* 24h half-life \*/, 10080.0, \&snap);

    assert(nodes\[0\].state \== TRAJ\_NOISE\_PRUNED);

    assert(nodes\[1\].state \== TRAJ\_NOISE\_PRUNED);

    assert(nodes\[2\].state \== TRAJ\_DISTILLED\_RULE);

    assert(snap.tokens\_saved\_pct \>= 90);

    printf("\[PASS\] All Nibras Arabic UTF-8 Normalizer & FadeMem Time-Accelerator tests passed\! (Tokens saved: %u%%)\\n",

           snap.tokens\_saved\_pct);

    return 0;

}

\#endif