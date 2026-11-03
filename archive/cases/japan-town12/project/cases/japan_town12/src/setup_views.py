from pathlib import Path
import json
C=Path(__file__).resolve().parents[1]
views=[dict(id='overview',eye=[264,170,256],target=[88,6,80],width=1800,height=1400,spanX=248,spanZ=192.889,ortho=True)]
for name,eye,target,span in [
 ('street',[53,19,93],[70,11,77],63),
 ('shops',[43,26,64],[55,11,105],73),
 ('civic',[112,33,97],[123,10,51],85),
 ('upper_homes',[72,38,70],[103,16,26],85),
 ('south_homes',[97,29,110],[142,14,131],81),
]:
 for night in [False,True]:views.append(dict(id=name+('_night' if night else ''),eye=eye,target=target,width=1600,height=1100,spanX=span,spanZ=span*1100/1600,ortho=True,night=night))
views.append(dict(id='H01_cut',eye=[52,38,73],target=[25,8,50],width=1400,height=1100,spanX=29,spanZ=22.786,ortho=True,bounds=[15,41,35,59],minY=4,cutY=10))
views.append(dict(id='H01_upper',eye=[52,45,73],target=[25,15,50],width=1400,height=1100,spanX=29,spanZ=22.786,ortho=True,bounds=[15,41,35,59],minY=11,cutY=17))
(C/'cameras.json').write_text(json.dumps(views,indent=2))
