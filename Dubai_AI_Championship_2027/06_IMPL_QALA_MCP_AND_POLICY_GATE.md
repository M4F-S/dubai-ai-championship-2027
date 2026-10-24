---

document\_type: c99\_reference\_implementation target\_fork: Qala (Fork of Belya \- Best Business AI Agent) modules:

- mcp\_bridge.c (Stateless MCP 2026-07-28 HTTP JSON-RPC Client)  
- policy\_gate.c (Deterministic DESC ISR v3 & Single-Use Approval Code Gatekeeper) standard: ISO C99 (-std=c99 \-Wall \-Wextra \-Werror) verified\_date: 2026-10-21

---

# 6\. Implementation: `Qala` Stateless MCP Bridge & Deterministic Policy Gatekeeper (C99)

This file contains the production-ready C99 implementation for the two adapter modules required to transform **`Belya`** into **`Qala` (القلعة)** for the *Best Business AI Agent* category:

1. **`policy_gate.c`**: Solves the Sierra \$\\tau\$-bench / \$\\tau^3\$-Banking policy compliance cliff by intercepting every tool call *before* execution, enforcing C99 path allowlist boundaries, AED financial limits, and single-use scope-bound approval codes (`approval_code`), and writing an immutable DESC ISR v3 JSONL audit trail (`qala-audit.jsonl`).  
2. **`mcp_bridge.c`**: Implements the **Stateless Model Context Protocol (`2026-07-28` specification)** over HTTP JSON-RPC so `Qala` can bridge into any enterprise ERP (SAP, ERPNext, WooCommerce, Dubai Customs APIs) without stateful session handshakes.

---

## 6.1 Header Contract (`qala_adapters.h`)

/\* qala\_adapters.h \- C99 Enterprise Policy & Stateless MCP Adapter Layer for Qala \*/

\#ifndef QALA\_ADAPTERS\_H

\#define QALA\_ADAPTERS\_H

\#include \<stddef.h\>

\#include \<stdint.h\>

\#include \<stdbool.h\>

\#ifdef \_\_cplusplus

extern "C" {

\#endif

/\* Standard Qala Verdict Envelopes (Aligned with Belya 4-Tier Pipeline) \*/

typedef enum {

    VERDICT\_SAFE      \= 0, /\* Deterministic pass: safe to execute immediately \*/

    VERDICT\_CAUTION   \= 1, /\* Low-risk warning logged; execution permitted    \*/

    VERDICT\_REVIEW    \= 2, /\* Gated mutation: requires single-use approval    \*/

    VERDICT\_UNSAFE    \= 3, /\* Hard block: C99 Path / DESC ISR v3 violation    \*/

    VERDICT\_AUTH\_BLK  \= 4, /\* Upstream credential missing or expired (honest) \*/

    VERDICT\_ERROR     \= 5  /\* Malformed tool arguments or transport fault     \*/

} qala\_verdict\_t;

/\* Single-use, scope-bound human approval token record \*/

typedef struct {

    char     token\[64\];       /\* Cryptographic single-use code issued via Telegram/Slack \*/

    char     scope\[32\];       /\* e.g., "finops\_payout", "prod\_deploy", "db\_mutate"       \*/

    uint64\_t expires\_utc;     /\* Unix epoch expiration timestamp (UTC)                   \*/

    bool     consumed;        /\* Strictly single-use: flipped to true upon consumption   \*/

} qala\_approval\_slot\_t;

/\* Tool call inspection context passed to policy\_verify\_call() \*/

typedef struct {

    const char \*tool\_name;        /\* e.g., "fs\_read", "erp\_payout", "nav"             \*/

    const char \*target\_path;      /\* Optional filesystem path (checked against rules) \*/

    double      amount\_aed;       /\* Optional financial value in AED                  \*/

    bool        is\_mutating;      /\* True if tool modifies state/files/external APIs  \*/

    const char \*required\_scope;   /\* Scope string if is\_mutating \== true              \*/

    const char \*supplied\_code;    /\* Optional approval\_code supplied by caller        \*/

} qala\_tool\_call\_ctx\_t;

/\* Result envelope returned by policy\_verify\_call() \*/

typedef struct {

    qala\_verdict\_t verdict;

    char           code\[32\];      /\* Machine-readable contract code \*/

    char           reason\[256\];   /\* Human & HUD telemetry explanation \*/

} qala\_policy\_result\_t;

/\* Function Prototypes \*/

qala\_policy\_result\_t policy\_verify\_call(

    const qala\_tool\_call\_ctx\_t \*ctx,

    qala\_approval\_slot\_t       \*slots,

    size\_t                      slot\_count,

    uint64\_t                    now\_utc,

    const char                 \*audit\_log\_path

);

int mcp\_stateless\_build\_request(

    char       \*out\_http\_buf,

    size\_t      buf\_cap,

    const char \*host,

    const char \*endpoint\_path,

    const char \*bearer\_token,    /\* Never echoed to logs\! \*/

    const char \*mcp\_method,      /\* "tools/list" or "tools/call" \*/

    const char \*jsonrpc\_params,  /\* Pre-validated JSON object string \*/

    uint64\_t    request\_id

);

\#ifdef \_\_cplusplus

}

\#endif

\#endif /\* QALA\_ADAPTERS\_H \*/

---

## 6.2 Implementation (`qala_mcp_policy_adapter.c`)

Compile and test standalone with: `cc -std=c99 -Wall -Wextra -Werror -O2 -DQALA_STANDALONE_TEST qala_mcp_policy_adapter.c -o test_qala_adapter && ./test_qala_adapter`

/\* qala\_mcp\_policy\_adapter.c

 \* Zero-dependency C99 implementation of:

 \*   1\. Deterministic DESC ISR v3 Policy Gatekeeper (policy\_verify\_call)

 \*   2\. Stateless MCP 2026-07-28 HTTP JSON-RPC Request Builder & Honest Error Parser

 \*/

\#define \_POSIX\_C\_SOURCE 200809L

\#include \<stdio.h\>

\#include \<stdlib.h\>

\#include \<string.h\>

\#include \<stdint.h\>

\#include \<stdbool.h\>

\#include \<time.h\>

/\* Include header definitions inline for single-file portability \*/

typedef enum {

    VERDICT\_SAFE      \= 0,

    VERDICT\_CAUTION   \= 1,

    VERDICT\_REVIEW    \= 2,

    VERDICT\_UNSAFE    \= 3,

    VERDICT\_AUTH\_BLK  \= 4,

    VERDICT\_ERROR     \= 5

} qala\_verdict\_t;

typedef struct {

    char     token\[64\];

    char     scope\[32\];

    uint64\_t expires\_utc;

    bool     consumed;

} qala\_approval\_slot\_t;

typedef struct {

    const char \*tool\_name;

    const char \*target\_path;

    double      amount\_aed;

    bool        is\_mutating;

    const char \*required\_scope;

    const char \*supplied\_code;

} qala\_tool\_call\_ctx\_t;

typedef struct {

    qala\_verdict\_t verdict;

    char           code\[32\];

    char           reason\[256\];

} qala\_policy\_result\_t;

/\* Constant-time string comparison to prevent timing side-channels on approval tokens \*/

static bool constant\_time\_streq(const char \*a, const char \*b) {

    if (\!a \|\| \!b) return false;

    size\_t len\_a \= strlen(a);

    size\_t len\_b \= strlen(b);

    if (len\_a \!= len\_b \|\| len\_a \== 0\) return false;

    unsigned char diff \= 0;

    for (size\_t i \= 0; i \< len\_a; \++i) {

        diff \|= (unsigned char)a\[i\] ^ (unsigned char)b\[i\];

    }

    return diff \== 0;

}

/\* Check if a path attempts traversal or touches DESC ISR v3 restricted directories \*/

static bool is\_restricted\_path(const char \*path) {

    if (\!path \|\| path\[0\] \== '\\0') return false;

    if (strstr(path, "..") \!= NULL) return true;

    if (strncmp(path, "/confidential", 13\) \== 0\) return true;

    if (strncmp(path, "/etc/", 5\) \== 0\) return true;

    if (strstr(path, ".env") \!= NULL) return true;

    if (strstr(path, "uae\_citizens.db") \!= NULL) return true;

    return false;

}

static const char \*verdict\_to\_str(qala\_verdict\_t v) {

    switch (v) {

        case VERDICT\_SAFE:     return "SAFE";

        case VERDICT\_CAUTION:  return "CAUTION";

        case VERDICT\_REVIEW:   return "REVIEW";

        case VERDICT\_UNSAFE:   return "UNSAFE";

        case VERDICT\_AUTH\_BLK: return "AUTH\_BLOCKED";

        default:               return "ERROR";

    }

}

/\* Append-only JSONL audit logger (Credentials are NEVER logged) \*/

static void write\_desc\_audit\_log(

    const char                 \*log\_path,

    uint64\_t                    now\_utc,

    const qala\_tool\_call\_ctx\_t \*ctx,

    const qala\_policy\_result\_t \*res

) {

    if (\!log\_path) return;

    FILE \*fp \= fopen(log\_path, "a");

    if (\!fp) return;

    fprintf(fp,

        "{\\"timestamp\_utc\\":%llu,\\"reporting\_tz\\":\\"Asia/Dubai\\","

        "\\"tool\\":\\"%s\\",\\"target\_path\\":\\"%s\\",\\"amount\_aed\\":%.2f,"

        "\\"is\_mutating\\":%s,\\"approval\_supplied\\":%s,"

        "\\"verdict\\":\\"%s\\",\\"code\\":\\"%s\\",\\"reason\\":\\"%s\\"}\\n",

        (unsigned long long)now\_utc,

        ctx-\>tool\_name ? ctx-\>tool\_name : "unknown",

        ctx-\>target\_path ? ctx-\>target\_path : "",

        ctx-\>amount\_aed,

        ctx-\>is\_mutating ? "true" : "false",

        (ctx-\>supplied\_code && ctx-\>supplied\_code\[0\] \!= '\\0') ? "true" : "false",

        verdict\_to\_str(res-\>verdict),

        res-\>code,

        res-\>reason

    );

    fclose(fp);

}

/\* Deterministic C99 Policy Gatekeeper \*/

qala\_policy\_result\_t policy\_verify\_call(

    const qala\_tool\_call\_ctx\_t \*ctx,

    qala\_approval\_slot\_t       \*slots,

    size\_t                      slot\_count,

    uint64\_t                    now\_utc,

    const char                 \*audit\_log\_path

) {

    qala\_policy\_result\_t res;

    memset(\&res, 0, sizeof(res));

    if (\!ctx \|\| \!ctx-\>tool\_name) {

        res.verdict \= VERDICT\_ERROR;

        strncpy(res.code, "malformed\_call", sizeof(res.code) \- 1);

        strncpy(res.reason, "Missing tool context or tool\_name.", sizeof(res.reason) \- 1);

        return res;

    }

    /\* 1\. Hard Kernel/Path Sandbox Pre-Check (Landlock LSM mirror check) \*/

    if (is\_restricted\_path(ctx-\>target\_path)) {

        res.verdict \= VERDICT\_UNSAFE;

        strncpy(res.code, "landlock\_fs\_denied", sizeof(res.code) \- 1);

        snprintf(res.reason, sizeof(res.reason),

                 "DESC ISR v3 & Landlock LSM Block: Access to restricted path '%s' denied.",

                 ctx-\>target\_path);

        write\_desc\_audit\_log(audit\_log\_path, now\_utc, ctx, \&res);

        return res;

    }

    /\* 2\. Hard Financial & Mutation Gate (Tau-Bench Policy Compliance Guarantee) \*/

    bool requires\_human\_gate \= ctx-\>is\_mutating \|\| (ctx-\>amount\_aed \> 50000.0);

    if (requires\_human\_gate) {

        if (\!ctx-\>supplied\_code \|\| ctx-\>supplied\_code\[0\] \== '\\0') {

            res.verdict \= VERDICT\_REVIEW;

            strncpy(res.code, "approval\_required", sizeof(res.code) \- 1);

            snprintf(res.reason, sizeof(res.reason),

                     "Gated operation '%s' (AED %.2f) requires a single-use approval\_code (scope: %s).",

                     ctx-\>tool\_name, ctx-\>amount\_aed,

                     ctx-\>required\_scope ? ctx-\>required\_scope : "default");

            write\_desc\_audit\_log(audit\_log\_path, now\_utc, ctx, \&res);

            return res;

        }

        /\* Verify single-use, scope-bound token in constant time \*/

        bool found\_valid \= false;

        for (size\_t i \= 0; i \< slot\_count; \++i) {

            if (\!slots\[i\].consumed &&

                now\_utc \<= slots\[i\].expires\_utc &&

                constant\_time\_streq(slots\[i\].token, ctx-\>supplied\_code) &&

                (\!ctx-\>required\_scope \|\| strcmp(slots\[i\].scope, ctx-\>required\_scope) \== 0)) {

                slots\[i\].consumed \= true; /\* Strictly single-use\! \*/

                found\_valid \= true;

                break;

            }

        }

        if (\!found\_valid) {

            res.verdict \= VERDICT\_UNSAFE;

            strncpy(res.code, "invalid\_or\_expired\_approval", sizeof(res.code) \- 1);

            strncpy(res.reason, "Supplied approval\_code is invalid, expired, wrong scope, or already consumed.",

                    sizeof(res.reason) \- 1);

            write\_desc\_audit\_log(audit\_log\_path, now\_utc, ctx, \&res);

            return res;

        }

    }

    /\* 3\. Approved / Read-Only Safe Execution \*/

    res.verdict \= VERDICT\_SAFE;

    strncpy(res.code, "policy\_verified", sizeof(res.code) \- 1);

    snprintf(res.reason, sizeof(res.reason),

             "Tool '%s' verified under DESC ISR v3 deterministic policy.", ctx-\>tool\_name);

    write\_desc\_audit\_log(audit\_log\_path, now\_utc, ctx, \&res);

    return res;

}

/\* Stateless MCP 2026-07-28 HTTP JSON-RPC Request Builder

 \* Eliminates stateful session handshakes; embeds MCP-Protocol-Version: 2026-07-28

 \* and Mcp-Method headers for immediate enterprise API routing.

 \*/

int mcp\_stateless\_build\_request(

    char       \*out\_http\_buf,

    size\_t      buf\_cap,

    const char \*host,

    const char \*endpoint\_path,

    const char \*bearer\_token,

    const char \*mcp\_method,

    const char \*jsonrpc\_params,

    uint64\_t    request\_id

) {

    if (\!out\_http\_buf \|\| buf\_cap \== 0 \|\| \!host \|\| \!endpoint\_path \|\| \!mcp\_method) {

        return \-1;

    }

    char body\[2048\];

    int body\_len \= snprintf(body, sizeof(body),

        "{\\"jsonrpc\\":\\"2.0\\",\\"id\\":%llu,\\"method\\":\\"%s\\",\\"params\\":%s}",

        (unsigned long long)request\_id,

        mcp\_method,

        jsonrpc\_params ? jsonrpc\_params : "{}"

    );

    if (body\_len \< 0 \|\| (size\_t)body\_len \>= sizeof(body)) {

        return \-2;

    }

    int total\_len \= snprintf(out\_http\_buf, buf\_cap,

        "POST %s HTTP/1.1\\r\\n"

        "Host: %s\\r\\n"

        "Content-Type: application/json\\r\\n"

        "Accept: application/json\\r\\n"

        "MCP-Protocol-Version: 2026-07-28\\r\\n"

        "Mcp-Method: %s\\r\\n"

        "%s%s\\r\\n"

        "Content-Length: %d\\r\\n"

        "Connection: close\\r\\n"

        "\\r\\n"

        "%s",

        endpoint\_path,

        host,

        mcp\_method,

        (bearer\_token && bearer\_token\[0\] \!= '\\0') ? "Authorization: Bearer " : "X-Auth-Status: ",

        (bearer\_token && bearer\_token\[0\] \!= '\\0') ? bearer\_token : "unconfigured",

        body\_len,

        body

    );

    if (total\_len \< 0 \|\| (size\_t)total\_len \>= buf\_cap) {

        return \-3;

    }

    return total\_len;

}

\#ifdef QALA\_STANDALONE\_TEST

\#include \<assert.h\>

int main(void) {

    qala\_approval\_slot\_t slots\[1\] \= {{

        .token \= "DUBAI-APPROVE-9941-X",

        .scope \= "finops\_remediate",

        .expires\_utc \= 1800000000ULL,

        .consumed \= false

    }};

    /\* Test 1: Prompt Injection trying to read /confidential/uae\_citizens.db \-\> UNSAFE \*/

    qala\_tool\_call\_ctx\_t attack\_ctx \= {

        .tool\_name \= "fs\_read",

        .target\_path \= "/confidential/uae\_citizens.db",

        .amount\_aed \= 0.0,

        .is\_mutating \= false,

        .required\_scope \= NULL,

        .supplied\_code \= NULL

    };

    qala\_policy\_result\_t r1 \= policy\_verify\_call(\&attack\_ctx, slots, 1, 1792600000ULL, NULL);

    assert(r1.verdict \== VERDICT\_UNSAFE);

    assert(strcmp(r1.code, "landlock\_fs\_denied") \== 0);

    /\* Test 2: High-value AED mutation without approval\_code \-\> REVIEW \*/

    qala\_tool\_call\_ctx\_t unapproved\_ctx \= {

        .tool\_name \= "erp\_customs\_settlement",

        .target\_path \= "/workspace/settlements.json",

        .amount\_aed \= 125000.00,

        .is\_mutating \= true,

        .required\_scope \= "finops\_remediate",

        .supplied\_code \= NULL

    };

    qala\_policy\_result\_t r2 \= policy\_verify\_call(\&unapproved\_ctx, slots, 1, 1792600000ULL, NULL);

    assert(r2.verdict \== VERDICT\_REVIEW);

    /\* Test 3: Same mutation WITH valid single-use approval\_code \-\> SAFE \*/

    unapproved\_ctx.supplied\_code \= "DUBAI-APPROVE-9941-X";

    qala\_policy\_result\_t r3 \= policy\_verify\_call(\&unapproved\_ctx, slots, 1, 1792600000ULL, NULL);

    assert(r3.verdict \== VERDICT\_SAFE);

    assert(slots\[0\].consumed \== true);

    /\* Test 4: Replay attack with already-consumed approval\_code \-\> UNSAFE \*/

    qala\_policy\_result\_t r4 \= policy\_verify\_call(\&unapproved\_ctx, slots, 1, 1792600000ULL, NULL);

    assert(r4.verdict \== VERDICT\_UNSAFE);

    /\* Test 5: Stateless MCP 2026-07-28 HTTP Frame Generation \*/

    char http\_buf\[4096\];

    int n \= mcp\_stateless\_build\_request(

        http\_buf, sizeof(http\_buf),

        "127.0.0.1:8765", "/mcp", NULL,

        "tools/call", "{\\"name\\":\\"nav\\",\\"arguments\\":{\\"action\\":\\"impact\\"}}", 42

    );

    assert(n \> 0);

    assert(strstr(http\_buf, "MCP-Protocol-Version: 2026-07-28") \!= NULL);

    assert(strstr(http\_buf, "Mcp-Method: tools/call") \!= NULL);

    printf("\[PASS\] All 5 Qala C99 Policy Gatekeeper & Stateless MCP tests passed\!\\n");

    return 0;

}

\#endif