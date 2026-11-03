#!/usr/bin/env python3
"""Package an offline, NBT-backed comparison and its runnable source."""
import sys,json,base64,argparse,zipfile,hashlib,io,html
from pathlib import Path
from PIL import Image,ImageDraw,ImageFont
ROOT=Path(__file__).resolve().parents[1]
VIEWS={'oblique':'整体斜视','front':'正立面','detail':'近景细部','cutaway':'侧向剖切','plan':'俯视剖切','night':'夜景示意'}
def data_url(path,mime='image/png'):
    return 'data:'+mime+';base64,'+base64.b64encode(Path(path).read_bytes()).decode()
def pack_datapack(out,dest):
    names=[]
    with zipfile.ZipFile(dest,'w',zipfile.ZIP_DEFLATED) as z:
        z.writestr('pack.mcmeta',json.dumps({'pack':{'pack_format':48,'description':'HA Detail Lab r02 | manual structure templates | game validation pending'}}))
        for f in sorted((out/'nbt').glob('*.nbt')):
            name=f.stem.lower();z.write(f,'data/ha_detail/structure/'+name+'.nbt');names.append('ha_detail:'+name)
        z.writestr('TEMPLATES.txt','\n'.join(names)+'\n\nManual example: /place template ha_detail:modern_b ~ ~ ~\nNo load/tick functions. Contains explicit air. Use an empty test world.\n')
    return names

TEMPLATE=r'''<!doctype html>
<html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>HA Detail Lab · 建筑细部样板 R02</title>
<style>
:root{--paper:#f5f3ed;--ink:#1c302d;--muted:#687772;--line:#d6dcd3;--accent:#b75c32;--green:#36594d}
*{box-sizing:border-box}html{scroll-behavior:smooth}body{margin:0;background:var(--paper);color:var(--ink);font:15px/1.65 system-ui,-apple-system,"PingFang SC","Microsoft YaHei",sans-serif}button,input,select,textarea{font:inherit}button,a.action{border:1px solid var(--line);background:white;border-radius:7px;padding:8px 12px;color:var(--ink);cursor:pointer;text-decoration:none}button:hover,a.action:hover{border-color:var(--green)}button[aria-pressed=true],button.primary{background:var(--green);color:white;border-color:var(--green)}a{color:var(--green)}header{padding:34px max(24px,calc((100vw - 1480px)/2));background:#1c302d;color:#edf2e7}header .eyebrow{letter-spacing:.15em;color:#bbccb4;font-size:12px}h1{font-size:clamp(28px,3vw,44px);line-height:1.2;margin:10px 0 14px;font-weight:650}header p{max-width:980px;margin:0;color:#cfdbcf}header nav{display:flex;gap:22px;margin-top:22px}header a{color:#dfe8da;text-decoration:none}main{max-width:1530px;margin:auto;padding:26px}.stats{display:grid;grid-template-columns:repeat(4,1fr);gap:12px;margin-bottom:24px}.stat{padding:15px 20px;background:#e9ede4;border:1px solid var(--line);border-radius:8px}.stat strong{font-size:29px;margin-right:9px}.stat small{display:block;color:var(--muted)}
.lab{display:grid;grid-template-columns:235px minmax(0,1fr);gap:22px}.rail{display:flex;flex-direction:column;gap:9px}.sample{padding:13px;text-align:left;display:flex;gap:10px;line-height:1.4}.sample .num{opacity:.65;font-size:12px;min-width:18px}.sample small{display:block;margin-top:4px;opacity:.8;font-size:11px}.rail aside{font-size:12px;color:var(--muted);padding:12px 4px}
.panel{min-width:0;background:white;border:1px solid var(--line);border-radius:10px;overflow:hidden}.panelhead{padding:22px 23px 14px}.panelhead h2{margin:0 0 8px;font-size:24px}.panelhead p{margin:0;color:var(--muted)}.toolbar{padding:0 23px 15px;display:flex;gap:7px;flex-wrap:wrap}.toolbar button{padding:6px 10px;font-size:13px}
.stage{position:relative;--split:50%;background:#b9c0b2;overflow:hidden}.stage img{display:block;width:100%;height:auto;aspect-ratio:4/3}.stage #b{position:absolute;inset:0;clip-path:inset(0 0 0 var(--split))}.stage .divider{position:absolute;left:var(--split);top:0;bottom:0;width:2px;background:#fcf9e7;box-shadow:0 0 5px #17291e70;pointer-events:none}.badges{position:absolute;top:15px;left:15px;right:15px;display:flex;justify-content:space-between;pointer-events:none}.badge{padding:6px 10px;border-radius:5px;background:#172f29dd;color:#fff;font-size:12px}.badge.b{background:#8f4328e8}.slider{display:flex;align-items:center;gap:12px;padding:13px 23px;border-bottom:1px solid var(--line);font-size:12px;color:var(--muted)}input[type=range]{flex:1;accent-color:var(--green)}.actions{display:flex;gap:8px;flex-wrap:wrap;padding:17px 23px 0}.actions button{font-size:13px}.description{padding:18px 23px 23px;display:grid;grid-template-columns:1fr 1fr;gap:20px}.description h3{font-size:14px;margin:0 0 5px}.description p{margin:0;font-size:13px;color:var(--muted)}.technical{font:12px/1.7 ui-monospace,monospace;word-break:break-all;padding:12px 23px;background:#f2f4ef;color:#54635d}
section.block{background:white;border:1px solid var(--line);border-radius:10px;padding:25px;margin-top:24px}section.block h2{font-size:23px;margin:0 0 12px}section.block p{max-width:1100px}.notice{border-left:3px solid var(--accent);padding:12px 15px;background:#f7eee6;color:#70432e;margin-top:14px}.muted{color:var(--muted);font-size:13px}.layer{display:grid;grid-template-columns:repeat(5,1fr);gap:8px}.layer div{border-top:4px solid var(--green);padding:13px;background:#eef1eb}.layer b{display:block}.layer span{color:var(--muted);font-size:12px}.sources{display:grid;grid-template-columns:repeat(4,1fr);gap:14px}.source{background:#f3f5ef;border-radius:6px;overflow:hidden}.source img{width:100%;aspect-ratio:4/3;object-fit:contain;background:#cad0c1}.source .body{padding:12px}.source h3{font-size:15px;margin:0 0 8px}.source p{font-size:12px;margin:0}.source code{font-size:10px;word-break:break-all;color:var(--muted)}details{border-top:1px solid var(--line);margin-top:16px;padding-top:14px}summary{cursor:pointer;font-weight:600}
table{width:100%;border-collapse:collapse;font-size:13px}th,td{text-align:left;vertical-align:top;border-bottom:1px solid var(--line);padding:11px}th{background:#edf1e8}pre{overflow:auto;background:#edf1e8;padding:12px;border-radius:4px;white-space:pre-wrap;word-break:break-word}form{display:grid;grid-template-columns:1fr 1fr;gap:14px}label{font-size:13px}label input,label select,label textarea{display:block;margin-top:5px;width:100%;padding:9px;border:1px solid #bfc9bd;border-radius:5px;background:#fff}textarea{min-height:110px;resize:vertical}.wide{grid-column:1/-1}.feedback-actions{display:flex;gap:10px;align-items:center;flex-wrap:wrap}.status{color:var(--green);font-size:12px}.checkgrid{display:grid;grid-template-columns:1fr 1fr;gap:20px}.checkgrid h3{font-size:16px}.checkgrid li{margin:7px 0}.plain{padding-left:19px}dialog{width:min(96vw,1510px);max-height:95vh;border:0;border-radius:9px;padding:15px;background:var(--paper)}dialog::backdrop{background:#10251ee6}dialog header{padding:0;background:none;color:var(--ink);display:flex;justify-content:space-between;align-items:center;margin-bottom:10px}dialog img{display:block;width:100%;max-width:1400px;height:auto;margin:auto}footer{padding:28px 0;color:var(--muted);font-size:12px}
@media(max-width:950px){.lab{grid-template-columns:1fr}.rail{display:grid;grid-template-columns:repeat(4,1fr)}.rail aside{display:none}.sample{padding:10px;font-size:12px}.sample small{display:none}.sources{grid-template-columns:repeat(2,1fr)}.layer{grid-template-columns:1fr 1fr}.description{grid-template-columns:1fr}.stats{grid-template-columns:1fr 1fr}}
@media(max-width:560px){main{padding:13px}header{padding:24px 18px}.rail{grid-template-columns:1fr 1fr}.stats{gap:7px}.stat{padding:10px}.stat strong{font-size:23px}.panelhead,.toolbar{padding-left:14px;padding-right:14px}.checkgrid,form{grid-template-columns:1fr}.sources{grid-template-columns:1fr}.layer{grid-template-columns:1fr}.badge{font-size:10px}section.block{padding:17px}}
</style></head><body>
<header><div class="eyebrow">GAFAcraft / ARCHITECTURAL DETAIL STUDIES / 2026.10.23</div><h1>从建筑外壳，走向构件与空间</h1><p>八组细部样板，把七份 schem 与两段幕墙教程中的层次关系落成真实 NBT。现代、中式、砖石、天线与场地分别检验；统一机位，让细部差别可看、可查、可回改。</p>
<nav><a href="#lab">样板对比</a><a href="#sources">七份案例</a><a href="#evaluation">验证与缺口</a><a href="#feedback">记录反馈</a></nav></header>
<main><div class="stats"><div class="stat"><strong>08</strong>组样板<small>16 份对照 NBT + 1 个展场</small></div><div class="stat"><strong>96</strong>张预览<small>每组两版 × 六个视角</small></div><div class="stat"><strong id="tests"></strong>项测试<small>代码与文件检查已通过</small></div><div class="stat"><strong>待测</strong>游戏内<small>导入、更新、碰撞、资源包和照明</small></div></div>
<div class="lab" id="lab"><div class="rail" id="samples"><aside>对照 A：将建筑细构件整块化。<br>细节 B：真实方块状态。<br><br>两版保持相同已占用格位与机位。A 不是旧 HA0.3 的重新运行结果，也不是精度评分。</aside></div>
<div class="panel"><div class="panelhead"><h2 id="sampleTitle"></h2><p id="focus"></p></div><div class="toolbar" id="views"></div>
<div class="stage" id="stage"><img id="a" alt="A 整块化对照"><img id="b" alt="B 有状态细部"><div class="divider"></div><div class="badges"><span class="badge">A · 建筑细部整块化</span><span class="badge b">B · 有状态细部</span></div></div>
<div class="slider"><span>A</span><input id="split" type="range" min="0" max="100" value="50" aria-label="拖动比较 A 与 B"><span>B</span><button id="reset">居中</button></div>
<div class="actions"><button id="zoomA">放大 A</button><button id="zoomB">放大 B</button><button id="downloadA">下载 A · NBT</button><button id="downloadB" class="primary">下载 B · NBT</button><button id="materials">B 材料 CSV</button><button id="feedbackJump">记录这一组反馈</button></div>
<div class="description"><div><h3>本组看什么</h3><p id="look"></p></div><div><h3>边界与待补</h3><p id="limits"></p></div></div><div class="technical" id="meta"></div></div></div>

<section class="block"><h2>前后层次，写成构件关系</h2><p>现代幕墙样板的局部关系如下。层数由建筑和构件决定，不是固定套一个层数模板。七份是学习案例的数量，也不构成参考图片数量限制。</p>
<div class="layer"><div><b>外侧细肋</b><span>铁栏，Z = 4<br>与玻璃分开占格</span></div><div><b>玻璃围护</b><span>玻璃片，Z = 5<br>连接状态在拼合后求解</span></div><div><b>窗后净空</b><span>Z = 6 起<br>保留真实空气格</span></div><div><b>内部示意</b><span>楼板、桌椅、顶灯<br>吊顶与结构层分开</span></div><div><b>内侧背景</b><span>Z = 15<br>参与明暗和进深</span></div></div>
<p class="muted">坐标来自 modern 样板；各类构件并非都覆盖整面。它是局部示意办公室，尚未提供完整出入口、楼梯和疏散路线。</p>
<div class="notice">所有图片来自实际 NBT 回读后的近似状态几何。它们不是游戏截图；无资源包纹理，玻璃、链条和夜景光照都有简化。局部剖切按格边截取后重新建网格，能看见新暴露的楼板和墙面。</div></section>

<section class="block" id="sources"><h2>七份案例 → 本轮样板</h2><p class="muted">以下小图是原 schem 的已有分析预览。原文件保留，学习来源与新样板分开记录；不能把这些学习材料算作未见建筑的验证集。</p><div class="sources" id="sourceCards"></div>
<details><summary>视频、官方资料与可追溯规则</summary><div id="external"></div><div id="rules"></div></details></section>

<section class="block" id="evaluation"><h2>当前已经证明什么，还没有证明什么</h2><div class="checkgrid"><div><h3>已经检查</h3><ul class="plain" id="verified"></ul></div><div><h3>仍需验收</h3><ul class="plain"><li>游戏导入后有没有丢失或重算的状态，旋转后的节点是否正确。</li><li>铁栏、玻璃片、楼梯的实际外观、碰撞，以及资源包差异。</li><li>内饰净高、可进入性、上下交通与真实灯光。</li><li>未参与学习的新建筑还原度；中式屋面尤其缺足够案例。</li></ul></div></div>
<table><thead><tr><th>下一步</th><th>样本</th><th>达标条件</th></tr></thead><tbody><tr><td>先在游戏里验收</td><td>现代幕墙 / 天线 / 花坛</td><td>正确载入；方向、连接、薄厚、光照逐项对照；保存同机位截图。</td></tr><tr><td>补节点和内部空间</td><td>幕墙转角、楼板端头、一间可进入房间</td><td>没有误封与悬空连接；门洞和净高可用；不把伪内饰叫完整内饰。</td></tr><tr><td>跨建筑验证</td><td>新选现代玻璃、砖石、中式各一例</td><td>关键构件有多视角证据，冻结尺度与机位，按轮廓/分格/深度/留空/节点评审。</td></tr><tr><td>再接入 HA</td><td>状态词表与组件适配层</td><td>保留旧完整方块入口及 NBT writer；大幅改工作流前单列范围确认。</td></tr></tbody></table>
<p class="muted">本轮形成可复用样板代码与十条学习记录，未做模型权重训练，未安装新 Skill，也未替换正式 HA 引擎。阶段能力可进入补测；不能据此宣布任意建筑的自动理解与还原已经完成。</p>
<details><summary>工程文件、材料与导入</summary><p>完整工程包含运行代码、配置、13 项测试、构件 ID sidecar、每份 NBT 的完整状态材料表、原始资产哈希及运行记录。</p>
<button id="gallery">下载 B 合并展场 · NBT</button> <button id="pack">下载 Java 1.21.1 数据包</button> <button id="validation">下载验证记录</button>
<p class="muted">数据包只包含结构模板，无自动执行函数。示例：/place template ha_detail:modern_b ~ ~ ~。尚未实测入游戏。NBT 有显式空气，应使用空白测试区域；单样板尺寸小于 48³，合并展场为 168 × 40 × 68，受导入工具能力限制。CSV 数量是放置的方块格数，不是完整合成配方预算。</p><pre id="materialsPreview"></pre></details></section>

<section class="block" id="feedback"><h2>留下能直接用于修改的反馈</h2><p class="muted">切换样板会保留各自草稿。导出的 JSON 包含当前 run、NBT 哈希、视角和问题位置；不会自动发送或修改工程。把反馈文件交回后，再按记录逐项迭代。</p>
<form id="feedbackForm"><label>样板<input id="fbSample" readonly></label><label>视角<select id="fbView"></select></label><label>部位 / 构件 ID<input id="fbPart" placeholder="例如 facade.bay1、吊顶、天线四脚"></label><label>处理建议<select id="fbDecision"><option>待讨论</option><option>保留 B</option><option>部分保留 A</option><option>重做局部</option><option>需要更多参考</option></select></label><label class="wide">看到的问题<textarea id="fbIssue" placeholder="例如：玻璃后退距离仍然太小；这一段不应有封闭楼板。"></textarea></label><label>希望怎样改变<textarea id="fbExpected" placeholder="写清希望保留、减少或重做的部位。"></textarea></label><label>参考来源 / 游戏坐标<textarea id="fbEvidence" placeholder="图片或视频链接、时间点、文件名、游戏版本和坐标。"></textarea></label><div class="wide feedback-actions"><button type="button" class="primary" id="exportFeedback">导出全部反馈 JSON</button><button type="button" id="saveDraft">保存本机草稿</button><span class="status" id="fbStatus" aria-live="polite"></span></div></form></section>
<footer>HA Detail Lab 0.1.0 · __RUN__ · 2026-10-23 · 原 HA0.3 / HAF / V5 与七份输入文件未改。固定状态几何、固定机位；优先检查分层、留空和节点。</footer></main>
<dialog id="zoom"><header><strong id="zoomTitle"></strong><button id="closeZoom">关闭</button></header><img id="zoomImage" alt="放大预览"></dialog>
<script id="payload" type="application/json">__DATA__</script>
<script>
'use strict';
const D=JSON.parse(document.getElementById('payload').textContent), $=id=>document.getElementById(id), views=D.views;
let selected=0,view='oblique',drafts={},canStore=true;
try{drafts=JSON.parse(localStorage.getItem('ha-detail-'+D.run)||'{}')}catch(e){canStore=false}
const clean=v=>String(v).replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
function download(url,name){const a=document.createElement('a');a.href=url;a.download=name;document.body.append(a);a.click();a.remove()}
function jsonDownload(obj,name){const url=URL.createObjectURL(new Blob([JSON.stringify(obj,null,2)],{type:'application/json;charset=utf-8'}));download(url,name);setTimeout(()=>URL.revokeObjectURL(url),1000)}
function save(){const s=D.samples[selected];drafts[s.id]={sample_id:s.id,view:$('fbView').value,part:$('fbPart').value,decision:$('fbDecision').value,issue:$('fbIssue').value,expected:$('fbExpected').value,evidence:$('fbEvidence').value,nbt_sha256_A:s.variants.A.sha256,nbt_sha256_B:s.variants.B.sha256};try{localStorage.setItem('ha-detail-'+D.run,JSON.stringify(drafts));$('fbStatus').textContent='已保存在本机草稿；可导出 JSON。'}catch(e){canStore=false;$('fbStatus').textContent='此环境不允许本机保存，请导出 JSON。'}}
function loadDraft(){const s=D.samples[selected],r=drafts[s.id]||{};$('fbSample').value=s.title;$('fbView').value=r.view||view;$('fbPart').value=r.part||'';$('fbDecision').value=r.decision||'待讨论';$('fbIssue').value=r.issue||'';$('fbExpected').value=r.expected||'';$('fbEvidence').value=r.evidence||'';$('fbStatus').textContent=canStore?'可填写并导出反馈。':'请通过 JSON 导出保留反馈。'}
function setView(v){view=v;render();$('fbView').value=v}
function render(){
 const s=D.samples[selected],a=s.variants.A,b=s.variants.B;
 $('sampleTitle').textContent=s.title;$('focus').textContent=s.focus;$('look').textContent=s.observation;$('limits').textContent=s.limits;
 $('a').src=s.images.A[view];$('b').src=s.images.B[view];$('a').alt=s.title+' / A / '+views[view];$('b').alt=s.title+' / B / '+views[view];
 document.querySelectorAll('.sample').forEach((x,i)=>x.setAttribute('aria-pressed',i===selected));
 document.querySelectorAll('#views button').forEach(x=>x.setAttribute('aria-pressed',x.dataset.view===view));
 $('meta').textContent='尺寸 '+b.size_xyz.join(' × ')+' 格 | 非空气 '+b.non_air_blocks.toLocaleString()+' | 改变状态 '+s.changed_state_cells+' 格 | B 细构件 '+b.partial_cells+' 格 | 构件 ID '+b.components+'\nB NBT SHA256: '+b.sha256;
 $('materialsPreview').textContent=Object.entries(b.base_material_counts).map(([k,n])=>k+' : '+n).join('\n');
}
for(const [i,s] of D.samples.entries()){let b=document.createElement('button');b.className='sample';b.innerHTML='<span class="num">'+String(i+1).padStart(2,'0')+'</span><span>'+clean(s.title.split(' · ')[0])+'<small>'+clean(s.title.split(' · ')[1]||'')+'</small></span>';b.onclick=()=>{save();selected=i;render();loadDraft()};$('samples').insertBefore(b,$('samples').lastElementChild)}
for(const [v,n] of Object.entries(views)){let b=document.createElement('button');b.textContent=n;b.dataset.view=v;b.onclick=()=>setView(v);$('views').append(b);let op=document.createElement('option');op.value=v;op.textContent=n;$('fbView').append(op)}
$('split').oninput=e=>$('stage').style.setProperty('--split',e.target.value+'%');$('reset').onclick=()=>{$('split').value=50;$('stage').style.setProperty('--split','50%')};
for(const tag of ['A','B']){$('zoom'+tag).onclick=()=>{const s=D.samples[selected];$('zoomImage').src=s.images[tag][view];$('zoomTitle').textContent=s.title+' / '+tag+' / '+views[view];$('zoom').showModal()};$('download'+tag).onclick=()=>{const s=D.samples[selected];download(s.downloads[tag],s.id+'_'+tag+'.nbt')}}
$('closeZoom').onclick=()=>$('zoom').close();$('zoom').onclick=e=>{if(e.target===$('zoom'))$('zoom').close()};
$('materials').onclick=()=>{let s=D.samples[selected];download(s.materials,s.id+'_B_materials.csv')};
$('gallery').onclick=()=>download(D.gallery,'detail_gallery_B.nbt');$('pack').onclick=()=>download(D.datapack,'HA_Detail_Lab_Java_1.21.1_datapack.zip');$('validation').onclick=()=>jsonDownload(D.validation,'HA_Detail_Lab_validation.json');
$('tests').textContent=D.validation.unit_tests;
$('verified').innerHTML=['13 项自动测试：序列化回读、确定性、旋转、形状范围、连接及边界案例。','17 份 NBT 已回读；合并展场与八份 B 样板按坐标精确对应。','96 张预览逐张核对文件哈希、源 NBT 哈希与机位。','8 对样板占格位置相同，材料状态真实不同。',D.validation.original_files_unchanged_checked+' 项现有源文件哈希保持不变。'].map(x=>'<li>'+clean(x)+'</li>').join('');
$('sourceCards').innerHTML=D.sources.map(s=>'<article class="source"><img loading="lazy" src="'+s.image+'" alt="'+clean(s.name)+'原案例分析预览"><div class="body"><h3>'+clean(s.name)+'</h3><p>'+clean(s.transfer)+'</p><details><summary>坐标证据与边界</summary><p>'+s.observations.map(clean).join('<br><br>')+'</p><p>'+clean(s.caution)+'</p><code>原文件 SHA256: '+s.source_sha256+'</code></details></div></article>').join('');
$('external').innerHTML='<p>'+Object.entries(D.rules.source_urls).map(([k,u])=>'<a href="'+clean(u)+'" target="_blank" rel="noopener">'+clean(k)+'</a>').join(' · ')+'</p><p class="muted">'+clean(D.rules.video_evidence_limit)+'</p>';
$('rules').innerHTML=D.rules.rules.map(r=>'<details><summary>'+clean(r.id+' · '+r.topic)+'</summary><p>'+clean(r.observed)+'</p><p>本轮应用：'+clean(r.application)+'</p><p>下轮验收：'+clean(r.next_acceptance)+'</p></details>').join('');
$('feedbackJump').onclick=()=>{$('feedback').scrollIntoView();$('fbPart').focus()};
$('feedbackForm').onsubmit=e=>e.preventDefault();$('feedbackForm').addEventListener('change',save);$('saveDraft').onclick=save;
$('exportFeedback').onclick=()=>{save();jsonDownload({schema:'ha-detail-feedback/1',run:D.run,created_at:new Date().toISOString(),feedback:Object.values(drafts).filter(r=>r.issue||r.expected||r.evidence||r.part||r.decision!=='待讨论')},'HA_Detail_Lab_'+D.run+'_feedback.json');$('fbStatus').textContent='已导出。把 JSON 交回后可按构件继续修改。'};
render();loadDraft();
</script></body></html>'''

OBSERVATIONS={
'modern':'看前置竖肋和玻璃之间的距离，再切到剖面找吊顶、桌椅与背景；薄构件不再占满整个格子。',
'millennium':'装饰横带比实际楼板更密；本组有三层示意空间，不能把每条白线都变成完整楼层。',
'western':'窗洞为真实空气，玻璃在厚墙后方。倒楼梯与半砖使窗套、檐口产生厚薄，而不是在墙面画颜色。',
'chinese':'中央开口能望入院内；深灰坡顶和白墙形成层次。木屏片与庭院是本轮推演，不作为传统古建规则。',
'antenna':'高处从四脚逐渐收为单芯；玻璃片在这里是细杆。请放大近景，检查粗杆、细杆、平台与灯标。',
'planter':'花坛土层抬高，边缘使用半砖压顶；座椅、树池、花卉和灯柱各有归属。A/B 花卉外形保持相同。',
'framework':'外围斜杆之外还有核心；只有中部功能楼层有玻璃。上下保持空气，不能默认用幕墙包满。',
'canopy':'砖柱与玻璃棚用两套表达；拱肋在棚内，屋面使用玻璃块，链条与末地烛做吊灯。'}
def montage(manifest,out,dest,font_path):
    labels=[c['title'] for c in manifest['samples']]
    chinese=font_path and Path(font_path).is_file()
    font=ImageFont.truetype(font_path if chinese else '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',32)
    small=ImageFont.truetype(font_path if chinese else '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',21)
    im=Image.new('RGB',(2800,2000),'#f5f3ed');d=ImageDraw.Draw(im)
    d.rectangle((0,0,2800,180),fill='#1c302d')
    d.text((50,34),'HA DETAIL LAB / 08 STUDIES / R02',fill='#f2f3e5',font=font)
    d.text((50,95),'B 版样板总览 · 真实 NBT 的近似状态预览 · 游戏内待验收' if chinese else 'Variant B / NBT-derived state previews / Game validation pending',font=small,fill='#b6c6b0')
    for i,c in enumerate(manifest['samples']):
        x=(i%4)*700;y=205+(i//4)*900
        a=Image.open(out/'previews'/(c['id']+'_B')/'oblique.png');a.thumbnail((690,518));im.paste(a,(x+5,y))
        d.text((x+20,y+536),str(i+1).zfill(2)+'  '+(labels[i].split(' · ')[0] if chinese else c['id']),font=font,fill='#233e34')
        detail=Image.open(out/'previews'/(c['id']+'_B')/'detail.png');detail.thumbnail((350,263));im.paste(detail,(x+20,y+598))
        text='B / '+str(c['variants']['B']['partial_cells'])+' detail cells'
        d.text((x+370,y+620),text,font=small,fill='#687772')
        d.text((x+370,y+660),'A vs B: '+str(c['changed_state_cells']),font=small,fill='#687772')
    im.save(dest)

def main():
    p=argparse.ArgumentParser();p.add_argument('--run',default='r02');p.add_argument('--font');a=p.parse_args();out=ROOT/'runs'/a.run
    manifest=json.loads((out/'manifest.json').read_text());validation=json.loads((out/'validation.json').read_text())
    dest=ROOT/'deliverables';dest.mkdir(exist_ok=True)
    pack=dest/'HA_Detail_Lab_Java_1.21.1_datapack.zip';pack_datapack(out,pack)
    d={'run':a.run,'views':VIEWS,'samples':[],'validation':validation,'sources':[],'rules':json.loads((ROOT/'evidence/learning_rules.json').read_text()),'gallery':data_url(out/'nbt/detail_gallery_B.nbt','application/octet-stream'),'datapack':data_url(pack,'application/zip')}
    for c in manifest['samples']:
        record={**c,'observation':OBSERVATIONS[c['id']],'images':{},'downloads':{},'materials':data_url(out/'nbt'/(c['id']+'_B_materials.csv'),'text/csv')}
        for tag in ['A','B']:
            record['images'][tag]={v:data_url(out/'previews'/(c['id']+'_'+tag)/(v+'.png')) for v in VIEWS}
            record['downloads'][tag]=data_url(out/'nbt'/(c['id']+'_'+tag+'.nbt'),'application/octet-stream')
        d['samples'].append(record)
    for c in json.loads((ROOT/'evidence/source_study.json').read_text())['cases']:
        d['sources'].append({**c,'image':data_url(ROOT/'evidence/reference_previews'/(c['case_id']+'.jpg'),'image/jpeg')})
    page=TEMPLATE.replace('__RUN__',html.escape(a.run)).replace('__DATA__',json.dumps(d,ensure_ascii=False).replace('</','<\\/'))
    report=dest/'HA_Detail_Lab_Review.html';report.write_text(page)
    montage(manifest,out,dest/'HA_Detail_Lab_Overview.png',a.font)
    snapshot=[]
    for name in ['detail_lab','tools','vendor','assets','configs','tests']:
        for f in sorted((ROOT/name).rglob('*')):
            if f.is_file() and '__pycache__' not in f.parts:snapshot.append({'path':str(f.relative_to(ROOT)),'sha256':hashlib.sha256(f.read_bytes()).hexdigest()})
    (out/'source_snapshot.json').write_text(json.dumps(snapshot,indent=2))
    bundle=dest/'HA_Detail_Lab_0.1.0_r02_Source_and_NBT.zip'
    with zipfile.ZipFile(bundle,'w',zipfile.ZIP_DEFLATED,compresslevel=6) as z:
        for name in ['detail_lab','tools','vendor','assets','configs','evidence','tests']:
            for f in sorted((ROOT/name).rglob('*')):
                if f.is_file() and '__pycache__' not in f.parts:z.write(f,'HA_Detail_Lab/'+str(f.relative_to(ROOT)))
        z.write(ROOT/'README.md','HA_Detail_Lab/README.md')
        for f in sorted(out.rglob('*')):
            if not f.is_file() or f.suffix=='.bin' or '__' in f.parent.name or 'scene' in f.parts or 'contact_' in f.name:continue
            if any('__' in s for s in f.relative_to(out).parts):continue
            z.write(f,'HA_Detail_Lab/'+str(f.relative_to(ROOT)))
        for f in [report,pack]:z.write(f,'HA_Detail_Lab/deliverables/'+f.name)
    inventory=[{'file':f.name,'bytes':f.stat().st_size,'sha256':hashlib.sha256(f.read_bytes()).hexdigest()} for f in [report,bundle,pack,dest/'HA_Detail_Lab_Overview.png']]
    (dest/'delivery_inventory.json').write_text(json.dumps(inventory,indent=2));print(json.dumps(inventory,indent=2))
if __name__=='__main__':main()

