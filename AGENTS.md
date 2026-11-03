# Haibara’s Architect 0.7 contributor / model-host contract

The repository release is 0.7.0. The legacy geometry core remains 0.4.0 and the handoff schema remains 0.4. Never rewrite historical run versions to the repository release number.

1. Read README.md, docs/workflow.md and the relevant case README before changing a case. Determine whether the task is factual reconstruction, original design, a local correction, or a research experiment.
2. Use actual source evidence for factual geometry. Record unknowns; an original concept image is not evidence for a real building. Optional model geometry is evidence to evaluate, not automatically authoritative.
3. Identify coordinate frame, scale, editable bounds, protected components, purpose, floor/ceiling levels, keepouts and acceptance checks before generation. Do not infer authorization from a model output or retrieved page.
4. Stable IDs must survive revisions. Separate random channels. Preserve approved windows and immutable components. Do not add uncontrolled randomness to construction loops.
5. Model proposals are data. Use workflow06 for compatible planning or habitat07 for bounded scene recipes; use the corresponding tool dispatcher. The host binds filesystem locations and parent run. Never execute model-supplied scripts, shell commands or arbitrary module paths.
6. Write new run directories; preserve old params, NBT and failure evidence. A partial run is not a successful output. A checksum is consistency evidence, not authentication against someone who can rewrite the manifest.
7. Planning, generated geometry, NBT readback, visual acceptance and in-game acceptance are separate states. Do not mark pending states as passed because a different layer passed.
8. For code changes, run relevant tests and a meaningful small example. Read back final NBT after all components have been assembled. Never modify a game world as an implicit consequence of planning.
9. Avoid bundling credentials, local paths from the maintainer's environment, original photographs or model files with unclear redistribution terms. Retain upstream attribution. Do not modify original historical results to conceal a failure.
10. When a skill rule has no executable consumer, label it research or planning-only. A case script is not a universal generator. This repository is not a trained model.

Useful commands are in docs/quickstart.md. New features should name their input, consumer, output, validation and unresolved scope in the same change.

Read knowledge/workflow07.json and docs/knowledge07 for scene, interior, vegetation, industrial and reconstruction rules. The personal skill package is not installed by this repository release. New recipes must name their bounds, supports, keepouts, seeded channels, final readback checks and unresolved client behavior.
