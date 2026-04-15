"""
Football 3D  –  Main entry point
Controls: WASD/arrows Move · Z Sprint · SPACE Pass · F/Shift Shoot
          C Cross · X Tackle · TAB Switch · P Pause · ESC Menu
"""
import sys
try:
    import pygame
except ImportError:
    print("pygame not found.  pip install pygame")
    sys.exit(1)

from constants import SCR_W, SCR_H, FPS
from menu   import MainMenu, TeamSelectScreen
from game   import Game
from league import (LeagueSetupScreen, LeagueHubScreen,
                    PostMatchScreen, SeasonEndScreen)


def run_league(screen, clock):
    """Full league season flow."""
    # 1. Setup: pick country + team
    setup = LeagueSetupScreen(screen, clock)
    ls    = setup.run()
    if ls is None:
        return   # back to main menu

    # 2. Season loop
    while not ls.season_over:
        # Simulate all CPU matches on this matchday first
        ls.simulate_matchday(skip_human=True)

        # Show hub (standings + fixtures)
        hub    = LeagueHubScreen(screen, clock, ls)
        action = hub.run()

        if action == 'back':
            return   # abandon season → main menu

        elif action == 'sim':
            # Simulate human's match too (user chose to skip it)
            hf = ls.human_fixture_today()
            if hf and not hf.played:
                hg, ag = hf.simulate()
                ls.apply_result(hf, hg, ag)
                PostMatchScreen(screen, clock, ls, hf).run()
            ls.advance_matchday()

        elif action == 'play':
            hf = ls.human_fixture_today()
            if hf is None:
                ls.advance_matchday()
                continue

            # Determine if human is home or away
            if hf.home == ls.human_key:
                team_a_key, team_b_key = hf.home, hf.away
            else:
                team_a_key, team_b_key = hf.away, hf.home

            # Play the match
            game = Game(screen, clock, team_a_key, team_b_key)
            home_goals, away_goals = game.run_league_match()

            # Translate score back to fixture orientation
            if hf.home == ls.human_key:
                hg, ag = home_goals, away_goals
            else:
                hg, ag = away_goals, home_goals

            ls.apply_result(hf, hg, ag)
            PostMatchScreen(screen, clock, ls, hf).run()
            ls.advance_matchday()

    # 3. Season over
    SeasonEndScreen(screen, clock, ls).run()


def main():
    pygame.init()
    screen = pygame.display.set_mode((SCR_W, SCR_H))
    pygame.display.set_caption("Football 3D")
    clock  = pygame.time.Clock()

    while True:
        result = MainMenu(screen, clock).run()

        if result == 'quick_play':
            teams = TeamSelectScreen(screen, clock).run()
            if teams is None:
                continue
            team_a_key, team_b_key = teams
            Game(screen, clock, team_a_key, team_b_key).run()

        elif result == 'league':
            run_league(screen, clock)


if __name__ == "__main__":
    try:
        main()
    except SystemExit:
        pass
