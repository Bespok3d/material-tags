# rfid-elegoo

Clean-room decoder for Elegoo's **published NTAG EPC-256** raw-page layout, anchored on
Elegoo's `EE EE EE EE` manufacturer marker.

- **Status:** experiment. No key, no reader change (raw-page payload parser).
- **Decodes:** material, sub-type, color (RGB888), diameter, weight. Elegoo's layout carries
  no temperatures.
- **BIG GOTCHA - factory Centauri spools do NOT read on the U1.** The factory tags are
  **ISO 14443-4 / IsoDep** (Shanghai Feiju), not the NTAG213 the public guide documents, and
  the U1 reader never even RF-wakes them (HIL-confirmed). This decoder is correct for **open /
  user-programmed Elegoo NTAG** tags; the factory IsoDep track is a separate hardware blocker
  (see the repo README "Blocked decoders" and RELAY-A5). Factory spools are trackable UID-only.
- Requires the RFID Spool Reader (`rfid-ntag`, auto-installed via `require: rfid-service`).

In-app doc: [doc/README.md](doc/README.md) - Changelog: [doc/CHANGELOG.md](doc/CHANGELOG.md)
