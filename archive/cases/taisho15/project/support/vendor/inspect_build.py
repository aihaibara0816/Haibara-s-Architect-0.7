#!/usr/bin/env python3
"""Read-only, bounded NBT inspection and block-state diff. Python 3.10+.

Supports a checked subset of Java structure NBT (single palette), and
Sponge schematic v2/v3 block containers. This is not a game validator,
renderer, universal NBT converter, or format certification tool.
No dependencies, network requests, code execution from inputs, or world edits.
"""
from __future__ import annotations
import argparse
from collections import Counter
from dataclasses import dataclass
import gzip
import hashlib
import io
import json
import math
from pathlib import Path
import re
import struct
import sys
from typing import Any

class InvalidBuild(ValueError):
    """Malformed, unsupported, or resource-limited input."""

@dataclass(frozen=True)
class Limits:
    file_bytes: int = 32 * 1024 * 1024
    decoded_bytes: int = 64 * 1024 * 1024
    cells: int = 1_000_000
    nodes: int = 8_000_000
    depth: int = 64

class Reader:
    def __init__(self, data: bytes, limits: Limits):
        self.data, self.pos, self.limits, self.nodes = data, 0, limits, 0

    def take(self, n: int) -> bytes:
        if n < 0 or self.pos + n > len(self.data):
            raise InvalidBuild('Truncated NBT payload or invalid length')
        out = self.data[self.pos:self.pos+n]
        self.pos += n
        return out

    def number(self, fmt: str) -> Any:
        return struct.unpack('>' + fmt, self.take(struct.calcsize('>' + fmt)))[0]

    def text(self) -> str:
        raw = self.take(self.number('H'))
        try:
            # NBT strings may use Java modified UTF-8. Normalize encoded NUL
            # and paired UTF-16 surrogates without discarding invalid bytes.
            value = raw.replace(b'\xc0\x80', b'\x00').decode('utf-8', 'surrogatepass')
            return value.encode('utf-16-le', 'surrogatepass').decode('utf-16-le', 'surrogatepass')
        except UnicodeError as exc:
            raise InvalidBuild('Invalid or unsupported NBT string encoding') from exc

    def count(self) -> int:
        n = self.number('i')
        if n < 0 or n > self.limits.nodes:
            raise InvalidBuild('Negative or excessive NBT array/list length')
        return n

    def payload(self, kind: int, depth: int = 0) -> Any:
        self.nodes += 1
        if depth > self.limits.depth or self.nodes > self.limits.nodes:
            raise InvalidBuild('NBT depth/node budget exceeded')
        if kind in (1, 2, 3, 4, 5, 6):
            return self.number({1:'b',2:'h',3:'i',4:'q',5:'f',6:'d'}[kind])
        if kind == 7:
            return self.take(self.count())
        if kind == 8:
            return self.text()
        if kind == 9:
            item_kind, n = self.number('B'), self.count()
            if item_kind not in range(13) or (item_kind == 0 and n):
                raise InvalidBuild('Invalid list tag type')
            if self.nodes + n > self.limits.nodes:
                raise InvalidBuild('NBT node budget exceeded')
            return [self.payload(item_kind, depth+1) for _ in range(n)]
        if kind == 10:
            out = {}
            while True:
                child = self.number('B')
                if child == 0:
                    return out
                name = self.text()
                if name in out:
                    raise InvalidBuild('Duplicate NBT compound key')
                out[name] = self.payload(child, depth+1)
        if kind in (11, 12):
            n = self.count()
            if self.nodes + n > self.limits.nodes:
                raise InvalidBuild('NBT node budget exceeded')
            self.nodes += n
            fmt = 'i' if kind == 11 else 'q'
            return [v[0] for v in struct.iter_unpack('>'+fmt, self.take(n*(4 if kind == 11 else 8)))]
        raise InvalidBuild(f'Unsupported/invalid NBT tag type {kind}')


def read_nbt(path: Path, limits: Limits) -> tuple[dict, dict]:
    with path.open('rb') as stream:
        raw = stream.read(limits.file_bytes+1)
    if len(raw) > limits.file_bytes:
        raise InvalidBuild('Compressed/input file size limit exceeded')
    if raw.startswith(b'\x1f\x8b'):
        try:
            with gzip.GzipFile(fileobj=io.BytesIO(raw)) as f:
                data = f.read(limits.decoded_bytes+1)
        except (OSError, EOFError) as exc:
            raise InvalidBuild('Invalid/truncated gzip stream') from exc
        compression = 'gzip'
    else:
        data, compression = raw, 'uncompressed'
    if len(data) > limits.decoded_bytes:
        raise InvalidBuild('Decoded NBT size limit exceeded')
    r = Reader(data, limits)
    if r.number('B') != 10:
        raise InvalidBuild('Expected big-endian NBT root compound; zlib, Bedrock and ZIP are unsupported')
    name = r.text()
    root = r.payload(10)
    if r.pos != len(data):
        raise InvalidBuild('Trailing bytes after the NBT root compound')
    return root, {'file_name':path.name, 'file_sha256':hashlib.sha256(raw).hexdigest(),
                  'file_bytes':len(raw), 'decoded_bytes':len(data), 'compression':compression,
                  'root_name':name}


def int3(value: Any, name: str) -> tuple[int, int, int]:
    if not isinstance(value, list) or len(value) != 3 or any(type(v) is not int for v in value):
        raise InvalidBuild(f'{name} must contain three integers')
    return tuple(value)


def state_name(name: Any, properties: Any = None) -> str:
    if not isinstance(name, str):
        raise InvalidBuild('Block state name is not a string')
    props = {} if properties is None else properties
    if '[' in name:
        if properties is not None or not name.endswith(']') or name.count('[') != 1:
            raise InvalidBuild('Malformed block state')
        name, text = name[:-1].split('[', 1)
        props = {}
        for pair in text.split(','):
            if pair.count('=') != 1:
                raise InvalidBuild('Malformed block state property')
            key, val = pair.split('=', 1)
            if key in props:
                raise InvalidBuild('Duplicate block state property')
            props[key] = val
    if not re.fullmatch(r'[a-z0-9_.-]+:[a-z0-9_./-]+', name):
        raise InvalidBuild('Malformed namespaced block ID')
    if not isinstance(props, dict):
        raise InvalidBuild('Properties must be a compound')
    for key, val in props.items():
        if not isinstance(key, str) or not re.fullmatch(r'[a-z0-9_]+', key):
            raise InvalidBuild('Malformed property name')
        if not isinstance(val, str) or not re.fullmatch(r'[a-z0-9_:.+-]+', val):
            raise InvalidBuild('Malformed property value')
    return name + ('['+','.join(f'{k}={props[k]}' for k in sorted(props))+']' if props else '')


AIR = {'minecraft:air', 'minecraft:cave_air', 'minecraft:void_air'}
IGNORED = AIR | {'minecraft:structure_void'}

def base_name(state: str) -> str:
    return state.split('[', 1)[0]

def visible_state(state: str | None) -> str | None:
    return None if state is None or base_name(state) in IGNORED else state


def decode_varints(data: Any, expected: int):
    if not isinstance(data, bytes):
        raise InvalidBuild('Schematic block data must be an NBT byte array')
    at = 0
    for _ in range(expected):
        value = 0
        for byte_index in range(5):
            if at >= len(data):
                raise InvalidBuild('Truncated schematic varint data')
            byte = data[at]
            at += 1
            value |= (byte & 127) << (7*byte_index)
            if not byte & 128:
                if value > 0x7fffffff:
                    raise InvalidBuild('Palette varint exceeds positive signed int range')
                yield value
                break
        else:
            raise InvalidBuild('Overlong schematic varint')
    if at != len(data):
        raise InvalidBuild('Schematic block data has trailing or excess entries')

@dataclass
class Build:
    size: tuple[int, int, int]
    blocks: dict[tuple[int, int, int], str]
    info: dict
    palette: list[str]


def load_build(path: Path, limits: Limits = Limits()) -> Build:
    root, info = read_nbt(path, limits)
    blocks = {}
    if {'size', 'blocks'}.issubset(root):
        if 'palette' not in root or 'palettes' in root:
            raise InvalidBuild('Only single-palette Java structure NBT is currently supported')
        size = int3(root['size'], 'size')
        palette_source = root['palette']
        if not isinstance(palette_source, list) or not palette_source:
            raise InvalidBuild('Missing or empty structure palette')
        palette = []
        for p in palette_source:
            if not isinstance(p, dict):
                raise InvalidBuild('Invalid palette entry')
            palette.append(state_name(p.get('Name'), p.get('Properties')))
        entries = root['blocks']
        if not isinstance(entries, list) or len(entries) > limits.cells:
            raise InvalidBuild('Invalid/excessive block entry list')
        _check_size(size, limits)
        block_entities = 0
        for b in entries:
            if not isinstance(b, dict):
                raise InvalidBuild('Invalid structure block record')
            pos, idx = int3(b.get('pos'), 'block pos'), b.get('state')
            if any(not 0 <= pos[i] < size[i] for i in range(3)):
                raise InvalidBuild('Out-of-bounds block coordinate')
            if type(idx) is not int or not 0 <= idx < len(palette):
                raise InvalidBuild('Out-of-range palette reference')
            if pos in blocks:
                raise InvalidBuild('Duplicate block coordinate')
            blocks[pos] = palette[idx]
            block_entities += 'nbt' in b
        info.update(format='java_structure', data_version=root.get('DataVersion'),
                    offset_xyz=[0,0,0], block_entities_count=block_entities,
                    entities_count=_entity_count(root.get('entities', [])))
    else:
        s = root.get('Schematic', root)
        if not isinstance(s, dict) or s.get('Version') not in (2, 3):
            raise InvalidBuild('Unsupported format: expected Java structure NBT or Sponge v2/v3')
        version = s['Version']
        dimensions = [s.get(k) for k in ('Width', 'Height', 'Length')]
        if any(type(v) is not int or not -32768 <= v <= 65535 for v in dimensions):
            raise InvalidBuild('Invalid schematic dimensions')
        size = tuple(v & 0xffff for v in dimensions)
        _check_size(size, limits)
        source = s.get('Blocks') if version == 3 else s
        if not isinstance(source, dict):
            raise InvalidBuild('Missing block container; biome-only schematics are unsupported')
        p = source.get('Palette')
        if not isinstance(p, dict) or not p:
            raise InvalidBuild('Missing or empty schematic palette')
        by_idx = {}
        for state, idx in p.items():
            if type(idx) is not int or not 0 <= idx <= 0x7fffffff or idx in by_idx:
                raise InvalidBuild('Invalid or duplicate schematic palette index')
            by_idx[idx] = state_name(state)
        palette = [by_idx[i] for i in sorted(by_idx)]
        data = source.get('Data' if version == 3 else 'BlockData')
        w, h, length = size
        for n, idx in enumerate(decode_varints(data, w*h*length)):
            if idx not in by_idx:
                raise InvalidBuild('Unmapped schematic palette reference')
            pos = (n % w, n // (w*length), (n // w) % length)
            blocks[pos] = by_idx[idx]
        info.update(format=f'sponge_schematic_v{version}', data_version=s.get('DataVersion'),
                    offset_xyz=list(int3(s.get('Offset', [0,0,0]), 'Offset')),
                    block_entities_count=_entity_count(source.get('BlockEntities', [])),
                    entities_count=_entity_count(s.get('Entities', [])))
    return Build(size, blocks, info, palette)


def _entity_count(value: Any) -> int:
    if not isinstance(value, list):
        raise InvalidBuild('Entity container must be an NBT list')
    return len(value)


def _check_size(size, limits):
    if any(v <= 0 for v in size) or math.prod(size) > limits.cells:
        raise InvalidBuild('Nonpositive dimensions or bounding-volume cell limit exceeded')


def bbox(points) -> list[list[int]] | None:
    lo = [None]*3
    hi = [None]*3
    for pos in points:
        for i in range(3):
            lo[i] = pos[i] if lo[i] is None else min(lo[i], pos[i])
            hi[i] = pos[i] if hi[i] is None else max(hi[i], pos[i])
    return None if lo[0] is None else [lo, hi]


def inspect(build: Build) -> dict:
    counts = Counter(build.blocks.values())
    layers = Counter(p[1] for p, s in build.blocks.items() if visible_state(s))
    h = hashlib.sha256()
    # Hash compares listed local block states, not compression, palette order,
    # placement offset, entities, or block-entity payloads.
    for pos, state in sorted(build.blocks.items()):
        h.update(json.dumps([pos, state], separators=(',', ':'), ensure_ascii=True).encode()+b'\n')
    visible_count = sum(layers.values())
    warnings = [
        'Subset structural checks only; no registry/property compatibility or game import test.',
        'Entities, block-entity contents, biomes, NBT field tag kinds and extra metadata are not semantically validated.',
        'Counts by Y are block distributions, not verified floor counts or collision/solidity measurements.'
    ]
    if not visible_count:
        warnings.append('No non-air/non-structure-void blocks were found: not a usable building sample.')
    return {**build.info, 'structural_subset_check':'pass', 'usable_nonempty_sample':bool(visible_count),
            'size_xyz':list(build.size), 'bounding_volume_cells':math.prod(build.size),
            'listed_block_entries':len(build.blocks),
            'unlisted_cells':math.prod(build.size)-len(build.blocks),
            'non_air_non_void_blocks':visible_count,
            'explicit_air_entries':sum(n for s,n in counts.items() if base_name(s) in AIR),
            'structure_void_entries':sum(n for s,n in counts.items() if base_name(s)=='minecraft:structure_void'),
            'occupied_bbox_inclusive':bbox(p for p,s in build.blocks.items() if visible_state(s)),
            'palette_entries':len(build.palette), 'used_block_state_counts':dict(sorted(counts.items())),
            'non_air_blocks_by_y':dict(sorted(layers.items())),
            'local_listed_blockstates_sha256':h.hexdigest(),
            'game_validation':'pending', 'warnings':warnings}


def compare(a: Build, b: Build, roi=None) -> dict:
    if roi is not None:
        if len(roi) != 6 or any(roi[i] > roi[i+3] for i in range(3)):
            raise InvalidBuild('ROI requires ordered inclusive x0 y0 z0 x1 y1 z1')
    changed, visible_changed = [], []
    added = removed = replaced = outside = 0
    # Absent entries differ from explicit air for placement semantics.
    for p in a.blocks.keys() | b.blocks.keys():
        old, new = a.blocks.get(p), b.blocks.get(p)
        if old != new:
            changed.append(p)
            added += old is None
            removed += new is None
            replaced += old is not None and new is not None
            if roi is not None and not all(roi[i] <= p[i] <= roi[i+3] for i in range(3)):
                outside += 1
        if visible_state(old) != visible_state(new):
            visible_changed.append(p)
    return {'comparison':'local_blockstates_only', 'before':a.info['file_name'], 'after':b.info['file_name'],
            'size_before':list(a.size), 'size_after':list(b.size),
            'offset_before':a.info['offset_xyz'], 'offset_after':b.info['offset_xyz'],
            'listed_state_changes':len(changed), 'added_entries':added,
            'removed_entries':removed, 'replaced_entries':replaced,
            'visible_state_changes':len(visible_changed),
            'change_bbox_inclusive':bbox(changed),
            'requested_roi_inclusive':roi, 'changes_outside_roi':outside if roi is not None else None,
            'warnings':[
                'No translation/rotation registration. Align the files before interpreting locality.',
                'Different extents or offsets may create widespread apparent changes.',
                'Absent and explicit air are distinct placement states; visual-state comparison ignores both.',
                'Entities, block-entity payloads, biome and other metadata changes are not compared.',
                'Local output changes do not prove that the generator used incremental internal computation.'
            ]}


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('file', type=Path)
    p.add_argument('--compare', type=Path, help='Compare block states against a second build')
    p.add_argument('--roi', type=int, nargs=6, metavar=('X0','Y0','Z0','X1','Y1','Z1'))
    p.add_argument('--out', type=Path, help='New JSON report path; existing files are not overwritten')
    p.add_argument('--max-cells', type=int, default=1_000_000)
    args = p.parse_args()
    try:
        if args.max_cells < 1:
            raise InvalidBuild('--max-cells must be positive')
        if args.roi and not args.compare:
            raise InvalidBuild('--roi requires --compare')
        limits = Limits(cells=args.max_cells)
        a = load_build(args.file, limits)
        result = compare(a, load_build(args.compare, limits), args.roi) if args.compare else inspect(a)
        text = json.dumps(result, ensure_ascii=True, indent=2) + '\n'
        if args.out:
            # Exclusive create protects both the input and existing reports.
            with args.out.open('x', encoding='utf-8') as f:
                f.write(text)
        else:
            print(text, end='')
        return 0
    except (InvalidBuild, OSError, UnicodeError, struct.error, TypeError, KeyError) as exc:
        print(json.dumps({'status':'error', 'message':str(exc)}, ensure_ascii=True), file=sys.stderr)
        return 2

if __name__ == '__main__':
    raise SystemExit(main())
