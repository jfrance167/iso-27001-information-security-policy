# Lab Report: Preventing SQL Injection with Parameterized Queries

## Abstract

This project investigated whether parameterized SQL statements prevent the
authentication bypass and data-exposure behavior associated with unsafe string
interpolation. Because the Science Buddies project's original AWS environment
is deprecated, the procedure was modernized into a safe local experiment. A
Python program created 25 fictional accounts in an in-memory SQLite database.
Six scenarios—valid credentials, an incorrect password, three bounded login
bypass patterns, and one bounded data-exposure pattern—were repeated four times
for every account, producing 600 trials. The unsafe legacy design was modeled
but never executed; the secure design ran the same inputs through real
parameterized SQLite queries. The legacy model predicted unauthorized
authentication in 300 of 300 login-injection trials and exposure of all 25
records in every union-exposure trial. The parameterized implementation had
zero unauthorized authentications, exposed zero rows for every attack
scenario, retained 100% legitimate-login success, and preserved database
integrity in all 600 trials. The results support the hypothesis that separating
SQL instructions from input values prevents this class of injection behavior.

## Research question

How does replacing string-interpolated SQL with parameterized queries affect
unauthorized authentication, row exposure, legitimate authentication, and
database integrity under controlled SQL-injection scenarios?

## Background

SQL is used by applications to create, retrieve, update, and delete database
records. An application becomes vulnerable to SQL injection when it combines
untrusted input with SQL instructions in a way that allows the input to change
the statement's meaning. An attacker may then bypass a login, retrieve records,
or alter data.

Parameterized queries separate the SQL statement from its values. The database
engine parses the fixed statement and treats supplied values as data, even when
those values contain quotation marks, SQL keywords, or comment markers.

The Science Buddies project asks students to fix a vulnerable PHP application,
but its page now warns that the required AWS feature has been deprecated. This
implementation keeps the learning objective while removing the obsolete cloud
dependency, payment-card requirement, public network service, and risk of
shipping deliberately exploitable code.

## Hypothesis

If all database operations use parameterized queries, then controlled injection
inputs will be treated as literal data. Therefore:

- legitimate credentials will continue to authenticate;
- incorrect credentials will remain rejected;
- injection scenarios will cause no unauthorized authentication;
- injection scenarios will expose no rows; and
- the number of database records will remain unchanged.

## Variables

### Independent variables

- Query design: modeled legacy string interpolation or real parameterized SQL
- Input scenario:
  - valid credentials
  - wrong password
  - username tautology
  - password tautology
  - comment-based bypass
  - union-style exposure attempt

### Dependent variables

- Authentication success rate
- Unauthorized authentication rate
- Mean rows exposed
- Database integrity rate

### Controlled variables

- 25 deterministic fictional accounts
- Four repetitions per account and scenario
- Experiment seed `20260924`
- Identical scenario inputs for both designs
- Identical in-memory SQLite schema
- Fixed parameterized login and search statements

## Materials

- Python 3.10 or newer
- Python standard library (`sqlite3`, `csv`, `json`, `hashlib`, `unittest`)
- `sql_injection_lab.py`
- `tests/test_sql_injection_lab.py`
- No web server, cloud account, external package, real credential, or personal
  information

## Engineering requirements

The replacement design had to:

1. accept legitimate synthetic credentials;
2. reject incorrect and injection-like inputs;
3. keep input separate from SQL syntax;
4. preserve all database records;
5. operate locally without opening a network port;
6. avoid executing dynamically constructed SQL;
7. produce deterministic and auditable evidence; and
8. omit raw passwords and payload text from result files.

## Design

The program creates an in-memory `users` table and populates it using
parameterized inserts. Each fictional email uses the reserved `.invalid`
top-level domain.

The secure login and search operations use fixed statements with `?`
placeholders. SQLite receives input values separately from the statement.

For scientific comparison, the program contains a bounded model of the
expected behavior of an unsafe legacy design for six predefined classroom
scenarios. The model records the predicted authentication and exposure result.
It does not create a dynamic SQL string and does not send one to SQLite. This is
an explicit safety control and a limitation of the experiment.

## Procedure

1. Generate 25 deterministic fictional users.
2. Create an in-memory SQLite database and its `users` table.
3. Insert all records with parameterized SQL.
4. Select one account and one of the six controlled scenarios.
5. Record the bounded legacy model's predicted authentication and exposure
   result.
6. Send the same supplied username and password to the real parameterized login
   query.
7. For the union-exposure scenario, send the supplied value to the real
   parameterized public-record search.
8. Record authentication, unauthorized access, exposed rows, and whether all
   25 database records still exist.
9. Repeat every scenario four times for every account.
10. Save the 600 redacted trials to `reports/results.csv`.
11. Aggregate the six scenario groups into `reports/summary.json`.
12. Run all 23 automated tests, compilation checks, Bandit, and CodeQL.

The exact experiment command was:

```powershell
python sql_injection_lab.py experiment `
  --users 25 `
  --repetitions 4 `
  --seed 20260924 `
  --output reports/results.csv `
  --summary reports/summary.json
```

## Results

Each scenario contained 100 trials.

| Scenario | Legacy authentication | Secure authentication | Legacy unauthorized access | Secure unauthorized access | Legacy mean rows exposed | Secure mean rows exposed |
|---|---:|---:|---:|---:|---:|---:|
| Valid credentials | 100% | 100% | 0% | 0% | 1 | 1 |
| Wrong password | 0% | 0% | 0% | 0% | 0 | 0 |
| Username tautology | 100% | 0% | 100% | 0% | 1 | 0 |
| Password tautology | 100% | 0% | 100% | 0% | 1 | 0 |
| Comment bypass | 100% | 0% | 100% | 0% | 1 | 0 |
| Union exposure | 0% | 0% | 0% | 0% | 25 | 0 |

Database integrity was 100% for every scenario. Across the 300 modeled login
injection trials, the legacy unauthorized-access rate was 100%, while the
parameterized implementation's rate was 0%. Across the 100 union-exposure
trials, the legacy model exposed an average of 25 rows and the parameterized
implementation exposed zero.

## Analysis

The control scenarios show that parameterization did not break expected
behavior: all legitimate attempts succeeded and all wrong-password attempts
failed in both designs.

The three login-injection scenarios sharply separated the designs. The unsafe
model treated the supplied fragments as statement structure and predicted an
authentication bypass. SQLite treated the same supplied strings as literal
values in the secure path and found no matching account.

The union-style scenario produced the largest modeled confidentiality impact:
all 25 synthetic records were exposed in the legacy model. The parameterized
search looked for a username exactly equal to the supplied string and returned
zero rows.

The database count remained 25 after every trial. This confirms that the
experiment did not execute destructive SQL and that the safe implementation
preserved integrity.

## Conclusion

The results support the hypothesis. Parameterized queries preserved legitimate
functionality while preventing every modeled unauthorized authentication and
data-exposure outcome. The experiment demonstrates the central defensive
principle: applications should send a fixed SQL statement and bind untrusted
values separately instead of combining values with SQL instructions.

## Limitations

- The legacy path is a deterministic model, not an executable vulnerable
  application. Its values are expected outcomes for the six defined scenarios.
- SQLite behavior does not represent every database engine or framework.
- The lab tests only a small, predefined scenario set.
- It does not evaluate authorization flaws, weak passwords, cross-site
  scripting, session security, or other web vulnerabilities.
- Synthetic plaintext passwords are used only to isolate the query-binding
  variable. Production systems must store passwords with a suitable salted
  password-hashing function and never as plaintext.

## Safety and ethics

All activity is confined to an in-memory database containing fictional data.
No service listens on a network, no external system is tested, and no dynamic
SQL statement is executed. Cybersecurity testing must be limited to systems
the tester owns or has explicit authorization to assess.

## Future improvements

- Add property-based generation of harmless quote and delimiter inputs.
- Compare safe parameter-binding APIs across multiple local database engines.
- Add a local-only web interface that exposes only the secure implementation.
- Measure query behavior under Unicode and normalization edge cases.
- Evaluate least-privilege database accounts and row-level authorization as
  separate defensive layers.

## References

- Science Buddies. [Preventing SQL Injection Attacks](https://www.sciencebuddies.org/science-fair-projects/project-ideas/Cyber_p008/cybersecurity/sql-injection).
- OWASP Foundation. [SQL Injection Prevention Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/SQL_Injection_Prevention_Cheat_Sheet.html).
- Python Software Foundation. [`sqlite3` — DB-API 2.0 interface for SQLite databases](https://docs.python.org/3/library/sqlite3.html).
