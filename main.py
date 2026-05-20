"""
Football 3D  –  Main entry point
Controls: WASD/arrows Move · Z Sprint · SPACE Pass · F/Shift Shoot
          C Cross · X Tackle · TAB Switch · ESC Menu
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
from champions_league import (
    UCLTeamPickerScreen, UCLState,
    UCLLeagueHubScreen, UCLKnockoutHubScreen,
    UCLPostMatchScreen, UCLChampionScreen,
)


# ═══════════════════════════════════════════════════════════════════
#  LEAGUE SEASON FLOW  (unchanged)
# ═══════════════════════════════════════════════════════════════════
def run_league(screen, clock):
    setup = LeagueSetupScreen(screen, clock)
    ls    = setup.run()
    if ls is None:
        return

    while not ls.season_over:
        ls.simulate_matchday(skip_human=True)
        hub    = LeagueHubScreen(screen, clock, ls)
        action = hub.run()

        if action == 'back':
            return
        elif action == 'sim':
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
            if hf.home == ls.human_key:
                ta_key, tb_key = hf.home, hf.away
            else:
                ta_key, tb_key = hf.away, hf.home
            game = Game(screen, clock, ta_key, tb_key)
            home_goals, away_goals = game.run_league_match()
            if hf.home == ls.human_key:
                hg, ag = home_goals, away_goals
            else:
                hg, ag = away_goals, home_goals
            ls.apply_result(hf, hg, ag)
            PostMatchScreen(screen, clock, ls, hf).run()
            ls.advance_matchday()

    SeasonEndScreen(screen, clock, ls).run()


# ═══════════════════════════════════════════════════════════════════
#  PLAY A SINGLE MATCH (UCL helper)
# ═══════════════════════════════════════════════════════════════════
def _play_match(screen, clock, ta_key, tb_key, context=""):
    """Play a match, show post-match screen. Returns (home_goals, away_goals)."""
    game = Game(screen, clock, ta_key, tb_key)
    hg, ag = game.run_league_match()
    UCLPostMatchScreen(screen, clock, ta_key, tb_key, hg, ag, context).run()
    return hg, ag


# ═══════════════════════════════════════════════════════════════════
#  KNOCKOUT ROUND HELPER
# ═══════════════════════════════════════════════════════════════════
def _run_knockout_round(screen, clock, state):
    """
    Runs one knockout round (play-off, R16, QF, SF, or Final).
    Handles the human's tie interactively; simulates all others.
    Returns 'back' to abandon, or 'done' when round is complete.
    """
    while True:
        ties = state.current_round_ties()
        if not ties:
            return 'done'
        all_done = all(t is not None and t.done for t in ties)
        if all_done:
            return 'done'

        hub    = UCLKnockoutHubScreen(screen, clock, state)
        action = hub.run()

        if action == 'back':
            return 'back'

        elif action == 'sim':
            # Simulate all undone ties (including human's)
            for tie in ties:
                if tie and not tie.done:
                    tie.simulate_remaining()

        elif action == 'play':
            human_tie = state.human_knockout_tie()
            if human_tie is None or human_tie.done:
                continue

            rname = __import__('champions_league').ROUND_NAMES.get(state.round, state.round)

            # Leg 1
            if not human_tie.played_leg1:
                ta, tb = human_tie.team_a, human_tie.team_b
                hg, ag = _play_match(screen, clock, ta, tb, f"{rname} — Leg 1")
                human_tie.set_leg_result(1, hg, ag)
                # Simulate all other leg-1s
                for tie in ties:
                    if tie and not tie.played_leg1 and tie is not human_tie:
                        tie.leg1.simulate(); tie.played_leg1 = True

            # Leg 2 (if two-legged and leg 1 done)
            elif human_tie.two_legs and not human_tie.played_leg2:
                ta, tb = human_tie.leg2.home, human_tie.leg2.away
                hg, ag = _play_match(screen, clock, ta, tb, f"{rname} — Leg 2")
                human_tie.set_leg_result(2, hg, ag)
                human_tie.determine_winner()
                # Simulate remaining ties
                for tie in ties:
                    if tie and not tie.done and tie is not human_tie:
                        tie.simulate_remaining()

            elif not human_tie.two_legs:
                ta, tb = human_tie.team_a, human_tie.team_b
                hg, ag = _play_match(screen, clock, ta, tb, f"{rname}")
                human_tie.set_leg_result(1, hg, ag)
                human_tie.played_leg1 = True
                human_tie.determine_winner()
                for tie in ties:
                    if tie and not tie.done and tie is not human_tie:
                        tie.simulate_remaining()


# ═══════════════════════════════════════════════════════════════════
#  CHAMPIONS LEAGUE FLOW
# ═══════════════════════════════════════════════════════════════════
def run_ucl(screen, clock):
    # 1. Pick 36 teams + choose which one to manage
    picker = UCLTeamPickerScreen(screen, clock)
    result = picker.run()
    if result is None:
        return
    participants, human_key = result

    state = UCLState(participants, human_key)

    # 2. League Phase (8 matchdays)
    while not state.league_done:
        state.simulate_league_matchday(skip_human=True)
        hub    = UCLLeagueHubScreen(screen, clock, state)
        action = hub.run()

        if action == 'back':
            return

        elif action == 'sim':
            hf = state.human_league_fixture()
            if hf and not hf.played:
                hg, ag = hf.simulate()
                state.apply_league_result(hf, hg, ag)
                UCLPostMatchScreen(screen, clock, hf.home, hf.away, hg, ag,
                                   f"League Phase — MD {state.league_matchday}").run()
            state.advance_league_matchday()

        elif action == 'play':
            hf = state.human_league_fixture()
            if hf is None:
                state.advance_league_matchday()
                continue
            ta_key = hf.home; tb_key = hf.away
            hg, ag = _play_match(screen, clock, ta_key, tb_key,
                                  f"League Phase — MD {state.league_matchday}")
            state.apply_league_result(hf, hg, ag)
            state.advance_league_matchday()

    # 3. Knockout rounds in sequence
    ROUND_SEQUENCE = ['playoff', 'r16', 'qf', 'sf', 'final']

    for rnd in ROUND_SEQUENCE:
        # If human was eliminated already, fast-forward this round
        human_alive = any(
            human_key in (t.team_a, t.team_b)
            for t in state.current_round_ties() if t
        )

        if not human_alive:
            # Simulate whole round instantly
            for tie in state.current_round_ties():
                if tie and not tie.done:
                    tie.simulate_remaining()
        else:
            outcome = _run_knockout_round(screen, clock, state)
            if outcome == 'back':
                return

        # Advance to next round
        if rnd == 'playoff': state.finish_playoff()
        elif rnd == 'r16':   state.finish_r16()
        elif rnd == 'qf':    state.finish_qf()
        elif rnd == 'sf':    state.finish_sf()
        elif rnd == 'final':
            # Determine final winner
            if state.final_tie and not state.final_tie.winner:
                state.final_tie.determine_winner()
            state.finish_final()
            break

    # 4. Champion screen
    UCLChampionScreen(screen, clock, state).run()


# ═══════════════════════════════════════════════════════════════════
#  MAIN
# ═══════════════════════════════════════════════════════════════════
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

        elif result == 'ucl':
            run_ucl(screen, clock)


if __name__ == "__main__":
    try:
        main()
    except SystemExit:
        pass
