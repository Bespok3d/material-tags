# rfid-opentag

Clean-room decoder for **OpenTag3D** (queengooborg) filament tags - a big-endian binary
block inside an NDEF record.

- **Status:** experiment. No key, no reader change (NDEF binary payload parser).
- **Decodes:** manufacturer, material + modifiers, color (RGBA), diameter, weight, and
  print/bed temperatures (incl. the extended min/max temps).
- **Gotcha:** only claims NDEF records of MIME type `application/opentag3d`, so it never
  collides with OpenSpool or the generic JSON decoder. Offsets are payload-relative,
  big-endian, taken verbatim from the public OpenTag3D spec (temps stored as degC/5,
  diameter in micrometres).
- Requires the RFID Spool Reader (`rfid-ntag`, auto-installed via `require: rfid-service`).

In-app doc: [doc/README.md](doc/README.md) - Changelog: [doc/CHANGELOG.md](doc/CHANGELOG.md)

## Support this project

Bespok3d is built and maintained in the open, on stock printer firmware. If it saved you an
afternoon, you can [buy me a coffee](https://buymeacoffee.com/unlucio).
