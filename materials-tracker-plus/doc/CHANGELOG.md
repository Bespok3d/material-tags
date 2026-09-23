# Changelog

## 0.1.5 - 2026-09-23

- Factory Elegoo spools are identified now. The collection requires `rfid-elegoo` 0.1.5 or newer,
  which reads material, colour, nozzle temperature range, diameter and weight from factory Elegoo
  (Centauri) tags. It was verified field by field against a real factory spool and its label, and
  that spool was read on a real U1 (one printer so far). Earlier versions followed ELEGOO's
  published byte table, which factory tags do not match, and would have shown a wrong diameter and
  weight. Loading takes one extra step: Elegoo's tag is small and sits further out than the U1's
  reader reaches for such a tag, so hold the tag against the centre of the spool holder while the filament feeds, then
  mount the spool. The Elegoo plugin's own page has the steps.
- The collection now requires the RFID Spool Reader (`rfid-ntag`) 0.1.15 or newer. Factory Elegoo
  tags are smaller than the area the reader asks for, and older versions threw the whole read away.
- Anycubic and Creality spools now report their diameter in the same unit as every other brand.
  The collection requires `rfid-anycubic` 0.2.2 and `rfid-creality` 0.2.2 or newer, which report
  `175` for 1.75 mm instead of `1.75`.
- The collection page lists what it installs as a plain list. The table it used before showed up in
  the app as raw text.

## 0.1.4 - 2026-09-13

- Fixed the manifest file publisher field. No functional changes in the plugin.

## 0.1.3 - 2026-09-12

- Creality CFS spools decode fully now. The stack requires `rfid-creality` 0.2.0 or newer, which
  reads material type, filament diameter, hotend temperature range, color, and weight, verified
  against a real Creality tag. Type, diameter, and temperatures are resolved from the tag's
  material id (from Creality's own slicer profiles; the tag does not carry them). You paste your
  two Creality keys into the plugin's config; without them a Creality spool falls back to UID-only
  tracking. `rfid-creality` 0.2.0 is a release candidate: confirmed against one real tag so far,
  and the tag's stored color did not match the physical filament on that sample (a factory write
  error), so the reported color may not always be accurate.
- Anycubic ACE spools decode fully now. The stack requires `rfid-anycubic` 0.2.0 or newer, which
  reads SKU, brand, material, color, diameter, length, weight, and temperatures (including bed
  minimum) straight off the tag, confirmed against real tags across three product lines. This
  brings the stack in line with the "All the Tags" collection, which picked up the same Anycubic
  release earlier.

## 0.1.2 - 2026-08-13

- QIDI spools now read. The new QIDI decoder comes with the stack and needs no key from you: QIDI
  leaves its tags on the factory default key every blank card ships with. A QIDI tag carries the
  material, the sub-type, and the colour, and nothing else, so weight, diameter, temperatures, and
  date still come from your slicer profile or from Spoolman.

## 0.1.1 - 2026-07-27

- Say what the Bambu and Creality decoders actually fall back to without a key: the tag's own ID, not
  the spool's serial number.

## 0.1.0 - 2026-07-27

- First release of the "Materials Tracker Plus" collection: the whole RFID tag-reading stack (reader,
  all eight decoders, Spoolman tracking) plus AFC Lite and the U1 G-code preview colours, installed
  in one batch with a single service restart.
- Experiment channel until the full read -> decode -> track stack is verified end to end on a real
  printer.
