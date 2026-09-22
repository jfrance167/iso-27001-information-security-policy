# Cloud IaC Security Scanning Lab

[![Terraform IaC security scan](https://github.com/jfrance167/iso-27001-information-security-policy/actions/workflows/iac-security-scan.yml/badge.svg)](https://github.com/jfrance167/iso-27001-information-security-policy/actions/workflows/iac-security-scan.yml)

This portfolio lab demonstrates a complete shift-left remediation cycle for AWS infrastructure as code. Trivy initially blocked nine HIGH/CRITICAL findings; the Terraform was then hardened until the same CI gate passed with zero blocking findings.

> [!NOTE]
> This is an educational configuration, not production infrastructure. Review names, networking, logging, recovery, and organizational requirements before deployment. No AWS credentials are needed to scan the lab.

## Controls demonstrated

| Resource | Remediation | Security outcome |
| --- | --- | --- |
| S3 bucket | Bucket-owner-enforced ownership and all public-access blocks enabled | ACLs and public policies cannot expose data |
| S3 bucket | SSE-KMS with a rotating customer-managed key | Data is encrypted under a controlled key |
| Security group | SSH and RDP restricted to a validated trusted CIDR | Administrative ports are not internet-accessible |
| Security group | Default unrestricted egress removed | No implicit outbound access |

## CI security gate

The repository workflow at `.github/workflows/iac-security-scan.yml` runs on pushes and pull requests that change this lab's Terraform or scanner configuration. Its action inputs explicitly select `HIGH,CRITICAL`, table output, and exit code `1` for blocking findings. The referenced `trivy.yaml` contains the same policy for local runs.

The current hardened configuration is expected to pass. Reintroducing one of the documented weaknesses should make the same gate fail before deployment.

The workflow is read-only, uses no cloud credentials, and has no deployment job.

## Run locally

Prerequisite: Docker Desktop or a local Trivy 0.74 installation.

PowerShell:

```powershell
./cloud-iac-security-scanning/scan.ps1
```

Bash:

```bash
bash ./cloud-iac-security-scanning/scan.sh
```

Or with an installed Trivy binary:

```bash
trivy config --config cloud-iac-security-scanning/trivy.yaml cloud-iac-security-scanning/terraform
```

Equivalent explicit command:

```bash
trivy config \
  --config cloud-iac-security-scanning/trivy.yaml \
  --severity HIGH,CRITICAL \
  --format table \
  cloud-iac-security-scanning/terraform
```

Expected result: zero HIGH/CRITICAL misconfigurations and exit code `0`.

## Remediation evidence

| Stage | HIGH | CRITICAL | Result |
| --- | ---: | ---: | --- |
| Initial vulnerable template | 8 | 1 | Blocked |
| S3 public-access remediation | 3 | 1 | Blocked |
| Network and KMS remediation | 0 | 0 | Passed |

The S3 ACL/public-access remediation removed `AWS-0086`, `AWS-0087`, `AWS-0091`, `AWS-0092`, and `AWS-0093` without suppressing any checks. The bucket now uses `BucketOwnerEnforced`, has no ACL or public bucket policy, and enables all four S3 public-access-block settings.

The final remediation removed `AWS-0104`, both `AWS-0107` findings, and `AWS-0132` by removing unrestricted egress, restricting administrative ingress, and enabling customer-managed SSE-KMS encryption with key rotation.

## Repository layout

```text
cloud-iac-security-scanning/
├── terraform/
│   ├── .terraform.lock.hcl
│   ├── main.tf
│   ├── variables.tf
│   └── versions.tf
├── trivy.yaml
├── scan.ps1
├── scan.sh
└── README.md
```
