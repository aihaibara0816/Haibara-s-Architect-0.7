"""Lossless, curve-atomic print modules from accepted B03 final NBT."""
from pathlib import Path
import sys,json,math,copy,hashlib,gzip,collections,csv,io,os
P=Path(__file__).resolve().parents[1];sys.path[:0]=[str(P/'deps'),str(P/'src')]
import nbtlib as n
import numpy as np
from scipy.spatial import cKDTree
from link_geometry import read_connection
R=P/'runs/B03S1';D=P/'deliverables/B03S1';R.mkdir(parents=True,exist_ok=True);D.mkdir(parents=True,exist_ok=True)
B=P/'runs/B03';spec=json.loads((B/'spec.json').read_text());v=spec['variants'][1];srcpath=B/v['filename'];src=n.load(srcpath)
assert hashlib.sha256(srcpath.read_bytes()).hexdigest()==v['sha256']=='74a0f683029fe4fe34067f84d08d311bfd4626849cb89e1926722a6a1252255b'
off=np.array(v['origin_in_station_coordinates']);owner=json.loads((B/'GuangzhouEast_LinkOnly_owners.json').read_text())
entries={tuple(np.array(e['pos'],int)+off):e for e in src['blocks']};owns={tuple(np.array(e['pos'],int)+off):owner[','.join(str(int(t))for t in e['pos'])] for e in src['blocks']}
palette=src['palette'];CURVES={};route_pts=collections.defaultdict(list);route_labels=collections.defaultdict(list)
def flatpart(route,p):
 d=p[0]-p[2]
 if d>=198:return 'E01' if route=='WS' else 'E02'
 if d<=(-190 if route=='WS' else -250):return 'S01' if route=='WS' else 'S02'
 return 'M01' if d>70 else 'M02' if d>-60 else 'M03'
for p,e in entries.items():
 for co in e.get('nbt',{}).get('Connections',[]):
  if not co['Primary']:continue
  q=tuple(np.array(p)+co['Positions'][1]['Pos'])
  desc=next(c for c in spec['curves'] if c['p']==list(p) and c['q']==list(q))
  route=desc['owner'];i=int(desc['id'][2:4]);part=('E01' if i<=4 else 'S01') if route=='WS' else ('S02' if i<=3 else 'E02')
  points=read_connection(p,co,901);CURVES[desc['id']]={'part':part,'p':p,'q':q,'points':points}
  route_pts[route].extend(points[:,[0,2]]);route_labels[route].extend([part]*len(points))
for line in spec['lines']:
 route=line['owner']
 if route not in ['WS','SW']:continue
 a,b=np.array(line['a']),np.array(line['b']);points=np.linspace(a,b,1001)
 route_pts[route].extend(points[:,[0,2]]);route_labels[route].extend([flatpart(route,p)for p in points])
trees={r:cKDTree(pts)for r,pts in route_pts.items()};parts={}
for p,e in entries.items():
 own=owns[p]
 if own in ['WS','SW']:
  _,i=trees[own].query(np.array(p)[[0,2]]);parts[p]=route_labels[own][i]
 elif own in ['main_E','east']:parts[p]='E01' if p[0]<=634 else 'E02'
 elif own=='main_S':parts[p]='S01' if p[2]<730 else 'S02'
 elif own=='signals':continue
 else:raise AssertionError((p,own))
# Connections form indivisible endpoint clusters. No BE is cut or duplicated.
for c in CURVES.values():
 for p in [c['p'],c['q']]:parts[p]=c['part']
# A pier footprint remains in one print file, including its whole vertical column.
for route in ['WS','SW']:
 feet={(p[0],p[2])for p in entries if p[1]==0 and owns[p]==route};remaining=set(feet)
 while remaining:
  seed=remaining.pop();cc={seed};todo=[seed]
  while todo:
   x,z=todo.pop()
   for dx,dz in [(1,0),(-1,0),(0,1),(0,-1)]:
    q=x+dx,z+dz
    if q in remaining:remaining.remove(q);cc.add(q);todo.append(q)
  votes=collections.Counter(parts[(x,0,z)]for x,z in cc);part=votes.most_common(1)[0][0]
  for p in entries:
   if (p[0],p[2])in cc and owns[p]==route:parts[p]=part
# Signal and pedestal travel with their target rail, not an arbitrary X/Z cut.
for p,e in entries.items():
 be=e.get('nbt',{})
 if str(be.get('id'))=='create:track_signal':
  target=tuple(np.array(p)+be['TargetTrack']);assert target in parts
  parts[p]=parts[target]
  pedestal=(p[0],p[1]-1,p[2]);assert owns[pedestal]=='signals';parts[pedestal]=parts[target]
assert set(parts)==set(entries)
for id,c in CURVES.items():assert parts[c['p']]==parts[c['q']]==c['part'],id
names={
'E01':('东枢纽·西转南','E01_东枢纽_西转南.nbt','东侧外分缓降、下穿转弯、南下缓坡及部分正线'),
'E02':('东枢纽·南转西','E02_东枢纽_南转西.nbt','北上缓坡、回转汇入西行线及东端正线'),
'M01':('中间直道·东段','M01_中间直道_东段.nbt','两股 Y=20 直道，靠东枢纽一段'),
'M02':('中间直道·中段','M02_中间直道_中段.nbt','两股 Y=20 直道，中间一段'),
'M03':('中间直道·南段','M03_中间直道_南段.nbt','两股 Y=20 直道，靠南枢纽一段'),
'S01':('南枢纽·西转南','S01_南枢纽_西转南.nbt','下行缓坡、汇入南行线及北端正线'),
'S02':('南枢纽·南转西','S02_南枢纽_南转西.nbt','南端外分、爬升跨线、上行缓坡及南端正线')}
def snbt(e):return palette[int(e['state'])].snbt(),e['nbt'].snbt() if 'nbt'in e else None
C=n.Compound;I=n.Int;LI=lambda a:n.List[n.Int](list(map(int,a)));LC=lambda a:n.List[n.Compound](a)
def save(id,title,filename,description,points,folder):
 lo=np.min(list(points),axis=0);hi=np.max(list(points),axis=0);size=hi-lo+1
 used=sorted({int(entries[p]['state'])for p in points});remap={v:i for i,v in enumerate(used)};out=[]
 for p in sorted(points,key=lambda p:(p[1],p[2],p[0])):
  e=copy.deepcopy(entries[p]);e['pos']=LI(np.array(p)-lo);e['state']=I(remap[int(e['state'])]);out.append(e)
 f=n.File({'DataVersion':copy.deepcopy(src['DataVersion']),'size':LI(size),'palette':LC([copy.deepcopy(palette[i])for i in used]),'blocks':LC(out),'entities':LC([])},gzipped=True)
 dest=D/folder/filename;dest.parent.mkdir(exist_ok=True);buf=io.BytesIO();f.write(buf);blob=gzip.compress(buf.getvalue(),mtime=0);tmp=dest.with_suffix('.partial');tmp.write_bytes(blob);os.replace(tmp,dest)
 curveids=[id for id,c in CURVES.items()if c['p']in points]
 return {'id':id,'name':title,'file':str(dest.relative_to(D)),'description':description,'origin_station_xyz':lo.tolist(),'origin_linkonly_xyz':(lo-off).tolist(),'size_xyz':size.tolist(),'block_entries':len(out),'curve_ids':curveids,'file_bytes':dest.stat().st_size,'sha256':hashlib.sha256(dest.read_bytes()).hexdigest(),'bounding_chunk_span_worst_alignment_xz':[math.ceil((int(size[k])+15)/16)for k in [0,2]],'occupied_chunks_at_station_origin_0':len({(p[0]//16,p[2]//16)for p in points}),'suggested_load_center_station_xyz':[(int(lo[0])+int(hi[0]))//2,0,(int(lo[2])+int(hi[2]))//2]}
modules=[]
for id,(title,file,desc)in names.items():modules.append(save(id,title,file,desc,{p for p in entries if parts[p]==id},'print_parts'))
groups=[]
for id,title,prefix in [('E','东枢纽','E'),('M','中间直道','M'),('S','南枢纽','S')]:
 groups.append(save(id,title,title+'_整组.nbt','整组备用；与对应打印分件内容相同，任选一种打印。',{p for p in entries if parts[p].startswith(prefix)},'whole_groups'))
# Independent read-back: exact world-position/state/BE reconstruction, no duplicate cells.
report={'source_sha256':v['sha256'],'source_block_entries':len(entries),'sets':{},'errors':[],'game':'not_run'}
for setname,items in [('print_parts',modules),('whole_groups',groups)]:
 rebuilt={};qarecs=[]
 for meta in items:
  f=n.load(D/meta['file']);lo=np.array(meta['origin_station_xyz']);tiles={tuple(np.array(e['pos'],int)+lo):e for e in f['blocks']};pal=f['palette'];ends=0
  assert len(tiles)==len(f['blocks'])
  for p,e in tiles.items():
   assert p not in rebuilt,(setname,'duplicate',p)
   rebuilt[p]=(pal[int(e['state'])].snbt(),e['nbt'].snbt() if 'nbt'in e else None)
   for co in e.get('nbt',{}).get('Connections',[]):
    q=tuple(np.array(p)+co['Positions'][1]['Pos']);assert q in tiles,(meta['id'],'external endpoint',p,q)
    mates=[m for m in tiles[q].get('nbt',{}).get('Connections',[])if tuple(np.array(q)+m['Positions'][1]['Pos'])==p]
    assert len(mates)==1 and bool(mates[0]['Primary'])!=bool(co['Primary']);ends+=1
   if 'TargetTrack'in e.get('nbt',{}):assert tuple(np.array(p)+e['nbt']['TargetTrack'])in tiles
  assert all(len(p)==3 and all(int(f['size'][k])>int(e['pos'][k])>=0 for k in range(3))for p,e in tiles.items())
  qarecs.append({'id':meta['id'],'blocks':len(tiles),'reciprocal_curve_endpoint_records':ends,'external_curve_endpoints':0,'external_signal_targets':0})
 assert set(rebuilt)==set(entries)
 diffs=[p for p in entries if rebuilt[p]!=snbt(entries[p])];assert not diffs,(setname,diffs[:5])
 report['sets'][setname]={'reassembled_block_entries':len(rebuilt),'exact_state_and_block_entity_match':True,'duplicates':0,'missing':0,'modules':qarecs}
manifest={'run':'B03S1','kind':'lossless_split_of_accepted_B03','source':v,'original_station_size':[150,44,220],'accepted_feedback':'User considers B03 substantially improved; line geometry frozen for segmentation.','axis':{'X':'east','Y':'up','Z':'south'},'reference_origins_station_xyz':{'station':[0,0,0],'complete':spec['variants'][0]['origin_in_station_coordinates'],'linkonly':v['origin_in_station_coordinates']},'recommended_parts':modules,'whole_groups_alternative':groups,'printing_notes':['Use either the seven small print parts or the three whole groups; do not build both sets on top of one another.','Every Bezier connection has both endpoints in its own file. No shared BE, no external endpoint and no join patch is required.','Boundaries meet through ordinary straight rails, with the source block states retained exactly.','NBT is sparse. Do not print implicit empty space as destructive air; Create cannon replacement mode should retain air unless clearing a verified corridor intentionally.','Offsets refer to the NBT minimum corner. Keep +X east / +Z south and do not rotate individual modules.','Actual chunk loading must cover the active part, its rail endpoints and the cannon. Smaller files reduce the span, but do not force-load chunks.','Create 6.0.10 source checks target chunk loading and requires cannon-to-schematic-anchor distance less than 256; no claim of live server testing.','Whole groups and parts exclude the station, six-to-two throats and preceding 144-block approach modules. Align to the B03 complete scene.'],'validation':'validation.json','planning':'Triangle proposals are conceptual overlays only; no extra industrial building is inserted in any NBT.'}
(R/'manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2));(R/'validation.json').write_text(json.dumps(report,ensure_ascii=False,indent=2));(R/'parts_owner.json').write_text(json.dumps({','.join(map(str,p)):parts[p]for p in entries}))
with (D/'放置坐标.csv').open('w',encoding='utf-8-sig',newline='')as f:
 w=csv.writer(f);w.writerow(['编号','名称','文件','相对原站X','Y','Z','尺寸X','Y','Z','方块条目','最大包围区块X','Z'])
 for a in modules+groups:w.writerow([a['id'],a['name'],a['file'],*a['origin_station_xyz'],*a['size_xyz'],a['block_entries'],*a['bounding_chunk_span_worst_alignment_xz']])
for a in modules+groups:print(a['id'],a['name'],'origin',a['origin_station_xyz'],'size',a['size_xyz'],'blocks',a['block_entries'],'curves',len(a['curve_ids']))
print('Exact recombination of both sets passed:',len(entries),'blocks; no curve crosses a file boundary.')
