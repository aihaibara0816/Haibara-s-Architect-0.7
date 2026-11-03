from pathlib import Path
import json,sys
C=Path(__file__).resolve().parents[1];run=sys.argv[1];sp=json.loads((C/'runs'/run/'site_records.json').read_text());hs={h['id']:h for h in sp['buildings']}
views=[dict(id='overview',eye=[240,160,224],target=[80,6,64],width=1800,height=1400,spanX=220,spanZ=171.111,ortho=True)]
for name,eye,target,span in [('street',[210,100,180],[80,10,62],170),('north_lane',[205,90,130],[78,12,26],154),('shops',[130,49,130],[77,11,49],77),('civic',[70,44,15],[34,9,92],45)]:
 for night in [False,True]:
  v=dict(id=name+('_night' if night else ''),eye=eye,target=target,width=1600,height=1100,spanX=span,spanZ=span*1100/1600,ortho=True,night=night)
  if name=='shops':v['bounds']=[46,36,112,64]
  if name=='north_lane':v['bounds']=[0,0,151,39]
  if name=='civic':v['bounds']=[16,75,50,108]
  views.append(v)
for night in [False,True]:views.append(dict(id='walk'+('_night' if night else ''),eye=[8,7,69],target=[116,10,66],width=1600,height=1000,ortho=False,fov=62,night=night))
# Individual views: explicit bounding crop and actual NBT floor cuts.
for hid,label in [('S01','sweet'),('P01','inn'),('P02','bath'),('H01','H01'),('S05','paper'),('P04','shrine')]:
 h=hs[hid];x,z,w,d,g=[h[k] for k in ['x','z','w','d','g']];cx=x+w/2;cz=z+d/2;south=h['face']=='S'
 view=dict(id=label+'_front',eye=[cx+30,g+20,cz+(48 if south else -48)],target=[cx,g+9,cz],width=1400,height=1100,spanX=max(w,d)*1.7,spanZ=max(w,d)*1.7*1100/1400,ortho=True,bounds=[x-3,z-5,x+w+3,z+d+5]);views.append(view)
 for k in ([0,1] if hid in ['H01','S01','P01'] else [0]):
  fy=g+6*k;views.append(dict(id=label+('_cut' if k==0 else '_upper'),eye=[cx+28,fy+38,cz+(35 if south else -35)],target=[cx,fy+1,cz],width=1400,height=1100,spanX=max(w,d)*1.6,spanZ=max(w,d)*1.6*1100/1400,ortho=True,bounds=[x-1,z-1,x+w+1,z+d+1],minY=fy,cutY=fy+4))
h=hs['S01'];cx=h['x']+h['w']/2;front=h['z']+h['d']-1
views.append(dict(id='eave_detail',eye=[cx+10,h['g']+3,front+15],target=[cx,h['g']+7,front-1],width=1400,height=1000,ortho=False,fov=56,bounds=[h['x']-3,h['z']-2,h['x']+h['w']+3,front+5]))
(C/'cameras.json').write_text(json.dumps(views,indent=2));print('cameras',len(views))
