# Attributions - rfid-creality

**Plugin author:** Bespok3d, tag format documented by DnG-Crafts (K2-RFID) and the Bambu Research Group

Reads Creality filament tags.

| Upstream project | Author | Licence | Needed at runtime | Code ships in this package |
| --- | --- | --- | --- | --- |
| RFID-Tag-Guide and the K2-RFID community schema | DnG-Crafts (K2-RFID) and the Bambu Research Group | MIT | no | no |
| Filament id to type/diameter/temperature data, harvested from Creality slicer profiles | CrealityOfficial/CrealityPrint | see repo | no | no (data only, regenerated from public profiles) |

The AES used to derive the sector key and decrypt the payload is a clean-room implementation of the
published FIPS-197 standard (`aes_min.py`), tested against the FIPS-197 known-answer vectors. It is
not taken from any third-party crypto library.

The filament id to type/diameter/temperature table (`creality_types.py`) is generated from Creality's own published slicer profiles (CrealityOfficial/CrealityPrint), the authoritative origin for that data. It is not copied from any third-party reader project.