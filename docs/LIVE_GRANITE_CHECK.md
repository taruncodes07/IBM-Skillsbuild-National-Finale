# Live Granite verification

Verified on 25 October 2026 against the existing Frankfurt IBM Cloud services.

- Associated the existing `WatsonMachineLearning` Runtime with the existing `Grid Trace` project through IBM's project API. Read-back confirmed the association.
- Updated the local ignored `.env` project ID from the old sandbox to Grid Trace. No API key or project ID is recorded here.
- IBM IAM authentication: HTTP 200.
- Inference endpoint: `https://eu-de.ml.cloud.ibm.com`.
- Model: `ibm/granite-4-h-small`.
- Standalone live registered-function call: valid typed proposal, supplied evidence ID and target preserved; selected `REQUEST_MISSING_DATA`. One measured request took 4.05 seconds and used 606 prompt plus 123 completion tokens.
- End-to-end application check: all four workers completed, Granite returned `REQUEST_MISSING_DATA`, the independent policy allowed it, and the investigation completed with nine persisted trace events.
- A preceding live missing-data run selected meter review and was correctly policy-rejected. That record was retained. The planner now receives an explicit policy-derived action enum, while independent policy validation remains mandatory.
- Adapter correction: Granite's double-encoded JSON arguments are decoded at most twice. Objects still pass strict Pydantic validation; lists, scalars, excessive encoding and invalid action schemas are rejected.
- Updated worker/provider regression tests: 12 passed. Other baseline tests were unchanged in this verification turn.

The local application was restarted to load the corrected configuration. Grok remains unconfigured and has not been live-verified. This connectivity check is not a blinded B2 benchmark, a field study or a savings result. Original source onboarding and optional visual inspection remain separate milestones.

No services, projects or IAM grants were created, and no commits or pushes were made.

## Adaptive verification

A live operator-requested electrical recheck produced evidence. Granite then selected and executed a topology check and replanned to an allowed missing-data request: two checks, three decisions (operator, Granite, Granite), two model calls. A separate browser run completed the operator electrical check and Granite recommended human meter review. Operator actions are labeled explicitly. All 43 backend tests and the frontend production build pass. Grok remains unconfigured. These are workflow checks, not independent B2 action-selection scores.
