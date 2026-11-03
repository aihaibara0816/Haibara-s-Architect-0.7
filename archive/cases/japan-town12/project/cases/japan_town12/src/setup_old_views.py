from pathlib import Path
import json
C=Path(__file__).resolve().parents[1]
views=[dict(id='overview',eye=[240,160,224],target=[80,6,64],width=1800,height=1400,spanX=220,spanZ=171.111,ortho=True)]
for name,eye,target,span in [
 ('street',[210,145,180],[80,9,65],170),
 ('shops',[98,35,130],[63,12,47],36),
 ('civic',[154,47,128],[117,10,48],62),
 ('upper_homes',[70,35,130],[32,12,51],58),
 ('south_homes',[110,47,-20],[90,11,88],85),
 ('tea_house',[-8,33,5],[26,12,89],41),
]:
 for night in [False,True]:views.append(dict(id=name+('_night' if night else ''),eye=eye,target=target,width=1600,height=1100,spanX=span,spanZ=span*1100/1600,ortho=True,night=night))
for v in views:
 key=v['id'].removesuffix('_night')
 if key in ['shops','upper_homes','civic']:v['bounds']={'shops':[52,33,74,69],'upper_homes':[8,32,51.9,72],'civic':[94,29,143,69.9]}[key]
 if key in ['tea_house','south_homes']:v['bounds']={'tea_house':[13,71,40,105],'south_homes':[41,68,139,101.9]}[key]
for night in [False,True]:views.append(dict(id='walk'+('_night' if night else ''),eye=[6,9,68],target=[100,12,66],width=1600,height=1000,ortho=False,fov=62,night=night))
views.append(dict(id='H01_cut',eye=[46,35,82],target=[19,7,51],width=1400,height=1100,spanX=31,spanZ=24.357,ortho=True,bounds=[11,39,28,62],minY=4,cutY=9))
views.append(dict(id='H01_upper',eye=[46,42,82],target=[19,13,51],width=1400,height=1100,spanX=31,spanZ=24.357,ortho=True,bounds=[11,39,28,62],minY=10,cutY=15))
(C/'cameras.json').write_text(json.dumps(views,indent=2))
