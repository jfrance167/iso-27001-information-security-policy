# Security and Responsible-Use Guidance

This project is a computational teaching model. It does not need elevated
privileges and does not inspect, delete, recover, or overwrite host files.

## Safe scope

- Use only synthetic data created for the lab.
- Write generated reports and simulated images only to locations you control.
- Do not use the code to examine another person's media or files.
- Do not treat a simulated result as evidence about a physical device.

## Physical-media warning

File deletion, formatting, shredding, and recovery tools can permanently
destroy data. If this experiment is extended to hardware:

1. Never use the operating-system drive or a drive containing valuable data.
2. Use a disposable external device dedicated to the experiment.
3. Obtain explicit authorization from the device owner.
4. Disconnect unrelated external storage before destructive steps.
5. Verify the exact device identifier and capacity before every operation.
6. Image the device and analyze a copy; keep the original unchanged.
7. Record acquisition and image hashes and maintain an evidence log.
8. Stop if a command targets an unexpected path or device.

This repository intentionally provides no command that wipes, formats, mounts,
or performs raw I/O against a physical device.

## Reporting a vulnerability

Follow the repository-level `SECURITY.md`. Do not include sensitive data,
credentials, personal files, or private forensic evidence in a report.
