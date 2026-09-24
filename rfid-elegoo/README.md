# rfid-elegoo

Clean-room decoder for the filament block on **factory Elegoo (Centauri)** spool tags, anchored on
Elegoo's `36 EE EE EE EE` header and manufacturer marker.

- **Status:** experiment. No key, no reader of its own: rfid-ntag's stock `NtagReader` reads the tag
  and hands the pages to this payload parser. Needs rfid-ntag **0.1.15+** (its chunked page reader;
  older versions discard the whole read of this 44-page tag).
- **Decodes:** material, color (RGB888), nozzle temperature range, diameter, weight, UID.
  Verified field by field against a real factory spool (PLA "Sea Green", 1.75 mm, 1 kg,
  190 to 230 C) and its label; that dump is the test fixture.
- **Does not follow ELEGOO's published byte table.** Factory tags are page-aligned (each field on
  its own 4-byte page) and carry a nozzle range the guide omits. The material code is one letter
  per byte in decimal-digit form (`00 80 76 65` = PLA). Sub-type and production date are not
  decoded: nothing confirms them yet.
- **Reads on a U1 only when held near the reader** (2026-09-23, one printer, one spool). Elegoo's
  NTAG-type tag is embedded in the cardboard flange about 35 mm from the centre-hole edge, beyond
  what the U1's reader reaches for NTAG-type tags (a plain NTAG sticker at 35 mm is found but not
  read; at 22.5 mm it reads; Mifare tags read out to 43.5 mm), so a mounted spool is not
  read. Held
  with the tag against the holder centre (while feeding, or with `DETECT_SPOOLS`), it reads in full
  and every field matches the label; the hub then keeps the lane's spool until unload. Permanent
  alternatives in the in-app doc: an OpenSpool sticker at the reader spot, a copy of the Elegoo
  tag's pages `0x10` to `0x18` on a blank NTAG213/215 sticker (confirmed on a U1 with an NTAG215),
  or moving the original tag inward. A factory
  spool has two tags, one per flange, with different UIDs and identical data. The tag is an open
  NFC Type 2 tag (Shanghai Feiju, NTAG213-style memory), not IsoDep.
- Requires the RFID Spool Reader (`rfid-ntag`, auto-installed via `require: rfid-service`).

In-app doc: [doc/README.md](doc/README.md) - Changelog: [doc/CHANGELOG.md](doc/CHANGELOG.md)

## Support this project

Bespok3d is built and maintained in the open, on stock printer firmware. If it saved you an
afternoon, you can [buy me a coffee](https://ko-fi.com/A623L7G).
