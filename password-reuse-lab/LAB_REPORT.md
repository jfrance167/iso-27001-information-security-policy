# Do People Use Different Passwords for Different Accounts?

## Abstract

This project examined how password reuse can be measured without collecting
passwords. The original Science Buddies project proposes a survey with letters
representing repeated passwords. Because human-subject approval and volunteers
were not available, this completed version generated 120 clearly labeled
synthetic respondents and used respondent-local opaque group labels. The run
contained 1,609 account rows across seven categories. Synthetic respondents had
an average of 13.408 accounts and 8.950 distinct password groups, giving a mean
normalized password diversity of 0.6722. The mean fraction of account pairs
sharing a password was 0.1329, and the average largest simulated exposure
cascade was 3.933 accounts. The results validate the analysis method and show
how reuse can enlarge the effect of one compromised password, but they do not
estimate real population behavior.

## Research question

How can password reuse across account categories be measured without collecting
passwords or other identifying information?

## Background

Reusing one password across services creates a shared failure point. If one
service exposes that password, an attacker may try it against other accounts in
a credential-stuffing attack. NIST SP 800-63B explains that password managers
can maintain distinct passwords for different services and identifies distinct
passwords as important protection against password stuffing.

The Science Buddies procedure avoids asking for password text. Participants
instead assign the same arbitrary letter to accounts that use the same password.
It recommends counting distinct passwords, normalizing by the number of accounts,
building a histogram, and comparing reuse across account categories. It also
states that human-subject rules and consent requirements must be addressed
before surveying people.

The source project's older discussion includes composition rules and frequent
password changes. Current NIST guidance differs: verifiers should not impose
character-type composition rules or require arbitrary periodic changes, should
check new passwords against a blocklist of commonly used or compromised values,
and should permit password managers and autofill.

## Hypothesis

A privacy-preserving, label-based analysis can quantify password reuse without
knowing any password. In a synthetic population containing low-, moderate-, and
high-reuse profiles, most respondents will use fewer distinct password groups
than accounts, and same-category accounts will sometimes share a group.

## Variables and measures

- **Independent/model factors:** synthetic reuse profile, account ownership,
  and account category.
- **Primary dependent measure:** normalized password diversity, calculated as
  distinct opaque groups divided by account count.
- **Secondary measures:** reused account-pair rate, largest exposure cascade,
  distinct-group histogram, and category outcomes.
- **Controlled factors:** account list, profile weights, generation algorithm,
  seed, output schema, and category definitions.

A normalized diversity of `1.0` means every account has a different password
group. Lower values indicate reuse. The reused account-pair rate is:

```text
pairs sharing a group / all possible account pairs
```

The largest exposure cascade is the maximum number of accounts assigned to one
group for a respondent. It is an educational reuse metric, not a prediction that
those accounts would actually be compromised.

## Privacy-preserving design

The generated dataset contains only:

- synthetic IDs such as `S0001`;
- generic account categories and slots;
- synthetic behavior profiles; and
- respondent-local labels such as `G01`.

It contains no humans, credentials, password hashes, usernames, providers,
demographics, or network activity. Every row is marked `SYNTHETIC SURVEY DATA -
NO HUMAN PASSWORDS OR RESPONSES`.

## Procedure

1. Define 17 generic account slots across email, work/school, finance, shopping,
   social, entertainment, and device categories.
2. Assign each synthetic respondent a low-, moderate-, or high-reuse profile
   using fixed documented weights.
3. Model account ownership with fixed probabilities while ensuring each
   respondent has at least two accounts.
4. Assign a new opaque group or reuse an existing group according to the profile.
   Same-category reuse is favored when reuse occurs.
5. Generate 120 respondents with seed `20260925`.
6. Calculate respondent-level normalized diversity, pair reuse, and largest
   group size.
7. Count respondents by number of distinct groups to form a histogram.
8. Classify each eligible respondent/category as all same, all different, or
   mixed and calculate its mean pair-reuse rate.
9. Repeat the run and automated tests to confirm deterministic behavior.

The command was:

```powershell
python password_reuse_lab.py experiment --respondents 120 --seed 20260925
```

## Results

The run generated 1,609 synthetic account rows and 120 respondent-metric rows.

| Overall measure | Result |
| --- | ---: |
| Mean accounts per respondent | 13.408 |
| Mean distinct password groups | 8.950 |
| Mean normalized password diversity | 0.6722 |
| Mean reused account-pair rate | 0.1329 |
| Mean largest exposure cascade | 3.933 accounts |

The distinct-group histogram was:

| Distinct groups | Respondents | Distinct groups | Respondents |
| ---: | ---: | ---: | ---: |
| 1 | 2 | 9 | 12 |
| 2 | 1 | 10 | 14 |
| 3 | 3 | 11 | 16 |
| 4 | 6 | 12 | 9 |
| 5 | 13 | 13 | 11 |
| 6 | 4 | 14 | 4 |
| 7 | 11 | 15 | 4 |
| 8 | 10 | — | — |

Category results include only respondents owning at least two accounts in that
category:

| Category | Eligible | All same | All different | Mixed | Mean pair reuse |
| --- | ---: | ---: | ---: | ---: | ---: |
| Device | 89 | 26 | 63 | 0 | 0.2921 |
| Email | 74 | 24 | 50 | 0 | 0.3243 |
| Entertainment | 104 | 21 | 60 | 23 | 0.2756 |
| Finance | 63 | 15 | 48 | 0 | 0.2381 |
| Shopping | 63 | 16 | 47 | 0 | 0.2540 |
| Social | 112 | 23 | 61 | 28 | 0.2887 |
| Work/school | 108 | 24 | 61 | 23 | 0.2932 |

## Analysis

The mean diversity of 0.6722 indicates that, inside the synthetic model, the
average respondent used roughly two distinct groups per three accounts. The
mean largest group covered almost four accounts, illustrating why one reused
secret can create a multi-account exposure. Email had the highest within-category
pair-reuse rate in this run, while finance had the lowest.

These differences are consequences of the seeded assumptions, not observations
about people. Their purpose is to verify that the method distinguishes all-same,
all-different, and mixed behavior and correctly normalizes respondents with
different account counts.

## Conclusion

The hypothesis was supported as a method-validation result. Opaque local labels
were sufficient to calculate password diversity, pair reuse, exposure cascade,
histogram counts, and category patterns without storing a password. The
synthetic population also produced the expected relationship: distinct groups
were usually fewer than accounts.

No conclusion about how often real students or adults reuse passwords is
justified from these data. That question requires an approved human-subject
survey and a clearly described sampling method.

## Limitations

- All responses are simulated from assumed probabilities.
- Profile weights and ownership rates were selected for demonstration, not
  estimated from a representative population.
- Opaque labels reveal equality relationships but do not measure password
  strength, compromise status, multifactor authentication, or passkeys.
- A shared group does not prove every associated account is exploitable; services
  can have different controls and usernames.
- Category eligibility varies because some synthetic respondents do not own two
  accounts in every category.
- A real convenience sample could have selection, recall, and social-desirability
  bias even if it collects no secrets.

## Optional physical survey extension

Use `survey_template.csv` only after approval described in
`HUMAN_SUBJECTS.md`. Participants should mark generic account slots as present
or absent and use arbitrary labels to indicate reuse. Do not collect names,
providers, login IDs, demographics, password text, hashes, or recognizable
password hints. Publish aggregate results only and compare them with the
synthetic pipeline after documenting sample size, recruitment, consent,
nonresponse, and exclusions.

## Recommendations

- Use a reputable password manager to generate and store distinct passwords.
- Prefer phishing-resistant authentication such as properly implemented
  passkeys when available.
- Enable multifactor authentication, especially on important accounts.
- Change a password when compromise is suspected or confirmed, rather than on
  an arbitrary schedule.
- Services should block commonly used or compromised passwords and allow paste,
  autofill, and long passwords consistent with current NIST guidance.

## References

1. Science Buddies. [Do People Use Different Passwords for Different Accounts?](https://www.sciencebuddies.org/science-fair-projects/project-ideas/HumBeh_p057/human-behavior/do-people-use-different-passwords-for-different-accounts).
2. National Institute of Standards and Technology. [SP 800-63B: Authentication and Authenticator Management](https://pages.nist.gov/800-63-4/sp800-63b.html), Revision 4.
