# Rule 02: Security Standards & Data Integrity

## 1. Zero Hardcoded Credentials

- **API Keys & Secrets:** Never store sensitive keys (`WATSONX_API_KEY`, `WATSONX_PROJECT_ID`, `GEMINI_API_KEY`) in source code, committed config files, test fixtures, or client code.
- **Environment Isolation:** All credentials must be read exclusively from `.env` at process startup via `backend/settings.py`.
- **Git Protections:** `.env` and `.env.*` files must remain strictly ignored by `.gitignore` and `.bobignore`.

---

## 2. Role-Based Access & Actor Boundaries

- **Actor Headers:** Endpoints exposing unredacted simulation ground-truth (such as `GET /api/runs/{id}/truth` and truth comparison routes) must enforce role verification via the `X-Actor` HTTP header.
- **Presenter vs. Operator Roles:**
  - `presenter`: Allowed to inspect calibration truth and trigger simulation seeds.
  - `operator`: Restricted to public observed telemetry, ranked next-checks, and approved worker traces.

---

## 3. Input Validation & Mathematical Safety

- **Public Contract Validation:** All incoming HTTP payloads and route parameters must be validated using Pydantic schemas with `ConfigDict(extra='forbid')`.
- **Numerical Bounds & Division by Zero:**
  - Every calculation involving denominators (such as relative percentage loss or normalization factors) must include explicit zero-guard checks prior to division.
  - Power and resistance inputs must be bounded against negative or infinite values.
- **SQL Injection Prevention:**
  - Never construct SQL queries using string formatting or f-strings.
  - All database interactions through `backend/store.py` must use parameterized placeholders (`?`).

---

## 4. Audit Log Immutability & Forensic Integrity

- **Append-Only Ledgers:** SQLite interval records and audit events must be append-only.
- **Database Triggers:** Database-level triggers must prevent `UPDATE` and `DELETE` operations on historical interval and audit tables.
- **Evidence Hashes:** Drone and inspection image artifacts stored under `data/evidence/` must be hashed (SHA-256) upon creation to verify chain of custody.

---

## 5. Synthetic Data Disclosure

- **Clear Attribution:** All synthetic test scenarios, simulated readings, and benchmark fixtures must be explicitly disclosed with metadata indicators (`source: synthetic` / `quality: simulated`).
- **No Misrepresentation:** Never present simulated anomalies as live utility telemetry without transparent disclosure.
