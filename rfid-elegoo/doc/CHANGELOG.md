# Changelog

## 0.1.2

- Corrected the decoder's marker-relative byte offsets to the published EPC-256 / OpenRFID
  layout (material @ marker+6, sub-type @ +10, RGB888 color @ +14, diameter @ +17, weight @
  +19). The 0.1.x decoder used the wrong offsets, never read the sub-type, and read two stray
  "temperature" fields that Elegoo's layout does not carry. The decode now matches the spec
  byte-for-byte and the regression tests pass (they had been xfail'd against the prior
  mismatch). Behaviour-only; no manifest/format change.

## 0.1.1

- Corrected the factory-tag finding after a full hardware investigation on a real U1
  (2026-06-29). The earlier "ISO 14443-4 / IsoDep, locked, needs an A5 reader" conclusion
  was wrong: Elegoo's data is OPEN NTAG213 memory (no key), and the real blocker is that the
  U1's reader gets no RF wake-up response from the factory Feiju tag, across the entire
  reader register space (receiver + transmitter), both coils, and a 1cm gap, all validated
  by a real BCC-checked UID. M1/NTAG read fine; phones and the Elegoo Canvas read the Elegoo.
  So it is a U1 reader antenna/coupling limit, not a decode or plugin gap, and not software
  fixable on the U1 as far as we can reach. Doc rewritten with the full findings, the working
  workaround (OpenSpool NTAG on the opposite side of the spool ring), and a community call to
  action (run the `u1-enhanced-rfid/tools/` sweep, report firmware + tag chip/UID). No code
  change; the decoder remains correct for the published NTAG layout.

## 0.1.0

- First release. Clean-room Elegoo (Centauri) decoder: finds the plaintext raw-page
  EPC-256 block by Elegoo's manufacturer signature and decodes material, sub-type,
  color, diameter, and weight into the shared `rfid_data.json`. No vendor key. Elegoo
  tags carry no temperatures. Read-only. Experiment channel.
- HIL finding (2026-06-29, junior U1): real Elegoo Centauri spools are ISO 14443-4 /
  IsoDep (Shanghai Feiju Microelectronics), not the documented NTAG213. The U1 reader
  cannot read IsoDep yet, so this decoder is DORMANT on current hardware; it targets the
  published NTAG EPC-256 layout. Blocked on an ISO 14443-4 reader capability.
