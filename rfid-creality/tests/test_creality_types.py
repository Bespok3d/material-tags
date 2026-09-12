# ruff: noqa: PLR2004  Tests assert on literal material values by design.
"""Tests for the Creality filament-id material table (creality_types).

The table is harvested from Creality's own slicer profiles. These pin the one id confirmed
against a real tag (01001 = Hyper PLA) and the accessor behavior for known and unknown ids.
"""
from creality_types import material_for_id, type_for_id


def test_known_id_resolves_full_record():
    mat = material_for_id("01001")
    assert mat is not None
    assert mat.type == "PLA"
    assert mat.diameter == 1.75
    assert mat.hotend_min == 190
    assert mat.hotend_max == 240


def test_type_for_id_shortcut():
    assert type_for_id("01001") == "PLA"


def test_unknown_id_returns_none():
    assert material_for_id("99999") is None
    assert type_for_id("99999") is None


def test_diameter_is_175_where_present():
    # Every entry that carries a diameter uses 1.75 mm (no 2.85 mm Creality CFS spools).
    from creality_types import CREALITY_ID_TO_MATERIAL
    diameters = {m.diameter for m in CREALITY_ID_TO_MATERIAL.values() if m.diameter is not None}
    assert diameters == {1.75}


def test_every_entry_has_a_type():
    from creality_types import CREALITY_ID_TO_MATERIAL
    assert all(m.type for m in CREALITY_ID_TO_MATERIAL.values())
