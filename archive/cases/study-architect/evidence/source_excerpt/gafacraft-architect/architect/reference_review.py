"""Bind manual visual judgements to verified render bytes and executable components."""
import hashlib,json
from pathlib import Path
STATUSES={'pass','needs_revision','unverifiable','pending'}

def validate_review(report,spec,run_dir):
    from jsonschema import Draft202012Validator
    from .legacy import ROOT
    schema=json.loads((ROOT/'schema/reference_review.schema.json').read_text())
    errors=list(Draft202012Validator(schema).iter_errors(report))
    if errors:raise ValueError('Invalid review schema: '+errors[0].message)
    root=Path(run_dir).resolve()
    build=json.loads((root/'build_report.json').read_text())
    # Do not accept a report paired with an unrelated spec or a replaced PNG.
    from .pipeline import canonical_hash
    if canonical_hash(spec)!=build['spec_sha256']:raise ValueError('Review spec does not match build')
    if report.get('schema_version')!='0.1' or report.get('build_id')!=build['build_id']:raise ValueError('Review build identity mismatch')
    if report.get('method')!='manual':raise ValueError('Only manual review is implemented')
    if report.get('game_status')!='pending_game_test':raise ValueError('This tool cannot certify a game test')
    images={x['image_id'] for x in spec['evidence']['images']};components={x['component_id'] for x in spec['components']}
    required=set(spec['evidence']['selected_image_ids'])
    declared=report.get('required_image_ids')
    if not isinstance(declared,list) or len(declared)!=len(set(declared)) or not set(declared)<=images or not required<=set(declared):raise ValueError('Required images must retain all selected evidence')
    views={x['view']:x for x in build['views']};seen=set();covered=set();statuses=[]
    for pair in report['pairs']:
        pid=pair['pair_id'];status=pair['status'];image_id=pair['image_id']
        if pid in seen:raise ValueError('Duplicate review pair')
        seen.add(pid)
        if image_id not in images or not pair['component_ids'] or not set(pair['component_ids'])<=components:raise ValueError('Dangling review evidence/component')
        if status not in STATUSES or pair['camera_match'] not in ('matched','approximate','unverifiable'):raise ValueError('Invalid review status/camera')
        if status=='pass' and pair['camera_match']=='unverifiable':raise ValueError('Unverifiable camera cannot pass')
        if not pair.get('finding') or not pair.get('checkpoints'):raise ValueError('Review needs actual findings and checkpoints')
        if status=='needs_revision' and pair.get('severity') not in ('major','minor'):raise ValueError('Issue severity required')
        if pair.get('severity')=='major' and status=='pass':raise ValueError('Major unresolved issue cannot pass')
        vid=pair['view'];meta=views.get(vid)
        if meta is None:raise ValueError('Unknown model view')
        path=(root/meta['file']).resolve()
        if not path.is_relative_to(root) or hashlib.sha256(path.read_bytes()).hexdigest()!=meta['sha256']:raise ValueError('View bytes changed')
        covered.add(image_id);statuses.append(status)
    if not set(declared)<=covered:raise ValueError('Missing per-image review pairs')
    # Empty review cannot earn a pass.
    overall=('pending' if not statuses or 'pending' in statuses else 'needs_revision' if 'needs_revision' in statuses else 'pass_with_gaps' if 'unverifiable' in statuses else 'visual_review_pass')
    return {'visual_status':overall,'pairs':len(statuses),'game_status':'pending_game_test','method':'manual','limits':'Checks linkage and status consistency; does not judge image fidelity or estimate camera pose.'}
