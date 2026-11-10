# rfid-bambu

Clean-room decoder for **Bambu Lab** filament tags - encrypted Mifare Classic. Decodes the
full filament once you supply the key.

- **Status:** stable. **Requires a user-supplied key** (HW claim reader + crypto1).
- **Decodes:** material, color (RGBA, plus the second color of a two-color spool as RGB),
  diameter, weight, and drying/bed/nozzle temperatures.
- **Gotchas:**
  - **You paste the key.** Bambu tags are encrypted; the public Bambu master key derives the
    per-tag sector keys (HKDF-SHA256 over the UID). We ship only the key's **SHA-256 hash** to
    validate your paste - **never the key itself**. With no/invalid key the spool is still
    tracked **UID-only** (no decode).
  - Bambu cards share Snapmaker's M1 **SAK 0x08**; the reader routes a 0x08 card the stock key
    cannot open to this claim handler (so it never disturbs the Snapmaker M1 path).
  - Decoding is proven against the published spec and its test vectors, and a real Bambu spool
    is read on a U1. The second color of a two-color spool is not yet tried on a real spool.
- Requires the RFID Spool Reader (`rfid-ntag` >= 0.1.6, the crypto1 substrate; auto-installed
  via `require: rfid-service`).

In-app doc: [doc/README.md](doc/README.md) - Changelog: [doc/CHANGELOG.md](doc/CHANGELOG.md)

## Support this project

Bespok3d is built and maintained in the open, on stock printer firmware. If it saved you an
afternoon, you can [buy me a coffee](https://ko-fi.com/A623L7G).
