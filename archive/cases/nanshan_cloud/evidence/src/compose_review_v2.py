"""Exact render contact sheets; image contents are not generated or altered."""
from pathlib import Path
import json,os
from PIL import Image,ImageDraw,ImageFont,PngImagePlugin
CASE=Path(__file__).resolve().parents[1];ROOT=CASE.parents[1]
OUT=ROOT/'deliverables/nanshan_cloud_v2'
FONT=Path(os.environ.get('HAF_CJK_FONT',str(ROOT/'support/fonts/NotoSansCJKsc-Regular.otf')))
def font(n):return ImageFont.truetype(str(FONT),n)
def save(im,path,source):
    info=PngImagePlugin.PngInfo();info.add_text('source_renders',json.dumps(source));im.save(path,pnginfo=info)
def main():
    OUT.mkdir(parents=True,exist_ok=True);prev=CASE/'review/previews/V2_r01'
    for mode,tag in [('day','Day'),('night','Night')]:
        im=Image.new('RGB',(2560,3680),'#f3f6f5');d=ImageDraw.Draw(im)
        d.text((55,25),'南山云科技大厦 V2 · 四个 45° 方向',font=font(50),fill='#153c3e')
        d.text((55,100),'模型坐标：东 +X，北 −Z；地理朝向待核实 · 点击文件可查看大图',font=font(27),fill='#496163')
        sources=[]
        for i,(q,title) in enumerate([('se','东南 SE'),('sw','西南 SW'),('ne','东北 NE'),('nw','西北 NW')]):
            x=40+(i%2)*1260;y=175+(i//2)*1740
            p=prev/(q+'_'+mode+'.png');v=Image.open(p).convert('RGB');v=v.resize((1220,1627),Image.Resampling.LANCZOS)
            d.text((x,y),title+' · '+('日间' if mode=='day' else '夜间'),font=font(35),fill='#153c3e');im.paste(v,(x,y+58));sources.append(str(p.relative_to(ROOT)))
        d.text((55,3635),'最终 NBT 几何预览 · 未加载资源包纹理 · 非游戏截图',font=font(25),fill='#496163')
        save(im,OUT/('Nanshan_Cloud_HAF_V2_Four_Views_'+tag+'.png'),sources)
    im=Image.new('RGB',(2320,2250),'#f3f6f5');d=ImageDraw.Draw(im)
    d.text((55,25),'露台比例修订 · 同相机正面对照',font=font(51),fill='#153c3e')
    d.text((55,105),'最高塔体 235 格不变；收小平台宽度与外挑，上部三行改为等宽',font=font(29),fill='#496163')
    src=[]
    for i,(label,run,note) in enumerate([('V1 · 原版','V1_r04','最大宽度 64 格 / 外挑 8 格'),('V2 · 收窄后','V2_r01','最大宽度 50 格 / 外挑 5 格')]):
        x=40+i*1160;p=CASE/'review/previews'/run/'front.png';v=Image.open(p).convert('RGB');v=v.resize((1080,1872),Image.Resampling.LANCZOS)
        d.text((x,175),label,font=font(39),fill='#153c3e');im.paste(v,(x,245));d.text((x,2140),note,font=font(28),fill='#496163');src.append(str(p.relative_to(ROOT)))
    d.text((55,2203),'宽度、外挑均按玻璃围护计；外侧压边另有 1 格。所有图像来自对应版本 NBT。',font=font(24),fill='#496163')
    save(im,OUT/'Nanshan_Cloud_HAF_V1_V2_Comparison.png',src)
    print('exact four-view sheets and comparison sheet written')
if __name__=='__main__':main()
