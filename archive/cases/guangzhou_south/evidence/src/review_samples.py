"""Explicit South construction-record adapter for shared HAF 0.3 checks."""
import json
from hafusion.review import construction_checks

def contract(run):
    return construction_checks(json.loads((run/'construction_records.json').read_text()))
