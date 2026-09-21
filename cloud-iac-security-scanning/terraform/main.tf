# WARNING: This file is intentionally vulnerable and must not be deployed.

resource "aws_s3_bucket" "public_demo" {
  bucket = var.bucket_name

  tags = {
    Name        = "intentionally-vulnerable-demo"
    Environment = "training-only"
  }
}

resource "aws_s3_bucket_ownership_controls" "public_demo" {
  bucket = aws_s3_bucket.public_demo.id

  rule {
    object_ownership = "ObjectWriter"
  }
}

resource "aws_s3_bucket_public_access_block" "public_demo" {
  bucket = aws_s3_bucket.public_demo.id

  # Intentionally unsafe: every S3 public-access safeguard is disabled.
  block_public_acls       = false
  block_public_policy     = false
  ignore_public_acls      = false
  restrict_public_buckets = false
}

resource "aws_s3_bucket_acl" "public_demo" {
  depends_on = [
    aws_s3_bucket_ownership_controls.public_demo,
    aws_s3_bucket_public_access_block.public_demo,
  ]

  bucket = aws_s3_bucket.public_demo.id
  acl    = "public-read"
}

resource "aws_s3_bucket_policy" "public_demo" {
  depends_on = [aws_s3_bucket_public_access_block.public_demo]
  bucket     = aws_s3_bucket.public_demo.id

  # Intentionally unsafe: anonymous users can read every object.
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid       = "AllowAnonymousRead"
        Effect    = "Allow"
        Principal = "*"
        Action    = "s3:GetObject"
        Resource  = "${aws_s3_bucket.public_demo.arn}/*"
      },
    ]
  })
}

resource "aws_security_group" "open_admin" {
  name        = "intentionally-open-admin-access"
  description = "Training-only security group with unrestricted admin ports"

  # Intentionally unsafe: SSH is exposed to the entire internet.
  ingress {
    description = "Unrestricted SSH"
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  # Intentionally unsafe: RDP is exposed to the entire internet.
  ingress {
    description = "Unrestricted RDP"
    from_port   = 3389
    to_port     = 3389
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  egress {
    description = "Unrestricted outbound traffic"
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name        = "intentionally-vulnerable-demo"
    Environment = "training-only"
  }
}
