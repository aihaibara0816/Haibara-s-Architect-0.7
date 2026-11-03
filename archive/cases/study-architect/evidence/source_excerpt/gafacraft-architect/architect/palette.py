"""Conservative full-cube preview support, not a Minecraft registry validator."""
from .legacy import core

FULL_CUBES = {
    "smooth_quartz", "quartz_block", "smooth_stone", "stone_bricks", "stone",
    "white_concrete", "light_gray_concrete", "gray_concrete", "black_concrete",
    "green_concrete", "lime_concrete", "orange_concrete", "yellow_concrete",
    "red_concrete", "blue_concrete", "cyan_concrete", "brown_concrete",
    "red_terracotta", "terracotta", "oak_planks", "dark_oak_planks",
    "glass", "light_blue_stained_glass", "cyan_stained_glass", "gray_stained_glass",
    "black_stained_glass", "sea_lantern", "glowstone", "moss_block", "dirt",
    "polished_andesite", "polished_blackstone", "iron_block", "bricks"
}

def check_materials(materials):
    for key, material in materials.items():
        name, properties = core.parse_state(material["block_state"])
        if not name.startswith("minecraft:") or name.split(":")[1] not in FULL_CUBES or properties:
            raise ValueError(f"{key}: unsupported full-cube block/state; add an explicit geometry implementation first")
    # A read-back renderer maps by block state, so contradictory colors are rejected.
    states = {}
    for key, m in materials.items():
        if m["block_state"] in states and states[m["block_state"]] != m["preview_color"]:
            raise ValueError("One block state cannot have two preview colors")
        states[m["block_state"]] = m["preview_color"]

