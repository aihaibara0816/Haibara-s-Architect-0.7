#!/usr/bin/env python3
from pathlib import Path
import argparse,sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from architect.packet_adapter import adapt
from architect.pipeline import dump

if __name__=="__main__":
    ap=argparse.ArgumentParser(description="Upstream packet + reviewed construction overlay -> BuildingSpec. Without overlay: research context only.")
    ap.add_argument("packet",type=Path);ap.add_argument("--overlay",type=Path);ap.add_argument("--out",required=True,type=Path)
    a=ap.parse_args()
    if a.out.exists():ap.error("Output exists; choose a new path")
    try:
        result=adapt(a.packet,a.overlay);a.out.parent.mkdir(parents=True,exist_ok=True);dump(a.out,result)
        print(f"{'BuildingSpec' if a.overlay else 'Research context (not executable geometry)'} written to {a.out}")
    except (ValueError,OSError,KeyError) as e:ap.error(str(e))
