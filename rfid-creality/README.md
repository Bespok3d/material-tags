# rfid-creality

Clean-room decoder for **Creality CFS** filament tags - encrypted Mifare Classic. Decodes the
filament once you supply the two keys.

- **Status:** rc. **Requires two user-supplied keys** (HW claim reader + crypto1 + a
  vendored pure-python AES).
- **Decodes:** material type, filament diameter, hotend temperature range, color (RGB), net
  weight (bucket: 250/500/600/750/1000 g), and the Creality material id.
- **How type/diameter/temps work:** the tag itself does not carry them. They are resolved from
  the material id via a table (`creality_types.py`) built from Creality's own published slicer
  profiles. Diameter is authoritative; hotend temps are nominal defaults the printer may
  override. Bed temperature is not filled (it is too printer-dependent to assert from the id).
- **Gotchas:**
  - **You paste two keys.** A *master key* derives the card key from the UID
    (`AES-128-ECB(master, tiled UID)`, first 6 bytes), and a *payload key* AES-ECB-decrypts the
    block. Both are public community values; we ship only their **SHA-256 hashes**, never the
    keys. No/invalid key -> the spool is tracked **UID-only**.
  - Mode is **AES-128-ECB** throughout. The derived key authenticates sector 1 (loaded as
    Key B, which a real tag confirmed).
  - **Color caveat.** Color is read from the tag as RGB, but the sample spool used for
    verification carried a tag color that did not match the physical filament (a factory write
    error on that spool). The reported color may not always match the real filament.
  - The material-id **name map is not published** by Creality, so the material stays a numeric
    id here (its type/diameter/temps are resolved as above).
  - **Verified against a real Creality tag** (blue Hyper PLA, 1kg) for material type, diameter,
    temperature range, and weight. Other material ids are resolved from Creality's profiles but
    not yet seen on hardware.
- Requires the RFID Spool Reader (`rfid-ntag` >= 0.1.6, the crypto1 substrate; auto-installed
  via `require: rfid-service`).

In-app doc: [doc/README.md](doc/README.md) - Changelog: [doc/CHANGELOG.md](doc/CHANGELOG.md)

## Support this project

Bespok3d is built and maintained in the open, on stock printer firmware. If it saved you an
afternoon, you can [buy me a coffee](https://ko-fi.com/A623L7G).