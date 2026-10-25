# Run Grid Trace with Docker

Docker Desktop must be running in Linux-container mode. Docker Compose 2.24+ is required for the optional runtime environment file. Node and Python on the host are not needed for the container build.

From PowerShell:

```powershell
cd "C:\Users\ambar.SAISH-ZEPHYRUS\OneDrive\Desktop\Grid trace\app"
docker compose up --build -d
docker compose ps
```

Open **http://127.0.0.1:8080/**. The first build downloads the Node/Python base images and locked packages. A new Docker data volume initializes a development month replay. The existing host app can continue using port 8000.

On another computer, clone/copy the project, create `app/.env` from `.env.example` and enter credentials locally if model access is needed, then run the same Compose command from `app/`. Without credentials, deterministic rules remain available. The browser needs WebGL for the 3D scene; case navigation and review remain available if rendering fails.

## API keys

Compose supplies the existing `app/.env` to the container at startup. It is optional and is excluded from the build context and image. The backend makes provider requests; keys do not enter the JavaScript bundle. Missing/failed providers fall back to rules under the existing policy. Gemini live verification remains pending.

After changing keys, recreate the container:

```powershell
docker compose up -d --force-recreate
```

Do not paste unredacted `docker compose config` or container-environment output into shared logs: it can contain runtime credentials. `docker compose config --quiet` validates configuration without printing them. For a hosted deployment, supply secrets using the hosting platform; the current localhost setup still uses simulated roles.

## Persistence and stopping

The named `gridtrace_data` volume contains SQLite (including journal files), evidence PNGs and generated exports at `/var/lib/gridtrace`. Restarting, rebuilding or recreating the service preserves that volume:

```powershell
docker compose restart
docker compose logs --tail 50 gridtrace
docker compose down
```

`down` keeps the volume. Adding `--volumes` would erase Docker's saved runs, cases and evidence.

Docker uses a separate data store from the host's existing `app/data/`; earlier host cases are not automatically imported. Continue using the host app for those cases until an explicit migration is made. Do not copy a live SQLite database without its journal state. Run only one Grid Trace service/process against a given database; the server owns a local clock and in-process investigation jobs.

## Port and access

To select another local port in PowerShell:

```powershell
$env:GRIDTRACE_PORT = "8081"
docker compose up -d
```

The published address stays bound to `127.0.0.1` because the role selector is a demo control, not authentication. Public/LAN access requires a separate access-protection and deployment configuration.

## Container design

The multi-stage image builds React/Vite with Node 24, installs the exact Python dependency lock on Python 3.14, and serves the built frontend/API/evidence from one FastAPI process. Runtime uses an unprivileged user. A Python-only HTTP health check avoids a curl dependency. Initial replay generation gets a 60-second health-check start period. Streaming connections have a 10-second shutdown grace period within Compose's 30-second stop allowance. Container shutdown interrupts active investigations; startup marks abandoned work interrupted, requiring explicit retry.

The saved evaluation reports and three evaluator source files are included for fingerprint validation. No evaluator runs on startup and no model requests are made by the health check. The image's evaluation describes the evaluated Python sources, not a claim of independent Linux field validation.

Docker environment-file behavior follows the [official Compose documentation](https://docs.docker.com/compose/how-tos/environment-variables/set-environment-variables/).

## Verified on 25 October 2026

- Built from the dependency locks on Docker Desktop's Linux/amd64 engine. The frontend production build passed inside the image; the existing large scene-chunk warning remains.
- Ran all 65 backend tests inside the Linux image with provider credentials disabled for the test process: 65 passed.
- Started a disposable Compose project on port 18080. The external `tests/docker_smoke.py` checked frontend assets, API health, saved evaluation freshness, SSE, a synthetic case's role/review flow, JSON/Markdown exports and frozen analysis.
- Recreated the container and verified the same case, four audit events, frozen analysis and a file in the evidence volume remained.
- Confirmed runtime UID 10001, working OpenCV import, and absence of host `.env`, `data/` and `node_modules/` paths in the image.
- Made one real Granite request from inside the container using runtime credentials: `ibm/granite-4-h-small` returned `ABSTAIN_NO_ACTION` (630 prompt / 133 completion tokens). Gemini was not retried.

This verifies the current Linux/amd64 container setup. Other CPU architectures and remote hosting environments still need their own smoke checks. The standalone smoke script uses host Python/httpx for developer verification; normal Docker use does not require host Python.
