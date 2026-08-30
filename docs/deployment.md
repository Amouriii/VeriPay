# Deployment

How to put VeriPay in front of a real audience. Three paths:

| Path | Account needed | Result |
|---|---|---|
| **Instant tunnel** (`scripts/live-demo-tunnel.sh`) | None (Cloudflare quick tunnel) | Live HTTPS URL to a local service, for as long as the process runs |
| **Render Blueprint** (`infra/deploy/render.yaml`) | Render free account | Persistent HTTPS URL per service |
| **Railway** (`infra/deploy/railway.json`) | Railway free account | Persistent HTTPS URL per service |

The older `infra/terraform/` and `infra/k8s/` configs are **stubs** (managed
Kafka/Redis/Postgres and GKE/EKS placeholders); Render/Railway do not use
them. Use the configs in `infra/deploy/` instead.

## 0. The build (shared)

Every service depends on the local `veripay-common` package, which is **not on
PyPI**, so the generic image `infra/deploy/veripay.Dockerfile` installs it from
source first and builds each service with the **repository root as the build
context**:

```bash
docker build -f infra/deploy/veripay.Dockerfile --build-arg SERVICE=ingress .
```

Render/Railway inject a `PORT` variable; the image binds it via
`HTTP_PORT=${PORT:-8000}`. Trained ML artifacts under `ml/models/` are
gitignored, so a fresh cloud build runs the **deterministic fallback** paths
(`supervised_model`/`anomaly_model` report `model_available: false`). To serve
real models on a persistent deploy, add a build step that trains them:

```dockerfile
# after installing ml[training] in the image:
RUN pip install -e "./ml[training]" && python ml/datasets/generate_synthetic.py \
    && python ml/supervised/train.py && python ml/anomaly/train.py
```

## 1. Instant tunnel (no account, works today)

```bash
brew install cloudflared          # one-time
make up                          # or run the services you want to demo
scripts/live-demo-tunnel.sh 5173 # live URL for the web dashboard
scripts/live-demo-tunnel.sh 8001 # live URL for the ingress API
```

Copy the printed `https://<random>.trycloudflare.com` URL. It is publicly
reachable until the script stops. Caveat: one URL per port; the dashboard uses
MSW mocks, so it is fully navigable on its own.

## 2. Render (Blueprint, persistent)

1. Push this repo to GitHub (it already is: `github.com/Amouriii/VeriPay`).
2. In Render: **New → Blueprint → connect the repo**.
3. Render reads `infra/deploy/render.yaml` and provisions one free web service
   per core stage (ingress, rule engine, risk fusion, decision engine,
   investigation agent, feedback loop) plus the dashboard.
4. Each service gets a `https://<name>.onrender.com` URL; health checks are
   wired to `/health`.

CLI alternative: `npx -y @renderinc/cli blueprint launch` with your API key.

## 3. Railway (persistent)

Railway config is per-service; duplicate `infra/deploy/railway.json` per stage
(changing `SERVICE` / `startCommand`):

```bash
railway init   # link the repo
railway up     # deploys the Dockerfile from railway.json
```

The dashboard can be added as a static or service deploy (`npm ci && npm run
build && npm run preview -- --host 0.0.0.0 --port $PORT`).

## 4. Vercel (web dashboard preview)

The `web/` Vite + React dashboard is deployed through the **Vercel GitHub
integration** (project `veri-pay`, owner `onouh`). Every push/PR on the repo
triggers a preview deployment; `main` also deploys to production. The Vercel
check is informational on PRs — it is **not** a required status check on
`main`.

### The two places deployment is configured

| Where | What lives there | Example |
|---|---|---|
| **Vercel project settings** (dashboard or API) | `rootDirectory`, framework, install/build/output commands | `rootDirectory = web`, framework `vite` |
| **`vercel.json` at the repo root** | Deployment-level build config | `framework`, `buildCommand`, `outputDirectory` |

**`rootDirectory` is a Vercel *project setting* — it is NOT a `vercel.json`
key.** The `vercel.json` schema rejects it:

```
The `vercel.json` schema validation failed with the following message:
should NOT have additional property `rootDirectory`
```

Set it in the project settings (Dashboard → Project → Settings) or via the
API:

```bash
# Requires a Vercel token (vercel CLI login, or VERCEL_TOKEN).
curl -X PATCH -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" \
  -d '{"rootDirectory":"web","framework":"vite","buildCommand":"npm run build","outputDirectory":"dist","installCommand":"npm install"}' \
  https://api.vercel.com/v9/projects/veri-pay
```

The committed `vercel.json` (repo root) explicitly installs and builds the
`web/` package, publishes `web/dist`, and rewrites client-side routes (including
`/executive-demo`) to the Vite entrypoint. It is schema-valid; keep it minimal
and valid:

```json
{
  "$schema": "https://openapi.vercel.sh/vercel.json",
  "framework": "vite",
  "installCommand": "cd web && npm install",
  "buildCommand": "cd web && npm run build",
  "outputDirectory": "web/dist",
  "rewrites": [{"source": "/(.*)", "destination": "/index.html"}]
}
```

### Failure mode this configuration prevents

Without `rootDirectory`/framework set, Vercel auto-detects the **monorepo
root** (which has a `pyproject.toml`) as a **Python project**, scans
`services/**` for FastAPI apps, finds many `app` objects, and fails the build
with:

```
Add this to your pyproject.toml:
[tool.vercel]
entrypoint = "services.analyst_api.veripay_analyst_api.main:app"
```

Always check the **Deployments** page / `vercel ls veri-pay` after touching
deployment config: a deployment should show `READY` and build `web/`, not the
repo root.

### Env vars (build-time)

`VITE_API_BASE` and `VITE_ANALYST_API_BASE` are read at build time by Vite.
`web/.env` is gitignored, so for a deployed build set them in the Vercel
project's environment variables. Left unset, the dashboard falls back to the
MSW mocks and the analyst console to its mock handlers.

### CI regression check

`.github/workflows/ci.yml` has a `vercel-build` job that (1) statically
validates `vercel.json` (schema-valid, no `rootDirectory` key) and (2) runs
the real `vercel pull` + `vercel build` pipeline against the `veri-pay`
project so framework/rootDirectory changes are caught in CI, not at deploy
time. Step (2) requires the `VERCEL_TOKEN` repository secret; without it the
step reports a skip and only the static validation runs.

### Inspecting deployments


```bash
npx vercel whoami              # must print your account
npx vercel ls veri-pay         # recent deployments + ready state
npx vercel inspect dpl_... --logs   # build logs for one deployment
```

Preview URLs are protected by the account's SSO gate; open them signed in as
the project owner.

## 5. What the live demo shows

With ingress + rule engine + risk fusion + decision engine + investigation
agent running, the chain works end-to-end over HTTP:

```bash
scripts/seed-demo.py            # drives the whole pipeline against localhost
# point it at the live services with VERIPAY_<SERVICE>_URL env vars, or
# run it inside the same network/container as the deployed services
```

The dashboard URL demonstrates the analyst console, investigation copilot,
FI Ops, Business portals, and the executive board briefing at
`/executive-demo` (MSW mocks against the frozen OpenAPI contracts).
