"""Make the self-contained HAF 0.2 overview from checked project documentation."""
from pathlib import Path
import json,html,re

ROOT=Path(__file__).resolve().parents[1]

def inline(s):
    s=html.escape(s)
    s=re.sub(r'`([^`]+)`',r'<code>\1</code>',s)
    return re.sub(r'\*\*(.*?)\*\*',r'<strong>\1</strong>',s)

def markdown(text):
    out=[];lines=text.splitlines();i=0;n=0
    while i<len(lines):
        s=lines[i]
        if not s.strip():i+=1;continue
        if s.startswith('# '):i+=1;continue
        if s.startswith('## '):
            n+=1;out.append(f'<h2 id="section-{n}"><span>{n:02d}</span>{inline(s[3:])}</h2>');i+=1;continue
        if s.startswith('|'):
            table=[]
            while i<len(lines) and lines[i].startswith('|'):
                row=[v.strip() for v in lines[i].strip().strip('|').split('|')];i+=1
                if all(re.fullmatch(r'[-: ]+',v) for v in row):continue
                table.append(row)
            out.append('<div class="table-wrap"><table><thead><tr>'+''.join('<th>'+inline(v)+'</th>' for v in table[0])+'</tr></thead><tbody>')
            for row in table[1:]:out.append('<tr>'+''.join('<td>'+inline(v)+'</td>' for v in row)+'</tr>')
            out.append('</tbody></table></div>');continue
        if s.startswith('- ') or re.match(r'^\d+\. ',s):
            ordered=not s.startswith('- ');tag='ol' if ordered else 'ul';out.append('<'+tag+'>')
            while i<len(lines) and (re.match(r'^\d+\. ',lines[i]) if ordered else lines[i].startswith('- ')):
                out.append('<li>'+inline(re.sub(r'^(?:\d+\. |- )','',lines[i]))+'</li>');i+=1
            out.append('</'+tag+'>');continue
        paragraph=[]
        while i<len(lines) and lines[i].strip() and not re.match(r'^(#|\||- |\d+\. )',lines[i]):
            paragraph.append(lines[i]);i+=1
        out.append('<p>'+inline(' '.join(paragraph))+'</p>')
    return '\n'.join(out)

def main():
    dest=ROOT/'releases/0.2/deliverables';dest.mkdir(parents=True,exist_ok=True)
    validation=json.loads((ROOT/'releases/0.2/validation.json').read_text())
    catalog=json.loads((ROOT/'docs/haf_0_2_capabilities.json').read_text())
    body=markdown((ROOT/'docs/HAF_0.2.md').read_text())
    cards=[]
    status={'integrated':'已有整栋/代码消费者','sample_only':'局部样板','inherited':'继承研究入口','pending':'未接入'}
    for row in catalog['capabilities']:
        lines=['<details><summary><b class="grade '+row['grade']+'">'+row['grade']+'</b> '+html.escape(row['name'])+' <small>'+status[row['status']]+'</small></summary>']
        lines.append('<p>'+html.escape(row['limits'])+'</p>')
        for key,label in [('controls','当前入口'),('implementation','实现文件'),('consumers','实际消费者'),('evidence','证据')]:
            if row[key]:lines.append('<p><b>'+label+'</b></p><ul>'+''.join('<li><code>'+html.escape(v)+'</code></li>' for v in row[key])+'</ul>')
        lines.append('</details>');cards.append(''.join(lines))
    flow="""<section class="flow" aria-label="HAF 研究与建造工作流">
<div class="wide node"><b>范围、尺度与原版本</b><span>先恢复当前工程与真实输入</span></div>
<div class="branches"><div class="node"><b>不限图数的日夜研究</b><span>主体 · 幕墙 · 屋顶 · 裙楼 · 内部 · 照明</span></div><div class="node optional"><b>可选模型研究</b><span>单位 · 坐标 · 年代 · 构件质量；没有模型仍可继续</span></div></div>
<div class="join">↓　按构件汇总，选择证据与参数　↓</div>
<div class="wide node"><b>构件取舍与关键局部样板</b><span>灯体尺度 / 薄构件前后层 / 家具净空 → 对应真实代码消费者</span></div>
<div class="branches"><div class="node"><b>固定照明和结构</b><span>形态、灯带、塔冠、已核实的障碍灯位</span></div><div class="node"><b>室内与窗灯深化</b><span>稳定房间 ID、功能分区、暗窗、可复现种子</span></div></div>
<div class="join">↓　接入已注册适配器，写入新 run　↓</div>
<div class="wide node strong"><b>HAF 生成 → 最终 NBT 独立回读</b><span>文件 / 几何 / 材料 / 同机位近远景与日夜对照</span></div>
<div class="branches"><div class="node"><b>离线审阅与构件反馈</b><span>指出问题 → 修订参数/代码 → 新 run 复验</span></div><div class="node optional"><b>目标游戏验收 · 待完成</b><span>导入、材质、碰撞、通行、真实夜景与灯体可见性</span></div></div>
</section>"""
    css="""
:root{--ink:#172c33;--muted:#566a70;--line:#dbe4e2;--paper:#fff;--bg:#f1f4f0;--accent:#256b60}
*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--ink);font:16px/1.75 system-ui,-apple-system,"Segoe UI","Noto Sans CJK SC","Microsoft YaHei",sans-serif}
header{background:#193d42;color:#fff;padding:58px max(6vw,24px) 40px}header .inner,main{max-width:1180px;margin:auto}.eyebrow{letter-spacing:.15em;font-size:12px;color:#bbd7d0}
h1{font-size:clamp(32px,5vw,57px);line-height:1.15;margin:17px 0}header p{color:#d8e7e3;max-width:800px;margin:18px 0}.version{border:1px solid #719b93;border-radius:30px;padding:4px 12px;display:inline-block;font-size:13px}
main{padding:28px 24px 70px}nav{display:flex;gap:10px;flex-wrap:wrap;margin-bottom:26px}nav a{color:var(--accent);border-bottom:1px solid var(--accent);text-decoration:none}
.stats{display:grid;grid-template-columns:repeat(4,1fr);gap:14px;margin:0 0 32px}.stats div{background:white;border:1px solid var(--line);border-radius:12px;padding:18px}.stats strong{font-size:30px;color:var(--accent);display:block}.stats span{font-size:13px;color:var(--muted)}
article{background:white;border:1px solid var(--line);border-radius:16px;padding:28px 36px}h2{font-size:23px;line-height:1.4;margin:40px 0 18px;padding-top:12px;border-top:1px solid var(--line)}h2 span{color:#8aa399;font:12px/1 monospace;margin-right:12px}
p{margin:14px 0}li{margin:7px 0}code{font-size:.86em;background:#eef3f1;padding:2px 4px;border-radius:4px;overflow-wrap:anywhere}table{width:100%;border-collapse:collapse;font-size:14px}th{text-align:left;background:#eaf1ed;color:#28554d}th,td{padding:13px 14px;vertical-align:top;border-bottom:1px solid var(--line)}td{min-width:105px;overflow-wrap:anywhere}.table-wrap{overflow-x:auto}
.note{background:#edf4ef;border-left:4px solid #4c8b78;padding:16px 20px;border-radius:5px}.flow{background:#f5f8f5;padding:20px;border:1px solid var(--line);border-radius:12px;margin:25px 0}.node{background:white;border:1px solid #b5cdc5;border-radius:8px;padding:13px 16px}.node b,.node span{display:block}.node span{font-size:13px;color:var(--muted)}.wide{text-align:center}.branches{display:grid;grid-template-columns:1fr 1fr;gap:16px;margin:14px 0}.optional{border-style:dashed}.join{text-align:center;font-size:13px;color:#477168;padding:4px}.strong{background:#e6f2ec;border-color:#519681}
details{border:1px solid var(--line);margin:12px 0;border-radius:8px;padding:12px 16px}summary{cursor:pointer;font-weight:650}summary small{font-weight:400;color:var(--muted);margin-left:9px}.grade{padding:2px 8px;border-radius:5px;background:#edf2f0;color:#356657}.C{background:#fff0d4;color:#836323}.D{background:#f9e7e2;color:#934a3c}
footer{font-size:12px;color:var(--muted);padding:30px 0}.muted{color:var(--muted)}
@media(max-width:680px){main{padding:16px 12px}article{padding:16px}.stats{grid-template-columns:1fr 1fr}.branches{grid-template-columns:1fr}h2{font-size:20px}header{padding:32px 22px}}
@media print{header{padding:20px;background:#fff;color:#193d42}header p{color:#193d42}main{padding:0}nav{display:none}article{border:0;padding:0}details{break-inside:avoid}.table-wrap{overflow:visible}}
"""
    report='<!doctype html><html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>HAF 0.2 · Skill、工作流与成品路线</title><style>'+css+'</style></head><body>'
    report+='<header><div class="inner"><div class="eyebrow">HAIBARA’S ARCHITECT / RELEASE NOTES / 2026.10.23</div><h1>HAF 0.2</h1><span class="version">灯光 · 细节 · 窗后空间</span><p>把已经做出的能力归纳成可复用规则，明确每一项控制的位置、证据和下一步。既保留进展，也保留尚未验证的边界。</p></div></header>'
    report+='<main><nav><a href="#section-2">Skill 清单</a><a href="#workflow">工作流</a><a href="#controls">实际控制</a><a href="#section-6">还缺什么</a></nav>'
    report+='<div class="stats"><div><strong>3</strong><span>已安装项目 Skill<br>另有 1 个工程内 Skill 依赖</span></div><div><strong>2</strong><span>当前注册建筑适配器<br>深圳特区报业大厦 / 广州周大福</span></div><div><strong>23</strong><span>本次核心测试通过<br>不代表游戏或整栋还原达标</span></div><div><strong>'+str(validation['protected_files']['count'])+'</strong><span>受保护文件未变<br>生成逻辑 / 参数 / 历史成果等</span></div></div>'
    report+='<article><div class="note"><b>当前交付定位：</b>可以制作离线建筑审阅版；游戏内最终成品仍需导入验收。HAF 0.2 是工程整理与能力归纳，本次没有重新生成建筑。</div>'
    report+=body.replace('<h2 id="section-4">','<div id="workflow"></div>'+flow+'<h2 id="section-4">')
    report+='<h2 id="controls"><span>附录</span>12 项真实能力与控制位置</h2><p>点开查看参数、源码、消费者和证据。该目录用于核查，不会自动改变建筑。</p>'+''.join(cards)
    report+='<h2 id="validation"><span>记录</span>本次验证范围</h2><p>23 项现有核心测试通过；6 项只读入口/错误参数检查通过；627 个受保护文件哈希一致。两项 Skill 完成结构校验与一次只读前向任务检查。归档解包和最终文件验证记录随源码包提供。</p><p class="muted">程序测试不替代用户视觉反馈。最终 NBT、游戏兼容、碰撞和夜景的状态分别记录；未进游戏始终标 pending。报告为静态离线 HTML，无外部脚本或图片依赖。</p></article><footer>HAF 0.2 · 工程版本 0.2.0 / HA 研究规则 0.2.1 / Architect 编排规则 0.2.2。原始照片版权仍属各权利人。</footer></main></body></html>'
    target=dest/'HAF_0.2_Skills_Workflow.html';target.write_text(report)
    print(target.name,target.stat().st_size)

if __name__=='__main__':main()
