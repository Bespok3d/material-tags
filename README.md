# all-the-tags

[![licence](https://img.shields.io/badge/licence-AGPL--3.0-blue)](LICENSE)
[![release](https://img.shields.io/github/v/release/Bespok3d/material-tags)](https://github.com/Bespok3d/material-tags/releases)
![printer](https://img.shields.io/badge/printer-Snapmaker%20U1-informational)
![stock firmware](https://img.shields.io/badge/stock%20firmware-no%20flashing-brightgreen)

Filament RFID/NFC **decoder plugins** for Bespok3d, plus two collections
(`kind:collection`, a members list with no payload of their own):

- **"All the Tags"** (`all-the-tags/`) installs the whole family at once: reader + every
  decoder + Spoolman tracking.
- **"Materials Tracker Plus"** (`materials-tracker-plus/`) is that same family plus
  `afc-lite` and `u1-gcode-colors`, for a printer with the filament changer. Those two
  members ship from other repos; a collection may name a member published elsewhere.

A decoder here is *just the payload decoder*. It does **not** re-architect the
reader: it plugs into the live RFID hub shipped by the **RFID Spool Reader**
(`rfid-ntag`, in the `u1-enhanced-rfid` repo) and maps one tag standard into the
shared `rfid_data.json`. Every decoder declares `require: rfid-service`, so
installing it auto-installs `rfid-ntag` (the hub + firmware patches + NTAG chip
stack). Decoders are **read-only**: writing tags is out of scope.

This repo is published as the **`material-tags`** sub-list
(`git@github.com:Bespok3d/material-tags.git`), a co-repo of independently-installable
plugins like `u1-extras`. Each tag dir has its own `README.md` (status + gotchas at a
glance) plus an in-app `doc/README.md`.

## Layout

```text
material-tags/
  <plugin-id>/             # one decoder = one dir; its name is the manifest .name
    manifest.json
    files/                 # payload the daemon places on the printer (klipper-extras + cfg)
    doc/README.md          # rendered in-app; not deployed
    doc/CHANGELOG.md
    README.md              # browse-the-repo summary (status + gotchas); NOT shipped in the .b3
  .github/workflows/release.yml
  index.json               # the published sub-list (CI-generated + committed; main-index lists[] it)
  dist/                    # build output (gitignored)
```

## Build locally

Needs Node.js 20+. Builds run through the shared `Bespok3d/b3-builder` tool:

```sh
npm install github:Bespok3d/b3-builder
npx b3-builder build --source ./rfid-opentag --atom-repo Bespok3d/material-tags
# -> dist/rfid-opentag-<ver>.b3 + dist/rfid-opentag.atom.json
```

Drop `--source` to build every plugin in the repo at once.

The Action runs with `bake: 'true'`: a plugin that ships a `requirements.txt` or
`klipper_requirements.txt` at its root gets its Python deps downloaded for the printer platform
(aarch64, CPython 3.11) at build time. Pass `--bake` to do the same locally.

Writing a plugin of your own? Start at the plugin documentation:
[Bespok3d/b3-builder/doc](https://github.com/Bespok3d/b3-builder/tree/main/doc).

## Releasing

Bump a plugin's `manifest.json` `version` and push the tag `plugin-<name>-v<version>` naming that
plugin and that exact number. A push to `main` publishes nothing, and the run is refused if the tag
and the manifest disagree. CI runs the `Bespok3d/b3-builder` Action over the whole repo, which packs
each `.b3`, cuts a release per plugin, assembles this repo's `index.json` sub-list as `Material
Tags`, and registers it in `Bespok3d/main-index` (`lists/<repo>.json`). Secrets: `MAIN_INDEX_TOKEN`
(contents:write on main-index) and `REGISTRY_SIGNING_KEY` (the org registry key the `b3-builder`
Action signs each `.b3` and atom with).


The `relay/` dir is build-coordination scratch and is **gitignored**: it never lands in the org repo.

## Shipped decoders

| Plugin | Tag standard | Seam | Status |
| --- | --- | --- | --- |
| `rfid-generic-ndef` | Any plain JSON over NDEF (no `protocol` field) | payload parser (NDEF JSON) | experiment |
| `rfid-opentag` | OpenTag3D (queengooborg), binary over NDEF | payload parser (NDEF binary) | experiment |
| `rfid-openprinttag` | OpenPrintTag (prusa3d), CBOR over NDEF | payload parser (NDEF binary + vendored CBOR) | experiment |
| `rfid-elegoo` | Elegoo (Centauri), raw-page binary (NOT NDEF) | payload parser (raw page) | experiment (open tags)* |
| `rfid-tigertag` | TigerTag, raw-page binary (NOT NDEF) | payload parser (raw page) | experiment |
| `rfid-anycubic` | Anycubic ACE, plaintext raw-page (NOT NDEF) | payload parser (raw page) | experiment (partial)** |
| `rfid-qidi` | QIDI, Mifare Classic on the factory default key | HW claim reader (no user key) | stable (device-proven)*** |
| `rfid-bambu` | Bambu Lab, encrypted Mifare Classic | HW claim reader + crypto1 (user key) | stable |
| `rfid-creality` | Creality CFS, encrypted Mifare Classic | HW claim reader + crypto1 + AES (user keys) | experiment |

The decoders cover every payload shape a decoder can take, so each is a worked template:
NDEF JSON (`rfid-generic-ndef`), NDEF binary (`rfid-opentag`), NDEF CBOR (`rfid-openprinttag`),
raw-page binary (`rfid-elegoo`, `rfid-tigertag`), Mifare-Classic on the factory default key
(`rfid-qidi`), and encrypted Mifare-Classic with user-supplied keys (`rfid-bambu`,
`rfid-creality`).

All are on the **experiment** channel until verified against a real tag on a printer
(junior `u1jr` is the bench; testers verify the spool kinds we do not own). The **"All the
Tags" collection** (`all-the-tags/`, shipped) bundles the reader + all decoders + Spoolman
into a one-click "Install all" and is the device-trial vehicle; see `relay/RELAY-D1.md`.

**`rfid-anycubic` is **partial by design**. The tag is plaintext NTAG (no key) and the public
RE agrees on the magic, version, ASCII brand/material, and nozzle/bed temps - which it decodes.
It does **not** decode color, diameter, or weight: the sources disagree on the SKU field length,
the color byte order (ARGB vs ABGR), and whether page 31 is weight, and no real tag dump has been
published to settle them. Guessing those would show a wrong color or a 10x-off weight, so they
wait for one tester dump (which makes them a small mechanical add).

*`rfid-elegoo` decodes Elegoo's **published NTAG EPC-256 layout** (material, sub-type, color,
diameter, weight). The **factory Centauri spools do not read on the U1** (HIL finding, 2026-06):
they are **ISO 14443-4 / IsoDep** (Shanghai Feiju Microelectronics) and the U1 reader never
even RF-wakes them, so the decoder never sees their bytes. Reading factory Elegoo needs a new
**ISO 14443-4 (APDU) reader track** plus the chip's undocumented auth - tracked as a hardware
blocker below (A5). The decoder is correct for any open Elegoo NTAG; testers with such a tag
verify it.

***`rfid-qidi` is **read end to end on junior** against physical QIDI spools (PLA Matte, PETG).
QIDI leaves its tags on the **Mifare factory default key** (`FF FF FF FF FF FF`), so there is no
user key and none is shipped. The whole payload is three bytes in sector 1 block 4 (material
code, colour code, manufacturer code) followed by an all-zero tail, which is also the signature
used to decline a foreign card. There is genuinely **no weight, diameter, temperature, date, or
SKU on a QIDI tag**, so those stay at their template defaults rather than being invented. The
code tables hold only pairings confirmed on a real spool; an unmapped code still tracks and logs
its number, so testers grow the tables. Wider community lists live at
[OpenRFID](https://github.com/suchmememanyskill/OpenRFID), read as reference only: no code and no
table from it is in this tree.

---

## The decoder-plugin template

This is the canonical recipe. A new tag decoder is mechanical: pick the seam,
write a pure decode module + a thin registration shell, declare the manifest.

### The pipeline (built in `rfid-ntag`, do not duplicate)

```
HW tag tapped
  -> fm175xx_reader (patched): SAK dispatch
       SAK 0x00 (NTAG) -> NtagReader.read_hw_tag -> raw page dump
  -> filament_detect (patched): card_protocol_parser dispatch
  -> bespok3d_rfid hub:
       _dispatch_parsers(raw)  -> each registered payload_parser, first OK wins
       rfid_ntag (a payload parser): ndef_parse -> JSON "protocol" -> protocol_mapper
  -> mapper/parser returns (FILAMENT_PROTO_OK, FILAMENT_INFO_STRUCT)
  -> hub writes rfid_data.json + notifies subscribers (spoolman)
```

### Three registration seams (pick by payload shape)

| Payload shape | Seam | Worked example |
| --- | --- | --- |
| JSON over NDEF **with** a `protocol` field | `rfid_ntag.register_protocol_mapper(m)` (keyed on `m.protocol_id`) | OpenSpool (in `rfid-ntag`) |
| JSON/binary over NDEF, **no** `protocol` field | `bespok3d_rfid.register_payload_parser(p)` (`p.to_filament_protocol(raw)`, first OK wins) | `rfid-generic-ndef`, `rfid-opentag` |
| Non-NDEF HW (e.g. raw-page binary, Mifare Classic UID) | `bespok3d_rfid.register_payload_parser(p)` reading raw pages directly (+ the A2 reader capability for Classic) | `rfid-elegoo` (raw-page, signature-anchored); TigerTag, Bambu/Creality deferred |

### Hard constraint: flat namespace

Every `klipper-extra` is placed by **basename** into `$KLIPPER_EXTRAS`; all
modules become flat siblings in `klippy.extras`. A decoder MUST:

- give each module a **unique basename** (`opentag_fields.py`,
  `rfid_tag_opentag.py`); never collide with `rfid-ntag`'s
  (`ndef_parser.py`, `payload_mapper.py`, `rfid_ntag.py`, `openspool_mapper.py`,
  `ntag_reader.py`, `bespok3d_rfid.py`);
- **not re-ship** the shared modules. Import them as siblings:
  `from . import filament_protocol, ndef_parser`. At runtime `.` is
  `klippy.extras`, so `filament_protocol` resolves to the stock firmware module and
  `ndef_parser` to the one `rfid-ntag` placed.

### Two-file split (pure core + relative-import shell)

The relative imports above cannot be unit-tested in isolation, so each decoder is
two flat modules, mirroring how `rfid-ntag` splits `payload_mapper` (pure, tested)
from `openspool_mapper` (shell):

- **`<name>_fields.py`** (pure): stdlib only, **no relative imports**. Takes the
  parsed NDEF records (or raw bytes) plus a `FILAMENT_INFO_STRUCT` **template dict**
  and returns the filled struct (or `None`). 100% unit-tested, asserting struct
  fields, with the template injected as a parameter.
- **`rfid_tag_<name>.py`** (shell): the Klipper extra for the
  `[rfid_tag_<name>]` config section. Does the relative imports, calls
  `ndef_parser.ndef_parse`, hands records + `dict(filament_protocol.FILAMENT_INFO_STRUCT)`
  to the pure core, registers with the hub on `klippy:ready`. ~30 lines, no logic.

The section name **must equal** the shell's module basename (Klipper maps
`[rfid_tag_opentag]` to `klippy/extras/rfid_tag_opentag.py`).

### Directory layout

Every decoder's klipper-extras live under a shared `rfid-tags/` parent, in their **own
per-plugin subdir** (`rfid-tags/<name>/`). The subdir is source organization only; the
daemon still places each module by **basename** into the flat `klippy.extras`, so the
runtime sibling-import rule below is unchanged.

```
rfid-<name>/
  manifest.json                       # provides: [], require: [{service: rfid-service, cardinality: one}]
  files/klipper/rfid-<name>.cfg       # just: [rfid_tag_<name>]   (klipper-config, NOT under rfid-tags/)
  files/klipper/klippy/extras/rfid-tags/<name>/rfid_tag_<name>.py   # shell (section + registration)
  files/klipper/klippy/extras/rfid-tags/<name>/<name>_fields.py     # pure decode core
  doc/README.md
  doc/CHANGELOG.md                    # required by the plugin-invariants test
  tests/conftest.py                   # puts files/.../extras/rfid-tags/<name> on sys.path
  tests/test_<name>_fields.py         # captured-payload fixtures -> assert struct fields
```

Copy `rfid-generic-ndef` (JSON) or `rfid-opentag` (binary) and fill in the field
map / offsets. `channel: "experiment"` until device-verified.

**Authoring `doc/README.md`:** the in-app Doc tab renders markdown WITHOUT remark-gfm,
so GFM pipe tables show as raw text. Use bullet lists, not tables. (The repo-level
`README.md` here is GitHub-rendered, where tables are fine.)

### Avoiding collisions between decoders

Parsers are tried first-OK-wins, so each must decline payloads it does not own:

- `rfid-generic-ndef` decodes only `application/json` records **without** a
  `protocol` field, so it never shadows OpenSpool or a protocol mapper.
- `rfid-opentag` decodes only `application/opentag3d` records.

### Tests + checks

`./scripts/check.sh` runs `pytest`/`ruff`/`mypy` on the new Python
(see the `Plugin: all-the-tags` block in `scripts/check.sh`) plus the
`plugin-invariants` vitest over every manifest. The pure `*_fields.py` modules are
mypy-checked; the relative-import shells are linted by ruff only (like
`rfid-ntag`'s shells).

---

## Blocked decoders (need real hardware input, not more code)

One tag remains a true hardware blocker; the research-backed facts are recorded so it becomes
a mechanical follow-on once the blocker clears. (Anycubic was de-blocked: it now ships its
dispute-free fields above and only its color/diameter/weight wait for a tester dump - that is
a small add, not a blocked decoder.)

| Tag | Blocker | Notes for the follow-on |
| --- | --- | --- |
| **Elegoo factory (IsoDep)** | The factory Centauri Feiju chip does not RF-wake to the U1 reader's WUPA, BELOW anticollision. Needs reader-firmware RF iteration on junior, then the chip's undocumented ISO-14443-4 auth. **Hardware/RF work, not an implementation task.** | RELAY-A5: real Centauri spools are ISO 14443-4 / IsoDep (Feiju, UID prefix `0x53`). Public NDEF is only the `elegoo.com` URL; filament data is behind the locked IsoDep layer. STEP 0 = capture the ATS/APDU exchange on junior (`DETECT_SPOOLS`, tag at the antenna). A prior session added a carrier power-cycle retry to the reader patch (rfid-ntag 0.1.4) - it changed the failure from WUPA-err to timer-err but still does not fully wake the chip. Decoding the locked payload stays an explicit non-goal until someone publishes the Feiju auth; UID-only tracking (via B1) is the deliverable for these spools. |

(**Elegoo open tags** ship as `rfid-elegoo`: the published EPC-256 NTAG layout decodes
fine; only the factory IsoDep spools are blocked, as above.)

## Repos this depends on

- `u1-enhanced-rfid/rfid-ntag` provides `rfid-service` (the hub + chip stack +
  firmware patches). Decoders resolve it cross-repo through main-index, like
  `webcam-*` resolve `camera-hw-accel`.

## Licence

Copyright (C) 2026 unlucio and the Bespok3d contributors

This program is free software: you can redistribute it and/or modify it under the terms of the GNU
Affero General Public License as published by the Free Software Foundation, either version 3 of the
License, or (at your option) any later version.

This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without
even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU Affero
General Public License for more details.

You should have received a copy of the GNU Affero General Public License along with this program. If
not, see <https://www.gnu.org/licenses/>. The full text is in [LICENSE](LICENSE).

Bespok3d is a project of the Bespok3d Organisation, which is not a legal entity. Copyright is held by
the individual authors named above.

## Support this project

Bespok3d is built and maintained in the open, on stock printer firmware. If it saved you an
afternoon, you can [buy me a coffee](https://buymeacoffee.com/unlucio).
