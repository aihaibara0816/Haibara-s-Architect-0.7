"""Guangzhou South V1, image/drawing-authored HAF 0.2 case adapter.
Not automatic reconstruction, surveyed BIM, or a working railway simulation.
X entrance-to-entrance; Z track direction. Bounds half-open.
"""
from pathlib import Path
import argparse,json,math,sys
import numpy as np
ROOT=Path(__file__).resolve().parents[3]
sys.path[:0]=[str(ROOT),str(ROOT/'support')]
from hafusion.classical import Builder,M
from hafusion.case_io import save_run,dump
from hafusion.lighting import room_lighting
CASE=Path(__file__).resolve().parents[1]
def build(p):
 b=Builder(p['size_xyz'],p['seed']);W,H,D=p['size_xyz'];g=p['ground_y'];cx,cz=p['center_xz'];ry=p['rail_y'];py=p['platform_y'];fy=p['departure_y'];x0,z0,x1,z1=p['hall_bounds_xz'];edges=p['roof_bay_edges_x'];sk=p['skylight'];t=p['track_layout']
 rec={k:[] for k in ['tracks','platforms','columns','lamps','roof_sections','stairs','entries','roof_samples','clearance','seats','synthetic_trains']};bx=b.box;put=b.put
 def lamp(x,y,z,o,m='sea_lantern'):
  q=tuple(map(int,(x,y,z)));put(*q,m,o);rec['lamps'].append({'xyz':q,'material':m,'component_id':o})
 def beam(a,c,m,o,r=0):
  for dx in range(-r,r+1):
   for dz in range(-r,r+1):b.line((a[0]+dx,a[1],a[2]+dz),(c[0]+dx,c[1],c[2]+dz),m,o)
 def column(x,z,y0,y1,o,width=2):
  if y1<=y0:return
  bx((x,y0,z),(x+width,y1,z+width),'smooth_quartz',o);rec['columns'].append({'xyz':[x,y0,z],'width':width,'top_y':y1,'component_id':o})
 def shell(x,z,h,o,mat='smooth_stone'):
  half=round(h*2)/2;yy=math.floor(half)
  if half%1:
   put(x,yy,z,M(mat+'_slab'),o);put(x,yy-1,z,M(mat+'_slab',type='top'),o+'.underskin')
  else:put(x,yy-1,z,mat,o)
  return yy
 def spine_width(x):
  if x<110:return sk['halfwidth_end']*math.sqrt(max(0,1-((110-x)/(110-sk['xmin']))**2))
  if x>510:return sk['halfwidth_end']*math.sqrt(max(0,1-((x-510)/(sk['xmax']-510))**2))
  return sk['halfwidth_center']+(sk['halfwidth_end']-sk['halfwidth_center'])*min(1,abs((x-cx)/200))**1.6
 def main_h(i,x):
  u=(x-edges[i])/(edges[i+1]-edges[i]);return p['roof_main_edge_y']+p['roof_main_rise']*math.sin(math.pi*max(0,min(1,u)))
 def wing_h(i,x,z,side):
  lo,hi=edges[i],edges[i+1];u=(x-lo)/(hi-lo);end=p['roof_north_ends_z'][i] if side=='north' else p['roof_south_ends_z'][i];inner=z0-4 if side=='north' else z1+4
  q=min(1,max(0,abs(z-inner)/abs(end-inner)));a,c=p['roof_outer_edge_y'];return a+(c-a)*q+p['roof_main_rise']*math.sin(math.pi*max(0,min(1,u)))
 bx((0,g,0),(W,g+1,D),'grass_block','site.ground');bx((x0,g,z0),(x1,g+1,z1),'smooth_stone','arrivals.floor')
 # Bounded plaza interpretation; proposed masterplan is not treated as as-built.
 for side,lo,hi in [('west',8,112),('east',510,632)]:
  bx((lo,g,204),(hi,g+1,456),'smooth_stone','site.'+side+'.plaza')
  for z in range(214,451,16):bx((lo,g,z),(hi,g+1,z+1),'polished_andesite','site.'+side+'.paving_joint')
  for xx in range(lo+10,hi-8,18):bx((xx,g,204),(xx+1,g+1,456),'polished_andesite','site.'+side+'.paving_joint')
  for za,zb in [(216,292),(368,444)]:
   for xa in range(lo+10,hi-12,27):
    bx((xa,g,za),(min(xa+15,hi-5),g+1,zb),'grass_block','site.'+side+'.garden')
    for zz in range(za+10,zb-4,20):
     b.tree(xa+7,zz,g+1,h=10,r=4);bx((xa+2,g+1,zz+5),(xa+9,g+2,zz+6),M('smooth_stone_slab'),'site.'+side+'.bench')
  for zz in [218,266,314,362,410,442]:
   for xx in [lo+4,hi-6]:b.lamp(xx,zz,g+1)
 track_x=[]
 for k in range(t['pairs']):
  pc=t['start_x']+k*t['pair_pitch']
  for off in t['track_centers_offset']:
   xx=pc+off;track_x.append(xx);tid=f'rail.track{len(track_x):02}'
   bx((xx-3,ry-1,10),(xx+4,ry,650),'polished_andesite',tid+'.ballast')
   for z in range(11,650,3):bx((xx-2,ry,z),(xx+3,ry+1,z+1),M('dark_oak_trapdoor'),tid+'.sleepers')
   for dx in [-1,1]:bx((xx+dx,ry,10),(xx+dx+1,ry+1,650),M('chain',axis='z'),tid+'.decorative_rail')
   rec['tracks'].append({'id':tid,'x':xx,'zrange':[10,650],'rail_y':ry,'functional':False})
 for k in range(t['pairs']+1):
  xx=t['start_x']+k*t['pair_pitch'];hw=3 if k in [0,14] else t['platform_halfwidth'];pid=f'rail.platform{k+1:02}'
  bx((xx-hw,py-1,100),(xx+hw+1,py,560),'smooth_stone',pid+'.deck');bx((xx-hw,py,100),(xx+hw+1,py+1,560),'light_gray_concrete',pid+'.surface')
  for edge in [xx-hw,xx+hw]:bx((edge,py,100),(edge+1,py+1,560),'yellow_terracotta',pid+'.edge_strip')
  for zz in range(58,650,64):
   bx((xx-2,g+1,zz-2),(xx+3,py-1,zz+3),'smooth_stone',pid+'.viaduct_pier');bx((xx-5,py-2,zz-3),(xx+6,py-1,zz+4),'smooth_stone',pid+'.pier_cap')
  rec['platforms'].append({'id':pid,'x':xx,'xrange':[xx-hw,xx+hw+1],'zrange':[100,560],'surface_y':py})
  for zz in [138,186,478,526]:
   column(xx,zz,py+1,py+8,pid+'.fixture_post',1);bx((xx-3,py+8,zz),(xx+4,py+9,zz+1),'blue_concrete',pid+'.sign')
   for dx in [-3,3]:lamp(xx+dx,py+7,zz,pid+'.light')
   bx((xx-2,py+1,zz+6),(xx+3,py+2,zz+7),M('polished_andesite_stairs',facing='north'),pid+'.bench')
 for xx in range(142,498,52):
  for zz in [252,304,356,408]:
   column(xx-1,zz-1,g+1,8,'arrivals.structure.stem',3);beam((xx,7,zz),(xx-6,12,zz),'smooth_quartz','arrivals.structure.ybranch',1);beam((xx,7,zz),(xx+6,12,zz),'smooth_quartz','arrivals.structure.ybranch',1)
 for zz in [268,330,392]:
  bx((116,11,zz-6),(508,12,zz+7),'light_gray_concrete','arrivals.ceiling.panel')
  for x in range(118,507,3):bx((x,10,zz-5),(x+1,11,zz+6),M('iron_trapdoor',half='top'),'arrivals.ceiling.slats')
  for x in range(124,505,18):lamp(x,10,zz,'lighting.arrivals.fixed')
 bx((x0,fy,z0),(x1,fy+1,z1),'smooth_stone','departure.floor')
 for pr in rec['platforms']:
  xx=pr['x']
  for side,zz,sign in [('north',z0+9,1),('south',z1-10,-1)]:
   for j in range(8):
    z=zz+sign*j*2;yy=py+1+j
    bx((xx-2,fy,z-1),(xx+3,fy+1,z+2),'minecraft:air',pr['id']+'.stairwell')
    bx((xx-2,yy-1,z-1),(xx+3,yy,z+1),'smooth_stone',pr['id']+'.stair_support')
    bx((xx-2,yy,z),(xx+3,yy+1,z+1),M('smooth_quartz_stairs',facing='south' if sign>0 else 'north'),pr['id']+'.stair')
    bx((xx-2,yy,z-sign),(xx+3,yy+1,z-sign+1),M('smooth_quartz_slab'),pr['id']+'.stair_landing')
    for dx in [-3,3]:put(xx+dx,yy+1,z,'glass_pane',pr['id']+'.stair_guard')
   topz=zz+sign*16;bx((xx-2,fy,topz-1),(xx+3,fy+1,topz+2),'smooth_stone',pr['id']+'.upper_landing');rec['stairs'].append({'platform_id':pr['id'],'x':xx,'side':side,'bottom_y':py+1,'top_y':fy,'z_start':zz,'z_sign':sign})
 for zz in [z0,z1-1]:
  bx((x0,fy+1,zz),(x1,42,zz+1),p['glazing_material'],'facade.hall.end.glazing')
  for xx in range(x0,x1,6):bx((xx,fy+1,zz-1),(xx+1,43,zz),'iron_bars','facade.hall.end.mullion')
  for yy in [fy+6,fy+12,41]:bx((x0,yy,zz-1),(x1,yy+1,zz),M('iron_trapdoor',half='top'),'facade.hall.end.transom')
 for i in range(6):
  lo,hi=edges[i],edges[i+1];mid=(lo+hi)/2;bid=f'roof.bay{i+1}'
  for x in range(lo,hi):
   mh=main_h(i,x);sw=spine_width(x)
   for z in range(z0-2,z1+2):
    if abs(z-cz)<=sw:continue
    if abs(x-mid)<1.5 and z0+14<z<z1-14:put(x,math.floor(mh)-1,z,'white_stained_glass',bid+'.ridge_glazing')
    else:shell(x,z,mh,bid+'.main_shell')
    if (z-z0)%4==0 and abs(x-mid)>2:put(x,math.floor(mh)-2,z,M('iron_trapdoor',half='top'),bid+'.soffit_slats')
   for side in ['north','south']:
    outer=p['roof_north_ends_z'][i] if side=='north' else p['roof_south_ends_z'][i];inner=z0-4 if side=='north' else z1+4
    inset=round(7*(abs((x-mid)/((hi-lo)/2)))**2);end=outer+inset if side=='north' else outer-inset;za,zb=sorted([end,inner])
    for z in range(za,zb+1):
     h=wing_h(i,x,z,side)
     if abs(x-mid)<1.5 and za+13<z<zb-13:put(x,math.floor(h)-1,z,'white_stained_glass',bid+'.'+side+'.ridge_glazing')
     else:shell(x,z,h,bid+'.'+side+'.shell')
     if z%4==0 and abs(x-mid)>2:put(x,math.floor(h)-2,z,M('iron_trapdoor',half='top'),bid+'.'+side+'.soffit')
    for zz in [end,inner]:put(x,math.floor(wing_h(i,x,zz,side)),zz,M('smooth_quartz_slab'),bid+'.'+side+'.arch_edge')
    zz=z0-3 if side=='north' else z1+2;hh=wing_h(i,x,inner,side)
    bx((x,int(hh),zz),(x+1,int(mh),zz+1),'light_blue_stained_glass_pane',bid+'.'+side+'.clerestory')
    if x%8==0:lamp(x,int(hh)+1,zz+(-1 if side=='north' else 1),'lighting.'+bid+'.clerestory')
   if x%12==0:
    for z in range(z0+7,z1-7):
     if abs(z-cz)>sw and z%3!=0:put(x,math.floor(mh),z,M('iron_trapdoor'),bid+'.standing_seam')
  for side in ['north','south','hall_north','hall_south']:
   ish=side.startswith('hall');north=side in ['north','hall_north'];outer=p['roof_north_ends_z'][i] if north else p['roof_south_ends_z'][i]
   zs=[z0+32,cz-46] if side=='hall_north' else [cz+46,z1-32] if side=='hall_south' else [outer+24,z0-36] if north else [z1+36,outer-24]
   for n,zz in enumerate(zs):
    if not ish and ((north and zz>=z0-8) or (not north and zz<=z1+8)):continue
    rid=bid+'.'+side+f'.truss{n}';ys=[]
    for xx in range(lo,hi+1):
     h=main_h(i,xx) if ish else wing_h(i,xx,zz,'north' if north else 'south');yy=round(h)-2;ys.append((xx,yy,zz));put(xx,yy,zz,'smooth_quartz',rid+'.arch')
    low=min(q[1] for q in ys)-3;beam((lo,low,zz),(hi,low,zz),'iron_bars',rid+'.tie')
    for xx in range(lo,hi,8):
     h=main_h(i,xx+4) if ish else wing_h(i,xx+4,zz,'north' if north else 'south')
     beam((xx,low,zz),(min(xx+4,hi),round(h)-2,zz),'iron_bars',rid+'.web');beam((min(xx+4,hi),round(h)-2,zz),(min(xx+8,hi),low,zz),'iron_bars',rid+'.web')
    for xx in [lo+5,hi-5]:
     pc=min(rec['platforms'],key=lambda r:abs(r['x']-xx))['x'];bottom=fy+1 if ish else py+1
     column(pc-1,zz-1,bottom,low-7,rid+'.support',2);beam((pc,low-7,zz),(xx,low,zz),'smooth_quartz',rid+'.vbranch');beam((pc,low-7,zz),(xx+(-5 if xx<mid else 5),low,zz),'smooth_quartz',rid+'.vbranch')
    for xx in range(lo+7,hi-5,14):lamp(xx,low-1,zz,'lighting.'+rid+'.downlight')
  rec['roof_sections'].append({'id':bid,'xrange':[lo,hi],'span_blocks':hi-lo,'north_end_z':p['roof_north_ends_z'][i],'south_end_z':p['roof_south_ends_z'][i],'main_crown_y':main_h(i,mid),'shell_not_solid':True})
  rec['roof_samples'].append({'xyz':[int(mid)-6,int(main_h(i,int(mid)-6))-1,z0+23],'id':bid+'.main_shell'})
 for side,aa,bb in [('west',102,edges[0]),('east',edges[-1],520)]:
  for x in range(aa,bb):
   u=(edges[0]-x)/(edges[0]-102) if side=='west' else (x-edges[-1])/(520-edges[-1]);h=43+3*u*u
   for z in range(z0-2,z1+2):
    if abs(z-cz)>spine_width(x):shell(x,z,h,'roof.'+side+'.cantilever')
 for x in range(sk['xmin'],sk['xmax']+1):
  hw=spine_width(x)
  if hw<1:continue
  for z in range(math.ceil(cz-hw),math.floor(cz+hw)+1):
   v=(z-cz)/hw;yy=round(sk['rim_y']+sk['rise']*math.sqrt(max(0,1-v*v)));grid=((x+z)%sk['grid_pitch']==0 or (x-z)%sk['grid_pitch']==0)
   put(x,yy,z,'smooth_quartz' if grid else 'white_stained_glass','roof.spine.diagrid' if grid else 'roof.spine.etfe')
  for sign in [-1,1]:
   zz=round(cz+sign*hw);put(x,sk['rim_y'],zz,'smooth_quartz','roof.spine.edge_beam');i=next((i for i in range(6) if edges[i]<=x<edges[i+1]),None);h=main_h(i,x) if i is not None else 43
   bx((x,min(sk['rim_y'],int(h)),zz),(x+1,max(sk['rim_y'],int(h))+1,zz+1),'white_stained_glass','roof.spine.junction_glazing')
 # East drop-off lands on the lower mezzanine, then climbs to the departure floor.
 bx((491,py,z0),(510,py+1,z1),'smooth_stone','interior.east_mezzanine.floor')
 for zz in [286,374]:
  for j in range(8):
   xx=505-j;yy=py+1+j
   bx((xx,yy-1,zz-4),(xx+1,yy,zz+5),'smooth_stone','interior.east_mezzanine.stair_support')
   bx((xx,yy,zz-4),(xx+1,yy+1,zz+5),M('smooth_quartz_stairs',facing='west'),'interior.east_mezzanine.stair')
   bx((xx,fy,zz-4),(xx+1,fy+1,zz+5),'minecraft:air','interior.east_mezzanine.well')
 for side,xx,dy,outward in [('west',112,fy,-1),('east',509,py,1)]:
  eid='entrance.'+side
  for z in range(z0,z1):
   top=43 if abs(z-cz)>31 else 45+round(9*math.sqrt(max(0,1-((z-cz)/32)**2)))
   bx((xx,g+1,z),(xx+1,top,z+1),p['glazing_material'],eid+'.glass')
   if (z-z0)%6==0:bx((xx+outward,g+1,z),(xx+outward+1,top,z+1),'iron_bars',eid+'.mullion')
   for yy in [dy+5,dy+11,fy+5]:
    if yy<top:put(xx+outward,yy,z,M('iron_trapdoor',half='top'),eid+'.transom')
  for zc in [cz-16,cz,cz+16]:
   door_xa,door_xb=sorted([xx,xx+outward])
   bx((door_xa,g+1,zc-3),(door_xb+1,g+6,zc+4),'minecraft:air',eid+'.ground_doorway')
   bx((door_xa,dy+1,zc-3),(door_xb+1,dy+6,zc+4),'minecraft:air',eid+'.doorway');bx((xx-2,dy,zc-4),(xx+3,dy+1,zc+5),'smooth_stone',eid+'.door_threshold');rec['entries'].append({'component_id':eid,'x':xx,'floor_y':dy,'z':zc})
  for zc in [cz-9,cz-3,cz+3,cz+9]:put(xx+outward,dy+10,zc,'gold_block',eid+'.sign_marker')
  for z in range(cz-31,cz+32,10):lamp(xx-outward*4,dy+9,z,'lighting.'+eid+'.lobby')
  for z in range(80,581):
   if 248<=z<=412:roadx=xx+outward*12;yy=dy
   else:
    q=(248-z)/168 if z<248 else (z-412)/168;roadx=xx+outward*(12+12*math.sin(q*math.pi/2));yy=round(dy-(dy-g)*q)
   roadx=round(roadx);yy=max(g,yy);bx((roadx-7,yy,z),(roadx+8,yy+1,z+1),'gray_concrete',eid+'.dropoff_road')
   for xe in [roadx-8,roadx+8]:put(xe,yy+1,z,M('smooth_stone_slab'),eid+'.road_guard')
   if z%8<4:put(roadx,yy,z,'white_concrete',eid+'.lane_marking')
   if z%32==0 and yy>g+2:
    bx((roadx-1,g+1,z-1),(roadx+2,yy,z+2),'smooth_stone',eid+'.road_pier');lamp(roadx+outward*7,yy+4,z,'lighting.'+eid+'.road','glowstone');beam((roadx+outward*7,yy+1,z),(roadx+outward*7,yy+3,z),'iron_bars',eid+'.road_light_post')
  xa,xb=sorted([xx,xx+outward*6]);bx((xa,dy,248),(xb+1,dy+1,413),'smooth_stone',eid+'.forecourt')
 for side,za,zb in [('north',z0+42,cz-30),('south',cz+30,z1-42)]:
  for xx in range(139,485,26):
   for z in range(za,zb,7):
    for dx in [-6,-4,-2,2,4,6]:put(xx+dx,fy+1,z,M('polished_andesite_stairs',facing='north' if side=='north' else 'south'),'interior.seating.'+side);rec['seats'].append([xx+dx,fy+1,z])
 for n,xx in enumerate([151,203,255,359,411,463]):
  for sign in [-1,1]:
   z=cz+sign*25;oid=f'interior.kiosk{n}_{sign}';bx((xx-5,fy+1,z-3),(xx+5,fy+5,z+3),'smooth_quartz',oid+'.body');bx((xx-4,fy+2,z+sign*3),(xx+4,fy+5,z+sign*3+1),'gray_stained_glass_pane',oid+'.display');bx((xx-6,fy+5,z-4),(xx+6,fy+6,z+4),'blue_concrete',oid+'.sign')
   d=room_lighting(p['seed'],'departures',oid,'commercial',p['lighting']['warm_commercial_activity'],namespace=p['lighting']['namespace'])
   if d['lit']:lamp(xx,fy+4,z+sign*3,oid+'.warm_light','glowstone')
   b.rooms.append({'id':oid,'occupancy':d,'actual_lamp':'glowstone' if d['lit'] else None,'fidelity':'synthetic retail pocket'})
 for x in range(130,499,18):
  for sign in [-1,1]:
   z=round(cz+sign*(spine_width(x)-4));h=sk['rim_y']+1;lamp(x,h,z,'lighting.spine.fixed');beam((x,h+1,z),(x,h+4,z),'chain','lighting.spine.hanger')
 for index,zstart in [(3,125),(9,462),(18,105),(25,452)]:
  xx=track_x[index-1];oid=f'context.train{index}';length=92
  for z in range(zstart,zstart+length):
   nose=min(z-zstart,zstart+length-1-z);hw=0 if nose<2 else 1 if nose<5 else 2;bx((xx-hw,ry+1,z),(xx+hw+1,ry+4,z+1),'white_concrete',oid+'.body');put(xx,ry+4,z,M('smooth_quartz_slab'),oid+'.roof')
   if nose>6 and (z-zstart)%23 not in [0,1]:
    for dx in [-2,2]:put(xx+dx,ry+3,z,'black_stained_glass',oid+'.window')
   for dx in [-hw,hw]:put(xx+dx,ry+2,z,'light_blue_stained_glass',oid+'.stripe')
  rec['synthetic_trains'].append({'id':oid,'track':index,'bounds':[xx-2,zstart,xx+3,zstart+length],'functional':False})
 for x in [180,240,300,360,420,480]:rec['clearance'].append({'xyz':[x,fy+2,cz],'kind':'central_concourse'})
 for xx in track_x:rec['clearance'].append({'xyz':[xx,ry+5,cz],'kind':'track_clearance'})
 print('constructed occupied',len(b.s.blocks),flush=True);return b,rec

def main():
 ap=argparse.ArgumentParser();ap.add_argument('--run',required=True);ap.add_argument('--params',type=Path);a=ap.parse_args()
 if Path(a.run).name!=a.run:ap.error('simple new run name required')
 p=json.loads((a.params or CASE/'research/parameters.json').read_text());b,rec=build(p)
 out=save_run(CASE,a.run,p,b,Path(__file__),{'route':'image_and_published_drawings','model_input':None,'scale_blocks_per_metre':p['blocks_per_metre'],'scope':'terminal + bounded plazas + decorative platform/rail scene','user_acceptance':'pending','geometry_is_case_specific':True})
 dump(out/'construction_records.json',rec)
if __name__=='__main__':main()
