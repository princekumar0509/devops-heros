# Terraform — AWS VPC + EKS for HelpDesk

Provisions everything HelpDesk needs on AWS, as code:

```text
AWS (ap-south-1)
└── VPC 10.20.0.0/16
    ├── public subnets  10.20.0.0/24, 10.20.1.0/24   (internet gateway; tagged for internet-facing load balancers)
    ├── private subnets 10.20.10.0/24, 10.20.11.0/24 (worker nodes; egress via a single NAT gateway)
    └── EKS cluster helpdesk-dev-eks
        ├── managed node group "main": 2× m7i-flex.large (min 2 / max 4), AL2023
        ├── add-ons: vpc-cni, coredns, kube-proxy, eks-pod-identity-agent,
        │            metrics-server (HPA), aws-ebs-csi-driver (Postgres volume, via Pod Identity)
        └── access entry for the GitHub Actions deploy role (namespace "helpdesk" only)
IAM
├── helpdesk-dev-ebs-csi           role for the EBS CSI driver
└── helpdesk-dev-github-deploy     assumable only by GitHub OIDC tokens from <repo> on refs/heads/main
```

| File | Purpose |
|---|---|
| `versions.tf` | Terraform/provider versions, AWS provider with default tags, optional S3 backend |
| `variables.tf` | Every tunable input, with defaults |
| `main.tf` | VPC module, EKS module, EBS CSI IAM role |
| `github-oidc.tf` | Keyless CI deploys: OIDC provider + deploy role |
| `outputs.tf` | Cluster name, kubectl command, deploy role ARN |
| `terraform.tfvars.example` | Copy to `terraform.tfvars` (git-ignored) |

## Prerequisites

- Terraform ≥ 1.7, AWS CLI v2, kubectl, Helm
- AWS credentials configured **locally** (`aws configure` or `aws sso login`). Never commit them. `*.tfvars`, `*.tfstate` and `.terraform/` are all git-ignored.

## Usage

```bash
cp terraform.tfvars.example terraform.tfvars    # edit github_repository
terraform init
terraform fmt -check && terraform validate
terraform plan -out tfplan                      # screenshot for M7
terraform apply tfplan                          # ~15–20 minutes
$(terraform output -raw configure_kubectl)      # aws eks update-kubeconfig ...
kubectl get nodes
terraform output github_deploy_role_arn         # → GitHub variable AWS_DEPLOY_ROLE_ARN
terraform output cluster_name                   # → GitHub variable EKS_CLUSTER_NAME
```

If your AWS account already has a GitHub OIDC provider (`aws iam list-open-id-connect-providers`), set `create_github_oidc_provider = false`.

`cluster_version` defaults to `1.34`. Check *EKS → Kubernetes versions* in the AWS docs and pick a version that is still in **standard** support. Older versions are billed at the extended-support rate.

## Destroy (do this after grading)

Delete the Kubernetes objects that created AWS resources first. Otherwise the load balancer and EBS volume are left behind, and they block VPC deletion:

```bash
helm uninstall helpdesk -n helpdesk
helm uninstall ingress-nginx -n ingress-nginx
helm uninstall kube-prometheus-stack -n monitoring
kubectl delete pvc --all -n helpdesk
terraform destroy                                # screenshot for M7
```

> **Cost warning:** the EKS control plane, NAT gateway, two m7i-flex.large nodes and the load balancer are billed hourly. Destroy everything when you are done.
