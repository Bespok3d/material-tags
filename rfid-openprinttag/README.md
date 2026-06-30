# rfid-openprinttag

Clean-room decoder for the **OpenPrintTag** (prusa3d) data format - an open CBOR payload on
an NDEF record.

- **Status:** experiment. No key, no reader change (NDEF + a vendored pure-python CBOR reader).
- **Decodes:** material/brand names, color (RGB/RGBA), diameter, weight, manufacture date,
  and nozzle/bed/drying temperatures.
- **Gotchas:**
  - We decode the **payload, not the hardware**. Prusa's own factory spools use **ISO-15693**
    tags the U1's 14443A reader cannot read; this targets OpenPrintTag payloads written onto a
    standard **NTAG21x** (which the U1 reads fine).
  - Claims only NDEF records of MIME type `application/vnd.openprinttag` (declines everything
    else). The CBOR reader is a minimal vendored subset (`cbor_min.py`); it rejects semantic
    tags, which OpenPrintTag does not use.
  - Verified against the public spec **and** a real captured Prusament payload.
- Requires the RFID Spool Reader (`rfid-ntag`, auto-installed via `require: rfid-service`).

In-app doc: [doc/README.md](doc/README.md) - Changelog: [doc/CHANGELOG.md](doc/CHANGELOG.md)
