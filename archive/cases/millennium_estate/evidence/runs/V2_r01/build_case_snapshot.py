"""Approved P01 translated into explicit HAF case geometry; no image reconstruction."""
from pathlib import Path
import sys,json,gzip,hashlib,collections,argparse,shutil
C=Path(__file__).resolve().parents[1];ROOT=C.parents[1]
sys.path[:0]=[str(ROOT),str(ROOT/'support')]
from hafusion.classical import Builder
from hafusion.case_io import save_run,dump,sha
from hafusion.design_handoff import compile_handoff
from vendor.inspect_build import load_build,Limits
from detail_lab import states
M=states.make
def rnd(k):return int(hashlib.sha256(k.encode()).hexdigest()[:12],16)/16**12
def inside(x,z,p):
 a=False
 for (x0,z0),(x1,z1) in zip(p,p[1:]+p[:1]):
  if (z0>z)!=(z1>z) and x<(x1-x0)*(z-z0)/(z1-z0)+x0:a=not a
 return a
def cells(p):return {(x,z) for x in range(40) for z in range(32) if inside(x+.5,z+.5,p)}

def build(run):
 source=C/'runs/V1_r06';plan=json.loads((C/'input/approved_P01.json').read_text())
 p=json.loads((source/'params_used.json').read_text());p['version']='V2';p['plan_version']='P01';p.pop('layout_source_towers',None)
 for t in p['towers']:
  if t['type']=='A':t.update(x=t['x']-3,w=30,d=28)
  t['outline']=plan['front' if t['type']=='A' else 'rear']['outline']
 p['implementation_notes']=['P01 outer footprints preserved. Front stair core extends west one cell and south into vestibule to fit stairs/lift.','Room partitions resolved with one-block walls; main private passage adjusted to two-cell width.','Final bedroom/bath/furniture geometry is authored, not a literal reading of colored zone boundaries.']
 b=Builder(p['size_xyz'],p['seed']);base=load_build(source/'building.nbt',Limits(cells=40_000_000,nodes=16_000_000))
 o=json.loads(gzip.decompress((source/'component_ownership.json.gz').read_bytes()));names=o['owner_names'];own={tuple(a[:3]):names[a[3]] for a in o['xyz_owner']}
 for q,mat in base.blocks.items():
  owner=own[q]
  if owner.split('.')[0] in {t['id'] for t in p['towers']}:continue
  # Remove old site props near the enlarged building volumes; ground remains intact.
  if q[1]>=3 and any(t['x']-3<=q[0]<t['x']+t['w']+3 and t['z']-4<=q[2]<t['z']+t['d']+4 for t in p['towers']):continue
  b.put(*q,mat,owner)
 del base,own,o
 modules=[];units=[];lamps=[];stairs=[];entries=[];floors=[];specs=[];plans=[];roofs=[];doors=[]
 for q,s in b.s.blocks.items():
  if s.split('[')[0] in ['minecraft:glowstone','minecraft:sea_lantern','minecraft:end_rod']:lamps.append({'xyz':list(q),'material':s.split(':')[1].split('[')[0],'owner':'garden.retained.light'})
 for t in p['towers']:
  tid=t['id'];X,Z=t['x'],t['z'];typ=t['type'];N=t['storeys'];top=3+5*N;foot=cells(t['outline'])
  edge={q for q in foot if any((q[0]+dx,q[1]+dz) not in foot for dx,dz in [(1,0),(-1,0),(0,1),(0,-1)])}
  def box(r,y,Y,mat,owner):x,z,xx,zz=r;b.box((X+x,y,Z+z),(X+xx,Y,Z+zz),mat,owner)
  def put(x,y,z,mat,owner):b.put(X+x,y,Z+z,mat,owner)
  def light(x,y,z,mat,owner):put(x,y,z,mat,owner);lamps.append({'xyz':[X+x,y,Z+z],'material':mat,'owner':owner})
  for x,z in foot:
   put(x,1,z,'dirt',tid+'.foundation');put(x,2,z,'stone_bricks',tid+'.foundation')
   for f in range(N+1):
    fy=3+5*f;put(x,fy-1,z,'oak_planks' if f<N else 'smooth_stone',tid+'.floor')
    if f:put(x,fy-2,z,'white_concrete',tid+'.ceiling')
  for x,z in edge:
   for y in range(3,top):
    belt=(y-3)%5==4
    pale=(typ=='A' and 11<=x<=20) or (typ=='B' and 13<=x<=23)
    mat='smooth_sandstone' if belt or pale else 'yellow_terracotta'
    # Restrained maintenance patches, stable by facade bay rather than pixel noise.
    if not belt and not pale and y%5 in [1,2] and rnd(tid+str(x//4)+str(z//4)+str(y//10)+'.repair')<.035:mat='sandstone'
    put(x,y,z,mat,tid+'.facade')
  # Distinct roof crowns: residential wings rise above the recessed central roof.
  parts=([(0,0,12,25,4),(12,4,20,25,2),(20,2,30,25,4),(20,25,28,28,1)] if typ=='A' else [(0,0,13,25,4),(13,3,24,21,1),(24,1,37,24,4)])
  for j,(x0,z0,x1,z1,h) in enumerate(parts):
   for x in range(x0-1,x1+1):
    for z in range(z0-1,z1+1):
     # Never bridge the intentionally recessed facade notches.
     if (x,z) not in foot and not any((x+dx,z+dz) in foot for dx,dz in [(1,0),(-1,0),(0,1),(0,-1)]):continue
     inset=max(0,min(x-x0+1,x1-x,z-z0+1,z1-z));yy=top+min(h,inset//2)
     put(x,top-1,z,M('smooth_sandstone_slab',type='top'),tid+'.roof.eave')
     if (X+x,yy,Z+z) not in b.s.blocks:put(x,yy,z,'bricks' if inset%2==0 else 'red_terracotta',tid+f'.roof.wing{j}')
   roofs.append({'tower':tid,'id':tid+f'.roof.wing{j}','rect':[X+x0,Z+z0,X+x1,Z+z1],'base_y':top,'rise':h})
  cx,cz=(11,4) if typ=='A' else (13,3)
  # Compact 7x9 two-wide U stair. Void and landings are resolved through every slab.
  box((cx+1,cz+1,cx+6,cz+6),2,top-1,'minecraft:air',tid+'.stair.void')
  for x in range(cx,cx+7):
   for z in range(cz,cz+9):
    if x in [cx,cx+6] or z in [cz,cz+8]:box((x,z,x+1,z+1),3,top-1,'smooth_sandstone',tid+'.stair.wall')
  box((cx+3,cz+3,cx+4,cz+6),2,top-1,'smooth_sandstone',tid+'.stair.spine')
  lx,lz=(12,13) if typ=='A' else (20,4)
  box((lx,lz,lx+3,lz+3),3,top+2,'light_gray_concrete',tid+'.lift.shell')
  box((lx+1,lz+1,lx+2,lz+2),3,top,'minecraft:air',tid+'.lift.void')
  box((lx-1,lz-1,lx+4,lz+4),top+2,top+3,'smooth_sandstone',tid+'.lift.crown')
  box((lx-1,lz-1,lx+4,lz+4),top+3,top+4,'red_terracotta',tid+'.lift.roof')
  spec={'schema_version':'0.4','project_id':'millennium-v2-'+tid,'route':'original','primary_use':'home','style':'modern','interior_level':'L2','identity_features':['客厅餐厅与厨房组合','独立卧室书房及储物','独立入户与连续公共楼梯'],'coordinates':{'unit':'block','up':'Y','north':'-Z'},'storeys_total':N,'authorized_scope':{'editable_regions':[[X-3,0,Z-4,X+t['w']+3,86,Z+t['d']+4]],'locked_component_ids':[]},'floor_levels':[],'rooms':[],'proposed_modules':[],'circulation_keepouts':[],'lighting':{'coverage_override':'selected_spaces','override_reason':'10/15层住宅，延续用户不要过亮的反馈；按住户启用，公共交通保持照明。'}}
  def module(rid,fy,kind,r,mirror=False):
   x,z,xx,zz=r;mid=rid+'.'+kind+'.'+str(sum(m['room_id']==rid for m in modules));hi=2 if kind in ['bed','wardrobe','television','kitchen','bath','bookcase','desk'] else 1
   rec={'component_id':mid,'room_id':rid,'kind':kind,'bounds_xyz':[X+x,fy,Z+z,X+xx,fy+hi,Z+zz],'use_faces':['interior_open_side'],'variant':int(rnd(rid+'.fabric')*3)};spec['proposed_modules'].append(rec)
   o=mid;variant=rec['variant']
   if kind=='bed':
    box(r,fy,fy+1,['white_concrete','light_gray_concrete','pink_concrete'][variant],o+'.base');box((x,z,xx,z+1),fy,fy+1,'smooth_quartz',o+'.pillow');box((x,z,xx,z+1),fy+1,fy+2,'oak_planks',o+'.headboard')
   elif kind=='wardrobe':box(r,fy,fy+2,'oak_planks' if variant<2 else 'dark_oak_planks',o)
   elif kind=='sofa':
    for u in range(x,xx):put(u,fy,z,M('smooth_quartz_stairs',facing='north'),o)
   elif kind=='armchair':put(x,fy,z,M('oak_stairs',facing='west' if not mirror else 'east'),o)
   elif kind=='coffee':box(r,fy,fy+1,M('dark_oak_slab',type='top'),o)
   elif kind=='television':box(r,fy,fy+1,'dark_oak_planks',o+'.console');box(r,fy+1,fy+2,'black_concrete',o+'.screen')
   elif kind=='dining':
    box((x+1,z,xx-1,zz),fy,fy+1,M('oak_slab',type='top'),o+'.table')
    for v in [z,zz-1]:put(x,fy,v,M('oak_stairs',facing='west'),o+'.chair');put(xx-1,fy,v,M('oak_stairs',facing='east'),o+'.chair')
   elif kind=='kitchen':
    box((x,z,x+1,zz),fy,fy+1,'smooth_quartz',o+'.counter');box((x,z,xx,z+1),fy,fy+1,'smooth_quartz',o+'.return');put(x,fy,z,'gray_concrete',o+'.hob');put(x,fy,zz-1,M('iron_trapdoor',half='top'),o+'.sink');put(xx-1,fy,z,'iron_block',o+'.fridge');put(xx-1,fy+1,z,'iron_block',o+'.fridge')
   elif kind=='bath':
    put(x,fy,z,M('smooth_quartz_stairs',facing='north'),o+'.wc');put(xx-1,fy,zz-1,'smooth_quartz',o+'.basin')
    if zz-z>2:put(x,fy+1,zz-1,'glass_pane',o+'.shower')
   elif kind=='desk':
    box((x,z,xx,z+1),fy,fy+1,M('oak_slab',type='top'),o+'.top');put(x,fy+1,z,'black_concrete',o+'.monitor')
    if zz-z>1:put(x+1 if xx-x>1 else x,fy,z+1,M('oak_stairs',facing='south'),o+'.chair')
   elif kind=='bookcase':box(r,fy,fy+2,'bookshelf',o)
   elif kind=='laundry':put(x,fy,z,'iron_block',o+'.washer');put(xx-1,fy,zz-1,'oak_planks',o+'.basket')
   elif kind=='plant':put(x,fy,z,'red_terracotta',o+'.pot')
   rec['placed_cells']=sum(1 for q,v in b.s.owners.items() if v.startswith(mid));rec['status']='consumed_case_geometry';rec['functional_game_furniture']=False;modules.append(rec)
  def room(uid,f,fun,name,r,entry,mods):
   fy=3+(f-1)*5;x,z,xx,zz=r;rid=uid+'.'+name;bb=[X+x,fy,Z+z,X+xx,fy+3,Z+zz]
   rec={'id':rid,'floor_id':f'{tid}.F{f:02d}','function':fun,'bounds_xyz':bb,'entrances':[[X+entry[0],fy,Z+entry[1]]],'color_intent':'neutral' if fun in ['kitchen','bathroom','utility'] else 'warm'}
   spec['rooms'].append(rec);b.rooms.append(rec)
   box(r,fy-1,fy,'smooth_quartz' if fun in ['kitchen','bathroom','utility'] else 'oak_planks',rid+'.floor')
   for kind,mr in mods:module(rid,fy,kind,mr)
   if rnd(uid+'.occupancy')<.34:
    q=(x+xx)//2,(z+zz)//2;light(q[0],fy+3,q[1],'sea_lantern' if fun in ['kitchen','bathroom','utility'] else 'glowstone',rid+'.recessed_light')
   return rid
  for f in range(1,N+1):
   fy=3+(f-1)*5;fid=f'{tid}.F{f:02d}'
   spec['floor_levels'].append({'id':fid,'floor_y':fy,'upper_floor_y':fy+5,'min_clear_height':3});floors.append({'tower':tid,'floor':f,'floor_y':fy,'ceiling_y':fy+3,'upper_floor_y':fy+5})
   def wall(r,openings=()):
    box(r,fy,fy+3,'smooth_sandstone',fid+'.partition')
    for x,z in openings:box((x,z,x+1,z+1),fy,fy+2,'minecraft:air',fid+'.doorway');doors.append([X+x,fy,Z+z])
   box((cx+4,cz+8,cx+6,cz+9),fy,fy+3,'minecraft:air',fid+'.stair.entry')
   # Lower landing and both full-width ascent tracks.
   if f<N:
    for v,h in [(5,0),(4,1),(3,2)]:
     for u in [1,2]:put(cx+u,fy+h,cz+v,M('smooth_quartz_stairs',facing='north'),fid+'.stair.tread')
    box((cx+1,cz+1,cx+6,cz+3),fy+2,fy+3,'smooth_quartz',fid+'.stair.landing')
    for v,h in [(3,3),(4,4)]:
     for u in [4,5]:put(cx+u,fy+h,cz+v,M('smooth_quartz_stairs',facing='south'),fid+'.stair.tread')
    box((cx+4,cz+5,cx+6,cz+6),fy+4,fy+5,'smooth_quartz',fid+'.stair.top')
    tracks=[]
    for k in [0,1]:
     tracks.append([[X+cx+1+k,fy,Z+cz+6],[X+cx+1+k,fy+1,Z+cz+5],[X+cx+1+k,fy+2,Z+cz+4],[X+cx+1+k,fy+3,Z+cz+3],[X+cx+1+k,fy+3,Z+cz+2],[X+cx+2,fy+3,Z+cz+2],[X+cx+3,fy+3,Z+cz+2],[X+cx+4+k,fy+3,Z+cz+2],[X+cx+4+k,fy+4,Z+cz+3],[X+cx+4+k,fy+5,Z+cz+4],[X+cx+4+k,fy+5,Z+cz+5],[X+cx+4+k,fy+5,Z+cz+6]])
    stairs.append({'id':fid+'.to_next','tracks':tracks,'trace':tracks[0],'from_floor':fy,'to_floor':fy+5,'width':2})
   put(cx+3,fy,cz+6,'iron_bars',fid+'.stair.guard');light(cx+4,fy+3,cz+7,'glowstone',fid+'.common.recessed_light')
   # Elevator is deliberately static. Its thin doors do not count as walkable clearance.
   for yy in [fy,fy+1]:put(lx+2,yy,lz+1,M('iron_trapdoor',open=True,facing='east'),fid+'.lift.static_door')
   if typ=='A':
    wall((11,4,12,25),[(11,17),(11,18)])
    wall((20,4,21,17))
    wall((12,16,20,17),[(17,16),(18,16)])
    box((18,4,20,16),fy-1,fy,'smooth_stone',fid+'.common.floor');box((15,13,20,16),fy-1,fy,'smooth_stone',fid+'.common.floor')
    wall((0,18,11,19),[(3,18),(4,18),(9,18),(10,18)])
    wall((7,19,8,25));wall((12,19,20,20),[(13,19),(14,19)]);wall((16,20,17,25));wall((19,19,20,25),[(19,21),(19,22)])
    wall((20,8,30,9),[(21,8),(22,8)]);wall((23,9,24,23),[(23,12),(23,13),(23,20),(23,21)])
    wall((23,17,30,18));wall((20,22,24,23));wall((23,23,24,28),[(23,24),(23,25)])
    uid=fid+'.U1';rr=[]
    layout=[
     ('living','living',(1,1,11,10),(9,9),[('sofa',(2,3,7,4)),('coffee',(3,6,6,7)),('television',(9,3,10,6)),('armchair',(2,8,3,9)),('plant',(1,1,2,2))]),
     ('dining','dining',(1,10,11,18),(10,17),[('dining',(3,11,7,14)),('wardrobe',(1,15,3,16))]),
     ('kitchen','kitchen',(1,19,7,24),(4,19),[('kitchen',(1,20,6,24))]),
     ('utility','utility',(8,19,11,24),(9,19),[('laundry',(8,21,10,23))]),
     ('study','study',(12,20,16,24),(13,20),[('desk',(12,22,15,24)),('bookcase',(15,20,16,22))]),
     ('bathroom','bath',(17,20,19,24),(18,21),[('bath',(17,20,18,24))]),
     ('bedroom','bed1',(21,3,29,8),(22,7),[('bed',(24,4,26,7)),('wardrobe',(27,6,29,7)),('desk',(22,3,24,5))]),
     ('bedroom','bed2',(24,10,29,17),(24,12),[('bed',(26,11,28,14)),('wardrobe',(25,15,29,16))]),
     ('bedroom','master',(24,18,29,24),(24,20),[('bed',(26,18,28,21)),('wardrobe',(25,22,29,23))]),
     ('bathroom','ensuite',(21,23,23,27),(22,24),[('bath',(21,23,22,27))]),
     ('storage','dressing',(24,24,27,27),(24,24),[('wardrobe',(25,26,27,27))])]
    for fun,name,r,e,ms in layout:rr.append(room(uid,f,fun,name,r,e,ms))
    units.append({'id':uid,'tower':tid,'floor':f,'floor_y':fy,'entry':[X+17,fy,Z+16],'rooms':rr,'lit':rnd(uid+'.occupancy')<.34})
    keeps=[(18,4,20,13),(17,14,20,16),(12,17,23,19),(21,9,23,22)]
    ex,ez=18,4
   else:
    box((14,13,23,21),fy-1,fy,'smooth_stone',fid+'.common.floor')
    for side in [0,1]:
     zz=side;end=24-side
     def pt(q):x,z=q;return (36-x if side else x,z+zz)
     def rect(r):x,z,xx,zz1=r;return (37-xx if side else x,z+zz,37-x if side else xx,zz1+zz)
     def mw(r,ds=()):wall(rect(r),[pt(q) for q in ds])
     mw((13,0,14,25-zz),[(13,18),(13,19)]);mw((6,1,7,9));mw((0,9,13,10),[(3,9),(4,9),(9,9),(10,9)])
     mw((0,12,11,13));mw((6,13,7,17));mw((10,12,11,18),[(10,15),(10,16)]);mw((0,17,10,18),[(3,17),(4,17)])
     uid=fid+f'.U{side+1}';rr=[]
     data=[('bedroom','bed1',(1,1,6,9),(4,8),[('bed',(2,2,4,5)),('wardrobe',(1,7,3,8)),('desk',(4,2,6,4))]),('bedroom','bed2',(7,1,12,9),(9,8),[('bed',(8,2,10,5)),('wardrobe',(10,7,12,8)),('desk',(10,2,12,4))]),('kitchen','kitchen',(1,13,6,17),(4,16),[('kitchen',(1,13,5,16))]),('bathroom','bath',(7,13,10,17),(9,15),[('bath',(7,13,9,17))]),('living_dining','living',(1,18,12,end-zz),(11,19),[('sofa',(2,18,6,19)),('coffee',(3,20,5,21)),('dining',(7,20,11,22))])]
     for fun,name,r,e,ms in data:rr.append(room(uid,f,fun,name,rect(r),pt(e),[(k,rect(q)) for k,q in ms]))
     uentry=pt((13,18));units.append({'id':uid,'tower':tid,'floor':f,'floor_y':fy,'entry':[X+uentry[0],fy,Z+uentry[1]],'rooms':rr,'lit':rnd(uid+'.occupancy')<.34})
    keeps=[(14,14,23,20),(11,10,13,20),(24,11,26,21)]
    ex,ez=18,20
   for rr in keeps:
    x,z,xx,zz=rr;spec['circulation_keepouts'].append([X+x,fy,Z+z,X+xx,fy+2,Z+zz])
   # Windows follow rooms, with partial grille installation and consistent household variation.
   wdefs=([(0,5,(-1,0),5,1),(0,13,(-1,0),4,1),(0,21,(-1,0),3,1),(5,24,(0,1),4,1),(14,24,(0,1),2,1),(25,2,(0,-1),5,1),(29,5,(1,0),3,1),(29,13,(1,0),4,1),(29,20,(1,0),4,1)] if typ=='A' else [(3,0,(0,-1),3,1),(9,0,(0,-1),3,1),(0,4,(-1,0),4,1),(0,15,(-1,0),2,1),(0,21,(-1,0),3,1),(33,1,(0,-1),3,2),(27,1,(0,-1),3,2),(36,5,(1,0),4,2),(36,16,(1,0),2,2),(36,21,(1,0),3,2)])
   for wi,(x,z,n,w,un) in enumerate(wdefs):
    uid=fid+f'.U{un}';key=uid+f'.window{wi}';fr=b.frame(X+x,Z+z,n);lo=-(w//2);hi=lo+w;style='cage' if rnd(key+'.net')<.26 else 'flush' if rnd(key+'.net')<.44 else 'none'
    glass=['glass_pane','light_blue_stained_glass_pane','gray_stained_glass_pane'][int(rnd(uid+'.glass')*3)]
    fr.rect(lo,hi,fy+1,fy+3,0,1,glass,key+'.glass');fr.rect(lo-1,hi+1,fy,fy+1,1,2,M('smooth_sandstone_slab',type='top'),key+'.sill')
    if style!='none':
     fr.rect(lo,hi,fy+1,fy+3,1,2,'iron_bars',key+'.grille')
     if style=='cage':fr.rect(lo,hi,fy,fy+1,1,2,M('iron_trapdoor',half='top'),key+'.base');fr.rect(lo,lo+1,fy+1,fy+3,0,2,'iron_bars',key+'.side');fr.rect(hi-1,hi,fy+1,fy+3,0,2,'iron_bars',key+'.side')
    if rnd(key+'.ac')<.35:fr.put(lo-1,fy+1,1,'iron_block',key+'.ac');fr.put(lo-1,fy+1,2,M('iron_trapdoor',open=True,facing='north'),key+'.ac_screen')
    b.windows.append({'id':key,'unit_id':uid,'floor_y':fy,'normal':n,'center':[X+x,fy+1,Z+z],'width':w,'security':style,'glass':glass})
   # Deep balconies; open and enclosed variants remain stable per household.
   bal=[(1,-3,11,0,'north',4,0,1),(24,28,28,30,'south',25,27,1)] if typ=='A' else [(1,25,11,28,'south',4,24,1),(26,24,36,27,'south',30,23,2)]
   for j,(a,z0,aa,z1,face,doorx,doorz,un) in enumerate(bal):
    uid=fid+f'.U{un}';o=uid+f'.balcony{j}';closed=rnd(uid+'.balcony')<.32
    box((a,z0,aa,z1),fy-1,fy,'smooth_sandstone',o+'.slab')
    rz=z0 if face=='north' else z1-1
    for x in range(a,aa):
     put(x,fy,rz,'smooth_sandstone' if closed else 'iron_bars',o+'.rail')
     if closed:
      for y in [fy+1,fy+2]:put(x,y,rz,'glass_pane',o+'.glass')
    for z in range(z0,z1):
     for x in [a,aa-1]:put(x,fy,z,'iron_bars',o+'.side')
    box((doorx,doorz,doorx+2,doorz+1),fy,fy+2,'minecraft:air',o+'.door')
    if f>1:box((a,z0,aa,z1),fy-2,fy-1,M('smooth_sandstone_slab',type='top'),o+'.soffit')
    if rnd(uid+'.plant')<.5:
     put(a+1,fy,z0+1,'red_terracotta',o+'.planter');put(a+1,fy+1,z0+1,'azalea_leaves',o+'.plant')
   if f==1:
    box((ex,ez,ex+2,ez+1),3,6,'minecraft:air',tid+'.main_entry')
    entries.append({'id':tid,'entry':[X+ex,3,Z+ez],'width':2,'direction':-1 if typ=='A' else 1,'core_landing':[X+cx+4,3,Z+cz+7]})
    if typ=='A':
     box((18,-2,20,5),2,3,'smooth_stone',tid+'.entry.porch');box((17,0,21,3),7,8,'gray_stained_glass',tid+'.entry.canopy')
    else:box((17,21,21,27),2,3,'smooth_stone',tid+'.entry.porch');box((16,21,22,24),7,8,'gray_stained_glass',tid+'.entry.canopy')
    # Compact mail/bench element at an off-route wall, no furniture scattered across the lobby.
    if typ=='B':box((14,14,16,15),3,4,'oak_planks',tid+'.lobby.mail');put(14,3,17,M('oak_stairs',facing='west'),tid+'.lobby.bench')
  plans.append(compile_handoff(spec));specs.append(spec)
 # Connect every revised entrance to the retained diagonal garden path.
 pathset=set(map(tuple,json.loads((source/'paths.json').read_text())['cells_xz']))
 pathset={q for q in pathset if not any(t['x']-2<=q[0]<t['x']+t['w']+2 and t['z']-4<=q[1]<t['z']+t['d']+4 for t in p['towers'])}
 for e,t in zip(entries,p['towers']):
  ex,_,ez=e['entry'];garden_z=(108-(ex-15)//5) if t['type']=='A' else (66-(ex-15)//5)
  near=min(pathset,key=lambda q:(q[0]-ex)**2+(q[1]-garden_z)**2)
  # 3-cell-wide L connector, with ground-level clearance only outside the facade.
  for z in range(min(ez,near[1]),max(ez,near[1])+1):
   for x in range(ex-1,ex+3):
    local=(x-t['x'],z-t['z'])
    if local not in cells(t['outline']) or (x in [ex,ex+1] and z==ez):pathset.add((x,z))
  for x in range(min(ex,near[0]),max(ex,near[0])+1):
   for z in range(near[1]-1,near[1]+2):pathset.add((x,z))
 for x,z in pathset:
  b.put(x,2,z,'smooth_sandstone','site.path.v2')
  for y in [3,4]:
   q=(x,y,z)
   if not b.s.owners.get(q,'').split('.')[0] in {t['id'] for t in p['towers']}:b.s.set(q,'minecraft:air','site.path.clearance')
 # Clear false stale lamp records removed by path and building refinement.
 lamps=[l for l in lamps if b.s.blocks.get(tuple(l['xyz']),'').split('[')[0]=='minecraft:'+l['material']]
 out=save_run(C,run,p,b,Path(__file__),{'route':'original','approved_plan':'P01','units':len(units),'furniture_modules':len(modules),'lit_households':sum(u['lit'] for u in units),'lighting_policy':'Recessed; selected households; common circulation on'})
 for n,obj in [('units',units),('lamps',lamps),('stairs',stairs),('entries',entries),('floor_levels',floors),('module_consumption',modules),('design_handoffs',specs),('resolved_plans',plans),('roof_parts',roofs),('paths',{'cells_xz':sorted(pathset)}),('doorway_cells',doors)]:dump(out/(n+'.json'),obj)
 dump(out/'provenance.json',{'source_baseline_sha256':sha(source/'building.nbt'),'approved_plan_sha256':sha(C/'input/approved_P01.json'),'status':'authored_case_geometry','web_research_this_revision':False,'source_code':sha(Path(__file__))})
 print('RUN',out,flush=True)
if __name__=='__main__':
 ap=argparse.ArgumentParser();ap.add_argument('--run',required=True);build(ap.parse_args().run)
