variable "aws_region" {
  description = "AWS region used by this educational lab."
  type        = string
  default     = "us-east-1"
}

variable "bucket_name" {
  description = "Globally unique name for the intentionally public demo bucket."
  type        = string
  default     = "replace-me-insecure-iac-demo-bucket"
}
