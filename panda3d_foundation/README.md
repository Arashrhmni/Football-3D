# Panda3D foundation

This is a **migration foundation**, not a full engine swap yet.

Why it is separate:
- the current football game is fully working in Pygame
- Panda3D is better for a true 3D pitch/camera pipeline, but moving the whole match loop into Panda3D is a **rewrite**, not a safe patch
- Panda3D uses a `ShowBase` application plus per-frame tasks and a scene graph, so rendering and update flow need to be moved intentionally

What is included:
- a small Panda3D scene with a pitch, goals, a ball, and simple player markers
- a per-frame task loop that updates ball/player nodes from a shared state model
- keyboard camera orbit/zoom controls as a starting point

To run later on your machine:
```bash
pip install panda3d
python panda3d_foundation/prototype_main.py
```
