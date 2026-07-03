# ruff: noqa: PLR2004  Tests assert on literal CBOR values by design.
"""Unit tests for the minimal CBOR reader (RFC 8949 subset)."""
import pytest
from openprinttag.cbor_min import CborError, load_at


def _value(hexstr: str):
    return load_at(bytes.fromhex(hexstr), 0)[0]


def test_small_uint():
    assert _value("0a") == 10


def test_one_byte_uint():
    assert _value("1864") == 100


def test_two_byte_uint():
    assert _value("1903e8") == 1000


def test_eight_byte_uint():
    assert _value("1b000007d0fcab45f9") == 8594173675001


def test_negative_int():
    assert _value("20") == -1
    assert _value("3863") == -100


def test_byte_string():
    assert _value("443d3e3dff") == bytes.fromhex("3d3e3dff")


def test_text_string():
    assert _value("6950727573616d656e74") == "Prusament"


def test_definite_array():
    assert _value("83010203") == [1, 2, 3]


def test_indefinite_array():
    assert _value("9f0001ff") == [0, 1]


def test_definite_map():
    assert _value("a10218d2") == {2: 210}


def test_indefinite_map():
    assert _value("bf6161186418ff63666f6fff") == {"a": 100, 255: "foo"}


def test_half_float():
    assert _value("f93cf6") == pytest.approx(1.240234375)


def test_single_float():
    assert _value("fa4134cccd") == pytest.approx(11.3, abs=1e-4)


def test_load_at_returns_next_offset():
    data = bytes.fromhex("0a1864")
    value, offset = load_at(data, 0)
    assert value == 10
    assert offset == 1


def test_semantic_tag_is_rejected():
    # Major type 6 (tag) is not used by OpenPrintTag; the reader must decline it.
    with pytest.raises(CborError):
        load_at(bytes.fromhex("c11a514b67b0"), 0)


def test_truncated_is_rejected():
    with pytest.raises(CborError):
        load_at(bytes.fromhex("1903"), 0)
