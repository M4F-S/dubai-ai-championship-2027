/* mcp_curl_client.c
 * Production C99 Driver for Stateless MCP 2026-07-28 over Streamable HTTP
 * Powered by libcurl (transport) + cJSON (JSON-RPC 2.0 serialization)
 */

#define _POSIX_C_SOURCE 200809L

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <stdint.h>
#include <stdbool.h>
#include <curl/curl.h>

#include "cJSON.h"
#include "mcp_curl_client.h"

/* Memory buffer for accumulating HTTP response body */
typedef struct {
    char  *data;
    size_t size;
} http_memory_buf_t;

static size_t curl_write_memory_callback(void *contents, size_t size, size_t nmemb, void *userp) {
    size_t realsize = size * nmemb;
    http_memory_buf_t *mem = (http_memory_buf_t *)userp;

    char *ptr = (char *)realloc(mem->data, mem->size + realsize + 1);
    if (!ptr) {
        return 0; /* Out of memory */
    }

    mem->data = ptr;
    memcpy(&(mem->data[mem->size]), contents, realsize);
    mem->size += realsize;
    mem->data[mem->size] = '\0';

    return realsize;
}

int mcp_client_global_init(void) {
    return (curl_global_init(CURL_GLOBAL_DEFAULT) == CURLE_OK) ? 0 : -1;
}

void mcp_client_global_cleanup(void) {
    curl_global_cleanup();
}

void mcp_response_free(mcp_tool_call_resp_t *resp) {
    if (!resp) return;
    if (resp->result_text_payload) {
        free(resp->result_text_payload);
        resp->result_text_payload = NULL;
    }
    if (resp->raw_json_response) {
        free(resp->raw_json_response);
        resp->raw_json_response = NULL;
    }
}

/* Internal routine: builds JSON-RPC 2.0 payload matching MCP 2026-07-28 spec */
static char *build_mcp_jsonrpc_body(
    const char *method,
    const char *tool_name,
    const char *arguments_json,
    uint64_t    request_id
) {
    cJSON *root = cJSON_CreateObject();
    if (!root) return NULL;

    cJSON_AddStringToObject(root, "jsonrpc", "2.0");
    cJSON_AddNumberToObject(root, "id", (double)request_id);
    cJSON_AddStringToObject(root, "method", method);

    cJSON *params = cJSON_CreateObject();
    if (params) {
        if (tool_name) {
            cJSON_AddStringToObject(params, "name", tool_name);
        }
        if (arguments_json && arguments_json[0] != '\0') {
            cJSON *args_parsed = cJSON_Parse(arguments_json);
            if (args_parsed) {
                cJSON_AddItemToObject(params, "arguments", args_parsed);
            } else {
                cJSON_AddObjectToObject(params, "arguments");
            }
        } else {
            cJSON_AddObjectToObject(params, "arguments");
        }
        cJSON_AddItemToObject(root, "params", params);
    }

    /* MCP 2026-07-28 protocol metadata */
    cJSON *meta = cJSON_CreateObject();
    if (meta) {
        cJSON_AddStringToObject(meta, "io.modelcontextprotocol/protocolVersion", "2026-07-28");
        cJSON_AddItemToObject(root, "_meta", meta);
    }

    char *json_str = cJSON_PrintUnformatted(root);
    cJSON_Delete(root);
    return json_str;
}

/* Parse JSON-RPC response from MCP Server */
static void parse_mcp_response(
    const char           *response_body,
    mcp_tool_call_resp_t *out_resp
) {
    if (!response_body || !out_resp) return;

    out_resp->raw_json_response = strdup(response_body);

    cJSON *root = cJSON_Parse(response_body);
    if (!root) {
        out_resp->status = MCP_ERR_JSON_PARSE;
        return;
    }

    /* Check for JSON-RPC error */
    cJSON *err_obj = cJSON_GetObjectItemCaseSensitive(root, "error");
    if (err_obj && cJSON_IsObject(err_obj)) {
        out_resp->is_rpc_error = true;
        out_resp->status = MCP_ERR_RPC_FAULT;

        cJSON *code = cJSON_GetObjectItemCaseSensitive(err_obj, "code");
        if (code && cJSON_IsNumber(code)) {
            out_resp->rpc_error_code = code->valueint;
        }

        cJSON *msg = cJSON_GetObjectItemCaseSensitive(err_obj, "message");
        if (msg && cJSON_IsString(msg) && msg->valuestring) {
            strncpy(out_resp->rpc_error_message, msg->valuestring, sizeof(out_resp->rpc_error_message) - 1);
        }
        cJSON_Delete(root);
        return;
    }

    /* Extract content from "result" */
    cJSON *res_obj = cJSON_GetObjectItemCaseSensitive(root, "result");
    if (res_obj) {
        cJSON *content_arr = cJSON_GetObjectItemCaseSensitive(res_obj, "content");
        if (content_arr && cJSON_IsArray(content_arr)) {
            cJSON *first_elem = cJSON_GetArrayItem(content_arr, 0);
            if (first_elem) {
                cJSON *text_node = cJSON_GetObjectItemCaseSensitive(first_elem, "text");
                if (text_node && cJSON_IsString(text_node) && text_node->valuestring) {
                    out_resp->result_text_payload = strdup(text_node->valuestring);
                }
            }
        }
        if (!out_resp->result_text_payload) {
            /* Fallback to printing unformatted result object */
            out_resp->result_text_payload = cJSON_PrintUnformatted(res_obj);
        }
        out_resp->status = MCP_SUCCESS;
    } else {
        out_resp->status = MCP_SUCCESS;
    }

    cJSON_Delete(root);
}

/* Execute HTTP POST request using libcurl */
static mcp_status_t execute_mcp_http_post(
    const mcp_client_config_t *config,
    const char                *mcp_method_header,
    const char                *post_body,
    mcp_tool_call_resp_t      *out_resp
) {
    if (!config || !config->endpoint_url || !post_body || !out_resp) {
        return MCP_ERR_INVALID_PARAM;
    }

    CURL *curl = curl_easy_init();
    if (!curl) {
        out_resp->status = MCP_ERR_CONNECT;
        return MCP_ERR_CONNECT;
    }

    http_memory_buf_t chunk = { .data = malloc(1), .size = 0 };
    if (!chunk.data) {
        curl_easy_cleanup(curl);
        out_resp->status = MCP_ERR_CONNECT;
        return MCP_ERR_CONNECT;
    }
    chunk.data[0] = '\0';

    /* Build HTTP headers adhering to Stateless MCP 2026-07-28 */
    struct curl_slist *headers = NULL;
    headers = curl_slist_append(headers, "Content-Type: application/json");
    headers = curl_slist_append(headers, "Accept: application/json, text/event-stream");
    headers = curl_slist_append(headers, "MCP-Protocol-Version: 2026-07-28");

    char method_hdr[128];
    snprintf(method_hdr, sizeof(method_hdr), "Mcp-Method: %s", mcp_method_header);
    headers = curl_slist_append(headers, method_hdr);

    if (config->bearer_token && config->bearer_token[0] != '\0') {
        char auth_hdr[256];
        snprintf(auth_hdr, sizeof(auth_hdr), "Authorization: Bearer %s", config->bearer_token);
        headers = curl_slist_append(headers, auth_hdr);
    }

    curl_easy_setopt(curl, CURLOPT_URL, config->endpoint_url);
    curl_easy_setopt(curl, CURLOPT_HTTPHEADER, headers);
    curl_easy_setopt(curl, CURLOPT_POSTFIELDS, post_body);
    curl_easy_setopt(curl, CURLOPT_WRITEFUNCTION, curl_write_memory_callback);
    curl_easy_setopt(curl, CURLOPT_WRITEDATA, (void *)&chunk);
    curl_easy_setopt(curl, CURLOPT_TIMEOUT_MS, (long)(config->timeout_ms ? config->timeout_ms : 5000));
    curl_easy_setopt(curl, CURLOPT_USERAGENT, "Qala-StatelessMCP-Client/1.0 (Dubai 2027)");

    CURLcode res = curl_easy_perform(curl);
    mcp_status_t final_status = MCP_SUCCESS;

    if (res != CURLE_OK) {
        if (res == CURLE_OPERATION_TIMEDOUT) {
            final_status = MCP_ERR_TIMEOUT;
        } else {
            final_status = MCP_ERR_CONNECT;
        }
        out_resp->status = final_status;
    } else {
        curl_easy_getinfo(curl, CURLINFO_RESPONSE_CODE, &out_resp->http_status_code);

        if (out_resp->http_status_code == 401 || out_resp->http_status_code == 403) {
            final_status = MCP_ERR_AUTH_BLOCKED;
            out_resp->status = final_status;
        } else if (out_resp->http_status_code >= 400) {
            final_status = MCP_ERR_HTTP_STATUS;
            out_resp->status = final_status;
        } else {
            parse_mcp_response(chunk.data, out_resp);
            final_status = out_resp->status;
        }
    }

    curl_slist_free_all(headers);
    curl_easy_cleanup(curl);
    free(chunk.data);

    return final_status;
}

mcp_status_t mcp_client_call_tool(
    const mcp_client_config_t *config,
    const mcp_tool_call_req_t *req,
    mcp_tool_call_resp_t      *out_resp
) {
    if (!out_resp) return MCP_ERR_INVALID_PARAM;
    memset(out_resp, 0, sizeof(*out_resp));

    if (!config || !req || !req->tool_name) {
        out_resp->status = MCP_ERR_INVALID_PARAM;
        return MCP_ERR_INVALID_PARAM;
    }

    char *post_body = build_mcp_jsonrpc_body("tools/call", req->tool_name, req->arguments_json, req->request_id);
    if (!post_body) {
        out_resp->status = MCP_ERR_JSON_PARSE;
        return MCP_ERR_JSON_PARSE;
    }

    mcp_status_t st = execute_mcp_http_post(config, "tools/call", post_body, out_resp);
    free(post_body);
    return st;
}

mcp_status_t mcp_client_list_tools(
    const mcp_client_config_t *config,
    uint64_t                   request_id,
    mcp_tool_call_resp_t      *out_resp
) {
    if (!out_resp) return MCP_ERR_INVALID_PARAM;
    memset(out_resp, 0, sizeof(*out_resp));

    if (!config) {
        out_resp->status = MCP_ERR_INVALID_PARAM;
        return MCP_ERR_INVALID_PARAM;
    }

    char *post_body = build_mcp_jsonrpc_body("tools/list", NULL, NULL, request_id);
    if (!post_body) {
        out_resp->status = MCP_ERR_JSON_PARSE;
        return MCP_ERR_JSON_PARSE;
    }

    mcp_status_t st = execute_mcp_http_post(config, "tools/list", post_body, out_resp);
    free(post_body);
    return st;
}

#ifdef MCP_CURL_STANDALONE_TEST
#include <assert.h>

int main(void) {
    /* Test 1: Verify JSON-RPC Body Builder produces valid MCP 2026-07-28 payload */
    char *body = build_mcp_jsonrpc_body("tools/call", "erp_customs_settlement", "{\"batch_id\":882,\"aed\":125000}", 42);
    assert(body != NULL);
    assert(strstr(body, "\"jsonrpc\":\"2.0\"") != NULL);
    assert(strstr(body, "\"id\":42") != NULL);
    assert(strstr(body, "\"method\":\"tools/call\"") != NULL);
    assert(strstr(body, "\"name\":\"erp_customs_settlement\"") != NULL);
    assert(strstr(body, "\"batch_id\":882") != NULL);
    assert(strstr(body, "\"io.modelcontextprotocol/protocolVersion\":\"2026-07-28\"") != NULL);
    free(body);

    /* Test 2: Verify MCP Response Parser on Successful Tool Execution */
    const char *mock_success_json =
        "{\"jsonrpc\":\"2.0\",\"id\":42,\"result\":{\"content\":[{\"type\":\"text\",\"text\":\"Settlement #882 executed for AED 125,000.00\"}]}}";
    
    mcp_tool_call_resp_t resp1;
    memset(&resp1, 0, sizeof(resp1));
    parse_mcp_response(mock_success_json, &resp1);

    assert(resp1.status == MCP_SUCCESS);
    assert(resp1.is_rpc_error == false);
    assert(resp1.result_text_payload != NULL);
    assert(strstr(resp1.result_text_payload, "AED 125,000.00") != NULL);
    mcp_response_free(&resp1);

    /* Test 3: Verify MCP Response Parser on JSON-RPC Error Payload */
    const char *mock_rpc_error_json =
        "{\"jsonrpc\":\"2.0\",\"id\":42,\"error\":{\"code\":-32602,\"message\":\"Invalid params: amount exceeds limit\"}}";

    mcp_tool_call_resp_t resp2;
    memset(&resp2, 0, sizeof(resp2));
    parse_mcp_response(mock_rpc_error_json, &resp2);

    assert(resp2.status == MCP_ERR_RPC_FAULT);
    assert(resp2.is_rpc_error == true);
    assert(resp2.rpc_error_code == -32602);
    assert(strstr(resp2.rpc_error_message, "exceeds limit") != NULL);
    mcp_response_free(&resp2);

    /* Test 4: Verify Honest Connection Fault on Non-Existent Local Port */
    mcp_client_global_init();

    mcp_client_config_t offline_cfg = {
        .endpoint_url = "http://127.0.0.1:59999/mcp",
        .bearer_token = NULL,
        .timeout_ms = 500
    };
    mcp_tool_call_req_t req = {
        .tool_name = "test_tool",
        .arguments_json = "{}",
        .request_id = 1
    };
    mcp_tool_call_resp_t resp3;
    mcp_status_t st = mcp_client_call_tool(&offline_cfg, &req, &resp3);

    assert(st == MCP_ERR_CONNECT);
    assert(resp3.status == MCP_ERR_CONNECT);
    mcp_response_free(&resp3);

    mcp_client_global_cleanup();

    printf("[PASS] All libcurl + cJSON Stateless MCP 2026-07-28 client tests passed successfully!\n");
    return 0;
}
#endif
