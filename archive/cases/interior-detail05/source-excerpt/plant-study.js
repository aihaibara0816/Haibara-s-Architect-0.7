(()=>{
'use strict';
const version='interior-plant-plan-0.1';
const furniture=[
 {id:'sofa',x:1,z:1.5,w:4,d:2,label:'沙发'},
 {id:'table',x:2,z:4.5,w:2.5,d:1.5,label:'低茶几'},
 {id:'cabinet',x:8,z:2.5,w:3,d:1,label:'低柜'},
 {id:'desk',x:8,z:5,w:3,d:1.5,label:'书桌'},
 {id:'side',x:1,z:8,w:1,d:1,label:'边几'}
];
const keepouts=[{id:'main_route',x:5.5,z:0.5,w:2,d:9.5},{id:'desk_approach',x:8,z:6.6,w:3,d:1.4}];
const candidates={
 window:[{x:10.5,z:1,r:.58,h:'高',support:'floor'},{x:9.1,z:.95,r:.3,h:'低',support:'floor'}],
 cabinet:[{x:8.5,z:3,r:.24,h:'低',support:'cabinet'},{x:10.55,z:3,r:.24,h:'低',support:'cabinet'}],
 side:[{x:1.5,z:8.5,r:.26,h:'中',support:'side'}],
 desk:[{x:10.6,z:5.35,r:.23,h:'低',support:'desk'}]
};
function hash(s){let n=2166136261;for(const c of s){n^=c.charCodeAt(0);n=Math.imul(n,16777619);}return n>>>0;}
function rand(seed,key){let n=hash(version+'|'+seed+'|'+key);return()=>{n=(Math.imul(1664525,n)+1013904223)>>>0;return n/4294967296;};}
const pots=['陶色盆','灰陶盆','木套盆'];
const leaves=['细叶','宽叶','疏枝'];
const messages={window:'窗边高低成组，缓和墙角与窗的直线。',cabinet:'小盆位于柜顶端部，呼应窗边主景。',side:'植物与边几一起围合起居角。',desk:'只在书桌端部点缀，保留工作面。'};
function intersects(p,b){return p.x+p.r>b.x&&p.x-p.r<b.x+b.w&&p.z+p.r>b.z&&p.z-p.r<b.z+b.d;}
function legal(p){if(p.x-p.r<0||p.x+p.r>12||p.z-p.r<0||p.z+p.r>10)return false;if(keepouts.some(k=>intersects(p,k)))return false;const support=furniture.find(f=>f.id===p.support);if(support){if(p.x-p.r<support.x||p.x+p.r>support.x+support.w||p.z-p.r<support.z||p.z+p.r>support.z+support.d)return false;}else if(p.support!=='floor')return false;return !furniture.some(f=>f.id!==p.support&&intersects(p,f));}
function build(seed){const plants=[];for(const group of ['window','cabinet','side','desk']){const r=rand(seed,group);let list=candidates[group];if(group==='cabinet')list=[list[Math.floor(r()*list.length)]];if((group==='side'||group==='desk')&&r()<.38)list=[];for(let i=0;i<list.length;i++){const p={...list[i],id:group+'-'+i,group,pot:pots[Math.floor(r()*pots.length)],leaf:leaves[Math.floor(r()*leaves.length)],angle:Math.floor(r()*360),reason:messages[group]};if(!legal(p))continue;if(plants.some(a=>Math.hypot(a.x-p.x,a.z-p.z)<a.r+p.r))continue;plants.push(p);}}
return {case_id:'InteriorDetail05-PlantPlan',version,plant_seed:seed,room_id:'schematic-living-corner',units:'schematic design units; not Minecraft blocks',room:{width:12,depth:10},furniture,keepouts,plants,status:{geometry:'schematic_only',nbt:'not_generated',game:'pending',aesthetic:'pending'},source:'用户反馈、已提供的室内图和 S01 01:49 旧观察；本次无新增视频观看'};}
const X=x=>40+x*40,Z=z=>40+z*40;
function rect(x,z,w,d,fill,extra=''){return `<rect x="${X(x)}" y="${Z(z)}" width="${w*40}" height="${d*40}" fill="${fill}" ${extra}/>`;}
function text(x,z,t,size=13,fill='#526254'){return `<text x="${X(x)}" y="${Z(z)}" fill="${fill}" font-size="${size}" text-anchor="middle">${t}</text>`;}
function scene(plan){let s='<title>起居角平面示意：家具固定，植物按种子变化</title>'+rect(0,0,12,10,'#eee6d5','stroke="#889282" stroke-width="6"')+rect(1,4,4.2,3.3,'#e5d4bc','rx="14"');s+=rect(5.5,.5,2,9.5,'#d9e5e2');s+=rect(8,6.6,3,1.4,'#d9e5e2');s+=text(6.5,8.5,'通道',13);s+=text(9.5,7.5,'使用空间',12);for(const f of furniture){s+=rect(f.x,f.z,f.w,f.d,'#c9b28d','rx="4" stroke="#a48b65" stroke-width="1"');s+=text(f.x+f.w/2,f.z+f.d/2+.1,f.label,13,'#534f43');}s+='<path d="M260 440 L340 440" stroke="#eee6d5" stroke-width="10"/>';s+=text(6.5,10.8,'入口',13);s+='<path d="M360 40 H480" stroke="#abc9cb" stroke-width="9"/>';s+=text(9.5,-.35,'窗',13);
for(const p of plan?.plants||[]){let leaf='';const count=p.leaf==='疏枝'?4:p.leaf==='细叶'?7:5;const rx=p.r*40*(p.leaf==='细叶'?.2:.36),ry=p.r*40*.53;for(let i=0;i<count;i++){leaf+=`<ellipse cx="0" cy="${-p.r*40*.47}" rx="${rx}" ry="${ry}" fill="${i%2?'#8d9e61':'#637d50'}" transform="rotate(${i*360/count})"/>`;}s+=`<g transform="translate(${X(p.x)},${Z(p.z)}) rotate(${p.angle})"><circle r="${p.r*40*.54}" fill="${p.pot==='陶色盆'?'#b8795d':p.pot==='灰陶盆'?'#a3aaa0':'#9b7d52'}"/>${leaf}<circle r="3" fill="#b5c27a"/></g>`;s+=text(p.x,p.z+p.r+.29,p.h,10,'#35533a');}return s;}
let current;function render(){current=build(Number(document.getElementById('plant-seed').value));document.getElementById('plant-base').innerHTML=scene(null);document.getElementById('plant-after').innerHTML=scene(current);document.getElementById('plant-status').textContent=`种子 ${current.plant_seed} · ${current.plants.length} 株 / ${new Set(current.plants.map(p=>p.group)).size} 组 · 家具与通道固定 · 已筛查示意叶冠与平面支撑，真实高度与碰撞待建造验证。`;const groupNames={window:'窗边主景',cabinet:'柜面呼应',side:'起居边几',desk:'书桌端部'};document.getElementById('plant-items').innerHTML=current.plants.map(p=>`<tr><td>${groupNames[p.group]}<small>${p.id}</small></td><td>${p.pot} · ${p.h}<small>${p.leaf}</small></td><td>${p.reason}</td></tr>`).join('');}
document.getElementById('plant-seed').addEventListener('change',render);
document.getElementById('plant-export').addEventListener('click',()=>{const a=document.createElement('a');a.href=URL.createObjectURL(new Blob([JSON.stringify(current,null,2)],{type:'application/json'}));a.download=`InteriorDetail05-plants-${current.plant_seed}.json`;a.click();setTimeout(()=>URL.revokeObjectURL(a.href),1000);});
window.InteriorPlantStudy={build,legal,furniture,keepouts};render();
})();
