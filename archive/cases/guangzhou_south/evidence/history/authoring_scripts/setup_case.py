from pathlib import Path
import json,shutil,hashlib
R=Path(__file__).parent/'HAF_Guangzhou_South';C=R/'cases/guangzhou_south'
(C/'review/assets').mkdir(parents=True,exist_ok=True)
src=Path('/workspace/scratch/cfe8adbb046e/zhujiang_v1/HAF_Zhujiang_Dijing/cases/zhujiang_dijing/review/assets/render_shader_reference.html')
shutil.copy2(src,C/'review/assets/render_shader_reference.html')
p={'schema':'haf-case-parameters-1','case':'guangzhou_south','engine':'HAF 0.2.0','adapter':'guangzhou-south-v1','seed':20261024,'size_xyz':[640,64,660],'blocks_per_metre':1.0,'scale_status':'uniform study scale; engineering drawing bay widths used, hidden dimensions estimated','ground_y':2,'rail_y':13,'platform_y':14,'departure_y':22,'center_xz':[310,330],'hall_bounds_xz':[112,234,510,426],'roof_bay_edges_x':[126,171,239,307,375,443,495],'roof_north_ends_z':[100,64,42,54,80,110],'roof_south_ends_z':[560,596,618,606,580,550],'roof_main_edge_y':43,'roof_main_rise':7,'roof_outer_edge_y':[35,25],'skylight':{'xmin':90,'xmax':532,'halfwidth_center':12,'halfwidth_end':32,'rim_y':45,'rise':9,'grid_pitch':6},'track_layout':{'start_x':124,'pair_pitch':26,'pairs':14,'track_centers_offset':[9,17],'platform_halfwidth':5,'zrange':[10,650],'platform_zrange':[100,560],'decorative_only':True},'lighting':{'public_hall_fixed':True,'warm_commercial_activity':0.45,'namespace':'guangzhou-south-v1'},'coordinates':{'x':'model east, entrance-to-entrance transverse direction','y':'up','z':'model south, track direction','actual_geographic_bearing':'not surveyed; working directions follow published elevation labels, no georeferenced transform'},'scope':{'include':['main terminal','six vaulted roof bays','central flared skylight','north/south platform canopies','15 platform bodies / 28 decorative track corridors','ground arrival hall and elevated waiting hall','east/west drop-offs at different levels','bounded plaza landscaping'],'exclude':['basements and metro','full railway throats','TOD towers','functional Create track/rolling stock/control','surveyed interiors']},'uncertainties':['source envelopes differ: sbp 450x400x40m vs drawing 398m axes and longer canopy envelope; not combined into one measured overall box','main roof heights are a study interpretation within the 47–52m maintenance-report range','six unequal bay widths use rounded published design axes, not as-built survey','plaza paving/planting and road curves are approximate','seating/retail/lighting fixture count are procedural supplements','15 platform bodies are retained but individual track spacing is regularized'], 'roof_material':'smooth_stone','structure_material':'smooth_quartz','glazing_material':'light_blue_stained_glass_pane'}
(C/'research/parameters.json').write_text(json.dumps(p,ensure_ascii=False,indent=2))
(R/'agent_config.json').write_text(json.dumps({'engine':'HAF 0.2.0','default_case':'guangzhou_south','control_catalog':'docs/haf_0_2_capabilities.json','cases':{'guangzhou_south':'cases/guangzhou_south/src/build_case.py'}},indent=2))
# Record unchanged dependency hashes before adding the adapter.
files={str(x.relative_to(R)):hashlib.sha256(x.read_bytes()).hexdigest() for sub in ['hafusion','support','tools','tests'] for x in (R/sub).rglob('*') if x.is_file() and '__pycache__' not in str(x)}
(C/'history/dependency_baseline.json').write_text(json.dumps(files,indent=2))
# All cameras target the final readback. Labels refer to model coordinates.
base={'width':2400,'height':1600,'fov':36,'ortho':True,'concept':False,'sun_day':[.65,.9,.7]}
views=[]
def cam(id,eye,target,span,**kw):views.append({**base,'id':id,'eye':eye,'target':target,'spanX':span,'spanZ':span*2/3,**kw})
cam('overview',[1010,490,1120],[320,20,330],850)
cam('night',[1010,490,1120],[320,20,330],850,night=True)
cam('top',[320,1100,330],[320,0,330],690,height=2300,spanZ=661.25)
cam('south_roof',[310,190,1000],[310,27,330],500)
cam('west_entrance',[-200,88,360],[117,28,330],210)
cam('east_entrance',[820,86,360],[505,24,330],210)
cam('entrance_night',[-200,72,350],[117,27,330],190,night=True)
cam('roof_detail',[130,235,100],[237,46,310],220)
cam('platform',[270,42,610],[250,27,480],125)
cam('platform_night',[270,42,610],[250,27,480],125,night=True)
cam('hall',[160,27,330],[420,43,330],100,ortho=False,fov=80)
cam('hall_night',[160,27,330],[420,43,330],100,ortho=False,fov=80,night=True)
cam('soffit',[260,27,270],[274,45,279],80,ortho=False,fov=78)
cam('arrivals',[145,6,325],[460,7,325],85,ortho=False,fov=78)
cam('section',[760,210,850],[320,25,330],600,cutX=312)
cam('platform_plan',[310,950,330],[310,0,330],470,cutY=20)
cam('waiting_plan',[310,950,330],[310,0,330],470,cutY=29)
cam('plaza',[-170,125,530],[56,10,330],250)
(C/'cameras.json').write_text(json.dumps(views,indent=2))
print('case initialized',R)
