"""Demonstrate a parameter revision, immutable outputs and measured locality."""
from pathlib import Path
import copy,sys,argparse
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from architect.legacy import ROOT,inspector
from architect.spec_loader import load_spec
from architect.pipeline import dump,build

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--out",type=Path,default=ROOT/"output/retail_store_revision")
    args=parser.parse_args()
    spec=load_spec(ROOT/"examples/retail_store/building_spec.json")
    spec["revision"]=2
    canopy=next(c for c in spec["components"] if c["component_id"]=="canopy")
    canopy["parameters"]["min_m"][2]=2
    canopy["provenance"]["basis"]="局部参数编辑实验：仅将雨棚向正面延长1个研究米，其余构件及证据保持不变。"
    if args.out.exists():raise ValueError("Revision output exists; use --out with a new directory")
    spec_path=ROOT/"examples/retail_store/revision_canopy.json"
    if not spec_path.exists():dump(spec_path,spec)
    elif load_spec(spec_path)!=spec:raise ValueError("Existing revision spec differs; preserve it and create a new version")
    report=build(spec_path,args.out)
    before=inspector.load_build(ROOT/"output/retail_store/building.nbt")
    after=inspector.load_build(args.out/"building.nbt")
    diff=inspector.compare(before,after,roi=[14,6,2,19,6,5])
    if diff["changes_outside_roi"]!=0 or diff["visible_state_changes"]!=6:raise ValueError("Revision locality acceptance failed")
    dump(args.out/"revision_diff.json",diff)
    dump(ROOT/"reports/revision_diff.json",diff)
    print(report["build_id"],diff)
if __name__=="__main__":main()
