#!/usr/bin/env python3
"""Vary authored window groups inside approved facade intervals, deterministically."""
import argparse
import hashlib
import json
import math
from pathlib import Path


def rnd(seed, *keys):
    return int.from_bytes(hashlib.sha256(json.dumps([seed, *keys]).encode()).digest()[:8], 'big') / 2**64


def clamp(v, a, b):
    return max(a, min(b, v))


def plan(spec):
    seed=spec.get('seed',20261026);results=[];seen=set()
    for g in sorted(spec['groups'],key=lambda x:x['id']):
        gid=g['id']
        if gid in seen:raise ValueError('duplicate group '+gid)
        seen.add(gid)
        a,b=g['allowed_u_m'];s,e=g['base_u_m'];height=g['floor_height_m']
        if not all(math.isfinite(v) for v in [a,b,s,e,height]):raise ValueError('non-finite geometry')
        if not (a<=s<e<=b and e-s>=.8 and height>=2.4):raise ValueError('invalid group envelope '+gid)
        system=g['system'];base_count=g['count_hint']
        if system not in ['slit','ribbon','glazed','screen']:raise ValueError('unsupported opening system')
        if not isinstance(base_count,int) or base_count<1:raise ValueError('invalid count')
        fixed=g.get('fixed',False)
        scale=1 if fixed else g.get('length_scale',.73+.35*rnd(seed,gid,'length'))
        if not math.isfinite(scale) or scale<=0:raise ValueError('invalid length scale')
        width=clamp((e-s)*scale,min(1.1,b-a),b-a)
        shift=0 if fixed else g.get('shift_m',(rnd(seed,gid,'shift')*2-1)*2.4)
        if not math.isfinite(shift):raise ValueError('invalid shift')
        center=clamp((s+e)/2+shift,a+width/2,b-width/2)
        start=round(center-width/2,4);end=round(center+width/2,4)
        if fixed:count=base_count
        else:count=max(1,base_count+int(rnd(seed,gid,'count')*5)-2)
        capacity=max(1,int(width/(.8 if system=='slit' else 1.25)))
        if fixed and count>capacity:raise ValueError('fixed window count does not fit interval')
        count=min(count,capacity)
        pitch=width/count
        opening_width=min(1.12,pitch*(.47+.17*rnd(seed,gid,'window-width'))) if system=='slit' else pitch-.12
        sill=.28 if system in ['glazed','screen'] else .9+.38*rnd(seed,gid,'sill')
        top=.22 if system in ['glazed','screen'] else .55+.3*rnd(seed,gid,'head')
        openings=[{'id':gid+'-W'+str(i),'u0_m':round(start+i*pitch+(pitch-opening_width)/2,4),
                   'u1_m':round(start+i*pitch+(pitch+opening_width)/2,4),
                   'sill_m':round(sill,4),'head_m':round(height-top,4)} for i in range(count)]
        ledges=[]
        if g.get('allow_ledges',False) and system!='screen':
            probability=g.get('planting_probability',.78)
            if not math.isfinite(probability) or not 0<=probability<=1:raise ValueError('invalid planting probability')
            # Unequal, shifted ledges on every eligible floor, with deliberate gaps.
            n=max(1,min(4,round(width/5)+int(rnd(seed,gid,'ledge-count')*3)-1))
            for i in range(n):
                cell=width/n;length=min(cell*.88,.9+3.8*rnd(seed,gid,i,'ledge-length'))
                left=start+i*cell+(cell-length)*rnd(seed,gid,i,'ledge-offset')
                planted=rnd(seed,gid,i,'planted')<probability
                ledges.append({'id':gid+'-L'+str(i),'u0_m':round(left,4),'u1_m':round(left+length,4),
                               'top_m':round(sill-.05,4),'depth_m':round(.28+.22*rnd(seed,gid,i,'depth'),3),
                               'thickness_m':round(.14+.08*rnd(seed,gid,i,'thickness'),3),
                               'planted':planted,'container_height_m':.28 if planted else 0,
                               'vegetation_variant':int(rnd(seed,gid,i,'foliage')*4),
                               'support_ref':g.get('support_ref'),
                               'status':'proposed_ledge; fixings_and_drainage_pending'})
            if not g.get('support_ref'):raise ValueError('ledge group needs authored support_ref '+gid)
        results.append({**g,'u0_m':start,'u1_m':end,'actual_shift_m':round(center-(s+e)/2,4),
                        'window_count':count,'openings':openings,'ledges':ledges})
    return {'schema':'HAA_opening_groups/0.1','algorithm':'haa-opening-groups/0.1','seed':seed,
            'geometry_authority':'group openings replace previous per-bay window rectangles',
            'groups':results,'status':'proposed_facade_geometry',
            'limits':['allowed intervals must be authored from spatial constraints',
                      'support references are not structural verification',
                      'door, escape, daylight and three-dimensional checks remain separate']}


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('input',type=Path);p.add_argument('--out',required=True,type=Path);a=p.parse_args()
    result=plan(json.loads(a.input.read_text(encoding='utf-8')));a.out.parent.mkdir(parents=True,exist_ok=True)
    a.out.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({'groups':len(result['groups']),'windows':sum(g['window_count'] for g in result['groups']),
                      'ledges':sum(len(g['ledges']) for g in result['groups'])}))
