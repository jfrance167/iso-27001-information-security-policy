# Hardened remediation target for the IaC security-scanning lab.

resource "aws_s3_bucket" "public_demo" {
  bucket = var.bucket_name

  tags = {
    Name        = "secure-iac-demo"
    Environment = "training-only"
  }
}

resource "aws_s3_bucket_ownership_controls" "public_demo" {
  bucket = aws_s3_bucket.public_demo.id

  rule {
    object_ownership = "BucketOwnerEnforced"
  }
}

resource "aws_s3_bucket_public_access_block" "public_demo" {
  bucket = aws_s3_bucket.public_demo.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

resource "aws_kms_key" "s3" {
  description             = "Customer-managed key for the IaC demo S3 bucket"
  deletion_window_in_days = 30
  enable_key_rotation     = true

  tags = {
    Name        = "secure-iac-demo-s3"
    Environment = "training-only"
  }
}

resource "aws_kms_alias" "s3" {
  name          = "alias/secure-iac-demo-s3"
  target_key_id = aws_kms_key.s3.key_id
}

resource "aws_s3_bucket_server_side_encryption_configuration" "public_demo" {
  bucket = aws_s3_bucket.public_demo.id

  rule {
    apply_server_side_encryption_by_default {
      kms_master_key_id = aws_kms_key.s3.arn
      sse_algorithm     = "aws:kms"
    }

    bucket_key_enabled = true
  }
}

resource "aws_security_group" "admin_access" {
  name        = "restricted-admin-access"
  description = "Training-only security group restricted to a trusted network"

  ingress {
    description = "SSH from trusted network"
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = [var.trusted_admin_cidr]
  }

  ingress {
    description = "RDP from trusted network"
    from_port   = 3389
    to_port     = 3389
    protocol    = "tcp"
    cidr_blocks = [var.trusted_admin_cidr]
  }

  tags = {
    Name        = "restricted-admin-access"
    Environment = "training-only"
  }
}
