"""Regression tests for the Elegoo registration shell.

0.1.5 removed the plugin's own hardware reader. A real U1 (2026-09-23) read a factory Elegoo tag
through rfid-ntag's stock NtagReader, so the shell now registers ONLY a payload parser. Before
0.1.5 it also claimed 254 SAKs on the base reader, which could intercept tags belonging to other
decoders; test_ready_registers_the_parser_and_no_reader_handler fails on 0.1.4 for that reason.
"""
import importlib
import logging
import sys
import types

from test_elegoo_fields import _dump

FILAMENT_PROTO_OK = 0
FILAMENT_PROTO_ERR = 1

shell = importlib.import_module("elegoo.rfid_tag_elegoo")


class RecordingHub:
    def __init__(self):
        self.payload_parsers = []

    def register_payload_parser(self, parser):
        self.payload_parsers.append(parser)


class RecordingReaderDelegate:
    """Stands in for the base reader; any handler registration on it would be recorded."""

    def __init__(self):
        self.claimed_saks = []

    def register_card_type_handler(self, sak, handler):
        self.claimed_saks.append(sak)

    def register_card_handler(self, claim, handler):
        self.claimed_saks.append(claim)


class FakePrinter:
    def __init__(self, hub):
        self.objects = {"bespok3d_rfid": hub, "fm175xx_reader": RecordingReaderDelegate()}
        self.ready_handlers = []

    def register_event_handler(self, event, handler):
        self.ready_handlers.append(handler)

    def lookup_object(self, name, default=None):
        return self.objects.get(name) or default


class FakeConfig:
    def __init__(self, printer):
        self.printer = printer

    def get_printer(self):
        return self.printer


def _ready(hub):
    printer = FakePrinter(hub)
    shell.load_config(FakeConfig(printer))
    for handler in printer.ready_handlers:
        handler()
    return printer


def test_ready_registers_the_parser_and_no_reader_handler() -> None:
    hub = RecordingHub()
    printer = _ready(hub)
    assert len(hub.payload_parsers) == 1
    assert isinstance(hub.payload_parsers[0], shell.ElegooParser)
    assert printer.objects["fm175xx_reader"].claimed_saks == []


def test_ready_without_the_hub_registers_nothing() -> None:
    printer = FakePrinter(None)
    shell.load_config(FakeConfig(printer))
    for handler in printer.ready_handlers:
        handler()
    assert printer.objects["fm175xx_reader"].claimed_saks == []


def test_parser_decodes_the_real_factory_spool() -> None:
    status, info = shell.ElegooParser().to_filament_protocol(_dump())
    assert status == FILAMENT_PROTO_OK
    assert info["MAIN_TYPE"] == "PLA"
    assert info["WEIGHT"] == 1000


def test_parser_declines_a_foreign_payload() -> None:
    assert shell.ElegooParser().to_filament_protocol(bytes(64)) == (FILAMENT_PROTO_ERR, None)


def test_parser_declines_an_empty_read() -> None:
    assert shell.ElegooParser().to_filament_protocol(b"") == (FILAMENT_PROTO_ERR, None)


def test_uid_is_logged_the_way_a_phone_prints_it() -> None:
    assert shell._uid_as_hex([0x53, 0xFC, 0xB6, 0x09, 0x30, 0x00, 0x04]) == "53:FC:B6:09:30:00:04"


def _with_ntag_reader(monkeypatch, has_chunked_reader):
    ntag_reader = types.ModuleType("elegoo.ntag_reader")
    if has_chunked_reader:
        ntag_reader.ChunkedType2PageReader = object
    monkeypatch.setitem(sys.modules, "elegoo.ntag_reader", ntag_reader)


def test_warns_when_rfid_ntag_predates_the_chunked_reader(monkeypatch, caplog) -> None:
    _with_ntag_reader(monkeypatch, has_chunked_reader=False)
    with caplog.at_level(logging.WARNING, logger="bespok3d.elegoo"):
        _ready(RecordingHub())
    assert "older than 0.1.15" in caplog.text


def test_no_warning_with_a_current_rfid_ntag(monkeypatch, caplog) -> None:
    _with_ntag_reader(monkeypatch, has_chunked_reader=True)
    with caplog.at_level(logging.WARNING, logger="bespok3d.elegoo"):
        _ready(RecordingHub())
    assert caplog.text == ""
