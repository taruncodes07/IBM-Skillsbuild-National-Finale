# Rules (Agent Mode): Strict Typing & Type Safety

> **Applies to:** Agent Mode sessions modifying Python backend code or TypeScript frontend code.

---

## 1. Python Backend Strict Typing Standards

### A. Full Signature Type Annotations
- All functions, methods, and route handlers must include explicit parameter and return type annotations.
- Untyped arguments (`def process(data):`) are strictly prohibited in new or edited code.
- Use explicit `typing` or standard library generics:
  ```python
  from typing import Optional, List, Dict, Any, Union, Tuple

  def compute_balance(
      boundary_id: str,
      intervals: List[Dict[str, float]],
      tolerance_kw: float = 0.05
  ) -> Dict[str, Union[str, float, bool]]:
      ...
  ```

### B. Public Contract Schemas via Pydantic
- All HTTP request bodies, query models, and structured responses must inherit from `pydantic.BaseModel`.
- Models exposed at public or inter-module boundaries must specify `model_config = ConfigDict(extra='forbid')`.
- Validate optional values with `Optional[...] = None` rather than bare default values.

### C. Safe Value Extraction & Optional Guards
- Avoid direct dictionary key access on dynamic objects (`data["meter"]`); use `.get("meter")` with a fallback or validate via Pydantic.
- When searching iterables, use `next((x for x in items if ...), None)` followed by an explicit `if result is None:` check. Never let uncaught `StopIteration` escape.

---

## 2. TypeScript / React Frontend Strict Typing Standards

### A. Zero Tolerated `any` Types
- The `any` type is strictly forbidden.
- Use `unknown` when dealing with uncertain external JSON payloads and narrow the type with type guards:
  ```typescript
  function isApiError(err: unknown): err is ApiError {
    return typeof err === 'object' && err !== null && 'status' in err;
  }
  ```

### B. No Unsafe Non-Null Assertions
- Do not use the non-null assertion operator (`!`) unless the type system provably guarantees non-null in the immediate scope.
- Use optional chaining (`obj?.property`) and explicit fallback values (`?? defaultValue`).

### C. Discriminated Unions for State Machines
- Multi-state structures (such as investigation states, worker results, and alert classifications) must use discriminated string literal unions:
  ```typescript
  export type WorkerStatus =
    | { status: 'idle' }
    | { status: 'running'; workerId: string; progress: number }
    | { status: 'completed'; workerId: string; findings: Finding[] }
    | { status: 'failed'; workerId: string; error: string };
  ```

### D. Typed API Responses & Async Functions
- All asynchronous fetch utilities in `frontend/api.ts` must return typed Promises (`Promise<Snapshot>`, `Promise<RunState>`).
- Catch blocks must handle unknown error types safely without empty swallows (`.catch(() => {})`).
