# Security and Responsible Use

This educational project analyzes password-reuse patterns without handling
credentials. It is not a password collector, credential tester, or account
access tool.

## Controls

- The completed dataset is deterministic and wholly synthetic.
- No field can accept a password, hash, username, provider, or account URL.
- Reuse relationships use respondent-local opaque labels such as `G01`.
- Synthetic identifiers cannot be mapped to people.
- The program performs no network, browser, authentication, or account access.
- Respondent counts are bounded to control resource use.

## Never collect

- actual or partial passwords, passphrases, PINs, recovery codes, or hashes;
- usernames, email addresses, account numbers, or service/provider names;
- security-question answers or identifying demographic combinations;
- authentication screenshots, breach data, or password-manager exports.

If an actual password is submitted accidentally, stop collection, do not copy
or analyze it, delete it using the approved research-data process, and notify
the supervising teacher or reviewer without repeating the secret.

Report suspected repository vulnerabilities through the root security policy.
