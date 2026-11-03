"""Adapt the preserved V5 NBT mesh exporter; emit separate comparison scenes."""
from pathlib import Path
import sys,argparse
ROOT=Path(__file__).resolve().parents[1]

def export(label,run,nbt):
    src=(ROOT/'case/views/src/export_scene.py').read_text()
    # This wrapper changes I/O only. Block parts, light approximation and face
    # visibility are the preserved V5 implementation, applied equally to both.
    src=src.replace("ROOT=Path(__file__).resolve().parents[1]", "ROOT=Path("+repr(str(ROOT/'previews'/label))+")")
    src=src.replace("PROJECT=ROOT/'source_project' if (ROOT/'source_project').exists() else ROOT.parent", "PROJECT=Path("+repr(str(ROOT/'case'))+")")
    src=src.replace("run=PROJECT/'runs'/args.run", "run=Path("+repr(str(run))+")")
    src=src.replace("canton280_plaza_v5.nbt",nbt)
    (ROOT/'previews'/label).mkdir(parents=True,exist_ok=True)
    ns={'__name__':'hafusion_preview_export','__file__':__file__}
    exec(compile(src,'preserved_v5_preview_export','exec'),ns)
    saved=sys.argv;sys.argv=[__file__,'--run',label]
    try:ns['main']()
    finally:sys.argv=saved

if __name__=='__main__':
    a=argparse.ArgumentParser();a.add_argument('label');a.add_argument('run');a.add_argument('nbt');x=a.parse_args()
    export(x.label,Path(x.run).resolve(),x.nbt)
