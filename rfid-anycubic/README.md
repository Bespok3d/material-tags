# rfid-anycubic

Clean-room decoder for **Anycubic ACE** filament tags - a plaintext (no key) NTAG21x block,
anchored on the `7B 00 65 00` magic (version `0x65`).

- **Status:** experiment, **PARTIAL by design**. No key, no reader change (raw-page payload parser).
- **Decodes:** brand, material, and nozzle/bed temperatures (little-endian).
- **BIG GOTCHA - color, diameter, and weight are NOT decoded yet.** The public reverse
  engineering (DnG-Crafts/ACE-RFID, SimplyPrint) **disagrees** on the SKU field length
  (12 vs 16), the color byte order (ARGB vs ABGR at page 20), and whether page 31 is weight -
  and no real tag dump has been published to settle them. Guessing would show a wrong color or
  a 10x-off weight, so those fields are left at their defaults until a tester captures a real
  ACE tag. The agreed fields (brand/material/temps) decode now.
  - **Have an ACE spool?** Tap it on a phone (NFC Tools / NXP TagInfo) and share the raw page
    dump - that pins the three disputed fields and unlocks the rest.
- Requires the RFID Spool Reader (`rfid-ntag`, auto-installed via `require: rfid-service`).

In-app doc: [doc/README.md](doc/README.md) - Changelog: [doc/CHANGELOG.md](doc/CHANGELOG.md)
