# Grid Trace provider setup

Granite through watsonx is primary, Gemini through Google is fallback, and the deterministic rule planner remains available if neither completes a valid response. All provider calls occur in the backend.

Copy `.env.example` to `.env` inside `app/`, fill credentials locally, and restart the server. The application loads supported settings as plain data; it never executes the file. Existing shell environment values take precedence. Populated `.env` files are ignored by Git. Do not paste keys into the browser, chat or case notes.

For IBM, set `WATSONX_API_KEY`, `WATSONX_PROJECT_ID`, `WATSONX_URL` and `WATSONX_MODEL_ID`. The provisional model is `ibm/granite-4-h-small`; verify its chat/tool capability and availability in your project/region.

For Gemini, set `GEMINI_API_KEY` and an available tool-capable `GEMINI_MODEL_ID`. No Gemini model ID is assumed without account verification.

The adapters submit a registered `grid_trace_next_check` function schema. Returned arguments are validated with Pydantic and checked against local evidence and policy. Only sanitized worker summaries and source metadata are sent. No private challenge truth, renderer-only geometry, raw API credentials or model private reasoning is stored in investigation traces.

Current limits: 500 output tokens, 15-second HTTP operation timeout, a shared 60-second investigation deadline, six provider attempts total across planning rounds, and at most two attempts per provider in a selection pass. At most three read-only local checks execute. A successful fallback stays pinned for later rounds. Only transient errors are retried. Tool execution is separate and is never retried simply because a model request failed. A policy denial stops the proposal; another provider is not used to evade it.

The tests cover mocked successful function calls, Granite-to-Gemini failover, bounded failure and rule fallback. Granite was live-verified on 25 October 2026, including a completed four-worker investigation and policy-approved action; see LIVE_GRANITE_CHECK.md. Gemini remains unconfigured and has not been live-verified. Health distinguishes configured credentials from verified execution; actual trace events identify the provider used.

References:

- IBM chat API: https://cloud.ibm.com/apidocs/watsonx-ai
- Gemini function calling compatibility: https://ai.google.dev/gemini-api/docs/openai
- LangGraph state graph: https://docs.langchain.com/oss/python/langgraph/use-graph-api

The application uses direct HTTP adapters and LangGraph. External LangSmith tracing is disabled around workflow execution. Cases and logs remain in local SQLite/data storage; a configured model provider receives the deidentified worker context required for planning.

Gemini uses Google's OpenAI-compatible Chat Completions endpoint with a forced registered function call. No OpenAI account or SDK is required. Create the key in https://aistudio.google.com/apikey and choose a tool-capable model available to that project. If both models fail, the fixed rule planner handles remaining evidence under the same policy checks. Historical Grok traces retain their original attribution.

Live Gemini check, 25 October 2026: model-list authentication succeeds (HTTP 200), and the configured gemini-3.8-flash is listed. The compatibility tool-call request repeatedly hit its bounded read timeout. A tiny native generateContent request returned HTTP 503 UNAVAILABLE. Live Gemini planning and Granite-to-Gemini failover remain unverified; mocked tests pass. No credentials are included in this record.
