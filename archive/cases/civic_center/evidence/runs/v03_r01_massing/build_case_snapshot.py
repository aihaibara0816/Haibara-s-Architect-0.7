"""Civic V0.3: consume frozen concept cells/openings. Case adapter, no inference."""
from pathlib import Path
import argparse,json,sys,math,hashlib,collections
R=Path(__file__).resolve().parents[2];sys.path[:0]=[str(R),str(R/'support')]
from hafusion.classical import Builder,M
from hafusion.case_io import save_run,dump
C=Path(__file__).parent
S=json.loads((C/'input/data/spatial.json').read_text())
F=json.loads((C/'input/data/facade-resolved.json').read_text())
I=json.loads((C/'input/data/interior-handoff.json').read_text())
def Q(v):return math.floor(v*2+.5)
def xyrect(r):
 x0,z0,x1,z1=r;return 12+Q(x0),12+Q(48-z1),12+Q(x1),12+Q(48-z0)
def yr(v):return 4+Q(v)
class Civic:
 def __init__(self,p,mode):
  self.p=p;self.mode=mode;self.b=Builder(p['size'],p['lighting']['seed']);self.audit={'openings':[],'ledges':[],'stairs':[],'doors':[],'equipment':[],'furniture':[],'quantization':[],'hidden_returns':[]}
  self.maps=[{(a,b):(kind,id) for a,b,kind,id in f['cells']} for f in S['floors']]
 def box(self,a,b,m,o):
  if all(b[i]>a[i] for i in range(3)):self.b.box(a,b,m,o)
 def put(self,x,y,z,m,o,empty=False):return self.b.put(x,y,z,m,o,empty=empty)
 def rect(self,r,y0,y1,m,o):
  x0,z0,x1,z1=xyrect(r);self.box((x0,y0,z0),(x1,y1,z1),m,o)
 def site(self):
  self.box((4,1,4),(140,3,116),'stone_bricks','site.foundation')
  self.box((4,3,4),(140,4,116),'smooth_stone','site.ground')
  for x in [8,136]:
   for z in [20,50,80,108]:
    self.box((x-1,4,z-2),(x+2,5,z+3),'smooth_quartz','site.planter')
    self.box((x-1,5,z-2),(x+2,6,z+3),'azalea_leaves','site.planting')
  # Park route has continuous paving at ground level, not an excavated void.
  self.rect([44,24,52,50],3,4,'polished_andesite','site.park_route')
 def boundary(self,fi):
  mp=self.maps[fi]
  for i,j in mp:
   for face,di,dj in [('W',-1,0),('E',1,0),('S',0,-1),('N',0,1)]:
    if (i+di,j+dj) in mp:continue
    x0,z0,x1,z1=xyrect([i*2,j*2,i*2+2,j*2+2])
    qs={'W':[(x0,z) for z in range(z0,z1)],'E':[(x1-1,z) for z in range(z0,z1)],'S':[(x,z1-1) for x in range(x0,x1)],'N':[(x,z0) for x in range(x0,x1)]}[face]
    yield i,j,face,qs
 def mass(self):
  for fi,f in enumerate(S['floors']):
   y=yr(f['elevation']);top=yr(f['elevation']+f['height']);self.audit['quantization'].append({'floor':fi+1,'design_m':f['elevation'],'actual_m':(y-4)/2,'error_m':(y-4)/2-f['elevation']})
   for i,j,kind,id in f['cells']:
    self.rect([i*2,j*2,i*2+2,j*2+2],y-1,y,'smooth_stone',f'floor.F{fi+1}')
   for i,j in f['terrace_cells']:
    self.rect([i*2,j*2,i*2+2,j*2+2],y-1,y,'smooth_quartz',f'terrace.F{fi+1}.deck')
   for i,j,face,qs in self.boundary(fi):
    # V01 internal boundary and the exposed bridge are guards, not full walls.
    ni=i+({'E':1,'W':-1}.get(face,0));nj=j+({'N':1,'S':-1}.get(face,0))
    atrium=fi==1 and 9<=ni<17 and 13<=nj<19
    bridge=fi==1 and 22<=i<26 and 19<=j<21
    for x,z in qs:
     if atrium or bridge:
      for yy in range(y,y+2):self.put(x,yy,z,'gray_stained_glass_pane','guard.atrium' if atrium else 'guard.bridge')
     else:
      self.box((x,y,z),(x+1,top,z+1),'smooth_quartz',f'wall.F{fi+1}.{face}')
   # Slab of the next floor is consumed from its actual footprint. Exposed roofs
   # are emitted only where no next occupied cell exists.
   above=set(self.maps[fi+1]) if fi<6 else set()
   for i,j in self.maps[fi]:
    if (i,j) not in above:
     self.rect([i*2,j*2,i*2+2,j*2+2],top-1,top,'smooth_quartz',f'roof.F{fi+1}.deck')
  # Missing atrium slab must remain missing: F1 ceiling is deferred to F3 slab.
  self.rect([18,26,34,38],yr(4.8)-1,yr(4.8),'minecraft:air','void.V01')
  # Bridge is the sole F2 slab above the outdoor passage.
  for z0,z1 in [(26,38),(42,48)]:self.rect([44,z0,52,z1],4,yr(9.6)-1,'minecraft:air','void.V02')
 def facade_coord(self,g,u,y,d=0):
  pl=g['plane_m'];face=g['face']
  if face=='E':return (12+Q(pl)-1+d,y,12+96-1-u)
  if face=='W':return (12+Q(pl)-d,y,12+96-1-u)
  if face=='N':return (12+u,y,12+Q(48-pl)-d)
  return (12+u,y,12+Q(48-pl)-1+d)
 def facade(self):
  palette={'cyan_glass':'cyan_stained_glass_pane','blue_glass':'blue_stained_glass_pane','dark_gray_glass':'gray_stained_glass_pane'}
  for g in F['groups']:
   floor=S['floors'][g['floor']-1];fy=yr(floor['elevation']);top=yr(floor['elevation']+floor['height'])
   for o in g['openings']:
    u0,u1=Q(o['u0_m']),Q(o['u1_m']);y0=max(fy,yr(o['surface_bounds_xyzxyz_m'][1]));y1=min(top-1,yr(o['surface_bounds_xyzxyz_m'][4]));material=palette[o['glass_material']]
    cells=[]
    for u in range(u0,max(u0+1,u1)):
     for y in range(y0,max(y0+1,y1)):
      q=self.facade_coord(g,u,y);old=self.b.s.owners.get(q,'')
      if old.startswith('wall.') or old.startswith('window.'):
       self.put(*q,material,'window.'+o['id']);cells.append(list(q))
    self.audit['openings'].append({'id':o['id'],'group':g['id'],'source':o,'quantized_u':[u0,u1],'quantized_y':[y0,y1],'cells':cells,'consumed':len(cells)>0})
    self.b.windows.append({'id':o['id'],'group':g['id'],'frozen':True,'quantized_u':[u0,u1],'quantized_y':[y0,y1]})
   for l in g['ledges']:
    u0,u1=Q(l['u0_m']),Q(l['u1_m']);y=yr(l['absolute_top_y_m'])-1;cells=[]
    # Top-half slab gives an actual top bearing surface for plant cubes.
    for u in range(u0,max(u0+1,u1)):
     q=self.facade_coord(g,u,y,1);anchor=self.facade_coord(g,u,y,0)
     self.put(*anchor,'smooth_quartz','ledge.'+l['id']+'.anchor')
     self.put(*q,M('smooth_quartz_slab',type='top'),'ledge.'+l['id']+'.tray');cells.append(list(q))
     if l['planted']:self.put(q[0],q[1]+1,q[2],'azalea_leaves','ledge.'+l['id']+'.plant')
    self.audit['ledges'].append({'id':l['id'],'source':l,'cells':cells,'planted':l['planted'],'top_actual_m':(y+1-4)/2,'depth_actual_m':.5,'thickness_actual_m':.25})
   if g['system']=='screen':
    openings=g['openings'];start=Q(min(o['u0_m'] for o in openings));end=Q(max(o['u1_m'] for o in openings))
    for u in range(start,end,4):
     for y in range(fy,top-1):self.put(*self.facade_coord(g,u,y,1),'orange_concrete','screen.'+g['id']+'.fin')
     self.put(*self.facade_coord(g,u,fy-1,1),'smooth_quartz','screen.'+g['id']+'.support')
    for u in range(start,end):self.put(*self.facade_coord(g,u,top-1,1),'orange_concrete','screen.'+g['id']+'.header')
  # Supplement only still-unopened inward returns. Stable cell IDs, not new
  # randomized front facades. Courtyard/public faces stay readable in 3D.
  for fi,f in enumerate(S['floors']):
   fy=yr(f['elevation']);top=yr(f['elevation']+f['height'])
   for i,j,face,qs in self.boundary(fi):
    if i in (0,29) or j in (0,23):continue
    if fi==1 and 22<=i<26:continue
    if self.maps[fi][(i,j)][0]=='core':continue
    if all(self.b.s.owners.get((x,fy+2,z),'').startswith('wall.') for x,z in qs):
     made=[]
     for x,z in qs[1:-1]:
      for y in range(fy+2,top-2):
       if self.b.s.owners.get((x,y,z),'').startswith('wall.'):
        self.put(x,y,z,'cyan_stained_glass_pane',f'return.F{fi+1}.{i}.{j}.{face}');made.append([x,y,z])
     if made:self.audit['hidden_returns'].append({'floor':fi+1,'cell':[i,j],'face':face,'cells':made,'status':'adapter_detail'})
 def cores(self):
  for core in S['cores']:
   x0,z0,x1,z1=xyrect(core['rect']);maxf=core['max_floor'];levels=self.p['floor_top_y'][:maxf+1];id=core['id']
   # Clear occupied core volumes, retaining a front landing on every level.
   self.box((x0+1,4,z0+1),(x1-1,levels[-1],z1-1),'minecraft:air','core.'+id+'.void')
   for fy in levels:
    self.box((x0+1,fy-1,z0+1),(x1-1,fy,z0+4),'smooth_stone','core.'+id+'.landing')
   for k,(fy,ty) in enumerate(zip(levels,levels[1:])):
    n=(ty-fy)//2;m=ty-fy-n;front=z0+4
    self.box((x0+1,fy+n-1,front+max(n,m)),(x0+11,fy+n,front+max(n,m)+3),'smooth_stone','stair.'+id+'.turn')
    for step in range(n):
     z=front+step;y=fy+step
     self.box((x0+2,y,z),(x0+6,y+1,z+1),M('smooth_quartz_stairs',facing='south'),'stair.'+id+'.up1')
     self.put(x0+6,y,z,'iron_bars','stair.'+id+'.rail_support');self.put(x0+6,y+1,z,'iron_bars','stair.'+id+'.rail')
    # Connect unequal flights to the same turn without a missing bearing gap.
    self.box((x0+2,fy+n-1,front+n),(x0+6,fy+n,front+max(n,m)+1),'smooth_stone','stair.'+id+'.turn_extension')
    for step in range(m):
     z=front+m-1-step;y=fy+n+step
     self.box((x0+8,y,z),(x0+11,y+1,z+1),M('smooth_quartz_stairs',facing='north'),'stair.'+id+'.up2')
     self.put(x0+7,y,z,'iron_bars','stair.'+id+'.rail_support');self.put(x0+7,y+1,z,'iron_bars','stair.'+id+'.rail')
    self.audit['stairs'].append({'core':id,'from_floor':k+1,'floor_y':fy,'next_y':ty,'flight_rises':[n,m],'start':[x0+3,fy,front-1],'end':[x0+9,ty,front-1]})
   # Explicit elevator shaft and glazed landing doors; no operational elevator.
   for x in [x0+12,x0+15]:self.box((x,4,z0+5),(x+1,levels[-1],z0+12),'light_gray_concrete','lift.'+id+'.wall')
   for z in [z0+5,z0+11]:self.box((x0+12,4,z),(x0+16,levels[-1],z+1),'light_gray_concrete','lift.'+id+'.wall')
   for fy in levels[:-1]:
    self.box((x0+13,fy,z0+5),(x0+15,fy+4,z0+6),'gray_stained_glass_pane','lift.'+id+'.door_static')
    # Open east edge of the core at each actual floor; internal routes terminate
    # here through the landing, not through solid placeholder columns.
    self.box((x1-2,fy,z0+1),(x1+1,fy+4,z0+4),'minecraft:air','door.'+id)
   # Roof exit small heads for C1/C2; C3 uses its specified roof enclosure nearby.
   ry=levels[-1]
   self.box((x0+1,ry,z0+1),(x0+12,ry+4,z0+2),'smooth_quartz','roof_exit.'+id)
   self.box((x0+1,ry+4,z0+1),(x0+12,ry+5,z0+5),'smooth_quartz','roof_exit.'+id+'.cap')
   for x in [x0+1,x0+11]:self.box((x,ry,z0+1),(x+1,ry+4,z0+5),'smooth_quartz','roof_exit.'+id)
 def doors(self):
  entries=[('main',[24,25.5,28,27],4),('staff',[4,47.5,8,49],4),('east',[54,25.5,58,27],4)]
  for id,r,fy in entries:
   self.rect(r,fy,fy+6,'minecraft:air','door.'+id)
   self.rect(r,fy-1,fy,'smooth_stone','door.'+id+'.threshold')
   self.audit['doors'].append({'id':id,'rect':r,'y':[fy,fy+6]})
 def terrace(self):
  for fi,f in enumerate(S['floors']):
   ts=set(map(tuple,f['terrace_cells']));mp=set(self.maps[fi]);fy=yr(f['elevation'])
   for i,j in sorted(ts):
    x0,z0,x1,z1=xyrect([i*2,j*2,i*2+2,j*2+2])
    for face,di,dj in [('W',-1,0),('E',1,0),('S',0,-1),('N',0,1)]:
     if (i+di,j+dj) in ts|mp:continue
     qs={'W':[(x0,z) for z in range(z0,z1)],'E':[(x1-1,z) for z in range(z0,z1)],'S':[(x,z1-1) for x in range(x0,x1)],'N':[(x,z0) for x in range(x0,x1)]}[face]
     for x,z in qs:
      for y in [fy,fy+1]:self.put(x,y,z,'gray_stained_glass_pane',f'terrace.F{fi+1}.guard')
    # Sparse supported low planters, kept away from the main terrace center.
    if (i*7+j*3)%11==0 and not any((i+di,j+dj) in mp for di,dj in [(1,0),(-1,0),(0,1),(0,-1)]):
     self.box((x0+1,fy,z0+1),(x0+3,fy+1,z0+3),'smooth_quartz',f'terrace.F{fi+1}.planter')
     self.box((x0+1,fy+1,z0+1),(x0+3,fy+2,z0+3),'azalea_leaves',f'terrace.F{fi+1}.green')
 def roof(self):
  for e in S['roof_equipment']:
   x0,z0,x1,z1=xyrect(e['rect']);y=yr(e['base']);top=yr(e['base']+e['height']);id='equipment.'+e['id']
   self.box((x0,y-1,z0),(x1,y,z1),'smooth_quartz',id+'.bearing')
   if e['kind']=='antenna':
    x=(x0+x1)//2;z=(z0+z1)//2
    self.box((x,y,z),(x+1,top,z+1),'iron_bars',id+'.mast')
    for yy in [y+2,top-2]:
     for xx in [x-1,x+1]:self.put(xx,yy,z,M('iron_trapdoor',open='true',facing='north'),id+'.panel')
   elif e['kind']=='hvac':
    self.box((x0,y,z0),(x1,top-1,z1),'light_gray_concrete',id+'.body')
    for x in range(x0+1,x1-1):
     for z in range(z0+1,z1-1):self.put(x,top-1,z,M('iron_trapdoor',half='top'),id+'.grille')
    for x in range(x0+1,x1,3):
     for yy in range(y,top-1):self.put(x,yy,z0,'iron_bars',id+'.vent')
   else:
    for x in [x0,x1-1]:self.box((x,y,z0),(x+1,top,z1),'light_gray_concrete',id+'.wall')
    for z in [z0,z1-1]:self.box((x0,y,z),(x1,top,z+1),'light_gray_concrete',id+'.wall')
    self.box((x0,top-1,z0),(x1,top,z1),'smooth_stone',id+'.roof')
    self.box((x0+2,y,z1-1),(min(x1-1,x0+5),min(y+4,top-1),z1),'minecraft:air',id+'.door')
   self.audit['equipment'].append({'id':e['id'],'kind':e['kind'],'bounds':[x0,y,z0,x1,top,z1]})
 def interior(self):
  for room in I['rooms']:
   fi=room['floor']-1;fy=yr(room['floor_elevation_m']);top=yr(room['floor_elevation_m']+room['floor_to_floor_height_m']);cells=set(map(tuple,room['occupied_cells']));kind=room['kind'];id=room['id'];count=0
   # Furniture lives strictly inside owned cells, leaving every shared corridor
   # untouched. Coarse modules are advisory interior detailing, not original CAD.
   for i,j in sorted(cells):
    if (i*3+j*5)%6!=0:continue
    if sum((i+di,j+dj) in cells for di,dj in [(1,0),(-1,0),(0,1),(0,-1)])<3:continue
    x0,z0,x1,z1=xyrect([i*2,j*2,i*2+2,j*2+2]);x=x0+1;z=z0+1
    if any((xx,yy,zz) in self.b.s.blocks for xx in range(x,x+2) for yy in range(fy,fy+3) for zz in range(z,z+2)):continue
    o='interior.'+id
    if kind in ['service','office','meeting','shared']:
     self.box((x,fy,z),(x+2,fy+1,z+1),'oak_planks',o+'.desk')
     self.put(x,fy+1,z,M('iron_trapdoor',half='bottom'),o+'.worktop')
     self.put(x,fy+1,z+1,M('dark_oak_stairs',facing='north'),o+'.chair')
     self.put(x,fy,z+1,'dark_oak_planks',o+'.chair_base')
     if kind in ['service','office']:self.put(x+1,fy+1,z,'black_stained_glass_pane',o+'.terminal')
    elif kind in ['waiting','public','lobby','activity']:
     for dx in [0,1]:self.put(x+dx,fy,z,M('oak_stairs',facing='south'),o+'.waiting_seat')
    else:
     self.box((x,fy,z),(x+2,fy+2,z+1),'oak_planks',o+'.storage')
    count+=1
   # Fixed service lighting, stable hash decision only for offices.
   lit=kind!='office' or int(hashlib.sha256((self.p['lighting']['namespace']+id).encode()).hexdigest()[:8],16)/2**32<self.p['lighting']['office_probability']
   if lit:
    for i,j in sorted(cells):
     if i%3==1 and j%3==1:
      x0,z0,x1,z1=xyrect([i*2,j*2,i*2+2,j*2+2]);q=(x0+1,top-2,z0+1)
      if q not in self.b.s.blocks and (q[0],top-1,q[2]) in self.b.s.blocks:self.put(*q,'sea_lantern','lighting.room.'+id)
   self.audit['furniture'].append({'id':id,'name':room['name'],'kind':kind,'modules':count,'lit':lit,'scope':'schematic service/office furniture in handed-off occupied cells'})
   self.b.rooms.append(self.audit['furniture'][-1])
  for fi,f in enumerate(S['floors']):
   fy=yr(f['elevation']);top=yr(f['elevation']+f['height'])
   for i,j,kind,id in f['cells']:
    if kind=='circulation' and i%3==1 and j%3==1:
     x0,z0,x1,z1=xyrect([i*2,j*2,i*2+2,j*2+2]);q=(x0+2,top-2,z0+2)
     if (q[0],top-1,q[2]) in self.b.s.blocks:self.put(*q,'sea_lantern','lighting.corridor')
  # Consultation island, self-service terminals and information board in atrium.
  for x in range(53,61):self.put(x,4,47,'smooth_quartz','interior.hall.consultation');self.put(x,5,47,M('dark_oak_slab',type='bottom'),'interior.hall.countertop')
  for x in [72,76]:
   self.put(x,4,41,'gray_concrete','interior.hall.kiosk');self.put(x,5,41,'black_stained_glass','interior.hall.kiosk_screen')
  for x in [51,74]:
   self.put(x,4,36,'smooth_quartz','interior.hall.guide_base');self.put(x,5,36,'blue_concrete','interior.hall.guide')
 def build(self):
  self.site();self.mass()
  if self.mode!='massing':self.facade();self.cores();self.terrace();self.roof();self.interior();self.doors()
  return self.b

def main():
 ap=argparse.ArgumentParser();ap.add_argument('--run',required=True);ap.add_argument('--mode',choices=['massing','complete'],default='complete');a=ap.parse_args()
 p=json.loads((C/'parameters.json').read_text());p['mode']=a.mode;obj=Civic(p,a.mode);b=obj.build()
 out=save_run(C,a.run,p,b,Path(__file__),{'route':p['route'],'adapter_status':'case_specific','world_origin_y_max':242,'sparse_air':True,'input_sha256':{f:hashlib.sha256((C/'input/data'/f).read_bytes()).hexdigest() for f in ['spatial.json','facade-resolved.json','interior-handoff.json']}})
 dump(out/'adaptation.json',obj.audit)
if __name__=='__main__':main()
