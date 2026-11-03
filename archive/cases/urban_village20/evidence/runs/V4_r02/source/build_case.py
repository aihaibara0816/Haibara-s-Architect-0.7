"""Original Guangdong urban-village case; explicit design, not image reconstruction."""
from pathlib import Path
import sys,json,hashlib,collections,argparse,math
C=Path(__file__).resolve().parents[1];ROOT=C.parents[1]
sys.path[:0]=[str(ROOT),str(ROOT/'support')]
from hafusion.classical import Builder
from hafusion.case_io import save_run,dump,sha
from hafusion.design_handoff import compile_handoff
from detail_lab import states
import site20
M=states.make
def rnd(s):return int(hashlib.sha256(str(s).encode()).hexdigest()[:12],16)/16**12
PAL={
 'ivory':('white_concrete',['smooth_quartz','quartz_block'],'light_gray_concrete','gray_stained_glass_pane'),
 'sand':('smooth_sandstone',['sandstone','cut_sandstone'],'red_terracotta','glass_pane'),
 'gray':('light_gray_concrete',['smooth_stone','polished_andesite'],'white_concrete','cyan_stained_glass_pane'),
 'rose':('terracotta',['packed_mud','yellow_terracotta'],'smooth_sandstone','light_blue_stained_glass_pane'),
 'mud':('packed_mud',['terracotta','yellow_terracotta'],'dark_oak_planks','glass_pane')}
SHOP_NAMES={'grocery':'杂货店','restaurant':'食店','repair':'维修铺','laundry':'洗衣店','barber':'理发店','tea':'街坊茶座'}

def build(run):
 p=json.loads((C/'input/design.json').read_text());b=Builder(p['size_xyz'],p['seed'])
 units=[];rooms=[];mods=[];stairs=[];entries=[];levels=[];lamps=[];equipment=[];keepouts=[];weather=[];plans=[];handoffs=[];floor_masks=[]
 width,height,depth=p['size_xyz'];houses=p['buildings']
 paths,street_sets,groundfoot,heightmap=site20.setup(b,p)
 # Household occupancy is selected once by ID, independent of material/damage channels.
 allhomes=[]
 for t in houses:
  for f in range(1,t['floors']+1):
   W=(t['w'] if t['rotation']%2==0 else t['d']); nlong=max(2,round((W-11)/12)) if W>=34 and f>1 else 1
   for side in ['L','R']+['R'+str(i) for i in range(2,nlong+1)]:
    if f==1 and side=='R' and t['ground']!='home':continue
    allhomes.append(f'{t["id"]}.F{f:02d}.{side}')
 lit=set(sorted(allhomes,key=lambda s:rnd(s+'.occupancy'))[:round(len(allhomes)*.7)])
 for t in houses:
  tid=t['id'];rot=t['rotation'];W,D=(t['w'],t['d']) if rot%2==0 else (t['d'],t['w']);N=t['floors'];top=3+N*5
  mat,tones,trim,glass=PAL[t['palette']];local_keeps=[];offset=t['base_y']-3;shape=site20.mask(t)
  def xyz(x,y,z):
   if rot==0:xx,zz=x,z
   elif rot==1:xx,zz=D-1-z,x
   elif rot==2:xx,zz=W-1-x,D-1-z
   else:xx,zz=z,W-1-x
   return (t['x']+xx,y+offset,t['z']+zz)
  def state(s):
   v=s if s.startswith('minecraft:') else M(s)
   for _ in range(rot):v=states.rotate_state(v)
   return v
  def put(x,y,z,s,o,empty=False):return b.put(*xyz(x,y,z),state(s),o,empty)
  def box(r,y,Y,s,o):
   x,z,X,Z=r
   for xx in range(x,X):
    for zz in range(z,Z):
     for yy in range(y,Y):put(xx,yy,zz,s,o)
  def bounds(r,y,Y):
   x,z,X,Z=r;ps=[xyz(xx,y,zz) for xx in [x,X-1] for zz in [z,Z-1]]
   return [min(q[0] for q in ps),y+offset,min(q[2] for q in ps),max(q[0] for q in ps)+1,Y+offset,max(q[2] for q in ps)+1]
  def light(x,y,z,m,o,uid=None):
   if t['shape']=='compound' and uid and uid.endswith('.R'):
    def lampfit(a,c):return a>=10 and all((a+dx,c+dz) in shape for dx,dz in [(0,0),(1,0),(-1,0),(0,1),(0,-1)]) and xyz(a,y-1,c) not in b.s.blocks
    if not lampfit(x,z):
     x,z=min(((a,c) for a,c in shape if lampfit(a,c)),key=lambda q:abs(q[0]-x)+abs(q[1]-z))
   put(x,y,z,m,o);lamps.append({'xyz':xyz(x,y,z),'material':m,'owner':o,'unit_id':uid,'fixture':'recessed' if m!='end_rod' else 'supported_rod'})
  def keep(r,y,Y):
   q=bounds(r,y,Y);keepouts.append(q);local_keeps.append(q)
  # Real floor plates and paired ceiling/floor layers.
  for f in range(N+1):
   fy=3+5*f;box((0,0,W,D),fy-1,fy,'smooth_stone' if f==N else 'oak_planks',tid+'.floor')
   if f:box((0,0,W,D),fy-2,fy-1,'white_concrete',tid+'.ceiling')
  for y in range(3,top):
   for x in range(W):
    for z in [0,D-1]:put(x,y,z,trim if (y-3)%5==4 and tid in ['A2','A4','B3','C1','C4'] else mat,tid+'.facade')
   for z in range(1,D-1):
    for x in [0,W-1]:put(x,y,z,trim if (y-3)%5==4 and tid in ['A2','A4','B3','C1','C4'] else mat,tid+'.facade')
  # Independent vertical core, 2-wide U stair. Roof is included as a destination.
  box((1,2,6,7),2,top+1,'minecraft:air',tid+'.stair.void')
  box((3,4,4,7),2,top,'smooth_sandstone',tid+'.stair.spine')
  box((6,1,7,10),3,top,'smooth_sandstone',tid+'.stair.wall')
  spec={'schema_version':'0.4','project_id':tid,'route':'original','primary_use':'home','secondary_uses':[],'style':'modern','interior_level':'L2','identity_features':['逐户睡眠烹饪和卫生空间','连续公共楼梯与独立入户','住商界面和屋顶生活设施'],'coordinates':{'unit':'block','up':'Y','north':'-Z'},'storeys_total':N,'authorized_scope':{'editable_regions':[[t['x']-4,0,t['z']-4,t['x']+t['w']+4,height,t['z']+t['d']+4]],'locked_component_ids':[]},'floor_levels':[],'rooms':[],'proposed_modules':[],'circulation_keepouts':local_keeps,'lighting':{'coverage_override':'selected_spaces','override_reason':p['lighting']['override_reason']}}
  def furniture(uid,fy,kind,r,roomid):
   x,z,X,Z=r;o=uid+'.furniture.'+kind+'.'+str(len(mods));H=2 if kind in ['bed','cabinet','shelf','fridge','kitchen','shower','tv','workbench','desk'] else 1
   original_r=r
   if (uid.endswith('.F01.R') and t['ground']!='home') or (uid.endswith('.R') and t['shape']=='compound'):
    def fits(rr):
     a,c,A,Cc=rr
     if a<10 or c<1 or A>W-1 or Cc>D-1:return False
     for xx in range(a,A):
      for zz in range(c,Cc):
       if t['shape']=='compound' and ((xx==W-7 and 1<=zz<=8) or (xx>=W-7 and zz==8)):return False
       if any((xx+dx,zz+dz) not in shape for dx,dz in [(0,0),(1,0),(-1,0),(0,1),(0,-1)]):return False
       if any(xyz(xx,yy,zz) in b.s.blocks for yy in range(fy,fy+H)):return False
     return True
    if not fits(r):
     options=sorted([(dx,dz) for dx in range(-8,9) for dz in range(-8,9)],key=lambda q:(abs(q[0])+abs(q[1]),q[1]<0,abs(q[0])))
     chosen=next(((x+dx,z+dz,X+dx,Z+dz) for dx,dz in options if fits((x+dx,z+dz,X+dx,Z+dz))),None)
     if chosen is None:raise ValueError(('no furniture fit',uid,kind,r))
     r=chosen;x,z,X,Z=r
   if kind=='bed':
    box(r,fy,fy+1,['white_concrete','light_gray_concrete','pink_concrete'][int(rnd(uid+'.bed')*3)],o)
    box((x,z,X,z+1),fy,fy+1,'smooth_quartz',o);box((x,z,X,z+1),fy+1,fy+2,'oak_planks',o)
   elif kind=='sofa':
    for zz in range(z,Z):put(x,fy,zz,M('smooth_quartz_stairs',facing='east'),o)
   elif kind=='chair':put(x,fy,z,M('oak_stairs',facing='north'),o)
   elif kind in ['table','counter']:box(r,fy,fy+1,M('oak_slab',type='top'),o)
   elif kind=='kitchen':
    box(r,fy,fy+1,'smooth_quartz',o);put(x,fy,z,'gray_concrete',o);put(x,fy,Z-1,M('iron_trapdoor',half='top'),o)
    if Z-z>=3:put(x,fy+1,z,'iron_block',o)
   elif kind=='fridge':box(r,fy,fy+2,'iron_block',o)
   elif kind=='wc':put(x,fy,z,M('smooth_quartz_stairs',facing='south'),o)
   elif kind=='basin':put(x,fy,z,'smooth_quartz',o)
   elif kind=='shower':put(x,fy+1,z,'glass_pane',o)
   elif kind=='shelf':
    box(r,fy,fy+2,'bookshelf',o)
   elif kind=='cabinet':box(r,fy,fy+2,'oak_planks',o)
   elif kind=='tv':put(x,fy,z,'dark_oak_planks',o);put(x,fy+1,z,'black_concrete',o)
   elif kind=='workbench':box(r,fy,fy+1,'dark_oak_planks',o);put(x,fy+1,z,'anvil',o)
   elif kind=='desk':box(r,fy,fy+1,M('oak_slab',type='top'),o);put(x,fy+1,z,'black_concrete',o)
   elif kind=='washer':put(x,fy,z,'iron_block',o);put(x,fy+1,z,M('iron_trapdoor',half='bottom'),o)
   elif kind=='plant':put(x,fy,z,'terracotta',o);put(x,fy+1,z,'azalea_leaves',o);H=2
   rec={'component_id':o,'unit_id':uid,'room_id':roomid,'kind':kind,'bounds_xyz':bounds(r,fy,fy+H),'use_faces':['adjacent_floor'],'game_functional':False,'original_local_rect':original_r,'placed_local_rect':r}
   mods.append(rec);spec['proposed_modules'].append(rec)
  def addroom(uid,f,fun,name,r,e):
   fy=3+(f-1)*5;rid=uid+'.'+name
   rec={'id':rid,'unit_id':uid,'floor_id':f'{tid}.F{f:02d}','function':fun,'bounds_xyz':bounds(r,fy,fy+3),'entrances':[list(xyz(e[0],fy,e[1]))],'color_intent':'neutral' if fun in ['kitchen','bathroom'] else 'warm'}
   rooms.append(rec);spec['rooms'].append(rec);return rid
  for f in range(1,N+1):
   fy=3+(f-1)*5;fid=f'{tid}.F{f:02d}';levels.append({'building':tid,'floor':f,'floor_y':fy+offset,'ceiling_y':fy+3+offset,'upper_floor_y':fy+5+offset})
   spec['floor_levels'].append({'id':fid,'floor_y':fy+offset,'upper_floor_y':fy+5+offset,'min_clear_height':3})
   # Shared corridor and the return landing; unit walls start beyond the landing.
   box((7,1,9,D-1),fy-1,fy,'smooth_stone',fid+'.common.floor')
   box((1,9,9,11),fy-1,fy,'smooth_stone',fid+'.common.floor')
   box((9,1,10,D-1),fy,fy+3,'smooth_sandstone',fid+'.partition')
   box((6,11,7,D-1),fy,fy+3,'smooth_sandstone',fid+'.partition')
   box((0,10,7,11),fy,fy+3,'smooth_sandstone',fid+'.partition')
   box((9,3,10,5),fy,fy+2,'minecraft:air',fid+'.R.door')
   box((6,12,7,14),fy,fy+2,'minecraft:air',fid+'.L.door')
   box((6,8,7,10),fy,fy+2,'minecraft:air',fid+'.stair.side_entry')
   keep((7,1,9,D-1),fy,fy+2);keep((4,8,9,10),fy,fy+2)
   for v,h in [(6,0),(5,1),(4,2)]:
    for u in [1,2]:put(u,fy+h,v,M('smooth_quartz_stairs',facing='north'),fid+'.stairs')
   box((1,2,6,4),fy+2,fy+3,'smooth_quartz',fid+'.landing')
   for v,h in [(4,3),(5,4)]:
    for u in [4,5]:put(u,fy+h,v,M('smooth_quartz_stairs',facing='south'),fid+'.stairs')
   box((4,6,6,7),fy+4,fy+5,'smooth_quartz',fid+'.top_landing')
   traces=[]
   for k in [0,1]:
    pts=[(1+k,fy,7),(1+k,fy+1,6),(1+k,fy+2,5),(1+k,fy+3,4),(1+k,fy+3,3),(2,fy+3,3),(3,fy+3,3),(4+k,fy+3,3),(4+k,fy+4,4),(4+k,fy+5,5),(4+k,fy+5,6),(4+k,fy+5,7)]
    traces.append([xyz(*q) for q in pts])
   stairs.append({'id':fid,'tracks':traces,'from_y':fy+offset,'to_y':fy+5+offset,'width':2})
   for z in [7,8]:put(3,fy,z,'iron_bars',fid+'.guard')
   light(8,fy+3,7,'sea_lantern',fid+'.common.light');light(4,fy+3,9,'glowstone',fid+'.landing.light')
   for side in ['L','R']:
    if side=='R' and W>=34 and f>1:continue
    uid=fid+'.'+side;is_shop=f==1 and side=='R' and t['ground']!='home';kind=t['ground'] if is_shop else 'home'
    x,z,X,Z=(1,11,6,D-1) if side=='L' else (10,1,W-1,D-1)
    ent=(6,12) if side=='L' else (9,3);rids=[]
    rid=addroom(uid,f,kind if is_shop else 'living',kind,(x,z,X,Z),(5,12) if side=='L' else (10,3));rids.append(rid)
    # Separate bathroom at rear, with a visible doorway and approaching floor.
    bath_z=max(z+3,Z-4);bath_x=x+min(3,X-x-1)
    box((x,bath_z,bath_x,bath_z+1),fy,fy+3,'light_gray_concrete',uid+'.bath.front')
    box((bath_x,bath_z,bath_x+1,Z),fy,fy+3,'light_gray_concrete',uid+'.bath.side')
    box((bath_x-1,bath_z,bath_x,bath_z+1),fy,fy+2,'minecraft:air',uid+'.bath.door')
    box((x,bath_z+1,bath_x,Z),fy-1,fy,'smooth_quartz',uid+'.bath.floor')
    brid=addroom(uid,f,'bathroom','bath',(x,bath_z+1,bath_x,Z),(bath_x-1,bath_z+1));rids.append(brid)
    furniture(uid,fy,'wc',(x,Z-1,x+1,Z),brid)
    if bath_x-x>=3:furniture(uid,fy,'basin',(bath_x-1,Z-1,bath_x,Z),brid)
    if is_shop:
     # Each shop has a different recognizable furniture organization.
     if kind=='grocery':
      furniture(uid,fy,'shelf',(x,6,x+1,10),rid);furniture(uid,fy,'shelf',(X-1,5,X,10),rid)
      if X-x>=9:furniture(uid,fy,'shelf',(x+4,7,x+5,10),rid)
      furniture(uid,fy,'counter',(X-4,2,X-1,3),rid)
      if W>=23:
       furniture(uid,fy,'shelf',(x+4,13,x+5,17),rid)
       furniture(uid,fy,'fridge',(X-2,11,X-1,12),rid)
      for xx in range(x+10,X-5,6):
       furniture(uid,fy,'shelf',(xx,7,xx+1,11),rid);furniture(uid,fy,'shelf',(xx,14,xx+1,18),rid)
     elif kind in ['restaurant','tea']:
      furniture(uid,fy,'kitchen',(x,bath_z-4,x+1,bath_z-1),rid)
      for zz in ([3,8,13] if D>=24 else [3,8]):
       for xx in (list(range(x+3,X-3,6)) if X-x>=11 else [X-4]):
        furniture(uid,fy,'table',(xx,zz,xx+2,zz+1),rid);furniture(uid,fy,'chair',(xx,zz-1,xx+1,zz),rid);furniture(uid,fy,'chair',(xx+1,zz+1,xx+2,zz+2),rid)
      furniture(uid,fy,'counter',(x,6,x+2,7),rid)
     elif kind=='repair':
      furniture(uid,fy,'workbench',(X-2,4,X-1,8),rid);furniture(uid,fy,'shelf',(x,7,x+1,10),rid)
      furniture(uid,fy,'counter',(X-5,2,X-2,3),rid)
      for xx in range(x+5,X-7,7):
       furniture(uid,fy,'workbench',(xx,8,xx+2,9),rid);furniture(uid,fy,'shelf',(xx,12,xx+1,15),rid)
     elif kind=='laundry':
      for zz in [3,6,9]:furniture(uid,fy,'washer',(X-2,zz,X-1,zz+1),rid)
      furniture(uid,fy,'counter',(x,7,x+1,10),rid);furniture(uid,fy,'chair',(x+2,9,x+3,10),rid)
     elif kind=='barber':
      for zz in [3,7]:
       furniture(uid,fy,'chair',(X-4,zz,X-3,zz+1),rid);furniture(uid,fy,'tv',(X-1,zz,X,zz+1),rid)
      furniture(uid,fy,'sofa',(x,7,x+1,10),rid)
    else:
     if side=='L':
      furniture(uid,fy,'bed',(1,11,3,14),rid)
      furniture(uid,fy,'kitchen',(5,max(14,bath_z),6,Z-1),rid)
      furniture(uid,fy,'table',(4,11,5,12),rid)
      # The smallest studios deliberately use compact sleeping/living space.
     else:
      furniture(uid,fy,'bed',(X-3,5,X-1,8) if t['shape']=='front_cut' else (X-2,2,X,5),rid)
      furniture(uid,fy,'cabinet',(X-5,3,X-4,4) if t['shape']=='front_cut' else (X-2,6,X,7),rid)
      furniture(uid,fy,'kitchen',(x,7,x+1,min(11,bath_z-1)),rid)
      furniture(uid,fy,'sofa',(X-1,9,X,12),rid)
      furniture(uid,fy,'table',(X-3,9,X-2,10),rid)
      if X-x>=11:
       # A separate front bedroom differentiates the wider family flats.
       px=X-6;box((px,1,px+1,8),fy,fy+3,'smooth_sandstone',uid+'.bedroom.wall')
       box((px,8,X,9),fy,fy+3,'smooth_sandstone',uid+'.bedroom.wall')
       box((px,5,px+1,7),fy,fy+2,'minecraft:air',uid+'.bedroom.door')
       rr=addroom(uid,f,'bedroom','bedroom',(px+1,1,X,8),(px+1,5));rids.append(rr)
       # Reassign front bed/cabinet to the actual private bedroom.
       for m in mods:
        if m['unit_id']==uid and m['kind'] in ['bed','cabinet']:m['room_id']=rr
       furniture(uid,fy,'table',(x+1,5,x+3,6),rid)
       furniture(uid,fy,'chair',(x+1,6,x+2,7),rid)
       furniture(uid,fy,'table',(x+5,11,x+8,12),rid)
       furniture(uid,fy,'chair',(x+5,12,x+6,13),rid)
       furniture(uid,fy,'tv',(X-5,9,X-4,10),rid)
       furniture(uid,fy,'desk',(x,12,x+1,14),rid)
       if X-x>=14 and D>=23 and t['shape']=='rect':
        bx,bz=X-7,Z-7
        box((bx,bz,bx+1,Z),fy,fy+3,'smooth_sandstone',uid+'.second_bed.wall')
        box((bx,bz,X,bz+1),fy,fy+3,'smooth_sandstone',uid+'.second_bed.wall')
        box((bx,bz+2,bx+1,bz+4),fy,fy+2,'minecraft:air',uid+'.second_bed.door')
        rid2=addroom(uid,f,'bedroom','second_bed',(bx+1,bz+1,X,Z),(bx+1,bz+2));rids.append(rid2)
        furniture(uid,fy,'bed',(X-3,Z-5,X-1,Z-2),rid2)
        furniture(uid,fy,'cabinet',(X-5,Z-2,X-3,Z-1),rid2)
    if is_shop and W>=34 and D>=24:
     # Long shop footprints receive a separated service/storage zone at the back.
     bx,bz=14,D-9;doorx=20
     box((bx,bz,W-1,bz+1),fy,fy+3,'smooth_sandstone',uid+'.service.front')
     box((bx,bz,bx+1,D-1),fy,fy+3,'smooth_sandstone',uid+'.service.side')
     box((doorx,bz,doorx+2,bz+1),fy,fy+2,'air',uid+'.service.door')
     backfun='kitchen' if kind=='restaurant' else 'utility'
     rr=addroom(uid,f,backfun,'service',(bx+1,bz+1,W-1,D-1),(doorx,bz+1));rids.append(rr)
     for xx in range(16,W-4,7):
      if kind=='restaurant':
       furniture(uid,fy,'kitchen',(xx,D-5,xx+1,D-2),rr)
       furniture(uid,fy,'fridge',(xx+2,D-3,xx+3,D-2),rr)
      else:furniture(uid,fy,'shelf',(xx,D-3,xx+3,D-2),rr)
     for xx in range(17,W-4,8):
      for zz in [7,14,D-5]:light(xx,fy+3,zz,'sea_lantern',uid+'.light.zone',uid)
    if not is_shop and side=='R' and D>=31:
     # Deep parcels gain a rear bedroom rather than an oversized empty living hall.
     bx,bz=14,17
     box((bx,bz,bx+1,D-1),fy,fy+3,'smooth_sandstone',uid+'.deep_bed.side')
     box((bx,bz,W-1,bz+1),fy,fy+3,'smooth_sandstone',uid+'.deep_bed.front')
     box((bx,19,bx+1,21),fy,fy+2,'air',uid+'.deep_bed.door')
     rr=addroom(uid,f,'bedroom','deep_bed',(bx+1,bz+1,W-1,D-1),(bx+1,19));rids.append(rr)
     furniture(uid,fy,'bed',(16,22,18,25),rr)
     furniture(uid,fy,'cabinet',(16,27,18,28),rr)
    active=is_shop or uid in lit
    if active:
     light(x+1 if side=='R' else (x+X)//2,fy+3,4 if side=='R' else z+2,'sea_lantern' if is_shop or rnd(uid+'.lamp')>.6 else 'glowstone',uid+'.light.main',uid)
     light(x+1,fy+3,Z-2,'sea_lantern',uid+'.light.bath',uid)
     if side=='R':light(X-2,fy+3,min(11,bath_z-1),'glowstone' if rnd(uid+'.rear_lamp')>.3 else 'sea_lantern',uid+'.light.rear',uid)
     if side=='R' and not is_shop and D>=31:light(17,fy+3,20,'glowstone',uid+'.light.deep_bed',uid)
     if side=='R' and not is_shop and X-x>=11:
      light(X-3,fy+3,4,'glowstone',uid+'.light.bedroom',uid)
      if X-x>=14 and D>=23 and t['shape']=='rect':light(X-4,fy+3,Z-4,'glowstone',uid+'.light.second_bed',uid)
    rec={'id':uid,'building':tid,'floor':f,'floor_y':fy+offset,'kind':kind,'lit':active,'entry':xyz(ent[0],fy,ent[1]),'rooms':rids,'bounds_xyz':bounds((x,z,X,Z),fy,fy+3),'layout':kind if is_shop else 'compact_studio' if side=='L' or X-x<11 else 'one_bedroom_flat'}
    units.append(rec)
   # Long street blocks: several rental flats, a rear shared hall and one true stair core.
   if W>=34 and f>1:
    box((9,3,10,5),fy,fy+3,'smooth_sandstone',fid+'.long_hall.old_door_closed')
    count=max(2,round((W-11)/12));edges=[10+round((W-11)*i/count) for i in range(count+1)];hallz=D-4
    box((7,hallz,W-1,D-1),fy,fy+3,'air',fid+'.long_hall.void')
    box((7,hallz,W-1,D-1),fy-1,fy,'smooth_stone',fid+'.long_hall.floor')
    box((10,hallz-1,W-1,hallz),fy,fy+3,'smooth_sandstone',fid+'.long_hall.wall')
    keep((7,hallz,W-t['cut']-1 if t['shape'] in ['rear_cut','notch'] else W-1,D-1),fy,fy+2)
    for j,(a,A) in enumerate(zip(edges,edges[1:])):
     uid=fid+'.R'+(str(j+1) if j else '');x=a if j==0 else a+1;X=A if j==count-1 else A-1;Z=hallz-1
     if j:box((a,1,a+1,hallz),fy,fy+3,'smooth_sandstone',uid+'.division')
     dx=min(X-2,x+5);box((dx,hallz-1,dx+1,hallz),fy,fy+2,'air',uid+'.door')
     rid=addroom(uid,f,'living','studio',(x,1,X,Z),(dx,Z-1))
     bz=Z-5;bx=x+3
     box((x,bz,bx+1,bz+1),fy,fy+3,'light_gray_concrete',uid+'.bath.front')
     box((bx,bz,bx+1,Z),fy,fy+3,'light_gray_concrete',uid+'.bath.side')
     box((bx-1,bz,bx,bz+1),fy,fy+2,'air',uid+'.bath.door')
     brid=addroom(uid,f,'bathroom','bath',(x,bz+1,bx,Z),(bx-1,bz+1))
     furniture(uid,fy,'wc',(x,Z-1,x+1,Z),brid);furniture(uid,fy,'basin',(bx-1,Z-1,bx,Z),brid)
     furniture(uid,fy,'bed',(X-3,4,X-1,7),rid)
     furniture(uid,fy,'cabinet',(x+1,3,x+3,4),rid)
     furniture(uid,fy,'kitchen',(x,7,x+1,min(11,bz-1)),rid)
     furniture(uid,fy,'sofa',(X-1,9,X,12),rid)
     furniture(uid,fy,'table',(X-3,10,X-2,11),rid)
     active=uid in lit
     if active:
      light(x+2,fy+3,6,'glowstone' if rnd(uid+'.lamp')<.6 else 'sea_lantern',uid+'.light.main',uid)
      light(x+1,fy+3,Z-2,'sea_lantern',uid+'.light.bath',uid)
      light(X-2,fy+3,10,'glowstone',uid+'.light.living',uid)
     units.append({'id':uid,'building':tid,'floor':f,'floor_y':fy+offset,'kind':'home','lit':active,'entry':xyz(dx,fy,hallz-1),'rooms':[rid,brid],'bounds_xyz':bounds((x,1,X,Z),fy,fy+3),'layout':'street_bar_rental_flat'})
    for hx in range(13,W-t['cut']-2,9):light(hx,fy+3,D-3,'sea_lantern',fid+'.long_hall.light')
   # Window placement responds to the core, private rooms and different elevations.
   defs=[(W-4,0,(0,-1),4),(W-1,4,(1,0),4),(W-1,min(11,D-5),(1,0),4),(W-4,D-1,(0,1),4),(3,D-1,(0,1),2),(0,D-5,(-1,0),3),(3,0,(0,-1),2)]
   defs.append((0,5,(-1,0),2))
   if W>=22:defs.append((12,0,(0,-1),3));defs.append((12,D-1,(0,1),3))
   if D>=24:defs.append((W-1,D-6,(1,0),3))
   for xx in range(18,W-6,7):
    for zz,n in [(0,(0,-1)),(D-1,(0,1))]:
     if all(abs(xx-a)>=5 or z!=zz for a,z,_,_ in defs):defs.append((xx,zz,n,4))
   for zz in range(18,D-6,7):
    if all(abs(zz-z)>=5 or x!=W-1 for x,z,_,_ in defs):defs.append((W-1,zz,(1,0),3))
   for wi,(wx,wz,n,ww) in enumerate(defs):
    tx,tz=n[1],-n[0]
    if any((wx+tx*u,wz+tz*u) not in shape for u in range(-(ww//2),-(ww//2)+ww)):continue
    key=fid+f'.window{wi}';fr=b.frame(*[0,0],(0,1)) if False else None
    tangent=(n[1],-n[0]);lo=-(ww//2);hi=lo+ww
    def fp(u,y,dep,s,o,empty=False):return put(wx+tangent[0]*u+n[0]*dep,y,wz+tangent[1]*u+n[1]*dep,s,o,empty)
    security='none' if wi==6 or f==1 else ('cage' if rnd(key+'.grille')<.25 else 'flush' if rnd(key+'.grille')<.52 else 'none')
    g=glass if rnd(key+'.glass')>.15 else 'gray_stained_glass_pane'
    for u in range(lo,hi):
     for yy in [fy+1,fy+2]:fp(u,yy,0,g,key+'.glass')
     if f>1:fp(u,fy,1,M('smooth_sandstone_slab',type='top'),key+'.sill')
     if security!='none':
      for yy in [fy+1,fy+2]:fp(u,yy,1,'iron_bars',key+'.grille')
      if security=='cage':fp(u,fy,1,M('iron_trapdoor',half='top'),key+'.grille_base')
    if security=='cage':
     for u in [lo,hi-1]:
      for yy in [fy+1,fy+2]:fp(u,yy,0,'iron_bars',key+'.cage_return')
    if f>1 and wi not in [5,6] and rnd(key+'.ac')<.54:
     u=lo-1;fp(u,fy+1,1,'iron_block',key+'.ac');fp(u,fy+2,1,M('iron_trapdoor',half='bottom'),key+'.ac_cover');fp(u,fy+1,2,M('iron_trapdoor',open=True,facing={(-1,0):'west',(1,0):'east',(0,-1):'north',(0,1):'south'}[n]),key+'.ac_grille')
     equipment.append({'id':key+'.ac','kind':'air_conditioner','anchor':xyz(wx+tangent[0]*u,fy+1,wz+tangent[1]*u),'cells':[xyz(wx+tangent[0]*u+n[0],fy+1,wz+tangent[1]*u+n[1])]})
    normal=states.DIRS[['north','east','south','west'][(rot+{(0,-1):0,(1,0):1,(0,1):2,(-1,0):3}[n])%4]]
    b.windows.append({'id':key,'building':tid,'floor':f,'security':security,'glass':g,'center':xyz(wx,fy+1,wz),'normal':normal,'width':ww})
   # Selected projecting balconies are tied to real door openings and plates.
   if t['balcony'] and f>1 and (f%3!=0 or N<=4):
    x1=W-1-(t['cut'] if t['shape']=='front_cut' else 0);x0=max(10,x1-8);o=fid+'.balcony';box((x0,-2,x1,0),fy-1,fy,'smooth_sandstone',o+'.floor')
    for xx in range(x0,x1):put(xx,fy,-2,'iron_bars',o+'.rail')
    for zz in [-2,-1]:
     for xx in [x0,x1-1]:put(xx,fy,zz,'iron_bars',o+'.rail')
    doorx=x1-3;box((doorx,-1,doorx+1,1),fy,fy+2,'minecraft:air',o+'.door')
    # Do not plant directly in front of the balcony doorway.
    if rnd(o+'.plant')<.55:put(x0+1,fy,-1,'terracotta',o+'.pot');put(x0+1,fy+1,-1,'azalea_leaves',o+'.plant')
    equipment.append({'id':o,'kind':'balcony','entry':xyz(doorx,fy,-1),'floor_y':fy+offset,'unit_id':fid+'.R'+(str(max(2,round((W-11)/12))) if W>=34 and f>1 else '')})
   if f==1:
    box((7,-2,9,1),fy,fy+3,'minecraft:air',tid+'.main_entry')
    box((6,-2,10,0),fy-1,fy,'stone_bricks',tid+'.entry.apron')
    box((6,-2,10,0),fy+3,fy+4,M('smooth_stone_slab'),tid+'.entry.canopy')
    e={'id':tid,'entry':xyz(7,fy,0),'outside':xyz(7,fy,-1),'core_landing':xyz(5,fy,8),'width':2};entries.append(e)
    if t['ground']!='home':
     sx=W-t['cut']-4 if t['shape']=='front_cut' else W-4;shopend=W-t['cut'] if t['shape']=='front_cut' else W;box((sx,-2,sx+2,1),fy,fy+3,'minecraft:air',tid+'.shop_entry')
     box((sx-1,-2,sx+2,0),fy-1,fy,'stone_bricks',tid+'.shop.apron')
     box((10,-2,shopend,0),fy+3,fy+4,M('iron_trapdoor',half='top'),tid+'.shop.awning')
     signmat={'grocery':'green_stained_glass','restaurant':'red_concrete','repair':'blue_concrete','laundry':'cyan_stained_glass','barber':'red_terracotta','tea':'dark_oak_planks'}[t['ground']]
     box((10,-1,shopend,0),fy+4,fy+5,signmat,tid+'.shop.sign_panel')
     # A blade sign attached at the shop edge, not at every residential window.
     box((shopend-1,-3,shopend,-1),fy+4,fy+7,signmat,tid+'.shop.blade_sign');put(shopend-1,fy+7,-1,'iron_bars',tid+'.shop.sign_support')
     entries.append({'id':tid+'.shop','entry':xyz(sx,fy,0),'outside':xyz(sx,fy,-1),'width':2,'kind':t['ground'],'unit_id':tid+'.F01.R','role':'service' if t['corner_shop'] else 'customer'})
  # Four shallow service wings break the footprint and add a usable rear room.
  if False:
   uid=tid+'.F01.R';o=tid+'.service_wing';box((W-8,D-1,W,D+4),2,3,'stone_bricks',o+'.foundation')
   box((W-8,D,W,D+4),6,7,'white_concrete',o+'.ceiling');box((W-8,D,W,D+4),7,8,'smooth_stone',o+'.roof')
   for xx in range(W-8,W):box((xx,D+3,xx+1,D+4),3,6,mat,o+'.wall')
   for zz in range(D,D+4):
    for xx in [W-8,W-1]:box((xx,zz,xx+1,zz+1),3,6,mat,o+'.wall')
   box((W-4,D-1,W-3,D),3,5,'minecraft:air',o+'.door')
   box((W-5,D+3,W-3,D+4),4,6,glass,o+'.window')
   rr=addroom(uid,1,'utility','service_wing',(W-7,D,W-1,D+3),(W-4,D));u=next(u for u in units if u['id']==uid);u['rooms'].append(rr)
   furniture(uid,3,'washer',(W-7,D+2,W-6,D+3),rr);furniture(uid,3,'cabinet',(W-2,D+2,W-1,D+3),rr)
   if u['lit']:light(W-4,6,D+1,'sea_lantern',o+'.light',uid)
   equipment.append({'id':o,'kind':'service_wing','bounds_xyz':bounds((W-8,D,W,D+4),2,8),'entry':xyz(W-4,3,D)})
  # Geometry follows an actual nonrectangular floor mask on all storeys.
  boundary={(x,z) for x,z in shape if any((x+dx,z+dz) not in shape for dx,dz in [(1,0),(-1,0),(0,1),(0,-1)])}
  diagonal={(x,z) for x,z in boundary if x not in [0,W-1] and z not in [0,D-1]}
  for xx in range(W):
   for zz in range(D):
    if (xx,zz) not in shape:
     for yy in range(2,top+1):put(xx,yy,zz,'air',tid+'.shape.cut')
     put(xx,2,zz,'smooth_stone','site.cut_corner_paving')
  for xx,zz in diagonal:
   for yy in range(3,top):
    if (yy-3)%5<3:put(xx,yy,zz,mat,tid+'.facade')
   for f in range(1,N+1):
    fy=3+(f-1)*5
    if (xx+2*zz)%5 in [0,1,2]:
     for yy in [fy+1,fy+2]:put(xx,yy,zz,glass,tid+'.shape.window')
  # The street-corner grocery has a glazed shopfront and a continuous turning canopy.
  if t['corner_shop']:
   shopfront={(xx,zz) for xx,zz in boundary if xx>=15 and (xx==W-1 or zz==D-1 or (xx,zz) in diagonal)}
   for xx,zz in shopfront:
    if (xx+zz)%6:
     for yy in range(3,6):put(xx,yy,zz,'glass_pane',tid+'.shop.glazed_front')
    dx,dz=(1,1) if (xx,zz) in diagonal else (1,0) if xx==W-1 else (0,1)
    put(xx+dx,6,zz+dz,M('smooth_stone_slab',type='top'),tid+'.shop.turning_canopy')
    put(xx+dx,7,zz+dz,'green_stained_glass',tid+'.shop.turning_sign')
  # Larger corner shops have two customer doors; the residential core stays separate.
  if t['extra_shop_entry']:
   fy=3
   if t['corner_shop']:
    ex,ez=W-1,D-t['cut']-4;ix,iz=ex-1,ez;ox,oz=ex+1,ez
   else:
    ex,ez=W-1,max(t['cut']+3,11);ix,iz=ex-1,ez;ox,oz=ex+1,ez
   for zz in range(ez,ez+2):
    box((ex-1,zz,ex+2,zz+1),fy,fy+3,'air',tid+'.shop.side_door')
    box((ex,zz,ex+3,zz+1),fy-1,fy,'stone_bricks',tid+'.shop.side_apron')
   entries.append({'id':tid+'.shop.side','unit_id':tid+'.F01.R','entry':xyz(ex,fy,ez),'inside':xyz(ix,fy,iz),'outside':xyz(ox,fy,oz),'width':2,'kind':t['ground'],'role':'customer'})
   for zz in range(ez-1,ez+4):
    put(W,fy+4,zz,'red_terracotta' if t['ground']=='restaurant' else 'dark_oak_planks',tid+'.shop.side_sign')
    put(W,fy+3,zz,M('iron_trapdoor',half='top'),tid+'.shop.side_awning')
   # Keep the secondary door approach clear of movable furnishings.
   clearworld=bounds((W-5,ez,W,ez+2),fy,fy+3)
   remove=[]
   for m in mods:
    x,y,z,X,Y,Z=m['bounds_xyz'];a0,c0,d0,a1,c1,d1=clearworld
    if m['unit_id']==tid+'.F01.R' and x<a1 and X>a0 and z<d1 and Z>d0:
     remove.append(m)
     for q,o in list(b.s.owners.items()):
      if o==m['component_id']:b.s.set(q,'minecraft:air',o+'.removed')
   for m in remove:mods.remove(m)
   if t['corner_shop']:
    # The diagonal corner is itself a customer entrance, facing the south/east junction.
    candidates=sorted(diagonal,key=lambda q:abs(q[0]-(W-t['cut']//2-1))+abs(q[1]-(D-t['cut']//2-1)))
    cx,cz=candidates[0]
    box((cx-1,cz-1,cx+2,cz+2),fy,fy+3,'air',tid+'.shop.corner_door')
    box((cx-1,cz-1,cx+3,cz+3),fy-1,fy,'stone_bricks',tid+'.shop.corner_apron')
    entries.append({'id':tid+'.shop.corner','unit_id':tid+'.F01.R','entry':xyz(cx,fy,cz),'inside':xyz(cx-1,fy,cz-1),'outside':xyz(cx+1,fy,cz+1),'width':3,'kind':t['ground'],'role':'customer'})
  # D5's blind diagonal becomes an inset, enterable corner loggia on F2-F6.
  if t.get('corner_loggia'):
   limit=W+D-2-t['cut'];inner=limit-5;xmin=W-t['cut']-2;zmin=D-t['cut']-2
   cx=(xmin+inner-zmin)//2;cz=inner-cx
   for f in range(2,N+1):
    fy=3+(f-1)*5;fid=f'{tid}.F{f:02d}';uid=fid+'.R';o=fid+'.corner_loggia'
    superseded=[w for w in b.windows if w['building']==tid and w['floor']==f and w['center'][0]>=t['x']+xmin and w['center'][2]>=t['z']+zmin]
    prefixes=[w['id'] for w in superseded]
    for q,owner in list(b.s.owners.items()):
     if any(owner.startswith(w+'.') for w in prefixes):b.s.set(q,'minecraft:air',o+'.replaced_window')
    b.windows=[w for w in b.windows if w not in superseded]
    equipment=[e for e in equipment if not any(e['id'].startswith(w+'.') for w in prefixes)]
    zone={(xx,zz) for xx,zz in shape if xx>=xmin and zz>=zmin and xx+zz>=inner}
    rail=[];glazing=[];floor=[]
    for xx,zz in sorted(zone):
     for yy in range(fy,fy+3):put(xx,yy,zz,'air',o+'.void')
     put(xx,fy-1,zz,'smooth_sandstone',o+'.floor');floor.append(xyz(xx,fy-1,zz))
    for xx,zz in sorted(zone):
     if xx+zz==inner:
      put(xx,fy,zz,'smooth_sandstone',o+'.window_sill')
      for yy in [fy+1,fy+2]:put(xx,yy,zz,'light_blue_stained_glass',o+'.glazing');glazing.append(xyz(xx,yy,zz))
     elif xx+zz>=limit-1 or xx==xmin or zz==zmin:
      for yy in range(fy,fy+(3 if f in [3,5] else 1)):
       put(xx,yy,zz,'iron_bars',o+'.screen' if f in [3,5] else o+'.rail');rail.append(xyz(xx,yy,zz))
    for yy in [fy,fy+1]:put(cx,yy,cz,'air',o+'.door')
    glazing=[q for q in glazing if q!=xyz(cx,fy+1,cz)]
    sample=(cx+1,cz+1)
    rr=addroom(uid,f,'terrace','corner_loggia',(xmin,zmin,W,D),sample)
    u=next(u for u in units if u['id']==uid);u['rooms'].append(rr)
    if u['lit']:light(*[sample[0],fy+3,sample[1]],'glowstone',uid+'.light.loggia',uid)
    if f in [2,4,6]:
     px,pz=xmin+1,inner-xmin+1
     put(px,fy,pz,'terracotta',o+'.planter');put(px,fy+1,pz,'azalea_leaves',o+'.plant')
    equipment.append({'id':o,'kind':'corner_loggia','unit_id':uid,'entry':xyz(cx,fy,cz),'sample':xyz(sample[0],fy,sample[1]),'floor_cells':floor,'rail_cells':rail,'glazing_cells':glazing,'screened':f in [3,5]})
  # Cut façades receive a continuous parapet in the same footprint.
  # Roof parapet, roof access hut, tank variations and selective daily-life equipment.
  for x in range(W):
   for z in [0,D-1]:put(x,top,z,trim,tid+'.roof.parapet')
  for z in range(D):
   for x in [0,W-1]:put(x,top,z,trim,tid+'.roof.parapet')
  for xx in range(W):
   for zz in range(D):
    if (xx,zz) not in shape:put(xx,top,zz,'air',tid+'.shape.cut')
  for xx,zz in boundary:put(xx,top,zz,trim,tid+'.roof.parapet')
  for x in range(0,10):
   for z in range(0,11):
    if x in [0,9] or z in [0,10]:box((x,z,x+1,z+1),top,top+3,mat,tid+'.roof.hut')
  box((7,10,9,11),top,top+2,'minecraft:air',tid+'.roof.exit')
  box((0,0,10,11),top+3,top+4,M('smooth_stone_slab',type='top'),tid+'.roof.hut_cap')
  if tid in ['A2','B3','C4']:
   for zz in range(0,11):
    for xx in range(0,10):put(xx,top+4+min(xx,9-xx)//3,zz,'red_terracotta',tid+'.roof.small_pitch')
  keep((7,7,9,13),top,top+2)
  roofentry=xyz(7,top,11);equipment.append({'id':tid+'.roof.access','kind':'roof_access','entry':roofentry})
  tx,tz=W-9,D-8;sz=2 if rnd(tid+'.tank')<.5 else 3
  box((tx-1,tz-1,tx+sz+1,tz+sz+1),top,top+1,'stone_bricks',tid+'.tank.plinth')
  box((tx,tz,tx+sz,tz+sz),top+1,top+3,'iron_block',tid+'.tank.body')
  box((tx,tz,tx+sz,tz+sz),top+3,top+4,M('smooth_quartz_slab'),tid+'.tank.cap')
  for yy in range(top+1,top+4):put(tx-1,yy,tz,'iron_bars',tid+'.tank.side')
  equipment.append({'id':tid+'.tank','kind':'water_tank_shape','base':xyz(tx,top,tz),'size':sz})
  if W>=34:
   tx2,tz2=W//2,D-7;o=tid+'.tank_aux'
   box((tx2-1,tz2-1,tx2+4,tz2+4),top,top+1,'stone_bricks',o+'.plinth')
   box((tx2,tz2,tx2+3,tz2+3),top+1,top+3,'iron_block',o+'.body')
   box((tx2,tz2,tx2+3,tz2+3),top+3,top+4,M('smooth_quartz_slab'),o+'.cap')
   equipment.append({'id':o,'kind':'water_tank_shape','base':xyz(tx2,top,tz2),'size':3})
  if rnd(tid+'.antenna')<.8:
   ax,az=(W-9,3) if t['shape']=='front_cut' else (W-3,2);put(ax,top,az,'stone_bricks',tid+'.antenna.base')
   for yy in range(top+1,top+6):put(ax,yy,az,'iron_bars',tid+'.antenna.mast')
   for xx in range(ax-2,ax+3):put(xx,top+4,az,'iron_bars',tid+'.antenna.cross')
   equipment.append({'id':tid+'.antenna','kind':'antenna','base':xyz(ax,top,az)})
  if W>=20:
   for xx in [11,15]:
    for yy in range(top,top+3):put(xx,yy,3,'iron_bars',tid+'.washing.post')
   for xx in range(11,16):put(xx,top+3,3,M('chain',axis='x'),tid+'.washing.line')
   for xx in [12,14]:put(xx,top+2,3,'white_stained_glass_pane' if xx==12 else 'blue_stained_glass_pane',tid+'.washing.cloth_approx')
   equipment.append({'id':tid+'.washing','kind':'clothesline','base':xyz(11,top,3)})
  if tid in ['A1','A4','B2','B4','C1','C2']:
   for xx in range(W-7,W-3):
    for zz in range(8,11):
     put(xx,top,zz,'stone_bricks',tid+'.solar.support')
     if zz==10:put(xx,top+1,zz,'stone_bricks',tid+'.solar.support')
     put(xx,top+1+(zz-8)//2,zz,M('polished_deepslate_slab',type='top'),tid+'.solar.panel')
   equipment.append({'id':tid+'.solar','kind':'solar_panel_shape','base':xyz(W-7,top,8)})
  # Full-height service pipe on a solid corner; y0 rests on paving, no fake floating pipes.
  pipe_candidates=([(-1,D-2,'east')] if t['shape']=='front_cut' else [(W,0,'west'),(-1,D-2,'east')])+[(W,zz,'west') for zz in [3,D//2,D-3]]+[(-1,zz,'east') for zz in [3,D//2,D-3]]
  pipe_places=[]
  for px,pz,face in pipe_candidates:
   q=xyz(px,3,pz);back=(px-1,pz) if face=='west' else (px+1,pz)
   if (q[0],q[2]) in paths or back not in shape or any(abs(px-a)+abs(pz-c)<5 for a,c,_ in pipe_places):continue
   pipe_places.append((px,pz,face))
   if len(pipe_places)>=1+int(rnd(tid+'.pipe2')>.45):break
  for px,pz,face in pipe_places:
   for yy in range(3,top+2):put(px,yy,pz,M('diorite_wall',**{face:'low' if (yy-3)%5==0 else 'none'}),tid+'.service.pipe')
   equipment.append({'id':tid+f'.pipe{px}_{pz}','kind':'rainwater_pipe','base':xyz(px,2,pz),'top_y':top+1+offset,'cells':[xyz(px,yy,pz) for yy in range(3,top+2)]})
  # Near-colour variation uses isolated cells; independent from form and openings.
  facade=[q for q,o in b.s.owners.items() if o==tid+'.facade' and b.s.blocks[q]==M(mat)]
  chosen=set()
  for q in sorted(facade,key=lambda q:rnd(str(q)+'.tone')):
   if rnd(str(q)+'.use_tone')>.10 or any(tuple(q[i]+v[i] for i in range(3)) in chosen for v in [(1,0,0),(-1,0,0),(0,1,0),(0,-1,0),(0,0,1),(0,0,-1)]):continue
   s=tones[int(rnd(str(q)+'.tone_kind')*len(tones))];b.put(*q,s,tid+'.facade.tone');chosen.add(q);weather.append({'id':tid+'.tone','xyz':q,'kind':'near_colour','material':s})
  # Local peeling/repair is sparse and conditional on exposed wall ownership.
  target=max(2,round((1-t['maintenance'])*14));selected=[]
  candidates=[q for q in facade if (q[1]-3-offset)%5 in [0,1,2] and q[1]<min(top+offset,20+offset)]
  for q in sorted(candidates,key=lambda q:rnd(str(q)+'.peel')):
   if len(selected)>=target:break
   if q in chosen or any(sum(abs(a-c) for a,c in zip(q,v))<4 for v in selected):continue
   if b.s.owners.get(q)!=tid+'.facade':continue
   s='bricks' if t['palette'] in ['sand','rose','mud'] else 'stone_bricks'
   b.put(*q,s,tid+'.facade.peeling');selected.append(q);weather.append({'id':tid+'.peel','xyz':q,'kind':'exposed_infill','material':s})
  # A few backed chips change depth, without opening a full hole into occupied rooms.
  for ix in [1,W-2]:
   z=D-1;y=4;q=xyz(ix,y,z);back=xyz(ix,y,z-1)
   if b.s.owners.get(q)==tid+'.facade' and back not in b.s.blocks and rnd(tid+str(ix)+'.chip')<.65:
    b.put(*back,'bricks',tid+'.facade.chip_backing');put(ix,y,z,M('stone_brick_stairs',facing='south'),tid+'.facade.chipped_edge')
    weather.append({'id':tid+'.chip','xyz':q,'kind':'backed_chipped_edge','backing':back,'material':'stone_brick_stairs'})
  # Room metadata uses final positions; compile the existing HAF 0.4 contract.
  spec['proposed_modules']=[m for m in mods if m['unit_id'].startswith(tid+'.')]
  handoffs.append(spec);plans.append(compile_handoff(spec))
  floor_masks.append({'building':tid,'size_local':[W,D],'world_bounds':[t['x'],t['z'],t['x']+t['w'],t['z']+t['d']],'rotation':rot,'cells_xz':[list(site20.local(t,x,z)) for x,z in sorted(shape)]})
 transitions=site20.connect(b,entries,paths,groundfoot,heightmap,p)
 trees,props=site20.decorate(b,paths,groundfoot,heightmap,p,lamps)
 counts=collections.Counter(b.s.owners.values())
 for m in mods:m['placed_cells']=counts[m['component_id']]
 b.rooms=rooms
 out=save_run(C,run,p,b,__file__,{'identity':'original_guangdong_urban_village','homes':len(allhomes),'lit_homes':len(lit),'shops':sum(t['ground']!='home' for t in houses),'storeys_total':sum(t['floors'] for t in houses)})
 data={'units':units,'module_consumption':mods,'stairs':stairs,'entries':entries,'floor_levels':levels,'lamps':lamps,'equipment':equipment,'street_props':props,'circulation_keepouts':keepouts,'weathering':weather,'design_handoffs':handoffs,'resolved_plans':plans,'floor_masks':floor_masks,'trees':trees,'terrain':{'heights_xzy':[[x,z,y] for (x,z),y in sorted(heightmap.items())],'grade_transitions':transitions,'site_boundary_xz':p['site']['boundary_xz'],'walk_surface_range':[min(b.site_surface.values()),max(b.site_surface.values())]},'paths':{'cells_xz':sorted(paths),'street_cells':{k:sorted(v) for k,v in street_sets.items()}},'lighting_assignment':{'home_ids':allhomes,'lit_home_ids':sorted(lit),'ratio':len(lit)/len(allhomes),'policy':p['lighting']},'provenance':{'reference_catalog_sha256':sha(C/'input/exterior_catalog_v02.json'),'actual_sources':['existing catalog v0.2','authored design.json'],'new_external_research':False,'game_test':'pending','skills_modified':False}}
 for k,v in data.items():dump(out/(k+'.json'),v)
 return out
if __name__=='__main__':
 ap=argparse.ArgumentParser();ap.add_argument('--run',required=True);a=ap.parse_args();build(a.run)
