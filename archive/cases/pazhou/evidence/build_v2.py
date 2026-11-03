"""Explicit Pazhou V2 adapter. Photos are interpreted upstream, not read by this code.

Uniform inherited scale. Named components preserve evidence bindings; dimensions
without surveys are research estimates. Interiors are synthetic view-back alcoves.
Existing HAF 0.3 geometry/state/export code is used without modification.
"""
from pathlib import Path
import argparse, json, math, sys, hashlib
ROOT=Path(__file__).resolve().parents[2]
sys.path[:0]=[str(ROOT),str(ROOT/'support'),str(ROOT/'support/deps')]
from hafusion.classical import Builder, M
from hafusion.case_io import save_run,dump
from hafusion.lighting import room_lighting,unit

CASE=Path(__file__).resolve().parent

def build(p,run):
    b=Builder(p['size_xyz'],p['seed']);t=p['tower'];d=p['detail'];seed=p['seed']
    x0,x1,z0,z1=t['x0'],t['x1'],t['z0'],t['z1'];top=t['top_exclusive']
    slab=M('smooth_stone_slab',type='top');thin=M('iron_trapdoor',half='top')
    glass=M('light_blue_stained_glass_pane');darkglass=M('gray_stained_glass_pane')
    checkpoints=[]
    def stage(label):
        out=save_run(CASE,run+'_'+label,p,b,Path(__file__),{'stage':label,'fidelity':'research reconstruction; not surveyed','parent_engine':'IFC_V1_Source HAF 0.3'})
        checkpoints.append({'stage':label,'run':out.name,'nbt_sha256':hashlib.sha256((out/'building.nbt').read_bytes()).hexdigest(),'blocks':len(b.s.blocks)})
    def rail(xa,xb,za,zb,y,owner):
        for x in range(xa,xb):
            b.put(x,y,za,glass,owner);b.put(x,y,zb-1,glass,owner)
        for z in range(za+1,zb-1):
            b.put(xa,y,z,glass,owner);b.put(xb-1,y,z,glass,owner)
    def tree(x,z,y,h=3):
        b.box((x,y,z),(x+1,y+h,z+1),'oak_log','landscape.tree.trunk')
        for dx,dz in [(0,0),(-1,0),(1,0),(0,-1),(0,1)]:
            b.put(x+dx,y+h-1,z+dz,'oak_leaves','landscape.tree.leaves',empty=True)
        b.put(x,y+h,z,'oak_leaves','landscape.tree.leaves',empty=True)
    def planar_shell(rect,ya,yb,owner,mat=glass):
        xa,xb,za,zb=rect
        for y in range(ya,yb):
            for x in range(xa,xb):
                b.put(x,y,za,mat,owner+'.glass');b.put(x,y,zb-1,mat,owner+'.glass')
            for z in range(za+1,zb-1):
                b.put(xa,y,z,mat,owner+'.glass');b.put(xb-1,y,z,mat,owner+'.glass')
    def platform_cells(q):
        for x in range(x0,x1):
            for z in range(q['front_z'],z1):
                if q['id']=='T4' and d['upper_slot_x'][0]<=x<d['upper_slot_x'][1] and d['upper_slot_z'][0]<=z<d['upper_slot_z'][1]:continue
                yield x,z
    # 01. Structural relationships and actual empty spaces.
    b.box((0,0,0),(56,1,82),'smooth_stone','site.paving')
    b.box((0,0,29),(56,1,42),'gray_concrete','site.road')
    for x in range(2,54,6):b.box((x,0,35),(x+3,1,36),'white_concrete','site.road.markings')
    for xa,xb,za,zb in [(2,10,3,27),(46,54,3,27),(3,10,47,78),(46,53,48,78),(15,41,73,80)]:
        b.box((xa,0,za),(xb,1,zb),'grass_block','site.lawn')
    for n,(xa,xb) in enumerate([(18,21),(35,38)]):
        b.box((xa,1,57),(xb,94,62),'gray_concrete',f'frame.core{n}')
    for x in [14,23,32,41]:
        for z in ([46,51,56,61,65] if x in [14,41] else [46,65]):
            b.box((x,1,z),(x+1,94,z+1),'smooth_quartz',f'frame.column.{x}.{z}')
    for q in p['platforms']:
        for x,z in platform_cells(q):b.put(x,q['y'],z,slab,'platform.'+q['id']+'.deck')
    for x in range(x0,x1):
        for z in range(z0,z1):
            if not 24<=x<32:b.put(x,top-1,z,M('smooth_stone_slab'),'frame.roof')
    # Podium open layers preserve road clearance.
    pod=p['podium']
    for y in [1,pod['middle_y'],pod['roof_y']]:
        b.box((14,y,10),(42,y+1,26),slab,'podium.deck')
    for x in [14,21,28,35,41]:
        for z in [10,25]:b.box((x,1,z),(x+1,26,z+1),'smooth_quartz','podium.columns')
    for q in p['bridges']:
        b.box((q['x0'],q['y'],26),(q['x1'],q['y']+1,48),slab,'bridges.'+q['id']+'.deck')
    stage('01_frame')
    # 02. Distinct facade planes. Open platform bands are NOT closed by glazing.
    bands=[(7,21),(26,34),(39,56),(61,78),(83,90)]
    floors=[]
    for a,c in bands:
        floors += list(range(a,c,3))
        for side,(xa,xb) in enumerate([(x0,24),(32,x1)]):
            own=f'facade.wing{side}.{a}'
            planar_shell((xa,xb,z0,z1),a,c,own)
            # Pale outer glass is a material approximation, not blue reflection made solid.
            for y in range(a,c):
                for z in range(z0+1,z1-1):
                    b.put(xa if side==0 else xb-1,y,z,M('white_stained_glass_pane'),own+'.outer_glass')
            for fy in range(a,c,3):
                b.box((xa+1,fy,z0+1),(xb-1,fy+1,z1-1),slab,own+'.floor_recessed')
                # Shallow ledges, not thick solid bands replacing the glass.
                for x in range(xa,xb):b.put(x,fy,z0-1,thin,own+'.horizontal_ledge')
                for z in range(z0,z1):
                    b.put(xa-1 if side==0 else xb,fy,z,thin,own+'.outer_ledge')
            # Thin vertical glass fins on outer walls, preserved window behind.
            for z in range(z0+2,z1-1,3):
                for y in range(a,c):b.put(xa-1 if side==0 else xb,y,z,M('white_stained_glass_pane'),own+'.fin',empty=True)
    for side,(xa,xb) in enumerate([(x0,24),(32,x1)]):planar_shell((xa,xb,z0,z1),2,7,'lobby.'+str(side))
    # The sectional zig-zag is an explicit terraced approximation of a sloping sheet.
    sections=p['canyon']['sections_y_z']
    for (ya,za),(yb,zb) in zip(sections,sections[1:]):
        for y in range(ya,yb):
            zz=math.floor(za+(zb-za)*(y-ya)/(yb-ya)+.5)
            for x in range(24,32):b.put(x,y,zz,darkglass,'canyon.inclined_sheet')
            # Raking side interfaces around the actual void. No opaque blue infill.
            for xx in [24,31]:
                for z in range(z0,zz):
                    if not any(q['y']<y<q['y']+q['open_above']+1 for q in p['platforms']):
                        b.put(xx,y,z,glass,'canyon.side_sheet')
            if (y-ya)%3==0:
                for x in range(24,32):b.put(x,y,zz-1,thin,'canyon.transom')
    for q in p['platforms'][:-1]:
        b.box((26,q['y']+1,46),(30,q['y']+2,60),slab,'canyon.walkway')
    # Podium low shop skin, open taller garden frame, rear pavilion.
    planar_shell((15,41,11,25),2,9,'podium.shops')
    planar_shell((16,25,18,25),11,25,'podium.rear_pavilion',darkglass)
    planar_shell((31,40,19,25),12,23,'podium.rear_pavilion',darkglass)
    b.box((16,25,18),(26,26,25),slab,'podium.rear_pavilion.roof')
    # Distinct upper bridge glazed truss sides and narrow lower bridge railings.
    for q in p['bridges']:
        rail(q['x0'],q['x1'],26,48,q['y']+1,'bridges.'+q['id']+'.rail')
        if q['id']=='B2':
            for x in [q['x0'],q['x1']-1]:
                for z in range(26,48):
                    for y in range(23,25):b.put(x,y,z,darkglass,'bridges.B2.glass')
                for z in range(26,45,4):b.line((x,22,z),(x,24,z+3),'iron_bars','bridges.B2.truss')
    stage('02_envelope')
    # 03. Sub-grid states and evidence-bound detail rules.
    for q in p['platforms']:
        own='soffit.'+q['id'];y=q['y'];front=q['front_z'];pitch=d['soffit_grid_pitch']
        for x,z in platform_cells(q):
            if z>=z0:continue
            # Two orthogonal families leave actual voids between thin plates.
            if (x-x0)%pitch==0 or (z-front)%pitch==0:
                b.put(x,y-1,z,thin,own+'.grid')
            if x0+1<x<x1-2 and front+1<z<z0-1 and unit(seed,q['id'],x,z,namespace='pazhou-soffit')<d['soffit_light_density']:
                b.put(x,y-1,z,M('end_rod',facing='east'),own+'.star_light')
        rail(x0,x1,front,z1,y+1,'platform.'+q['id']+'.rail')
        if q['id']=='T4':
            # Guard the aperture; keep the central hole physically clear.
            xa,xb=d['upper_slot_x'];za,zb=d['upper_slot_z']
            for z in range(za,zb):
                b.put(xa-1,y+1,z,glass,'platform.T4.aperture_rail');b.put(xb,y+1,z,glass,'platform.T4.aperture_rail')
            continue
        for xa,zz in [(16,front+2),(36,front+2)]:
            b.box((xa,y+1,zz),(xa+4,y+2,zz+2),'moss_block','landscape.'+q['id']+'.planter')
        tree(18,front+3,y+2,2)
        # Small pavilions vary by level; footprints inferred, not measured rooms.
        xa,xb=(16,22) if q['id']!='T2' else (34,40);za=max(front+3,42)
        planar_shell((xa,xb,za,za+5),y+1,y+4,'pavilion.'+q['id'],darkglass)
        b.box((xa-1,y+4,za-1),(xb+1,y+5,za+6),M('polished_deepslate_slab'),'pavilion.'+q['id']+'.roof')
    for q in p['bridges']:
        for z in range(27,47,d['bridge_rib_pitch']):
            for x in range(q['x0'],q['x1']):b.put(x,q['y']-1,z,thin,'bridge_ribs.'+q['id'])
        for z in range(28,46,6):
            b.put(q['x0']+1,q['y']-1,z,M('end_rod',facing='east'),'lighting.bridge')
    # Visible rooftop pavilions and restrained planting; avoid filling terrace.
    for xa,xb,za,zb,h in [(16,25,16,24,3),(29,38,18,24,4)]:
        planar_shell((xa,xb,za,zb),27,27+h,'podium.rooftop_pavilion',darkglass)
        for z in range(za-1,zb+1):
            yy=27+h+int((z-za)//4)
            for x in range(xa-1,xb+1):b.put(x,yy,z,M('polished_deepslate_slab'),'podium.rooftop_pavilion.roof')
    for x,z,y in [(17,13,27),(38,13,27),(29,13,27),(17,13,11),(37,14,11)]:tree(x,z,y,3)
    for x,z in [(6,8),(6,21),(49,8),(49,21),(6,52),(7,68),(49,52),(49,69),(20,76),(37,76)]:tree(x,z,1,3)
    # Restricted scenic interior alcoves behind front/side glass. No surveyed plan.
    for fy in floors:
        for side,(xa,xb) in enumerate([(15,23),(33,41)]):
            for bay,xx in enumerate(range(xa+1,xb-1,3)):
                rid=f'office.{side}.{fy}.{bay}';rr=room_lighting(seed,str(fy),rid,'office',d['room_activity'],namespace='pazhou-v2')
                b.box((xx-1,fy+1,51),(xx+2,fy+3,52),'light_gray_concrete','interior.'+rid+'.back')
                b.put(xx,fy+1,49,M('dark_oak_slab'),'interior.'+rid+'.desk',empty=True)
                placed=False
                if rr['lit']:placed=b.put(xx,fy+2,50,M('end_rod',facing='east'),'interior.'+rid+'.lamp',empty=True)
                b.rooms.append({'id':rid,'floor_y':fy,'synthetic':True,'real_plan':False,'occupancy':rr,'actual_lamp':'end_rod' if placed else None})
                b.windows.append({'id':rid,'anchor':[xx,fy+1,46],'glass_layer_z':46,'slab_front_z':47,'back_z':51,'evidence':'synthetic alcove; image-008 supports nonuniform occupancy only'})
    # Site lights are small separate fixtures, no continuous glowing facade.
    for x,z in [(12,28),(43,28),(12,44),(43,44)]:b.put(x,1,z,M('end_rod'),'lighting.site')
    # Aviation obstruction light positions are not established by current imagery.
    # Deliberately no inferred red light array; record as unverifiable in review.
    stage('03_final')
    dump(CASE/'runs'/(run+'_03_final')/'checkpoints.json',checkpoints)
    return b

if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--run',required=True);ap.add_argument('--params',type=Path,default=CASE/'params.json');a=ap.parse_args()
    if Path(a.run).name!=a.run:ap.error('simple run name required')
    build(json.loads(a.params.read_text()),a.run)
