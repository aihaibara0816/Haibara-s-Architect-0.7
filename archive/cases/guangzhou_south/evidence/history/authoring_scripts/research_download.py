from pathlib import Path
import re,urllib.request,urllib.parse,html,json,hashlib,concurrent.futures
from PIL import Image,ImageDraw
CASE=Path(__file__).parent/'HAF_Guangzhou_South/cases/guangzhou_south';R=CASE/'research'; items=[]
def add(i,u,p,role):items.append({'image_id':i,'url':html.unescape(u),'source_page':p,'role':role})
def get(u):return urllib.request.urlopen(urllib.request.Request(u,headers={'User-Agent':'Mozilla/5.0'}),timeout=30).read()
f='https://farrells.com/project/guangzhou-south-railway-station/'
s=(R/'pages/farrells.html').read_text()
urls=list(dict.fromkeys(re.findall(r'https?[^\s"\'<>]+?\.(?:jpg|png)',s)))
for n,u in enumerate([x for x in urls if re.search(r'Guangzhou-South-Railway-Station-\d\d.jpg$',x)],1):add('F%02d'%n,u,f,'architect_photo')
a='https://www.archdaily.com/267849/guangzhou-south-railway-station-tfp-farrells'
s=(R/'pages/archdaily.html').read_text();links=list(dict.fromkeys(re.findall(r"href='([^']+/503c[^']+)'",s)))
def gallery(k,u):
 try:
  u=urllib.parse.urljoin(a,u);raw=get(u);(R/'pages'/f'drawing{k}.html').write_bytes(raw);t=raw.decode(errors='replace')
  allu=list(dict.fromkeys(re.findall(r'https://images.adsttc.com/[^\s"\'<>]+',t)))
  good=[x for x in allu if 'large_jpg' in x or '/original/' in x]
  return k,u,(good or [x for x in allu if 'medium_jpg' in x])[0]
 except Exception as e:return k,u,str(e)
for k,p,u in concurrent.futures.ThreadPoolExecutor(4).map(lambda kv:gallery(*kv),enumerate(links,1)):
 if u.startswith('http'):add('D%02d'%k,u,p,'design_drawing')
 else:print('DRAWING_FAIL',k,u,flush=True)
for i,end in enumerate(['2324_1437_a_MAX.jpg.pagespeed.ce.ueh2IdQYp_.jpg','2324_1437_c_MAX.jpg.pagespeed.ce.6z81LaoRHY.jpg'],1):add('S%02d'%i,'https://www.sbp.de/app/uploads/2021/12/'+end,'https://www.sbp.de/en/project/guangzhou-south-railway-station/','engineer_photo')
add('A01','https://img3.winshang.com/Upload/member/header/2021/5/1/132643433272459421.jpg','https://m.winshang.com/news684460.html','aerial_photo')
add('N01','https://n.sinaimg.cn/spider20221130/285/w1200h685/20221130/4403-9424904a63100da89e82b91752046b2c.jpg','https://finance.sina.cn/2022-11-30/detail-imqqsmrp8121832.d.html','night_aerial')
add('N02','https://imagepphcloud.thepaper.cn/pph/image/162/671/941.jpg','https://m.thepaper.cn/baijiahao_15266147','night_entrance')
add('N03','https://upload.wikimedia.org/wikipedia/commons/b/b5/Guangzhou_South_Railway_Station_platform_at_night.jpg','https://commons.wikimedia.org/wiki/File:Guangzhou_South_Railway_Station_platform_at_night.jpg','night_platform')
u='https://huacheng.gz-cmc.com/pages/2022/04/20/2e8c89aa86f34bc5971944cc2b5ae620.html'
try:
 raw=get(u);(R/'pages/roof_maintenance.html').write_bytes(raw);t=raw.decode(errors='replace')
 us=list(dict.fromkeys(re.findall(r'''(?:src|data-src)=["']([^"']+\.(?:jpg|jpeg|png)(?:\?[^"']*)?)["']''',t,re.I)))
 for k,x in enumerate(us,1):add('R%02d'%k,urllib.parse.urljoin(u,x),u,'roof_maintenance')
except Exception as e:print('maintenance page',str(e))
def download(x):
 try:
  raw=get(x['url']);fp=R/'images'/(x['image_id']+'.jpg');fp.write_bytes(raw)
  with Image.open(fp) as im:im.load();sz=im.size;fmt=im.format
  x.update(local_file='images/'+fp.name,sha256=hashlib.sha256(raw).hexdigest(),size_bytes=len(raw),pixels=sz,format=fmt,status='downloaded_not_yet_viewed',license='unknown',training_authorized=False)
 except Exception as e:x.update(status='failed',error=str(e))
 print(x['image_id'],x['status'],x.get('pixels'),flush=True);return x
items=list(concurrent.futures.ThreadPoolExecutor(5).map(download,items))
(R/'downloads.json').write_text(json.dumps(items,ensure_ascii=False,indent=2))
valid=[x for x in items if x['status'].startswith('downloaded')]
for part in range(0,len(valid),9):
 group=valid[part:part+9];out=Image.new('RGB',(1800,410*((len(group)+2)//3)),'#e7e9ea');d=ImageDraw.Draw(out)
 for i,x in enumerate(group):
  im=Image.open(R/x['local_file']).convert('RGB');im.thumbnail((590,370));xx=(i%3)*600;yy=(i//3)*410;out.paste(im,(xx,yy+30));d.text((xx+10,yy+7),x['image_id']+' '+x['role'],fill='black')
 out.save(R/f'contact{part//9+1}.jpg')
print('DONE',len(valid),len(items))
