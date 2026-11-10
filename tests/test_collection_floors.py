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
    # Both sides of a Bambu spool name one shared spool identity, so it stays one spool, and a
    # two-color spool shows both its colors.
    "rfid-bambu": (0, 3, 0),
    # Ties both sides of a Bambu spool to one spool and never ties one tag to two spools.
    # 0.1.37 to 0.1.39 were never published; 0.1.40 is the first release that carries this.
    "spoolman": (0, 1, 40),
    # Fiberon spools show their own material, not PLA.
    "rfid-creality": (0, 2, 3),
    # Spools with several colors show all of them, not only the first.
    "rfid-openprinttag": (0, 2, 0),
    "rfid-tigertag": (0, 2, 0),
    "rfid-generic-ndef": (0, 2, 0),
    # Spools with several colors, and OpenTag3D v2 tags, show the details the tag holds.
    "rfid-opentag": (0, 2, 0),
}


def member_floors(collection: str) -> dict[str, str]:
    manifest = json.loads((REPO_ROOT / collection / "manifest.json").read_text())
    return {member["id"]: member["version"] for member in manifest["members"]}


def version_parts(version: str) -> tuple[int, ...]:
    return tuple(int(part) for part in version.split("."))


def version_numbers(floor: str) -> tuple[int, ...]:
    assert floor.startswith(FLOOR_PREFIX), f"{floor} is not a minimum version"
    return version_parts(floor.removeprefix(FLOOR_PREFIX))


@pytest.mark.parametrize("collection", COLLECTIONS)
@pytest.mark.parametrize(("member", "needed"), FLOORS_FIXES_NEED.items())
def test_the_collection_requires_the_member_version_with_the_fix(
    collection: str, member: str, needed: tuple[int, ...],
) -> None:
    floors = member_floors(collection)
    assert member in floors, f"{collection} no longer lists {member}"
    assert version_numbers(floors[member]) >= needed


def versions_in_this_repo() -> dict[str, str]:
    manifests = (json.loads(path.read_text()) for path in REPO_ROOT.glob("*/manifest.json"))
    return {manifest["name"]: manifest["version"] for manifest in manifests}


def floors_on_members_in_this_repo() -> list[tuple[str, str, str, str]]:
    versions = versions_in_this_repo()
    return [
        (collection, member, floor, versions[member])
        for collection in COLLECTIONS
        for member, floor in member_floors(collection).items()
        if member in versions
    ]


def test_the_collections_list_members_from_this_repo() -> None:
    # An empty list would make pytest skip the floor check below instead of failing it.
    assert floors_on_members_in_this_repo()


@pytest.mark.parametrize(
    ("collection", "member", "floor", "version"), floors_on_members_in_this_repo(),
)
def test_the_member_in_this_repo_reaches_the_collection_floor(
    collection: str, member: str, floor: str, version: str,
) -> None:
    shortfall = f"{collection} needs {member} {floor}, this repo has {version}"
    assert version_parts(version) >= version_numbers(floor), shortfall
