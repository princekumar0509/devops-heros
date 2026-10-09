terraform {
  required_version = ">= 1.7.0"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 6.0"
    }
  }

  # Optional: keep state in S3 so it is not lost with your laptop. Create the bucket first, then uncomment.
  # backend "s3" {
  #   bucket       = "YOUR-tfstate-bucket"
  #   key          = "helpdesk/eks/terraform.tfstate"
  #   region       = "ap-south-1"
  #   use_lockfile = true
  # }
}

provider "aws" {
  region = var.aws_region

  default_tags {
    tags = local.tags
  }
}
