"""Every decoder requires the RFID Spool Reader, so installing a decoder installs the reader too.

A decoder only registers a payload parser on the reader's hub; without the reader nothing ever
hands it a tag, so a decoder installed alone reads nothing.
"""
import json
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
READER_SERVICE = "rfid-service"
# Every plugin in this repo is a decoder except the collections, which only bundle the others.
COLLECTION_KIND = "collection"

# A factory Elegoo tag is 44 pages; a reader older than its chunked page reader drops the read.
READER_FLOOR_BY_DECODER = {"rfid-elegoo": ">=0.1.15"}


def load_decoder_manifests() -> dict[str, dict]:
    manifests = (json.loads(path.read_text()) for path in REPO_ROOT.glob("*/manifest.json"))
    return {
        manifest["name"]: manifest
        for manifest in manifests
        if manifest.get("kind") != COLLECTION_KIND
    }


DECODER_MANIFESTS = load_decoder_manifests()


def reader_requirement(decoder: str) -> dict | None:
    requirements = DECODER_MANIFESTS[decoder].get("require") or []
    return next((entry for entry in requirements if entry["service"] == READER_SERVICE), None)


def test_the_repo_has_decoders() -> None:
    # An empty list would make pytest skip the checks below instead of failing them.
    assert DECODER_MANIFESTS


@pytest.mark.parametrize("decoder", sorted(DECODER_MANIFESTS))
def test_the_decoder_requires_the_reader(decoder: str) -> None:
    requirement = reader_requirement(decoder)
    assert requirement is not None, f"{decoder} does not require {READER_SERVICE}"
    assert requirement["cardinality"] == "one"


@pytest.mark.parametrize(("decoder", "floor"), READER_FLOOR_BY_DECODER.items())
def test_the_decoder_requires_the_reader_version_it_needs(decoder: str, floor: str) -> None:
    requirement = reader_requirement(decoder) or {}
    assert requirement.get("version") == floor
