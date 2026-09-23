# Lab Report: Password Security and Guessing Strategies

## Abstract

This experiment evaluated how password length, alphabet size, and human choice
affect resistance to guessing. A Python program calculated fixed-length search
spaces and tested four algorithms against synthetic salted password verifiers:
numeric brute force, alphanumeric brute force, a dictionary attack, and a
combined-word attack. Search spaces grew exponentially: eight alphanumeric
characters have 218,340,105,584,896 possible combinations, while 12 have more
than 3.22 sextillion. In the measured trials, dictionary structure mattered as
much as length. The nine-character dictionary value was recovered in six
guesses, while a two-character alphanumeric value required 2,302 guesses. The
results support the hypothesis that longer randomly selected passwords are
harder to exhaust, but show why length and character-count arithmetic alone do
not describe human-chosen password strength.

## Research question

How do password length, available character count, and guess strategy change
the number of attempts and time required to recover a synthetic password?

## Background

For a fixed password length `L` and an alphabet containing `N` possible
characters, the number of combinations is:

```text
search space = N^L
worst-case seconds = search space / guesses per second
```

Each added character multiplies the search space by `N`, producing exponential
rather than linear growth. A brute-force search enumerates that space. A
dictionary search instead exploits the fact that people often choose familiar
words and predictable variations. Combining words expands the dictionary
search but remains much smaller than enumerating every possible character
sequence of the same length.

Password hashing does not encrypt a password for later decryption. A verifier
derives a value from a candidate and compares it with the stored value. An
offline guessing experiment therefore repeats the derivation for each guess.
This implementation uses PBKDF2-HMAC-SHA-256 with a unique synthetic salt. The
small demonstration work factor keeps the classroom experiment bounded and is
not a production setting.

## Hypothesis

Increasing password length or alphabet size will increase worst-case guessing
time exponentially. Dictionary attacks will recover predictable word-based
passwords in far fewer attempts than brute force, while short random-looking
values will require enumeration unless they appear in the dictionary.

## Variables

- Independent variables: password length, alphabet size, password construction
  pattern, and guess algorithm.
- Dependent variables: candidate count and elapsed time until recovery.
- Controlled variables: Python 3.13.7, one Windows computer, candidate order,
  PBKDF2-HMAC-SHA-256, 2,000 iterations for timed demonstrations, fixed salts
  for repeatability, one-million-guess safety cap, and the same synthetic word
  list.

## Materials

- Windows computer
- Python 3.13.7
- `password_lab.py`
- `samples/synthetic_words.txt`
- Automated tests and this electronic lab notebook

No real credentials, accounts, websites, or remote systems were used.

## Method

### Part 1: calculate password strength

1. Calculate `N^L` for lengths 1 through 8 using alphabet sizes 10 (digits),
   26 (uppercase letters), and 62 (digits plus lowercase and uppercase letters).
2. Treat the number of combinations as worst-case seconds at one guess per
   second, matching the worksheet.
3. Calculate larger 62-character cases for lengths 12, 16, and 20 at one
   million guesses per second.
4. Compare the curves by observing the constant multiplier added by each new
   character.

### Part 2: compare guessing algorithms

1. Create four explicit synthetic passwords: `042`, `A7`, `Sunshine`, and
   `red+planet`.
2. Derive salted PBKDF2 verifier records; do not store real credentials.
3. Test `042` by enumerating `000` through `999`, preserving leading zeros.
4. Test `A7` by enumerating the 62-character alphabet from length 1 through 2.
5. Test `Sunshine` with a synthetic dictionary and lowercase, capitalized,
   uppercase, and reversed variations.
6. Test `red+planet` using pairs of distinct words, separator variations, and
   capitalization variations.
7. Run the complete experiment five times and record the mean, minimum, and
   maximum elapsed time. Candidate counts remain deterministic.
8. Run 15 automated correctness and safety-limit tests.

## Results

### Search-space tables

The completed worksheet tables are:

| Length | Digits: `10^L` | Uppercase: `26^L` | Alphanumeric: `62^L` |
|---:|---:|---:|---:|
| 1 | 10 | 26 | 62 |
| 2 | 100 | 676 | 3,844 |
| 3 | 1,000 | 17,576 | 238,328 |
| 4 | 10,000 | 456,976 | 14,776,336 |
| 5 | 100,000 | 11,881,376 | 916,132,832 |
| 6 | 1,000,000 | 308,915,776 | 56,800,235,584 |
| 7 | 10,000,000 | 8,031,810,176 | 3,521,614,606,208 |
| 8 | 100,000,000 | 208,827,064,576 | 218,340,105,584,896 |

At one guess per second, the numeric cases grow from 10 seconds at length 1 to
3.17 years at length 8. Uppercase-only cases grow from 26 seconds to about
6,620 years. Alphanumeric cases grow from 62 seconds to about 6.92 million
years. On a logarithmic graph these values form straight rising lines; on a
linear graph they form steep exponential curves. Each extra position multiplies
the corresponding curve by 10, 26, or 62.

Longer alphanumeric estimates at one million guesses per second were:

| Length | Combinations | Worst-case time |
|---:|---:|---:|
| 8 | 218,340,105,584,896 | 6.92 years |
| 12 | 3,226,266,762,397,899,821,056 | 102 million years |
| 16 | 47,672,401,706,823,533,450,263,330,816 | 1.51 quadrillion years |
| 20 | 704,423,425,546,998,022,968,330,264,616,370,176 | 22.3 sextillion years |

These are mathematical exhaustive-search estimates, not promises about a
human-selected password. The figures also assume fixed guess throughput;
actual throughput depends heavily on the password hashing scheme and work
factor.

### Measured synthetic attacks

| Method | Value | Guesses | Mean (s) | Minimum (s) | Maximum (s) |
|---|---|---:|---:|---:|---:|
| Numeric brute force | `042` | 43 | 0.037428 | 0.034914 | 0.041791 |
| Alphanumeric brute force | `A7` | 2,302 | 2.006844 | 1.930428 | 2.102128 |
| Dictionary variations | `Sunshine` | 6 | 0.005894 | 0.004997 | 0.008585 |
| Combined words | `red+planet` | 909 | 0.809988 | 0.747781 | 0.881277 |

All four synthetic passwords were recovered. The 15-test suite passed without
failures. The guess counts are repeatable; elapsed times vary with host load.

## Analysis

The search-space results support the first part of the hypothesis. Increasing
length by one multiplies the combinations by the alphabet size. Expanding from
8 to 12 alphanumeric characters multiplies the fixed-length search space by
`62^4`, or 14,776,336.

The measured results support the second part. `Sunshine` has nine characters,
but the dictionary method found it in six guesses because it was a predictable
word and capitalization pattern. `A7` has only two characters but required
2,302 guesses in the chosen brute-force ordering. Length matters most when the
characters are independently and randomly selected; human patterns can reduce
the attacker's effective search dramatically.

The combined-word value required more guesses than the single dictionary word,
but far fewer than exhaustive brute force over all 10-character alphanumeric
strings. This shows that adding separators and words improves resistance only
to the extent that the resulting phrase is unpredictable. A unique, long
password generated by a password manager avoids much of this selection bias.

## Modern security interpretation

The original 2021 activity used MD5 examples. MD5 is unsuitable for password
storage because it is fast and was not designed as a costed password hashing
scheme. This lab uses salted PBKDF2 to demonstrate modern verifier structure,
although its deliberately small demo iteration count is also unsuitable for
production.

Current [NIST SP 800-63B](https://pages.nist.gov/800-63-4/sp800-63b.html)
requires at least 15 characters for a single-factor password, comparison
against a blocklist of common or compromised values, rate limiting for online
attempts, and salted password hashing with a practical cost factor. It also
rejects arbitrary composition rules as a substitute for those controls.
Passwords are not phishing-resistant, so multi-factor or phishing-resistant
authentication remains important.

## Sources of error and limitations

- The word list is intentionally tiny and synthetic, so it does not model a
  real attacker corpus.
- Synthetic target positions were selected for a bounded classroom runtime.
- PBKDF2 timing varies by processor, operating system load, Python version, and
  iteration count.
- A single speed figure cannot represent both rate-limited online attacks and
  offline attacks against stolen verifier data.
- Search-space calculations assume uniform random selection and exact knowledge
  of the alphabet and length.
- Worst-case search takes every guess; an average uniformly random target takes
  roughly half the search space.
- The demo does not evaluate phishing, password reuse, malware, credential
  stuffing, or multi-factor authentication.

## Conclusion

The lab objective was achieved. The program calculated exponential search
spaces, implemented four distinct guessing strategies, measured attempts and
time, and recovered every bundled synthetic example. Longer independently
random passwords create far larger exhaustive search spaces, while predictable
words and patterns can be guessed early regardless of their apparent length.
Strong real-world practice therefore combines long unique passwords, a
password manager, compromised-password blocking, rate limiting, secure salted
password hashing, and stronger authentication factors.

## Reproduction commands

```powershell
python -m unittest discover -s tests -v
python password_lab.py table
python password_lab.py estimate 62 12 --guesses-per-second 1000000
python password_lab.py demo --iterations 2000 --json
```

## References

- Science Buddies Staff. [Password Security: How Easily Can Your Password Be
  Hacked?](https://www.sciencebuddies.org/science-fair-projects/project-ideas/CompSci_p046/computer-science/password-security-how-easily-can-your-password-be-hacked),
  last edited April 1, 2021; accessed September 22, 2026.
- National Institute of Standards and Technology. [SP 800-63B: Authentication
  and Authenticator Management](https://pages.nist.gov/800-63-4/sp800-63b.html),
  current revision accessed September 22, 2026.
