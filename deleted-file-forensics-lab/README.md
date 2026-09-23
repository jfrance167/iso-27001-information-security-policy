# Deleted-File Forensics Lab

A safe, reproducible implementation inspired by the Science Buddies project
"Is a Deleted File Really Gone?" The lab models a small block device in memory,
deletes synthetic files under controlled conditions, attempts signature-based
recovery, and verifies recovered content with SHA-256.

No real disk, Recycle Bin, personal file, or operating-system storage is read,
deleted, or overwritten. The measured results describe the model only; they are
not presented as physical-HDD measurements.

## Research question

How does the fraction of a deleted file's clusters that are subsequently
overwritten affect whether the file can be located and whether its original
contents can be recovered exactly?

## What the experiment models

- Fixed-size storage clusters and a bounded allocation map
- Directory metadata for active and recycled files
- Recycle Bin emptying, which releases clusters without clearing their bytes
- File carving from a recognizable header after metadata is removed
- Controlled deterministic overwriting of 25%, 50%, 75%, or 100% of released
  clusters
- Exact recovery verification using SHA-256
- Partial recovery measurement using matching byte positions

The format is deliberately educational, not an implementation of NTFS, FAT,
ext4, APFS, or another production filesystem.

## Requirements

- Python 3.10 or newer
- No third-party runtime packages

## Run the completed experiment

From this directory:

```powershell
python forensic_lab.py experiment `
  --trials 25 `
  --seed 20260923 `
  --output reports/results.csv `
  --summary reports/summary.json
```

This performs 450 trials: three synthetic file types, six deletion/overwrite
conditions, and 25 repetitions per condition. The committed CSV and JSON files
were produced by that exact command.

Create a harmless 16 KiB simulated image for hex-editor inspection:

```powershell
python forensic_lab.py image reports/example-volume.bin
```

Generated `.bin` and `.img` images are ignored by Git because they are derived
artifacts. They contain only synthetic bytes.

## Test the implementation

```powershell
python -m unittest discover -s tests -v
```

The 17 tests cover geometry limits, allocation, metadata deletion, carving,
hash verification, complete overwriting, repeatability, result aggregation,
report output, and both command-line workflows.

## Results

| Condition | Trials | Located | Exact | Mean matching bytes |
|---|---:|---:|---:|---:|
| File in Recycle Bin | 75 | 100.0% | 100.0% | 100.0% |
| Recycle Bin emptied, no overwrite | 75 | 100.0% | 100.0% | 100.0% |
| 25% of clusters overwritten | 75 | 66.67% | 0.0% | 47.64% |
| 50% of clusters overwritten | 75 | 49.33% | 0.0% | 22.91% |
| 75% of clusters overwritten | 75 | 28.0% | 0.0% | 6.35% |
| 100% of clusters overwritten | 75 | 0.0% | 0.0% | 0.0% |

An item can be *located* while still failing hash verification. That distinction
is important: finding recognizable remnants is not the same as recovering an
intact file.

See [LAB_REPORT.md](LAB_REPORT.md) for the complete hypothesis, variables,
method, results, interpretation, limitations, and conclusion.

## Project layout

```text
deleted-file-forensics-lab/
|-- forensic_lab.py          storage model, recovery code, and CLI
|-- LAB_REPORT.md            complete scientific-method report
|-- README.md                usage and results summary
|-- SECURITY.md              safety and evidence-handling guidance
|-- reports/
|   |-- results.csv          all 450 trial records
|   `-- summary.json         grouped results
`-- tests/
    `-- test_forensic_lab.py 17 standard-library tests
```

## Responsible extension to physical media

Do not adapt this lab to a computer's internal drive. A physical follow-up
should use a disposable external drive containing only synthetic files, obtain
written authorization, create a forensic image, preserve the original, record
cryptographic hashes, and perform recovery against the copy. Storage behavior
varies by filesystem, operating system, device firmware, and SSD TRIM support.

## References

- Sandra Slutz, [Is a Deleted File Really Gone?](https://www.sciencebuddies.org/science-fair-projects/project-ideas/CompSci_p061/computer-science/is-a-deleted-file-really-gone), Science Buddies, last edited July 23, 2025.
- NIST SP 800-86, [Guide to Integrating Forensic Techniques into Incident Response](https://csrc.nist.gov/pubs/sp/800/86/final).
