# Security and Responsible Use

This project is an educational, local-only demonstration. It must be used only
with the bundled synthetic passwords or other test values you created and are
authorized to analyze.

The tool has no networking, login automation, credential ingestion, or remote
target support. Do not modify it to guess passwords for accounts, devices,
websites, files, or systems you do not own and have explicit authorization to
test. Never place a real password in source code, command history, screenshots,
test output, or this repository.

The deliberately small PBKDF2 work factor used by the demo keeps classroom
runtime practical and is not a production recommendation. Production systems
must use current, reviewed password-storage guidance, unique salts, an
appropriately expensive password-hashing scheme, blocklists, and online rate
limiting.
