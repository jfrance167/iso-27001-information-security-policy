# Security and Responsible Use

This project studies defensive RFID shielding through a bounded simulation and
an optional benchtop experiment. It is not an RFID credential reader, cloner,
or access-control tool.

## Safety boundary

- The software has no serial-port, NFC, USB-device, or network access.
- It generates only synthetic tag labels and simulated read outcomes.
- Reports contain no tag identifiers, credentials, or personal information.
- Repetition and input ranges are bounded to prevent accidental resource abuse.
- Generated data is prominently labeled so it cannot be mistaken for physical
  measurements.

## Optional hardware work

Use only a reader you own and expendable sample tags supplied for experiments.
Do not scan, record, test, or attempt to defeat payment cards, passports,
employee or student badges, transit passes, implanted tags, or any credential
without the issuer's explicit written authorization. Do not store tag serial
numbers in the repository.

Operate the reader at its manufacturer-approved power and frequency. Test on a
stable non-metallic surface, keep metal away from energized electronics, and
have an adult supervise cutting sharp foil or mesh.

Report suspected vulnerabilities through the repository's root security policy
without publishing private identifiers or access details.
