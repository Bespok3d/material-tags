"""Test path setup for the Creality plugin modules.

At runtime Klipper flattens these modules into klippy/extras/ and loads the shell as
extras.rfid_tag_creality, so sibling imports use the package-relative form
(from . import creality_types). Tests reproduce that package context by importing the creality
source directory as a package named 'creality', then aliasing its leaf modules to their bare
names so bare-import modules (aes_min, creality_keys) and the standalone tests that import them
by bare name keep working. Both import styles are supported:
  * bare:      import creality_fields            (used by tests and by leaf modules)
  * relative:  from . import creality_types       (used inside creality_fields at runtime)
The two runtime-only siblings that rfid-ntag places at install time (filament_protocol,
fm175xx_reader) are not part of this repo, so minimal stubs stand in for them.
"""
import importlib
import importlib.util
import sys
import types
from pathlib import Path

_CREALITY_DIR = (
    Path(__file__).resolve().parent.parent
    / "files" / "klipper" / "klippy" / "extras" / "rfid-tags" / "creality"
)

# Register the directory as a package named 'creality' so relative imports resolve.
_spec = importlib.util.spec_from_file_location(
    "creality", _CREALITY_DIR / "__init__.py",
    submodule_search_locations=[str(_CREALITY_DIR)],
)
if _spec is not None and "creality" not in sys.modules:
    _pkg = importlib.util.module_from_spec(_spec)
    _pkg.__path__ = [str(_CREALITY_DIR)]
    sys.modules["creality"] = _pkg

# Also put the dir on sys.path so bare 'import creality_fields' works, and alias each leaf
# module to its bare name pointing at the package submodule (a single instance each).
sys.path.insert(0, str(_CREALITY_DIR))
for _name in ("aes_min", "creality_keys", "creality_types", "creality_fields"):
    _mod = importlib.import_module(f"creality.{_name}")
    sys.modules.setdefault(_name, _mod)

# Stub the two runtime-only siblings that rfid-ntag places at install time. Registered under
# both the package and bare names so either import form resolves.
if "creality.filament_protocol" not in sys.modules:
    _fp = types.ModuleType("creality.filament_protocol")
    _fp.FILAMENT_PROTO_OK = 0
    _fp.FILAMENT_PROTO_ERR = -1
    _fp.FILAMENT_INFO_STRUCT = {
        "VENDOR": "NONE", "MANUFACTURER": "NONE", "MAIN_TYPE": "NONE", "SUB_TYPE": "NONE",
        "WEIGHT": 0, "SKU": 0, "RGB_1": 0, "COLOR_NUMS": 0, "ALPHA": 0, "ARGB_COLOR": 0,
        "DIAMETER": 0, "HOTEND_MIN_TEMP": 0, "HOTEND_MAX_TEMP": 0,
        "CARD_UID": [], "OFFICIAL": False, "MF_DATE": "",
    }
    sys.modules["creality.filament_protocol"] = _fp
    sys.modules["filament_protocol"] = _fp

if "creality.fm175xx_reader" not in sys.modules:
    _fm = types.ModuleType("creality.fm175xx_reader")
    _fm.FM175XX_OK = 0
    _fm.FM175XX_CARD_READ_ERR = -29
    _fm.FM175XX_M1_CARD_AUTH_MODE_B = 1
    sys.modules["creality.fm175xx_reader"] = _fm
    sys.modules["fm175xx_reader"] = _fm
