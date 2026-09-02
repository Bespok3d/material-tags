# Attributions - rfid-anycubic

**Plugin author:** Bespok3d ([Mauker](https://github.com/Mauker1)), tag format documented by
DnG-Crafts

**Contributors:** [LixNix](https://github.com/LixNix) captured and annotated a real Anycubic
ACE tag, a peach-pink PLA Spezial spool, which settled the color byte order
(alpha, then blue, green, red, the first sample tested was black, where the two possible
orders look identical), confirmed the bed temperature pair and blank-brand case against a
second, independent tag, and surfaced the `0x64` format version, distinct from the `0x65`
seen elsewhere.

Reads Anycubic ACE filament tags.

| Upstream project | Author | Licence | Needed at runtime | Code ships in this package |
| --- | --- | --- | --- | --- |
| ACE-RFID tag-format research | DnG-Crafts and contributors | see the project | no | no |
| Anycubic-NFC-Tagger-QT5 | mrRobot62 | see the project | no | no |
| anycubic-nfc-filament SKU/color catalog | Molodos and contributors | see the project | no | no |

Field layout follows the community reverse-engineering write-up at
https://github.com/DnG-Crafts/ACE-RFID. The ASA-material reference dump used to confirm the
temperature and print-speed fields against a second material came from
https://github.com/mrRobot62/Anycubic-NFC-Tagger-QT5. The SKU/color-code catalog at
https://github.com/Molodos/anycubic-nfc-filament/issues/15 pinned the color byte order
against a second, independently sourced sample and identified the Refill-line SKU that would
settle the remaining field-length question. No code from any of these projects is used here,
only the tag data and field-layout research they documented.