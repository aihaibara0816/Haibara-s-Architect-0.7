"""B03S2: exact rail-block datums, all cut joints, and the omitted south approach.
The accepted connector and its ten existing NBT files remain byte-identical.
"""
from pathlib import Path
import sys,json,copy,io,gzip,os,hashlib,csv,collections,math
P=Path(__file__).resolve().parents[1];sys.path[:0]=[str(P/'deps'),str(P/'src')]
import nbtlib as n
import numpy as np
from link_geometry import read_connection
R=P/'runs/B03S2';D=P/'deliverables/B03S1';R.mkdir(parents=True,exist_ok=True);(D/'approach_parts').mkdir(exist_ok=True)
m=json.loads((P/'runs/B03S1/manifest.json').read_text());s=json.loads((P/'runs/B03/spec.json').read_text())
sha=lambda b:hashlib.sha256(b).hexdigest()
for v in s['variants']:assert sha((P/'runs/B03'/v['filename']).read_bytes())==v['sha256']
full=n.load(P/'runs/B03/GuangzhouEast_Complete.nbt');offset=s['variants'][0]['origin_in_station_coordinates'];pal=full['palette']
world={tuple(int(v)+offset[i]for i,v in enumerate(e['pos'])):e for e in full['blocks']}
sig=lambda f,e:(f['palette'][int(e['state'])].snbt(),e.get('nbt',n.Compound()).snbt())
rail=lambda e:str(pal[int(e['state'])]['Name'])=='create:track'
allrails={p:e for p,e in world.items() if rail(e)}
mods={};placed={};trackparts={}
for a in m['recommended_parts']+m['whole_groups_alternative']:
 f=n.load(D/a['file']);assert sha((D/a['file']).read_bytes())==a['sha256'];o=a['origin_station_xyz']
 cells={tuple(int(v)+o[i]for i,v in enumerate(e['pos'])):e for e in f['blocks']}
 mods[a['id']]={'meta':a,'file':f,'cells':cells}
 if len(a['id'])>1:
  for p,e in cells.items():
   assert p not in placed;placed[p]=a['id'];assert sig(f,e)==sig(full,world[p])
   if str(f['palette'][int(e['state'])]['Name'])=='create:track':trackparts[p]=(a['id'],str(f['palette'][int(e['state'])]['Properties']['shape']))
gap={p:e for p,e in world.items()if 118<=p[0]<=132 and 0<=p[1]<=7 and 364<=p[2]<=653 and p not in placed}
assert len(gap)==9606 and not(set(gap)&set(placed))
extra=[]
for id,z0,length in [('A01',364,144),('A02',508,144),('A03',652,2)]:
 cells={p:e for p,e in gap.items()if z0<=p[2]<z0+length};origin=[118,0,z0];size=[15,8,length]
 used=sorted({int(e['state'])for e in cells.values()});remap={old:new for new,old in enumerate(used)};out=[]
 for p,e in sorted(cells.items(),key=lambda a:(a[0][1],a[0][2],a[0][0])):
  e=copy.deepcopy(e);e['pos']=n.List[n.Int]([int(p[i]-origin[i])for i in range(3)]);e['state']=n.Int(remap[int(e['state'])]);out.append(e)
 f=n.File({'DataVersion':copy.deepcopy(full['DataVersion']),'size':n.List[n.Int](size),'palette':n.List[n.Compound]([copy.deepcopy(pal[i])for i in used]),'blocks':n.List[n.Compound](out),'entities':n.List[n.Compound]([])})
 filename=f'approach_parts/{id}_南侧补接直道_{length}格.nbt';dest=D/filename;buf=io.BytesIO();f.write(buf);blob=gzip.compress(buf.getvalue(),mtime=0);tmp=dest.with_suffix('.partial');tmp.write_bytes(blob);os.replace(tmp,dest)
 g=n.load(dest);readback={tuple(int(v)+origin[i]for i,v in enumerate(e['pos'])):e for e in g['blocks']}
 assert set(readback)==set(cells)
 for p,e in readback.items():assert sig(g,e)==sig(full,world[p])
 meta={'id':id,'name':f'南侧补接直道·{length}格','file':filename,'origin_station_xyz':origin,'size_xyz':size,'block_entries':len(out),'sha256':sha(blob),'file_bytes':len(blob),'rail_run_z_inclusive':[z0,z0+length-1],'standard_profile_local_rail_blocks':[[4,7,0],[10,7,0]],'source':'Exact extraction from B03 complete main_S, not a copy of the original standard_144 file.'}
 extra.append(meta);mods[id]={'meta':meta,'file':g,'cells':readback}
 for p,e in readback.items():
  assert p not in placed;placed[p]=id
  if str(g['palette'][int(e['state'])]['Name'])=='create:track':trackparts[p]=(id,str(g['palette'][int(e['state'])]['Properties']['shape']))
# Count coordinate increments, with the existing last rail block being step zero.
datums=[{'id':'P0','name':'东侧144格直道末端·北股轨道方块','p':[462,33,30]}, {'id':'Q0','name':'南侧144格直道末端·西股轨道方块','p':[122,7,363]}]
PIN={
 'E01':([462,33,30],'P0',[0,0,0],'与 P0 重合；E01 向站内覆盖末端 4 排，不额外留空。'),
 'E02':([654,33,36],'P0',[192,0,6],'从 P0 向东 192、向南 6，同高；这是南转西的回接点。'),
 'M01':([490,20,292],'E01',[491,20,291],'从 E01 西南端 (491,20,291)，西 1、南 1，同高。'),
 'M02':([426,20,356],'M01',[427,20,355],'从 M01 西转南股末端 (427,20,355)，西 1、南 1，同高。'),
 'M03':([360,20,422],'M02',[361,20,421],'从 M02 西转南股末端 (361,20,421)，西 1、南 1，同高。'),
 'S01':([122,7,654],'A03',[122,7,653],'从 A03 西股末端，向南 1，同高；即 Q0 向南第 291 格。'),
 'S02':([122,7,730],'S01',[122,7,729],'从 S01 西股正线末端，向南 1，同高。'),
 'A01':([122,7,364],'Q0',[0,0,1],'从 Q0 向南 1，同高；占第 1–144 格。'),
 'A02':([122,7,508],'Q0',[0,0,145],'从 Q0 向南 145，同高；占第 145–288 格。'),
 'A03':([122,7,652],'Q0',[0,0,289],'从 Q0 向南 289，同高；占第 289–290 格。'),
 'E':([462,33,30],'P0',[0,0,0],'整组东枢纽，与 P0 重合。'),
 'M':([490,20,292],'E01',[491,20,291],'整组中间直道，与 E01 末端西 1、南 1 的轨道方块对齐。'),
 'S':([122,7,654],'A03',[122,7,653],'整组南枢纽，第一排正线放在 Q0 向南第 291 格。')}
anchors=[]
for id,(point,ref,delta,note)in PIN.items():
 a=mods[id]['meta'];local=[point[i]-a['origin_station_xyz'][i]for i in range(3)]
 assert tuple(point)in mods[id]['cells'];assert str(mods[id]['file']['palette'][int(mods[id]['cells'][tuple(point)]['state'])]['Name'])=='create:track'
 anchors.append({'id':id,'name':a['name'],'file':a['file'],'origin':a['origin_station_xyz'],'size':a['size_xyz'],'rail_pin_station':point,'rail_pin_local':local,'origin_minus_pin':[-v for v in local],'instruction':note,'reference':ref,'reference_data':delta,'sha256':a['sha256']})
steps={'xo':[(1,0,0),(-1,0,0)],'zo':[(0,0,1),(0,0,-1)],'nd':[(1,0,-1),(-1,0,1)],'pd':[(1,0,1),(-1,0,-1)]}
seams=[]
for p,(part,shape)in trackparts.items():
 for d in steps[shape]:
  q=tuple(p[i]+d[i]for i in range(3))
  if q in trackparts and part<trackparts[q][0] and shape==trackparts[q][1]:
   other=trackparts[q][0];seams.append({'a':part,'b':other,'pa':list(p),'pb':list(q),'delta':list(d),'a_local':[p[i]-mods[part]['meta']['origin_station_xyz'][i]for i in range(3)],'b_local':[q[i]-mods[other]['meta']['origin_station_xyz'][i]for i in range(3)],'shape':shape})
seams.sort(key=lambda a:(a['a'],a['b'],a['pa']))
# Independent corridor checks: every ordinary mainline rail cell after the two 144 modules is now supplied.
for x in range(463,721):
 for z in [30,36]:assert (x,33,z)in trackparts
for z in range(364,901):
 for x in [122,128]:assert (x,7,z)in trackparts
curves=[]
for c in s['curves']:
 p,q=c['p'],c['q'];e=world[tuple(p)]
 be=next(co for co in e['nbt']['Connections']if co['Primary'] and [int(p[i])+int(co['Positions'][1]['Pos'][i])for i in range(3)]==q)
 points=read_connection(p,be,241)
 curves.append({'id':c['id'],'module':trackparts[tuple(p)][0],'p':p,'q':q,'delta':[q[i]-p[i]for i in range(3)],'points':np.round(points,4).tolist(),'note':'Endpoint block displacement; NOT arc length or slope run.'})
for q in [(x,33,z)for x in range(459,463)for z in [30,36]]:assert trackparts[q][0]=='E01'
report={'run':'B03S2','original_10_nbt_unchanged':True,'new_gap_blocks':len(gap),'original_link_blocks':61119,'expanded_addon_blocks':len(placed),'new_modules_exact_source_match':True,'new_modules_do_not_overlap_old_parts':True,'east_main_463_through_720_both_tracks':True,'south_main_364_through_900_both_tracks':True,'anchors_checked':len(anchors),'inter_module_rail_joints':len(seams),'game':'not_run'}
spec={'run':'B03S2','coordinate_type':'Integer block coordinates of create:track. Not player position, rail edge, or rendered curve handle.','datums':datums,'datum_Q0_minus_P0':[-340,-26,333],'extra_modules':extra,'anchors':anchors,'seams':seams,'curves':curves,'scope':'Only placement instructions and three south approach extracts added. Original ten connector NBTs unchanged.','standard_note':'Specific to this B03 geometry and original cardinal orientation. Matching rail ports does not make an arbitrary 144-block template interchangeable.'}
(R/'interface_spec.json').write_text(json.dumps(spec,ensure_ascii=False,indent=2));(R/'validation.json').write_text(json.dumps(report,ensure_ascii=False,indent=2))
with (D/'GuangzhouEast_Interface_Coordinates.csv').open('w',encoding='utf-8-sig',newline='')as f:
 w=csv.writer(f);w.writerow(['编号','文件','定位轨道X','定位轨道Y','定位轨道Z','轨道在NBT内X','轨道在NBT内Y','轨道在NBT内Z','原点X','原点Y','原点Z','数格接法'])
 for a in anchors:w.writerow([a['id'],a['file'],*a['rail_pin_station'],*a['rail_pin_local'],*a['origin'],a['instruction']])
print(json.dumps(report,ensure_ascii=False))
