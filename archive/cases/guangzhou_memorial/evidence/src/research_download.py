"""Download named original research evidence; no cap on research image count."""
from pathlib import Path
import urllib.request,hashlib,json,concurrent.futures
from PIL import Image
CASE=Path(__file__).resolve().parents[1]
PAGE='https://www.yuexiu.gov.cn/zjyx/yxjd/gzjdgms/content/post_8659223.html'
items=[
 ('ref01','https://www.yuexiu.gov.cn/img/0/762/762089/8659223.png',PAGE,'official exterior'),
 ('ref02','https://www.yuexiu.gov.cn/img/0/762/762094/8659223.png',PAGE,'official panorama'),
 ('ref03','https://www.yuexiu.gov.cn/img/0/762/762096/8659223.png',PAGE,'official aerial'),
 ('ref04','https://www.yuexiu.gov.cn/img/0/762/762110/8659223.png',PAGE,'official exterior detail'),
 ('ref05','https://www.yuexiu.gov.cn/img/0/762/762100/8659223.png',PAGE,'official auditorium'),
 ('ref06','https://ak-d.tripcdn.com/images/0100612000jukouas08E6_W_960_0_Q60.webp?proc=source%2Ftrip','https://my.trip.com/travel-guide/attraction/guangzhou/sun-yat-sen-memorial-hall-in-guangzhou-76907?locale=en-MY','night candidate'),
 ('ref07','https://cdn.getyourguide.com/image/format%3Dauto%2Cfit%3Dcontain%2Cgravity%3Dauto%2Cquality%3D60%2Cwidth%3D1440%2Cheight%3D650%2Cdpr%3D1/tour_img/f17afa29fab5147ec853399273518f48ac99e2658b336cbff1a741194ba0dfc4.jpeg','https://www.getyourguide.com/en-au/guangzhou-l184/from-guanzghou-guided-baiyun-mountain-day-tour-by-car-t910506/','aerial alternative'),
 ('ref08','https://ak-d.tripcdn.com/images/1mi2y224x98mq56rp3948_R_600_400_R5_Q90.jpg?proc=source%2Ftrip','https://my.trip.com/moments/detail/guangzhou-152-143104502?locale=en-MY','night alternative'),
 ('ref09','https://ak-d.tripcdn.com/images/1mi5g424x8zgcsk2d7F7B.jpg?proc=source%2Ftrip','https://id.trip.com/moments/detail/guangzhou-152-134335245?locale=en-ID','night front and statue')]
def fetch(item):
 ident,url,page,use=item;row={'image_id':ident,'url':url,'source_page':page,'candidate_use':use,'viewed':False,'licence':'unknown; reference study only'}
 try:
  req=urllib.request.Request(url,headers={'User-Agent':'Mozilla/5.0','Referer':page})
  data=urllib.request.urlopen(req,timeout=25).read();p=CASE/'research/images'/(ident+'.image');p.write_bytes(data)
  with Image.open(p) as im:im.load();row.update(width=im.width,height=im.height,format=im.format)
  ext={'JPEG':'jpg','PNG':'png','WEBP':'webp'}.get(row['format'],'image');dest=p.with_suffix('.'+ext);p.rename(dest)
  row.update(status='downloaded',path=str(dest.relative_to(CASE)),sha256=hashlib.sha256(data).hexdigest())
 except Exception as e:row.update(status='failed',error=str(e))
 return row
if __name__=='__main__':
 with concurrent.futures.ThreadPoolExecutor(max_workers=4) as ex:rows=list(ex.map(fetch,items))
 (CASE/'research/image_manifest.json').write_text(json.dumps(rows,ensure_ascii=False,indent=2))
 for r in rows:print(r['image_id'],r['status'],r.get('width'),r.get('height'),r.get('error',''))
