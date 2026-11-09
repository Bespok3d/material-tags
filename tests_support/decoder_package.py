"""Loads a decoder's source directory for its tests the way Klipper loads it on the printer.

At runtime Klipper flattens a decoder's modules into klippy/extras/ and loads its reader shell as a
package member, so the shell imports its siblings package-relative (from . import ...). The tests
reproduce that package context, while the pure modules stay importable by bare name too (import
bambu_fields), both names pointing at one module instance. The runtime-only siblings that the
printer's firmware or rfid-ntag place at install time (filament_protocol, fm175xx_reader) are not
in this repo, so each decoder's conftest stands stubs in for them.
"""
import importlib
import sys
import types
from pathlib import Path
from typing import Any


def register_decoder_package(
    package_name: str, source_dir: Path, leaf_names: tuple[str, ...],
) -> None:
    """Register source_dir as package_name and alias each leaf module to its bare name.

    Stub the runtime siblings first: a leaf that imports one fails to load without it.
    """
    package = types.ModuleType(package_name)
    package.__path__ = [str(source_dir)]
    sys.modules[package_name] = package
    sys.path.insert(0, str(source_dir))
    for leaf_name in leaf_names:
        sys.modules[leaf_name] = importlib.import_module(f"{package_name}.{leaf_name}")


def stub_runtime_sibling(
    package_name: str, sibling_name: str, attributes: dict[str, Any],
) -> None:
    """Stand a stub in for a sibling the printer provides, under its package and bare names."""
    sibling = types.ModuleType(f"{package_name}.{sibling_name}")
    vars(sibling).update(attributes)
    sys.modules[f"{package_name}.{sibling_name}"] = sibling
    sys.modules[sibling_name] = sibling
