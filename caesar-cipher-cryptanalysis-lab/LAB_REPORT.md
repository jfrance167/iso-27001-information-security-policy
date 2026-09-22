# Lab Report: Breaking a Caesar Cipher

## Abstract

This experiment tested how effectively a computer can recover English text
encrypted with a Caesar cipher. A Python program was developed to encrypt and
decrypt files, enumerate all 25 possible nonzero keys, infer a key by assuming
the most common ciphertext letter represents E, and rank all keys with an
English letter-frequency score. Brute force recovered both supplied messages.
The simple E assumption recovered the longer message but failed on the shorter
one. A chi-squared ranking placed the correct key first for both. The results
show that the cipher's 25-key search space is its decisive weakness and that
frequency analysis becomes less dependable as the message gets shorter.

## Research question

Can a program recover English plaintext from a Caesar cipher without being
given the key, and how do brute force and frequency analysis compare on short
and longer messages?

## Background

A Caesar cipher is a monoalphabetic substitution cipher. Encryption replaces
each letter with the letter a fixed number of positions later in the alphabet.
Modulo 26 arithmetic makes the shift wrap from Z to A:

```text
encryption: C = (P + key) mod 26
decryption: P = (C - key) mod 26
```

There are 26 possible shifts, but shift 0 leaves the text unchanged. An
attacker therefore needs to test only 25 non-identity keys. Frequency analysis
uses the uneven distribution of English letters to estimate the substitution.
The experiment's simple method assumes the most common ciphertext letter is an
encrypted E. That assumption is plausible for a large English sample but is
not guaranteed for any individual message.

## Hypothesis

Brute force will always include the correct plaintext because every possible
key is tested. The E-assumption method will be faster to inspect when its
assumption is true, but it will be less reliable on a short message because a
small sample may not have E as its most common plaintext letter.

## Variables

- Independent variable: attack method (brute force, simple E assumption, or
  chi-squared ranking) and ciphertext length/content.
- Dependent variables: recovered key, readable plaintext, and rank of the
  correct candidate.
- Controlled conditions: English ASCII input, Caesar substitution over A-Z
  and a-z, keys from 1 to 25, unchanged punctuation and spaces, and the same
  Python implementation for every trial.

## Materials

- Windows computer
- Python 3.13.7
- `caesar_cipher.py`
- UTF-8 text fixtures in `samples/`
- Lab notebook represented by this report and automated test output

## Method

1. Implement letter shifting with modulo 26 while preserving case and leaving
   nonletters unchanged.
2. Read a plaintext file, choose a random nonzero key, encrypt the text, and
   save the ciphertext. Also use a recorded key for a repeatable round-trip.
3. Decrypt the repeatable trial with its known key and compare the recovered
   bytes with the original plaintext.
4. For each supplied ciphertext, decrypt with keys 1 through 25 and inspect the
   candidate that forms meaningful English.
5. Count ciphertext letters. Treat the most common letter as encrypted E,
   calculate `key = (cipher_letter - E) mod 26`, and decrypt with that key.
6. As an extension, score every brute-force candidate against standard English
   letter frequencies using chi-squared distance and sort from lowest to
   highest score.
7. Run the automated test suite to verify known values, edge cases, file I/O,
   and attack output.

All experiments used local, public or synthetic text. No accounts, networks,
or third-party systems were accessed.

## Results

### Implementation validation

The standard shift-three control produced the expected result:

```text
Plaintext:  THIS IS A SECRET MESSAGE
Ciphertext: WKLV LV D VHFUHW PHVVDJH
```

The random-key file trial selected key 5. A separate repeatable file round-trip
test encrypted and then decrypted `Meet me at 5:30.` with key 8. The recovered
text content matched the original, including case, spaces, digits, and
punctuation. The automated suite completed 10 tests with no failures.

### Supplied ciphertext trials

| Measurement | Example 1 | Example 2 |
|---|---:|---:|
| Letters analyzed | 36 | 89 |
| Correct key | 25 | 17 |
| Correct plaintext found by brute force | Yes | Yes |
| Most common ciphertext letter | B (4 occurrences) | V (11 occurrences) |
| Key predicted by E assumption | 23 | 17 |
| E-assumption result correct | No | Yes |
| Chi-squared rank of correct key | 1 | 1 |
| Correct candidate chi-squared score | 20.316 | 29.206 |

Brute force identified the following plaintexts:

```text
Example 1, key 25:
CONGRATULATIONS! YOU HAVE CRACKED THE CODE!

Example 2, key 17:
DID YOU THINK THIS PROJECT WAS FUN? CHECK OUT THE LEARN MORE SECTION TO
LEARN ABOUT CAREERS IN CYBERSECURITY.
```

For Example 1, the simple method predicted key 23 and returned gibberish. The
short plaintext's most common letter was not E, so its core assumption was
false. For Example 2, ciphertext V mapped back to E with key 17, so both the
key and plaintext were recovered immediately.

### Method comparison

| Method | Keys evaluated | Strength | Limitation |
|---|---:|---|---|
| Brute force | 25 | Correct answer is guaranteed to be present | A person or scoring rule must identify the readable candidate |
| Most-common letter -> E | 1 | Very simple and fast | Fails whenever E is not the sample's most common plaintext letter |
| Chi-squared ranking | 25 | Automatically prioritizes English-like distributions | Can mis-rank very short, unusual, or non-English text |

## Analysis

The observations support the hypothesis. Brute force succeeded regardless of
message length because the key space was fully enumerated. Its computational
cost is trivial: for a message of length `n`, testing all keys requires about
`25n` character operations, which scales linearly with message length.

The frequency result depended on the text sample rather than the cipher alone.
Example 1 contained only 36 letters, and the most common plaintext letter did
not match the assumed E. Example 2 contained 89 letters and happened to satisfy
the assumption. The longer sample therefore worked, but length does not create
a guarantee; topic, vocabulary, repetition, and language all influence the
observed distribution.

The chi-squared extension used the full alphabet instead of one letter. It
ranked both correct plaintexts first, including the sample that defeated the E
assumption. This improves automation, although it still relies on the message
resembling the reference English distribution.

## Sources of error and limitations

- Readability was determined from known English output; another language would
  require different expected frequencies.
- Letter-frequency scoring ignores word boundaries, grammar, and context.
- Small or deliberately unusual samples can produce misleading statistics.
- Tied most-common letters are resolved alphabetically for repeatability; a
  different tie rule could predict a different key.
- Only ASCII A-Z and a-z are shifted. Accented and non-Latin letters remain
  unchanged.
- The supplied examples test known classroom data, not adversarial inputs.

## Conclusion

The program met the objective: it decrypted Caesar-cipher text without prior
knowledge of the key. Brute force was the most dependable technique because 25
possibilities are small enough to test exhaustively. Simple frequency analysis
worked on the longer sample but failed on the short sample, demonstrating why
statistical attacks need enough representative text. Using all letter
frequencies improved ranking, but no variation makes the Caesar cipher secure.
Modern confidential data requires reviewed, authenticated encryption rather
than a small substitution cipher.

## Reproduction commands

```powershell
python -m unittest discover -s tests -v
python caesar_cipher.py encrypt samples/plaintext.txt ciphertext.txt --key 11
python caesar_cipher.py decrypt ciphertext.txt recovered.txt --key 11
python caesar_cipher.py brute-force samples/example-1.txt
python caesar_cipher.py frequency samples/example-1.txt --rank 3
python caesar_cipher.py frequency samples/example-2.txt --rank 3
```

## Reference

Finio, B. (2024, July 3). [Crack the Code: Breaking a Caesar
Cipher](https://www.sciencebuddies.org/science-fair-projects/project-ideas/Cyber_p005/cybersecurity/crack-caesar-cipher).
Science Buddies. Accessed September 22, 2026.
