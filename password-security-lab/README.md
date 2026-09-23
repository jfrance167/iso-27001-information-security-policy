# Password Security Lab

A safe, local implementation of the Science Buddies project "Password
Security: How Easily Can Your Password Be Hacked?" It calculates exponential
password search spaces and compares four guessing strategies against synthetic
lab-only password verifiers:

1. fixed-length numeric brute force;
2. variable-length alphanumeric brute force;
3. dictionary guesses with common case variations; and
4. pairs of dictionary words joined by separators.

The implementation was written from scratch for this repository. It follows
the experiment's learning objectives without copying its downloadable code or
legacy password hashes.

## Security Notice

This project is educational and not a production password-auditing tool. It has
no networking, account login, remote targeting, or credential-file support.
Use only the bundled synthetic examples or test values you created and are
authorized to analyze. Never enter a real password into the program, source
code, shell history, screenshots, or repository.

## Requirements

- Python 3.10 or newer
- No runtime dependencies outside the Python standard library

## Run the experiment

From this directory, calculate the complete 1-8 character tables for numeric,
uppercase alphabetic, and alphanumeric search spaces:

```powershell
python password_lab.py table
```

Save the table as CSV:

```powershell
python password_lab.py table --output reports/search-space.csv
```

Estimate a specific worst-case search. This example evaluates 12 characters
from a 62-character alphabet at one million guesses per second:

```powershell
python password_lab.py estimate 62 12 --guesses-per-second 1000000
```

Run the four bounded attacks against bundled synthetic examples:

```powershell
python password_lab.py demo
python password_lab.py demo --json
```

The demo intentionally uses a small PBKDF2 work factor so it finishes quickly
in a classroom. That setting is not suitable for production password storage.

## Run the tests

```powershell
python -m unittest discover -s tests -v
```

The 15 tests validate the published search-space value `62^8`, leading zeros,
alphanumeric enumeration, dictionary variants, combined words, guess limits,
PBKDF2 verification, calculations, and command-line output.

## Results summary

Five runs with a 2,000-iteration synthetic verifier produced these averages on
the lab computer:

| Method | Synthetic value | Guesses | Mean time |
|---|---|---:|---:|
| Three-digit numeric | `042` | 43 | 0.037428 s |
| Alphanumeric through length 2 | `A7` | 2,302 | 2.006844 s |
| Dictionary with variations | `Sunshine` | 6 | 0.005894 s |
| Two words plus separator | `red+planet` | 909 | 0.809988 s |

These times compare algorithms under one controlled implementation; they are
not estimates of how long a production password would withstand attack. The
complete hypothesis, data tables, analysis, modern guidance, and conclusion
are in [LAB_REPORT.md](LAB_REPORT.md).

## Design notes

- The guess generator is separate from verification, making each method easy
  to test and compare.
- Every search defaults to a maximum of one million guesses.
- Synthetic records use salted PBKDF2-HMAC-SHA-256 instead of the source
  project's obsolete MD5 examples.
- Verification uses constant-time digest comparison.
- Timing uses a monotonic high-resolution clock.
- Search-space estimates report the worst case. A uniformly random target
  would take about half as many guesses on average.

## Modern password guidance

Search-space arithmetic is useful for understanding exponential growth, but
real password security also depends on selection bias, breached-password
blocklists, rate limiting, multi-factor authentication, and secure verifier
storage. Current [NIST SP 800-63B](https://pages.nist.gov/800-63-4/sp800-63b.html)
requires at least 15 characters for single-factor passwords, discourages
composition rules, and requires salted, costed password hashing plus online
rate limiting.

## Reference

Science Buddies Staff. [Password Security: How Easily Can Your Password Be
Hacked?](https://www.sciencebuddies.org/science-fair-projects/project-ideas/CompSci_p046/computer-science/password-security-how-easily-can-your-password-be-hacked),
last edited April 1, 2021; accessed September 22, 2026.
