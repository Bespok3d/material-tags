# Changelog

## 0.1.5

- Factory Elegoo spools now read on a Snapmaker U1. On a real U1 (2026-09-23) a factory Elegoo
  PLA spool was identified as PLA, `#09C299`, 190 to 230 C, 1.75 mm, 1000 g, matching its label.
  That was the spool's second tag, so the layout now holds on two physical tags.
- It needs one extra step when loading. Elegoo's tag is small and sits inside the cardboard about
  35 mm from the spool's centre hole, further out than the U1's reader reaches for a tag that
  small, so a spool sitting on its holder is not read. Hold the tag against the centre of the holder
  while the filament feeds, then mount the spool; the lane keeps it until the filament is unloaded.
  The in-app doc has the steps, plus other ways to get a tag where the reader looks: an OpenSpool
  sticker at the reader spot, a copy of the Elegoo tag on a blank sticker (confirmed on a U1: it
  keeps Elegoo's own data under the sticker's UID), moving the original tag, and what to watch for
  when respooling or using an external spool holder.
- Removed this plugin's own tag reader. The U1 reads a factory Elegoo tag with the RFID Spool
  Reader's standard NTAG reader, like any other NTAG, and hands the pages to this decoder. The
  plugin's reader claimed every other card type on the reader, which could have taken tags meant
  for other decoders; it now registers nothing on the reader at all.
- Needs RFID Spool Reader 0.1.15 or newer. A factory Elegoo tag is smaller than the area the reader
  asks for, and older versions threw the whole read away. The plugin logs a warning at startup when
  the installed reader is too old.

## 0.1.4

- The decoder now reads factory Elegoo spool tags correctly. It was checked field by field
  against the complete memory of a real factory spool (PLA "Sea Green", 1.75 mm, 1 kg, 190 to
  230 C, all from its label), and that memory is now the test fixture.
- Every field offset changed. Earlier versions followed the byte table in ELEGOO's published
  guide, which packs the fields byte against byte. Factory tags follow the guide's own alignment
  note instead: each field starts on its own 4-byte page. On the real spool 0.1.3 would have
  reported material as unreadable, diameter as 39423 and weight as 190 g, flagged as an official
  spool.
- Added the nozzle temperature range. Factory tags carry it even though the guide does not
  document it; 0.1.2 was wrong to remove it.
- Material is now decoded the way factory tags store it: one letter per byte, each byte's hex
  digits being the letter's decimal ASCII code (`00 80 76 65` = PLA). A code that does not come
  out as capital letters is left blank instead of shown as garbage.
- Stopped decoding the sub-type. The sample spool has none, and the guide shows two different
  encodings for it, so there is nothing to check a decode against yet.
- The block must now start on a page boundary, which every real tag does, so a stray signature
  in unrelated data is declined.
- The parser's log line now carries the UID and every decoded field, so a tester's log is enough
  to check a new spool against its label.
- Docs corrected: the factory tag is an open NFC Type 2 tag (NTAG213-style memory), not a locked
  IsoDep chip, and no U1 has read one yet.

## 0.1.3

- Diagnostic build, for a tester with a real Elegoo spool. It changes what the reader records,
  not what the decoder decides, so no decode behaviour changes.
- The reader asked `read_nfc_type2_pages` for all 32 pages in one call. That driver performs its
  physical reads in full 4-page groups and discards every byte already collected inside a call
  the moment any group in it fails, so a chip that answers its first pages and then stops
  reported `FM175XX_CARD_READ_ERR` (-29) with zero bytes and told us nothing about where it
  stopped. The reader now walks the tag one native chunk per call, logs each chunk's start page,
  error and byte count, and keeps the pages that did come back. This is the same failure
  rfid-ntag 0.1.15 describes and fixes for its own NtagReader. The walk also runs past the 45
  pages of an NTAG213, because where it stops is itself the measurement we are after.
- The SELECT-phase log line read a name-mangled private attribute of the reader,
  `_Fm175xxReader__picc_a`. Snapmaker's class is spelled `FM175XXReader`, so the real mangled
  name is `_FM175XXReader__picc_a` and the lookup could only ever return nothing: every tap
  logged `SAK=0x-1`, the one fact the line exists to capture. It now reads the public
  `selected_card_sak`, `selected_card_atqa` and `selected_card_uid` accessors that rfid-ntag
  0.1.5 added, tolerating both an attribute and a method, and on an older reader that has
  neither it falls back to the stock driver's own activated-card record under the correct
  mangled name, so a tester on an older install still reports a real SAK, ATQA and UID.
- The reader now logs, once per session, which reader primitives the live base reader carries,
  and whether the installed `ntag_reader` has `ChunkedType2PageReader`. Between them those two
  lines date the installed rfid-ntag from the log alone, so a tester does not have to look it up.
- The parser now says so when it declines a payload for want of the `EEEEEEEE` signature,
  instead of declining silently.

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
