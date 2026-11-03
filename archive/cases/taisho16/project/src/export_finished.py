from pathlib import Path
import sys,pickle
ROOT=Path(__file__).resolve().parents[1]
s=(ROOT/'src/build_valley.py').read_text();oldrun,newrun=sys.argv[1:3];sys.argv=[sys.argv[0],newrun]
exec(s[:s.index('mods=all_types')])
for sub in[n.Compound,n.Int,n.String,n.Double,n.Float,n.Short,n.Byte]:
 cls=n.List[sub];setattr(n.tag,cls.__name__,cls)
globals().update(pickle.loads((ROOT/'runs'/oldrun/'finished_checkpoint.pkl').read_bytes()))
from finish_fixes import apply
changed=apply(city,height,rawheight)
delta={(q['x'],q['z']):q for q in terrain['delta']}
for x,z in changed:
 if rawheight[x,z]!=height[x,z]:delta[x,z]={'x':x,'z':z,'before':rawheight[x,z],'after':height[x,z]}
 else:delta.pop((x,z),None)
terrain['delta']=sorted(delta.values(),key=lambda q:(q['x'],q['z']));terrain['changed_columns']=len(delta);terrain['unchanged_columns']=W*D-len(delta);terrain['cut_blocks']=sum(max(0,q['before']-q['after'])for q in delta.values());terrain['fill_blocks']=sum(max(0,q['after']-q['before'])for q in delta.values())
for m in mods:m.local_spec['run']=newrun
exec(s[s.index('# Exact-state sparse NBT exporter.'):])
