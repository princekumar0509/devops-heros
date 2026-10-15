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
    # Only the deploy job of this one repository may assume the role. That job uses
    # `environment: production`, so GitHub sets sub to the environment, not the branch;
    # the job itself only runs on main. Repos on GitHub's immutable subject format put
    # owner/repo IDs in the prefix instead, so accept that form too when configured.
    condition {
      test     = "StringEquals"
      variable = "${local.github_oidc_url}:sub"
      values = compact([
        "repo:${var.github_repository}:environment:production",
        var.github_oidc_sub_prefix != "" ? "${var.github_oidc_sub_prefix}:environment:production" : "",
      ])
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
