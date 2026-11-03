"""Reused BuildKit NBT writer, verified by its separate bounded reader."""
from .legacy import core,inspector
from .voxelizer import scene_from_readback

def export_and_readback(scene,spec,path):
    meta=core.export_structure(scene,path,spec["environment"]["data_version"],spec["output"]["include_air"])
    build=inspector.load_build(path)
    reread=scene_from_readback(build)
    if reread.size!=scene.size or reread.blocks!=scene.blocks or reread.fingerprint()!=scene.fingerprint():
        raise ValueError("Export/readback geometry mismatch")
    return meta,build,inspector.inspect(build)

