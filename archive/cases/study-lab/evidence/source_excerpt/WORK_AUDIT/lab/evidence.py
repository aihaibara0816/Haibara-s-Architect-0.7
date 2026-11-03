"""Independent research prototype. Produces proposals, never edits BuildingSpec.

Extends the supplied RTM R0.1 experiment: normalize units, filter epochs/phases,
keep independent source families, expose conflicts. Policy is explicit case input.
No model training, calibrated probabilities, or autonomous architectural decisions.
"""
from copy import deepcopy
import math

LENGTH_UNITS = {'m': 1.0, 'cm': .01, 'mm': .001, 'inch': .0254}
STATUSES = {'confirmed', 'observed', 'estimated'}

def normalize(row, kind):
    value, unit = row['value'], row.get('unit')
    if kind in ('length', 'count'):
        if isinstance(value, bool) or not isinstance(value, (float, int)) or not math.isfinite(value):
            raise ValueError('finite numeric value required')
        if kind == 'length':
            if unit not in LENGTH_UNITS:
                raise ValueError('unknown length unit; block needs an explicit scale conversion')
            return float(value) * LENGTH_UNITS[unit], 'm'
        if unit != 'count' or value != int(value):
            raise ValueError('count requires an integer and unit=count')
        return int(value), 'count'
    if kind != 'category' or not isinstance(value, str) or unit is not None:
        raise ValueError('category requires a string without a unit')
    return value, None

def arbitrate(rows, *, kind, tolerance, target_epoch, source_order, baseline_hash, phase='as_built'):
    """One component/attribute. Tolerance is in normalized metres or counts.

    Epoch and phase come from prior source review; this module cannot infer them.
    Different values in one source family are reported, never counted as votes.
    """
    if not math.isfinite(tolerance) or tolerance < 0 or len(set(source_order)) != len(source_order):
        raise ValueError('invalid policy')
    if not baseline_hash or not target_epoch:
        raise ValueError('explicit baseline and epoch required')
    result = dict(status='insufficient', selected=None, conflicts=[], excluded=[],
                  families=[], baseline_hash=baseline_hash, automatic_write=False,
                  policy=dict(kind=kind, tolerance=tolerance, epoch=target_epoch, phase=phase, source_order=source_order))
    if not rows:
        return result
    key = (rows[0]['component_id'], rows[0]['attribute'])
    if any((r['component_id'], r['attribute']) != key for r in rows):
        raise ValueError('one component and attribute per decision')
    candidates = []
    for original in rows:
        r = deepcopy(original)
        if not all(r.get(k) for k in ('source_id', 'source_family', 'component_id', 'attribute')):
            raise ValueError('identifiers and source family required')
        reason = None
        if r.get('epoch') != target_epoch: reason = 'epoch_unknown_or_mismatch'
        elif r.get('phase') != phase: reason = 'phase_unknown_or_mismatch'
        elif r.get('status') not in STATUSES: reason = 'unsupported_evidence_status'
        elif r.get('source_type') not in source_order: reason = 'source_not_in_policy'
        if reason:
            result['excluded'].append({'source_id': r['source_id'], 'reason': reason}); continue
        try: r['normalized_value'], r['normalized_unit'] = normalize(r, kind)
        except ValueError as e:
            result['status'] = 'blocked'; result['reason'] = str(e)
            result['invalid_source_id'] = r['source_id']; return result
        candidates.append(r)
    def agree(a, b):
        if kind == 'category': return a['normalized_value'] == b['normalized_value']
        return abs(a['normalized_value'] - b['normalized_value']) <= tolerance
    grouped = {}
    for r in candidates: grouped.setdefault(r['source_family'], []).append(r)
    representatives = []
    for family, values in sorted(grouped.items()):
        result['families'].append({'family': family, 'source_ids': sorted({r['source_id'] for r in values})})
        if any(not agree(a, b) for a in values for b in values):
            result['status'] = 'needs_review'; result['reason'] = 'same_family_inconsistent'
            result['conflicts'].append({'family': family, 'values': values}); return result
        representatives.append(min(values, key=lambda r: (source_order.index(r['source_type']), r['source_id'])))
    if not representatives: return result
    ranked = sorted(representatives, key=lambda r: (source_order.index(r['source_type']), r['source_id']))
    winner = ranked[0]; peer_conflict = False
    for r in ranked[1:]:
        if not agree(winner, r):
            peer = winner['source_type'] == r['source_type']
            result['conflicts'].append({'a': winner['source_id'], 'b': r['source_id'], 'a_value': winner['normalized_value'], 'b_value': r['normalized_value'], 'peer': peer})
            peer_conflict |= peer
    result['independent_families'] = len(representatives)
    result['status'] = 'needs_review' if peer_conflict else 'proposal'
    result['selected'] = None if peer_conflict else winner
    result['reason'] = 'peer_disagreement' if peer_conflict else 'explicit_attribute_policy'
    return result
