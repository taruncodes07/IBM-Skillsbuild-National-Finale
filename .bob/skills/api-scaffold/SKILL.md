---
name: api-scaffold
description: Scaffold a new typed API endpoint across FastAPI backend, Pydantic contracts, pytest acceptance tests, and TypeScript client integration.
---

# API Scaffold Skill

This workflow provides a standardized, error-free recipe for scaffolding new REST API endpoints in Grid Trace. It enforces end-to-end type safety, Pydantic validation, physical truth isolation, automated pytest verification, and TypeScript client integration.

---

## Workflow Steps

### Step 1: Define Pydantic Schemas (`backend/contracts.py`)

1. Open `backend/contracts.py`.
2. Define the request payload schema (if applicable) and response schema using Pydantic v2 models.
3. Enforce strict extra-field rejection on public contracts:

```python
from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List

class NewFeatureRequest(BaseModel):
    model_config = ConfigDict(extra='forbid')
    boundary_id: str = Field(..., description="Target boundary or asset identifier")
    sample_window: int = Field(default=4, ge=1, le=96, description="15-min intervals")

class NewFeatureResponse(BaseModel):
    model_config = ConfigDict(extra='forbid')
    status: str
    boundary_id: str
    computed_loss_kwh: float
    confidence: float
```

---

### Step 2: Implement Core Service Logic (`backend/`)

1. Implement the calculation or analytical function in the appropriate backend module (e.g. `analytics.py`, `ranking.py`, or `investigations.py`).
2. **Crucial Checks:**
   - **Truth Isolation:** Do NOT import `simulation.py` or access `store.private_truth`.
   - **Zero Division:** Guard all denominators before division operations.
   - **Units:** Confirm if inputs are in $\text{kWh}$ or $\text{kW}$. Normalize if quadratic losses are evaluated.

---

### Step 3: Register Route Handler (`backend/main.py`)

1. Open `backend/main.py`.
2. Import the schemas and service logic.
3. Define the FastAPI endpoint with response models, status codes, and error handlers:

```python
from backend.contracts import NewFeatureRequest, NewFeatureResponse
from fastapi import HTTPException, status

@app.post(
    "/api/features/calculate",
    response_model=NewFeatureResponse,
    status_code=status.HTTP_200_OK,
    tags=["Features"]
)
def calculate_feature(payload: NewFeatureRequest) -> NewFeatureResponse:
    try:
        result = perform_feature_calculation(payload.boundary_id, payload.sample_window)
        return NewFeatureResponse(**result)
    except KeyError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Asset or boundary not found: {exc}"
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc)
        )
```

---

### Step 4: Add Automated Acceptance Test (`tests/`)

1. Create or update a test in `tests/` (e.g., `test_features.py`).
2. Use `TestClient(app)` to test both happy path (200 OK) and error conditions (400, 404, 422):

```python
from fastapi.testclient import TestClient
from backend.main import app

client = TestClient(app)

def test_calculate_feature_success():
    response = client.post("/api/features/calculate", json={
        "boundary_id": "DT-01",
        "sample_window": 4
    })
    assert response.status_code == 200
    data = response.json()
    assert data["boundary_id"] == "DT-01"
    assert "computed_loss_kwh" in data

def test_calculate_feature_invalid_input():
    response = client.post("/api/features/calculate", json={
        "boundary_id": "DT-01",
        "sample_window": 0  # Below minimum ge=1
    })
    assert response.status_code == 422
```

---

### Step 5: Update Frontend TypeScript Client (`frontend/`)

1. In `frontend/types.ts`, define the matching TypeScript interfaces:

```typescript
export interface NewFeatureRequest {
  boundary_id: string;
  sample_window?: number;
}

export interface NewFeatureResponse {
  status: string;
  boundary_id: string;
  computed_loss_kwh: number;
  confidence: number;
}
```

2. In `frontend/api.ts`, add the typed API fetch wrapper:

```typescript
export async function calculateFeature(
  request: NewFeatureRequest
): Promise<NewFeatureResponse> {
  return fetchJson<NewFeatureResponse>('/api/features/calculate', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(request),
  });
}
```

---

### Step 6: Verify and Run Tests

Run the backend test suite from `app/` in PowerShell:

```powershell
$env:TEMP = "$PWD\.test-tmp"; $env:TMP = $env:TEMP
.\.venv\Scripts\python.exe -m pytest -q tests/test_features.py
npm run build
```
