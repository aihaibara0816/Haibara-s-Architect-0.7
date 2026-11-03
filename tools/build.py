from pathlib import Path
import sys,argparse,json
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from hafusion.pipeline import build
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--run',required=True);p.add_argument('--cache');p.add_argument('--materials')
    p.add_argument('--core-max-shift',type=int,choices=range(4),default=3)
    p.add_argument('--ring-inset',type=float,default=1.6)
    a=p.parse_args();build(a.run,cache_root=a.cache,material_overrides=json.loads(Path(a.materials).read_text()) if a.materials else None,core_max_shift=a.core_max_shift,ring_inset=a.ring_inset)
