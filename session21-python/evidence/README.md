# Grading evidence — HelpDesk capstone

Screenshots were captured on 2026-10-14. `m3-commit-history.png` was re-captured on 2026-10-15 after the history was rewritten, and the `eks-*` files were captured on 2026-10-16 from the live AWS deployment. Terminal images are renderings of the real command output. The exact text of each is in [`raw/`](raw/).

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

## Live deployment on AWS EKS (2026-10-16)

The same chart now runs on **AWS EKS** in account 284874841362, `ap-south-1`. It was provisioned by `terraform apply` and deployed by the CI pipeline itself through GitHub OIDC. These screenshots were captured from the live pages on 2026-10-16.

| Module | Evidence | What it shows |
|---|---|---|
| **M5** CI/CD | [eks-pipeline-green.png](eks-pipeline-green.png) | [Run #7](https://github.com/princekumar0509/devops-heros/actions/runs/38929115705) on commit `5acff46`: test → build + Trivy + push → **Deploy to EKS (Helm)**, all green |
| | [eks-ghcr-helpdesk-backend.png](eks-ghcr-helpdesk-backend.png), [eks-ghcr-helpdesk-frontend.png](eks-ghcr-helpdesk-frontend.png) | GHCR packages; each version is tagged with its full commit SHA |
| **M7** Terraform | [eks-aws-console-cluster.png](eks-aws-console-cluster.png) | AWS Console: EKS cluster `helpdesk-dev-eks`, status **Active**, Kubernetes 1.34 |
| | [eks-aws-console-nodegroup.png](eks-aws-console-nodegroup.png), [eks-aws-console-ec2-nodes.png](eks-aws-console-ec2-nodes.png) | Managed node group **Active** (desired size 2); both EC2 nodes running as `m7i-flex.large` across 2 AZs |
| | [eks-aws-console-vpc.png](eks-aws-console-vpc.png), [eks-aws-console-subnets.png](eks-aws-console-subnets.png) | VPC `helpdesk-dev-vpc` (10.20.0.0/16): **2 public and 2 private subnets** in ap-south-1a/1b, with their route tables |
| **M8** Kubernetes + Helm | [eks-app-via-ingress.png](eks-app-via-ingress.png) | App served from the public AWS NLB through ingress-nginx: `/` → frontend, `/api` → backend |
| | [raw/eks-kubectl-get.txt](raw/eks-kubectl-get.txt), [raw/eks-helm-list.txt](raw/eks-helm-list.txt), [raw/eks-aws-cluster-vpc.txt](raw/eks-aws-cluster-vpc.txt) | Nodes, pods, Services, Ingress, HPA and PVC on EKS; `helm list`; cluster and subnet details from the AWS CLI |
| **M9** Observability | [eks-prometheus-targets.png](eks-prometheus-targets.png) | Prometheus on EKS: `serviceMonitor/helpdesk/helpdesk-backend` **2/2 UP** |
| | [eks-grafana-dashboard.png](eks-grafana-dashboard.png) | "HelpDesk API" dashboard on EKS with live traffic: 2.2 req/s, 0% 5xx, p95 95 ms, 2 backend pods |

The console screenshots were taken through a one-hour, read-only federated sign-in. That is why a few widgets that need extra permissions show "Access denied" or "Data unavailable".

The `m8-*` and `m9-*` files above are the earlier run on a local **kind** cluster, made while the AWS account was waiting for activation. They use the same chart and the same CI-built images.

**Still to do after grading:** `terraform destroy` and its screenshot. See [../README.md](../README.md) §6.
