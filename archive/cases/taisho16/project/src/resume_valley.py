from pathlib import Path
import sys,pickle
ROOT=Path(__file__).resolve().parents[1]
s=(ROOT/'src/build_valley.py').read_text()
oldrun,newrun=sys.argv[1:3];sys.argv=[sys.argv[0],newrun]
exec(s[:s.index('mods=all_types')])
exec(s[s.index('# Helpers rotate'):s.index('# Reserve a connected')])
exec(s[s.index('def route('):s.index('trunks=[')])
for sub in [n.Compound,n.Int,n.String,n.Double,n.Float,n.Short,n.Byte]:
 cls=n.List[sub];setattr(n.tag,cls.__name__,cls)
globals().update(pickle.loads((ROOT/'runs'/oldrun/'placement_checkpoint.pkl').read_bytes()))
for m in mods:m.local_spec['run']=newrun
exec(s[s.index('# Reserve true geometry'):])
