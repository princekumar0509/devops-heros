# HelpDesk: presentation script

**Total length:** about 12 minutes, in 12 parts.

**How to record your voice:**
- Record **one audio file per part**, named `part01.m4a`, `part02.m4a` … `part12.m4a`. Phone voice-memo files (`.m4a`, `.mp3`, `.wav`) all work.
- Put the 12 files in `session21-python/presentation/audio/`. That folder is git-ignored, so your voice files are not pushed to GitHub.
- Speak at a calm pace. If you stumble, stop and record that part again. Don't try to fix it mid-sentence.
- You don't need to match the timing exactly. The video for each part is stretched or trimmed to fit your audio.
- To combine them with the screen recordings, run `python make_video.py --audio audio/` in this folder. It writes `recording/HelpDesk-Presentation.mp4`.
- Everything in **"Say"** is what you read aloud. **"On screen"** describes what the video shows at that moment, so you know what you're talking about.

---

## Part 1: Introduction (≈ 45 s)

**On screen:** title slide, then the "What is HelpDesk" slide.

**Say:**
> Hello, my name is Prince Kumar. This is my DevOps capstone project, **HelpDesk**.
>
> HelpDesk is a customer-support ticketing system. Customers raise tickets, such as a bug, a billing question or a feature request, and support agents pick them up, reply, add internal notes and resolve them.
>
> In this presentation I'll show the application, then the full DevOps pipeline around it: testing, Docker, CI/CD, security scanning, Terraform on AWS, Kubernetes with Helm, and monitoring with Prometheus and Grafana. At the end I'll show a live change going from a Git commit to production on AWS.

---

## Part 2: Architecture (≈ 60 s)

**On screen:** architecture slide.

**Say:**
> This is the architecture.
>
> The frontend is **React**, served by **Nginx**. The backend is a **FastAPI** REST API in Python, and the data is in **PostgreSQL**. The database schema is managed with **Alembic** migrations.
>
> When I push code to GitHub, **GitHub Actions** runs the tests, builds Docker images, scans them with **Trivy**, and pushes them to the **GitHub Container Registry**.
>
> The infrastructure on AWS (a VPC and an EKS Kubernetes cluster) is created with **Terraform**. The pipeline then deploys the application to EKS with **Helm**.
>
> Users reach the app through an **AWS load balancer** and an **NGINX Ingress**. **Prometheus** collects metrics from the backend, and **Grafana** shows them on a dashboard.

---

## Part 3: The application (≈ 90 s)

**On screen:** the live HelpDesk app on AWS, then the Swagger API page.

**Say:**
> This is the application running on AWS, opened through the load-balancer address.
>
> The dashboard shows the number of open tickets, tickets in progress, urgent tickets and resolved tickets, plus a breakdown by category.
>
> Let me create a new ticket. I enter the subject, the customer's name and email, choose a category and a priority, and save it. It appears in the list straight away.
>
> The new ticket opens on the right. I assign it to myself, then reply to the customer. Because the assigned agent replied, the ticket moves to *In progress* automatically. I can also add an internal note that the customer doesn't see. Finally I mark it as resolved.
>
> The backend is a REST API. This is the Swagger documentation. It has endpoints to create, read, update and delete tickets, plus statistics and comments. There are also `/health` and `/ready` endpoints for Kubernetes probes, and a `/metrics` endpoint for Prometheus.

---

## Part 4: Testing and code quality (≈ 45 s)

**On screen:** terminal running `ruff` and `pytest`.

**Say:**
> For quality I use two tools.
>
> **Ruff** is a fast Python linter that checks the code style and catches common mistakes.
>
> **Pytest** runs 19 automated tests covering the ticket API: creating, listing, filtering, updating and deleting tickets, comments, statistics, and the health endpoints.
>
> The tests don't touch the real database. The `conftest.py` file creates a fresh in-memory SQLite database for every test, so tests are fast and isolated. All 19 pass.

---

## Part 5: Docker (≈ 45 s)

**On screen:** terminal with the Dockerfiles, `docker compose ps`, and `id` inside the containers.

**Say:**
> Both services are containerized.
>
> The backend Dockerfile has two stages: one installs the dependencies, and the final image only contains what's needed to run. The frontend Dockerfile is also multi-stage: **Node** builds the React app, and a small **Nginx** image serves it.
>
> For security, both containers run as **non-root users**: the backend as user 10001 and the frontend as user 101.
>
> With **Docker Compose**, one command (`docker compose up --build`) starts all three services, the frontend, backend and Postgres, with health checks. All three are healthy.

---

## Part 6: CI/CD: a live change (≈ 2 min)

**On screen:** I change the sidebar text in the code, commit, push, and the GitHub Actions pipeline runs.

**Say:**
> Now the most important part: the CI/CD pipeline. I'll make a real change and follow it all the way to production.
>
> In the sidebar component I change the subtitle text. Then I commit the change with a clear message and push it to the `main` branch.
>
> The push starts the GitHub Actions workflow. It has three jobs.
>
> **Job one, Test:** it runs Ruff, the 19 pytest tests, the frontend build and `helm lint`. If any test fails, the pipeline stops here and nothing is deployed.
>
> **Job two, Build, scan and push:** it builds both Docker images, scans them with Trivy, and pushes them to the GitHub Container Registry. The images are tagged with the **Git commit SHA**, not `latest`, so every deployment can be traced back to an exact commit.
>
> **Job three, Deploy:** it signs in to AWS using **OpenID Connect**, so there are no AWS keys stored in GitHub at all, and runs `helm upgrade` on the EKS cluster.
>
> All three jobs are green.

---

## Part 7: Security scanning with Trivy (≈ 30 s)

**On screen:** the Trivy step in the pipeline and the GHCR package page.

**Say:**
> Trivy is the DevSecOps part. It scans every image for known vulnerabilities, or CVEs. The pipeline is set to **fail on any HIGH or CRITICAL** vulnerability that has a fix available.
>
> My images have a clean result. I chose small, up-to-date base images and removed `pip` from the final backend image, so there's less software that could contain a vulnerability.
>
> Here in the GitHub Container Registry you can see the images, each tagged with its commit SHA.

---

## Part 8: Terraform on AWS (≈ 75 s)

**On screen:** the Terraform code, `terraform plan`, then the AWS Console (VPC, subnets, EKS cluster, node group, EC2 nodes).

**Say:**
> The AWS infrastructure is written as code with **Terraform**. Nothing was created by clicking in the console.
>
> It creates a **VPC** in the Mumbai region with **two public and two private subnets** across two availability zones, plus a NAT gateway. It then creates an **EKS cluster**, Kubernetes 1.34, with a managed **node group** of two nodes, and add-ons like the EBS storage driver and metrics-server. It also creates the IAM role that GitHub Actions uses through OpenID Connect.
>
> `terraform plan` shows exactly what will be created. Here in the AWS Console are the VPC with its subnets, the EKS cluster in *Active* state, the node group, and the two EC2 worker nodes.
>
> One real problem I hit: my AWS account is on the **Free plan**, which only allows free-tier instance types. My first choice, `t3.medium`, was rejected, so I switched to `m7i-flex.large`, which is free-tier eligible and has more memory.

---

## Part 9: Kubernetes and Helm (≈ 75 s)

**On screen:** terminal with `kubectl` and `helm`, then the browser refreshed to show the change from Part 6.

**Say:**
> The application runs on Kubernetes, packaged as a **Helm chart**.
>
> `kubectl get pods` shows two backend pods, two frontend pods and the Postgres pod, all *Running*. The backend and frontend have **ClusterIP services**. The **Ingress** sends `/api` to the backend and everything else to the frontend.
>
> Postgres runs as a StatefulSet with a 5 GB persistent volume on AWS EBS, so the data survives pod restarts.
>
> `helm history` shows every release. The latest one was deployed by the pipeline, so if a release breaks, I can roll back with one command.
>
> Now I refresh the browser, and the sidebar shows the text I changed a few minutes ago. That is the complete flow: **commit, pipeline, deploy, live**.

---

## Part 10: Autoscaling and monitoring (≈ 90 s)

**On screen:** terminal with a load test and the HPA scaling, then Prometheus targets and the Grafana dashboard.

**Say:**
> The backend has a **Horizontal Pod Autoscaler**. It keeps CPU usage around 60 percent, with between 2 and 6 pods.
>
> I start a load test that sends many requests. As CPU rises, the autoscaler adds pods, and we can watch the replica count go up. When the load stops, it scales back down to 2.
>
> For monitoring, the backend exposes a `/metrics` endpoint in Prometheus format. **Prometheus** finds it automatically through a ServiceMonitor. On the targets page both backend pods are *UP*.
>
> **Grafana** shows the "HelpDesk API" dashboard: request rate, the 5xx error ratio, latency percentiles, pods up, and CPU per pod. The dashboard is installed automatically by the Helm chart.

---

## Part 11: Challenges and what I learned (≈ 60 s)

**On screen:** challenges slide.

**Say:**
> A few real problems I solved along the way.
>
> **One:** my first AWS account never activated. The cause was a failed verification, so I created a new account and verified it properly.
>
> **Two:** the Free plan blocked `t3.medium` instances and load balancers at first. I moved to a free-tier instance type, and AWS later enabled load balancers.
>
> **Three:** the CI deploy failed on authentication. GitHub sends its OIDC identity in a newer "immutable" format, and the AWS role didn't trust it. I fixed the trust policy in Terraform.
>
> **Four:** after that, Helm couldn't manage the Prometheus ServiceMonitor, because the CI role's Kubernetes permissions didn't cover it. I added a small RBAC Role for just that resource. That kept the principle of **least privilege**: CI can only touch the `helpdesk` namespace.
>
> The main lesson: read the actual error message, find the real cause, and fix it in code, not by hand.

---

## Part 12: Cleanup and thank you (≈ 30 s)

**On screen:** closing slide.

**Say:**
> Finally, cost. EKS costs money every hour, so after the evaluation I'll uninstall the Helm releases and run `terraform destroy`, which removes every AWS resource that Terraform created.
>
> All the code, documentation and evidence screenshots are in my public GitHub repository, `devops-heros`, in the `session21-python` folder.
>
> Thank you for watching.
