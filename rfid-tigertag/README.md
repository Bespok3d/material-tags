# rfid-tigertag

Clean-room decoder for **TigerTag** filament tags - an open NTAG21x raw-page block (no key),
anchored on TigerTag's magic header.

- **Status:** experiment. No key, no reader change (raw-page payload parser).
- **Decodes:** color (RGBA), diameter (from the diameter code), nozzle min/max + bed +
  drying temperatures, weight, and the product id (surfaced as SKU).
- **Gotchas:**
  - Both magic variants are handled: standard `0x5BF59264` and Plus `0xBC0FCB97`; the
    blank/init marker `0x6C41A2E1` is declined.
  - **Brand and material stay as numeric ids.** TigerTag's id->name tables are **GPLv3**, so
    vendoring them would force this plugin to GPL; it keeps the ids numeric instead. (TigerTag
    also runs a free public lookup API - a future optional online name-resolution could use it
    without bundling any GPL data.)
  - Offsets follow the official TigerTag-RFID-Guide spec (NTAG213, big-endian).
- Requires the RFID Spool Reader (`rfid-ntag`, auto-installed via `require: rfid-service`).

In-app doc: [doc/README.md](doc/README.md) - Changelog: [doc/CHANGELOG.md](doc/CHANGELOG.md)
