"""
champions_league.py
═══════════════════
Modern UEFA Champions League format (2024-25 onwards):
  • 36 teams in a single league phase (8 matches each, varied opponents)
  • Top 8 qualify directly for Round of 16
  • Teams 9-24 enter a 2-legged Knockout Play-off round
  • Bottom 12 are eliminated
  • Round of 16 → Quarter-finals → Semi-finals → Final (single leg except R16 2-leg)

Human player:
  • Can pick 1–36 teams manually; rest are randomised from all 5 leagues
  • Chooses which team they play AS
  • Simulates all non-human matches; plays their own
"""

import pygame
import sys
import math
import random
import itertools

from constants import SCR_W, SCR_H, FPS, TEAMS, get_stars, ai_params
from shared_ui import (
    GOLD, WHITE, GREY, PANEL_BG,
    draw_stadium_bg, make_particles, update_particles, draw_particles,
    draw_football, draw_kit, draw_flag, glass_panel, gold_divider,
    draw_page_title, FancyBtn, CountryTab, TeamCard, FLAG_DATA
)

# ── UCL palette ──────────────────────────────────────────────────
UCL_BLUE   = ( 0,  30, 100)
UCL_DARK   = ( 2,   8,  28)
UCL_STAR   = (255, 215,  0)
UCL_SILVER = (180, 190, 210)
UCL_RED    = (200,  20,  20)
UCL_GREEN  = ( 20, 160,  60)

UCL_TOTAL_TEAMS = 36

ALL_TEAM_KEYS = list(TEAMS.keys())
ALL_COUNTRIES = sorted(set(v['country'] for v in TEAMS.values()))

ROUND_NAMES = {
    'league':  'League Phase',
    'playoff': 'Knockout Play-offs',
    'r16':     'Round of 16',
    'qf':      'Quarter-finals',
    'sf':      'Semi-finals',
    'final':   'Final',
}


def draw_stars(surf, x, y, stars, size=8, gap=2):
    """Draw 1-5 gold/grey stars at (x,y)."""
    col_on  = (255, 210, 0)
    col_off = (50, 55, 75)
    for i in range(5):
        c = col_on if i < stars else col_off
        pygame.draw.circle(surf, c, (x + i*(size+gap) + size//2, y + size//2), size//2)


# ═══════════════════════════════════════════════════════════════════
# DATA MODELS
# ═══════════════════════════════════════════════════════════════════
class UCLTeamRecord:
    def __init__(self, key):
        self.key = key
        self.name = TEAMS[key]['name']
        self.col  = TEAMS[key]['hud_col']
        self.P = self.W = self.D = self.L = 0
        self.GF = self.GA = self.pts = 0
        self.results = []

    @property
    def GD(self): return self.GF - self.GA

    def add_result(self, gf, ga):
        self.P += 1; self.GF += gf; self.GA += ga
        if gf > ga:
            self.W += 1; self.pts += 3; self.results.append('W')
        elif gf == ga:
            self.D += 1; self.pts += 1; self.results.append('D')
        else:
            self.L += 1; self.results.append('L')


class UCLFixture:
    def __init__(self, home, away, matchday=0, leg=1):
        self.home = home; self.away = away
        self.matchday = matchday; self.leg = leg
        self.played = False
        self.home_goals = self.away_goals = 0

    def simulate(self):
        """
        Score simulation weighted by star ratings.
        A 5-star team vs a 1-star team will win much more often
        and score more goals. Poisson-like sampling using star-adjusted λ.
        """
        h_stars = get_stars(self.home)
        a_stars = get_stars(self.away)
        # λ for Poisson-ish goal distribution
        # Base λ ~1.3 goals per team; scale by relative star power
        h_lam = 0.6 + (h_stars / 5.0) * 2.2 - (a_stars / 5.0) * 0.8
        a_lam = 0.6 + (a_stars / 5.0) * 2.2 - (h_stars / 5.0) * 0.8
        h_lam = max(0.15, h_lam)
        a_lam = max(0.15, a_lam)
        # Home advantage
        h_lam *= 1.12
        # Sample goals (Poisson approximation: sum of uniform draws)
        def poisson_approx(lam):
            L = math.exp(-lam); k = 0; p = 1.0
            while p > L:
                p *= random.random(); k += 1
            return max(0, k - 1)
        h = poisson_approx(h_lam)
        a = poisson_approx(a_lam)
        self.home_goals = h; self.away_goals = a
        self.played = True
        return h, a

    def set_result(self, h, a):
        self.home_goals = h; self.away_goals = a; self.played = True


class KnockoutTie:
    def __init__(self, team_a, team_b, two_legs=True):
        self.team_a = team_a; self.team_b = team_b
        self.two_legs = two_legs
        self.leg1 = UCLFixture(team_a, team_b, leg=1)
        self.leg2 = UCLFixture(team_b, team_a, leg=2) if two_legs else None
        self.winner = None
        self.played_leg1 = False
        self.played_leg2 = False

    @property
    def done(self):
        if self.two_legs:
            return self.played_leg1 and self.played_leg2
        return self.played_leg1

    def aggregate(self):
        if not self.played_leg1:
            return 0, 0
        a1, b1 = self.leg1.home_goals, self.leg1.away_goals
        if self.two_legs and self.played_leg2:
            a2, b2 = self.leg2.away_goals, self.leg2.home_goals
            return a1 + a2, b1 + b2
        return a1, b1

    def determine_winner(self):
        agg_a, agg_b = self.aggregate()
        if agg_a > agg_b:
            self.winner = self.team_a
        elif agg_b > agg_a:
            self.winner = self.team_b
        else:
            self.winner = random.choice([self.team_a, self.team_b])
        return self.winner

    def simulate_remaining(self):
        if not self.played_leg1:
            self.leg1.simulate(); self.played_leg1 = True
        if self.two_legs and not self.played_leg2:
            self.leg2.simulate(); self.played_leg2 = True
        return self.determine_winner()

    def set_leg_result(self, leg, h, a):
        if leg == 1:
            self.leg1.set_result(h, a); self.played_leg1 = True
        else:
            self.leg2.set_result(h, a); self.played_leg2 = True


class UCLState:
    def __init__(self, participant_keys, human_key):
        assert len(participant_keys) == UCL_TOTAL_TEAMS
        self.all_teams = participant_keys[:]
        self.human_key = human_key
        self.records   = {k: UCLTeamRecord(k) for k in participant_keys}

        self.league_fixtures = []
        self.league_matchday = 1
        self.league_done     = False
        self._gen_league_fixtures()

        self.round       = 'league'
        self.playoff_ties = []
        self.r16_ties    = []
        self.qf_ties     = []
        self.sf_ties     = []
        self.final_tie   = None
        self.champion    = None
        self._direct_r16 = []

    def _gen_league_fixtures(self):
        teams = self.all_teams[:]
        random.shuffle(teams)
        padded = teams[:]
        if len(padded) % 2 == 1:
            padded.append('__bye__')
        half = len(padded) // 2
        rotated = padded[1:]
        rounds_needed = 8
        home_count = {k: 0 for k in teams}
        opponents  = {k: set() for k in teams}
        schedule   = []

        for rnd in range(len(padded) - 1):
            rot = rotated[rnd:] + rotated[:rnd]
            pairs = [(padded[0], rot[0])] + \
                    [(rot[i], rot[half-1-i]) for i in range(1, half)]
            if rnd < rounds_needed:
                for a, b in pairs:
                    if '__bye__' in (a, b): continue
                    if b in opponents[a]: continue
                    if home_count[a] <= home_count[b]:
                        home, away = a, b
                    else:
                        home, away = b, a
                    home_count[home] += 1
                    opponents[a].add(b); opponents[b].add(a)
                    schedule.append((home, away, rnd + 1))

        random.shuffle(schedule)
        self.league_fixtures = [UCLFixture(h, a, md) for h, a, md in schedule]
        self.total_league_matchdays = rounds_needed

    def sorted_table(self):
        recs = list(self.records.values())
        recs.sort(key=lambda r: (-r.pts, -r.GD, -r.GF, r.name))
        return recs

    def current_league_fixtures(self):
        return [f for f in self.league_fixtures
                if f.matchday == self.league_matchday and not f.played]

    def human_league_fixture(self):
        for f in self.current_league_fixtures():
            if self.human_key in (f.home, f.away):
                return f
        return None

    def simulate_league_matchday(self, skip_human=True):
        for f in self.current_league_fixtures():
            if skip_human and self.human_key in (f.home, f.away): continue
            h, a = f.simulate()
            self.records[f.home].add_result(h, a)
            self.records[f.away].add_result(a, h)

    def apply_league_result(self, fix, hg, ag):
        fix.set_result(hg, ag)
        self.records[fix.home].add_result(hg, ag)
        self.records[fix.away].add_result(ag, hg)

    def advance_league_matchday(self):
        self.league_matchday += 1
        if self.league_matchday > self.total_league_matchdays:
            self.league_done = True
            self._build_knockout_bracket()

    def _build_knockout_bracket(self):
        table = self.sorted_table()
        self._direct_r16    = [r.key for r in table[:8]]
        playoff_teams       = [r.key for r in table[8:24]]
        self.eliminated_league = [r.key for r in table[24:]]
        random.shuffle(playoff_teams)
        self.playoff_ties = []
        half = len(playoff_teams) // 2
        for i in range(half):
            self.playoff_ties.append(
                KnockoutTie(playoff_teams[i], playoff_teams[-(i+1)], two_legs=True))
        self.round = 'playoff'

    def finish_playoff(self):
        winners = [t.winner for t in self.playoff_ties]
        all_r16 = self._direct_r16 + winners
        random.shuffle(all_r16)
        self.r16_ties = []
        for i in range(0, len(all_r16), 2):
            self.r16_ties.append(KnockoutTie(all_r16[i], all_r16[i+1], two_legs=True))
        self.round = 'r16'

    def finish_r16(self):
        winners = [t.winner for t in self.r16_ties]
        random.shuffle(winners)
        self.qf_ties = []
        for i in range(0, len(winners), 2):
            self.qf_ties.append(KnockoutTie(winners[i], winners[i+1], two_legs=False))
        self.round = 'qf'

    def finish_qf(self):
        winners = [t.winner for t in self.qf_ties]
        random.shuffle(winners)
        self.sf_ties = []
        for i in range(0, len(winners), 2):
            self.sf_ties.append(KnockoutTie(winners[i], winners[i+1], two_legs=False))
        self.round = 'sf'

    def finish_sf(self):
        winners = [t.winner for t in self.sf_ties]
        self.final_tie = KnockoutTie(winners[0], winners[1], two_legs=False)
        self.round = 'final'

    def finish_final(self):
        self.champion = self.final_tie.winner
        self.round = 'done'

    def current_round_ties(self):
        return {
            'playoff': self.playoff_ties,
            'r16':     self.r16_ties,
            'qf':      self.qf_ties,
            'sf':      self.sf_ties,
            'final':   [self.final_tie] if self.final_tie else [],
        }.get(self.round, [])

    def human_knockout_tie(self):
        for tie in self.current_round_ties():
            if tie and self.human_key in (tie.team_a, tie.team_b):
                return tie
        return None


# ═══════════════════════════════════════════════════════════════════
# TEAM PICKER SCREEN
# ═══════════════════════════════════════════════════════════════════
class UCLTeamPickerScreen:
    SLOT_W, SLOT_H = 200, 42
    SLOT_GAP = 6
    SLOTS_PER_COL = 18
    BROWSER_CARD_X = 162
    BROWSER_CARD_W = 340   # fixed width for card area

    def __init__(self, screen, clock):
        self.screen = screen; self.clock = clock
        self.f_title  = pygame.font.SysFont("Georgia", 36, bold=True)
        self.f_sub    = pygame.font.SysFont("Georgia", 13, italic=True)
        self.f_med    = pygame.font.SysFont("Arial",   13, bold=True)
        self.f_small  = pygame.font.SysFont("Arial",   11)
        self.f_btn    = pygame.font.SysFont("Georgia", 19, bold=True)
        self.f_ctry   = pygame.font.SysFont("Arial",   12, bold=True)
        self.f_card   = pygame.font.SysFont("Arial",   10, bold=True)
        self.f_fsmall = pygame.font.SysFont("Arial",    9)

        self.slots = [None] * UCL_TOTAL_TEAMS
        self._sel_country = None
        self._team_cards  = []
        self._browser_scroll = 0

        self.SLOTS_X = self.BROWSER_CARD_X + self.BROWSER_CARD_W + 20
        self.SLOTS_Y = 105

        # Country tabs
        BROWSER_X, BROWSER_Y = 14, 105
        ty = BROWSER_Y
        self._country_tabs = []
        for ctry in ALL_COUNTRIES:
            self._country_tabs.append(
                CountryTab(ctry, (BROWSER_X, ty, 140, 52), self.f_ctry))
            ty += 58

        bh = 46
        self.btn_rand  = FancyBtn("🎲 RANDOMISE REST",
            (14, SCR_H-bh*2-22, 240, bh), self.f_btn,
            bg=(18,28,80), bg_h=(30,50,140), tc=UCL_STAR, bc=(60,90,200))
        self.btn_clear = FancyBtn("✕ CLEAR ALL",
            (14, SCR_H-bh-10, 240, bh), self.f_btn,
            bg=(60,14,14), bg_h=(100,24,24), tc=WHITE, bc=(160,30,30))
        self.btn_next  = FancyBtn("▶ CHOOSE YOUR CLUB",
            (SCR_W-340-14, SCR_H-bh-10, 340, bh), self.f_btn,
            bg=(16,76,34), bg_h=(26,116,50), tc=GOLD, bc=(40,155,65), enabled=False)
        self.btn_back  = FancyBtn("← BACK",
            (SCR_W-340-14, SCR_H-bh*2-22, 160, bh), self.f_btn,
            bg=(24,24,50), bg_h=(40,40,88), tc=WHITE)
        self._t = 0.0
        self._parts = make_particles(30, SCR_W, SCR_H)

    def _rebuild_cards(self):
        self._team_cards = []; self._browser_scroll = 0
        if not self._sel_country: return
        used = set(s for s in self.slots if s is not None)
        keys = [k for k in ALL_TEAM_KEYS
                if TEAMS[k]['country'] == self._sel_country and k not in used]
        bx = self.BROWSER_CARD_X; by = 105
        cw, ch = TeamCard.W, TeamCard.H; g = 8
        cols = max(1, (self.BROWSER_CARD_W + g) // (cw + g))
        for i, k in enumerate(keys):
            c2 = i % cols; r2 = i // cols
            x = bx + c2*(cw+g); y = by + r2*(ch+g)
            self._team_cards.append(TeamCard(k, (x, y, cw, ch), self.f_card, self.f_fsmall))

    def _card_area(self):
        return pygame.Rect(self.BROWSER_CARD_X, 105, self.BROWSER_CARD_W, SCR_H-105-110)

    def _max_card_scroll(self):
        if not self._team_cards: return 0
        return max(0, max(c.rect.bottom for c in self._team_cards) -
                   (105 + self._card_area().h))

    def _slot_rect(self, idx):
        col = idx // self.SLOTS_PER_COL
        row = idx % self.SLOTS_PER_COL
        x = self.SLOTS_X + col*(self.SLOT_W + self.SLOT_GAP)
        y = self.SLOTS_Y + row*(self.SLOT_H + self.SLOT_GAP)
        return pygame.Rect(x, y, self.SLOT_W, self.SLOT_H)

    def _first_empty(self):
        for i, s in enumerate(self.slots):
            if s is None: return i
        return -1

    def _filled(self): return sum(1 for s in self.slots if s is not None)

    def _update_btn(self): self.btn_next.enabled = (self._filled() > 0)

    def _randomise_rest(self):
        used = set(s for s in self.slots if s is not None)
        pool = [k for k in ALL_TEAM_KEYS if k not in used]
        random.shuffle(pool)
        for i, s in enumerate(self.slots):
            if s is None and pool:
                self.slots[i] = pool.pop(0)
        self._rebuild_cards(); self._update_btn()

    def _clear_all(self):
        self.slots = [None]*UCL_TOTAL_TEAMS
        self._rebuild_cards(); self._update_btn()

    def handle_event(self, ev):
        ca = self._card_area()
        if ev.type == pygame.MOUSEBUTTONDOWN:
            mx, my = ev.pos
            if ev.button == 4 and ca.collidepoint(mx, my):
                self._browser_scroll = max(0, self._browser_scroll-36)
            elif ev.button == 5 and ca.collidepoint(mx, my):
                self._browser_scroll = min(self._max_card_scroll(), self._browser_scroll+36)
            elif ev.button == 1:
                for tab in self._country_tabs:
                    if tab.clicked(mx, my):
                        if tab.country != self._sel_country:
                            self._sel_country = tab.country
                            self._rebuild_cards()
                        for t in self._country_tabs: t.selected = (t.country==tab.country)
                        return
                for card in self._team_cards:
                    cr = pygame.Rect(card.rect.x, card.rect.y-self._browser_scroll,
                                     card.rect.w, card.rect.h)
                    if cr.collidepoint(mx,my) and ca.collidepoint(mx,my):
                        slot = self._first_empty()
                        if slot >= 0:
                            self.slots[slot] = card.key
                            self._rebuild_cards(); self._update_btn()
                        return
                for i in range(UCL_TOTAL_TEAMS):
                    if self._slot_rect(i).collidepoint(mx,my) and self.slots[i]:
                        self.slots[i] = None
                        self._rebuild_cards(); self._update_btn()
                        return

    def update(self, mx, my):
        for tab in self._country_tabs: tab.update(mx,my)
        ca = self._card_area()
        for card in self._team_cards:
            cr = pygame.Rect(card.rect.x, card.rect.y-self._browser_scroll, card.rect.w, card.rect.h)
            card._hov = cr.collidepoint(mx,my) and ca.collidepoint(mx,my)
        self.btn_rand.update(mx,my); self.btn_clear.update(mx,my)
        self.btn_next.update(mx,my); self.btn_back.update(mx,my)

    def _run_choose_team(self):
        chosen = None
        f_sub = pygame.font.SysFont("Georgia", 13, italic=True)
        bh = 46
        btn_back = FancyBtn("← BACK", (14,SCR_H-bh-10,130,bh), self.f_btn,
                            bg=(24,24,50),bg_h=(40,40,88),tc=WHITE)
        btn_confirm = FancyBtn("▶ START UCL", (SCR_W-300-14,SCR_H-bh-10,300,bh), self.f_btn,
                               bg=(16,76,34),bg_h=(26,116,50),tc=GOLD,bc=(40,155,65),enabled=False)
        while True:
            self.clock.tick(FPS); self._t += 0.04
            mx, my = pygame.mouse.get_pos()
            hover_slot = -1
            for i in range(UCL_TOTAL_TEAMS):
                if self._slot_rect(i).collidepoint(mx,my) and self.slots[i]:
                    hover_slot = i
            btn_back.update(mx,my); btn_confirm.update(mx,my)
            for ev in pygame.event.get():
                if ev.type == pygame.QUIT: pygame.quit(); sys.exit()
                if ev.type == pygame.KEYDOWN and ev.key == pygame.K_ESCAPE: return None
                if ev.type == pygame.MOUSEBUTTONDOWN and ev.button == 1:
                    if btn_back.clicked(mx,my): return '__back__'
                    if btn_confirm.clicked(mx,my) and chosen: return chosen
                    for i in range(UCL_TOTAL_TEAMS):
                        if self._slot_rect(i).collidepoint(mx,my) and self.slots[i]:
                            chosen = self.slots[i]; btn_confirm.enabled = True; break
            update_particles(self._parts, SCR_W, SCR_H)
            draw_stadium_bg(self.screen, self._t, SCR_W, SCR_H)
            draw_particles(self.screen, self._parts)
            self._draw_header("CHOOSE YOUR CLUB")
            sub = f_sub.render("Click the club you want to manage", True, UCL_SILVER)
            self.screen.blit(sub, sub.get_rect(centerx=SCR_W//2, y=80))
            for i in range(UCL_TOTAL_TEAMS):
                r = self._slot_rect(i); key = self.slots[i]
                ic = (key==chosen); ih = (i==hover_slot)
                col = (10,80,25) if ic else ((20,40,90) if ih else (8,14,40))
                bc  = (GOLD if ic else (UCL_STAR if ih else (30,44,80)))
                pygame.draw.rect(self.screen, col, r, border_radius=8)
                pygame.draw.rect(self.screen, bc, r, (2 if ic else 1), border_radius=8)
                if key:
                    ns = self.f_small.render(TEAMS[key]['name'], True,
                                             GOLD if ic else TEAMS[key]['hud_col'])
                    self.screen.blit(ns, ns.get_rect(x=r.x+6, centery=r.centery))
                else:
                    es = self.f_fsmall.render(f"Slot {i+1}", True, (30,44,70))
                    self.screen.blit(es, es.get_rect(x=r.x+5, centery=r.centery))
            btn_back.draw(self.screen); btn_confirm.draw(self.screen)
            pygame.display.flip()

    def run(self):
        while True:
            self.clock.tick(FPS); self._t += 0.04
            mx, my = pygame.mouse.get_pos()
            update_particles(self._parts, SCR_W, SCR_H)
            self.update(mx, my)
            for ev in pygame.event.get():
                if ev.type == pygame.QUIT: pygame.quit(); sys.exit()
                if ev.type == pygame.KEYDOWN and ev.key == pygame.K_ESCAPE: return None
                self.handle_event(ev)
                if ev.type == pygame.MOUSEBUTTONDOWN and ev.button == 1:
                    if self.btn_back.clicked(mx,my): return None
                    if self.btn_rand.clicked(mx,my): self._randomise_rest()
                    if self.btn_clear.clicked(mx,my): self._clear_all()
                    if self.btn_next.clicked(mx,my):
                        self._randomise_rest()
                        result = self._run_choose_team()
                        if result == '__back__': continue
                        if result is None: return None
                        return self.slots[:], result
            self._draw()
            pygame.display.flip()

    def _draw_header(self, sub):
        cx = SCR_W//2
        for r2, a in [(220,10),(160,18),(100,28)]:
            g = pygame.Surface((r2*2,60), pygame.SRCALPHA)
            pygame.draw.ellipse(g, (*UCL_STAR,a), g.get_rect())
            self.screen.blit(g, (cx-r2, 8))
        title = self.f_title.render(f"⭐  {sub}  ⭐", True, UCL_STAR)
        self.screen.blit(title, title.get_rect(centerx=cx, y=10))

    def _draw(self):
        draw_stadium_bg(self.screen, self._t, SCR_W, SCR_H)
        draw_particles(self.screen, self._parts)
        self._draw_header("SELECT 36 CLUBS")
        sub = self.f_sub.render(
            f"{self._filled()}/36 selected  ·  pick a country  ·  click team to add  ·  click slot to remove",
            True, UCL_SILVER)
        self.screen.blit(sub, sub.get_rect(centerx=SCR_W//2, y=80))
        for tab in self._country_tabs: tab.draw(self.screen)
        ca = self._card_area()
        if not self._sel_country:
            glass_panel(self.screen, ca, alpha=80)
            hint = self.f_small.render("← Pick a league", True, (55,75,130))
            self.screen.blit(hint, hint.get_rect(centerx=ca.centerx, centery=ca.centery))
        else:
            clip = pygame.Surface((ca.w,ca.h), pygame.SRCALPHA)
            for card in self._team_cards:
                cr = pygame.Rect(card.rect.x-ca.x, card.rect.y-ca.y-self._browser_scroll,
                                 card.rect.w, card.rect.h)
                if cr.bottom<0 or cr.top>ca.h: continue
                tmp = TeamCard(card.key, cr, self.f_card, self.f_fsmall)
                tmp._hov = card._hov; tmp._t = card._t; tmp.draw(clip)
            self.screen.blit(clip, ca.topleft)
            total = self._max_card_scroll()+ca.h
            if total > ca.h:
                sbx = ca.right+3
                bh2 = max(18, int(ca.h*ca.h/total))
                by2 = ca.y+int(self._browser_scroll/total*ca.h)
                pygame.draw.rect(self.screen,(22,36,72),(sbx,ca.y,4,ca.h),border_radius=2)
                pygame.draw.rect(self.screen,GOLD,(sbx,by2,4,bh2),border_radius=2)
        # Slots
        hdr = self.f_med.render("36 PARTICIPANTS", True, UCL_STAR)
        self.screen.blit(hdr, (self.SLOTS_X, self.SLOTS_Y-20))
        for i in range(UCL_TOTAL_TEAMS):
            r = self._slot_rect(i); key = self.slots[i]
            filled = key is not None
            pygame.draw.rect(self.screen, (8,18,50) if filled else (4,8,22), r, border_radius=7)
            pygame.draw.rect(self.screen, (60,90,160) if filled else (20,30,60), r, 1, border_radius=7)
            if filled:
                name = TEAMS[key]['name']
                ns = self.f_small.render(name, True, TEAMS[key]['hud_col'])
                while ns.get_width() > self.SLOT_W-44 and len(name)>3:
                    name = name[:-1]; ns = self.f_small.render(name+'…', True, TEAMS[key]['hud_col'])
                self.screen.blit(ns, ns.get_rect(x=r.x+5, centery=r.centery-5))
                draw_stars(self.screen, r.x+5, r.centery+4, get_stars(key), size=7, gap=1)
            else:
                es = self.f_fsmall.render(f"Slot {i+1}", True, (30,44,70))
                self.screen.blit(es, es.get_rect(x=r.x+5, centery=r.centery))
        self.btn_rand.draw(self.screen); self.btn_clear.draw(self.screen)
        self.btn_next.draw(self.screen); self.btn_back.draw(self.screen)


# ═══════════════════════════════════════════════════════════════════
# LEAGUE PHASE HUB
# ═══════════════════════════════════════════════════════════════════
class UCLLeagueHubScreen:
    def __init__(self, screen, clock, state):
        self.screen = screen; self.clock = clock; self.state = state
        self.f_head  = pygame.font.SysFont("Georgia", 26, bold=True)
        self.f_sub   = pygame.font.SysFont("Georgia", 14, bold=True)
        self.f_tbl   = pygame.font.SysFont("Arial",   12, bold=True)
        self.f_tbl_s = pygame.font.SysFont("Arial",   11)
        self.f_btn   = pygame.font.SysFont("Georgia", 18, bold=True)
        self.f_small = pygame.font.SysFont("Arial",   11)
        self._t = 0.0
        self._parts = make_particles(20, SCR_W, SCR_H)
        bh = 44
        self.btn_play = FancyBtn("▶ PLAY MY MATCH",
            (SCR_W-290,SCR_H-bh-10,276,bh), self.f_btn,
            bg=(16,76,34),bg_h=(26,116,50),tc=GOLD,bc=(40,155,65))
        self.btn_sim = FancyBtn("⏩ SIMULATE MATCHDAY",
            (SCR_W-290,SCR_H-bh*2-22,276,bh), self.f_btn,
            bg=(18,28,80),bg_h=(30,48,140),tc=WHITE)
        self.btn_back = FancyBtn("← MENU",
            (14,SCR_H-bh-10,100,bh), self.f_btn,
            bg=(24,24,50),bg_h=(40,40,88),tc=WHITE)
        self._refresh()

    def _refresh(self):
        hf = self.state.human_league_fixture()
        self.btn_play.enabled = (hf is not None) and not self.state.league_done
        self.btn_sim.enabled  = not self.state.league_done

    def run(self):
        self._refresh()
        while True:
            self.clock.tick(FPS); self._t += 0.04
            mx, my = pygame.mouse.get_pos()
            for ev in pygame.event.get():
                if ev.type == pygame.QUIT: pygame.quit(); sys.exit()
                if ev.type == pygame.KEYDOWN and ev.key == pygame.K_ESCAPE: return 'back'
                if ev.type == pygame.MOUSEBUTTONDOWN and ev.button == 1:
                    if self.btn_back.clicked(mx,my): return 'back'
                    if self.btn_play.clicked(mx,my): return 'play'
                    if self.btn_sim.clicked(mx,my):  return 'sim'
            self.btn_play.update(mx,my); self.btn_sim.update(mx,my); self.btn_back.update(mx,my)
            update_particles(self._parts, SCR_W, SCR_H)
            self._draw(); pygame.display.flip()

    def _draw(self):
        draw_stadium_bg(self.screen, self._t, SCR_W, SCR_H, grass_frac=0.88)
        draw_particles(self.screen, self._parts)
        hbar = pygame.Surface((SCR_W,48), pygame.SRCALPHA)
        pygame.draw.rect(hbar, (*UCL_BLUE,40), hbar.get_rect())
        self.screen.blit(hbar, (0,0))
        draw_football(self.screen, 36, 24, 16, self._t)
        ht = self.f_head.render(
            f"⭐ UCL League Phase  MD {self.state.league_matchday}/{self.state.total_league_matchdays}",
            True, UCL_STAR)
        self.screen.blit(ht, ht.get_rect(x=60, centery=24))
        gold_divider(self.screen, 50, SCR_W, margin=16)

        TBL_X,TBL_Y,TBL_W = 10,58,560
        COL_W = [24,178,26,26,26,26,36,36,40]
        LABELS = ['','Club','P','W','D','L','GF','GA','Pts']
        glass_panel(self.screen,(TBL_X,TBL_Y,TBL_W,22),tint=(6,12,32),alpha=220,border=UCL_STAR,radius=5)
        cx2 = TBL_X+4
        for lbl,cw in zip(LABELS,COL_W):
            s = self.f_tbl.render(lbl,True,UCL_STAR)
            self.screen.blit(s,(cx2+cw//2-s.get_width()//2,TBL_Y+3)); cx2+=cw

        table = self.state.sorted_table(); ROW_H=18
        ZONES = [(range(0,8),(0,40,80)),(range(8,24),(0,50,20)),(range(24,36),(50,10,10))]
        for rank,rec in enumerate(table):
            ry = TBL_Y+24+rank*ROW_H
            if ry > SCR_H-110: break
            is_h = (rec.key==self.state.human_key)
            tint = (20,50,30) if is_h else next((v for r,v in ZONES if rank in r),(8,14,40))
            glass_panel(self.screen,(TBL_X,ry,TBL_W,ROW_H-1),
                        tint=tint,alpha=200,border=GOLD if is_h else (26,38,70),radius=3)
            vals=[str(rank+1),rec.name,str(rec.P),str(rec.W),str(rec.D),
                  str(rec.L),str(rec.GF),str(rec.GA),str(rec.pts)]
            cx2=TBL_X+4
            for i,(val,cw) in enumerate(zip(vals,COL_W)):
                fc = UCL_STAR if i==len(vals)-1 else (GOLD if is_h else (175,180,205))
                s = self.f_tbl_s.render(val,True,fc)
                self.screen.blit(s,(cx2+cw//2-s.get_width()//2,ry+2)); cx2+=cw
            # Stars below team name (col index 1)
            stars_x = TBL_X+4+COL_W[0]+2
            draw_stars(self.screen, stars_x, ry+11, get_stars(rec.key), size=5, gap=1)

        ly=TBL_Y+24+min(36,len(table))*ROW_H+4
        for txt,col in [("Top 8 → R16",(80,140,220)),("9–24 → Play-offs",(80,190,100)),("25–36 → Out",(200,80,80))]:
            ls=self.f_small.render(txt,True,col); self.screen.blit(ls,(TBL_X+4,ly)); ly+=14

        FIX_X=TBL_X+TBL_W+16; FIX_W=SCR_W-FIX_X-14
        glass_panel(self.screen,(FIX_X,TBL_Y,FIX_W,SCR_H-TBL_Y-108),tint=(6,12,32),alpha=210,border=(36,52,90))
        sec=self.f_sub.render(f"MD {self.state.league_matchday} Fixtures",True,UCL_STAR)
        self.screen.blit(sec,sec.get_rect(x=FIX_X+8,y=TBL_Y+5))
        pygame.draw.line(self.screen,(*UCL_STAR,80),(FIX_X+6,TBL_Y+24),(FIX_X+FIX_W-6,TBL_Y+24),1)
        fy=TBL_Y+30
        for fix in [f for f in self.state.league_fixtures if f.matchday==self.state.league_matchday]:
            is_hf=self.state.human_key in (fix.home,fix.away); fh=30
            glass_panel(self.screen,(FIX_X+4,fy,FIX_W-8,fh),
                        tint=(14,40,18) if is_hf else (8,14,38),alpha=210,
                        border=(50,170,65) if is_hf else (30,44,78),radius=6)
            mid=FIX_X+FIX_W//2
            if fix.played:
                st=self.f_tbl_s.render(
                    f"{TEAMS[fix.home]['name']}  {fix.home_goals}–{fix.away_goals}  {TEAMS[fix.away]['name']}",
                    True,(140,230,140) if is_hf else (155,165,195))
                self.screen.blit(st,st.get_rect(centerx=mid,centery=fy+fh//2))
            else:
                hs=self.f_tbl_s.render(TEAMS[fix.home]['name'],True,TEAMS[fix.home]['hud_col'])
                vs=self.f_small.render("vs",True,(70,80,110))
                as_=self.f_tbl_s.render(TEAMS[fix.away]['name'],True,TEAMS[fix.away]['hud_col'])
                self.screen.blit(vs,vs.get_rect(centerx=mid,centery=fy+fh//2))
                self.screen.blit(hs,hs.get_rect(right=mid-14,centery=fy+fh//2))
                self.screen.blit(as_,as_.get_rect(x=mid+14,centery=fy+fh//2))
            fy+=fh+3
            if fy>SCR_H-120:
                more=self.f_small.render("…more fixtures",True,(50,60,95))
                self.screen.blit(more,(FIX_X+6,fy)); break
        self.btn_play.draw(self.screen); self.btn_sim.draw(self.screen); self.btn_back.draw(self.screen)


# ═══════════════════════════════════════════════════════════════════
# KNOCKOUT HUB SCREEN
# ═══════════════════════════════════════════════════════════════════
class UCLKnockoutHubScreen:
    def __init__(self, screen, clock, state):
        self.screen = screen; self.clock = clock; self.state = state
        self.f_head = pygame.font.SysFont("Georgia", 26, bold=True)
        self.f_tie  = pygame.font.SysFont("Arial",   13, bold=True)
        self.f_btn  = pygame.font.SysFont("Georgia", 18, bold=True)
        self.f_small= pygame.font.SysFont("Arial",   11)
        self._t = 0.0; self._parts = make_particles(20,SCR_W,SCR_H)
        bh=44
        self.btn_play = FancyBtn("▶ PLAY MY MATCH",
            (SCR_W-290,SCR_H-bh-10,276,bh),self.f_btn,
            bg=(16,76,34),bg_h=(26,116,50),tc=GOLD,bc=(40,155,65))
        self.btn_sim = FancyBtn("⏩ SIMULATE ALL",
            (SCR_W-290,SCR_H-bh*2-22,276,bh),self.f_btn,
            bg=(18,28,80),bg_h=(30,48,140),tc=WHITE)
        self.btn_back=FancyBtn("← MENU",(14,SCR_H-bh-10,100,bh),self.f_btn,
            bg=(24,24,50),bg_h=(40,40,88),tc=WHITE)
        self._refresh()

    def _refresh(self):
        hf=self.state.human_knockout_tie(); ties=self.state.current_round_ties()
        all_done=all(t.done for t in ties) if ties else True
        self.btn_play.enabled=(hf is not None and not hf.done)
        self.btn_sim.enabled=not all_done

    def run(self):
        self._refresh()
        while True:
            self.clock.tick(FPS); self._t+=0.04
            mx,my=pygame.mouse.get_pos()
            for ev in pygame.event.get():
                if ev.type==pygame.QUIT: pygame.quit();sys.exit()
                if ev.type==pygame.KEYDOWN and ev.key==pygame.K_ESCAPE: return 'back'
                if ev.type==pygame.MOUSEBUTTONDOWN and ev.button==1:
                    if self.btn_back.clicked(mx,my): return 'back'
                    if self.btn_play.clicked(mx,my): return 'play'
                    if self.btn_sim.clicked(mx,my):  return 'sim'
            self.btn_play.update(mx,my); self.btn_sim.update(mx,my); self.btn_back.update(mx,my)
            update_particles(self._parts,SCR_W,SCR_H); self._draw(); pygame.display.flip()

    def _draw(self):
        draw_stadium_bg(self.screen,self._t,SCR_W,SCR_H,grass_frac=0.88)
        draw_particles(self.screen,self._parts)
        rname=ROUND_NAMES.get(self.state.round,self.state.round.upper())
        hbar=pygame.Surface((SCR_W,48),pygame.SRCALPHA)
        pygame.draw.rect(hbar,(*UCL_BLUE,40),hbar.get_rect())
        self.screen.blit(hbar,(0,0))
        draw_football(self.screen,36,24,16,self._t)
        ht=self.f_head.render(f"⭐ UCL — {rname}",True,UCL_STAR)
        self.screen.blit(ht,ht.get_rect(x=60,centery=24))
        gold_divider(self.screen,50,SCR_W,margin=16)

        ties=self.state.current_round_ties()
        cx=SCR_W//2; TIE_W,TIE_H,GAP=480,60,12
        total_h=len(ties)*(TIE_H+GAP)
        start_y=max(60,SCR_H//2-total_h//2-40)
        for i,tie in enumerate(ties):
            if not tie: continue
            r=pygame.Rect(cx-TIE_W//2,start_y+i*(TIE_H+GAP),TIE_W,TIE_H)
            is_h=self.state.human_key in (tie.team_a,tie.team_b)
            glass_panel(self.screen,r,tint=(14,46,20) if is_h else (8,14,42),
                        alpha=220,border=(50,180,70) if is_h else (34,52,94),radius=12)
            tn_a=TEAMS[tie.team_a]['name']; cn_a=TEAMS[tie.team_a]['hud_col']
            tn_b=TEAMS[tie.team_b]['name']; cn_b=TEAMS[tie.team_b]['hud_col']
            mid_x=r.centerx
            if tie.played_leg1:
                agg_a,agg_b=tie.aggregate()
                agg_s=self.f_tie.render(f"{agg_a}  –  {agg_b}",True,GOLD if tie.done else UCL_SILVER)
                self.screen.blit(agg_s,agg_s.get_rect(centerx=mid_x,centery=r.centery))
                if tie.done and tie.winner:
                    ws=self.f_small.render(f"✓ {TEAMS[tie.winner]['name']}",True,(80,230,100))
                    self.screen.blit(ws,ws.get_rect(centerx=mid_x,centery=r.bottom-12))
            else:
                vs=self.f_small.render("vs",True,(70,80,110))
                self.screen.blit(vs,vs.get_rect(centerx=mid_x,centery=r.centery))
            a_s=self.f_tie.render(tn_a,True,cn_a); b_s=self.f_tie.render(tn_b,True,cn_b)
            self.screen.blit(a_s,a_s.get_rect(right=mid_x-22,centery=r.centery))
            self.screen.blit(b_s,b_s.get_rect(x=mid_x+22,centery=r.centery))
            if tie.played_leg1:
                l1=self.f_small.render(f"L1: {tie.leg1.home_goals}–{tie.leg1.away_goals}",True,(120,130,160))
                self.screen.blit(l1,(r.x+8,r.y+6))
            if tie.two_legs and tie.played_leg2:
                l2=self.f_small.render(f"L2: {tie.leg2.home_goals}–{tie.leg2.away_goals}",True,(120,130,160))
                self.screen.blit(l2,(r.x+8,r.y+20))
        self.btn_play.draw(self.screen); self.btn_sim.draw(self.screen); self.btn_back.draw(self.screen)


# ═══════════════════════════════════════════════════════════════════
# UCL CHAMPION SCREEN
# ═══════════════════════════════════════════════════════════════════
class UCLChampionScreen:
    def __init__(self,screen,clock,state):
        self.screen=screen;self.clock=clock;self.state=state
        self.f_xl =pygame.font.SysFont("Georgia",52,bold=True)
        self.f_big=pygame.font.SysFont("Georgia",34,bold=True)
        self.f_med=pygame.font.SysFont("Georgia",22,bold=True)
        self.f_btn=pygame.font.SysFont("Georgia",20,bold=True)
        self._t=0.0; self._parts=make_particles(70,SCR_W,SCR_H,seed=42)
        self.btn=FancyBtn("← MAIN MENU",(SCR_W//2-150,SCR_H-70,300,50),self.f_btn,
            bg=(24,24,50),bg_h=(40,40,88),tc=WHITE)

    def run(self):
        while True:
            self.clock.tick(FPS);self._t+=0.05
            mx,my=pygame.mouse.get_pos();self.btn.update(mx,my)
            for ev in pygame.event.get():
                if ev.type==pygame.QUIT:pygame.quit();sys.exit()
                if ev.type==pygame.MOUSEBUTTONDOWN and ev.button==1:
                    if self.btn.clicked(mx,my):return
                if ev.type==pygame.KEYDOWN:return
            update_particles(self._parts,SCR_W,SCR_H);self._draw();pygame.display.flip()

    def _draw(self):
        champ=self.state.champion; is_h=(champ==self.state.human_key)
        for y in range(SCR_H):
            f=y/SCR_H
            pygame.draw.line(self.screen,(int(2+6*f),int(4+12*f),int(12+22*f)),(0,y),(SCR_W,y))
        draw_stadium_bg(self.screen,self._t,SCR_W,SCR_H,grass_frac=0.92)
        draw_particles(self.screen,self._parts)
        cx=SCR_W//2
        for r2,a in [(280,10),(210,18),(140,30)]:
            g=pygame.Surface((r2*2,120),pygame.SRCALPHA)
            pygame.draw.ellipse(g,(*UCL_STAR,a),g.get_rect())
            self.screen.blit(g,(cx-r2,60))
        ss=self.f_med.render("★ ★ ★ ★ ★ ★ ★ ★",True,UCL_STAR)
        self.screen.blit(ss,ss.get_rect(centerx=cx,y=68))
        title=self.f_xl.render("UEFA CHAMPIONS LEAGUE WINNER",True,UCL_STAR)
        self.screen.blit(title,title.get_rect(centerx=cx,y=108))
        if champ:
            cn=self.f_big.render(TEAMS[champ]['name'],True,TEAMS[champ]['hud_col'])
            self.screen.blit(cn,cn.get_rect(centerx=cx,y=178))
        if is_h:
            glass_panel(self.screen,(cx-260,230,520,50),tint=(12,50,16),alpha=220,border=GOLD,radius=14)
            you=self.f_med.render("🏆  YOU ARE THE CHAMPIONS!  🏆",True,GOLD)
            self.screen.blit(you,you.get_rect(centerx=cx,centery=255))
        if self.state.final_tie and self.state.final_tie.played_leg1:
            ft=self.state.final_tie
            fs=self.f_med.render(
                f"FINAL: {TEAMS[ft.team_a]['name']}  {ft.leg1.home_goals}–{ft.leg1.away_goals}  {TEAMS[ft.team_b]['name']}",
                True,UCL_SILVER)
            self.screen.blit(fs,fs.get_rect(centerx=cx,y=296))
        self.btn.draw(self.screen)


# ═══════════════════════════════════════════════════════════════════
# POST-MATCH SCREEN
# ═══════════════════════════════════════════════════════════════════
class UCLPostMatchScreen:
    def __init__(self,screen,clock,home_key,away_key,hg,ag,context=""):
        self.screen=screen;self.clock=clock
        self.home_key=home_key;self.away_key=away_key
        self.hg=hg;self.ag=ag;self.context=context
        self.f_xl =pygame.font.SysFont("Georgia",48,bold=True)
        self.f_sc =pygame.font.SysFont("Georgia",46,bold=True)
        self.f_med=pygame.font.SysFont("Georgia",18,bold=True)
        self.f_btn=pygame.font.SysFont("Georgia",18,bold=True)
        self._t=0.0;self._timer=FPS*4
        self._parts=make_particles(45,SCR_W,SCR_H,seed=77)
        self.btn=FancyBtn("CONTINUE →",(SCR_W//2-120,SCR_H-68,240,48),self.f_btn,
            bg=(16,76,34),bg_h=(26,116,50),tc=GOLD,bc=(40,155,65))

    def run(self):
        while True:
            self.clock.tick(FPS);self._t+=0.05;self._timer-=1
            mx,my=pygame.mouse.get_pos();self.btn.update(mx,my)
            for ev in pygame.event.get():
                if ev.type==pygame.QUIT:pygame.quit();sys.exit()
                if ev.type==pygame.KEYDOWN:return
                if ev.type==pygame.MOUSEBUTTONDOWN and ev.button==1:
                    if self.btn.clicked(mx,my):return
            if self._timer<=0:return
            update_particles(self._parts,SCR_W,SCR_H);self._draw();pygame.display.flip()

    def _draw(self):
        for y in range(SCR_H):
            f=y/SCR_H
            pygame.draw.line(self.screen,(int(2+8*f),int(4+14*f),int(16+34*f)),(0,y),(SCR_W,y))
        draw_stadium_bg(self.screen,self._t,SCR_W,SCR_H,grass_frac=0.91)
        draw_particles(self.screen,self._parts)
        cx=SCR_W//2
        for r2,a in [(230,12),(165,22),(100,35)]:
            g=pygame.Surface((r2*2,80),pygame.SRCALPHA)
            pygame.draw.ellipse(g,(*UCL_STAR,a),g.get_rect()); self.screen.blit(g,(cx-r2,110))
        if self.context:
            cs=self.f_med.render(self.context,True,UCL_SILVER)
            self.screen.blit(cs,cs.get_rect(centerx=cx,y=118))
        glass_panel(self.screen,(cx-280,148,560,100),tint=(6,12,40),alpha=230,border=UCL_STAR,radius=18)
        draw_kit(self.screen,cx-200,198,TEAMS[self.home_key])
        draw_kit(self.screen,cx+200,198,TEAMS[self.away_key])
        sc=self.f_sc.render(f"{self.hg}  –  {self.ag}",True,WHITE)
        self.screen.blit(sc,sc.get_rect(centerx=cx,y=155))
        hn=self.f_med.render(TEAMS[self.home_key]['name'],True,TEAMS[self.home_key]['hud_col'])
        an=self.f_med.render(TEAMS[self.away_key]['name'],True,TEAMS[self.away_key]['hud_col'])
        self.screen.blit(hn,hn.get_rect(right=cx-160,centery=198))
        self.screen.blit(an,an.get_rect(x=cx+160,centery=198))
        cd=max(0,self._timer//FPS)
        hint=self.f_med.render(f"Auto-continuing in {cd}s",True,(60,75,110))
        self.screen.blit(hint,hint.get_rect(centerx=cx,y=SCR_H-100))
        self.btn.draw(self.screen)
