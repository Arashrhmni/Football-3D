"""
╔══════════════════════════════════════════════════════════╗
║    FOOTBALL 3D — Barcelona vs Real Madrid  (11v11)       ║
╠══════════════════════════════════════════════════════════╣
║  MOVE        Arrow Keys / WASD                           ║
║  SPRINT      Z  (hold)                                   ║
║  PASS        SPACE  → auto-switches to receiver          ║
║  CROSS       C  (near byline → whips ball into box)      ║
║  SHOOT       Hold F / Shift → release for power shot     ║
║  TACKLE      X  (near opponent)                          ║
║  SWITCH      TAB                                         ║
║  QUIT        ESC  only                                   ║
╠══════════════════════════════════════════════════════════╣
║  Run:  python main.py                                    ║
║  Requires: pip install pygame                            ║
╚══════════════════════════════════════════════════════════╝

File structure
──────────────
main.py       Entry point
constants.py  World dimensions, colours, physics, formation
ball.py       Ball class (physics + draw)
player.py     Player class (draw + movement)
pitch.py      Bakes the static pitch surface
ai.py         All AI: keeper, team support, CPU build-up, defence
hud.py        Heads-up display
game.py       Main game loop, input, dead-ball, goals/out
"""

import sys

try:
    import pygame
except ImportError:
    print("pygame not found.  Install it with:  pip install pygame")
    sys.exit(1)

from game import Game


if __name__ == "__main__":
    try:
        Game().run()
    except SystemExit:
        pass
