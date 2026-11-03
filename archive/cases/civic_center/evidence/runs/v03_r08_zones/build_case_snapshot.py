"""User-requested civic interiors: authored social zones, frames and clusters.
Starts from immutable R06; exterior geometry and frozen facade remain exact.
"""
from build_case import *
from vendor.inspect_build import load_build,Limits
from detail_lab import states
import gzip,copy
from collections import deque
BASE='v03_r06_final'
class ZonedInterior:
 def __init__(self):
  d=C/'runs'/BASE;self.p=json.loads((d/'params_used.json').read_text());self.p['interior_revision']='v0.3.1 public zones';self.p['interior_lighting_namespace']='civic-zones-v2'
  rb=load_build(d/'building.nbt',Limits(cells=40000000,nodes=16000000));od=json.loads(gzip.decompress((d/'component_ownership.json.gz').read_bytes()));self.old_owners={tuple(q[:3]):od['owner_names'][q[3]] for q in od['xyz_owner']};self.old_blocks=dict(rb.blocks)
  self.b=Builder(list(rb.size));self.b.s.blocks=dict(rb.blocks);self.b.s.owners=dict(self.old_owners)
  for q,o in list(self.b.s.owners.items()):
   if o.startswith(('interior.','lighting.room.','lighting.corridor','lighting.atrium_fixed')):self.b.s.blocks.pop(q);self.b.s.owners.pop(q)
  self.audit=json.loads((d/'adaptation.json').read_text());self.audit['furniture']=[];self.b.windows=json.loads((d/'windows.json').read_text())
  self.rooms={r['id']:r for r in I['rooms']};self.masks={};self.reserved={};self.paths=[];self.ports={};self.modules=[];self.zones=[];self.frames=[];self.skipped=[];self.revision={'baseline':BASE,'feedback':'too uniform and scattered, lacks public areas','structural_status':'visual pseudo-columns only; no engineering analysis'}
  for r in I['rooms']:
   mask=set()
   for i,j in r['occupied_cells']:
    x0,z0,x1,z1=xyrect([i*2,j*2,i*2+2,j*2+2]);mask.update((x,z) for x in range(x0,x1) for z in range(z0,z1))
   self.masks[r['id']]=mask
  for fi,f in enumerate(S['floors']):
   fy=yr(f['elevation']);res=set()
   for i,j,kind,id in f['cells']:
    if kind=='circulation':
     x0,z0,x1,z1=xyrect([i*2,j*2,i*2+2,j*2+2]);res.update((x,z) for x in range(x0,x1) for z in range(z0,z1))
   self.reserved[fi+1]=res
   # Preserve actual R06 access detours as well as diagrammed circulation cells.
   start=(44,28);prev={start:None};todo=deque([start])
   def walk(q):
    x,z=q;v=self.b.s.blocks.get((x,fy-1,z));return v and states.support_cube(v) and all((x,y,z) not in self.b.s.blocks for y in range(fy,fy+3))
   while todo:
    q=todo.popleft()
    for dx,dz in [(1,0),(-1,0),(0,1),(0,-1)]:
     nq=q[0]+dx,q[1]+dz
     if nq not in prev and walk(nq):prev[nq]=q;todo.append(nq)
   targets=[]
   for core in S['cores']:
    if fi+1<=core['max_floor']:
     x0,z0,x1,z1=xyrect(core['rect']);targets.append((core['id'],(x0+9,z0+2)))
   for r in I['rooms']:
    if r['floor']!=fi+1:continue
    candidates=[q for q in self.masks[r['id']] if q in prev and walk(q) and any((q[0]+dx,q[1]+dz) in res for dx,dz in [(1,0),(-1,0),(0,1),(0,-1)])]
    if not candidates:candidates=[q for q in self.masks[r['id']] if q in prev and walk(q)]
    if candidates:
     target=min(candidates,key=lambda q:abs(q[0]-44)+abs(q[1]-28));targets.append((r['id'],target));self.ports[r['id']]=[target[0],fy,target[1]]
   for id,target in targets:
    if target not in prev:continue
    path=[];q=target
    while q is not None:path.append(q);q=prev[q]
    for x,z in path:
     for dx in [-1,0,1]:
      for dz in [-1,0,1]:res.add((x+dx,z+dz))
    self.paths.append({'floor':fi+1,'target_id':id,'path_xz':path})
 def coord(self,x,z):return 12+Q(x),12+Q(48-z)
 def safe(self,rid,x,z,dy=0):
  r=self.rooms[rid];fy=yr(r['floor_elevation_m']);q=(x,fy+dy,z)
  return (x,z) in self.masks[rid] and (x,z) not in self.reserved[r['floor']] and (x,fy-1,z) in self.b.s.blocks and q not in self.b.s.blocks
 def place(self,rid,id,parts,kind):
  r=self.rooms[rid];fy=yr(r['floor_elevation_m']);coords={}
  for a,b,m in parts:
   for x in range(a[0],b[0]):
    for y in range(a[1],b[1]):
     for z in range(a[2],b[2]):coords[(x,fy+y,z)]=m
  shifts=[(0,0)]
  if kind not in ['pseudo_column','sofa','glazed_partition']:
   shifts += sorted([(dx,dz) for dx in range(-5,6) for dz in range(-5,6) if 0<abs(dx)+abs(dz)<=6],key=lambda q:(abs(q[0])+abs(q[1]),abs(q[1]),q))
  chosen=None
  for dx,dz in shifts:
   candidate={(x+dx,y,z+dz):m for (x,y,z),m in coords.items()}
   if any((x,z) not in self.masks[rid] or (x,z) in self.reserved[r['floor']] or (x,fy-1,z) not in self.b.s.blocks or (x,y,z) in self.b.s.blocks for x,y,z in candidate):continue
   chosen=(candidate,dx,dz);break
  if chosen is None:self.skipped.append({'id':id,'room':rid,'reason':'no complete placement respecting circulation, existing geometry and owned cells'});return False
  coords,dx,dz=chosen
  for q,m in coords.items():self.b.put(*q,m,'interior2.'+rid+'.'+id)
  self.modules.append({'id':id,'room':rid,'floor':r['floor'],'kind':kind,'adjustment_blocks':[dx,dz],'blocks':len(coords),'bounds':[min(q[0] for q in coords),min(q[1] for q in coords),min(q[2] for q in coords),max(q[0] for q in coords)+1,max(q[1] for q in coords)+1,max(q[2] for q in coords)+1]})
  return True
 def paint(self,rid,rect,mat,id):
  fy=yr(self.rooms[rid]['floor_elevation_m']);x0,z0,x1,z1=xyrect(rect);n=0
  for x in range(x0,x1):
   for z in range(z0,z1):
    q=(x,fy-1,z)
    if (x,z) not in self.masks[rid] or not self.b.s.owners.get(q,'').startswith('floor.'):continue
    # Exterior slab edges and facade positions are immutable.
    if any(self.old_owners.get((x+dx,fy,z+dz),'').startswith(('wall.','window.','return.','ledge.')) for dx,dz in [(0,0),(1,0),(-1,0),(0,1),(0,-1)]):continue
    self.b.put(*q,mat,'interior2.'+rid+'.floor.'+id);n+=1
  self.zones.append({'id':id,'room':rid,'floor':self.rooms[rid]['floor'],'rect_m':rect,'material':mat,'painted_blocks':n})
 def table(self,rid,id,xm,zm,w=6,d=3,kind='shared_table'):
  x,z=self.coord(xm,zm);parts=[((x,1,z),(x+w,2,z+d),M('oak_slab',type='bottom'))]
  for xx in [x,x+w-1]:
   for zz in [z,z+d-1]:parts.append(((xx,0,zz),(xx+1,1,zz+1),'dark_oak_planks'))
  # Chairs face the table as a coherent cluster.
  for xx in range(x+1,x+w-1,2):
   for zz,back in [(z-1,z-2),(z+d,z+d+1)]:parts.extend([((xx,0,zz),(xx+1,1,zz+1),'oak_planks'),((xx,0,back),(xx+1,2,back+1),'dark_oak_planks')])
  return self.place(rid,id,parts,kind)
 def sofa(self,rid,id,xm,zm,w=8,face='north'):
  x,z=self.coord(xm,zm);back=z if face=='south' else z+2
  return self.place(rid,id,[((x,0,z),(x+w,1,z+3),'light_gray_concrete'),((x,1,back),(x+w,2,back+1),'blue_concrete'),((x,1,z),(x+1,2,z+3),'blue_concrete'),((x+w-1,1,z),(x+w,2,z+3),'blue_concrete')],'sofa')
 def coffee(self,rid,id,xm,zm):
  x,z=self.coord(xm,zm);return self.place(rid,id,[((x,0,z),(x+4,1,z+2),M('smooth_quartz_slab',type='bottom'))],'coffee_table')
 def planter(self,rid,id,xm,zm):
  x,z=self.coord(xm,zm);return self.place(rid,id,[((x,0,z),(x+3,1,z+3),'smooth_quartz'),((x,1,z),(x+3,2,z+3),'azalea_leaves')],'indoor_planter')
 def shelf(self,rid,id,xm,zm,w=8):
  x,z=self.coord(xm,zm);return self.place(rid,id,[((x,0,z),(x+w,3,z+1),'bookshelf'),((x,3,z),(x+w,4,z+1),M('oak_slab',type='bottom'))],'shelf_partition')
 def counter(self,rid,id,xm,zm,w=18):
  x,z=self.coord(xm,zm);parts=[((x,0,z),(x+w,2,z+2),'smooth_quartz'),((x,2,z),(x+w,3,z+2),M('dark_oak_slab',type='bottom')),((x+w-3,0,z+2),(x+w,2,z+5),'smooth_quartz')]
  for xx in range(x+2,x+w-2,5):parts.append(((xx,3,z),(xx+1,4,z+1),'black_stained_glass_pane'))
  return self.place(rid,id,parts,'service_counter')
 def kiosk(self,rid,id,xm,zm):
  x,z=self.coord(xm,zm);return self.place(rid,id,[((x,0,z),(x+2,3,z+2),'smooth_quartz'),((x,3,z),(x+2,5,z+1),'blue_concrete'),((x,3,z+1),(x+2,4,z+2),'black_stained_glass')],'self_service')
 def partition(self,rid,id,xm,z0m,z1m,door_m):
  x,z0=self.coord(xm,z1m);_,z1=self.coord(xm,z0m);_,dz=self.coord(xm,door_m);parts=[]
  for z in range(z0,z1):
   if abs(z-dz)<=2:continue
   parts += [((x,0,z),(x+1,2,z+1),'smooth_quartz'),((x,2,z),(x+1,6,z+1),'gray_stained_glass_pane')]
  if parts:return self.place(rid,id,parts,'glazed_partition')
 def lounge(self,rid,id,rect):
  x0,z0,x1,z1=rect;self.paint(rid,rect,'oak_planks',id)
  W=x1-x0;H=z1-z0
  if W<5:
   x,z=self.coord(x0+.5,z1-1);length=min(12,Q(H-2))
   self.place(rid,id+'.long_bench',[((x,0,z),(x+3,1,z+length),'light_gray_concrete'),((x,1,z),(x+1,2,z+length),'blue_concrete'),((x,1,z),(x+3,2,z+1),'blue_concrete'),((x,1,z+length-1),(x+3,2,z+length),'blue_concrete')],'sofa')
   self.planter(rid,id+'.plant',x0+2,z0+2);return
  w=min(10,Q(W-3));xm=x0+1
  self.sofa(rid,id+'.sofaA',xm,z1-.5,w,'south')
  if H>=6:self.sofa(rid,id+'.sofaB',xm,z0+1.5,w,'north')
  self.coffee(rid,id+'.coffee',xm+.5,(z0+z1)/2+.5 if H>=6 else z0+1.5)
  self.planter(rid,id+'.plant',x1-2,z1-.5)
 def workpod(self,rid,id,xm,zm,w=10):
  x,z=self.coord(xm,zm);parts=[((x,1,z),(x+w,2,z+5),M('smooth_quartz_slab',type='bottom'))]
  for xx in [x,x+w-1]:
   for zz in [z,z+4]:parts.append(((xx,0,zz),(xx+1,1,zz+1),'dark_oak_planks'))
  parts.append(((x,2,z+2),(x+w,3,z+3),'gray_stained_glass_pane'))
  for xx in range(x+1,x+w,3):
   for zz,back in [(z-1,z-2),(z+5,z+6)]:parts.extend([((xx,0,zz),(xx+1,1,zz+1),'oak_planks'),((xx,0,back),(xx+1,2,back+1),'dark_oak_planks')])
  return self.place(rid,id,parts,'work_pod')
 def columns(self):
  anchors=[(2,9),(12,9),(12,25),(2,25),(12,37),(24,44),(35,37),(42,44),(56,28),(58,36)]
  for fi,f in enumerate(S['floors']):
   fy=yr(f['elevation']);top=yr(f['elevation']+f['height']);accepted=[]
   for ai,(xm,zm) in enumerate(anchors):
    x,z=self.coord(xm,zm);rid=next((r['id'] for r in I['rooms'] if r['floor']==fi+1 and all((xx,zz) in self.masks[r['id']] for xx in range(x,x+2) for zz in range(z,z+2))),None)
    if not rid:continue
    if any((x+dx,top-1,z+dz) not in self.b.s.blocks for dx in [0,1] for dz in [0,1]):continue
    if self.place(rid,f'column.{ai}',[((x,0,z),(x+2,top-fy-1,z+2),'smooth_quartz')],'pseudo_column'):
     accepted.append((x,z,rid));self.frames.append({'floor':fi+1,'xy_base':[x,fy,z],'size':[2,top-fy-1,2],'structural':'visual_only'})
   # Short beams connect same-axis neighboring columns only across occupied slabs.
   for i,(x,z,rid) in enumerate(accepted):
    for X,Z,RID in accepted[i+1:]:
     if x!=X and z!=Z:continue
     dist=abs(x-X)+abs(z-Z)
     if not 4<=dist<=36:continue
     qs=[(xx,top-2,zz) for xx in range(min(x,X),max(x,X)+2) for zz in range(min(z,Z),max(z,Z)+2)]
     if any((xx,top-1,zz) not in self.b.s.blocks or self.old_owners.get((xx,fy,zz),'').startswith(('wall.','window.','guard.')) for xx,yy,zz in qs):continue
     for q in qs:
      if q not in self.b.s.blocks:self.b.put(*q,'light_gray_concrete',f'interior2.frame.F{fi+1}.beam')
 def furnish(self):
  # Public services: long counters, queue seating and form-filling tables.
  self.paint('101',[1,1,14,10],'smooth_sandstone','service_hall')
  self.counter('101','continuous_service',2,6,20)
  self.table('101','form_filling',2,22,10,3,'form_filling')
  self.sofa('101','queue_row_A',2,3,18,'north');self.sofa('101','queue_row_B',2,8,18,'south')
  for k,x in enumerate([10.5,12]):self.kiosk('101','kiosk'+str(k),x,20)
  self.lounge('102','quiet_waiting',[10,27,14,37])
  self.shelf('103','archiveA',1,29,12);self.shelf('103','archiveB',1,35,12);self.partition('103','backoffice_boundary',8,27,37,32)
  self.paint('104',[19,27,33,37],'smooth_sandstone','public_atrium')
  self.counter('104','consultation_island',28,36,8)
  self.lounge('104','atrium_lounge',[19,33,25,37]);self.kiosk('104','information',30,29)
  self.lounge('105','consult_lounge',[35,27,43,33]);self.table('105','consult_table',35,36,8,3,'consultation')
  self.partition('105','privacy_screen',40,27,37,34)
  self.lounge('106','public_refresh',[25,43,33,47]);self.shelf('106','documents',36,46,10)
  self.shelf('107','exhibition_wall',58,28,2);self.kiosk('107','exhibit_terminal',58,33);self.sofa('107','entry_waiting',52.5,29,6)
  # Second floor: appointments and calm waiting, plus a distinct classroom.
  self.paint('201',[1,1,14,10],'smooth_sandstone','appointment')
  for k,x in enumerate([2,7]):self.table('201','interview'+str(k),x,5,6,3,'interview')
  self.partition('201','private_rooms',6.5,1,9,7.5)
  self.lounge('201','appointment_lounge',[1,19,13,25])
  self.lounge('202','quiet_lounge_A',[1,27,7,37]);self.lounge('202','quiet_lounge_B',[8,27,14,37])
  self.shelf('202','reading_wall',2,36,8)
  self.shelf('203','filing',11,46,20);self.table('203','support',25,45,8,3,'backoffice')
  self.table('204','booking',35,35,10,3,'interview');self.lounge('204','booking_wait',[35,27,43,32])
  self.lounge('205','tea_corner',[35,43,42,47])
  self.paint('206',[53,27,59,37],'oak_planks','classroom')
  self.shelf('206','teaching_wall',53,36,10)
  for k,z in enumerate([29,32,35]):self.table('206','classrow'+str(k),53.5,z,8,2,'classroom_table')
  # Third floor is a community floor, deliberately without office work pods.
  self.paint('301',[1,1,14,10],'oak_planks','meeting_forum');self.table('301','conference',2,5,18,4,'conference_table');self.lounge('301','shared_lounge',[1,19,13,25])
  self.paint('302',[1,27,14,37],'smooth_sandstone','workshop')
  self.table('302','workshopA',2,30,10,4,'workshop_table');self.table('302','workshopB',8,34,8,4,'workshop_table');self.shelf('302','materials_wall',2,36,8)
  self.shelf('303','community_storage',11,46,22);self.table('303','staff_help',25,45,8,3,'support')
  self.lounge('304','cross_volume_lounge',[25,24,34,29]);self.lounge('304','cross_volume_lounge_B',[35,24,43,29]);self.shelf('304','public_reading',26,20,18)
  self.paint('305',[25,31,51,37],'smooth_sandstone','flexible_activity')
  self.table('305','activity_roundtable_A',26,34,10,4,'activity_table');self.table('305','activity_roundtable_B',34,34,10,4,'activity_table');self.lounge('305','activity_break',[42,31,51,37])
  self.lounge('306','multipurpose',[53,27,59,37]);self.shelf('306','media_wall',53,36,9)
  self.lounge('307','community_tea',[35,43,43,47])
  # Office floors: coherent six-seat pods, shared storage, meeting and rest zones.
  for floor in [4,5]:
   a=f'{floor}01';b=f'{floor}02';self.paint(a,[1,1,14,10],'polished_andesite','work_zone')
   self.workpod(a,'team_pod_A',2,5,10);self.workpod(a,'team_pod_B',8,5,10)
   self.lounge(a,'staff_lounge',[1,19,13,25]);self.shelf(a,'shared_files',11,13,4)
   self.paint(b,[1,27,14,37],'polished_andesite','team_zone');self.workpod(b,'team_pod_A',2,30,10);self.workpod(b,'team_pod_B',8,34,10);self.shelf(b,'shared_files',2,36,8)
  self.lounge('403','staff_tea',[11,43,23,47]);self.shelf('403','print_corner',25,46,10)
  self.paint('404',[25,24,43,29],'oak_planks','meeting');self.table('404','long_meeting',27,27,22,4,'conference_table');self.partition('404','meeting_edge',42,24,29,26)
  self.paint('405',[25,31,51,37],'polished_andesite','co_work');self.workpod('405','pod_A',26,34,10);self.workpod('405','pod_B',33,34,10);self.lounge('405','team_break',[41,31,51,37])
  self.table('406','interview',53,34,9,3,'interview');self.lounge('407','break_corner',[35,43,43,47])
  self.lounge('503','tea_archive',[11,43,23,47]);self.table('504','conference',37,36,20,3,'conference_table');self.lounge('505','staff_break',[37,43,50,47]);self.table('506','interview',53,36,8,2,'interview')
  for floor in [6,7]:
   a=f'{floor}01';b=f'{floor}02';d=f'{floor}03'
   self.paint(a,[1,19,14,29],'polished_andesite','office_team')
   self.workpod(a,'pod_A',2,22,10);self.workpod(a,'pod_B',8,27,10)
   self.lounge(a,'window_rest',[10,9,14,17]);self.shelf(a,'shared_storage',1,19,10)
   self.paint(b,[1,31,14,37],'oak_planks','meeting_collaboration');self.table(b,'meeting',2,34,18,3,'conference_table')
   self.partition(b,'meeting_boundary',12.5,31,37,35)
   self.lounge(d,'tea_corner',[11,43,23,47])
 def lights(self):
  # Sparse grouped pendant strips rather than identical dots over every cell.
  for zid in self.zones:
   r=self.rooms[zid['room']];fy=yr(r['floor_elevation_m']);top=yr(r['floor_elevation_m']+r['floor_to_floor_height_m']);x0,z0,x1,z1=xyrect(zid['rect_m']);cx=(x0+x1)//2;cz=(z0+z1)//2
   if r['id']=='104':top=23
   lit=r['floor']<=3 or int(hashlib.sha256((self.p['interior_lighting_namespace']+':20261026:'+r['id']).encode()).hexdigest()[:8],16)/2**32<.6
   if not lit:continue
   for x in range(cx-2,cx+3):
    if (x,top-1,cz) not in self.b.s.blocks:continue
    if (x,top-2,cz) in self.b.s.blocks:continue
    # Keep the agreed open atrium volume; edge fixtures remain separately fixed.
    if r['id']=='104':continue
    self.b.put(x,top-2,cz,'sea_lantern','lighting.interior2.'+r['id'])
  for fi,f in enumerate(S['floors']):
   fy=yr(f['elevation']);top=yr(f['elevation']+f['height'])
   for i,j,kind,id in f['cells']:
    if kind=='circulation' and i%4==0 and j%3==1:
     x0,z0,x1,z1=xyrect([i*2,j*2,i*2+2,j*2+2]);q=(x0+2,top-2,z0+2)
     if (q[0],top-1,q[2]) in self.b.s.blocks and q not in self.b.s.blocks:self.b.put(*q,'sea_lantern','lighting.interior2.corridor')
  for x in [49,79]:
   for z in [34,52]:self.b.put(x,21,z,'sea_lantern','lighting.atrium_fixed')
 def build(self):
  self.columns();self.furnish();self.lights()
  for r in I['rooms']:
   mods=[m for m in self.modules if m['room']==r['id'] and m['kind']!='pseudo_column'];row={'id':r['id'],'name':r['name'],'kind':r['kind'],'modules':len(mods),'lit':any(o.startswith('lighting.interior2.'+r['id']) for o in self.b.s.owners.values()),'scope':'authored functional clusters, floor zones and visual frame; not complete fitted interiors'}
   self.audit['furniture'].append(row);self.b.rooms.append(row)
  self.audit['interior_revision']={**self.revision,'zones':self.zones,'modules':self.modules,'frames':self.frames,'protected_paths':self.paths,'room_access_ports':self.ports,'skipped_modules':self.skipped}
  return self.b
if __name__=='__main__':
 ap=argparse.ArgumentParser();ap.add_argument('--run',required=True);a=ap.parse_args();o=ZonedInterior();b=o.build()
 out=save_run(C,a.run,o.p,b,Path(__file__),{'baseline_run':BASE,'route':'approved_original_interior_revision','adapter_status':'case_specific','world_origin_y_max':242,'sparse_air':True})
 dump(out/'adaptation.json',o.audit);print('zones',len(o.zones),'modules',len(o.modules),'columns',len(o.frames),'skipped',len(o.skipped))
