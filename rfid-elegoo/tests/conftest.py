"""Test path setup for the Elegoo plugin modules.

At runtime Klipper flattens these modules into klippy/extras/ and loads the shell as
extras.rfid_tag_elegoo, so sibling imports use the package-relative form (from . import
filament_protocol). Tests reproduce that package context by importing the elegoo source
directory as a package named 'elegoo', then aliasing the pure module to its bare name so the
tests that import it by bare name keep working. Both import styles are supported:
  * bare:      import elegoo_fields            (used by the field tests)
  * relative:  from . import filament_protocol (used inside rfid_tag_elegoo at runtime)
The runtime-only sibling the printer's firmware provides (filament_protocol) is not part of this
repo, so a minimal stub stands in for it. Tests load the shell as elegoo.rfid_tag_elegoo.
"""
import importlib
import importlib.util
import sys
import types
from pathlib import Path

_ELEGOO_DIR = (
    Path(__file__).resolve().parent.parent
    / "files" / "klipper" / "klippy" / "extras" / "rfid-tags" / "elegoo"
)

# Register the directory as a package named 'elegoo' so relative imports resolve.
_spec = importlib.util.spec_from_file_location(
    "elegoo", _ELEGOO_DIR / "__init__.py",
    submodule_search_locations=[str(_ELEGOO_DIR)],
)
if _spec is not None and "elegoo" not in sys.modules:
    _pkg = importlib.util.module_from_spec(_spec)
    _pkg.__path__ = [str(_ELEGOO_DIR)]
    sys.modules["elegoo"] = _pkg

# Stub the runtime-only sibling before any plugin module that imports it is loaded.
# Registered under both the package and bare names so either import form resolves.
if "elegoo.filament_protocol" not in sys.modules:
    _filament_protocol = types.ModuleType("elegoo.filament_protocol")
    _filament_protocol.FILAMENT_PROTO_OK = 0
    _filament_protocol.FILAMENT_PROTO_ERR = 1
    _filament_protocol.FILAMENT_INFO_STRUCT = {
        "VENDOR": "NONE", "MANUFACTURER": "NONE", "MAIN_TYPE": "NONE", "SUB_TYPE": "NONE",
        "ALPHA": 0xFF, "COLOR_NUMS": 1, "ARGB_COLOR": 0xFFFFFFFF, "RGB_1": 0xFFFFFF,
        "DIAMETER": 0, "WEIGHT": 0, "HOTEND_MIN_TEMP": 0, "HOTEND_MAX_TEMP": 0,
        "OFFICIAL": False, "CARD_UID": 0,
    }
    sys.modules["elegoo.filament_protocol"] = _filament_protocol
    sys.modules["filament_protocol"] = _filament_protocol

# Also put the dir on sys.path so bare 'import elegoo_fields' works, and alias the bare name to
# the package submodule so both import styles share a single instance.
sys.path.insert(0, str(_ELEGOO_DIR))
sys.modules.setdefault("elegoo_fields", importlib.import_module("elegoo.elegoo_fields"))
