# Blocking RFID Readers from Reading an ID Card

## Abstract

This project investigated whether conductive shielding materials reduce the
distance at which a passive radio-frequency identification (RFID) tag can be
read. Because the reader specified by the source project is discontinued and no
replacement hardware was available, the completed experiment used a transparent
computational model rather than fabricated physical observations. Three
synthetic tag profiles, eight material conditions, and distances from 1 through
15 cm were tested ten times each, producing 3,600 reproducible simulated
trials. The model predicts that solid conductive materials reduce read range
substantially, while paper behaves approximately like the unshielded control.
These results support the hypothesis inside the model, but physical testing is
still required before making claims about a particular reader, tag, or product.

## Research question

How does the shielding material placed completely around a passive low-frequency
RFID tag affect its farthest reliable read distance?

## Background

Passive RFID tags obtain operating energy from a reader's electromagnetic field
and return stored data without a continuously powered transmitter. The source
Science Buddies project proposes comparing the farthest readable distance of
several tag types through materials such as aluminum foil, copper foil, metal
mesh, steel, and a commercial shielding sleeve. It also notes that the original
125 kHz Parallax reader is no longer available.

NIST SP 800-98 describes RFID systems, their security and privacy risks, and
practical safeguards. Shielding is only one layer: system owners must also
consider authentication, authorization, data protection, monitoring, and the
properties of the specific RFID frequency and equipment.

At low frequency and short distance, inductive RFID behavior is a near-field
coupling problem. For this classroom model, received power is assumed to fall
approximately with the inverse sixth power of distance. If a material introduces
an illustrative attenuation of `A` decibels, the modeled range is:

```text
shielded range = unshielded range × 10^(-A / 60)
```

This equation is a simplified model, not a material certification method.

## Hypothesis

If a conductive material fully covers a passive RFID tag, then its farthest
reliable read distance will be lower than for the unshielded control. Solid
metal foils and a commercial sleeve are expected to reduce range more than
paper or open metal mesh.

## Variables

- **Independent variable:** shielding material.
- **Dependent variable:** farthest distance with an 80% or greater simulated
  read-success rate.
- **Controlled variables:** tag profile, reader model, material coverage,
  orientation, distance steps, number of repetitions, and random seed.
- **Modeled tag factor:** unshielded range (5 cm, 8 cm, or 11 cm).

## Materials and assumptions

The computational experiment requires Python 3.11 or later and no third-party
packages. It evaluates these documented assumptions:

| Condition | Assumed attenuation | Category |
| --- | ---: | --- |
| No shield | 0.0 dB | Control |
| Paper | 0.2 dB | Nonconductive control |
| Aluminum screen | 10.0 dB | Conductive mesh |
| Copper mesh | 12.0 dB | Conductive mesh |
| Steel sheet | 18.0 dB | Solid metal |
| Aluminum foil | 24.0 dB | Solid metal |
| Copper foil | 28.0 dB | Solid metal |
| Commercial RFID sleeve | 32.0 dB | Commercial shield |

These attenuation values are illustrative inputs selected to exercise the
model. They are not measured values, product ratings, or claims that one metal
always outperforms another.

## Computational procedure

1. Define three synthetic tags with unshielded ranges of 5, 8, and 11 cm.
2. Calculate each tag/material effective range with the documented equation.
3. Evaluate distances from 1 through 15 cm.
4. Convert the effective range into a smooth probability of successful reading,
   accounting for ordinary trial-to-trial variation near the boundary.
5. Run ten seeded repetitions for every tag, material, and distance.
6. Store every row with an explicit simulated-data label.
7. Calculate the farthest distance where at least 80% of trials succeeded.
8. Repeat with the same seed and verify byte-for-byte reproducibility through
   automated tests.

The completed run used seed `20260924`:

```powershell
python rfid_shielding_lab.py experiment --seed 20260924 --repetitions 10
```

## Results

The run produced 3,600 trials and 24 tag/material summary records. Selected
results are shown below. Distances are modeled centimeters.

| Material | Small fob reliable range | ID card reliable range | Large card reliable range |
| --- | ---: | ---: | ---: |
| No shield | 4 | 7 | 9 |
| Paper | 4 | 7 | 11 |
| Aluminum screen | 2 | 3 | 6 |
| Copper mesh | 2 | 4 | 4 |
| Steel sheet | 2 | 3 | 4 |
| Aluminum foil | 1 | 2 | 3 |
| Copper foil | 1 | 2 | 3 |
| Commercial RFID sleeve | 1 | 2 | 2 |

The modeled effective range of the ID-card profile declined from 8.000 cm with
no shield to 3.185 cm with aluminum foil and 2.343 cm with the commercial sleeve.
That corresponds to modeled reductions of about 60% and 71%, respectively.
Paper's modeled effective range was 7.939 cm, effectively matching the control.

The reliable-distance statistic is based on only ten Bernoulli repetitions at
integer distance steps. Random variation can therefore make one discrete value
look unexpectedly high or low—for example, paper and the large-card profile.
The continuous modeled effective range and the full success-rate data in the
report files provide necessary context.

## Conclusion

Within this model, the results support the hypothesis. Conductive shielding
reduced the reliable read range for all three synthetic tag profiles, and the
largest assumed attenuation produced the shortest range. The experiment also
predicts that a larger or better-coupled tag can remain readable farther away
than a smaller tag under the same shielding condition.

The strongest defensible conclusion is conditional: **if** the model assumptions
approximately describe a physical setup, complete conductive coverage should
reduce read range. The simulation alone cannot prove that a real wallet, foil,
or mesh blocks a specific credential reader.

## Limitations and sources of error

- No physical reader, tag, or shield was measured.
- Material attenuation values are assumptions, not laboratory measurements.
- The inverse-sixth-power approximation omits antenna geometry, resonance,
  detuning, polarization, reader power, noise, and complex near-field effects.
- Real gaps, seams, folds, mesh spacing, orientation, and incomplete coverage
  can dominate performance.
- Results for a 125 kHz inductive system do not automatically apply to 13.56
  MHz NFC or UHF RFID systems.
- Integer-centimeter steps and ten repetitions limit measurement resolution.
- A shielding product should not be trusted for security without testing it
  against the actual tag and reader environment.

## Optional physical validation protocol

Only use expendable sample tags and a reader you own. Never experiment on live
payment, identity, transit, access-control, or implanted credentials.

1. Record the reader model, approved operating frequency, tag type, and test
   environment. Do not record the tag identifier.
2. Mount the reader and sample tag facing each other on non-metallic supports.
3. Keep tag orientation, height, shield area, and coverage identical throughout.
4. Establish the unshielded control by moving from outside the read range toward
   the reader in 1 cm increments.
5. At each distance, attempt ten reads and record only success/failure. Define a
   reliable distance as at least eight successful reads out of ten.
6. Repeat three complete trials for the control and at least six shielding
   materials, using equal-sized pieces and complete tag coverage.
7. Randomize material order to reduce drift and operator-learning effects.
8. Enter only aggregate farthest distances into
   `physical_measurement_template.csv`; keep all credential identifiers out.
9. Compare physical averages and variation with the model. Replace the assumed
   attenuation values only if the fitted method and source data are documented.

## Future work

A useful extension would compare multiple legal sample-tag frequencies, test
seams and partial coverage, use finer distance steps, and calculate confidence
intervals from more repetitions. A second extension could fit model parameters
to properly collected physical data and reserve a separate validation set to
test predictive accuracy.

## References

1. Science Buddies. [Blocking RFID Readers from Reading your ID Card](https://www.sciencebuddies.org/science-fair-projects/project-ideas/CompSci_p048/computer-science/blocking-rfid-readers-from-reading-your-id-card).
2. National Institute of Standards and Technology. [SP 800-98: Guidelines for Securing Radio Frequency Identification (RFID) Systems](https://csrc.nist.gov/pubs/sp/800/98/final), 2007.
