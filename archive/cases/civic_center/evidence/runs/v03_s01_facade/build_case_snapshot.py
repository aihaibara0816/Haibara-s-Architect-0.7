from build_case import *
from vendor.voxel_core import Scene,export_structure
from vendor.inspect_build import load_build,Limits
from detail_lab.states import boxes
p=json.loads((C/'parameters.json').read_text());obj=Civic(p,'sample');obj.mass();obj.facade();obj.b.finish()
s=Scene((12,56,44));lo=(54,10,44)
for q,v in obj.b.s.blocks.items():
 qq=tuple(q[i]-lo[i] for i in range(3))
 if all(0<=qq[i]<s.size[i] for i in range(3)):s.set(qq,v,obj.b.s.owners[q])
out=C/'samples/facade_s01';out.mkdir(parents=True,exist_ok=False);meta=export_structure(s,out/'Facade.nbt',include_air=False);rb=load_build(out/'Facade.nbt',Limits(cells=1000000,nodes=1000000));assert s.blocks==rb.blocks
checks={}
for typ in ['slab','glass','iron','orange']:
 matches=[v for v in s.blocks.values() if typ in v]
 checks[typ]={'count':len(matches),'visual_box_examples':{v:boxes(v) for v in sorted(set(matches))[:4]}}
dump(out/'sample_review.json',{'source':'frozen V0.3 east main facade','origin_in_whole':lo,'size':s.size,'meta':meta,'states':checks,'readback_exact':True,'game':'pending'})
# A sample-only immutable run at original coordinates lets the same camera be reused.
b=Builder(p['size'])
for q,v in s.blocks.items():b.put(*(q[i]+lo[i] for i in range(3)),v,s.owners[q])
save_run(C,'v03_s01_facade',p,b,Path(__file__),{'sample_only':True})
