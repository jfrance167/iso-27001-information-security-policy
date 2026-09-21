# Cloud IaC Security Scanning Lab

[![Terraform IaC security scan](https://github.com/jfrance167/iso-27001-information-security-policy/actions/workflows/iac-security-scan.yml/badge.svg)](https://github.com/jfrance167/iso-27001-information-security-policy/actions/workflows/iac-security-scan.yml)

This portfolio lab demonstrates a shift-left security control for AWS infrastructure as code. The Terraform is intentionally misconfigured, and Trivy blocks it before any deployment step can run.

> [!CAUTION]
> The files under `terraform/` are deliberately vulnerable. Do not run `terraform apply`. No AWS credentials are needed to scan this lab.

## What is intentionally wrong

| Resource | Misconfiguration | Risk |
| --- | --- | --- |
| S3 bucket | Public ACL and all four public-access safeguards disabled | Anonymous data exposure |
| S3 bucket policy | Wildcard principal can read every object | Public data disclosure |
| S3 bucket | Encryption, access logging, and versioning omitted | Reduced confidentiality, monitoring, and recovery |
| Security group | SSH (`22`) open to `0.0.0.0/0` | Internet-wide administrative access |
| Security group | RDP (`3389`) open to `0.0.0.0/0` | Internet-wide administrative access |
| Security group | Unrestricted outbound traffic | Weak egress control |

## CI security gate

The repository workflow at `.github/workflows/iac-security-scan.yml` runs on pushes and pull requests that change this lab's Terraform or scanner configuration. It uses Trivy's IaC scanner and exits with code `1` when a `HIGH` or `CRITICAL` misconfiguration is found.

Because the sample is intentionally vulnerable, the initial workflow run is expected to fail. That red build is the evidence that the preventive control works. Remediating the findings should make the same gate pass.

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

Expected result: Trivy 0.74 reports nine blocking findings (eight `HIGH` and one `CRITICAL`), then returns exit code `1`:

| Trivy check | Severity | Observed finding |
| --- | --- | --- |
| `AWS-0086`, `AWS-0087`, `AWS-0091`, `AWS-0093` | High | S3 public-access protections disabled |
| `AWS-0092` | High | Public-read bucket ACL |
| `AWS-0107` (twice) | High | SSH and RDP exposed to the internet |
| `AWS-0104` | Critical | Unrestricted security-group egress |
| `AWS-0132` | High | No customer-managed encryption key |

## Remediation exercise

To turn the failing gate green:

1. Remove the public ACL and wildcard bucket policy.
2. Set every S3 public-access-block option to `true`.
3. Enable bucket encryption, logging, and versioning.
4. Restrict SSH/RDP ingress to a documented trusted CIDR, or remove those rules.
5. Restrict egress to only required destinations and ports.
6. Run the local scan again and open a pull request with the clean result.

## Repository layout

```text
cloud-iac-security-scanning/
├── terraform/
│   ├── main.tf
│   ├── variables.tf
│   └── versions.tf
├── trivy.yaml
├── scan.ps1
├── scan.sh
└── README.md
```
