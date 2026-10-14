# Grading evidence — HelpDesk capstone

All screenshots were captured on 2026-10-14, except `m3-commit-history.png`, which was re-captured on 2026-10-15 after the history was rewritten. Terminal images are renderings of the real command output. The exact text of each is in [`raw/`](raw/).

| Module | Evidence | What it shows |
|---|---|---|
| **M1** App | [m1-app-dashboard.png](m1-app-dashboard.png), [m1-app-ticket-detail.png](m1-app-ticket-detail.png), [m1-app-mobile.png](m1-app-mobile.png) | React UI on `localhost:3000`: KPI cards, filters, ticket drawer with conversation and internal note, and the responsive phone layout |
| | [m1-api-swagger.png](m1-api-swagger.png) | FastAPI Swagger UI listing all REST endpoints |
| | [m1-postgres-table.png](m1-postgres-table.png) | Rows in the PostgreSQL `tickets` table (schema created by Alembic) |
| **M2** Tests | [m2-pytest-passing.png](m2-pytest-passing.png) | `pytest -v`: 19 passed |
| **M3** Git | [m3-commit-history.png](m3-commit-history.png) | Commit history on GitHub with descriptive messages |
| **M4** Docker | [m4-docker-compose.png](m4-docker-compose.png) | `docker compose up --build`: all 3 services healthy; `id` shows backend uid 10001 and frontend uid 101 (non-root) |
| **M5** CI/CD | [m5-pipeline-green.png](m5-pipeline-green.png), [m5-build-scan-push-job.png](m5-build-scan-push-job.png) | Green GitHub Actions run: test → build → Trivy → push. [Run link](https://github.com/princekumar0509/devops-heros/actions/runs/37872148985) |
| | [m5-ghcr-backend-package.png](m5-ghcr-backend-package.png), [m5-ghcr-frontend-package.png](m5-ghcr-frontend-package.png) | GHCR packages tagged with the commit SHA `d38b280…` (not `latest`) |
| **M6** Trivy | [m6-trivy-scan.png](m6-trivy-scan.png) | Trivy scan of the exact CI images pulled from GHCR: 0 fixable HIGH/CRITICAL findings, exit code 0 |
| **M7** Terraform | [m7-terraform-plan.png](m7-terraform-plan.png), [raw/m7-terraform-plan.txt](raw/m7-terraform-plan.txt) | `terraform plan` against AWS account 931253428806 as IAM user `devops-admin`: **65 to add, 0 errors** (VPC with 2 public and 2 private subnets, NAT, EKS, managed node group, add-ons, IAM) |
| **M8** Kubernetes + Helm | [m8-helm-install.png](m8-helm-install.png), [m8-helm-list.png](m8-helm-list.png) | `helm upgrade --install` of `./helm/helpdesk` with the GHCR SHA images; `helm list` and `helm history` show revisions 1 and 2 |
| | [m8-kubectl-get.png](m8-kubectl-get.png) | Backend and frontend, 2 replicas each, all `Running` with 0 restarts; ClusterIP Services; Ingress; HPA; bound PVC |
| | [m8-app-via-ingress.png](m8-app-via-ingress.png), [m8-ingress-curl.png](m8-ingress-curl.png) | App served through the Ingress host `helpdesk.local`: `/` → frontend, `/api` → backend |
| | [m8-hpa-scaling.png](m8-hpa-scaling.png) | Under `scripts/load-test.sh` the HPA scales the backend from 2 to 6 pods |
| **M9** Observability | [m9-metrics-endpoint.png](m9-metrics-endpoint.png) | `/metrics` returns Prometheus-format output |
| | [m9-prometheus-targets-up.png](m9-prometheus-targets-up.png) | Prometheus target health: `serviceMonitor/helpdesk/helpdesk-backend` **6/6 UP** |
| | [m9-grafana-dashboard.png](m9-grafana-dashboard.png) | Auto-provisioned "HelpDesk API" Grafana dashboard with live request rate, error ratio, latency and per-pod CPU |
| **M10** Demo | [m10-troubleshooting-labs.png](m10-troubleshooting-labs.png) | Troubleshooting labs: ImagePullBackOff and a Service with no endpoints, diagnosed and fixed |

## Where M8/M9 ran, and what is still pending

The Kubernetes, Helm, Ingress, HPA and monitoring evidence comes from a **kind** cluster (Kubernetes 1.37) on the development laptop. It runs the same Helm chart, `values-prod.yaml` and **exact GHCR images built by CI**. EKS couldn't be used yet: the new AWS account is still waiting for AWS activation, and EC2/EKS API calls return `OptInRequired` / `SubscriptionRequiredException`.

**Still pending, until AWS activates the account:** `terraform apply` (the AWS console screenshot of the VPC and EKS), the CI deploy job to EKS, and `terraform destroy`. The steps are in [../README.md](../README.md) §6–§7 and [../terraform/README.md](../terraform/README.md).
