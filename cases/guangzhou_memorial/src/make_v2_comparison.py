from pathlib import Path
from PIL import Image,ImageDraw,ImageFont
import io,os,json,hashlib
ROOT=Path(__file__).resolve().parents[3];CASE=Path(__file__).resolve().parents[1];OUT=ROOT/'deliverables/guangzhou_memorial_v2'
old=CASE/'review/previews/V1_r03';new=CASE/'review/previews/V2_r02'
font='/root/.local/share/fonts/haf/NotoSansCJKsc-Regular.otf'
im=Image.new('RGB',(2800,2350),'#f3f0e7');d=ImageDraw.Draw(im)
d.text((48,22),'广州中山纪念堂 · V1 → V2',font=ImageFont.truetype(font,56),fill='#153350')
d.text((50,98),'相同尺度与相机；小匾额、门廊承托、八角窗带与屋顶接合',font=ImageFont.truetype(font,30),fill='#526a72')
for col,(folder,label) in enumerate([(old,'V1 · 保留原始缺陷'),(new,'V2 · 本次修订')]):
    d.text((col*1400+45,160),label,font=ImageFont.truetype(font,42),fill='#153350')
    for row,(fid,crop) in enumerate([('entrance',None),('roof',(650,780,1840,1570))]):
        a=Image.open(folder/(fid+'.png')).convert('RGB')
        if crop:a=a.crop(crop)
        a.thumbnail((1370,950));x=col*1400+(1400-a.width)//2;y=235+row*1020+(950-a.height)//2;im.paste(a,(x,y))
d.text((46,2220),'上：匾额缩小，柱础落在连续平台上。下：补齐窗带下部与抱厦转角。',font=ImageFont.truetype(font,32),fill='#153350')
d.text((46,2280),'HAF 0.2 · 实际 NBT 离线预览 · 游戏内导入与碰撞待验证',font=ImageFont.truetype(font,27),fill='#526a72')
buf=io.BytesIO();im.save(buf,format='PNG');blob=buf.getvalue();tmp=OUT/'compare.tmp'
with tmp.open('wb') as f:f.write(blob);f.flush();os.fsync(f.fileno())
tmp.replace(OUT/'Guangzhou_Memorial_V1_V2_Compare.png')
# Camera equality is verified independently of the visual labels.
a={x['camera']['id']:x['camera'] for x in json.loads((old/'render_report.json').read_text())}
b={x['camera']['id']:x['camera'] for x in json.loads((new/'render_report.json').read_text())}
shared=['front','roof','entrance'];assert all(a[k]==b[k] for k in shared)
(CASE/'validation/v2_comparison_cameras.json').write_text(json.dumps({'same_camera':True,'views':shared,'crops_identical':True,'baseline':'V1_r03','revision':'V2_r02'},indent=2))
print('Comparison board and matching-camera check complete')
