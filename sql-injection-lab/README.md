# SQL Injection Prevention Lab

This lab is a safe, local modernization of Science Buddies' **Preventing SQL
Injection Attacks** project. The original AWS-based procedure is deprecated, so
this version uses an in-memory SQLite database, fictional accounts, a bounded
legacy-behavior model, and a real parameterized-query implementation.

The lab measures whether controlled injection scenarios would cause
unauthorized authentication or data exposure in a modeled string-interpolation
design, then runs the same inputs as literal values through parameterized SQL.

## Safety boundary

- No network listener, cloud account, remote system, or real website is used.
- Every account and email address is synthetic; `.invalid` domains cannot
  receive mail.
- Dynamically constructed SQL is never executed.
- Only six fixed classroom scenarios are modeled.
- The real SQLite path uses parameterized queries exclusively.
- Raw synthetic passwords and payload text are omitted from result files.

Do not use the example payloads against systems you do not own or lack explicit
permission to test.

## Run the completed experiment

```powershell
cd sql-injection-lab
python sql_injection_lab.py experiment
```

This writes 600 reproducible trials to `reports/results.csv` and six aggregated
scenario records to `reports/summary.json`.

Run one redacted demonstration:

```powershell
python sql_injection_lab.py demo --scenario username_tautology
```

Run the tests:

```powershell
python -m unittest discover -s tests -v
```

## Files

- `sql_injection_lab.py` — experiment, SQLite implementation, model, and CLI
- `tests/test_sql_injection_lab.py` — automated behavior and safety tests
- `reports/results.csv` — raw redacted trial results
- `reports/summary.json` — aggregated scenario results
- `LAB_REPORT.md` — full scientific and engineering write-up
- `SECURITY.md` — responsible-use guidance

## Source project

- [Science Buddies: Preventing SQL Injection Attacks](https://www.sciencebuddies.org/science-fair-projects/project-ideas/Cyber_p008/cybersecurity/sql-injection)

Science Buddies explicitly notes that its original AWS dependency has been
deprecated. This lab preserves the learning objective without relying on that
obsolete environment.
