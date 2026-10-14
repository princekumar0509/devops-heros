locals {
  name = "${var.project}-${var.environment}"
  azs  = slice(var.availability_zones, 0, var.az_count)

  tags = {
    Project     = var.project
    Environment = var.environment
    ManagedBy   = "terraform"
  }
}

################################################################################
# Network: VPC with public + private subnets across AZs, one NAT gateway
################################################################################

module "vpc" {
  source  = "terraform-aws-modules/vpc/aws"
  version = "~> 6.7"

  name = "${local.name}-vpc"
  cidr = var.vpc_cidr
  azs  = local.azs

  # /24 subnets: public 10.20.0-1.0, private 10.20.10-11.0
  public_subnets  = [for i, _ in local.azs : cidrsubnet(var.vpc_cidr, 8, i)]
  private_subnets = [for i, _ in local.azs : cidrsubnet(var.vpc_cidr, 8, i + 10)]

  enable_nat_gateway   = true
  single_nat_gateway   = true # one NAT keeps classroom costs down; use one per AZ in production
  enable_dns_hostnames = true
  enable_dns_support   = true

  # Tags the AWS load balancer integration uses to pick subnets for Service type=LoadBalancer.
  public_subnet_tags = {
    "kubernetes.io/role/elb" = 1
  }
  private_subnet_tags = {
    "kubernetes.io/role/internal-elb" = 1
  }
}

################################################################################
# EKS cluster with one managed node group in the private subnets
################################################################################

module "eks" {
  source  = "terraform-aws-modules/eks/aws"
  version = "~> 21.29"

  name               = "${local.name}-eks"
  kubernetes_version = var.cluster_version

  vpc_id     = module.vpc.vpc_id
  subnet_ids = module.vpc.private_subnets

  endpoint_public_access                   = true
  enable_cluster_creator_admin_permissions = true

  addons = {
    coredns                = {}
    kube-proxy             = {}
    vpc-cni                = { before_compute = true }
    eks-pod-identity-agent = { before_compute = true }
    metrics-server         = {} # required by the HorizontalPodAutoscaler
    aws-ebs-csi-driver = {      # required for the PostgreSQL PersistentVolumeClaim
      pod_identity_association = [{
        role_arn        = aws_iam_role.ebs_csi.arn
        service_account = "ebs-csi-controller-sa"
      }]
    }
  }

  eks_managed_node_groups = {
    main = {
      instance_types = var.node_instance_types
      ami_type       = "AL2023_x86_64_STANDARD"
      # Let EKS choose the current AMI release instead of looking it up in SSM at plan time.
      use_latest_ami_release_version = false
      min_size                       = var.node_min_size
      desired_size                   = var.node_desired_size
      max_size                       = var.node_max_size
      disk_size                      = 30
    }
  }

  access_entries = local.github_deploy_enabled ? {
    github_actions = {
      principal_arn = aws_iam_role.github_deploy[0].arn
      policy_associations = {
        # Scoped to the app namespace only: CI can deploy HelpDesk but cannot touch the rest of the cluster.
        helpdesk = {
          policy_arn   = "arn:aws:eks::aws:cluster-access-policy/AmazonEKSAdminPolicy"
          access_scope = { type = "namespace", namespaces = ["helpdesk"] }
        }
      }
    }
  } : {}
}

################################################################################
# IAM role for the EBS CSI driver (EKS Pod Identity)
################################################################################

data "aws_iam_policy_document" "pod_identity_trust" {
  statement {
    actions = ["sts:AssumeRole", "sts:TagSession"]
    principals {
      type        = "Service"
      identifiers = ["pods.eks.amazonaws.com"]
    }
  }
}

resource "aws_iam_role" "ebs_csi" {
  name               = "${local.name}-ebs-csi"
  assume_role_policy = data.aws_iam_policy_document.pod_identity_trust.json
}

resource "aws_iam_role_policy_attachment" "ebs_csi" {
  role       = aws_iam_role.ebs_csi.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AmazonEBSCSIDriverPolicy"
}
