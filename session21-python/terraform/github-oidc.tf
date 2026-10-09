################################################################################
# Lets GitHub Actions deploy with short-lived OIDC credentials, so no AWS keys
# are ever stored in GitHub secrets. Enabled when var.github_repository is set.
################################################################################

locals {
  github_deploy_enabled = var.github_repository != ""
  github_oidc_url       = "token.actions.githubusercontent.com"
}

resource "aws_iam_openid_connect_provider" "github" {
  count = local.github_deploy_enabled && var.create_github_oidc_provider ? 1 : 0

  url            = "https://${local.github_oidc_url}"
  client_id_list = ["sts.amazonaws.com"]
}

data "aws_iam_openid_connect_provider" "github" {
  count = local.github_deploy_enabled && !var.create_github_oidc_provider ? 1 : 0
  url   = "https://${local.github_oidc_url}"
}

data "aws_iam_policy_document" "github_trust" {
  count = local.github_deploy_enabled ? 1 : 0

  statement {
    actions = ["sts:AssumeRoleWithWebIdentity"]
    principals {
      type = "Federated"
      identifiers = [
        var.create_github_oidc_provider ? aws_iam_openid_connect_provider.github[0].arn : data.aws_iam_openid_connect_provider.github[0].arn
      ]
    }
    condition {
      test     = "StringEquals"
      variable = "${local.github_oidc_url}:aud"
      values   = ["sts.amazonaws.com"]
    }
    # Only workflow runs on the main branch of this one repository may assume the role.
    condition {
      test     = "StringEquals"
      variable = "${local.github_oidc_url}:sub"
      values   = ["repo:${var.github_repository}:ref:refs/heads/main"]
    }
  }
}

resource "aws_iam_role" "github_deploy" {
  count = local.github_deploy_enabled ? 1 : 0

  name               = "${local.name}-github-deploy"
  assume_role_policy = data.aws_iam_policy_document.github_trust[0].json
}

data "aws_iam_policy_document" "github_deploy" {
  count = local.github_deploy_enabled ? 1 : 0

  statement {
    actions   = ["eks:DescribeCluster"]
    resources = [module.eks.cluster_arn]
  }
}

resource "aws_iam_role_policy" "github_deploy" {
  count = local.github_deploy_enabled ? 1 : 0

  name   = "describe-eks-cluster"
  role   = aws_iam_role.github_deploy[0].id
  policy = data.aws_iam_policy_document.github_deploy[0].json
}
