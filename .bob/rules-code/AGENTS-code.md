# Grid Trace — Code Mode Context

Extends the root `AGENTS.md`. Use when writing, modifying, or refactoring code.

## Key files to read before editing

Before touching any backend module, read its header and the relevant section of
`AGENTS.md` — specifically the **Boundaries** table. The simulation/analytics
separation is the most critical invariant.

## Minimal-change principle

Make the smallest edit that solves the problem. Do not refactor unrelated code,
add unrequested features, or change test fixtures.

## Test after every change

```powershell
# From app/ with the project venv
$env:TEMP = "$PWD\.test-tmp"; $env:TMP = $env:TEMP
.\.venv\Scripts\python.exe -m pytest -q          # 101 backend tests
npm run test:client                               # 13 client tests
npm run build                                     # tsc + vite
```

All three must pass before considering a code change complete.

## Backend patterns

- Use `next((...), None)` with an explicit `None` check — never let
  `StopIteration` propagate to a route handler.
- Guard every division by a value that can be zero before the operation.
- Route handlers return `HTTPException` with a specific status code; log full
  tracebacks before raising 500s (`import traceback; logging.error(...)`).
- No f-string SQL; use parameterised `store.DB.execute('...', (value,))`.

## Frontend patterns

- No `!` non-null assertions unless TypeScript statically guarantees non-null.
- Never use `.catch(() => {})` — log at minimum, set visible error state for
  user-facing failures.
- Polling loops must cap retries with exponential back-off and a maximum failure
  count before surfacing an error banner.

## Do not commit or push

Changes are local-only unless the user explicitly requests otherwise.
