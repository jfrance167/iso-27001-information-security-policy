# Security Policy

## Supported version

Only the latest commit on `main` is maintained.

## Intended use

This repository is educational and not production-ready governance, legal
advice, or a certification guarantee. The Terraform under
`cloud-iac-security-scanning/terraform/` is intentionally vulnerable and must
not be deployed. Organizations must remediate the lab and tailor and approve
the policy template for their own scope, risks, obligations, and control
environment.

## Reporting a security issue

Use GitHub private vulnerability reporting for leaked real data, unsafe
repository automation, or another unintended issue. Do not disclose sensitive
organizational information in a public issue. Rotate exposed credentials before
repository cleanup.

## Maintainer checks

Before publishing, run `pre-commit run --all-files`, GitHub secret scanning, and
the repository policy workflow. Review document metadata and placeholders.
