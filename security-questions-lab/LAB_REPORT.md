# How Secure Are Security Questions?

## Abstract

This project examined whether personal-knowledge security questions are
suitable for account recovery. The original Science Buddies procedure compares
volunteers' expectations with personal facts found online. To eliminate the
privacy and human-subject risks of researching real people, this completed
version uses a deterministic simulation with 200 fictional profiles and ten
question types. The run generated 2,000 explicitly labeled observations. In the
model, correct-answer discoverability ranged from 10.0% for favorite food to
76.5% for current employer. For 27.5% of fictional profiles, all three of the
least-secure answers were modeled as correctly discoverable; the equivalent
rate for the three most-secure questions was 0.5%. These figures demonstrate
the analysis and compounding-risk concept but are not measurements of real
people. Current NIST guidance says verifiers should not use knowledge-based
authentication or security questions.

## Research question

How do public discoverability and user expectations affect the modeled security
of personal-knowledge account-recovery questions?

## Background

Security questions assume that an answer is memorable to the account owner but
difficult for anyone else to learn. That assumption is weak when information is
common, guessable, known to acquaintances, or publicly discoverable. A strong
password cannot protect an account if a weaker recovery process bypasses it.

The Science Buddies project proposes ten questions, anonymous volunteers, an
expectation-versus-reality table, ranking by correct answers found, and a test
of the three least- and most-secure questions. It includes important warnings
about consent, impersonation, private accounts, illegally obtained data, and
destroying sensitive research records.

This implementation retains the analytical structure but removes real-person
research entirely. That choice also reflects NIST SP 800-63B Revision 4, which
states that verifiers and credential service providers shall not prompt users
to use knowledge-based authentication or security questions when selecting
passwords.

## Hypothesis

Question types associated with commonly published biographical facts will have
higher modeled correct-answer discoverability than preference or historical
details. Combining three discoverable questions will create a measurable
recovery exposure even when each question is evaluated separately.

## Variables

- **Independent variable:** fictional security-question type.
- **Dependent variables:** information-found rate, correct-answer-found rate,
  unexpected-exposure rate, expectation gap, and all-three-known rate.
- **Controlled variables:** 200 profiles, ten questions per profile, model
  probabilities, seed, analysis definitions, and one simulated attempt.

## Model assumptions

Each question has three illustrative probabilities:

| Question | Public | Expected public | Correct if found |
| --- | ---: | ---: | ---: |
| Current employer | 0.82 | 0.68 | 0.94 |
| High school | 0.72 | 0.52 | 0.90 |
| Birth city | 0.65 | 0.48 | 0.88 |
| Mother's maiden name | 0.46 | 0.22 | 0.84 |
| First pet name | 0.41 | 0.20 | 0.76 |
| Wedding location | 0.36 | 0.28 | 0.84 |
| Street grew up on | 0.30 | 0.16 | 0.78 |
| First car model | 0.27 | 0.18 | 0.71 |
| Favorite sports team | 0.34 | 0.27 | 0.68 |
| Favorite food | 0.20 | 0.13 | 0.52 |

These are teaching assumptions chosen to exercise the method. They are not
survey estimates, measurements, or claims about a population.

## Procedure

1. Define ten fictional question models and their three probabilities.
2. Generate 200 fictional profile IDs without names or identity attributes.
3. For every profile and question, simulate whether the profile expects the
   information to be public and whether information is found.
4. If information is found, simulate whether it supplies the correct fictional
   answer. No answer value is ever generated or stored.
5. For each question, count the four expectation/finding outcomes:
   expected/found, expected/not found, not expected/found, and neither.
6. Calculate expected-online, found-online, correct-answer, unexpected-exposure,
   and expectation-gap rates.
7. Rank questions from highest to lowest correct-answer-found rate.
8. Calculate the percentage of fictional profiles for which all three answers
   are known for the least-secure and most-secure sets.
9. Repeat the seeded run and automated tests to confirm reproducibility.

The completed command was:

```powershell
python security_questions_lab.py experiment --participants 200 --seed 20260925
```

## Results

The run generated 2,000 observations. Questions ranked by modeled correct-answer
discoverability as follows:

| Rank | Question | Expected online | Found online | Correct found | Unexpected exposure | Gap |
| ---: | --- | ---: | ---: | ---: | ---: | ---: |
| 1 | Current employer | 63.5% | 80.0% | 76.5% | 27.0% | +16.5 pp |
| 2 | High school | 51.5% | 73.5% | 65.0% | 39.0% | +22.0 pp |
| 3 | Birth city | 52.0% | 65.0% | 56.0% | 30.5% | +13.0 pp |
| 4 | Mother's maiden name | 22.0% | 46.0% | 41.0% | 35.0% | +24.0 pp |
| 5 | Wedding location | 26.5% | 39.5% | 35.5% | 32.0% | +13.0 pp |
| 6 | First pet name | 19.5% | 43.0% | 34.5% | 37.0% | +23.5 pp |
| 7 | Favorite sports team | 29.5% | 30.5% | 21.0% | 22.0% | +1.0 pp |
| 8 | Street grew up on | 20.0% | 33.5% | 21.0% | 27.0% | +13.5 pp |
| 9 | First car model | 21.0% | 28.5% | 18.5% | 18.0% | +7.5 pp |
| 10 | Favorite food | 10.5% | 14.5% | 10.0% | 12.5% | +4.0 pp |

The three least-secure modeled questions were current employer, high school,
and birth city. All three answers were correctly discoverable for 27.5% of the
fictional profiles. The three most-secure set was street grew up on, first car
model, and favorite food; all three were discoverable for 0.5%.

## Analysis

The result supports the model's hypothesis. Biographical facts assigned higher
public probabilities ranked as less secure, and expectations understated
discoverability for every question. The largest expectation gaps were mother's
maiden name (+24.0 percentage points), first pet name (+23.5 points), and high
school (+22.0 points).

Requiring three answers reduced the modeled success rate compared with any
single question, but did not make the least-secure set acceptable: more than one
quarter of fictional profiles still had all three modeled as known. This is an
illustration of correlated public exposure and recovery design risk, not an
account-compromise test.

## Conclusion

The synthetic experiment demonstrates that expectation-versus-reality tables
and question rankings can evaluate a recovery design without collecting
personal answers. Within the stated assumptions, questions about commonly
published biographical facts were the weakest, and combining several weak
questions retained substantial modeled exposure.

The more important engineering conclusion comes from current standards:
services should not rely on personal-knowledge security questions. They should
use stronger recovery mechanisms, protect enrollment and authenticator changes,
support password managers, and offer phishing-resistant authentication where
appropriate.

## Limitations

- Every profile and outcome is synthetic.
- Probabilities were selected for demonstration rather than measured.
- Question outcomes are modeled independently even though real public facts may
  be correlated.
- The model omits guessing, acquaintances, rate limits, identity proofing,
  multifactor authentication, notifications, and recovery delays.
- “Correct answer found” is a Boolean event; no answer is generated or tested.
- The three-question result is not evidence that any real account is vulnerable.
- Results cannot estimate prevalence in a student, adult, or internet population.

## Ethical boundary and future work

Future work should remain synthetic or use published aggregate research. Useful
extensions include correlated exposures, recovery-notification controls,
rate-limiting models, passkey recovery, and comparisons between phishing-
resistant and knowledge-based approaches. Do not search for real people's
answers or test live recovery pages. The repository's `ETHICS.md` defines this
boundary.

## References

1. Science Buddies. [How Secure Are Your Security Questions?](https://www.sciencebuddies.org/science-fair-projects/project-ideas/Cyber_p007/cybersecurity/security-questions).
2. National Institute of Standards and Technology. [SP 800-63B: Authentication and Authenticator Management](https://pages.nist.gov/800-63-4/sp800-63b.html), Revision 4.
