from pathlib import Path
import json,html
P=Path(__file__).resolve().parents[1];A=json.loads((P/'research/input_analysis.json').read_text());out=P/'research'
style='<style>text{font-family:Arial,"Noto Sans CJK SC",sans-serif;fill:#183d50;font-size:17px}.small{font-size:13px}.title{font-size:25px;font-weight:bold}.dim{stroke:#297e9b;stroke-width:1.5;fill:none} .ref{stroke:#9aaeb7;stroke-dasharray:5 4;fill:none}</style>'
def svg(w,h,parts):return f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}" role="img">'+style+'<rect width="100%" height="100%" fill="#f2f6f5"/>'+''.join(parts)+'</svg>'
def text(x,y,t,cls=''):return f'<text x="{x}" y="{y}" class="{cls}">{html.escape(t)}</text>'
def rect(x,y,w,h,col,stroke='#85979c',opacity=1):return f'<rect x="{x}" y="{y}" width="{w}" height="{h}" fill="{col}" stroke="{stroke}" opacity="{opacity}"/>'
parts=[text(34,42,'样本截面 · first_floor.nbt','title'),text(34,69,'Z=50，轨道轴 X=144；Y 以轨道所在方块底面为 0','small')];s=next(s for s in A[1]['sections'] if s['track'][2]==144);sc=49;x0=425;y0=390
cols={'quartz_block':'#e4e3dc','smooth_stone':'#a4aca8','cobblestone_slab':'#7d8985'}
for key,v in s['points'].items():
 x,y=map(int,key.split(','));n=v['Name'].split(':')[-1]
 if -6<=x<=5 and -2<=y<=2 and n in cols:
  h=.5 if n.endswith('slab') else 1;parts.append(rect(x0+(x-.5)*sc,y0-(y+h)*sc,sc,h*sc,cols[n]))
# Official measured rail rendering envelope, full-width tie shown as transverse section.
parts += [rect(x0-1.371875*sc,y0-.10*sc,2.74375*sc,.22*sc,'#847760')]
for z in [-.965625,.965625]:parts.append(rect(x0+(z-.125)*sc,y0-.346484*sc,.25*sc,.266484*sc,'#7d8d93'))
parts += [rect(x0-2.5*sc,y0-6*sc,5*sc,6*sc,'#7cbacb','#2b7595',.16),text(x0-92,126,'车体占格包络：宽 5 格'),text(x0-95,149,'最高设备顶约 +6 格','small')]
# Height marker and platform labels.
parts += [f'<path d="M100 {y0}H740M100 {y0-2*sc}H294" class="ref"/>',text(45,y0-2*sc-13,'站台完成面 +2'),text(45,y0+19,'轨道基准 ±0'),text(47,518,'浅色：石英基层 ｜ 灰色：平滑石 ｜ 边侧半砖：圆石半砖','small'),text(47,543,'枕木外缘约 2.744 格；这是 Create 模型尺寸，不是“1 格宽”的实体铁轨。','small')]
(out/'source_cross_section.svg').write_text(svg(810,570,parts))
# Authored maintenance section: exact proposed geometry, train envelope is a study overlay.
p=[text(32,40,'检修区截面 · 本次设计','title'),text(32,67,'以轨道基准 ±0 计；车体虚线仅作尺度校核，不是已装配的运行列车','small')];sc=47;x0=430;y0=420
# surface, pit and overhead platforms
p += [rect(75,y0,sc*7,3*sc,'#afb9b3'),rect(x0+.5*sc,y0,300,3*sc,'#afb9b3'),rect(x0-.5*sc,y0+2*sc,sc,sc,'#959f98')]
# fix left ground ends at x0-.5sc; separate rectangle uses calculated endpoint
p[2]=rect(75,y0,x0-.5*sc-75,3*sc,'#afb9b3')
for lo in [-4.5,3.5]:
 p.append(rect(x0+lo*sc,y0-5*sc,2*sc,sc,'#bbc4bf'))
 p.append(rect(x0+lo*sc,y0-5*sc,sc*.18,sc,'#d9aa40'))
p += [f'<rect x="{x0-2.5*sc}" y="{y0-6*sc}" width="{5*sc}" height="{6*sc}" fill="#9ac9d5" fill-opacity=".18" stroke="#3b8eaa" stroke-dasharray="7 5"/>']
p.append(rect(x0-1.371875*sc,y0-.1*sc,2.74375*sc,.22*sc,'#847760'))
for z in [-.965625,.965625]:p.append(rect(x0+(z-.125)*sc,y0-.346484*sc,.25*sc,.266484*sc,'#7d8d93'))
def person(cx,feet):
 yy=y0-feet*sc;return f'<g stroke="#264c61" stroke-width="6" fill="none"><circle cx="{cx}" cy="{yy-1.56*sc}" r="{.20*sc}"/><path d="M{cx} {yy-1.34*sc}V{yy-.62*sc}m0 -.45l{-sc*.25} {sc*.35}m{sc*.25} {-sc*.35}l{sc*.25} {sc*.35}M{cx} {yy-.62*sc}l{-sc*.22} {sc*.62}M{cx} {yy-.62*sc}l{sc*.22} {sc*.62}"/></g>'
p += [person(x0,-2),person(x0+4*sc,5),text(38,127,'车顶设备包络 +6'),text(38,187,'高位平台脚面 +5'),text(38,398,'轨道基准 ±0'),text(38,515,'坑内脚面 −2'),text(38,587,'坑净宽 1 格；人员先侧向走出轨道下方，再通过台阶回到地面。','small'),text(38,611,'人物以 1.8 格高度示意；碰撞、作业手感和曲线扫掠仍需游戏确认。','small')]
(out/'maintenance_section.svg').write_text(svg(850,638,p))
# Original three-car envelope from decoded carriage cells; consist spacing from entity positions.
p=[text(30,38,'编组核对 · 两端驾驶车辆 + 一节中间车厢','title')];x=45;scale=10
for length,name,cab in [(23,'端车 A',True),(22,'中间车厢',False),(23,'端车 B',True)]:
 p.append(rect(x,100,length*scale,62,'#b8d6df' if cab else '#d7e3e4'));p += [text(x+20,126,name),text(x+20,150,f'{length} 格 / 控制器 '+('1' if cab else '0'),'small')];x+=length*scale
p += [text(42,207,'23 + 22 + 23 ≈ 68 格：附件中的车体方块包络，不含运行时摆动裕量。'),rect(45,240,680,16,'#8bbbc5'),rect(45,280,900,16,'#e5c98f'),rect(45,320,1200,16,'#a6c6b8'),text(740,254,'样本约 68 格','small'),text(961,294,'90 格设计校核','small'),text(45,367,'有效检修区 120 格；停站标记提前 12 格，为车头超出停车基准留出余量。')]
(out/'consist.svg').write_text(svg(1300,400,p))
facts={'source_files':[{'file':a['file'],'sha256':a['sha256'],'size':a['size']} for a in A],'measured':{'sample_cab_controls':[1,0,1],'sample_car_lengths':[23,22,23],'sample_consist_envelope_approx':68,'car_cell_width':5,'track_model_sleeper_width':2.74375,'platform_finish_above_track_block_base':2,'normal_adjacent_track_axis_spacing':6,'island_platform_axis_spacing':15},'proposed':{'working_length':120,'design_train_length_envelope':90,'curve_length_target':[50,60],'track_axis_spacing_in_workshops':12,'pit_foot_below_track_base':2,'high_platform_foot_above_track_base':5},'uncertain':['Game physics/collision and placement not run','Original vehicles require Steam n Rails, Copycats and other extra mods; no orphan entities imported','User 256 placement maximum is server-specific; vanilla Create 6.0.10 config source has default32 and upper128; this design curves under60 needs no override']}
(out/'findings.json').write_text(json.dumps(facts,ensure_ascii=False,indent=2))
print('research diagrams and measured/design split saved')
