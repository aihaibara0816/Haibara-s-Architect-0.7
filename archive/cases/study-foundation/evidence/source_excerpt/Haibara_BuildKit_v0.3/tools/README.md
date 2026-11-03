# Tools v0.3

voxel_core.py: basic bounded geometry and minimal typed Java structure exporter.
gafa_colonnade.py: one GAFA-specific study adapter, not a universal building model.
inspect_build.py: inherited independent subset parser/inspector/diff.
make_viewer.py + viewer_template.html: self-contained CPU Canvas viewer constructed from read-back NBT.
capture_previews.py: optional Playwright/Chromium screenshot harness.

Core generation uses Python standard library only. Screenshot harness has optional dependencies. No tool calls a model, accepts credentials or writes game saves. Unknown Minecraft shape/state behavior remains pending, not validated by the schematic renderer.
