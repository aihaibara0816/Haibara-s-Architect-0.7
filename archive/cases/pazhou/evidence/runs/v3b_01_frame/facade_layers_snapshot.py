"""Pazhou planar curtain-wall study. Explicit rules, no photo inference.

Only closed bands on the two wings are eligible. Terrace voids and the inclined
canyon remain excluded. Offsets are discrete study adaptations, not measured
construction thicknesses. Colours approximate a Minecraft appearance; they do
not reconstruct physical reflections. No random distribution is used.
"""
from collections import Counter
from hafusion.classical import M
from detail_lab import states

VERSION='pazhou-layered-curtain-0.1'
BANDS=[(7,21),(26,34),(39,56),(61,78),(83,90)]

def faces(t,p):
    x0,x1,z0,z1=t['x0'],t['x1'],t['z0'],t['z1']
    for side,(xa,xb) in enumerate([(x0,24),(32,x1)]):
        for label,z,n,depth in [('front',z0,(0,-1),p['front_back_depth']),('rear',z1-1,(0,1),p['side_back_depth'])]:
            yield {'id':f'{side}.{label}','normal':n,'origin':xa,'coords':[(x,z) for x in range(xa,xb)],'back_depth':depth}
        x=xa if side==0 else xb-1;n=(-1,0) if side==0 else (1,0)
        yield {'id':f'{side}.outer','normal':n,'origin':z0,'coords':[(x,z) for z in range(z0,z1)],'back_depth':p['side_back_depth']}

def apply(b,t,p,mode='layered'):
    if mode not in {'colour','layered'}:raise ValueError(mode)
    for k in ['fin_pitch','colour_bay_width','front_back_depth','side_back_depth']:
        if type(p[k]) is not int or p[k]<1:raise ValueError(k)
    if min(p['front_back_depth'],p['side_back_depth'])<2:raise ValueError('Window cavity must remain')
    mats=[M(s) for s in p['palette_cycle']]
    black=M('black_stained_glass_pane');bar=M('iron_bars');back=M(p['back_material'])
    stats=Counter()
    def place_bar(x,y,z,owner):
        # Do not grow a new arm on a neighbouring bridge/terrace railing.
        # Checking the completed scene is necessary: component-local assembly
        # alone misses these cross-component pane connection changes.
        for dx,dy,dz in states.DIRS.values():
            q=(x+dx,y+dy,z+dz);s=b.s.blocks.get(q)
            if s and states.family(s)=='pane' and not b.s.owners[q].startswith(('facade.wing','facade_layer.')):
                stats['protected_neighbour_bar_omissions']+=1
                return False
        return b.put(x,y,z,bar,owner,empty=True)
    if mode=='layered':
        # Remove the old white glass fin only; preserve all horizontal ledges.
        for q,o in list(b.s.owners.items()):
            if o.startswith('facade.wing') and o.endswith('.fin'):
                b.s.set(q,'minecraft:air','facade_layer.removed_white_fin');stats['old_fins_removed']+=1
    for face in faces(t,p):
        dx,dz=face['normal'];own='facade_layer.'+face['id']
        for a,c in BANDS:
            for x,z in face['coords']:
                u=x if dz else z;local=u-face['origin'];bay=local//p['colour_bay_width']
                for y in range(a,c):
                    q=(x,y,z);existing=b.s.blocks.get(q,'')
                    if 'glass_pane' not in existing:continue
                    floor=(y-a)%3==0
                    # Fixed vertical bay cadence, with dark spandrel rows.
                    mat=black if floor else mats[bay%len(mats)]
                    b.s.set(q,mat,own+'.glass');stats['glazing_assignments']+=1
                    if mode=='colour':continue
                    if local%p['fin_pitch']==0 or local==len(face['coords'])-1:
                        if place_bar(x+dx,y,z+dz,own+'.outer_bar'):stats['bars_added']+=1
                    # A real recessed, opaque layer. Every fourth bay stays open
                    # to retain nonuniform interior depth; no continuous solid fill.
                    if floor or bay%p['back_gap_period']==p['back_gap_period']-1:continue
                    depth=face['back_depth'];qb=(x-dx*depth,y,z-dz*depth)
                    prev=b.s.owners.get(qb,'')
                    if qb not in b.s.blocks or (prev.startswith('interior.') and prev.endswith('.back')):
                        b.s.set(qb,back,own+'.recessed_back');stats['back_assignments']+=1
    if mode=='layered':
        # Close the outward corner between the two perpendicular bar families.
        # Stop at each terrace band; no continuous cage across open floors.
        for xx in [t['x0']-1,t['x1']]:
            for zz in [t['z0']-1,t['z1']]:
                for a,c in BANDS:
                    for y in range(a,c):
                        if (y-a)%3 and place_bar(xx,y,zz,'facade_layer.corner.return'):stats['corner_bars_added']+=1
    return {'rule_version':VERSION,'mode':mode,'operations':dict(stats),'scope':'closed outer wing surfaces only; rear treatment is an unverified extrapolation','game_status':'pending'}
