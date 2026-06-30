"""Minimal CBOR reader (RFC 8949 subset) for OpenPrintTag payloads.

Pure, stdlib-only, unit-tested. Python's standard library has no CBOR codec, so this decodes
exactly the subset OpenPrintTag uses: unsigned/negative ints (major 0/1), byte/text strings
(2/3), arrays (4), maps (5, definite and indefinite), and floats/simple values (7: f16/f32/f64,
plus false/true/null). Semantic tags (major 6) are not used by OpenPrintTag, so encountering
one raises - the decoder then declines the record. Each decode returns (value, next_offset)
so the caller can walk the concatenated meta/main/aux section maps.
"""
import struct
from collections.abc import Callable
from typing import Any

MAJOR_SHIFT = 5
INFO_MASK = 0x1F
ARG_IN_HEAD = 24          # info < 24 -> the argument is the info value itself
INDEFINITE = 31
BREAK = 0xFF
NEG_BIAS = -1

MAJOR_UINT = 0
MAJOR_NEGINT = 1
MAJOR_BYTES = 2
MAJOR_TEXT = 3
MAJOR_ARRAY = 4
MAJOR_MAP = 5
MAJOR_SIMPLE = 7

HALF_FLOAT = 25
SINGLE_FLOAT = 26
DOUBLE_FLOAT = 27
FALSE = 20
TRUE = 21
NULL = 22

_ARG_WIDTHS = {24: 1, 25: 2, 26: 4, 27: 8}
_FLOAT_FORMATS = {HALF_FLOAT: (">e", 2), SINGLE_FLOAT: (">f", 4), DOUBLE_FLOAT: (">d", 8)}
_SIMPLE_VALUES = {FALSE: False, TRUE: True, NULL: None}


class CborError(Exception):
    """The byte stream is not valid CBOR for the subset OpenPrintTag uses."""


def _slice(data: bytes, offset: int, length: int) -> bytes:
    end = offset + length
    if end > len(data):
        raise IndexError("truncated CBOR item")
    return data[offset:end]


def _read_argument(data: bytes, offset: int, info: int) -> tuple[int, int]:
    if info < ARG_IN_HEAD:
        return info, offset
    width = _ARG_WIDTHS[info]
    return int.from_bytes(_slice(data, offset, width), "big"), offset + width


def _decode_uint(data: bytes, offset: int, info: int) -> tuple[Any, int]:
    return _read_argument(data, offset, info)


def _decode_negint(data: bytes, offset: int, info: int) -> tuple[Any, int]:
    value, offset = _read_argument(data, offset, info)
    return NEG_BIAS - value, offset


def _decode_bytes(data: bytes, offset: int, info: int) -> tuple[Any, int]:
    length, offset = _read_argument(data, offset, info)
    return _slice(data, offset, length), offset + length


def _decode_text(data: bytes, offset: int, info: int) -> tuple[Any, int]:
    length, offset = _read_argument(data, offset, info)
    return _slice(data, offset, length).decode("utf-8", "replace"), offset + length


def _decode_array(data: bytes, offset: int, info: int) -> tuple[Any, int]:
    items: list[Any] = []
    if info == INDEFINITE:
        while data[offset] != BREAK:
            value, offset = decode_item(data, offset)
            items.append(value)
        return items, offset + 1
    count, offset = _read_argument(data, offset, info)
    while len(items) < count:
        value, offset = decode_item(data, offset)
        items.append(value)
    return items, offset


def _decode_map(data: bytes, offset: int, info: int) -> tuple[Any, int]:
    result: dict[Any, Any] = {}
    if info == INDEFINITE:
        while data[offset] != BREAK:
            key, offset = decode_item(data, offset)
            value, offset = decode_item(data, offset)
            result[key] = value
        return result, offset + 1
    count, offset = _read_argument(data, offset, info)
    index = 0
    while index < count:
        key, offset = decode_item(data, offset)
        value, offset = decode_item(data, offset)
        result[key] = value
        index += 1
    return result, offset


def _decode_simple(data: bytes, offset: int, info: int) -> tuple[Any, int]:
    if info in _FLOAT_FORMATS:
        fmt, width = _FLOAT_FORMATS[info]
        return struct.unpack(fmt, data[offset:offset + width])[0], offset + width
    return _SIMPLE_VALUES[info], offset


_DECODERS: dict[int, Callable[[bytes, int, int], tuple[Any, int]]] = {
    MAJOR_UINT: _decode_uint,
    MAJOR_NEGINT: _decode_negint,
    MAJOR_BYTES: _decode_bytes,
    MAJOR_TEXT: _decode_text,
    MAJOR_ARRAY: _decode_array,
    MAJOR_MAP: _decode_map,
    MAJOR_SIMPLE: _decode_simple,
}


def decode_item(data: bytes, offset: int) -> tuple[Any, int]:
    """Decode one CBOR data item at offset; return (value, next_offset). Raises KeyError on
    an unsupported major type (e.g. a semantic tag), which load_at wraps as CborError."""
    head = data[offset]
    major = head >> MAJOR_SHIFT
    info = head & INFO_MASK
    return _DECODERS[major](data, offset + 1, info)


def load_at(data: bytes, offset: int) -> tuple[Any, int]:
    """Decode the CBOR item at offset, raising CborError for any malformed/unsupported input."""
    try:
        return decode_item(data, offset)
    except (KeyError, IndexError, ValueError, struct.error) as err:
        raise CborError(str(err)) from err
