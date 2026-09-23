# Lab Report: Is a Deleted File Really Gone?

## Abstract

This experiment tested how deletion metadata and later overwriting affect file
recovery. To avoid risking a real disk, a Python model represented a bounded
block device with 128-byte clusters. Three synthetic file types were placed on
fresh simulated volumes, deleted under six conditions, and recovered using
directory metadata or signature carving. Twenty-five repetitions per file type
and condition produced 450 trials. Files in the Recycle Bin and files deleted
without overwriting were recovered exactly in every trial. After 25%, 50%, and
75% controlled overwriting, files were located in 66.67%, 49.33%, and 28.0% of
trials, respectively, but none passed SHA-256 verification. Complete
overwriting prevented all recovery. The results support the hypothesis that
deletion alone removes references rather than content, while subsequent writes
progressively destroy recoverable bytes. These findings apply to this model,
not directly to any physical filesystem or storage device.

## Research question

How does the fraction of a deleted file's clusters that are subsequently
overwritten affect whether the file can be located and whether its original
contents can be recovered exactly?

## Background

A filesystem normally maintains metadata connecting a filename to storage
locations. Moving a file to a Recycle Bin preserves enough metadata to restore
it. Emptying the bin may remove that reference and mark the underlying space as
available without immediately clearing every byte. A forensic carving process
can search unallocated space for recognizable structure even when directory
metadata is gone.

Recovery and integrity are different outcomes. A tool might find a header and
produce a file while some of its clusters contain newer data. This experiment
therefore records both whether an object was located and whether its SHA-256
digest matches the original.

The Science Buddies project recommends an external HDD because experiments
with deletion and shredding can destroy data. This implementation substitutes
a documented in-memory model. NIST SP 800-86 describes a broader forensic
process of collection, examination, analysis, and reporting. The lab follows
that structure using synthetic evidence and repeatable measurements.

## Hypothesis

Files will remain exactly recoverable while their bytes are unchanged, even
after directory metadata is removed. Increasing the overwritten fraction will
reduce both the probability of locating a file and the fraction of original
bytes recovered. A completely overwritten file will not be recoverable.

## Variables

### Independent variable

Deletion and overwrite condition:

- file retained in the simulated Recycle Bin;
- Recycle Bin emptied with no overwriting;
- 25% of allocated clusters overwritten;
- 50% of allocated clusters overwritten;
- 75% of allocated clusters overwritten; or
- 100% of allocated clusters overwritten.

### Dependent variables

- File located or not located
- Exact SHA-256 match or mismatch
- Number and ratio of bytes matching the original at the same positions

### Controlled variables

- Python implementation and host computer
- 128-byte clusters and 128 clusters per fresh volume
- Contiguous initial allocation
- Synthetic text, PNG-like, and PDF-like payloads
- Twenty-five trials per file type and condition
- Deterministic experiment seed `20260923`
- Same header-based carving algorithm and SHA-256 verification

## Materials

- Windows computer
- Python 3.13.7
- `forensic_lab.py`
- `tests/test_forensic_lab.py`
- Synthetic evidence returned by `sample_files()`
- CSV and JSON report outputs

No external drive, personal data, raw device, elevated privilege, or recovery
software was used.

## Model design

The volume contains 128 fixed-size clusters. A synthetic file is stored as:

```text
magic | filename length | payload length | SHA-256 | filename | payload
```

The first available contiguous run is allocated. Deleting a directory entry
marks its clusters free but leaves their bytes unchanged. Controlled overwrite
selects the requested fraction of those clusters using a seeded SHA-256 ranking
generator and replaces their contents with nonzero synthetic noise.

The carver inspects each cluster boundary for the four-byte `DFL1` marker. If a
valid header remains, it reconstructs the stated number of bytes and compares
the recovered SHA-256 digest with the digest embedded before deletion. For the
experiment only, the original fixture is also retained so matching byte
positions can be counted.

## Procedure

1. Define three deterministic synthetic payloads: 2,048-byte text, 4,096-byte
   PNG-like data, and 3,072-byte PDF-like data.
2. Create a fresh simulated volume for every trial.
3. Write one fixture and record its SHA-256 digest.
4. Apply one deletion condition.
5. For overwrite conditions, select and replace the required percentage of the
   file's released clusters using the controlled seed.
6. Recover a recycled file using directory metadata or scan every cluster for
   deleted file signatures.
7. Record location, exact hash match, matching bytes, and recovery method.
8. Repeat each combination 25 times.
9. Save every trial to `reports/results.csv` and grouped results to
   `reports/summary.json`.
10. Run the 17 automated tests.

The exact experiment command was:

```powershell
python forensic_lab.py experiment `
  --trials 25 `
  --seed 20260923 `
  --output reports/results.csv `
  --summary reports/summary.json
```

## Results

Each row below combines three file types and 25 repetitions, for 75 trials per
condition.

| Condition | Located | Exact | Mean matching byte ratio |
|---|---:|---:|---:|
| Recycle Bin | 75/75 (100.0%) | 75/75 (100.0%) | 1.0000 |
| Emptied, no overwrite | 75/75 (100.0%) | 75/75 (100.0%) | 1.0000 |
| 25% overwritten | 50/75 (66.67%) | 0/75 (0.0%) | 0.4764 |
| 50% overwritten | 37/75 (49.33%) | 0/75 (0.0%) | 0.2291 |
| 75% overwritten | 21/75 (28.0%) | 0/75 (0.0%) | 0.0635 |
| 100% overwritten | 0/75 (0.0%) | 0/75 (0.0%) | 0.0000 |

All 17 automated tests passed. The raw 450-row dataset is committed so each
aggregate can be independently recalculated.

## Analysis

The Recycle Bin condition recovered every file through preserved directory
metadata. After the bin was emptied, directory metadata was unavailable, but
the carving marker and payload remained unchanged; carving therefore recovered
all files exactly.

Any nonzero overwrite condition produced zero exact hashes. This is expected:
changing even one bit changes the SHA-256 digest, and the experiment overwrote
at least one complete cluster. Some damaged objects remained locatable because
their header cluster survived. At 25% overwriting, 66.67% were located, but their
mean matching-byte ratio was only 47.64% when unrecovered files were counted as
zero. At 75%, only 28.0% could still be located and the mean matching ratio
fell to 6.35%.

The fall in location rate is tied to whether the first cluster survived seeded
selection. The decline in matching bytes reflects corruption of later payload
clusters. Complete overwriting removed both the marker and payload, so no file
was located.

## Conclusion

The results support the hypothesis. In the model, deleting metadata did not
erase content, so unchanged deleted files remained exactly recoverable through
carving. Subsequent overwriting progressively reduced recoverability. A file
that could be located after overwriting was still not an intact recovery, as
shown by the failed SHA-256 checks. Complete overwriting prevented recovery.

The correct answer to “Is a deleted file really gone?” is therefore conditional:
deletion alone may leave recoverable content, but recoverability depends on
whether the storage has been reused and on device-specific behavior.

## Limitations

- This is a computational model, not a physical-drive experiment.
- The custom format and carver are simpler than real filesystems and forensic
  tools.
- Files are allocated contiguously; real files can be fragmented.
- The model overwrites whole clusters and does not simulate caches, journals,
  copy-on-write snapshots, wear leveling, garbage collection, or SSD TRIM.
- Physical recovery outcomes vary with filesystem, OS, controller, firmware,
  storage medium, elapsed time, and workload.
- Matching bytes use the known fixture as experimental ground truth, which an
  investigator would not always possess.

## Future work

A separately authorized follow-up could use a disposable external HDD and
synthetic fixtures. The drive should first be imaged, hashed, and preserved;
analysis should occur only on copies. Results could compare filesystems,
fragmentation, file sizes, time after deletion, and controlled write volume.
Such work must never target a system drive or media containing valuable data.

## References

1. Sandra Slutz, “Is a Deleted File Really Gone?”, Science Buddies, last edited
   July 23, 2025. <https://www.sciencebuddies.org/science-fair-projects/project-ideas/CompSci_p061/computer-science/is-a-deleted-file-really-gone>
2. Karen Kent, Suzanne Chevalier, Tim Grance, and Hung Dang, *Guide to
   Integrating Forensic Techniques into Incident Response*, NIST SP 800-86,
   August 2006. <https://csrc.nist.gov/pubs/sp/800/86/final>
