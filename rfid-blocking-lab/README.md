# RFID Shielding Lab

This lab is a safe, reproducible adaptation of Science Buddies' **Blocking
RFID Readers from Reading your ID Card** project. It investigates how shielding
material changes a passive tag's maximum reliable read distance.

The reader named by the original project is discontinued and no physical RFID
hardware was available for this implementation. The completed computational
experiment therefore uses a documented near-field model, synthetic tag
profiles, eight material conditions, 15 distances, and 10 repetitions. Every
generated row says `SIMULATED DATA - NOT PHYSICAL RFID MEASUREMENTS`.

## Completed experiment

From this directory, run:

```powershell
python rfid_shielding_lab.py experiment
python -m unittest discover -s tests -v
```

The experiment writes 3,600 deterministic modeled trials to
`reports/results.csv` and 24 tag/material summaries to
`reports/summary.json`.

To inspect one modeled setup:

```powershell
python rfid_shielding_lab.py estimate id_card aluminum_foil
```

## Optional physical follow-up

The model is complete, but it does not replace a hardware experiment. If a
compatible reader and expendable sample tags become available, follow the
controlled procedure in `LAB_REPORT.md` and enter measurements in
`physical_measurement_template.csv`. Never use an employee badge, payment
card, passport, transit pass, or another live credential.

## Files

- `rfid_shielding_lab.py` — bounded model, experiment, analysis, and CLI
- `tests/test_rfid_shielding_lab.py` — model, safety-label, output, and CLI tests
- `reports/results.csv` — 3,600 clearly labeled simulated trials
- `reports/summary.json` — 24 aggregated tag/material results
- `physical_measurement_template.csv` — blank worksheet for future real data
- `LAB_REPORT.md` — full scientific-method write-up and hardware protocol
- `SECURITY.md` — privacy and responsible-use boundaries

## Sources

- [Science Buddies: Blocking RFID Readers from Reading your ID Card](https://www.sciencebuddies.org/science-fair-projects/project-ideas/CompSci_p048/computer-science/blocking-rfid-readers-from-reading-your-id-card)
- [NIST SP 800-98: Guidelines for Securing RFID Systems](https://csrc.nist.gov/pubs/sp/800/98/final)
