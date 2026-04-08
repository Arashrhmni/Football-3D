# Football 3D — Updated Pygame Edition

A lightweight isometric football game built with **Pygame**.

## Why I kept it on Pygame
This version stays on Pygame instead of mixing in Arcade, Ren'Py, or Panda3D. The reason is practical: this game already depends on a single active Pygame display and loop, and mixing another engine would make the runtime much more fragile.

## What's new
- radar / minimap
- stamina system for the controlled player
- new **through pass** on `Q`
- pause menu on `P`
- restart match on `R` from pause or full-time
- fullscreen toggle on `F11`
- faster visual feel with ball motion trail
- small HUD polish and control updates

## Controls
- Move: `WASD` / arrow keys
- Sprint: `Z`
- Pass: `SPACE`
- Through pass: `Q`
- Cross: `C`
- Shoot: hold `F` or `Shift`, release to shoot
- Tackle: `X`
- Switch player: `TAB`
- Pause / resume: `P`
- Restart match: `R`
- Fullscreen: `F11`
- Quit: `ESC`

## Run
```bash
pip install -r requirements.txt
python main.py
```
