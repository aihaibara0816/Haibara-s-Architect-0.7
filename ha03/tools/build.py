#!/usr/bin/env python3
from pathlib import Path
import sys,argparse,json
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from architect.pipeline import build

def main():
    ap=argparse.ArgumentParser(description="BuildingSpec -> NBT readback -> five PNG views")
    ap.add_argument("spec",type=Path)
    ap.add_argument("--out",type=Path,required=True)
    a=ap.parse_args()
    try:
        r=build(a.spec,a.out)
        print(json.dumps({"build_id":r["build_id"],"out":str(a.out),"size":r["size_xyz"],"non_air_blocks":r["non_air_blocks"],"nbt_bytes":r["nbt"]["bytes"],"views":len(r["views"]),"game":"pending_game_test"},ensure_ascii=False))
    except (ValueError,OSError,KeyError) as e:
        print(f"BUILD FAILED: {e}",file=sys.stderr);return 2
    return 0
if __name__=="__main__":raise SystemExit(main())
