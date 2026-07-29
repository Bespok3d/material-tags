# rfid-generic-ndef

Best-effort decoder for **plain JSON over NDEF** filament tags that carry no `protocol`
field. Maps recognizable JSON keys into the shared `rfid_data.json`.

- **Status:** experiment. No key, no reader change (NDEF JSON payload parser).
- **Decodes:** whatever the tag's JSON exposes (material, color, temps, ...).
- **Gotcha:** it deliberately **declines JSON that has a `protocol` field**, so it never
  shadows OpenSpool or a protocol-specific mapper - those win first. It is the lowest-priority
  catch-all for untagged JSON tags.
- Requires the RFID Spool Reader (`rfid-ntag`, auto-installed via `require: rfid-service`).

In-app doc: [doc/README.md](doc/README.md) - Changelog: [doc/CHANGELOG.md](doc/CHANGELOG.md)

## Support this project

Bespok3d is built and maintained in the open, on stock printer firmware. If it saved you an
afternoon, you can [buy me a coffee](https://buymeacoffee.com/unlucio).
