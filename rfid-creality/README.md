# rfid-creality

Clean-room decoder for **Creality CFS** filament tags - encrypted Mifare Classic. Decodes the
filament once you supply the two keys.

- **Status:** experiment. **Requires two user-supplied keys** (HW claim reader + crypto1 + a
  vendored pure-python AES).
- **Decodes:** color (RGB), weight (bucket: 250/500/600/750/1000 g), manufacture date, and the
  numeric material id.
- **Gotchas:**
  - **You paste two keys.** A *master key* derives the card key from the UID
    (`AES-128-ECB(master, tiled UID)`, first 6 bytes), and a *payload key* AES-ECB-decrypts the
    block. Both are public community values; we ship only their **SHA-256 hashes**, never the
    keys. No/invalid key -> the spool is tracked **UID-only**.
  - Mode is **AES-128-ECB** throughout (verified against the public RE; not CBC). The derived
    key is loaded as **Key B** - if a real tag turns out to need Key A, that is the one
    device-verify item (a one-line change).
  - Creality's tag carries **no diameter or temperatures** (the printer resolves those from the
    material id via its unpublished database), and the **material-id name map is not published**,
    so the material stays a number.
  - Decoding is proven against the published schema and its test vectors. **Not yet read from a
    real Creality spool** (we have no Creality spool to scan).
- Requires the RFID Spool Reader (`rfid-ntag` >= 0.1.6, the crypto1 substrate; auto-installed
  via `require: rfid-service`).

In-app doc: [doc/README.md](doc/README.md) - Changelog: [doc/CHANGELOG.md](doc/CHANGELOG.md)
