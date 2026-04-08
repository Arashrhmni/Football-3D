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


## April 2026 update

- Fixed the byline restart bug so a shot that goes out behind the defending team now becomes a **goal kick** instead of the wrong corner.
- Restart logic is now based on the teams' **current defended goals**, so it stays correct after side swaps too.
- Added a `panda3d_foundation/` folder with a small 3D migration starter. The working match is still the Pygame version; the Panda3D folder is the first step toward a real full-3D port.
