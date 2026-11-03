"""Taisho14: 18 different buildings, two sloping streets and public nodes."""
from pathlib import Path
import sys,json,copy,hashlib,io,gzip,random,math
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'pydeps'),str(ROOT/'src'),str(ROOT/'support'),str(ROOT)]
import nbtlib as n
import taisho_states
from prototype_base import Study
from quarter_types import all_types
from detail_lab import states as S
from vendor.voxel_core import Scene,export_structure,parse_state
RUN=sys.argv[1]if len(sys.argv)>1 else'Q01';SEED=int(sys.argv[2])if len(sys.argv)>2 else 141145
OUT=ROOT/'runs'/RUN;OUT.mkdir(parents=True,exist_ok=False)
W,H,D=196,60,158
mods=all_types(SEED);byid={m.id:m for m in mods}
transitions={24:14,43:13,62:12,81:11,100:10,119:9,138:8,157:7}
def grade(x):
 v=15
 for a,b in transitions.items():
  if x>=a:v=b
 return v
def centre(x,row=0):return int(round((50 if row==0 else 100)+3*math.sin(max(0,min(1,x/175))*math.pi*(.8 if row==0 else 1.2))))
def river(z):return 184+int(round(2*math.sin(z*.048)))
# The actual lot mix is authored; dimensions, programs, entry levels and rotations are explicit.
layout=[('Bookshop',6,15,False,0),('Textile',36,22,False,0),('Library',59,16,False,0),('School',88,10,False,0),('Clinic',125,18,False,0),('Sake',151,30,False,0),('Tea',8,56,True,0),('Photo',29,58,True,0),('Pharmacy',54,54,True,0),('Inn',90,55,True,0),('Florist',134,62,True,0),('Residence',6,109,True,1),('Bakery',31,112,True,1),('Post',54,112,True,1),('Workshop',78,109,True,1),('Bath',106,110,True,1),('Clock',151,76,False,1),('Station',146,111,True,1)]
placements=[]
for id,x,z,rev,row in layout:
 m=byid[id];ex=x+(m.w-1-m.entry[0]if rev else m.entry[0]);f=grade(ex)-2*row
 placements.append((m,[x,f-2,z],rev,row))
city=Study('Taisho14',W,D,1,'櫻坂風貌街｜十八栋街区');city.blocks={};city.seed=SEED
height={};road=set();routes=[];route_nodes=[]
def ground(x,z):
 hill=22*math.exp(-(((x-9)/29)**2+((z-7)/17)**2));shoulder=4*math.exp(-(((x-49)/50)**2+((z-9)/20)**2))
 return max(4,int(grade(x)+hill+shoulder-max(0,z-65)/40))
for x in range(W):
 for z in range(D):
  h=ground(x,z)
  for row in[0,1]:
   if abs(z-centre(x,row))<=6 and x<178:h=grade(x)-2*row
  for m,o,rev,row in placements:
   if o[0]+1<=x<o[0]+m.w-1 and o[2]+1<=z<o[2]+m.d-1:h=o[1]+2
  rc=river(z)
  if abs(x-rc)<=4:h=2
  elif x>=rc-9:h=4
  height[x,z]=h
  for y in range(h+1):city.p(x,y,z,'stone'if y<h-2 else'dirt'if y<h else'grass_block','terrain')
  if abs(x-rc)<=4:city.p(x,2,z,'gravel','creek.bed');city.p(x,3,z,'stone'if z in[0,D-1]else'water','creek',**({}if z in[0,D-1]else{'level':0}))
def pave(x,z,f,edge=False,stair=None):
 for y in (range(f+1)if x<178 else[f-1]):city.p(x,y,z,'stone','road.foundation')
 rr=random.Random(SEED+(x//4)*719+(z//3)*997)
 mat='stone_bricks'if edge else('andesite'if rr.random()<.15 else'mossy_cobblestone'if rr.random()<.06 else'cobblestone')
 city.p(x,f,z,mat,'road.surface')
 if stair:city.p(x,f+1,z,'cobblestone_stairs','road.step',facing=stair)
 for y in range(f+2 if stair else f+1,H):city.p(x,y,z,'air')
 road.add((x,z));height[x,z]=f
for row in[0,1]:
 route=[]
 for x in range(3,W-1):
  cz=centre(x,row);f=grade(x)-2*row
  for z in range(cz-3,cz+4):pave(x,z,f,abs(z-cz)==3,'west'if x in transitions else None)
  route.append([x+.5,f+1,cz+.5])
 routes.append({'id':'upper_street'if row==0 else'lower_street','path':route})
 for x in range(178,W-1):
  for z in[centre(x,row)-4,centre(x,row)+4]:
   city.p(x,f,z,'stone_bricks','bridge.edge');city.p(x,f+1,z,'dark_oak_fence','bridge.rail')
# Connecting lanes at west edge, between the photo shop and pharmacy, and by the creek.
for cx in[4,51,173]:
 z0=centre(cx,0);z1=centre(cx,1);f0=grade(cx);path=[]
 for z in range(z0,z1+1):
  step=int(z>z0+16)+int(z>z0+32);f=f0-step;isstep=z in[z0+17,z0+33]
  for x in range(cx-1,cx+2):pave(x,z,f,False,'north'if isstep else None)
  path.append([cx+.5,f+1,z+.5])
 routes.append({'id':'lane.'+str(cx),'path':path})
def rotstate(st,rev):
 if not rev:return st
 name,p=parse_state(st);mp={'north':'south','south':'north','east':'west','west':'east'}
 if p.get('facing')in mp:p['facing']=mp[p['facing']]
 for a,b in[('north','south'),('east','west')]:
  if a in p or b in p:p[a],p[b]=p.get(b,'false'),p.get(a,'false')
 return name+('['+','.join(k+'='+v for k,v in sorted(p.items()))+']'if p else'')
def pt(q,m,o,rev,continuous=False):
 x,y,z=q
 if rev:x=(m.w if continuous else m.w-1)-x;z=(m.d if continuous else m.d-1)-z
 return[x+o[0],y+o[1],z+o[2]]
records=[];alluses=[];alldoors=[];alllights=[];allstairs=[]
for m,o,rev,row in placements:
 for q,st in m.blocks.items():
  if q[1]<2:continue
  if m.id in['Bookshop','Pharmacy','Inn']and q in[(3,3,3),(m.w-2,3,5),(3,3,m.d-6)]:continue
  owner=m.owners.get(q,'')
  if q[1]==2 and(st.startswith('minecraft:grass_block')or owner.endswith('.street')):continue
  if any(owner.endswith('.'+s)for s in['groundcover','pot','shrub']):continue
  g=pt(q,m,o,rev)
  if q[1]==2:
   for y in range(g[1]):city.p(g[0],y,g[2],'stone_bricks'if y>=g[1]-2 else'stone','building.foundation')
  city.p(*g,rotstate(st,rev),owner)
 for q,be in m.bes.items():
  g=tuple(pt(q,m,o,rev))
  if g in city.blocks:city.bes[g]=copy.deepcopy(be)
 for e in m.entities:
  ee=copy.deepcopy(e);q=pt([int(ee[k])for k in['TileX','TileY','TileZ']],m,o,rev)
  for k,a in zip(['TileX','TileY','TileZ'],q):ee[k]=n.Int(a)
  ee['Pos']=n.List[n.Double]([n.Double(a)for a in pt(list(map(float,ee['Pos'])),m,o,rev,True)])
  if rev:ee['facing']=n.Byte((int(ee['facing'])+2)%4)
  city.entities.append(ee)
 rec=m.stats();rec.update(size=[m.w,m.h,m.d],origin=o,rotated_180=rev,entry_world=pt(m.entry,m,o,rev),upper_start=m.upper_start,street_row=row);records.append(rec)
 for u in m.uses:alluses.append({**u,'pos':pt(u['pos'],m,o,rev),'floor_block_y':u['floor_block_y']+o[1]})
 for d in m.doors:alldoors.append({**d,'pos':pt(d['pos'],m,o,rev),'lintel':pt(d['lintel'],m,o,rev),'facing':{'north':'south','south':'north','east':'west','west':'east'}[d['facing']]if rev else d['facing']})
 for l in m.lights:alllights.append({'position':pt(l['position'],m,o,rev),'support':pt(l['support'],m,o,rev)})
 for p in m.stair_paths:allstairs.append({'id':m.id,'path':[pt(q,m,o,rev,True)for q in p],'start_y':o[1]+3,'end_y':o[1]+9})
 ex,ey,ez=rec['entry_world'];destz=centre(ex,row);floor=ey-1
 for z in range(min(ez,destz),max(ez,destz)+1):
  for x in range(ex-1,ex+2):
   if(z>ez if not rev else z<ez):
    for y in range(floor+1):city.p(x,y,z,'stone_bricks'if y==floor else'stone','entry.landing')
    for y in range(floor+1,floor+3):city.p(x,y,z,'air')
 local=copy.deepcopy(rec);local['origin']=[0,0,0];local['rotated_180']=False
 m.local_spec={'case_id':m.id,'run':RUN,'seed':SEED,'buildings':[local],'uses':m.uses,'doors':m.doors,'lights':m.lights,'stairs':m.stair_paths,'spawn_local':[m.entry[0],3,m.entry[2]+1],'upper_start':m.upper_start}
 # Make the individual study's approach a real paved strip at its own level.
 for x in range(m.entry[0]-1,m.entry[0]+2):m.p(x,2,m.entry[2]+1,'stone_bricks','threshold')

# A forecourt in front of the school and a compact clock plaza are actual public ground.
for x0,X,z0,Z,f,kind in[(98,119,42,47,grade(105),'school.court'),(149,171,94,105,5,'clock.square'),(149,178,105,114,5,'station.forecourt')]:
 for x in range(x0,X):
  for z in range(z0,Z):
   for y in range(f+1):city.p(x,y,z,'stone','public.foundation')
   city.p(x,f,z,'stone_bricks'if(x+z)%11 else'polished_andesite',kind)
   for y in range(f+1,f+3):city.p(x,y,z,'air')
 for x in range(x0+2,min(x0+7,X-2)):city.p(x,f+1,Z-2,'dark_oak_slab','public.bench',type='bottom');city.p(x,f+1,Z-1,'dark_oak_trapdoor','public.bench.back',facing='south',open=True)
# West garden and riverbank keep their own levels, not a flat carpet around the houses.
for x in range(5,148):
 z=13;h=height[x,z]
 if(x,h+1,z)not in city.blocks:
  for y in range(max(0,h-2),h+1):city.p(x,y,z,'stone_bricks'if x%13 else'mossy_stone_bricks','retaining.edge')
for row in[0,1]:
 for x in[8,31,53,79,104,129,173,191]:
  z=centre(x,row)-4;f=grade(x)-2*row
  for y in range(f+1,f+6):city.p(x,y,z,'dark_oak_fence','street.lamp.post')
  city.p(x+1,f+5,z,'dark_oak_slab','street.lamp.arm',type='bottom');city.p(x,f+5,z,'dark_oak_slab','street.lamp.cap',type='bottom');city.p(x+1,f+4,z,'lantern','street.lamp',hanging=True)
  alllights.append({'position':[x+1,f+4,z],'support':[x+1,f+5,z]})
# Connected utility rhythm, one line along each street, with irregular pole intervals.
for row in[0,1]:
 poles=[(x,centre(x,row)+4)for x in[5,35,68,111,150,176]]
 for x,z in poles:
  f=grade(x)-2*row
  for y in range(f+1,f+13):city.p(x,y,z,'stripped_spruce_log','utility.pole',axis='y')
  for zz in range(z-2,z+3):city.p(x,f+12,zz,'dark_oak_fence','crossarm')
 for (xa,za),(xb,zb)in zip(poles,poles[1:]):
  for x in range(xa+1,xb):
   t=(x-xa)/(xb-xa);z=round(za+(zb-za)*t);y=round((grade(xa)-2*row+12)*(1-t)+(grade(xb)-2*row+12)*t-1.2*math.sin(t*math.pi))
   city.p(x,y,z,'chain','utility.wire',axis='x')
def tree(x,z,h,kind='spruce'):
 f=height[x,z];trunk=kind+'_log';leaves=kind+'_leaves'
 if any((x,y,z)in city.blocks for y in range(f+1,f+h)):return
 for y in range(f+1,f+h+1):city.p(x,y,z,trunk,'tree.trunk',axis='y')
 if kind=='cherry':
  for dx,dy,dz in[(-2,h-1,0),(2,h,1),(0,h+2,-1)]:
   for xx in range(min(x,x+dx),max(x,x+dx)+1):city.p(xx,f+h-2,z,'cherry_log','tree.branch',axis='x')
   for xx in range(x+dx-3,x+dx+4):
    for zz in range(z+dz-3,z+dz+4):
     for yy in range(f+dy-2,f+dy+3):
      if 0<=xx<W and 0<=zz<D and((xx-x-dx)/3)**2+((yy-f-dy)/2)**2+((zz-z-dz)/3)**2<=1.15 and(xx,yy,zz)not in city.blocks:city.p(xx,yy,zz,leaves,'tree.canopy',persistent=True,distance=1)
 else:
  for y in range(f+3,f+h+3):
   r=max(1,min(4,(f+h+2-y)//2+1))
   for xx in range(x-r,x+r+1):
    for zz in range(z-r,z+r+1):
     if 0<=xx<W and 0<=zz<D and abs(xx-x)+abs(zz-z)<=r+1 and(xx,y,zz)not in city.blocks:city.p(xx,y,zz,leaves,'tree.canopy',persistent=True,distance=1)
for x,z,h in[(8,5,10),(23,5,11),(39,6,9),(55,5,10),(74,5,9),(129,6,10),(148,9,9),(170,16,10),(191,20,9),(190,77,8),(191,130,8),(12,151,8),(39,151,9),(70,151,8),(97,152,8),(133,150,9)]:tree(x,z,h)
for x,z,h in[(5,90,7),(57,96,6),(141,88,7),(175,124,7)]:tree(x,z,h,'cherry')
rr=random.Random(SEED)
for x in range(2,W-2):
 for z in range(2,D-2):
  f=height[x,z]
  if not city.blocks.get((x,f,z),'').startswith('minecraft:grass_block')or(x,f+1,z)in city.blocks:continue
  if any(abs(z-centre(x,row))<5 for row in[0,1]):continue
  patch=(math.sin(x*.32)+math.cos(z*.27))*.5
  if rr.random()<(.30 if patch>.3 else.10):city.p(x,f+1,z,rr.choices(['short_grass','fern','oxeye_daisy','dandelion'],[50,35,10,5])[0],'planting.groundcover')
for x,z in[(175,23),(176,27),(175,31),(177,35),(173,26),(172,30),(176,138),(175,142),(177,145)]:
 f=height[x,z]
 if city.blocks.get((x,f,z),'').startswith('minecraft:grass_block'):
  for y in range(f+1,f+8):city.p(x,y,z,'bamboo','bamboo.grove',age=1,leaves='large'if y>=f+5 else'none',stage=1)
for m,o,rev,row in placements:
 for x,z in[(3,m.d-3),(m.w-4,m.d-3)]:
  q=pt([x,3,z],m,o,rev)
  if(q[0],q[2])not in road and(q[0],q[1]+1,q[2])not in city.blocks:
   city.p(q[0],q[1]-1,q[2],'stone_bricks','pot.base');city.p(*q,'terracotta','street.pot');city.pot(q[0],q[1]+1,q[2])
def clean(m):
 for q,be in list(m.bes.items()):
  name=m.blocks.get(q,'minecraft:air').split('[')[0];expect='minecraft:sign'if name.endswith('_wall_sign')else'minecraft:bed'if name.endswith('_bed')else'minecraft:banner'if name.endswith('_wall_banner')else name
  if str(be['id'])!=expect:del m.bes[q]
def save(m,name,sp,size):
 clean(m);sc=Scene(size,max_cells=4000000)
 for q,st in m.blocks.items():sc.set(q,st,m.owners.get(q,'detail'))
 S.connect(sc)
 for st in set(sc.blocks.values()):S.validate(st)
 raw=OUT/(name+'.geometry.tmp');export_structure(sc,raw,include_air=False);f=n.load(raw)
 for b in f['blocks']:
  q=tuple(map(int,b['pos']))
  if q in m.bes:b['nbt']=m.bes[q]
 f['entities']=n.List[n.Compound]([n.Compound({'pos':copy.deepcopy(e['Pos']),'blockPos':n.List[n.Int]([e[k]for k in['TileX','TileY','TileZ']]),'nbt':e})for e in m.entities])
 buf=io.BytesIO();f.write(buf);p=OUT/(name+'.nbt');p.write_bytes(gzip.compress(buf.getvalue(),mtime=0))
 sp.update(source_nbt_sha256=hashlib.sha256(p.read_bytes()).hexdigest(),non_air=len(sc.blocks),size_xyz=list(size),block_entities=len(m.bes),entities=len(m.entities));(OUT/(name+'_spec.json')).write_text(json.dumps(sp,ensure_ascii=False,indent=2));return sp
for m in mods:save(m,m.id,m.local_spec,(m.w,m.h,m.d))
sp={'case_id':'Taisho14','run':RUN,'mainline':'HAF 0.4','seed':SEED,'buildings':records,'uses':alluses,'doors':alldoors,'lights':alllights,'stairs':allstairs,'routes':routes,'spawn_local':[192,6,centre(192,1)],'floor_profile':transitions,'scope':'Original 18-building mixed Taisho-romance streetscape; authored layout and bounded seeded surface/plant variation.','status':{'game':'pending','aesthetic':'pending user review'}}
save(city,'Taisho14',sp,(W,H,D));(OUT/'spec.json').write_text(json.dumps(sp,ensure_ascii=False,indent=2));(OUT/'heightmap.json').write_text(json.dumps([[height[x,z]for x in range(W)]for z in range(D)]));print('BUILT',RUN,'buildings',len(mods),'blocks',len(city.blocks),flush=True)
