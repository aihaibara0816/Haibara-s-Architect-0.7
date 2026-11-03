from pathlib import Path
import sys
ROOT = Path(__file__).resolve().parents[1]
CASE = ROOT / 'case'
for p in [ROOT, ROOT/'ha03', CASE/'src', CASE/'vendor', ROOT/'upstream/PlanCraft/tools/building']:
    if str(p) not in sys.path: sys.path.insert(0, str(p))
