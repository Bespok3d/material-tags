# rfid-qidi

Clean-room decoder for **QIDI** filament spool tags: a Mifare Classic 1K left on the Mifare
**factory default key**, with the whole payload in the first data block of sector 1.

- **Status:** experiment. **No key to supply** and none shipped, no reader change (HW claim
  reader on the factory default key).
- **Decodes:** material, sub-type, and colour.
- **A QIDI tag is tiny.** The card carries three bytes: a material code, a colour code, and a
  manufacturer code. There is no weight, diameter, temperature, date or SKU written on it, so
  those keep coming from your slicer profile or Spoolman.
- **Unknown spool codes still track.** The code tables hold only pairings read off a physical
  spool. A code that is not in them is reported as its number in the log and on the spool,
  never guessed. Wider community lists live at
  [OpenRFID](https://github.com/suchmememanyskill/OpenRFID).
  - **Have a QIDI spool we do not?** Tap it on the printer and share the material/colour codes
    the log prints, and that pairing joins the tables.
- Requires the RFID Spool Reader (`rfid-ntag`, auto-installed via `require: rfid-service`).

In-app doc: [doc/README.md](doc/README.md) - Changelog: [doc/CHANGELOG.md](doc/CHANGELOG.md)

## Support this project

Bespok3d is built and maintained in the open, on stock printer firmware. If it saved you an
afternoon, you can [buy me a coffee](https://buymeacoffee.com/unlucio).
