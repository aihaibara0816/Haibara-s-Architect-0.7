"""Read-only review of a preserved run. Missing contracts remain pending."""
from pathlib import Path
import argparse, hashlib, importlib.util, json, sys, subprocess, tempfile
ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT), str(ROOT/'support')]
from vendor.inspect_build import load_build, Limits
from hafusion.review import review_samples, review_views, status


def review_case(case_id, run_id):
    config = json.loads((ROOT/'agent_config.json').read_text())
    if case_id not in config['cases'] or Path(run_id).name != run_id or run_id in ('.','..'):
        raise ValueError('Registered case and simple run name required')
    case = ROOT/'cases'/case_id
    run = case/'runs'/run_id
    nbt = run/'building.nbt'
    digest = hashlib.sha256(nbt.read_bytes()).hexdigest()
    build = load_build(nbt, Limits(cells=64_000_000, nodes=64_000_000))
    checks = []
    adapter = case/'src/review_samples.py'
    if adapter.exists():
        spec = importlib.util.spec_from_file_location('review_'+case_id, adapter)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        checks = review_samples(build.blocks, build.size, mod.contract(run))
    if case_id == 'civic_center' and run_id.startswith(('v03_r14','v03_r15','v03_r16')):
        with tempfile.TemporaryDirectory(prefix='haf-civic-review-') as tmp:
            for name in ['validate_case.py','validate_interior.py','validate_ceiling_landscape.py']:
                report_file=Path(tmp)/(name+'.json')
                proc=subprocess.run([sys.executable,str(case/name),'--run',run_id,'--output',str(report_file)],capture_output=True,text=True,cwd=ROOT)
                if not report_file.exists():
                    checks.append({'name':name,'status':'fail','details':proc.stderr[-2000:]})
                    continue
                result=json.loads(report_file.read_text())
                checks.extend({'name':name+':'+q['name'],'status':'pass' if q['pass'] else 'fail','details':q.get('details')} for q in result['checks'])
    bounds = all(all(0 <= q[i] < build.size[i] for i in range(3)) for q in build.blocks)
    report_path = case/'review/previews'/run_id/'render_report.json'
    rendered = json.loads(report_path.read_text()) if report_path.exists() else []
    views = review_views(rendered, digest)
    return {'case': case_id, 'run': run_id, 'nbt_sha256': digest,
            'size_xyz': build.size, 'nonair': len(build.blocks),
            'file_status': 'pass' if bounds else 'fail',
            'geometry_status': status(checks), 'geometry_checks': checks,
            'view_metadata_status': status(views), 'view_checks': views,
            'visual_fidelity': 'requires_scoped_human_review', 'game_status': 'pending',
            'limits': ['Declared samples only; no automatic image understanding',
                       'View metadata does not establish fidelity or image visibility',
                       'Full cube support and air cells are not Minecraft collision tests',
                       'No contract means pending; earlier case-specific reports remain separate']}


if __name__ == '__main__':
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--case', required=True)
    ap.add_argument('--run', required=True)
    a = ap.parse_args()
    report = review_case(a.case, a.run)
    print(json.dumps(report, ensure_ascii=False, indent=2))
    raise SystemExit(1 if 'fail' in (report['file_status'], report['geometry_status'], report['view_metadata_status']) else 0)
