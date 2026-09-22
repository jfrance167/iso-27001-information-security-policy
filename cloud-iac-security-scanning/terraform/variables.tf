variable "aws_region" {
  description = "AWS region used by this educational lab."
  type        = string
  default     = "us-east-1"
}

variable "bucket_name" {
  description = "Globally unique name for the encrypted private demo bucket."
  type        = string
  default     = "replace-me-secure-iac-demo-bucket"
}

variable "trusted_admin_cidr" {
  description = "Trusted private network allowed to use SSH and RDP."
  type        = string
  default     = "10.0.0.0/8"

  validation {
    condition     = can(cidrnetmask(var.trusted_admin_cidr)) && var.trusted_admin_cidr != "0.0.0.0/0"
    error_message = "trusted_admin_cidr must be a valid restricted IPv4 CIDR and cannot be 0.0.0.0/0."
  }
}
