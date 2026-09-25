# Password Reuse Survey Lab

This is a privacy-safe adaptation of Science Buddies' **Do People Use Different
Passwords for Different Accounts?** project. It measures password reuse with
opaque group labels and normalized metrics without collecting password values.

The completed experiment uses 120 synthetic respondents. No human responses,
usernames, services, credentials, or real passwords are present. Every output
row is labeled `SYNTHETIC SURVEY DATA - NO HUMAN PASSWORDS OR RESPONSES`.

## Run the completed experiment

From this directory:

```powershell
python password_reuse_lab.py experiment
python -m unittest discover -s tests -v
```

The deterministic run writes:

- `reports/synthetic_responses.csv` — 1,609 synthetic account assignments
- `reports/respondent_metrics.csv` — one privacy-safe row per respondent
- `reports/summary.json` — overall, histogram, and category-level results

## Optional human-subject follow-up

The included `survey_template.csv` asks only for an arbitrary reuse label such
as `A`, `B`, or `C`. A participant uses the same label when two accounts share a
password. **They must never enter the password itself, a username, an account
provider, or identifying information.**

Do not collect human data until a teacher, fair coordinator, or institutional
review process has approved the protocol. Review `HUMAN_SUBJECTS.md` first.

## Files

- `password_reuse_lab.py` — bounded synthetic-data generator and analyzer
- `tests/test_password_reuse_lab.py` — privacy, metric, output, and CLI tests
- `reports/` — reproducible synthetic data and aggregated findings
- `survey_template.csv` — blank, provider-neutral optional questionnaire
- `HUMAN_SUBJECTS.md` — consent, minimization, and handling checklist
- `LAB_REPORT.md` — full scientific-method report
- `SECURITY.md` — responsible-use boundary

## Sources

- [Science Buddies: Do People Use Different Passwords for Different Accounts?](https://www.sciencebuddies.org/science-fair-projects/project-ideas/HumBeh_p057/human-behavior/do-people-use-different-passwords-for-different-accounts)
- [NIST SP 800-63B: Authentication and Authenticator Management](https://pages.nist.gov/800-63-4/sp800-63b.html)
