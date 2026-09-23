# Lab Report: Hacking the Air Gap with an Optical Side Channel

## Abstract

This experiment modeled whether an isolated computer could transmit a small
binary message through controlled screen-brightness changes. A safe Python
simulation framed the synthetic payload `LAB` with a preamble, length field,
and CRC-8 integrity check. It then transmitted the packet through a
display-to-camera channel with inverse-square signal loss and deterministic
sensor noise. Five distances, three brightness contrasts, three bit rates,
three interference levels, and ten repetitions produced 1,350 trials. In a
representative low-contrast condition (3%, 1 bit/s, quiet interference), exact
packet recovery was 100% through 3 m, 80% at 6 m, and 0% at 9 m. Mean bit error
rate rose from 0 at 3 m to 0.0042 at 6 m and 0.1646 at 9 m. These findings
support the hypothesis that physical emanations can cross a network air gap,
while distance, speed, and interference limit reliability. The results are
simulated and must not be presented as measurements of physical equipment or
human perception.

## Research question

How do transmitter-to-receiver distance, screen-brightness contrast, bit rate,
and environmental interference affect packet recovery and bit error rate in a
simulated optical channel from an air-gapped computer?

## Background

An air-gapped computer has no direct wired or wireless connection to an
external network. Network isolation reduces attack surface, but the computer
still interacts with its physical environment through light, sound, heat,
vibration, and electrical power. A controlled change in one of those quantities
can encode binary information that a nearby sensor may detect.

Science Buddies proposes investigating one such quantity and measuring range,
interference tolerance, bit rate, and whether a person would notice the signal.
It lists screen brightness measured by a phone light sensor or lux meter as one
safe option. The project also warns that heat and fan-control methods can damage
hardware.

The BRIGHTNESS research paper describes a display-to-camera optical channel and
reports that received signal strength depends on display contrast, alignment,
and distance. Its optical model predicts signal strength proportional to
`1 / distance²`. It also demonstrates that small screen changes may be detected
by cameras under controlled conditions even when users do not notice them.

This implementation uses those concepts in a transparent mathematical model.
It does not reproduce malware or operate a real covert channel.

## Hypothesis

Packet recovery will decrease and bit error rate will increase as distance,
bit rate, or interference increases. Increasing brightness contrast will
improve recovery. Low-contrast settings may remain machine-detectable in the
model even though a physical human-perception claim cannot be made without a
proper human-subject experiment.

## Variables

### Independent variables

- Distance: 0.5, 1.5, 3, 6, and 9 m
- Screen-brightness contrast: 1%, 3%, and 5%
- Bit rate: 1, 5, and 10 bits/s
- Interference: quiet, moderate, and high deterministic sensor noise

### Dependent variables

- Packet recovered with valid framing and CRC-8
- Number of incorrect bits
- Bit error rate
- Model signal-to-noise ratio

### Controlled variables

- Synthetic payload `LAB`
- Packet format and CRC algorithm
- Inverse-square attenuation equation
- Deterministic SHA-256-derived noise generator
- Base noise values for each interference category
- Experiment seed `20260923`
- Ten trials per parameter combination

## Materials

- Computer capable of running Python 3.10 or newer
- `optical_channel_lab.py`
- `tests/test_optical_channel_lab.py`
- No camera, microphone, phone, malware, network connection, personal data, or
  third-party Python package

## Model design

The transmitter builds this packet:

```text
8-bit preamble | 8-bit payload length | payload | 8-bit CRC
```

Each zero is transmitted as a negative displacement from the decision
threshold and each one as a positive displacement. The received signal
amplitude is:

```text
signal amplitude = contrast percent / distance²
```

Quiet, moderate, and high interference use increasing noise levels. Model noise
also grows with the square root of bit rate, representing less observation time
per bit. Every noise sample is derived deterministically from the experiment
seed and sample index, so the dataset is exactly reproducible.

The receiver compares each measurement with zero, reconstructs the bytes, and
accepts a packet only when the preamble, declared length, and CRC are all valid.
Contrast labels are descriptive model bands; they are not measurements of what
a person can see.

## Procedure

1. Define the synthetic three-byte payload `LAB`.
2. Add a preamble, length byte, and CRC-8 to create a 48-bit packet.
3. Select one distance, contrast, bit rate, and interference level.
4. Calculate received optical amplitude using inverse-square attenuation.
5. Convert each sent bit into one of two amplitudes around the receiver's
   decision threshold.
6. Add a deterministic noise sample based on the scenario seed.
7. Decode every sample as zero or one.
8. Reconstruct the packet and verify its framing and CRC.
9. Record bit errors, bit error rate, packet recovery, signal-to-noise ratio,
   and the descriptive contrast band.
10. Repeat each of the 135 parameter combinations ten times.
11. Save 1,350 raw trials to `reports/results.csv` and 135 grouped scenarios to
    `reports/summary.json`.
12. Run the 19 automated tests.

The exact experiment command was:

```powershell
python optical_channel_lab.py experiment `
  --trials 10 `
  --seed 20260923 `
  --output reports/results.csv `
  --summary reports/summary.json
```

## Results

The following controlled slice holds contrast at 3%, bit rate at 1 bit/s, and
interference at quiet. Each row contains ten trials.

| Distance | Packets recovered | Mean BER | Mean model SNR |
|---:|---:|---:|---:|
| 0.5 m | 10/10 (100%) | 0.000000 | 670.820 |
| 1.5 m | 10/10 (100%) | 0.000000 | 74.536 |
| 3.0 m | 10/10 (100%) | 0.000000 | 18.634 |
| 6.0 m | 8/10 (80%) | 0.004167 | 4.658 |
| 9.0 m | 0/10 (0%) | 0.164583 | 2.070 |

At 6 m, quiet interference, and 1 bit/s, contrast also changed the outcome:

| Contrast | Packets recovered | Mean BER | Descriptive band |
|---:|---:|---:|---|
| 1% | 0/10 (0%) | 0.208333 | Very low contrast |
| 3% | 8/10 (80%) | 0.004167 | Low contrast |
| 5% | 10/10 (100%) | 0.000000 | Higher contrast |

All 19 tests passed. The complete 1,350-row dataset is committed for independent
recalculation of every group.

## Analysis

The representative distance results follow the hypothesis. With fixed
contrast, speed, and interference, model SNR fell sharply as distance increased.
Perfect recovery through 3 m gave way to occasional CRC failures at 6 m and no
valid packets at 9 m. The receiver still decoded many individual bits at 9 m,
but a 16.46% mean BER made the complete 48-bit packet invalid in every trial.

The contrast comparison shows the expected tradeoff. At 6 m, raising contrast
from 1% to 5% increased packet recovery from 0% to 100%. Higher contrast creates
a stronger sensor signal but may be more noticeable in a physical experiment.
This implementation does not claim a universal visibility threshold. The
paper's low-contrast findings depended on controlled equipment, ambient light,
observers, and display content.

Higher modeled interference and bit rate both reduced performance because they
increased noise relative to the attenuated signal. This illustrates why range,
throughput, reliability, and covertness cannot all be maximized at once.

## Conclusion

The hypothesis was supported within the model. A network air gap prevented
ordinary network transfer but did not eliminate the possibility of a physical
side channel. Reliable optical communication depended on sufficient contrast
and signal-to-noise ratio. Distance, interference, and faster transmission
progressively increased errors, while CRC checking prevented corrupted packets
from being mistaken for intact data.

The defensive lesson is that air-gapped systems require layered physical and
procedural controls in addition to network isolation.

## Defensive recommendations

- Restrict phones, cameras, and unapproved sensors near sensitive displays.
- Control physical sight lines, windows, and surveillance-camera placement.
- Use privacy filters or enclosures where appropriate.
- Monitor trusted display paths for unexplained brightness or color modulation.
- Restrict removable media and require approved transfer stations.
- Maintain access logs and separate duties for sensitive areas.
- Treat the air gap as one control in a layered architecture, not a guarantee.

## Limitations

- This is a mathematical simulation, not a physical side-channel measurement.
- Inverse-square attenuation is a simplified geometry with perfect alignment.
- The model does not simulate camera frame timing, rolling shutters, automatic
  exposure, compression, perspective, screen refresh, reflections, or ambient
  light drift.
- Noise categories are controlled model parameters, not calibrated lux values.
- The visibility bands are labels, not human-subject observations.
- Only one short synthetic payload and one binary modulation method are used.
- Physical results depend on the exact display, sensor, distance, angle,
  lighting, content, and receiver algorithm.

## Future work

A separately authorized classroom follow-up could display only synthetic black
and gray patterns and measure them with a phone light sensor at controlled
distances. It should record ambient light, angle, sampling rate, screen model,
and informed observations. It must not use malware, private data, concealed
recording, heat stress, or unapproved equipment.

## References

1. Ben Finio, “Hacking the Air Gap: Stealing Data from a Computer that isn't
   Connected to the Internet,” Science Buddies.
   <https://www.sciencebuddies.org/science-fair-projects/project-ideas/Cyber_p006/cybersecurity/air-gap-computer-hacking>
2. Mordechai Guri, Dima Bykhovsky, and Yuval Elovici, “BRIGHTNESS: Leaking
   Sensitive Data from Air-Gapped Workstations via Screen Brightness,” 2020.
   <https://arxiv.org/abs/2002.01078>
