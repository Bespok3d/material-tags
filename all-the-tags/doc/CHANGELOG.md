# Changelog

## 0.1.2 - 2026-07-30

- The collection page now says what a tag does not fix. Your slicer only syncs to filaments it ships
  itself, so anything else lands on `Generic <material>` with the right colour, and a tag still has to
  resolve to a spool that exists in Spoolman. Two ways to give it one: bind the tag with
  `SH_BIND_CARD_UID CHANNEL={0..3} SPOOL=<id>`, or fill the SKU the tag reports into that filament's
  Article Number. `DETECT_SPOOLS` re-reads every lane when one looks wrong, without a reboot and
  without pulling the spool off the printer.
- Records what was checked on a real printer: on a Snapmaker U1 on stock firmware, with two genuine
  Snapmaker spools, the firmware exposes each card's own hardware UID, and binding that UID makes the
  lane resolve by the card itself, with the Article Number cleared so no SKU match was possible.

## 0.1.1 - 2026-07-26

- Updates the `rfid-bambu` plugin to version 0.2.0, the first stable release.

## 0.1.0 - 2026-06-30

- First release of the "All the Tags" collection: installs the RFID Spool Reader, all eight tag
  decoders (generic NDEF, OpenTag3D, OpenPrintTag, TigerTag, Anycubic, Bambu, Creality, Elegoo), and
  Spoolman tracking together in one batch (a single service restart).
- Experiment channel until the full read -> decode -> track stack is verified end to end on a real
  printer.
