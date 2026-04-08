"""
╔══════════════════════════════════════════════════════════╗
║    FOOTBALL 3D  –  Main entry point                      ║
╠══════════════════════════════════════════════════════════╣
║  MOVE        Arrow Keys / WASD                           ║
║  SPRINT      Z  (hold)                                   ║
║  PASS        SPACE  → auto-switches to receiver          ║
║  CROSS       C  (near byline → whips ball into box)      ║
║  SHOOT       Hold F / Shift → release for power shot     ║
║  TACKLE      X  (near opponent)                          ║
║  SWITCH      TAB                                         ║
║  PAUSE       P                                           ║
║  MENU        ESC                                         ║
╚══════════════════════════════════════════════════════════╝
"""

import sys

try:
    import pygame
except ImportError:
    print("pygame not found.  Install it:  pip install pygame")
    sys.exit(1)

from constants import SCR_W, SCR_H, FPS
from menu import MainMenu, TeamSelectScreen
from game import Game


def main():
    pygame.init()
    screen = pygame.display.set_mode((SCR_W, SCR_H))
    pygame.display.set_caption("Football 3D")
    clock = pygame.time.Clock()

    while True:
        # ── Main menu ─────────────────────────────────────────────
        result = MainMenu(screen, clock).run()

        if result == 'quick_play':
            # ── Team selection ────────────────────────────────────
            teams = TeamSelectScreen(screen, clock).run()
            if teams is None:
                continue    # user pressed Back → return to main menu

            team_a_key, team_b_key = teams

            # ── Match loop (can restart) ──────────────────────────
            outcome = Game(screen, clock, team_a_key, team_b_key).run()
            # outcome == 'menu'  →  loop back to main menu


if __name__ == "__main__":
    try:
        main()
    except SystemExit:
        pass
