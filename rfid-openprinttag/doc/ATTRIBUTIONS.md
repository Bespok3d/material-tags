# Attributions - rfid-openprinttag

**Plugin author:** Bespok3d, tag format published by the OpenPrintTag project

Reads OpenPrintTag filament tags.

| Upstream project | Author | Licence | Needed at runtime | Code ships in this package |
| --- | --- | --- | --- | --- |
| OpenPrintTag specification | the OpenPrintTag project | published specification | no | no |

The CBOR reader (`cbor_min.py`) is a clean-room implementation of the RFC 8949 subset OpenPrintTag
uses, because Python's standard library has no CBOR codec. It is not taken from any third-party CBOR
library.
