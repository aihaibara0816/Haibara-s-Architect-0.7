"""Independent readback checks for P4 water topology and preserved buildings."""
from pathlib import Path
import sys,json,gzip,hashlib,collections
import numpy as np
from scipy.ndimage import label
C=Path(__file__).resolve().parents[1];ROOT=C.parents[1];sys.path[:0]=[str(ROOT),str(ROOT/'support')]
import rural_states
from detail_lab import states
from vendor.inspect_build import load_build,Limits
run=sys.argv[1];R=C/'runs'/run;A=C/'runs/P3_B4'
limits=Limits(cells=40_000_000,nodes=16_000_000)
old=load_build(A/'building.nbt',limits).blocks;new=load_build(R/'building.nbt',limits).blocks
p=json.loads((R/'params_used.json').read_text());q=json.loads(gzip.decompress((A/'component_ownership.json.gz').read_bytes()))
protected={tuple(v[:3]):old[tuple(v[:3])] for v in q['xyz_owner'] if q['owner_names'][v[3]].startswith('R')}
house_changes=[pos for pos,st in protected.items() if new.get(pos)!=st]
water=np.zeros((288,320),dtype=bool)
for (x,y,z),st in new.items():
 if y==2 and st.startswith('minecraft:water'):water[z,x]=True
labs,n=label(water);root=int(labs[6,6]);field_results=[]
for f in p['fields']:
 a,c,u,v=f['bounds'];inside=[(pos,st) for pos,st in new.items() if a<pos[0]<u-1 and c<pos[2]<v-1 and states.family(st)=='crop']
 bad=[pos for pos,st in inside if pos[1]!=3]
 wetcells=np.argwhere(water[c+1:v-1,a+1:u-1]);connected=all(labs[z+c+1,x+a+1]==root for z,x in wetcells)
 field_results.append({'id':f['id'],'crops':len(inside),'water_cells':len(wetcells),'crop_height_errors':len(bad),'connected_to_main':bool(connected)})
oldlamps={pos:st for pos,st in old.items() if any(s in st for s in ('glowstone','sea_lantern'))}
lampchanges=[pos for pos,st in oldlamps.items() if new.get(pos)!=st]
extra=p['landscape_revision']['extra_lights'];missing_extra=[pos for pos in extra if 'glowstone' not in new.get(tuple(pos),'')]
newpaths=p['landscape_revision']['new_path_cells'];path_blockers=[[x,yy,z] for x,y,z in newpaths for yy in (4,5) if (x,yy,z) in new]
report={'new_path_cells':len(newpaths),'new_path_blockers':path_blockers,'run':run,'source_nbt_sha256':hashlib.sha256((R/'building.nbt').read_bytes()).hexdigest(),'baseline_run':'P3_B4','protected_house_blocks':len(protected),'changed_house_blocks':house_changes,'primary_water_y':2,'primary_water_components':int(n),'primary_water_cells':int(water.sum()),'fields':field_results,'old_lights':len(oldlamps),'changed_old_lights':lampchanges,'added_lights':len(extra),'missing_added_lights':missing_extra,'paddy_count':p['landscape_revision']['paddy_count'],'game_fluid_updates':'not simulated; geometry checks only'}
(R/'landscape_check.json').write_text(json.dumps(report,ensure_ascii=False,indent=2))
assert not path_blockers and not house_changes and not lampchanges and not missing_extra and len(protected)>10000
assert n==1 and all(f['connected_to_main'] and not f['crop_height_errors'] for f in field_results)
print(json.dumps({k:v for k,v in report.items() if k!='fields'},ensure_ascii=False,indent=2))
