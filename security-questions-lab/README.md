# Security Questions Lab

This lab is a privacy-safe modernization of Science Buddies' **How Secure Are
Your Security Questions?** project. It preserves the original expectation,
discoverability, ranking, and three-question analyses without researching real
people or storing recovery answers.

The completed experiment contains 200 fictional profiles and 2,000 synthetic
observations. Every row says `SYNTHETIC DATA - NO REAL PEOPLE OR RECOVERY
ANSWERS`.

## Run the completed experiment

From this directory:

```powershell
python security_questions_lab.py experiment
python -m unittest discover -s tests -v
```

The deterministic run writes:

- `reports/trials.csv` — 2,000 labeled fictional observations
- `reports/summary.json` — expectation tables, question rankings, and
  three-question portfolio results

## Safety boundary

This project does not perform open-source intelligence gathering, search for
people, collect human-subject data, test recovery workflows, or access accounts.
Do not replace the fictional profiles with real people. See `ETHICS.md` and
`SECURITY.md`.

## Files

- `security_questions_lab.py` — bounded generator, analysis, and CLI
- `tests/test_security_questions_lab.py` — safety, model, analysis, and output tests
- `reports/` — reproducible synthetic experiment results
- `fictional_scenario_template.csv` — blank worksheet for invented scenarios only
- `LAB_REPORT.md` — complete scientific-method write-up
- `ETHICS.md` — privacy-preserving research boundary
- `SECURITY.md` — responsible-use controls

## Sources

- [Science Buddies: How Secure Are Your Security Questions?](https://www.sciencebuddies.org/science-fair-projects/project-ideas/Cyber_p007/cybersecurity/security-questions)
- [NIST SP 800-63B: Authentication and Authenticator Management](https://pages.nist.gov/800-63-4/sp800-63b.html)
