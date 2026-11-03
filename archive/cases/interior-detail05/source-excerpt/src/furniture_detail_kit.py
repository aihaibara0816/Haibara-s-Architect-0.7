"""Authored furniture studies v0.1, Java 1.21.1; not a room layout solver.

Uses InteriorKit's callback/metadata contract. Local y=0 is the floor block.
Reserve the reported footprints BEFORE calling; no overwrite protection is implied.
References guide composition, not a claim to exact tutorial block reconstruction.
"""
from interior_kit import InteriorKit


class FurnitureDetailKit(InteriorKit):
    def put(self,x,y,z,name,owner_part,**props):
        pos=super().put(x,y,z,name,owner_part,**props)
        if not hasattr(self,'_detail_placements'): self._detail_placements=[]
        self._detail_placements.append({'part':owner_part,'pos':list(pos)})
        return pos

    def panel(self, x, y, z, facing, part, wood='oak'):
        return self.put(x,y,z,wood+'_trapdoor',part,facing=facing,
                        half='bottom',open=True,powered=False,waterlogged=False)

    def detail_record(self, start, recipe, bounds, refs, limitations, api):
        component_start, placement_start=start
        self.record(recipe, api, bounds)
        self.components[-1].update(recipe_version='0.1', source_refs=refs,
            evidence='authored adaptation', geometry_consumer=__file__.split('/')[-1],
            children=[v['id'] for v in self.components[component_start:-1]],
            part_cells=self._detail_placements[placement_start:],
            limitations=limitations, game_checked=False)

    def framed_daybed(self, x, z, width=3, id='daybed'):
        """5x3 footprint for width=3, facing south. Actual paired beds, thin frame.

        Mattress occupies x..x+width-1,z..z+1. Keep south approach clear.
        This is a bed-backed daybed representation, not interactively sittable sofa.
        """
        if width not in (2,3): raise ValueError('supported widths: 2 or 3')
        start=(len(self.components),len(getattr(self,'_detail_placements',[])))
        for xx in range(x,x+width):
            self.bed(xx,z+1,id=id+'.mattress')
            self.components[-1]['use_points']=[[xx+self.origin[0],1+self.origin[1],z+2+self.origin[2]]]
            self.panel(xx,1,z-1,'north',id+'.back')
        for zz in range(z,z+2):
            self.panel(x-1,1,zz,'west',id+'.arm')
            self.panel(x+width,1,zz,'east',id+'.arm')
        self.detail_record(start,id,[x-1,1,z-1,x+width+1,2,z+2],['S01@01:49'],
                           ['bed-as-upholstery; vanilla sleep interaction untested',
                            'decorative seating; no sit interaction promised'],'framed_daybed')

    def bed_wall(self, x, z, id='bedwall'):
        """6x5 reserved ensemble: double bed, inset headboard, unequal side units.

        x,z is left bed head. True beds remain accessible on both outer sides.
        """
        start=(len(self.components),len(getattr(self,'_detail_placements',[])))
        for xx in [x,x+1]:
            self.bed(xx,z+1,id=id+'.sleep')
            side=x-1 if xx==x else x+2
            self.components[-1]['use_points']=[[side+self.origin[0],1+self.origin[1],z+1+self.origin[2]]]
        for xx in range(x-1,x+3):
            self.put(xx,1,z-1,'spruce_planks',id+'.headboard')
            self.panel(xx,2,z-1,'north',id+'.headboard_top')
        for xx in [x-2,x+3]:
            self.put(xx,1,z,'oak_stairs',id+'.bedside',facing='north',
                     half='top',shape='straight',waterlogged=False)
        self.put(x-2,2,z,'lantern',id+'.lamp',hanging=False,waterlogged=False)
        self.put(x+3,2,z,'flower_pot',id+'.cup')
        for xx in range(x-1,x+3):
            for zz in [z+2,z+3]: self.put(xx,1,zz,'light_gray_carpet',id+'.rug')
        self.detail_record(start,id,[x-2,1,z-1,x+4,3,z+4],['B01@00:26.070','UIMG2'],
                           ['true double bed plus authored headboard, not enlarged fake mattress',
                            'lighting and sleep still require client verification'],'bed_wall')

    def kitchen_band(self,x,z,id='kitchen',wood='spruce'):
        """Seven wide work band. Height 4; reserve 2 deep and front working aisle.

        Distinct closed storage, open shelf, sink and furnace. No texture heads.
        """
        start=(len(self.components),len(getattr(self,'_detail_placements',[])))
        self.barrel(x,1,z,id=id+'.store')
        self.put(x+1,1,z,wood+'_planks',id+'.prep')
        self.sink(x+2,z,id=id+'.wash')
        self.put(x+3,1,z,wood+'_planks',id+'.prep')
        self.furnace(x+4,z,id=id+'.cook')
        self.barrel(x+5,1,z,id=id+'.store')
        self.put(x+6,1,z,wood+'_planks',id+'.end')
        # Solid prep surfaces accept small objects; front plates are thin.
        for xx in [x+1,x+3,x+6]: self.panel(xx,1,z+1,'south',id+'.door_front')
        self.cake(x+1,2,z,id=id+'.meal')
        self.put(x+6,2,z,'flower_pot',id+'.cup')
        for xx in [x,x+1,x+5,x+6]:
            self.put(xx,3,z,wood+'_planks',id+'.upper')
            self.panel(xx,3,z+1,'south',id+'.upper_door')
        self.put(x+3,3,z,'oak_slab',id+'.open_shelf',type='top',waterlogged=False)
        self.put(x+3,4,z,'flower_pot',id+'.shelf_cup')
        self.put(x+4,3,z,'polished_andesite_slab',id+'.hood',type='top',waterlogged=False)
        self.detail_record(start,id,[x,1,z,x+7,5,z+2],['UIMG1','Y02@00:37'],
                           ['authored small kitchen; appliance interaction untested',
                            'cup/meal props are symbolic vanilla blocks, not custom heads'],'kitchen_band')

    def mixed_cabinet(self,x,z,id='cabinet'):
        """Four wide cabinet: storage + one open bay + books; not barrel wall."""
        start=(len(self.components),len(getattr(self,'_detail_placements',[])))
        for xx in [x,x+1]: self.barrel(xx,1,z,id=id+'.closed')
        self.put(x+2,1,z,'bookshelf',id+'.books')
        self.put(x+3,1,z,'oak_stairs',id+'.open_base',facing='north',half='top',shape='straight',waterlogged=False)
        self.put(x+3,2,z,'flower_pot',id+'.open_object')
        for xx in range(x,x+4):self.put(xx,3,z,'oak_slab',id+'.cap',type='top',waterlogged=False)
        for yy in [1,2,3]:
            self.panel(x-1,yy,z,'west',id+'.side')
            self.panel(x+4,yy,z,'east',id+'.side')
        self.detail_record(start,id,[x-1,1,z,x+5,4,z+1],['S01@01:49','UIMG1'],
                           ['fixed bay composition; no auto-fit or container access guarantee'],'mixed_cabinet')
