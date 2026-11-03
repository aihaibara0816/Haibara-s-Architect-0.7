"""R10 delta: supported fixed ambient lights and two entrance bamboo gardens."""
from build_case import *
from vendor.inspect_build import load_build,Limits
from detail_lab import states
import gzip
BASE='v03_r10_public'
class LightingGarden:
 def __init__(self):
  d=C/'runs'/BASE;rb=load_build(d/'building.nbt',Limits(cells=40000000,nodes=16000000));od=json.loads(gzip.decompress((d/'component_ownership.json.gz').read_bytes()))
  self.old=dict(rb.blocks);self.oldowners={tuple(q[:3]):od['owner_names'][q[3]] for q in od['xyz_owner']}
  self.b=Builder(list(rb.size));self.b.s.blocks=dict(rb.blocks);self.b.s.owners=dict(self.oldowners);self.b.windows=json.loads((d/'windows.json').read_text());self.b.rooms=json.loads((d/'interiors.json').read_text())
  self.audit=json.loads((d/'adaptation.json').read_text());self.p=json.loads((d/'params_used.json').read_text());self.p['lighting_garden_revision']='V0.3.2';self.fixtures=[];self.stems=[];self.gardens=[]
  self.p['ambient_lighting']={'public_spacing_blocks':8,'office_spacing_blocks':10,'public_strip_length':3,'office_strip_length':2,'namespace':'fixed-functional-ambient-v1','old_task_lights':'retained'}
 def no_pane_neighbor(self,x,y,z):return not any(states.family(self.b.s.blocks.get((x+dx,y,z+dz),'minecraft:air'))=='pane' for dx,dz in [(1,0),(-1,0),(0,1),(0,-1)])
 def ceiling(self,x,z,top,id,mat='sea_lantern',length=3):
  qs=[(xx,top-2,z) for xx in range(x,x+length)]
  if any(q in self.b.s.blocks or not states.support_cube(self.b.s.blocks.get((q[0],top-1,q[2]),'minecraft:air')) or not self.no_pane_neighbor(*q) for q in qs):return False
  for q in qs:self.b.put(*q,mat,'lighting3.'+id)
  self.fixtures.append({'id':id,'type':'ceiling','cells':qs,'support_y':top-1,'material':mat});return True
 def inset(self,x,z,y,id,mat='glowstone'):
  q=x,y,z;o=self.oldowners.get(q,'')
  if not (o.startswith(('floor.','terrace.','site.ground','site.park_route')) or '.floor.' in o):return False
  if (x,y+1,z) in self.b.s.blocks or not self.no_pane_neighbor(x,y,z):return False
  self.b.put(*q,mat,'lighting3.'+id);self.fixtures.append({'id':id,'type':'inset_floor','cells':[q],'material':mat});return True
 def lighting(self):
  # Every functional room gets a modest ambient layer; existing brighter task
  # strips and office lighting decisions remain untouched.
  for r in I['rooms']:
   if r['id']=='104':continue
   fy=yr(r['floor_elevation_m']);top=yr(r['floor_elevation_m']+r['floor_to_floor_height_m']);mask=set()
   for i,j in r['occupied_cells']:
    x0,z0,x1,z1=xyrect([i*2,j*2,i*2+2,j*2+2]);mask.update((x,z) for x in range(x0,x1) for z in range(z0,z1))
   step=8 if r['floor']<=3 else 10;length=3 if r['floor']<=3 else 2
   warm=r['kind'] in ['support','lounge'] or r['id'] in ['102','202','304','306','307','403','503','603','703']
   for x in range(15,132,step):
    for z in range(15,108,step):
     if not all((x+dx,z) in mask for dx in range(length)):continue
     if any((x+dx,fy-1,z) not in self.old for dx in range(length)):continue
     self.ceiling(x,z,top,'ambient.'+r['id'], 'glowstone' if warm else 'sea_lantern',length)
  for fi,f in enumerate(S['floors'],1):
   top=yr(f['elevation']+f['height'])
   for i,j,kind,id in f['cells']:
    if kind=='circulation' and (i+j)%2==0:
     x0,z0,x1,z1=xyrect([i*2,j*2,i*2+2,j*2+2]);self.ceiling(x0+1,z0+2,top,f'corridor.F{fi}',length=2)
   for core in S['cores']:
    if fi>core['max_floor']:continue
    x0,z0,x1,z1=xyrect(core['rect'])
    for dx,dz in [(3,2),(9,2),(2,11)]:self.ceiling(x0+dx,z0+dz,top,f'landing.{core["id"]}.F{fi}',length=2)
    fy=yr(f['elevation'])
    for z in [z0,z1-1]:
     q=(x0+6,fy+3,z)
     if self.oldowners.get(q)==f'core.{core["id"]}.wall' and self.no_pane_neighbor(*q):
      self.b.put(*q,'glowstone','lighting3.core_inset.'+core['id']);self.fixtures.append({'id':'core_inset.'+core['id'],'type':'wall_inset','cells':[q],'material':'glowstone'})
   for i,j in f['terrace_cells']:
    if i%4==1 and j%3==1:
     x0,z0,x1,z1=xyrect([i*2,j*2,i*2+2,j*2+2]);self.inset(x0+2,z0+2,yr(f['elevation'])-1,f'terrace.F{fi}')
  # Tall atrium: floor-edge accents bridge the light falloff from the high
  # ceiling, while the protected double-height central volume stays empty.
  for x in [51,62,73]:
   for z in [35,51]:
    for dx in range(3):self.inset(x+dx,z,3,'atrium_edge')
  for z in range(34,53,4):
   for x in [49,79]:self.ceiling(x,z,23,'atrium_perimeter',length=1)
  # Low-level dark corners found in the independent R12 lightfield preview.
  for x,z in [(14,78),(14,82),(14,86),(30,50),(34,18),(58,62),(58,70),(70,42),(82,42),(94,54),(98,54),(130,38),(130,46),(130,14)]:
   if not self.ceiling(x,z,14,'F1_corner',length=1):self.inset(x,z,3,'F1_corner')
  # Bridge soffit lights are inset into its existing slab: no reduced clearance.
  for x in [104,110]:
   for z in [26,30]:self.inset_bridge(x,13,z)
  for x,z in [(74,60),(82,60),(76,83),(82,94),(62,99),(76,99),(119,61),(129,61)]:self.bollard(x,z,'entry_path')
 def inset_bridge(self,x,y,z):
  q=x,y,z
  if self.oldowners.get(q,'').startswith('floor.') and self.no_pane_neighbor(*q):
   self.b.put(*q,'sea_lantern','lighting3.bridge_soffit');self.fixtures.append({'id':'bridge_soffit','type':'inset_slab','cells':[q],'material':'sea_lantern'})
 def bollard(self,x,z,id):
  if any((x,y,z) in self.b.s.blocks for y in [4,5,6]):return
  if any(not self.no_pane_neighbor(x,y,z) for y in [4,5,6]):return
  if not states.support_cube(self.b.s.blocks.get((x,3,z),'minecraft:air')):return
  self.b.put(x,4,z,'polished_deepslate','garden.fixture_support');self.b.put(x,5,z,'glowstone','lighting3.'+id);self.b.put(x,6,z,M('polished_deepslate_slab',type='bottom'),'garden.fixture_cap')
  self.fixtures.append({'id':id,'type':'bollard','cells':[[x,5,z]],'material':'glowstone'})
 def garden(self,id,rect):
  x0,z0,x1,z1=rect
  for x in range(x0,x1):
   for z in range(z0,z1):
    assert (x,4,z) not in self.b.s.blocks
    edge=x in [x0,x1-1] or z in [z0,z1-1]
    self.b.put(x,4,z,M('smooth_quartz_slab',type='top') if edge else 'moss_block','garden.'+id+('.rim' if edge else '.soil'))
  for x in range(x0+2,x1-2,2):
   for z in range(z0+2,z1-2,3):
    n=int(hashlib.sha256(f'bamboo-v1:{id}:{x}:{z}'.encode()).hexdigest()[:8],16);h=5+n%5
    if n%6==0:continue
    for dy in range(h):
     leaves='large' if dy>=h-2 else 'small' if dy==h-3 else 'none'
     self.b.put(x,5+dy,z,M('bamboo',age=1,leaves=leaves,stage=1),'garden.'+id+'.bamboo')
    self.stems.append({'garden':id,'base':[x,5,z],'height':h,'tip_stage':1})
  for x in range(x0+2,x1-1,4):
   q=(x,5,z1-2)
   if q not in self.b.s.blocks:self.b.put(*q,'oxeye_daisy','garden.'+id+'.flowers')
  # An outward-facing bench stays outside the central entry route.
  for x in range(x0+1,x1-1):
   self.b.put(x,4,z1,M('oak_slab',type='top'),'garden.'+id+'.bench');self.b.put(x,4,z1+1,M('oak_slab',type='top'),'garden.'+id+'.bench')
  for x,z in [(x0+1,z0+1),(x1-2,z1-2)]:
   self.b.put(x,5,z,'glowstone','lighting3.garden.'+id);self.b.put(x,6,z,M('dark_oak_slab',type='bottom'),'garden.'+id+'.light_cap')
   self.fixtures.append({'id':'garden.'+id,'type':'planter_light','cells':[[x,5,z]],'material':'glowstone'})
  self.gardens.append({'id':id,'rect_xz_blocks':rect,'source':'user-requested bamboo garden; placement adapted to approved entrance','ground_y':4,'approach_path_xz':[[82,100],[78,84],[68,66],[64,58]]})
 def build(self):
  self.garden('west',[62,80,73,94]);self.garden('east',[86,62,99,75]);self.lighting()
  self.audit['lighting_garden_revision']={'baseline':BASE,'fixtures':self.fixtures,'bamboo_stems':self.stems,'gardens':self.gardens,'lighting_basis':'functional synthetic completion, retaining prior task lights','preview_limit':'bamboo stems use official model dimensions; foliage is simplified, no resource pack texture or actual game test'}
  return self.b
if __name__=='__main__':
 ap=argparse.ArgumentParser();ap.add_argument('--run',required=True);args=ap.parse_args();a=LightingGarden();b=a.build();out=save_run(C,args.run,a.p,b,Path(__file__),{'baseline_run':BASE,'route':'interior_lighting_and_entrance_bamboo','game_status':'pending'});dump(out/'adaptation.json',a.audit)
 print('added fixtures',len(a.fixtures),'bamboo stems',len(a.stems))
