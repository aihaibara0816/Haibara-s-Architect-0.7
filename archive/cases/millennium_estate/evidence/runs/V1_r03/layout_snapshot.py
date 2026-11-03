"""Authorized R03: rigid towers in two parallel stepped rows, ten blocks per column.
Landscape paths follow the slope; buildings and apartments are never sheared.
"""
import copy
from hafusion.classical import Builder
from hafusion.design_handoff import compile_handoff
def rearrange(p,b,specs,units,modules,lamps,trees,stairs,entries):
 p=copy.deepcopy(p);old=copy.deepcopy(p['towers']);p['layout_source_towers']=old
 targets={'A1':118,'A2':108,'A3':98,'B1':31,'B2':21,'B3':11};dz={t['id']:targets[t['id']]-t['z'] for t in old}
 for t in p['towers']:t['z']=targets[t['id']]
 p['size_xyz']=[160,86,166];p['layout_intent']='从左至右各退10格；两排平行，中央花园与环路随斜向排列。'
 nb=Builder(p['size_xyz'],p['seed'])
 def gs(x):return 21-round(x/5)
 def delta(owner,x,z):
  root=owner.split('.')[0]
  if root in dz:return dz[root]
  if owner.startswith('garden.pergola'):return gs(112)
  if owner.startswith('garden.play'):return gs(48)
  if owner.startswith('garden.pond'):return gs(52)
  if owner in ['garden.root','garden.trunk','garden.canopy']:
   t=min(trees,key=lambda t:(t['root'][0]-x)**2+(t['root'][2]-z)**2);return gs(t['root'][0])
  if owner=='garden.bench':return gs(min([67,86,93,61],key=lambda n:abs(n-x)))
  return gs(x)
 nb.box((0,0,0),(160,2,166),'dirt','site.foundation');nb.box((0,2,0),(160,3,166),'grass_block','site.lawn')
 for x in range(160):
  for z in range(166):
   if x<5 or x>=155 or z<5 or z>=158:nb.put(x,2,z,'gray_concrete','site.road')
   elif x<9 or x>=151 or z<8 or z>=154:nb.put(x,2,z,'smooth_stone','site.pavement')
 for q,s in b.s.blocks.items():
  own=b.s.owners[q]
  if own.startswith('site.'):continue
  x,y,z=q;nb.put(x,y,z+delta(own,x,z),s,own)
 paths=set()
 def rect(x0,z0,x1,z1):
  paths.update((x,z) for x in range(x0,x1) for z in range(z0,z1))
 def garden_rect(x0,z0,x1,z1):
  paths.update((x,z+gs(x)) for x in range(x0,x1) for z in range(z0,z1))
 garden_rect(9,46,151,50);garden_rect(9,90,151,94);garden_rect(25,68,136,72);garden_rect(101,48,105,92)
 for x in range(22,139):
  for z in range(48,91):
   r=((x+.5-80)/55)**2+((z+.5-70)/19)**2
   if .78<r<1.12:paths.add((x,z+gs(x)))
 # Rigid pergola access joins the sloping middle route.
 rect(115,70+gs(115),120,74+gs(112));rect(50,90+gs(52),55,159)
 rect(5,8,8,155);rect(152,8,155,155)
 for t in p['towers']:
  ex=t['x']+(11 if t['type']=='A' else 20);ez=t['z'] if t['type']=='A' else t['z']+24
  if t['type']=='A':rect(ex-1,90+gs(ex),ex+3,ez)
  else:rect(ex-1,ez+1,ex+3,50+gs(ex))
  rect(ex,ez,ex+2,ez+1)
 for x,z in paths:nb.put(x,2,z,'smooth_sandstone','site.path')
 for x in range(10,150,7):nb.box((x,2,161),(x+3,3,162),'white_concrete','site.marking')
 for x in range(9,151):
  for z in [8,154]:
   if (z==154 and 48<=x<=57) or (x,z) in paths:continue
   nb.put(x,3,z,'iron_bars','site.fence')
 for z in range(9,154):
  for x in [9,150]:
   if (x,z) not in paths:nb.put(x,3,z,'iron_bars','site.fence')
 for x in [48,57]:nb.box((x,3,153),(x+1,8,156),'smooth_sandstone','site.gate.pier')
 nb.box((47,8,152),(59,9,157),'red_terracotta','site.gate.roof')
 def point(a,off):return [a[0],a[1],a[2]+off]
 def bounds(a,off):return [a[0],a[1],a[2]+off,a[3],a[4],a[5]+off]
 units=copy.deepcopy(units);modules=copy.deepcopy(modules);lamps=copy.deepcopy(lamps);trees=copy.deepcopy(trees);stairs=copy.deepcopy(stairs);entries=copy.deepcopy(entries);specs=copy.deepcopy(specs)
 for u in units:u['entry']=point(u['entry'],dz[u['tower']])
 for m in modules:m['bounds_xyz']=bounds(m['bounds_xyz'],dz[m['component_id'].split('.')[0]])
 for l in lamps:
  x,y,z=l['xyz'];l['xyz']=point(l['xyz'],delta(l['owner'],x,z))
 for t in trees:t['root']=point(t['root'],gs(t['root'][0]))
 for s in stairs:s['trace']=[point(q,dz[s['id'].split('.')[0]]) for q in s['trace']]
 for e in entries:
  e['entry']=point(e['entry'],dz[e['id']]);e['core_landing']=point(e['core_landing'],dz[e['id']])
 for s in specs:
  tid=s['project_id'].split('-')[-1];off=dz[tid]
  s['authorized_scope']['editable_regions']=[bounds(a,off) for a in s['authorized_scope']['editable_regions']]
  s['circulation_keepouts']=[bounds(a,off) for a in s['circulation_keepouts']]
  for r in s['rooms']:r['bounds_xyz']=bounds(r['bounds_xyz'],off);r['entrances']=[point(a,off) for a in r['entrances']]
  for m in s['proposed_modules']:m['bounds_xyz']=bounds(m['bounds_xyz'],off)
 nb.rooms=[r for s in specs for r in s['rooms']];nb.windows=copy.deepcopy(b.windows)
 for w in nb.windows:w['center']=point(w['center'],dz[w['id'].split('.')[0]])
 plans=[compile_handoff(s) for s in specs]
 return p,nb,specs,plans,units,modules,lamps,trees,stairs,entries,paths
