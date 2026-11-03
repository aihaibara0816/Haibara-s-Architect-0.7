"""Read final IFC NBT; verify silhouette, ownership and independent replay."""
from pathlib import Path
import sys,json,gzip,collections,argparse,copy,contextlib,io
CASE=Path(__file__).resolve().parents[1];ROOT=CASE.parents[1]
sys.path[:0]=[str(ROOT),str(ROOT/'support'),str(CASE/'src'),str(ROOT/'tools')]
from vendor.inspect_build import load_build,Limits
from hafusion.case_io import dump
from build_case import IFC
from review_case import review_case

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--run',required=True);a=ap.parse_args();run=CASE/'runs'/a.run
    p=json.loads((run/'params_used.json').read_text());b=load_build(run/'building.nbt',Limits(cells=40_000_000,nodes=16_000_000))
    own=json.loads(gzip.decompress((run/'component_ownership.json.gz').read_bytes()));owners={tuple(v[:3]):own['owner_names'][v[3]] for v in own['xyz_owner']}
    checks=[]
    def check(id,ok,**e):checks.append(dict(id=id,status='pass' if ok else 'fail',**e))
    check('ownership_covers_exact_final_blocks',set(owners)==set(b.blocks))
    g=p['frame']['grade_y'];points=[q for q,o in owners.items() if not o.startswith(('site.','podium.'))]
    height=max(q[1] for q in points)+1-g
    check('tower_height_220',height==220,height_blocks=height)
    widths={}
    for y in range(g+10,g+p['tower']['glass_height_blocks']):
        qs=[q for q,o in owners.items() if q[1]==y and o.startswith('facade.glazing.')]
        widths[y]=[max(q[i] for q in qs)-min(q[i] for q in qs)+1 for i in [0,2]]
    max_width=max(w[0] for w in widths.values());base=widths[g+10][0];top=widths[max(widths)][0]
    maxima=[y for y,w in widths.items() if w[0]==max_width];middle=sum(maxima)/len(maxima)-g
    check('spindle_narrows_above_and_below',top<base<max_width,base=base,maximum=max_width,top=top,axes='X, discrete outer glass')
    check('broadest_band_near_lower_third',.23< middle/220 <.43,mean_maximum_height=middle,range=[min(maxima)-g,max(maxima)-g])
    core_y=[q[1] for q,o in owners.items() if o=='interior.office_core']
    check('office_core_stops_below_atrium',max(core_y)<g+p['tower']['hotel_lobby_blocks'],max_core_y=max(core_y))
    diag={o for o in owners.values() if o.startswith('structure.diagrid.')}
    check('opposing_diagrid_families_retained',len(diag)==30,component_count=len(diag))
    mats=collections.Counter(s.split('[')[0] for s in b.blocks.values())
    check('warm_cool_and_thin_blocks_present',all(mats[x]>0 for x in ['minecraft:sea_lantern','minecraft:glowstone','minecraft:gray_stained_glass_pane','minecraft:diorite_wall','minecraft:iron_bars']),counts={x:mats[x] for x in mats if any(k in x for k in ['lantern','glowstone','wall','pane','slab'])})
    with contextlib.redirect_stdout(io.StringIO()):
        same=IFC(p).build();same.finish()
    check('deterministic_replay',same.s.blocks==b.blocks and same.s.size==b.size)
    alt=copy.deepcopy(p);alt['lighting']['room_activity']=.18
    with contextlib.redirect_stdout(io.StringIO()):
        other=IFC(alt).build();other.finish()
    diff={q for q in set(same.s.blocks)|set(other.s.blocks) if same.s.blocks.get(q)!=other.s.blocks.get(q)}
    bad=[q for q in diff if not (same.s.owners.get(q,'').startswith('lighting.room.') or other.s.owners.get(q,'').startswith('lighting.room.'))]
    check('activity_change_only_affects_room_lamps',bool(diff) and not bad,changed_cells=len(diff),non_lamp_changes=len(bad))
    shared=review_case('guangzhou_ifc',a.run);dump(run/'shared_review.json',shared)
    check('declared_final_geometry_samples',shared['geometry_status']=='pass',checks=shared['geometry_checks'])
    check('matched_views_and_true_top',shared['view_metadata_status']=='pass',status_detail=shared['view_metadata_status'])
    report={'case':'guangzhou_ifc','run':a.run,'checks':checks,'status':'pass' if all(c['status']=='pass' for c in checks) else 'fail','game_status':'pending','visual_fidelity':'manual limited inspection; user review pending','scope':'No survey validation or real-world structural safety assessment'}
    dump(run/'validation.json',report);print(json.dumps(report,ensure_ascii=False,indent=2));raise SystemExit(0 if report['status']=='pass' else 1)
if __name__=='__main__':main()
