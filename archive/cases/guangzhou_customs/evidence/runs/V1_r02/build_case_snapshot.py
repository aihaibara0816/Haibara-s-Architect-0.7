"""Guangzhou Customs V1: explicit photo interpretation on HAF 0.2.

No SU/model or geographic registration is claimed. 137 blocks is the preserved
study envelope from a conflicted source packet. The front is model +Z.
"""
from pathlib import Path
import argparse, collections, json, math, sys
import numpy as np

CASE = Path(__file__).resolve().parents[1]
HAF = CASE.parents[1]
sys.path[:0] = [str(HAF), str(HAF / 'support')]
from hafusion.classical import Builder, M
from hafusion.case_io import save_run, dump
from hafusion.lighting import unit
from hafusion.interiors import room_style, furnishing_cells

DIRS = [('front', 0, 1), ('rear', 0, -1), ('left', -1, 0), ('right', 1, 0)]


class Customs(Builder):
    def __init__(self, p):
        super().__init__(p['frame']['size_xyz'], p['seed'])
        self.p = p
        self.g = p['frame']['ground_y']
        self.cx = p['frame']['center_x']
        w, h, d = self.s.size
        self.mass = np.zeros((h, d, w), dtype=bool)
        self.surface_samples = []
        self.floor_ys = sorted({self.g + y for y in p['podium']['floor_levels'] + p['tower']['floor_levels'] + p['tower']['upper_floor_levels']})

    def mark(self, rect, y0, y1):
        x0, z0, x1, z1 = rect
        self.mass[self.g+y0:self.g+y1, z0:z1, x0:x1] = True

    def masks(self):
        t = self.p['tower']
        self.mark(self.p['podium']['rect'], 0, self.p['podium']['top'])
        self.mark([25, 39, 102, 71], 22, t['wing_top'])
        self.mark([25, 39, 38, 74], 22, t['wing_top'])
        self.mark([89, 39, 102, 74], 22, t['wing_top'])
        self.mark(t['central_rect'], 22, t['center_top'])
        # The middle window field is behind the two solid central piers.
        self.mass[self.g+22:self.g+96, 73:76, 57:70] = False
        self.mass[self.g+96:self.g+112, 74:76, 57:70] = False

    def site(self):
        g = self.g
        self.box((5, g-2, 7), (122, g-1, 113), 'stone_bricks', 'site.foundation')
        for x in range(5, 122):
            for z in range(7, 113):
                m = 'polished_andesite' if x % 12 == 0 or z % 10 == 0 else 'smooth_stone'
                self.put(x, g-1, z, m, 'site.paving')
        # Modest front planting; not a survey of the entire surrounding block.
        for x0, z0, x1, z1 in [(15, 94, 42, 102), (85, 94, 112, 102), (7, 24, 11, 82), (116, 24, 120, 82)]:
            self.box((x0, g-1, z0), (x1, g, z1), 'dirt', 'site.planter.soil')
            for x in range(x0, x1):
                for z in range(z0, z1):
                    edge = x in (x0, x1-1) or z in (z0, z1-1)
                    self.put(x, g, z, M('smooth_stone_slab') if edge else 'moss_block', 'site.planter.edge' if edge else 'site.planter.low_green')
                    if not edge and (x+z) % 7 == 0:
                        self.put(x, g+1, z, 'azalea_leaves', 'site.planter.hedge')
        for x, z in [(21, 98), (35, 98), (91, 98), (105, 98), (9, 32), (118, 72)]:
            self.tree(x, z, g+1, h=10, r=3)
        for x, z in [(38, 109), (88, 109), (8, 15), (119, 15)]:
            self.line((x, g, z), (x, g+5, z), 'iron_bars', 'lighting.site.pole')
            for dx in [-1, 1]:
                self.put(x+dx, g+5, z, 'iron_bars', 'lighting.site.arm')
                self.put(x+dx, g+6, z, 'glowstone', 'lighting.site.head')
                self.put(x+dx, g+7, z, M('smooth_stone_slab'), 'lighting.site.cap')

    def shell_and_floors(self):
        g = self.g
        for y in range(g, g+self.p['tower']['center_top']):
            active = self.mass[y]
            # Two-block wall depth provides a true recessed window reveal.
            interior = active.copy()
            for shift in [1, 2]:
                for axis in [0, 1]:
                    interior &= np.roll(active, shift, axis=axis)
                    interior &= np.roll(active, -shift, axis=axis)
            boundary = active & ~interior
            exposed_top = active & ~self.mass[y+1]
            exposed_bottom = active & ~self.mass[y-1]
            floor = y in self.floor_ys
            for z, x in zip(*np.where(boundary | exposed_top | exposed_bottom | (active if floor else False))):
                x, z = int(x), int(z)
                body = 'podium' if y < g+22 else 'tower'
                if boundary[z, x]:
                    # Repeated panel texture, not random stains across the facade.
                    m = 'quartz_block' if (x+z) % 4 == 0 else self.p['materials']['main_stone']
                    self.put(x, y, z, m, body+'.masonry')
                elif exposed_top[z, x]:
                    m = self.p['podium']['roof_surface'] if body == 'podium' else 'smooth_stone'
                    self.put(x, y, z, m, body+'.roof.surface')
                elif floor or exposed_bottom[z, x]:
                    self.put(x, y, z, M('smooth_stone_slab', type='top'), body+'.floor')
        # A restrained horizontal cornice, separated from the repetitive window rows.
        for rect, level, own in [([13, 16, 114, 87], 21, 'podium.cornice'), ([25, 39, 102, 74], 103, 'tower.shoulder.cornice'), ([50, 28, 77, 76], 112, 'tower.center.cornice')]:
            self.cornice(rect, g+level, own)

    def cornice(self, rect, y, own):
        x0, z0, x1, z1 = rect
        for dy, ext, m in [(-1, 0, 'smooth_quartz'), (0, 1, M('smooth_quartz_slab', type='top')), (1, 2, M('smooth_stone_slab'))]:
            for x in range(x0-ext, x1+ext):
                for z in [z0-ext, z1-1+ext]:
                    self.put(x, y+dy, z, m, own)
            for z in range(z0-ext, z1+ext):
                for x in [x0-ext, x1-1+ext]:
                    self.put(x, y+dy, z, m, own)
        # Half-height dentils remain subordinate to the main silhouette.
        for x in range(x0, x1, 3):
            for z in [z0-1, z1]:
                self.put(x, y-1, z, M('smooth_quartz_slab', type='top'), own+'.dentil')

    def window(self, x, z, normal, y, width, height, own, room=True):
        f = self.frame(x, z, normal)
        lo = -(width//2)
        f.rect(lo, lo+width, y, y+height, -2, 1, 'minecraft:air', own+'.opening')
        f.rect(lo, lo+width, y, y+height, -1, 0, self.p['materials']['glass'], own+'.glass')
        for u in range(lo, lo+width):
            f.put(u, y-1, 0, M('smooth_quartz_slab', type='top'), own+'.sill')
        self.windows.append({'id': own, 'anchor': [x, y, z], 'normal_xz': list(normal), 'width': width, 'height': height, 'glass_recess': 1, 'room_candidate': room})

    def tower_facades(self):
        t, g = self.p['tower'], self.g
        for fi, fy in enumerate(t['floor_levels']):
            y = g+fy+1
            if fy+3 >= t['wing_top']: continue
            for x in t['outer_pair_windows']:
                self.window(x, t['outer_front_z'], (0, 1), y, 3, 2, f'tower.front.outer.f{fi}.x{x}')
            for x in t['inner_windows']:
                self.window(x, t['inner_front_z'], (0, 1), y, 2, 2, f'tower.front.inner.f{fi}.x{x}')
            for x in t['center_edge_windows']:
                self.window(x, t['center_front_z'], (0, 1), y, 2, 2, f'tower.front.pier.f{fi}.x{x}')
            if fy < 94:
                for x in t['center_windows']:
                    self.window(x, t['middle_front_z'], (0, 1), y, 2, 2, f'tower.front.center.f{fi}.x{x}')
            # The rear central projection and side elevations have their own bays.
            for x in [29, 34, 40, 45, 53, 58, 63, 68, 73, 81, 86, 93, 98]:
                zz = 28 if 50 <= x < 77 else 39
                self.window(x, zz, (0, -1), y, 2, 2, f'tower.rear.f{fi}.x{x}')
            for x, n, side in [(25, (-1, 0), 'left'), (101, (1, 0), 'right')]:
                for z in [43, 48, 53, 58, 63, 68]:
                    self.window(x, z, n, y, 2, 2, f'tower.{side}.f{fi}.z{z}')
            for x, n, side in [(50, (-1, 0), 'rear_left'), (76, (1, 0), 'rear_right')]:
                for z in [32, 36]:
                    self.window(x, z, n, y, 2, 2, f'tower.{side}.f{fi}.z{z}', room=False)
        # The two high side-piers continue above the lower shoulders.
        for fy in t['upper_floor_levels']:
            for x in t['center_edge_windows']:
                self.window(x, 75, (0, 1), g+fy+1, 2, 2, f'tower.front.upper.{fy}.{x}', room=False)
            for x in [53, 58, 63, 68, 73]:
                self.window(x, 28, (0, -1), g+fy+1, 2, 2, f'tower.rear.upper.{fy}.{x}', room=False)
            for x, n, side in [(50, (-1, 0), 'left'), (76, (1, 0), 'right')]:
                for z in [33, 40, 47, 54, 61, 68]:
                    self.window(x, z, n, g+fy+1, 2, 2, f'tower.upper.{side}.{fy}.{z}', room=False)
        # Shallow vertical shadow slots in the middle three window fields.
        for a, b, z in [(38, 50, 70), (57, 70, 72), (77, 89, 70)]:
            for x in range(a+1, b, 4 if a != 57 else 3):
                for y in range(g+23, g+94):
                    if (x, y, z) in self.s.blocks and 'glass' not in self.s.blocks[(x, y, z)]:
                        self.put(x, y, z, 'quartz_block', 'tower.front.recessed_panel')
        # Shoulder attic blind half-rounds, not copies of the central giant arch.
        for x in [41, 46, 80, 85]:
            f = self.frame(x, 70, (0, 1))
            f.rect(-1, 2, g+101, g+103, -2, 1, 'minecraft:air', 'tower.shoulder.attic.opening')
            f.rect(-1, 2, g+101, g+102, -1, 0, 'black_stained_glass_pane', 'tower.shoulder.attic.glass')
            f.put(0, g+102, -1, 'black_stained_glass_pane', 'tower.shoulder.attic.glass')
        # Separate horizontal ledge below the two-storey outer shoulder caps.
        for x0, x1 in [(25, 38), (89, 102)]:
            self.box((x0-1, g+94, 74), (x1+1, g+95, 75), M('smooth_quartz_slab', type='top'), 'tower.shoulder.lower_ledge')

    def podium(self):
        g = self.g
        # Central entry replaces windows here; other sides remain completely enclosed.
        for fy in [0, 5, 10, 15]:
            for x in list(range(18, 47, 6)) + list(range(84, 112, 6)):
                self.window(x, 86, (0, 1), g+fy+1, 3, 3, f'podium.front.{fy}.{x}', room=False)
            for x in range(18, 111, 6):
                self.window(x, 16, (0, -1), g+fy+1, 3, 3, f'podium.rear.{fy}.{x}', room=False)
            for x, n, side in [(13, (-1, 0), 'left'), (113, (1, 0), 'right')]:
                for z in range(22, 83, 6):
                    self.window(x, z, n, g+fy+1, 3, 3, f'podium.{side}.{fy}.{z}', room=False)
        # Long base pilasters, paired with thin cap/foot details.
        for x in list(range(14, 47, 6)) + list(range(81, 114, 6)):
            self.box((x, g, 87), (x+1, g+16, 88), 'smooth_quartz', 'podium.front.pilaster')
            for y in [g, g+15]: self.put(x, y, 88, M('smooth_quartz_slab'), 'podium.front.pilaster.cap')
        # Two dark glazed rooftop enclosures observed in the high oblique photo.
        for i, rect in enumerate(self.p['podium']['glass_pavilions']):
            x0, z0, x1, z1 = rect; y0 = g+22; y1 = y0+self.p['podium']['pavilion_height']
            for y in range(y0, y1):
                for x in range(x0, x1):
                    for z in [z0, z1-1]:
                        mat = 'smooth_quartz' if (x-x0) % 5 == 0 or y in [y0+3, y1-1] else 'black_stained_glass_pane'
                        self.put(x, y, z, mat, f'podium.pavilion{i}.skin')
                for z in range(z0, z1):
                    for x in [x0, x1-1]:
                        mat = 'smooth_quartz' if (z-z0) % 4 == 0 or y in [y0+3, y1-1] else 'black_stained_glass_pane'
                        self.put(x, y, z, mat, f'podium.pavilion{i}.skin')
            self.box((x0, y1, z0), (x1, y1+1, z1), M('smooth_stone_slab'), f'podium.pavilion{i}.roof')
            for x in range(x0, x1, 5):
                self.box((x, y1+1, z0), (x+1, y1+2, z1), M('smooth_quartz_slab'), f'podium.pavilion{i}.roof_rib')
        # Roof perimeter/parapet with occasional open balusters; green finish is not lawn.
        for x in range(14, 113):
            for z in [17, 85]:
                if x % 3 == 0: self.put(x, g+23, z, 'diorite_wall', 'podium.roof.rail')
                self.put(x, g+24, z, M('smooth_quartz_slab'), 'podium.roof.coping')
        for z in range(18, 85):
            for x in [14, 112]:
                if z % 3 == 0: self.put(x, g+23, z, 'diorite_wall', 'podium.roof.rail')
                self.put(x, g+24, z, M('smooth_quartz_slab'), 'podium.roof.coping')
        # Large arched side bays in the high oblique reference. The assignment
        # to model-right is provisional, rather than a claim to a surveyed face.
        ar = self.p['podium']['side_arcades']; radius = ar['width']/2
        for i, z in enumerate(ar['centers_z']):
            f = self.frame(ar['wall_x'], z, tuple(ar['normal']))
            for u in range(-5, 6):
                for yy in range(ar['bottom'], 18):
                    inside = abs(u)<=radius and (yy<=ar['spring'] or u*u+(yy-ar['spring'])**2<=radius*radius)
                    if inside:
                        f.rect(u, u+1, g+yy, g+yy+1, -2, 1, 'minecraft:air', f'podium.arcade{i}.opening')
                        f.put(u, g+yy, -1, 'gray_stained_glass_pane', f'podium.arcade{i}.glazing')
                    elif abs(u)<=radius+1:
                        f.put(u, g+yy, 0, 'smooth_quartz', f'podium.arcade{i}.ring')
            for u in [-5, 5]:
                f.rect(u, u+1, g+2, g+18, 1, 2, 'smooth_quartz', f'podium.arcade{i}.pier')
                for yy in [g+2,g+17]: f.put(u, yy, 2, M('smooth_quartz_slab'), f'podium.arcade{i}.cap')
            f.rect(-5, 6, g+18, g+19, 1, 2, M('smooth_quartz_slab', type='top'), f'podium.arcade{i}.head')

    def round_column(self, x, z, y0, y1, owner):
        for yy in range(y0, y1):
            self.disk(x+.5, z+.5, 1.2, yy, 'smooth_quartz', owner+'.shaft')
        for yy in [y0, y1-1]:
            self.box((x-1, yy, z-1), (x+2, yy+1, z+2), M('smooth_quartz_slab', type='top'), owner+'.cap')

    def entrance(self):
        e, g = self.p['entrance'], self.g
        # True double-height lobby, set behind the four round columns.
        self.box((47, g+4, 77), (80, g+19, 89), 'minecraft:air', 'entrance.lobby.void')
        self.box((46, g+2, 77), (81, g+3, 102), 'smooth_sandstone', 'entrance.landing.foundation')
        self.box((46, g+3, 77), (81, g+4, 102), 'smooth_stone', 'entrance.landing.floor')
        # Six half-height rises, supported from below.
        for k in range(6):
            z = 107-k; yy = g+k//2
            self.box((48, g-1, z), (79, yy, z+1), 'smooth_quartz', 'entrance.stair.support')
            self.box((48, yy, z), (79, yy+1, z+1), M('smooth_quartz_slab', type='top' if k%2 else 'bottom'), 'entrance.stair.tread')
        for x in e['column_x']:
            self.round_column(x, 94, g+4, g+e['canopy_bottom'], 'entrance.column.'+str(x))
        self.box((46, g+e['canopy_bottom'], 84), (81, g+e['canopy_top'], 97), 'smooth_quartz', 'entrance.entablature')
        self.box((45, g+e['canopy_top'], 83), (82, g+e['canopy_top']+1, 98), M('smooth_quartz_slab'), 'entrance.cornice')
        for x in range(47, 81, 2):
            self.put(x, g+e['canopy_bottom']-1, 96, M('smooth_quartz_slab', type='top'), 'entrance.dentil')
        for x in range(48, 80):
            for z in range(84, 96):
                if x % 4 == 0 or z % 4 == 0:
                    self.put(x, g+e['canopy_bottom']-1, z, M('smooth_sandstone_slab', type='top'), 'entrance.soffit.coffer')
        # The source's four-character name is omitted at this scale, not replaced by fake text.
        for x in range(49, 79):
            for y in range(g+4, g+15):
                mat = 'smooth_quartz' if x in [49, 56, 70, 78] or y == g+11 else 'gray_stained_glass_pane'
                self.put(x, y, 84, mat, 'entrance.recessed_glazing')
        self.box((60, g+4, 84), (67, g+8, 85), 'minecraft:air', 'entrance.open_doorway')
        self.box((49, g+4, 77), (78, g+5, 82), 'smooth_stone', 'interior.lobby.floor')
        for x in [50, 76]:
            self.put(x, g+5, 81, 'dark_oak_planks', 'interior.lobby.planter')
            self.put(x, g+6, 81, 'oak_leaves', 'interior.lobby.plant')
        for x in [55, 63, 71]:
            self.put(x, g+14, 91, 'glowstone', 'lighting.entrance.ceiling')
            self.put(x, g+14, 86, 'sea_lantern', 'lighting.entrance.inner')

    def crown(self):
        c, g = self.p['crown'], self.g
        f = self.frame(self.cx, 75, (0, 1)); r = c['arch_width']/2
        # Hollow behind the arch; the upper office floors stop short of this atrium.
        self.box((57, g+96, 66), (70, g+112, 77), 'minecraft:air', 'crown.arch.void')
        for u in range(-7, 8):
            for yy in range(c['arch_bottom'], c['arch_top']+2):
                inside = abs(u) <= r and (yy <= c['arch_spring'] or u*u+(yy-c['arch_spring'])**2 <= r*r)
                if inside:
                    f.put(u, g+yy, -1, 'gray_stained_glass_pane', 'crown.arch.glass')
                elif abs(u) <= r+1 and yy <= c['arch_spring']+r+1:
                    f.put(u, g+yy, 0, 'smooth_quartz', 'crown.arch.ring')
        for u in [-4, 0, 4]:
            for yy in range(c['arch_bottom'], c['arch_spring']+1):
                f.put(u, g+yy, -1, 'black_stained_glass_pane', 'crown.arch.mullion')
        for yy in [c['arch_bottom']+3, c['arch_bottom']+7]:
            for u in range(-5, 6): f.put(u, g+yy, -1, M('iron_trapdoor', half='top'), 'crown.arch.transom')
        for x in [54, 57, 69, 72]:
            self.round_column(x, 77, g+96, g+111, 'crown.paired_column.'+str(x))
        self.box((52, g+94, 74), (75, g+96, 80), 'smooth_quartz', 'crown.balcony.base')
        for x in range(52, 75):
            self.put(x, g+96, 79, M('smooth_quartz_slab'), 'crown.balcony.coping')
            if x % 3 == 0: self.put(x, g+95, 79, 'polished_deepslate', 'crown.balcony.inset')
        self.box((52, g+111, 74), (75, g+113, 80), 'smooth_quartz', 'crown.portico.entablature')
        # Roof-side flat service surfaces; no extra skyline machinery invented.
        x, z = c['clock_center_xz']; rr = c['clock_radius']
        self.box((x-rr, g+c['clock_base'], z-rr), (x+rr+1, g+c['clock_roof'], z+rr+1), 'smooth_quartz', 'clock.chamber')
        self.box((x-rr+2, g+c['clock_base']+1, z-rr+2), (x+rr-1, g+c['clock_roof']-1, z+rr-1), 'minecraft:air', 'clock.interior.void')
        self.cornice([x-rr, z-rr, x+rr+1, z+rr+1], g+c['clock_roof']-1, 'clock.cornice')
        for face, (dx, dz) in enumerate([(0, 1), (1, 0), (0, -1), (-1, 0)]):
            f = self.frame(x+rr*dx, z+rr*dz, (dx, dz)); cy = g+c['dial_y']; rad = c['dial_radius']
            for u in range(-5, 6):
                for v in range(-5, 6):
                    d = math.hypot(u, v)
                    if d <= rad:
                        f.put(u, cy+v, 0, 'white_concrete', f'clock.dial{face}.face')
                        if d > rad-.30: f.put(u, cy+v, 1, 'polished_andesite', f'clock.dial{face}.ring')
            # At one block/metre full Roman numerals would merge into a black
            # disc. Preserve the white face and four major marks instead.
            for hour in [0,3,6,9]:
                a = hour*math.tau/12
                f.put(round((rad-1)*math.sin(a)), cy+round((rad-1)*math.cos(a)), 1, 'black_concrete', f'clock.dial{face}.markers')
            hh, mm = c['clock_time']
            for a, ln in [(mm/60*math.tau, rad-1), ((hh+mm/60)/12*math.tau, rad-2)]:
                f.line((0, cy, 1), (ln*math.sin(a), cy+ln*math.cos(a), 1), 'black_concrete', f'clock.dial{face}.hands')
            for u in [-5, 5]:
                f.rect(u, u+1, g+c['clock_base']+1, g+c['clock_roof']-1, 1, 2, 'smooth_quartz', f'clock.dial{face}.pilaster')
            # Discrete lights below the dial, rather than filling the dial with emitters.
            for u in [-4, 4]: f.put(u, g+c['clock_base'], 1, 'glowstone', f'lighting.clock.{face}')
        # Shallow curved metal cap, followed by a fine 10-block needle.
        for xx in range(x-rr, x+rr+1):
            for zz in range(z-rr, z+rr+1):
                d = math.hypot((xx-x)/rr, (zz-z)/rr)
                if d <= 1.05:
                    rise = round(c['dome_rise'] * math.sqrt(max(0, 1-d*d)))
                    self.put(xx, g+c['clock_roof']+rise, zz, M('smooth_stone_slab'), 'clock.dome.metal')
        for yy in range(g+c['spire_base'], g+c['spire_top']):
            mat = 'diorite_wall' if yy < g+c['spire_base']+2 else 'iron_bars'
            self.put(x, yy, z, mat, 'clock.spire')
        self.put(x, g+c['spire_top']-1, z, 'redstone_torch', 'lighting.aviation.tip')

    def interiors(self):
        g = self.g
        groups = {}
        for w in self.windows:
            if not w['room_candidate'] or not w['id'].startswith('tower.'): continue
            x, wy, z = w['anchor']; dx, dz = w['normal_xz']; fy = wy-1
            tangent = (dz, -dx); u = x if dz else z
            key = (dx, dz, z if dz else x, fy, u//6)
            groups.setdefault(key, []).append(w)
        for key, windows in sorted(groups.items()):
            w = windows[len(windows)//2]; x, wy, z = w['anchor']; dx, dz = w['normal_xz']; fy=wy-1
            tx, tz = dz, -dx; rid = 'office.'+'.'.join(map(str,key))
            # Keep each alcove wholly behind the original volume, away from corner junctions.
            coords = [(x+tx*u-dx*d, fy+2, z+tz*u-dz*d) for u in [-2, 2] for d in [2, 7]]
            if not all(self.mass[yy, zz, xx] for xx, yy, zz in coords): continue
            if fy >= g+94 and 55 <= x <= 71 and dz == 1: continue
            style = room_style(self.seed, rid, 3, 'office')
            for u in range(-2, 3):
                for yy in range(fy+1, fy+4):
                    self.put(x+tx*u-dx*7, yy, z+tz*u-dz*7, 'light_gray_concrete', 'interior.'+rid+'.back', empty=True)
            for u, yy, d, m in furnishing_cells(style['style'], 3):
                q = (x+tx*(u-2)-dx*(d+2), fy+1+yy, z+tz*(u-2)-dz*(d+2))
                if self.mass[q[1],q[2],q[0]]: self.put(*q, m, 'interior.'+rid+'.furniture', empty=True)
            draw = unit(self.seed, rid, 'occupancy', namespace=self.p['lighting']['namespace'])
            material = None if draw < .5 else 'glowstone' if draw < .75 else 'sea_lantern'
            q = (x-dx*4, fy+3, z-dz*4); placed=False
            if material: placed=self.put(*q, material, 'lighting.room.'+rid, empty=True)
            self.rooms.append({'id':rid,'floor_y':fy,'windows':[a['id'] for a in windows], 'style':style['style'], 'expected_material':material,'lamp_position':list(q) if placed else None,'actual_lamp':material if placed else None,'fidelity':'synthetic office window-back; unknown real plan'})
        # A small service stair in the central volume. Not the actual fire stair.
        for fy in self.p['tower']['floor_levels'][:-1]:
            yy=g+fy
            self.box((60, yy, 43), (64, yy+1, 52), 'minecraft:air', 'interior.service_stair.floor_void')
            for k in range(8):
                self.box((60, yy+1+k//2, 44+k), (64, yy+2+k//2, 45+k), M('smooth_stone_slab', type='top' if k%2 else 'bottom'), 'interior.service_stair.tread')
            for k in range(9): self.put(64, yy+2+k//2, 43+k, 'iron_bars', 'interior.service_stair.rail')

    def build(self):
        for name in ['masks', 'site', 'shell_and_floors', 'tower_facades', 'podium', 'entrance', 'crown', 'interiors']:
            getattr(self, name)()
            print(name, len(self.s.blocks), flush=True)
        return self


def main():
    ap=argparse.ArgumentParser();ap.add_argument('--run', required=True);ap.add_argument('--params',type=Path);a=ap.parse_args()
    if Path(a.run).name != a.run or a.run in ['.','..']: ap.error('new simple run name required')
    p=json.loads((a.params or CASE/'params.json').read_text());b=Customs(p).build()
    counts=collections.Counter(r['actual_lamp'] or 'off' for r in b.rooms)
    out=save_run(CASE,a.run,p,b,__file__,{'route':'image_only','three_dimensional_model_used':False,'nominal_blocks_per_metre':1,'building_height_envelope':137,'height_status':'conflicted photo-based study, not surveyed','floor_schedule':b.floor_ys,'room_lighting_counts':dict(counts),'clock_face_count':4,'geographic_bearing':'unverified','estimate_notice':p['estimates']})
    dump(out/'build_decisions.json',{'front':'+Z','room_lights':dict(counts),'height_conflict_preserved':True,'reference_images_used':['img-nc-08','img-nc-11','img-nc-07','img-nc-01'],'no_night_photo_claim':True,'clock_unseen_faces':'two faces inferred','source_module':'cases/guangzhou_customs/src/build_case.py'})


if __name__ == '__main__': main()
