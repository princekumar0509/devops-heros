# HelpDesk — Customer Support Ticketing (Session 21 DevOps Capstone)

HelpDesk is a small SaaS-style support desk. Customers' problems come in as **tickets**. Support agents triage them by category and priority, assign an owner, reply to the customer or leave internal notes, and move each ticket through `OPEN → IN_PROGRESS → RESOLVED → CLOSED`. A dashboard shows the live queue: open, in progress, urgent, unassigned and resolved, plus where requests come from.

The application is deliberately small. The point of the project is the delivery pipeline around it: how a commit on a laptop becomes a scanned container image, running on AWS EKS, autoscaled and monitored.

```text
 git push ──► GitHub Actions ──────────────────────────────────────────────────────────────┐
              │ test:   ruff · pytest (19 tests) · frontend tests + build · helm lint       │
              │ build:  docker build backend + frontend (tag = commit SHA)                  │
              │ scan:   Trivy — fail on fixable HIGH/CRITICAL CVEs                          │
              │ push:   ghcr.io/<user>/helpdesk-{backend,frontend}:<sha>                    │
              │ deploy: OIDC → AWS (no stored keys) → helm upgrade --install on EKS         │
              └─────────────────────────────────────────────────────────────────────────────┘
 Terraform ──► AWS VPC (2 public + 2 private subnets, NAT) ──► EKS + managed node group
                                                             │
     Internet ─► ingress-nginx (AWS NLB) ─► Ingress ──┬─ /     ─► frontend Service ─► React/Nginx pods (×2)
                                                      └─ /api  ─► backend Service  ─► FastAPI pods (×2–6, HPA)
                                                                                         │
                                                                     PostgreSQL StatefulSet + EBS volume
     Prometheus ◄── ServiceMonitor scrapes /metrics ──┘      Grafana ◄── "HelpDesk API" dashboard (auto-provisioned)
```

| Layer | Technology |
|---|---|
| Frontend | React 19 + Vite, responsive CSS (light/dark), served by unprivileged Nginx |
| Backend | FastAPI, SQLAlchemy 2, Pydantic v2, Alembic migrations |
| Database | PostgreSQL 16 |
| Tests | pytest (isolated in-memory SQLite per test), ruff lint, Node test runner |
| Containers | Docker multi-stage builds, non-root users, Docker Compose |
| CI/CD | GitHub Actions → Trivy → GHCR → Helm deploy to EKS via OIDC |
| Infrastructure | Terraform: VPC + EKS (+ EBS CSI, metrics-server, GitHub OIDC role) |
| Kubernetes | Helm chart: Deployments, Services, StatefulSet, Ingress, HPA, ServiceMonitor |
| Observability | kube-prometheus-stack (Prometheus, Grafana, Alertmanager) |

---

## Repository layout

```text
session21-python/
├── backend/                 FastAPI app
│   ├── app/                 main.py (health/ready/metrics), routes.py (ticket API), models, schemas, db, config
│   ├── alembic/versions/    0001_create_tickets.py — tickets + ticket_comments tables
│   ├── tests/               conftest.py (isolated test DB) + 19 tests
│   ├── Dockerfile           multi-stage python:3.12-slim (venv, no pip at runtime), non-root uid 10001
│   └── requirements*.txt    runtime vs dev dependencies (pinned)
├── frontend/                React app (src/components/*), nginx.conf.template, multi-stage Dockerfile
├── docker-compose.yml       postgres + backend + frontend
├── terraform/               AWS VPC + EKS + IAM (see terraform/README.md)
├── helm/helpdesk/           Helm chart (+ values-dev.yaml for local clusters, values-prod.yaml for EKS)
├── k8s/                     namespace + optional GHCR pull-secret helper
├── monitoring/              kube-prometheus-stack values (Prometheus, Grafana, alert rules)
├── troubleshooting/         3 deliberately broken manifests with investigation + fix steps
└── scripts/                 seed-data.sh (demo data), load-test.sh (traffic for Grafana/HPA)

../.github/workflows/session21-helpdesk.yml   CI/CD pipeline (GitHub only runs workflows from the repo root)
```

---

## API

Interactive docs: `http://localhost:8000/docs` (Swagger UI).

| Method | Path | Purpose |
|---|---|---|
| GET | `/health` | Liveness: process is up |
| GET | `/ready` | Readiness: database reachable (`SELECT 1`) |
| GET | `/metrics` | Prometheus metrics (request count, latency histograms) |
| GET | `/api/tickets?status=&priority=&category=&q=` | List and filter tickets, newest first |
| GET | `/api/tickets/stats` | Counts by status and category, urgent-active and unassigned counts |
| GET | `/api/tickets/{id}` | One ticket |
| POST | `/api/tickets` | Create a ticket (always starts `OPEN`) |
| PUT | `/api/tickets/{id}` | Update status, priority, category, agent… (sets or clears `resolved_at`) |
| DELETE | `/api/tickets/{id}` | Delete a ticket and its comments |
| GET | `/api/tickets/{id}/comments` | Conversation thread |
| POST | `/api/tickets/{id}/comments` | Reply or internal note (an agent's public reply moves `OPEN → IN_PROGRESS`) |

```bash
curl -X POST localhost:8000/api/tickets -H 'Content-Type: application/json' \
  -d '{"subject":"Checkout returns 500","category":"BUG","priority":"URGENT",
       "requester_name":"Meera","requester_email":"meera@example.com"}'
```

---

## 1. Run locally with Docker Compose

```bash
cd session21-python
docker compose up --build        # first build takes a few minutes
./scripts/seed-data.sh           # optional: load demo tickets
```

| URL | What |
|---|---|
| http://localhost:3000 | HelpDesk UI (Nginx proxies `/api` to the backend) |
| http://localhost:8000/docs | Swagger UI |
| http://localhost:8000/metrics | Prometheus metrics |

Postgres is published on `127.0.0.1:5433` (5433, so it doesn't clash with a locally installed Postgres). To show the table:

```bash
docker compose exec postgres psql -U helpdesk -d helpdesk -c "select id, subject, status, priority from tickets;"
```

Stop with `docker compose down`. Add `-v` to also delete the database volume.

## 2. Run the backend without Docker

```bash
cd backend
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements-dev.txt
export DATABASE_URL='postgresql+psycopg://helpdesk:helpdesk@localhost:5433/helpdesk'   # e.g. the Compose Postgres
alembic upgrade head
uvicorn app.main:app --reload --port 8000

# frontend, in another terminal (proxies /api to :8000)
cd frontend && npm install && npm run dev      # http://localhost:5173
```

## 3. Tests

```bash
cd backend && pytest -v          # 19 tests, each on a fresh in-memory SQLite DB (never touches Postgres)
ruff check . && ruff format --check .
cd ../frontend && npm test       # helper/unit tests
```

The tests cover health, readiness and metrics, create and validation, list, filter and search, get/404, update and the `resolved_at` logic, delete, stats, comments, and the agent-reply status transition. `tests/conftest.py` overrides FastAPI's `get_db` dependency, so each test gets its own empty database.

Tests run **before** any image is built in CI. If they fail, the pipeline stops and no broken image reaches the registry.

---

## 4. CI/CD (GitHub Actions)

The workflow is [`.github/workflows/session21-helpdesk.yml`](../.github/workflows/session21-helpdesk.yml). It runs on every push or PR to `main` that touches `session21-python/`.

| Job | What happens |
|---|---|
| **test** | ruff → pytest → `npm ci && npm test && npm run build` → `helm lint` |
| **build-scan-push** | Builds both images tagged with `github.sha`, scans each with **Trivy** (`HIGH,CRITICAL`, `ignore-unfixed`, `exit-code: 1`), then pushes to **GHCR** (on pushes only, not PRs) |
| **deploy** | Assumes an AWS role through **GitHub OIDC**, runs `aws eks update-kubeconfig`, then `helm upgrade --install --rollback-on-failure --wait` with the new SHA tags |

The image tag is the commit SHA, so every running pod traces back to one exact commit (`kubectl get deploy helpdesk-backend -n helpdesk -o wide`).

**One-time setup:**
1. After `terraform apply` (with `github_repository` set), add two repository **variables** under *Settings → Secrets and variables → Actions → Variables*:
   - `AWS_DEPLOY_ROLE_ARN` = `terraform output -raw github_deploy_role_arn`
   - `EKS_CLUSTER_NAME` = `terraform output -raw cluster_name`

   Until these exist, the deploy job is skipped and test/build/scan/push still run.
2. After the first push, open *GitHub → your profile → Packages → helpdesk-backend / helpdesk-frontend → Package settings* and set the visibility to **Public**, so EKS can pull without credentials. If you'd rather keep them private, see `k8s/ghcr-pull-secret.example.sh`.

No AWS keys are stored in GitHub. The deploy role can only be assumed by workflow runs on `main` of this repository, and inside EKS it is limited to the `helpdesk` namespace.

## 5. Security scanning (Trivy)

Trivy scans each image's OS packages (Debian for the backend, Alpine for the frontend) and language dependencies (Python wheels; the frontend runtime image contains only static files and Nginx) for known CVEs and leaked secrets. The pipeline fails on any **HIGH or CRITICAL** vulnerability that already has a fixed version. Both Dockerfiles apply OS patches (`apt-get upgrade` / `apk upgrade`), and the Python dependencies are pinned to current releases. The backend image also removes `pip` after installing dependencies. A first scan flagged HIGH CVEs in libraries vendored inside pip (`urllib3`, `msgpack`, `setuptools`), code the running app never uses, so the multi-stage build drops pip from the runtime image instead of ignoring the findings. A clean scan doesn't mean "secure". It means no known, fixable, high-severity CVE was in the image at build time. It complements, rather than replaces, code review, dependency updates, secret scanning and runtime controls (non-root users, dropped Linux capabilities, Pod Security Standards).

---

## 6. AWS infrastructure (Terraform)

See [terraform/README.md](terraform/README.md) for details. In short:

```bash
cd terraform
cp terraform.tfvars.example terraform.tfvars      # set github_repository; never put AWS keys here
terraform init && terraform plan && terraform apply          # ~15–20 min
$(terraform output -raw configure_kubectl)                    # point kubectl at the cluster
```

This creates a VPC in `ap-south-1` with 2 public and 2 private subnets across 2 AZs and one NAT gateway. It also creates an EKS cluster with a managed node group (2× t3.medium), the EBS CSI driver (for the Postgres volume), metrics-server (for the HPA), and the GitHub OIDC deploy role.

> **Cost:** EKS control plane, NAT gateway, 2 EC2 nodes and a load balancer cost several USD per day. Run `terraform destroy` after grading (uninstall the Helm releases first so the load balancer is removed, see below).

## 7. Deploy to Kubernetes

One-time cluster bootstrap (after `terraform apply`):

```bash
kubectl apply -f k8s/namespace.yaml

# Ingress controller → creates an AWS load balancer
helm upgrade --install ingress-nginx ingress-nginx --repo https://kubernetes.github.io/ingress-nginx \
  -n ingress-nginx --create-namespace \
  --set controller.service.annotations."service\.beta\.kubernetes\.io/aws-load-balancer-type"=nlb

# Prometheus + Grafana (install before the app so the ServiceMonitor CRD exists)
helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
helm upgrade --install kube-prometheus-stack prometheus-community/kube-prometheus-stack \
  -n monitoring --create-namespace -f monitoring/kube-prometheus-stack-values.yaml
```

Deploy the app. CI does this on every push to `main`; this is the manual equivalent:

```bash
helm upgrade --install helpdesk ./helm/helpdesk -n helpdesk -f helm/helpdesk/values-prod.yaml \
  --set backend.image.repository=ghcr.io/<github-user>/helpdesk-backend  --set backend.image.tag=<sha> \
  --set frontend.image.repository=ghcr.io/<github-user>/helpdesk-frontend --set frontend.image.tag=<sha>

kubectl get pods,svc,ingress,hpa -n helpdesk
helm list -n helpdesk
kubectl get ingress helpdesk -n helpdesk     # ADDRESS = load balancer hostname → open http://<ADDRESS>
```

What the chart creates:

| Resource | Notes |
|---|---|
| `helpdesk-backend` Deployment | 2 replicas (HPA scales 2–6 on 60% CPU), startup/readiness/liveness probes, init container waits for Postgres, runs as non-root with all capabilities dropped |
| `helpdesk-frontend` Deployment | 2 replicas, Nginx on 8080 as uid 101 |
| `helpdesk-backend` / `helpdesk-frontend` Services | ClusterIP |
| `helpdesk-postgres` StatefulSet + Service + Secret | 5 Gi PVC; the password is generated on first install and kept across upgrades |
| `helpdesk` Ingress | `/api` → backend, `/` → frontend |
| HPA, ServiceMonitor, Grafana dashboard ConfigMap | Enabled in `values-prod.yaml` |

Rollback: `helm history helpdesk -n helpdesk` then `helm rollback helpdesk <revision> -n helpdesk`.

**Local cluster instead of EKS** (kind/minikube with ingress-nginx): build the images, load them into the cluster (`kind load docker-image helpdesk-backend:local helpdesk-frontend:local`), then run `helm upgrade --install helpdesk ./helm/helpdesk -n helpdesk -f helm/helpdesk/values-dev.yaml`. Add `127.0.0.1 helpdesk.local` to `/etc/hosts`.

## 8. Autoscaling demo (HPA)

```bash
kubectl get hpa -n helpdesk -w                                     # terminal 1
URL=http://<ingress-address> CONCURRENCY=40 REQUESTS=40000 ./scripts/load-test.sh   # terminal 2
```

Backend CPU climbs above the 60% target and the HPA adds pods, up to 6. When the load stops, it scales back to 2 after the stabilization window.

## 9. Monitoring (Prometheus + Grafana)

```bash
kubectl port-forward -n monitoring svc/kube-prometheus-stack-prometheus 9090:9090   # Status → Targets: helpdesk-backend UP
kubectl port-forward -n monitoring svc/kube-prometheus-stack-grafana 3001:80          # admin / helpdesk-admin (change it!)
```

In Grafana, open **Dashboards → HelpDesk API**. It is provisioned automatically from `helm/helpdesk/dashboards/helpdesk-api.json` and shows request rate, 5xx ratio, p95 latency, backend pods up, requests per endpoint, responses by status class, p50/p95/p99 latency, and per-pod CPU (what the HPA acts on). Run `scripts/load-test.sh` to fill the graphs. Two alert rules (`HelpDeskHighErrorRate`, `HelpDeskBackendDown`) are defined in `monitoring/kube-prometheus-stack-values.yaml`.

## 10. Troubleshooting labs

Each file in `troubleshooting/` has the symptoms, the commands to investigate, and the fix in its header comment.

| Lab | Symptom | Lesson |
|---|---|---|
| `broken-image.yaml` | `ImagePullBackOff` | `kubectl describe pod` → Events show that the tag doesn't exist |
| `broken-service.yaml` | Service has no endpoints | A Service finds pods only through label selectors, and `targetPort` must match the container port |
| `crashloop-bad-db.yaml` | `CrashLoopBackOff` | The image is fine but the config is wrong. `kubectl logs --previous` shows the DB connection error |

## 11. Tear down

```bash
helm uninstall helpdesk -n helpdesk
helm uninstall ingress-nginx -n ingress-nginx          # deletes the AWS load balancer
helm uninstall kube-prometheus-stack -n monitoring
kubectl delete pvc --all -n helpdesk                   # deletes the EBS volume
cd terraform && terraform destroy
```

---

## Final demo script

1. **App:** open the Ingress URL, create a ticket, open it, reply as the agent (it moves to *In progress*), resolve it.
2. **API:** use `/docs` to create, read, update and delete a ticket.
3. **DB:** `kubectl exec -n helpdesk helpdesk-postgres-0 -- psql -U helpdesk -d helpdesk -c "select id,subject,status from tickets"`
4. **Git → CI:** change something visible (e.g. the sidebar subtitle in `frontend/src/components/Sidebar.jsx`), commit, push, and watch the pipeline: tests → build → Trivy → GHCR → deploy.
5. **Registry:** GHCR package page showing the new `<sha>` tag.
6. **Kubernetes:** `kubectl get pods,svc,ingress,hpa -n helpdesk`, `helm history helpdesk -n helpdesk`, and refresh the browser to show the change live.
7. **Terraform:** walk through `terraform/main.tf` and show the VPC and EKS in the AWS console.
8. **HPA + monitoring:** run the load test, watch the HPA scale, and show the Grafana panels and the Prometheus target `UP`.
9. **Failure:** apply a troubleshooting lab and debug it live.

## Grading evidence checklist (see GRADING.md)

The screenshots for every module are in [`evidence/`](evidence/README.md), with an index of what each one shows.

| Module | Where it is | Screenshot to capture |
|---|---|---|
| M1 App | `backend/app`, `backend/alembic/versions`, `frontend/`, `docker-compose.yml` | UI in browser |
| M2 Tests | `backend/tests/`, `backend/pytest.ini` | `pytest -v` (19 passed) |
| M3 Git | repo history, `.gitignore` | commit history (≥ 10 commits) |
| M4 Docker | `backend/Dockerfile`, `frontend/Dockerfile` (multi-stage, both non-root) | `docker compose up --build`, http://localhost:3000 |
| M5 CI/CD | `../.github/workflows/session21-helpdesk.yml` | green run, GHCR packages with SHA tags |
| M6 Trivy | Trivy steps in the workflow | Trivy output in the run log |
| M7 Terraform | `terraform/`, `terraform.tfvars.example` | `plan`, AWS console VPC + EKS, `destroy` |
| M8 K8s + Helm | `k8s/`, `helm/helpdesk/` | `kubectl get pods/svc`, `helm list`, app via Ingress |
| M9 Observability | `monitoring/`, ServiceMonitor + dashboard in chart | `curl /metrics`, Prometheus Targets, Grafana |
| M10 Docs | this README | live demo |
