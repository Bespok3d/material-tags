"""Creality filament-id to material data (pure, stdlib-only).

Harvested from Creality's own slicer profiles (CrealityOfficial/CrealityPrint,
resources/profiles/Creality/filament/*.json). That repo is the authoritative, non-GPL origin
for this mapping; nothing here is copied from any GPL reader project.

Per filament id we map:
  * type       (filament_type)                       stable across profiles
  * diameter   (filament_diameter)                   stable (1.75 where present)
  * hotend_min (nozzle_temperature_range_low)        modal value across profiles
  * hotend_max (nozzle_temperature_range_high)       modal value across profiles

Type and diameter are stable per id. Nozzle temps vary slightly between printer profiles, so
the MODAL (most common) value is used: a nominal default the printer may still override from
its own database. Bed temperature is deliberately omitted: it is strongly printer-dependent
(about half the ids disagree across profiles), so the tag cannot assert a single correct value.
Any field a profile did not provide is None. Confirmed against a real tag for 01001 (Hyper PLA,
1.75mm, 190 to 240).
"""
from typing import NamedTuple


class _Mat(NamedTuple):
    type: str
    diameter: float | None
    hotend_min: int | None
    hotend_max: int | None


CREALITY_ID_TO_MATERIAL = {
    "00001": _Mat("PLA", 1.75, 190, 240),
    "00002": _Mat("PLA", 1.75, 190, 240),
    "00003": _Mat("PETG", 1.75, 220, 270),
    "00004": _Mat("ABS", 1.75, 240, 280),
    "00005": _Mat("TPU", 1.75, 200, 250),
    "00006": _Mat("PLA-CF", 1.75, 190, 240),
    "00007": _Mat("ASA", 1.75, 240, 280),
    "00008": _Mat("PA", 1.75, 240, 260),
    "00009": _Mat("PA-CF", 1.75, 260, 300),
    "00010": _Mat("BVOH", 1.75, 200, 220),
    "00011": _Mat("PVA", 1.75, 215, 225),
    "00012": _Mat("HIPS", 1.75, 220, 250),
    "00013": _Mat("PET-CF", 1.75, 280, 320),
    "00014": _Mat("PETG-CF", 1.75, 240, 260),
    "00015": _Mat("PA-CF", 1.75, 280, 300),
    "00016": _Mat("PA-CF", 1.75, 300, 320),
    "00017": _Mat("PPS", 1.75, 320, 350),
    "00018": _Mat("PPS-CF", 1.75, 305, 320),
    "00019": _Mat("PP", 1.75, 220, 250),
    "00020": _Mat("PET", 1.75, 210, 230),
    "00021": _Mat("PC", 1.75, 250, 270),
    "00022": _Mat("PA-CF", 1.75, 260, 300),
    "00023": _Mat("PA", 1.75, 260, 300),
    "00024": _Mat("PLA", 1.75, 190, 240),
    "00025": _Mat("PA-CF", 1.75, 260, 300),
    "00026": _Mat("TPU", 1.75, 215, 240),
    "00027": _Mat("PETG-GF", 1.75, 240, 270),
    "00031": _Mat("PP-CF", 1.75, 220, 270),
    "00032": _Mat("PCTG", 1.75, 250, 270),
    "00033": _Mat("ASA-CF", 1.75, 250, 280),
    "00034": _Mat("PA-GF", 1.75, 250, 290),
    "00035": _Mat("PLA", 1.75, 190, 270),
    "00036": _Mat("TPU", 1.75, 190, 240),
    "00037": _Mat("TPU", 1.75, 200, 250),
    "01001": _Mat("PLA", 1.75, 190, 240),
    "01002": _Mat("PLA", 1.75, 200, 270),
    "01003": _Mat("PLA", 1.75, 190, 230),
    "01004": _Mat("PLA", 1.75, 190, 240),
    "01601": _Mat("PLA", 1.75, 190, 240),
    "02001": _Mat("PLA-CF", 1.75, 190, 240),
    "03001": _Mat("ABS", 1.75, 230, 260),
    "04001": _Mat("PLA", 1.75, 190, 240),
    "05001": _Mat("PLA", 1.75, 190, 240),
    "06001": _Mat("PETG", 1.75, 220, 270),
    "06002": _Mat("PETG", 1.75, 220, 270),
    "06003": _Mat("PETG-CF", 1.75, 240, 260),
    "06004": _Mat("PETG-GF", 1.75, 240, 260),
    "06005": _Mat("PETG", None, 220, 270),
    "07001": _Mat("ABS", 1.75, 230, 260),
    "07002": _Mat("PC", 1.75, 250, 270),
    "08001": _Mat("PLA", 1.75, 190, 240),
    "09001": _Mat("PLA", 1.75, 190, 240),
    "09002": _Mat("PLA", 1.75, 190, 240),
    "10001": _Mat("TPU", 1.75, 200, 240),
    "11001": _Mat("PA", 1.75, 250, 270),
    "12002": _Mat("PA-CF", 1.75, 280, 320),
    "12003": _Mat("PA-CF", 1.75, 280, 320),
    "12004": _Mat("PA-CF", 1.75, 290, 320),
    "12005": _Mat("PA-CF", 1.75, 290, 320),
    "13001": _Mat("PLA-CF", 1.75, 190, 240),
    "14001": _Mat("PLA", 1.75, 190, 240),
    "15001": _Mat("PLA", 1.75, 190, 240),
    "16001": _Mat("TPU", 1.75, 210, 240),
    "17001": _Mat("PLA", 1.75, 190, 240),
    "18001": _Mat("PLA", 1.75, 190, 240),
    "19001": _Mat("ASA", 1.75, 240, 280),
    "29001": _Mat("PLA", 1.75, 190, 240),
    "E1001": _Mat("PLA", 1.75, 210, 230),
    "E1002": _Mat("PLA", 1.75, 210, 230),
    "E1003": _Mat("PLA", 1.75, 210, 230),
    "E1004": _Mat("PLA", 1.75, 210, 230),
    "E1005": _Mat("PLA", None, None, None),
    "E1006": _Mat("PLA", None, None, None),
    "E1008": _Mat("PLA", None, None, None),
    "E1009": _Mat("PLA", None, None, None),
    "E2001": _Mat("PETG", None, None, None),
    "E2002": _Mat("PETG", None, None, None),
    "E2003": _Mat("PETG", None, None, None),
    "E2004": _Mat("PETG", None, None, 270),
    "E3001": _Mat("ABS", None, None, None),
    "E3002": _Mat("ABS", None, None, 270),
    "E3003": _Mat("ABS", 1.75, 190, 270),
    "E4001": _Mat("ASA", None, None, None),
    "E5001": _Mat("TPU", None, None, None),
    "E8001": _Mat("PET", None, None, None),
    "P1001": _Mat("PLA", 1.75, 190, 230),
    "P1002": _Mat("PLA", 1.75, 190, 230),
    "P1003": _Mat("PLA", 1.75, 190, 230),
    "P1004": _Mat("PLA", 1.75, 190, 230),
    "P2001": _Mat("PLA", 1.75, 250, 280),
    "P2002": _Mat("PETG-CF", 1.75, 240, 270),
    "P7001": _Mat("PLA", 1.75, 280, 300),
    "P7002": _Mat("PA-CF", 1.75, 240, 290),
    "P7003": _Mat("PA-CF", 1.75, 240, 290),
    "P7004": _Mat("PA-CF", 1.75, 240, 290),
    "P7005": _Mat("PLA", 1.75, 280, 300),
    "P8001": _Mat("PLA", 1.75, 270, 300),
    "P9001": _Mat("PLA", 1.75, 310, 340),
}


def material_for_id(material_id: str) -> _Mat | None:
    """Return the material record for a Creality filament id, or None if unknown."""
    return CREALITY_ID_TO_MATERIAL.get(material_id)


def type_for_id(material_id: str) -> str | None:
    """Return just the material type for a Creality filament id, or None if unknown."""
    mat = CREALITY_ID_TO_MATERIAL.get(material_id)
    return mat.type if mat is not None else None
