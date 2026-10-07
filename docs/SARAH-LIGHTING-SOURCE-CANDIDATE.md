# Sarah-owned lighting: source reconstruction candidate

2026-10-07. Codex offline follow-up to the extended audit. NOT IMPLEMENTED;
NOT NATIVE-VERIFIED. Independent lighting remains OPEN. No gameplay changes.

## New distinction

The Java lighting bridge registers explicit source parameters without a player
index: LightingJNI.addLight and addRoomLight. Its output/update scheduling uses
player slots. This does not prove native calculations are observer-independent,
but it means global source state should not be rejected merely because the final
render caches are player-indexed. A Sarah-owned calculation from source facts is
a different approach from reading those caches. It is an authored perception
model, not a claim to reproduce the native renderer.

## Read-only primitive candidates

Sources inspected under ignored runtime paths:
- research-adapter-20261005/fresh/zombie/iso/LightingJNI.java:
  checkLights at the source loop around280-340 reconciles activity/power and
  registers coordinate, radius, RGB and building restrictions. At361-399 room
  lights reconcile room switch state and switch electricity before registration.
  Source state is updated asynchronously with engine scheduling; isActive alone
  does not establish freshness or present electrical supply.
- research-adapter-20261005/fresh/zombie/iso/IsoCell.java:
  getLamppostPositions at2554 returns a live source stack; getLightSourceAt at2558
  searches by position. This stack is not a complete list of all illumination.
- gemini-investigation-20261007/src/zombie/iso/IsoLightSource.java:
  getters at142-200 return coordinates, RGB, radius and activity; at255-263 return
  hydro-power and building restriction. These are field reads. update(), clear()
  and setters must never be invoked by an observer. isInBounds uses chunk maps,
  and checkLights removes out-of-bounds sources, so coverage remains constrained
  by loaded-world management. No positive source means unknown, not darkness.
- research-engine-20261005/fresh/zombie/characters/IsoGameCharacter.java:
  getActiveLightItems at13179 copies held/attached emitting items into a supplied
  list. Inspect item getter semantics and use a fresh private list before any
  native admission. Installed Lua already calls item.getLightStrength.
- LightingJNI.java at410-431: single-player torch registration enumerates
  IsoPlayer.players. Sarah being an IsoPlayer does not by itself prove that her
  carried lamp is registered. Treat NPC emitted-light rendering as a separate
  native gate; do not invent a sensory light absent from the visible world.
- LightingJNI.java around640-725 passes door, curtain, barricade and window
  transmission facts to JNI. Geometric line-clear alone is not light transport.

## Minimum experiment before implementation

Start with one explicit non-hydro artificial lamp in a loaded, same-floor scene.
Read only its source getters and independently verify loaded source/target/path
coverage. Keep model state isolated from movement and Stop; no timed actions.
Compare on/off, distance, solid wall, closed/open door, curtain and unload cases.
Keep player and Sarah positions fixed when testing player-facing independence.
Calibrate any attenuation and detectable threshold against isolated observations;
never invent a threshold and call it native-compatible. The old deprecated
Java falloff is a candidate formula only, not proof of current JNI behavior.

Unknown source freshness, unsupported obstruction/transmission, missing squares,
unsupported source type or budget exhaustion must yield unknown. No-source and
artificial-light-negative results must also yield unknown while sunlight, room
lighting, vehicles, fire and torches are incomplete. Emit modeled values with
provenance separately from confirmed visual detections. Knowledge admission must
remain disabled until the model has explicit native acceptance.

## Recommendation

Investigate bounded source snapshots next, followed by one isolated calibration
batch. Do not build a speculative whole-engine light solver or repurpose player
slots. A custom model may provide useful independent perception, but cannot yet
close the lighting gate. A native bridge is another future option and would need
its own supported interface and safety evidence; none was established here.
