# Caesar Cipher Cryptanalysis Lab

A complete, reproducible implementation of the Science Buddies project
"Crack the Code: Breaking a Caesar Cipher." The lab encrypts text from a file,
tries all 25 possible nonzero keys, performs the project's most-common-letter
frequency attack, and ranks candidates with a chi-squared English-frequency
score.

The Caesar cipher is intentionally weak. This project demonstrates why a key
space of only 25 possibilities does not provide useful modern security.

## Security Notice

This is an educational, local-only cryptography exercise, not a production
encryption tool. Do not use a Caesar cipher to protect passwords, personal
information, financial data, or any other secret. Run the lab only on text you
own or are authorized to analyze.

## Requirements

- Python 3.10 or newer
- No third-party packages

## Quick start

Run these commands from this directory.

Encrypt a file with a randomly selected key from 1 through 25:

```powershell
python caesar_cipher.py encrypt samples/plaintext.txt ciphertext.txt
```

The command displays the selected key so the experiment can be recorded. A
repeatable test can specify the key explicitly:

```powershell
python caesar_cipher.py encrypt samples/plaintext.txt ciphertext.txt --key 11
python caesar_cipher.py decrypt ciphertext.txt recovered.txt --key 11
```

Try every possible key:

```powershell
python caesar_cipher.py brute-force samples/example-1.txt
```

Save all candidates and scores as JSON:

```powershell
python caesar_cipher.py brute-force samples/example-1.txt --output candidates.json
```

Perform the simple E-assumption attack and show the five strongest
chi-squared candidates:

```powershell
python caesar_cipher.py frequency samples/example-2.txt --rank 5
```

## What the program demonstrates

- `encrypt` reads plaintext from UTF-8 text, shifts ASCII letters, and saves
  ciphertext to another file.
- `decrypt` reverses encryption when the key is known.
- `brute-force` generates one plaintext candidate for each key from 1 to 25.
- `frequency` counts ciphertext letters and predicts that the most common one
  represents plaintext E, as specified in the source experiment.
- The ranked output tests every key against typical English letter
  frequencies. A lower chi-squared score means a closer statistical match.
- Uppercase and lowercase letters wrap independently; whitespace, digits,
  punctuation, and non-ASCII characters are unchanged.

## Test the lab

```powershell
python -m unittest discover -s tests -v
```

The test suite covers the published shift-three example, wraparound, case and
punctuation preservation, brute-force coverage, simple frequency analysis,
English-frequency ranking, invalid input, file round trips, and JSON output.

## Results

The complete experiment, observations, limitations, and conclusions are in
[LAB_REPORT.md](LAB_REPORT.md). In summary:

| Test ciphertext | Brute-force result | Simple E assumption | Ranked frequency result |
|---|---|---|---|
| Example 1 (short) | Correct key 25 found | Incorrect key 23 | Correct key 25 ranked first |
| Example 2 (long) | Correct key 17 found | Correct key 17 | Correct key 17 ranked first |

Brute force was reliable for both samples because it exhausts the entire key
space. The simple frequency hypothesis failed on the short sample because its
most frequent ciphertext letter did not represent E.

## Project layout

```text
caesar-cipher-cryptanalysis-lab/
|-- caesar_cipher.py       implementation and command-line interface
|-- LAB_REPORT.md          scientific-method write-up and measured results
|-- README.md              usage and project overview
|-- SECURITY.md            responsible-use guidance
|-- samples/               plaintext and supplied ciphertext fixtures
`-- tests/                 standard-library unit and CLI tests
```

## Reference

Project procedure and example ciphertexts: Ben Finio, [Crack the Code:
Breaking a Caesar Cipher](https://www.sciencebuddies.org/science-fair-projects/project-ideas/Cyber_p005/cybersecurity/crack-caesar-cipher),
Science Buddies, last edited July 3, 2024; accessed September 22, 2026.
