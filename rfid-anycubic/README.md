# rfid-anycubic

Clean-room decoder for **Anycubic ACE** filament tags, a plaintext (no key) Mifare Ultralight
C block, anchored on a `7B 00` magic prefix followed by a one-byte format version (`0x64` or
`0x65` confirmed so far) and a trailing zero.

- **Status:** experiment. Most fields decode; one is still genuinely open.
- **Decodes:** SKU, brand, material, color, nozzle/bed temperatures, diameter, length, and
  weight, confirmed against three independently sourced tags across three product lines
  (PLA+, PLA Spezial, ASA). Print speed decodes when the tag carries it, seen populated on
  one of the three so far.
- **Still open:** the SKU field length (12 vs 16 bytes) has no tag long enough yet to prove
  it either way; a PLA+ Refill spool (`AHPLP<color>-A108`) is the one that would settle it.
  Weight, diameter, and length are confirmed in position but only tested against a standard
  1kg/330m spool so far, a differently sized spool is what would confirm the scale holds
  generally.
  - **Have an ACE spool, especially a Refill pack or an unusual size?** Tap it on a phone
    (NFC Tools / NXP TagInfo) and share the raw page dump, that's what closes out what's left.
- Requires the RFID Spool Reader (`rfid-ntag`, auto-installed via `require: rfid-service`).

In-app doc: [doc/README.md](doc/README.md), Changelog: [doc/CHANGELOG.md](doc/CHANGELOG.md)

## Support this project

Bespok3d is built and maintained in the open, on stock printer firmware. If it saved you an
afternoon, you can [buy me a coffee](https://ko-fi.com/A623L7G).