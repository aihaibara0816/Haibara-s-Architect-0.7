# 当前交付：木漏日町山溪版 T07

请先阅读 [README_TERRAIN.md](README_TERRAIN.md)。以下保留 J03 平地街区的原始说明，作为历史基线。

---

# 木漏日町 · Komorebi09

HAF 0.4 / bounded original neighborhood case / final J03 / 2026-10-30.

18 buildings: 4 large shop-houses based on the accepted Machiya08 M08, 6 new compact two-storey homes/shops, and 8 new single-storey specialty buildings. Two streets and cross alleys lead to an east-side creek, two bridges and bank walks. Every building has an authored interior. This is a three-family case adapter, not 18 independent generative design systems.

Final size: 164 × 24 × 112 (X,Y,Z). Final NBT SHA-256: `06b8a2ff23c5aea0692dcd33f4111396a8e09352a4ee1b2162fb0a14276205e1`.

## Play

Use the separately supplied `Komorebi09_World_1.21.1.zip`. Extract `Komorebi09_1.21.1` into Minecraft Java 1.21.1 `saves`. No required mods. Spawn: -15 65 -13. The world offset is [-82,62,-56]. The standalone HTML gives a separate entrance teleport command for all 18 buildings and 104 previews. Time, weather and random block ticks are paused; `/time set night` switches the display time. Containers are empty. Decorative seats/baths do not provide extra gameplay.

The NBT is sparse: clear its full bounding box before applying it to an existing scene. The prepared world is easier to use and includes paintings as entities.

## Reproduce

Python 3.11+ with dependencies in `requirements.txt`. Commands below run from this project root; choose unused run names (the generator intentionally refuses to overwrite a run).

```bash
python -m pip install -r requirements.txt
python src/build_town.py Replay --seed 1145
python src/audit_town.py Replay
python src/world_town.py Replay world_Replay
python src/build_town.py SeedB --seed 2718
python src/audit_town.py SeedB
```

`build_town.py` and `audit_town.py` do not download assets. Geometry, placements, doors, stairs and light positions are fixed for this case. The stable-ID random streams alter safe tree pockets/heights/canopies, groundcover patches/species and potted plants. Seed 1145 reproduces the final NBT bytes; seed 2718 changes 6,987 cells, all within the planting scope, and also passes the geometry audit. It is not an arbitrary street-layout generator.

## Render and report

Official Java 1.21.1 models/textures are not redistributed in this package. `assets/vanilla_source.json` and `src/fetch_vanilla_assets.py` document the official source and hash. Set `ROOM06_MC_ASSETS` to an extracted `assets/minecraft` directory. Offline rendering needs a Linux EGL/OpenGL 3.3 context (`libEGL.so.1`, for example Mesa with surfaceless rendering) and the Python dependencies above. Node.js is only needed for the HTML behavior harness. Existing 104 PNGs can be reviewed without renderer dependencies.

```bash
python src/random_check.py J03 Replay SeedB
python src/diagram_town.py J03
python src/render_town.py J03 overview
python src/render_town.py J03 streets
python src/render_town.py J03 B01
```

Render B02 through B18 in the same way, then `creek`. Render groups sequentially because they share the temporary scene mesh. Overview texture sampling is capped at 3 subdivisions, street views at 4, building/creek close views at 12; model geometry remains from the source NBT. Building views crop surrounding blocks but retain the building's walls, roof and ceiling. `all_views.json` combines the group reports; `render_report.json` alone only describes the last group.

```bash
python src/report_town.py J03 /path/to/Komorebi09.html /path/to/Komorebi09_World_1.21.1.zip
python src/check_report.py J03 /path/to/Komorebi09.html /tmp/komorebi_qa /path/to/Komorebi09_World_1.21.1.zip
node src/check_report_dom.cjs /tmp/komorebi_qa runs/J03/report_check.json
```

## Checks and limits

- 18/18 ground entrances, 285 usage points and 10 stair flights pass the approximate 0.6 × 1.8 player-body checks. Doors are treated open. This does not replace client collision/interaction checks.
- Creek containment, plant support, double-plant pairing, persistent leaves, bed pairing, block entities and rotated painting supports are checked.
- Java 1.21.1 world readback checks 589,824 cells with zero mismatch, plus 335 block-entity and 12 painting entity payloads. Light recalculates when opened in game.
- 104 preview PNGs record the final NBT hash and camera. The HTML embeds these as compressed WebP plus one exact exploded-floor SVG, and contains the world/NBT/design-data downloads.
- The preview is an offline rendering, not a Minecraft screenshot. Signs, banners, beds and water have some renderer simplifications. Cold/warm block colors do not create colored light propagation in vanilla Minecraft.
- No Minecraft client execution occurred in this environment. `game` and final aesthetic acceptance remain pending. Do not mark earlier interior complaints as closed by the geometry checks.

## History and references

J01 introduced 18 buildings, creek and layered planting; its first view showed excessive spacing. J02 reduced the scene to 164 × 112 and tightened the lots. J03 added side windows and thin shutters to the 14 smaller modules so creek/alleys face windows rather than blank walls. Final M08 is preserved in `input/`; this case does not overwrite it.

The previous Freedom #80 public-image and #104 excerpt observation record is retained in `input/Freedom_frontage_research.json`. No new video watching or full tutorial reproduction is claimed this round. Street layout, rooms and landscape are authored adaptations. This work updates a case project, not a model's trained weights or an installed skill.

`manifest.json` records packaged file SHA-256 hashes. Heavy temporary mesh outputs, cache files and official game assets are deliberately excluded.
