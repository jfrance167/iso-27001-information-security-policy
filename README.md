# Cybersecurity Portfolio

This repository contains hands-on defensive security projects and a generic information security policy template aligned with ISO/IEC 27001:2022 and the NIST Cybersecurity Framework 2.0.

## Featured lab

- [Cloud IaC Security Scanning](cloud-iac-security-scanning/README.md) — intentionally vulnerable AWS Terraform protected by a Trivy security gate in GitHub Actions
- [Caesar Cipher Cryptanalysis Lab](caesar-cipher-cryptanalysis-lab/README.md) — file-based encryption, exhaustive key search, frequency analysis, tests, and a complete experimental report

## Policy template

The policy template covers policy purpose and scope, information security objectives, management commitment, risk management, supporting policies, legal and contractual compliance, roles and responsibilities, awareness and training, document control, monitoring, enforcement, and exceptions.

The document is anonymized for portfolio use. Replace `[Organization Name]` and adapt the policy to the organization’s actual legal, regulatory, contractual, and risk requirements before adoption.

## Security Notice

This repository is educational and not production-ready. The cloud IaC lab is
explicitly and intentionally vulnerable so scanners can detect it; it must not
be deployed. The repository contains no real credentials. An organization must
tailor, approve, implement, and periodically review the policy template against
its own scope, risks, obligations, and control environment before use.

Do not deploy the vulnerable infrastructure or adopt the policy as a production
policy without appropriate remediation and review.

## File

- `Information Security Policy.docx` — editable Word policy template
