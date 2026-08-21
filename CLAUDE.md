# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this is

Football 3D is an 11v11 football (soccer) simulation with top-down orthographic
projection, autonomous agent AI, and a full League + Champions League season
framework. Built from scratch in Python + Pygame — no game engine, no external
assets (all rendering is procedural via `pygame.draw` / surfaces).

## Commands

```bash
pip install -r requirements.txt   # only dependency: pygame>=2.0.0
python3 main.py                   # run the game
```

There is no test suite, linter, or build step configured in this repo — don't
invent commands for them. Validate changes by running the game and exercising
the affected screen/flow manually (see Controls in README.md).

## Architecture

### Entry flow (`main.py`)
`main()` drives a top-level menu loop (`MainMenu`) that dispatches into one of
three modes, each returning to the menu when done:
- **Quick Play** — `TeamSelectScreen` → `Game(...).run()`
- **League** — `run_league()`: `LeagueSetupScreen` → loop over `LeagueHubScreen`
  (sim/play/back) → `Game.run_league_match()` per human fixture → `PostMatchScreen`
  → `SeasonEndScreen`
- **Champions League** — `run_ucl()`: `UCLTeamPickerScreen` → league-phase loop
  (`UCLLeagueHubScreen`) → knockout rounds (`_run_knockout_round`, playoff → R16
  → QF → SF → final, each potentially two-legged) → `UCLChampionScreen`

`Game` is reused across all three modes: `run()` is the standalone quick-play
loop (returns to menu), `run_league_match()` is the variant used when a match
is embedded inside a season (returns final score instead of looping to menu).

### Coordinate system (`constants.py`)
Two coordinate spaces are used everywhere:
- **World space** `(wx, wy, wz)` — pitch is `W_W x W_H` world units, origin
  top-left, `wz` is height off the ground (ball arcs, animation "hop").
- **Screen space** — produced from world space via `w2s(wx, wy, wz)`, a simple
  top-down orthographic transform (`PITCH_SCALE`, `ISO_CX/CY`, `Z_LIFT`). This
  is *not* isometric despite older comments/README wording — it's a clean
  bird's-eye view; `wz` only lifts objects vertically on screen, it doesn't
  skew the pitch.

All entities (`Player`, `Ball`) store position in world space and are
projected to screen space only at draw time. Physics/AI helpers (`d2`, `n2`,
`clamp`, `lerpc`) operate in world space and live in `constants.py`.

`constants.py` also holds the full `TEAMS` dict (114 clubs across 6 leagues —
England, Spain, Germany, Italy, Portugal, Netherlands — with fictional names
for portfolio-safe branding — e.g. `the_gunners` = Arsenal, `sky_blues` = Man
City), `TEAM_STARS`, and `get_stars()` / `ai_params(stars)` which scale AI
behavior (speed, reaction, pass/shoot/tackle chances) by a club's star rating.
When adding a team, follow the existing dict shape (`name`, `country`, kit
colors, `skin`/`hair`, `hud_col`, optional `half_half`/`sash`/style flags).

### Per-match simulation (`game.py`, `ai.py`, `player.py`, `ball.py`)
`Game` owns two teams (`self.ta`, `self.tb`, lists of `Player`), the `Ball`,
and a `match_state` string machine (`'playing'`, `'paused'`, `'half_time'`,
`'full_time'`, `'quit_to_menu'`, dead-ball states). Each frame in `run()`:
handle input → advance AI (`cpu_ai`, `cpu_attacking_shape`, `team_a_support`
from `ai.py`) → `ball.update()` → goal/out-of-bounds checks → possession
pickup → draw scene + HUD → flip.

- `ai.py` — all non-human team behavior: pass-target scoring, support
  positioning, tackling, shooting decisions. Behavior is parameterized by the
  `ai_params(stars)` dict rather than hardcoded per team.
- `player.py` — procedural sprite rendering (drawn onto a transparent
  mini-canvas, then scaled — avoids hard edges/black boxes) plus sine-wave
  limb animation driven by velocity, and player physics/movement.
- `ball.py` — ball physics: friction, gravity, height (`wz`) for lobbed
  passes/crosses/shots, and possession snapping to the carrying player.
- `pitch.py` — bakes the static pitch surface (grass texture, lines, boxes,
  arcs) once at startup rather than redrawing it every frame.
- `hud.py` — scoreboard/timer overlay, reads state off the `Game` instance.

### Menus & season systems (`menu.py`, `league.py`, `champions_league.py`, `shared_ui.py`)
`shared_ui.py` is the shared visual toolkit (stadium background, particles,
gold dividers, `FancyBtn`, `CountryTab`, `TeamCard`, flags) used by all three
screen modules so menus/league/UCL share one visual language — add new shared
widgets there rather than duplicating drawing code per module.

- `league.py` — single-league season: round-robin "circle method" fixture
  generation, `TeamRecord` standings (points → goal difference → goals for),
  matchday simulation for non-human fixtures, hub/post-match/season-end screens.
- `champions_league.py` — modern 36-team UCL format: single league phase (8
  matches, varied opponents) → top 8 auto-qualify, 9–24 go to a 2-legged
  playoff, bottom 12 eliminated → R16 (2-legged) → QF/SF/Final (single-leg).
  `UCLState` tracks the whole competition; ties can be single- or two-legged
  (`tie.two_legs`) and simulate via `tie.simulate_remaining()` when the human
  isn't involved.

Both season systems always simulate non-human fixtures automatically and only
hand control to `Game` for the human's own matches, then return to the hub.

## Conduct rules (`AGENTS.md`)

`AGENTS.md` has mandatory rules for this repo, most importantly: every code,
data, or doc change must get a newest-at-the-bottom entry appended to
`AUDIT.md` (summary, files touched, what/why, and exactly how it was
verified) in the same session as the change. Read `AGENTS.md` before making
changes — don't skip logging.
