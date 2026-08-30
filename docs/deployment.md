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

## 4. What the live demo shows

With ingress + rule engine + risk fusion + decision engine + investigation
agent running, the chain works end-to-end over HTTP:

```bash
scripts/seed-demo.py            # drives the whole pipeline against localhost
# point it at the live services with VERIPAY_<SERVICE>_URL env vars, or
# run it inside the same network/container as the deployed services
```

The dashboard URL demonstrates the analyst console, investigation copilot,
FI Ops, and Business portals (MSW mocks against the frozen OpenAPI contracts).
