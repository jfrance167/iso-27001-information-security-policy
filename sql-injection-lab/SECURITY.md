# Security and Responsible Use

This project is an educational, local SQL-injection prevention simulation. It
is not a penetration-testing tool and must not be deployed as a production
authentication service.

## Permitted use

- Run the lab against its included in-memory database and fictional records.
- Extend the tests with additional synthetic inputs.
- Study how parameterized queries keep input separate from SQL instructions.

## Prohibited use

- Do not test websites, databases, accounts, or networks without explicit
  authorization from their owner.
- Do not insert real credentials, personal information, or production data.
- Do not expose a deliberately vulnerable service to a network.
- Do not use the sample inputs to access, modify, or delete third-party data.

## Design controls

- The legacy path is a bounded behavioral model; it does not execute SQL.
- The real SQLite path accepts input only through parameter placeholders.
- The database exists only in memory and contains synthetic `.invalid` records.
- Reports store scenario labels and outcomes, not supplied payloads or
  passwords.

Report unexpected security behavior through the repository's root security
policy rather than publishing exploit details with sensitive data.
