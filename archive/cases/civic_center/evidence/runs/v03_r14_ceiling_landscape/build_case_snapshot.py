"""R13 delta: flush two-block ceilings and a complete modern public forecourt."""
from revise_lighting_garden import *
BASE='v03_r13_lighting'
class CeilingLandscape:
 def __init__(self):
  d=C/'runs'/BASE;rb=load_build(d/'building.nbt',Limits(cells=40000000,nodes=16000000));od=json.loads(gzip.decompress((d/'component_ownership.json.gz').read_bytes()))
  self.old=dict(rb.blocks);self.oo={tuple(q[:3]):od['owner_names'][q[3]] for q in od['xyz_owner']};self.b=Builder(list(rb.size));self.b.s.blocks=dict(rb.blocks);self.b.s.owners=dict(self.oo);self.b.windows=json.loads((d/'windows.json').read_text());self.b.rooms=json.loads((d/'interiors.json').read_text());self.ad=json.loads((d/'adaptation.json').read_text());self.p=json.loads((d/'params_used.json').read_text());self.ceil=[];self.stems=[];self.paths=[];self.trees=[];self.water=[]
 def put(self,x,y,z,m,o):self.b.put(x,y,z,m,o)
 def ceiling(self):
  cores=[xyrect(c['rect']) for c in S['cores']]
  for (x,y,z),v in self.old.items():
   if y not in [13,22,31,39,47,55,63]:continue
   o=self.oo.get((x,y,z),'')
   if not (o.startswith(('floor.','roof.','terrace.')) or (o.startswith('interior2.') and '.floor.' in o)):continue
   if not states.support_cube(v):continue
   # Never lower stair shafts or the open outdoor park passage.
   if any(a<=x<b and c<=z<d for a,c,b,d in cores):continue
   if 100<=x<116 and 12<=z<56:continue
   # Keep existing pane states and a perimeter shadow reveal unchanged.
   if any(states.family(self.old.get((x+dx,y-1,z+dz),'minecraft:air'))=='pane' for dx,dz in [(0,0),(1,0),(-1,0),(0,1),(0,-1)]):continue
   if (x,y-1,z) not in self.old:
    self.put(x,y-1,z,'smooth_quartz','ceiling4.panel');self.ceil.append([x,y-1,z])
  # Landing fixtures lack the new ceiling because of stair clearance: recess them
  # directly into their existing supporting slab instead of leaving cubic drops.
  self.recess=[]
  for q,v in list(self.b.s.blocks.items()):
   o=self.b.s.owners.get(q,'')
   if o.startswith(('lighting.','lighting3.')) and v in ['minecraft:sea_lantern','minecraft:glowstone']:
    x,y,z=q
    if y not in [12,21,30,38,46,54,62]:continue
    if not states.support_cube(self.b.s.blocks.get((x,y+1,z),'minecraft:air')):continue
    surround=sum(states.support_cube(self.b.s.blocks.get((x+dx,y,z+dz),'minecraft:air')) for dx,dz in [(1,0),(-1,0),(0,1),(0,-1)])
    if surround<2:
     self.b.s.blocks.pop(q);self.b.s.owners.pop(q,None);self.put(x,y+1,z,v,'lighting4.recessed_slab');self.recess.append({'from':q,'to':[x,y+1,z]})
  self.p['ceiling_lighting_policy']={'revision':'V0.3.3','floor_count':7,'functional_rooms_on':'all','full_cube_fixture':'flush','upper_floor_levels':'preserved','modern_separator_blocks':2,'exceptions':['stair shafts: existing slab recess','outdoor bridge and passage: existing soffit recess','facade shadow reveal preserves glass connections'],'warm_cool':'material appearance; vanilla propagation is not colored'}
 def route_dist(self,x,z,line):
  ds=[]
  for (ax,az),(bx,bz) in zip(line,line[1:]):
   vx,vz=bx-ax,bz-az;t=max(0,min(1,((x-ax)*vx+(z-az)*vz)/(vx*vx+vz*vz)));ds.append(((x-ax-t*vx)**2+(z-az-t*vz)**2)**.5)
  return min(ds)
 def landscape(self):
  for q,o in list(self.b.s.owners.items()):
   if o.startswith(('garden.','lighting3.garden.')) or o=='lighting3.entry_path' or (60<=q[0]<140 and 58<=q[2]<116 and o in ['site.planter','site.planting']):self.b.s.blocks.pop(q,None);self.b.s.owners.pop(q,None)
  self.pathdefs=[{'id':'main','points':[[64,56],[68,65],[81,80],[81,112]],'half_width':3.5},{'id':'east','points':[[124,56],[124,112]],'half_width':3},{'id':'park','points':[[108,56],[108,82],[116,92],[124,100]],'half_width':3},{'id':'cross','points':[[64,110],[136,110]],'half_width':3},{'id':'pond_walk','points':[[81,90],[89,87],[107,87],[116,92]],'half_width':2.5}]
  self.region={(x,z) for x in range(60,140) for z in range(58,116)}
  self.walk=set();plant=set();pond=set();deck=set()
  for x,z in self.region:
   path=any(self.route_dist(x,z,p['points'])<=p['half_width'] for p in self.pathdefs)
   plaza=((x-81)/10)**2+((z-78)/9)**2<=1
   inpond=((x-100)/11)**2+((z-99)/6)**2<=1 and not path
   indeck=88<=x<102 and 64<=z<75 and not path
   inplant=((x-66)/6)**2+((z-88)/17)**2<1 or ((x-72)/7)**2+((z-103)/5)**2<1 or ((x-132)/6)**2+((z-87)/19)**2<1 or ((x-98)/10)**2+((z-61)/3)**2<1 or ((x-115)/4)**2+((z-73)/11)**2<1
   if path or plaza:self.walk.add((x,z));mat='smooth_quartz' if plaza else 'polished_andesite'
   elif inpond:pond.add((x,z));mat='water'
   elif indeck:deck.add((x,z));mat='oak_planks'
   elif inplant:plant.add((x,z));mat='moss_block'
   else:mat='smooth_stone'
   if any((x,y,z) in self.b.s.blocks for y in [4,5]):continue
   self.put(x,3,z,M('water',level=0) if mat=='water' else mat,'landscape4.'+('water' if mat=='water' else 'paving'))
   if mat=='water':self.put(x,2,z,'polished_andesite','landscape4.pond_base');self.water.append([x,3,z])
  # One-block dry retaining edge outside water; level with forecourt, no huge box.
  for x,z in pond:
   for dx,dz in [(1,0),(-1,0),(0,1),(0,-1)]:
    q=x+dx,z+dz
    if q not in pond and q in self.region and q not in self.walk:self.put(q[0],3,q[1],'polished_andesite','landscape4.pond_edge')
  # Bamboo is clustered in staggered groups, varying height, all rooted at grade.
  for x,z in sorted(plant):
   n=int(hashlib.sha256(f'landscape4:{x}:{z}'.encode()).hexdigest()[:8],16)
   if x<72 and x%3==0 and (z+x//3)%4==0 and 73<=z<=102:
    h=5+n%5
    for dy in range(h):self.put(x,4+dy,z,M('bamboo',age=1,leaves='large' if dy>=h-2 else 'small' if dy==h-3 else 'none',stage=1),'landscape4.bamboo')
    self.stems.append({'base':[x,4,z],'height':h})
   elif n%15==0:self.put(x,4,z,'oxeye_daisy','landscape4.flowers')
   elif n%7==0:self.put(x,4,z,M('azalea_leaves',persistent=True,distance=1),'landscape4.shrub')
  for x,z,h in [(72,101,7),(132,73,7),(133,99,8)]:
   if (x,z) in self.walk:continue
   self.put(x,3,z,'moss_block','landscape4.tree_ground')
   for y in range(4,4+h):self.put(x,y,z,M('oak_log',axis='y'),'landscape4.tree_trunk')
   for dx in range(-4,5):
    for dz in range(-4,5):
     for dy in range(-2,3):
      if (dx/4)**2+(dz/3.5)**2+(dy/2.5)**2<=1 and (dx or dz or dy>=0):self.put(x+dx,4+h+dy,z+dz,M('oak_leaves',persistent=True,distance=1),'landscape4.tree_canopy')
   self.trees.append({'base':[x,4,z],'height':h})
  # L-shaped seating around the open plaza; facing paths and pond.
  self.benches=[]
  for x0,z0,w,dep in [(86,82,9,2),(89,105,14,2),(128,84,2,8),(61,98,2,7),(88,65,11,2)]:
   for x in range(x0,x0+w):
    for z in range(z0,z0+dep):
     if (x,z) in self.walk or (x,z) in pond:continue
     for y in [4,5,6]:
      if self.b.s.owners.get((x,y,z),'').startswith('landscape4.'):self.b.s.blocks.pop((x,y,z),None);self.b.s.owners.pop((x,y,z),None)
     self.put(x,4,z,M('oak_slab',type='top'),'landscape4.bench')
   self.benches.append([x0,z0,w,dep])
  # Light pergola on wood terrace. Posts never occupy a through-route.
  for x in [88,101]:
   for z in [64,74]:
    for y in range(4,12):self.put(x,y,z,'dark_oak_planks','landscape4.pergola_post')
  for x in range(88,102):
   for z in [64,74]:self.put(x,11,z,'dark_oak_planks','landscape4.pergola_beam')
  for x in range(88,102,2):
   for z in range(64,75):self.put(x,12,z,M('dark_oak_slab',type='bottom'),'landscape4.pergola_slats')
  for x in [91,97]:self.put(x,10,64,M('end_rod',facing='down'),'lighting4.pergola_rod')
  # All landscape lamps are flush paving or slim rods; no three-block bollards.
  self.pathlights=[]
  for x,z in [(64,62),(72,70),(77,82),(77,91),(77,101),(82,111),(93,110),(105,110),(116,110),(121,63),(121,74),(121,85),(121,100),(108,66),(108,78),(112,86),(89,87),(101,87)]:
   if (x,z) in self.water:continue
   if (x,4,z) in self.b.s.blocks:continue
   self.put(x,3,z,'glowstone','lighting4.path_inset');self.pathlights.append([x,3,z])
  # Shore accents sit in retaining floor, never unsupported in flowing water.
  for x,z in [(90,99),(100,94),(109,99)]:
   if (x,z) in pond:self.put(x,2,z,'sea_lantern','lighting4.pond_base')
 def build(self):
  self.ceiling();self.landscape()
  self.ad['ceiling_landscape_revision']={'baseline':BASE,'revision':'V0.3.3','ceiling_cells':self.ceil,'recessed_slab_fixtures':self.recess,'paths':self.pathdefs,'path_cells':[list(q) for q in sorted(self.walk)],'landscape_bounds_xz':[60,58,140,116],'bamboo_stems':self.stems,'trees':self.trees,'benches':self.benches,'water':self.water,'path_lights':self.pathlights,'video_evidence':'titles, authors, description/chapter metadata read; playback and storyboard image access failed; no frame-level or complete viewing claim','garden_design':'new modern forecourt design inspired by stated garden/pond subjects, not a copied video plan','game_status':'pending'}
  return self.b
if __name__=='__main__':
 ap=argparse.ArgumentParser();ap.add_argument('--run',required=True);args=ap.parse_args();a=CeilingLandscape();b=a.build();out=save_run(C,args.run,a.p,b,Path(__file__),{'baseline_run':BASE,'route':'flush_ceiling_full_landscape','game_status':'pending'});dump(out/'adaptation.json',a.ad);print('ceiling cells',len(a.ceil),'recessed lamps',len(a.recess),'bamboo',len(a.stems),'water',len(a.water))
