# AUDIT.md

Append-only change log for AI-assisted work on this repository. See
`AGENTS.md` for the logging rules. Newest entries go at the bottom; never
edit or remove a past entry.

---

## 2026-08-20 — Added AGENTS.md and this audit log
**Agent:** Claude Code (claude-sonnet-5)
**Files:** AGENTS.md, AUDIT.md
**Change:** Created `AGENTS.md` defining conduct rules for AI agents working
  in this repo (no invented facts/APIs, no cheating fixes, no overstated
  claims, verify manually since there's no test suite) and pointing to
  `CLAUDE.md` for architecture. Created this file, `AUDIT.md`, as the
  append-only log `AGENTS.md` requires every future change to be recorded in.
**Verified:** Both files written and reviewed by re-reading their content;
  no code behavior changed by this entry, so there is nothing to run in
  `python3 main.py` to check.

## 2026-08-20 — Added the Netherlands (Eredivisie) as a playable league
**Agent:** Claude Code (claude-sonnet-5)
**Files:** constants.py, league.py, shared_ui.py
**Change:**
  - `constants.py`: added an 18-club Netherlands section to `TEAMS`
    (`godenzonen`/Ajax, `boeren`/PSV, `legioen`/Feyenoord, `kaasboeren`/AZ,
    `domstedelingen`/Utrecht, `tukkers`/Twente, `snelheid`/Vitesse,
    `superfriezen`/Heerenveen, `noorderlingen`/Groningen, `waalstad`/NEC,
    `kasteel`/Sparta Rotterdam, `ijsselvogels`/Go Ahead Eagles,
    `blauwvingers`/PEC Zwolle, `leather_city`/RKC Waalwijk,
    `fortuinzoekers`/Fortuna Sittard, `herculeans`/Heracles Almelo,
    `breda_city`/NAC Breda, `palingboeren`/Volendam), following the existing
    portfolio-safe naming convention (mix of real club nicknames and plain
    descriptive fictional names, same as the England/Spain/etc. sections).
    Added matching `TEAM_STARS` entries (1-5) balanced by rough real-world
    tier. Kit data reuses the existing `stripe`/`half_half`/`sash` flags and
    avoids pure-black (0,0,0) fills, consistent with prior fixes in this repo
    for black-box kit rendering.
  - `league.py`: added `'Netherlands': 'De Eredivisie'` to `LEAGUE_NAMES`,
    an orange accent to `LEAGUE_ACCENT`, and `'Netherlands'` to
    `LeagueSetupScreen.COUNTRY_ORDER` so it appears as a country tab in the
    League Setup screen.
  - `shared_ui.py`: added a Dutch flag (`FLAG_DATA['Netherlands']`, red/
    white/blue) used by the League and Champions League team pickers.
  - Champions League (`champions_league.py`) required no code change: its
    country list (`ALL_COUNTRIES`) is derived automatically from
    `TEAMS`, so Dutch clubs are already selectable/randomizable there.
  - Deliberately left `menu.py`'s Quick Play `COUNTRY_ORDER` (Spain/England/
    Germany only) untouched — Italy and Portugal are already excluded from
    Quick Play by the same pre-existing list, so Netherlands not appearing
    there is consistent with that existing scope, not an oversight. Flagged
    to the user rather than silently "fixed."
**Verified:** Ran (not just read) all of the following headlessly with
  `SDL_VIDEODRIVER=dummy`/`SDL_AUDIODRIVER=dummy`:
  - `python3 -m py_compile` on every touched file — all compile.
  - AST-level check confirming no duplicate keys in `TEAMS`/`TEAM_STARS`
    and that both dicts' key sets match exactly (114 entries each).
  - Instantiated `LeagueSetupScreen`, selected country `'Netherlands'`,
    built its team cards — 18 cards produced.
  - Built a `Game` between two Dutch clubs and ran 300 real update+draw
    frames (input handling, AI, ball physics, goal/out checks, HUD, kit
    rendering including the new `stripe`/`half_half`/`sash` kits) — no
    crash.
  - Built a full `LeagueState('Netherlands', ...)`, confirmed round-robin
    fixture generation (18 teams → 34 matchdays, 306 fixtures, 34 games per
    club), simulated the entire season, and printed a valid sorted final
    table.
  - Confirmed `champions_league.ALL_COUNTRIES` now includes `'Netherlands'`
    and that a random 36-team UCL draw can include Dutch clubs.
  Not run: the actual `python3 main.py` interactive GUI session (no display
  in this environment) — the above are direct, real executions of the same
  underlying game/league/UCL code paths, not mocked.

## 2026-08-20 — Fixed Quick Play only offering 3 of 6 leagues
**Agent:** Claude Code (claude-sonnet-5)
**Files:** menu.py, shared_ui.py, champions_league.py
**Change:**
  - `menu.py`: `COUNTRY_ORDER` (Quick Play's team-select screen) hardcoded
    only `['Spain', 'England', 'Germany']`, leaving Italy, Portugal, and
    Netherlands unreachable from Quick Play despite existing in `TEAMS`.
    Expanded it to all 6 countries, matching `league.py`'s order. Confirmed
    via layout-constant math that the country-tab column has enough vertical
    room (552px available vs. 420px needed for 6 tabs) before making the
    change, not just by trial and error.
  - `menu.py`: the main-menu footer string was stuck at
    `"76 clubs · 5 leagues"`, already stale before this fix (actual count is
    114 clubs / 6 leagues). Updated the string to match.
  - `shared_ui.py`: while investigating, found and pixel-measured a real
    regression from the prior Netherlands-add session — `CountryTab` draws
    its label with no truncation, so "Netherlands" (the longest name)
    overlapped the selected-state '▶' arrow by ~12px in League Setup and
    ~7px in the Champions League team picker (Quick Play's own wider tabs
    were unaffected). Flagged to the user and, on their confirmation, fixed
    it directly in the shared `CountryTab.draw()` — reserves room for the
    arrow unconditionally and trims the label to `…` if it doesn't fit,
    mirroring the existing trim-to-ellipsis pattern already used by
    `TeamCard.draw()`. Single self-contained fix; no changes needed in
    `league.py` or `champions_league.py` for this part.
  - `champions_league.py`: updated a stale docstring comment ("all 5
    leagues" → "all 6 leagues"); comment-only, no behavior change.
**Verified:** Ran (not just read), headlessly with `SDL_VIDEODRIVER=dummy`/
  `SDL_AUDIODRIVER=dummy`:
  - `python3 -m py_compile` on all touched files (plus constants.py,
    league.py, game.py, main.py) — all compile.
  - Instantiated `TeamSelectScreen` and confirmed both panels build exactly
    the 6 `COUNTRY_ORDER` tabs, in order.
  - Selected Netherlands in a Quick Play panel and confirmed 18 `TeamCard`s
    are built; drew a full frame with all 6 tabs to confirm no rendering
    crash.
  - Re-ran the exact pixel-overlap measurement that found the bug, across
    all 6 countries and all 3 screens' real tab sizes (Quick Play 184px,
    League Setup 150px, Champions League 140px) — zero overlap everywhere,
    confirmed Quick Play shows the full "Netherlands" untruncated while the
    two tighter screens correctly show "Netherl…" / "Netherla…".
  - Picked two Dutch clubs through the actual `TeamSelectScreen` selection
    path, constructed a `Game` with them, and ran 200 real update+draw
    frames with no crash.
  Not run: the interactive `python3 main.py` GUI session (no display in this
  environment) — the checks above exercise the same real code paths
  directly rather than mocking them.

## 2026-08-20 — Updated README, added .gitignore
**Agent:** Claude Code (claude-sonnet-5)
**Files:** README.md, .gitignore (new); staged (not committed) untracking of
  `__pycache__/` and `.DS_Store` via `git rm --cached`
**Change:**
  - `README.md`: corrected stale/inaccurate claims found while reviewing it —
    "60+ unique club identities" → 114 (current true count); "leagues of
    varying sizes (18 to 22 teams)" → "18 to 20" (actual per-league team
    counts: England 20, Spain 20, Italy 20, Germany 18, Portugal 18,
    Netherlands 18); "Isometric 3D projection" (in the intro and a section
    header) → "top-down orthographic projection", matching the actual
    rendering technique in `constants.py`'s `w2s()` (already noted as a
    pre-existing inaccuracy in `CLAUDE.md`). Added a "Game Modes" section
    and a Champions League features section — the README never mentioned
    UCL mode at all, despite `champions_league.py`/`main.py`'s `run_ucl()`
    having shipped it in an earlier commit.
  - Added `.gitignore` (repo had none) covering `__pycache__/`, `*.pyc`,
    packaging artifacts, common venv folders, editor folders, `.DS_Store`,
    and test/coverage artifacts — standard Python project ignores, nothing
    invented for frameworks not used here.
  - Ran `git rm -r --cached __pycache__ .DS_Store`: these were already
    *tracked* in git (11 `.pyc` files + `.DS_Store`, confirmed via
    `git ls-files` before making any change), so adding `.gitignore` alone
    would not have stopped them from showing as modified on every future
    commit. This only removes them from git's index (staged, not yet
    committed) — the files themselves are untouched on disk. Flagging this
    explicitly since it wasn't literally asked for, only implied by "update
    the gitignore file" actually working.
**Verified:** Read the full diff (`git diff --stat`) before finishing;
  confirmed no remaining "60+", "76 clubs", "5 leagues", or
  "Isometric"/"isometric" strings anywhere in `README.md` or `menu.py` via
  grep. Did not re-run the game for this entry — it's a docs/config-only
  change with no game-code behavior touched. Did not run `git commit` —
  per instructions, changes are staged/prepared only; the user commits.
