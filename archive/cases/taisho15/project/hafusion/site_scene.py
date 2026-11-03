"""Explicit sparse site budget, retaining the original BuildKit Scene limits.

Landscape scenes contain a lot of empty sky. A separately bounded scene permits
that sky without permitting unlimited occupied blocks. Primitives/export remain
the preserved BuildKit implementation; this is not a new geometry backend.
"""
import math
from vendor.voxel_core import Scene, AIR


class SiteScene(Scene):
    def __init__(self, size, *, max_volume_cells=40_000_000, max_blocks=1_500_000):
        self.size = tuple(size)
        if (len(self.size) != 3 or any(type(v) is not int or v < 1 for v in self.size)
                or type(max_volume_cells) is not int
                or not 1 <= max_volume_cells <= 64_000_000
                or math.prod(self.size) > max_volume_cells):
            raise ValueError('Invalid or excessive site bounding volume')
        if type(max_blocks) is not int or not 1 <= max_blocks <= 2_000_000:
            raise ValueError('Explicit occupied-block budget required (1..2,000,000)')
        self.max_cells = max_volume_cells
        self.max_blocks = max_blocks
        self.blocks, self.owners, self.events = {}, {}, []

    def set(self, p, s, owner):
        p = tuple(p)
        if s != AIR and p not in self.blocks and len(self.blocks) >= self.max_blocks:
            raise ValueError('Occupied site block budget exceeded')
        super().set(p, s, owner)

    def snapshot(self):
        out = SiteScene(self.size, max_volume_cells=self.max_cells, max_blocks=self.max_blocks)
        out.blocks, out.owners, out.events = dict(self.blocks), dict(self.owners), list(self.events)
        return out
