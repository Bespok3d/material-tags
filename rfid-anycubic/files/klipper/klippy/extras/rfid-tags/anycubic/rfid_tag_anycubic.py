"""Registers the Anycubic ACE raw-page decoder with the RFID hub.

Klipper loads this module for the ``[rfid_tag_anycubic]`` config section. Anycubic ACE rides
a plaintext NTAG21x (no key), which the stock rfid-ntag reader already page-reads, so this
plugin needs no reader change: it registers a payload parser that scans the raw page dump for
Anycubic's `7B 00 65 00` magic and decodes the dispute-free fields. Parsers are first-OK-wins,
so a non-Anycubic tag (no magic) is declined and the next parser tries.

Thin relative-import shell: the decode logic lives in the pure, unit-tested
``anycubic_fields`` sibling. ``filament_protocol`` resolves as a flat ``klippy.extras``
sibling at runtime (placed by rfid-ntag).
"""
import logging

from . import filament_protocol
from .anycubic_fields import build_struct

_log = logging.getLogger("bespok3d.anycubic")

BYTES_PER_PAGE = 4  # NTAG21x / Ultralight page width, for page-aligned dump readability


def _page_aligned_hex(raw_bytes):
    """Groups raw_bytes into page-width chunks so a dump lines up with the page numbers
    anycubic_fields' offsets are documented against, instead of one unbroken hex string."""
    page_starts = range(0, len(raw_bytes), BYTES_PER_PAGE)
    pages = [raw_bytes[start:start + BYTES_PER_PAGE] for start in page_starts]
    return " ".join(page.hex() for page in pages)


class AnycubicParser:
    def to_filament_protocol(self, raw_bytes):
        if not raw_bytes:
            return filament_protocol.FILAMENT_PROTO_ERR, None

        info = build_struct(bytes(raw_bytes), dict(filament_protocol.FILAMENT_INFO_STRUCT))
        if info is None:
            _log.warning("Anycubic: magic not found, declining")
            return filament_protocol.FILAMENT_PROTO_ERR, None
        _log.info("Anycubic: parsed fields = %s", info)
        _log.info("Anycubic: uid=%s vendor=%s type=%s nozzle=%s-%s", info.get("CARD_UID"),
                  info.get("VENDOR"), info.get("MAIN_TYPE"), info.get("HOTEND_MIN_TEMP"),
                  info.get("HOTEND_MAX_TEMP"))
        return filament_protocol.FILAMENT_PROTO_OK, info


class RfidTagAnycubic:
    def __init__(self, config):
        self.printer = config.get_printer()
        self.printer.register_event_handler("klippy:ready", self._handle_ready)

    def _handle_ready(self):
        hub = self.printer.lookup_object("bespok3d_rfid", None)
        if hub is None:
            _log.warning("bespok3d_rfid not loaded: Anycubic support inactive")
            return
        hub.register_payload_parser(AnycubicParser())
        _log.info("ready: Anycubic payload parser registered")


def load_config(config):
    return RfidTagAnycubic(config)
