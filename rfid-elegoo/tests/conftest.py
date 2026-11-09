"""Loads the Elegoo decoder modules as package 'elegoo', the way Klipper loads them.

tests_support/decoder_package.py explains the package setup. The runtime-only sibling the
printer's firmware provides is stubbed with the values the reader shell relies on. Tests load the
shell as elegoo.rfid_tag_elegoo.
"""
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "tests_support"))

# The shared helper lives outside this decoder's dir, so it imports only after the path insert.
from decoder_package import register_decoder_package, stub_runtime_sibling  # noqa: E402

ELEGOO_DIR = (
    REPO_ROOT / "rfid-elegoo" / "files" / "klipper" / "klippy" / "extras" / "rfid-tags" / "elegoo"
)

stub_runtime_sibling("elegoo", "filament_protocol", {
    "FILAMENT_PROTO_OK": 0,
    "FILAMENT_PROTO_ERR": 1,
    "FILAMENT_INFO_STRUCT": {
        "VENDOR": "NONE", "MANUFACTURER": "NONE", "MAIN_TYPE": "NONE", "SUB_TYPE": "NONE",
        "ALPHA": 0xFF, "COLOR_NUMS": 1, "ARGB_COLOR": 0xFFFFFFFF, "RGB_1": 0xFFFFFF,
        "DIAMETER": 0, "WEIGHT": 0, "HOTEND_MIN_TEMP": 0, "HOTEND_MAX_TEMP": 0,
        "OFFICIAL": False, "CARD_UID": 0,
    },
})
register_decoder_package("elegoo", ELEGOO_DIR, ("elegoo_fields",))
