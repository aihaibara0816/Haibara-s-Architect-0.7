"""Import immutable, attributed BuildKit modules; never duplicate the NBT writer."""
from pathlib import Path
import importlib.util
import sys

ROOT = Path(__file__).resolve().parents[1]

def _load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module

core = _load("architect_legacy_voxel_core", ROOT / "vendor/buildkit_v03/tools/voxel_core.py")
inspector = _load("architect_legacy_inspector", ROOT / "vendor/buildkit_v03/tools/inspect_build.py")

