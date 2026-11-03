#!/usr/bin/env python3
"""Deterministic uniform scaling; Python standard library only; no network."""
import argparse
import json
from decimal import Decimal, ROUND_HALF_UP
from math import isfinite


def positive(value):
    return isinstance(value, (int, float)) and not isinstance(value, bool) and isfinite(value) and value > 0


def rounded_blocks(meters, s):
    if not positive(meters) or not positive(s):
        raise ValueError('meters and s must be finite positive numbers')
    return int((Decimal(str(meters)) * Decimal(str(s))).quantize(Decimal('1'), rounding=ROUND_HALF_UP))


def convert(value_m=None, range_m=None, s=1):
    """Unknown stays null. Estimates use intervals, never an invented point value."""
    if not positive(s):
        raise ValueError('s must be finite and positive')
    if value_m is not None and range_m is not None:
        raise ValueError('provide value_m OR range_m, not both')
    result={'s':s,'blocks':None,'blocks_range':None,'error_m':None,'error_range_m':None}
    if value_m is not None:
        b=rounded_blocks(value_m,s)
        result.update(blocks=b,error_m=round(b/s-value_m,9))
    elif range_m is not None:
        if not isinstance(range_m,list) or len(range_m)!=2 or not all(positive(v) for v in range_m) or range_m[0]>range_m[1]:
            raise ValueError('range_m must be [positive lower, positive upper]')
        b=[rounded_blocks(v,s) for v in range_m]
        result.update(blocks_range=b,error_range_m=[round(b[i]/s-range_m[i],9) for i in range(2)])
    return result


def uniform_bound(dimensions, budget):
    """Input dims: width/depth/height in meters. Unknown/unconfirmed bounds omitted."""
    limits={}
    omitted=[]
    for axis in ('width','depth','height'):
        d=dimensions.get(axis)
        limit=budget.get(axis,{})
        if positive(d) and limit.get('confirmed') is True and positive(limit.get('blocks')):
            limits[axis]=limit['blocks']/d
        else:
            omitted.append(axis)
    return {'maximum_s':min(limits.values()) if limits else None,'axis_limits':limits,'omitted_axes':omitted}


def packet_bound(scale):
    def upper(group,key):
        m=scale.get(group,{}).get(key,{})
        if positive(m.get('value_m')): return m['value_m']
        r=m.get('range_m')
        if isinstance(r,list) and len(r)==2 and all(positive(v) for v in r): return max(r)
        return None
    def largest(*values):
        known=[v for v in values if positive(v)]
        return max(known) if known else None
    dimensions={'width':largest(upper('building_dimensions','width'),upper('site_dimensions','width')),
                'depth':largest(upper('building_dimensions','length'),upper('site_dimensions','length')),
                'height':upper('building_dimensions','overall_height')}
    return uniform_bound(dimensions,scale.get('world_budget',{}))


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--meters',type=float)
    ap.add_argument('--range',nargs=2,type=float,dest='interval')
    ap.add_argument('--s',type=float,default=1)
    ap.add_argument('--packet',help='Compute conservative uniform scale bound from packet JSON')
    args=ap.parse_args()
    try:
        if args.packet:
            with open(args.packet,encoding='utf-8') as f: result=packet_bound(json.load(f)['scale'])
        else: result=convert(args.meters,args.interval,args.s)
    except (ValueError,KeyError,TypeError,OSError) as e: ap.error(str(e))
    print(json.dumps(result,ensure_ascii=False,indent=2,allow_nan=False))

if __name__=='__main__': main()
