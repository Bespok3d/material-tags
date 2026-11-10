"""Each collection requires member versions that carry the fixes its users rely on.

A collection installs whatever meets its floors, so a floor below a fix lets an install keep
the bug.
"""
import json
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
COLLECTIONS = ("all-the-tags", "materials-tracker-plus")
FLOOR_PREFIX = ">="

FLOORS_FIXES_NEED = {
    # Both sides of a Bambu spool name one shared spool identity, so it stays one spool.
    "rfid-bambu": (0, 2, 2),
    # Ties both sides of a Bambu spool to one spool and never ties one tag to two spools.
    "spoolman": (0, 1, 39),
    # Fiberon spools show their own material, not PLA.
    "rfid-creality": (0, 2, 3),
    # Spools with several colours show all of them, not only the first.
    "rfid-openprinttag": (0, 1, 2),
    "rfid-opentag": (0, 1, 1),
    "rfid-tigertag": (0, 1, 1),
    "rfid-generic-ndef": (0, 1, 1),
}


def member_floors(collection):
    manifest = json.loads((REPO_ROOT / collection / "manifest.json").read_text())
    return {member["id"]: member["version"] for member in manifest["members"]}


def version_numbers(floor):
    assert floor.startswith(FLOOR_PREFIX), f"{floor} is not a minimum version"
    return tuple(int(part) for part in floor.removeprefix(FLOOR_PREFIX).split("."))


@pytest.mark.parametrize("collection", COLLECTIONS)
@pytest.mark.parametrize(("member", "needed"), FLOORS_FIXES_NEED.items())
def test_the_collection_requires_the_member_version_with_the_fix(collection, member, needed):
    floors = member_floors(collection)
    assert member in floors, f"{collection} no longer lists {member}"
    assert version_numbers(floors[member]) >= needed
