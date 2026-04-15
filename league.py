"""
league.py – Full league season system.

Flow:
  LeagueSetupScreen  →  pick country + your team
  LeagueState        →  generates all fixtures (home+away round-robin)
  LeagueHubScreen    →  standings table + today's fixtures, PLAY / SIM buttons
  Game               →  plays the human's match
  PostMatchScreen    →  result flash, back to hub
"""
import pygame
import sys
import math
import random
import itertools

from constants import SCR_W, SCR_H, FPS, TEAMS

# ── Palette (shared with menu.py) ────────────────────────────────
BG_TOP  = (6,  10,  22)
BG_BOT  = (14, 28,  52)
GOLD    = (255, 210,  40)
WHITE   = (240, 240, 240)
GREY    = (110, 110, 130)
GREEN   = ( 30, 140,  60)
RED_C   = (180,  30,  30)
BLUE_C  = ( 30,  80, 180)

COUNTRY_TEAMS = {}   # built at module load
for key, data in TEAMS.items():
    COUNTRY_TEAMS.setdefault(data['country'], []).append(key)

LEAGUE_NAMES = {
    'Spain':   'La Primera',
    'England': 'The Premier League',
    'Germany': 'Die Bundesliga',
}


# ── Background helpers ────────────────────────────────────────────
def _gradient_bg(surf):
    for y in range(SCR_H):
        t   = y / SCR_H
        col = tuple(int(BG_TOP[i] + (BG_BOT[i] - BG_TOP[i]) * t) for i in range(3))
        pygame.draw.line(surf, col, (0, y), (SCR_W, y))


def _panel(surf, rect, alpha=200, radius=14):
    s = pygame.Surface((rect[2], rect[3]), pygame.SRCALPHA)
    s.fill((10, 18, 45, alpha))
    surf.blit(s, rect[:2])
    pygame.draw.rect(surf, (40, 55, 100), rect, 1, border_radius=radius)


# ── League data model ─────────────────────────────────────────────
class TeamRecord:
    def __init__(self, key):
        self.key = key
        self.name = TEAMS[key]['name']
        self.col  = TEAMS[key]['hud_col']
        self.P = self.W = self.D = self.L = 0
        self.GF = self.GA = self.pts = 0

    @property
    def GD(self):
        return self.GF - self.GA

    def add_result(self, gf, ga):
        self.P  += 1
        self.GF += gf
        self.GA += ga
        if gf > ga:
            self.W   += 1
            self.pts += 3
        elif gf == ga:
            self.D   += 1
            self.pts += 1
        else:
            self.L += 1


class Fixture:
    def __init__(self, home_key, away_key, matchday):
        self.home      = home_key
        self.away      = away_key
        self.matchday  = matchday
        self.played    = False
        self.home_goals = 0
        self.away_goals = 0

    def simulate(self):
        """CPU vs CPU – simple random result weighted by nothing (placeholder)."""
        h = random.randint(0, 3)
        a = random.randint(0, 3)
        self.home_goals = h
        self.away_goals = a
        self.played = True
        return h, a

    def set_result(self, h, a):
        self.home_goals = h
        self.away_goals = a
        self.played = True


class LeagueState:
    def __init__(self, country, human_key):
        self.country    = country
        self.human_key  = human_key
        self.league_name = LEAGUE_NAMES.get(country, country)
        self.team_keys  = COUNTRY_TEAMS[country][:]
        self.records    = {k: TeamRecord(k) for k in self.team_keys}
        self.fixtures   = []
        self.matchday   = 1
        self._gen_fixtures()

    def _gen_fixtures(self):
        teams = self.team_keys
        n     = len(teams)
        # Round-robin schedule using circle method
        if n % 2 == 1:
            teams = teams + ['__bye__']
        n2  = len(teams)
        half = n2 // 2
        lst  = teams[1:]
        days_first  = []
        for rnd in range(n2 - 1):
            pairs = []
            pivot = teams[0]
            rot   = lst[rnd:] + lst[:rnd]
            for i in range(half):
                h = pivot if i == 0 else rot[i-1]
                a = rot[-(i)] if i == 0 else rot[half+i-1] if half+i-1 < len(rot) else rot[i]
                # simpler: just pair rot[i] vs rot[n2-2-i]
            # Use simpler direct pairing
            rot2 = lst[rnd:] + lst[:rnd]
            round_pairs = [(teams[0], rot2[0])]
            for i in range(1, half):
                round_pairs.append((rot2[i], rot2[n2-1-i]))
            days_first.append(round_pairs)

        days_second = [[(b, a) for a, b in day] for day in days_first]
        all_days    = days_first + days_second

        md = 1
        for day_pairs in all_days:
            for h, a in day_pairs:
                if h == '__bye__' or a == '__bye__':
                    continue
                self.fixtures.append(Fixture(h, a, md))
            md += 1
        self.total_matchdays = md - 1

    def current_fixtures(self):
        return [f for f in self.fixtures if f.matchday == self.matchday and not f.played]

    def human_fixture_today(self):
        for f in self.current_fixtures():
            if f.home == self.human_key or f.away == self.human_key:
                return f
        return None

    def simulate_matchday(self, skip_human=True):
        """Simulate all fixtures on current matchday except human's."""
        for f in self.current_fixtures():
            is_human = (f.home == self.human_key or f.away == self.human_key)
            if skip_human and is_human:
                continue
            h, a = f.simulate()
            self.records[f.home].add_result(h, a)
            self.records[f.away].add_result(a, h)

    def apply_result(self, fixture, home_goals, away_goals):
        fixture.set_result(home_goals, away_goals)
        self.records[fixture.home].add_result(home_goals, away_goals)
        self.records[fixture.away].add_result(away_goals, home_goals)

    def advance_matchday(self):
        self.matchday += 1

    def sorted_table(self):
        recs = list(self.records.values())
        recs.sort(key=lambda r: (-r.pts, -r.GD, -r.GF, r.name))
        return recs

    @property
    def season_over(self):
        return self.matchday > self.total_matchdays


# ── Generic button ────────────────────────────────────────────────
class Btn:
    def __init__(self, text, rect, font, enabled=True,
                 bg=(28,44,90), bg_h=(46,74,150), bg_d=(20,26,42),
                 tc=WHITE, tc_d=(50,50,60), bc=None):
        self.text, self.rect = text, pygame.Rect(rect)
        self.font    = font
        self.enabled = enabled
        self.bg, self.bg_h, self.bg_d = bg, bg_h, bg_d
        self.tc, self.tc_d = tc, tc_d
        self.bc      = bc
        self._hov    = False
        self._pulse  = 0.0

    def update(self, mx, my):
        self._hov   = self.enabled and self.rect.collidepoint(mx, my)
        self._pulse = (self._pulse + 0.07) % (math.pi*2)

    def draw(self, surf):
        col = self.bg_d if not self.enabled else (self.bg_h if self._hov else self.bg)
        pygame.draw.rect(surf, col, self.rect, border_radius=10)
        bc  = self.bc if self.bc else (GOLD if self._hov and self.enabled else (50,65,110))
        if not self.enabled: bc = (34,40,56)
        pygame.draw.rect(surf, bc, self.rect, 2, border_radius=10)
        tc  = self.tc if self.enabled else self.tc_d
        lbl = self.font.render(self.text, True, tc)
        surf.blit(lbl, lbl.get_rect(center=self.rect.center))
        if self._hov and self.enabled:
            g = pygame.Surface((self.rect.w+10, self.rect.h+10), pygame.SRCALPHA)
            pygame.draw.rect(g, (*GOLD, int(25+15*math.sin(self._pulse))), g.get_rect(), border_radius=11)
            surf.blit(g, (self.rect.x-5, self.rect.y-5))

    def clicked(self, mx, my):
        return self.enabled and self.rect.collidepoint(mx, my)


# ── League Setup Screen ───────────────────────────────────────────
class LeagueSetupScreen:
    """Step 1: pick league country. Step 2: pick your team (single panel)."""

    COUNTRY_ORDER = ['Spain', 'England', 'Germany']

    def __init__(self, screen, clock):
        self.screen = screen
        self.clock  = clock
        self.f_title   = pygame.font.SysFont("Georgia", 42, bold=True)
        self.f_sub     = pygame.font.SysFont("Georgia", 20, bold=True)
        self.f_country = pygame.font.SysFont("Arial",   15, bold=True)
        self.f_card    = pygame.font.SysFont("Arial",   11, bold=True)
        self.f_small   = pygame.font.SysFont("Arial",   10)
        self.f_btn     = pygame.font.SysFont("Georgia", 22, bold=True)

        self.selected_country = None
        self.selected_team    = None
        self._scroll          = 0
        self._country_btns    = []
        self._team_cards      = []

        # Country buttons  (left side, stacked)
        FLAG_INFO = {
            'Spain':   [((198,11,30),0.25),((255,196,0),0.50),((198,11,30),0.25)],
            'England': [((255,255,255),1.0)],
            'Germany': [((0,0,0),0.333),((221,0,0),0.333),((255,206,0),0.334)],
        }
        CROSS_COL = {'England': (198,11,30)}
        self._flag_info  = FLAG_INFO
        self._cross_info = CROSS_COL

        cy = 160
        for country in self.COUNTRY_ORDER:
            self._country_btns.append({
                'country': country,
                'rect': pygame.Rect(60, cy, 200, 68),
                'selected': False,
                'hover': False,
            })
            cy += 82

        bh = 50
        self.btn_start = Btn("▶  START SEASON",
            (SCR_W//2 - 130, SCR_H - bh - 12, 260, bh), self.f_btn,
            enabled=False,
            bg=(20,80,36), bg_h=(30,120,54), bg_d=(18,28,18),
            tc=GOLD, tc_d=(40,60,40), bc=(40,160,70))
        self.btn_back = Btn("← BACK",
            (20, SCR_H - bh - 12, 120, bh), self.f_btn,
            bg=(26,26,52), bg_h=(44,44,90))

        # Grid layout for team cards
        self.CARD_W, self.CARD_H = 142, 110
        self.CARD_GAP  = 10
        self.GRID_X    = 290
        self.GRID_Y    = 140
        self.GRID_W    = SCR_W - self.GRID_X - 30
        self.GRID_H    = SCR_H - self.GRID_Y - 80

    # ── flag drawing ─────────────────────────────────────────────
    def _draw_flag(self, surf, rect, country):
        x, y, w, h = rect
        info = self._flag_info.get(country, [((100,100,100),1.0)])
        dx = x
        for col, frac in info:
            fw = int(w*frac)
            pygame.draw.rect(surf, col, (dx, y, fw, h))
            dx += fw
        cc = self._cross_info.get(country)
        if cc:
            cx2, cy2 = x+w//2, y+h//2
            pygame.draw.rect(surf, cc, (x, cy2-2, w, 5))
            pygame.draw.rect(surf, cc, (cx2-2, y, 5, h))
        pygame.draw.rect(surf, (70,70,70), rect, 1)

    # ── team card grid ────────────────────────────────────────────
    def _build_cards(self):
        self._team_cards = []
        self._scroll     = 0
        if not self.selected_country:
            return
        keys = COUNTRY_TEAMS.get(self.selected_country, [])
        cols = max(1, (self.GRID_W + self.CARD_GAP) // (self.CARD_W + self.CARD_GAP))
        for i, key in enumerate(keys):
            col = i % cols
            row = i // cols
            x   = self.GRID_X + col*(self.CARD_W+self.CARD_GAP)
            y   = self.GRID_Y + row*(self.CARD_H+self.CARD_GAP)
            self._team_cards.append({'key': key, 'x': x, 'y': y,
                                     'selected': False, 'hover': False})

    def _card_screen_rect(self, card):
        return pygame.Rect(card['x'], card['y'] - self._scroll,
                           self.CARD_W, self.CARD_H)

    def _grid_clip(self):
        return pygame.Rect(self.GRID_X, self.GRID_Y, self.GRID_W, self.GRID_H)

    def _max_scroll(self):
        if not self._team_cards:
            return 0
        bottom = max(c['y'] + self.CARD_H for c in self._team_cards)
        return max(0, bottom - (self.GRID_Y + self.GRID_H))

    # ── kit preview (inline, small) ──────────────────────────────
    def _draw_kit(self, surf, cx, cy, kit):
        s1, s2 = kit['shirt1'], kit.get('shirt2', kit['shirt1'])
        sh, sk = kit['shorts'], kit['socks']
        body   = pygame.Rect(cx-15, cy-12, 30, 24)
        if kit.get('stripe'):
            cols = kit.get('stripe_cols', [s1, s2, s1])
            sw   = max(2, body.w // len(cols))
            for si, sc in enumerate(cols):
                clip  = pygame.Rect(body.x+si*sw, body.y, sw, body.h)
                inter = body.clip(clip)
                if inter.w > 0:
                    pygame.draw.rect(surf, sc, inter, border_radius=2)
        elif kit.get('half_half'):
            pygame.draw.rect(surf, s1, (body.x, body.y, body.w//2, body.h), border_radius=2)
            pygame.draw.rect(surf, s2, (body.x+body.w//2, body.y, body.w//2, body.h), border_radius=2)
        else:
            pygame.draw.rect(surf, s1, body, border_radius=2)
        pygame.draw.rect(surf, (0,0,0), body, 1, border_radius=2)
        pygame.draw.rect(surf, s1, (cx-22, cy-6,  8, 12), border_radius=2)
        pygame.draw.rect(surf, s2, (cx+14, cy-6,  8, 12), border_radius=2)
        pygame.draw.rect(surf, sh, (cx-11, cy+11, 22,  9), border_radius=2)
        for so in (-5, 5):
            pygame.draw.rect(surf, sk, (cx+so-2, cy+20, 5, 5), border_radius=1)

    # ── event handling ────────────────────────────────────────────
    def handle_event(self, ev):
        mx, my = pygame.mouse.get_pos()
        gc     = self._grid_clip()

        if ev.type == pygame.MOUSEBUTTONDOWN:
            if ev.button == 4 and gc.collidepoint(ev.pos):
                self._scroll = max(0, self._scroll - 36)
            elif ev.button == 5 and gc.collidepoint(ev.pos):
                self._scroll = min(self._max_scroll(), self._scroll + 36)
            elif ev.button == 1:
                # Country buttons
                for cb in self._country_btns:
                    if cb['rect'].collidepoint(ev.pos):
                        if cb['country'] != self.selected_country:
                            self.selected_country = cb['country']
                            self.selected_team    = None
                            self._build_cards()
                        for c in self._country_btns:
                            c['selected'] = (c['country'] == cb['country'])
                        return

                # Team cards
                for card in self._team_cards:
                    sr = self._card_screen_rect(card)
                    if sr.collidepoint(ev.pos) and gc.collidepoint(ev.pos):
                        for c in self._team_cards:
                            c['selected'] = False
                        card['selected']   = True
                        self.selected_team = card['key']
                        self.btn_start.enabled = True

    def update(self, mx, my):
        for cb in self._country_btns:
            cb['hover'] = cb['rect'].collidepoint(mx, my)
        gc = self._grid_clip()
        for card in self._team_cards:
            sr = self._card_screen_rect(card)
            card['hover'] = sr.collidepoint(mx, my) and gc.collidepoint(mx, my)
        self.btn_start.update(mx, my)
        self.btn_back.update(mx, my)

    def run(self):
        while True:
            self.clock.tick(FPS)
            mx, my = pygame.mouse.get_pos()

            for ev in pygame.event.get():
                if ev.type == pygame.QUIT:
                    pygame.quit(); sys.exit()
                if ev.type == pygame.KEYDOWN and ev.key == pygame.K_ESCAPE:
                    return None
                self.handle_event(ev)
                if ev.type == pygame.MOUSEBUTTONDOWN and ev.button == 1:
                    if self.btn_back.clicked(mx, my):
                        return None
                    if self.btn_start.clicked(mx, my):
                        return LeagueState(self.selected_country, self.selected_team)

            self.update(mx, my)
            self._draw()
            pygame.display.flip()

    # ── drawing ───────────────────────────────────────────────────
    def _draw(self):
        _gradient_bg(self.screen)

        title = self.f_title.render("LEAGUE MODE", True, GOLD)
        self.screen.blit(title, title.get_rect(centerx=SCR_W//2, y=16))

        sub_txt = "Select a league, then choose your club" if not self.selected_country else \
                  f"{LEAGUE_NAMES.get(self.selected_country, self.selected_country)}  —  pick your team"
        sub = self.f_sub.render(sub_txt, True, (140, 160, 210))
        self.screen.blit(sub, sub.get_rect(centerx=SCR_W//2, y=68))

        # Country buttons
        for cb in self._country_btns:
            if cb['selected']:
                bg, bc, bw = (28, 52, 110), GOLD, 3
            elif cb['hover']:
                bg, bc, bw = (20, 36, 80), (100,140,210), 2
            else:
                bg, bc, bw = (12, 20, 48), (38,52,86), 1
            pygame.draw.rect(self.screen, bg, cb['rect'], border_radius=12)
            pygame.draw.rect(self.screen, bc, cb['rect'], bw, border_radius=12)
            self._draw_flag(self.screen,
                (cb['rect'].x+8, cb['rect'].y+17, 46, 28), cb['country'])
            lbl = self.f_country.render(cb['country'], True,
                                        GOLD if cb['selected'] else WHITE)
            self.screen.blit(lbl, lbl.get_rect(x=cb['rect'].x+64,
                                               centery=cb['rect'].centery))
            if cb['selected']:
                arr = self.f_country.render('▶', True, GOLD)
                self.screen.blit(arr, arr.get_rect(right=cb['rect'].right-8,
                                                   centery=cb['rect'].centery))

        # Divider
        pygame.draw.line(self.screen, (38,52,86),
                         (278, 130), (278, SCR_H-80), 1)

        # Team card grid (clipped)
        if not self.selected_country:
            hint = self.f_sub.render("← Pick a league first", True, (55, 70, 120))
            self.screen.blit(hint, hint.get_rect(
                centerx=(self.GRID_X + SCR_W)//2, centery=SCR_H//2))
        else:
            gc     = self._grid_clip()
            clip_s = pygame.Surface((gc.w, gc.h), pygame.SRCALPHA)
            for card in self._team_cards:
                kit = TEAMS[card['key']]
                ry  = card['y'] - self.GRID_Y - self._scroll
                rx  = card['x'] - self.GRID_X
                cr  = pygame.Rect(rx, ry, self.CARD_W, self.CARD_H)
                if cr.bottom < 0 or cr.top > gc.h:
                    continue

                if card['selected']:
                    bg, bc, bw = (34,58,108), GOLD, 3
                elif card['hover']:
                    bg, bc, bw = (22,38,80), (100,140,210), 2
                else:
                    bg, bc, bw = (14,22,50), (38,52,86), 1

                pygame.draw.rect(clip_s, bg, cr, border_radius=10)
                pygame.draw.rect(clip_s, bc, cr, bw, border_radius=10)
                self._draw_kit(clip_s, cr.centerx, cr.y+36, kit)

                name = kit['name']
                ns   = self.f_card.render(name, True,
                                          WHITE if (card['selected'] or card['hover']) else GREY)
                if ns.get_width() > cr.w - 8:
                    while ns.get_width() > cr.w - 8 and len(name) > 3:
                        name = name[:-1]
                    ns = self.f_card.render(name+'…', True,
                                            WHITE if (card['selected'] or card['hover']) else GREY)
                clip_s.blit(ns, ns.get_rect(centerx=cr.centerx, y=cr.bottom-18))

                if card['selected']:
                    chk = self.f_small.render('✓ YOUR CLUB', True, GOLD)
                    clip_s.blit(chk, chk.get_rect(centerx=cr.centerx, y=cr.y+4))

            self.screen.blit(clip_s, gc.topleft)

            # Scroll bar
            total = self._max_scroll() + self.GRID_H
            if total > self.GRID_H:
                sb_x  = gc.right + 4
                bh2   = max(20, int(gc.h * gc.h / total))
                by2   = gc.y + int(self._scroll / total * gc.h)
                pygame.draw.rect(self.screen, (30,45,80),  (sb_x, gc.y, 4, gc.h), border_radius=2)
                pygame.draw.rect(self.screen, GOLD, (sb_x, by2, 4, bh2), border_radius=2)

        self.btn_start.draw(self.screen)
        self.btn_back.draw(self.screen)


# ── League Hub Screen ─────────────────────────────────────────────
class LeagueHubScreen:
    """
    Main league screen shown between matchdays.
    Left half  : standings table
    Right half : today's fixtures (with PLAY / SIM buttons for human match)
    """

    def __init__(self, screen, clock, league: LeagueState):
        self.screen = screen
        self.clock  = clock
        self.ls     = league

        self.f_title  = pygame.font.SysFont("Georgia", 32, bold=True)
        self.f_sub    = pygame.font.SysFont("Georgia", 16, bold=True)
        self.f_tbl    = pygame.font.SysFont("Arial",   13, bold=True)
        self.f_tbl_s  = pygame.font.SysFont("Arial",   12)
        self.f_fix    = pygame.font.SysFont("Arial",   13, bold=True)
        self.f_btn    = pygame.font.SysFont("Georgia", 20, bold=True)
        self.f_small  = pygame.font.SysFont("Arial",   11)

        bh = 46
        self.btn_play = Btn("▶  PLAY MY MATCH",
            (SCR_W-310, SCR_H-bh-10, 290, bh), self.f_btn,
            bg=(20,80,36), bg_h=(30,120,54), bg_d=(18,28,18),
            tc=GOLD, tc_d=(40,60,40), bc=(40,160,70))
        self.btn_sim  = Btn("⏩  SIMULATE MATCHDAY",
            (SCR_W-310, SCR_H-bh*2-22, 290, bh), self.f_btn,
            bg=(30,30,80), bg_h=(50,50,130),
            tc=WHITE)
        self.btn_back = Btn("← MENU",
            (14, SCR_H-bh-10, 120, bh), self.f_btn,
            bg=(26,26,52), bg_h=(44,44,90))

        self._action = None   # 'play' | 'sim' | 'back' | 'season_over'

    def _refresh_buttons(self):
        hf = self.ls.human_fixture_today()
        self.btn_play.enabled = (hf is not None) and (not self.ls.season_over)
        self.btn_sim.enabled  = not self.ls.season_over

    def run(self):
        self._refresh_buttons()
        while True:
            self.clock.tick(FPS)
            mx, my = pygame.mouse.get_pos()

            for ev in pygame.event.get():
                if ev.type == pygame.QUIT:
                    pygame.quit(); sys.exit()
                if ev.type == pygame.KEYDOWN and ev.key == pygame.K_ESCAPE:
                    return 'back'
                if ev.type == pygame.MOUSEBUTTONDOWN and ev.button == 1:
                    if self.btn_back.clicked(mx, my):
                        return 'back'
                    if self.btn_play.clicked(mx, my):
                        return 'play'
                    if self.btn_sim.clicked(mx, my):
                        return 'sim'

            self.btn_play.update(mx, my)
            self.btn_sim.update(mx, my)
            self.btn_back.update(mx, my)
            self._draw()
            pygame.display.flip()

    # ── drawing ───────────────────────────────────────────────────
    def _draw(self):
        _gradient_bg(self.screen)

        # Header
        header = self.f_title.render(
            f"{self.ls.league_name}  —  Matchday {self.ls.matchday} / {self.ls.total_matchdays}",
            True, GOLD)
        self.screen.blit(header, header.get_rect(centerx=SCR_W//2, y=10))

        if self.ls.season_over:
            done = self.f_sub.render("SEASON COMPLETE  —  Final standings below", True, (120,220,120))
            self.screen.blit(done, done.get_rect(centerx=SCR_W//2, y=48))

        # ── Left: standings table ─────────────────────────────────
        TBL_X, TBL_Y = 18, 70
        TBL_W        = 590
        col_widths   = [28, 200, 30, 30, 30, 30, 44, 44, 44]
        col_labels   = ['',  'Club', 'P', 'W', 'D', 'L', 'GF','GA','Pts']
        headers_y    = TBL_Y

        # Header row
        _panel(self.screen, (TBL_X, headers_y, TBL_W, 22), alpha=180, radius=6)
        cx = TBL_X + 4
        for i, (lbl, cw) in enumerate(zip(col_labels, col_widths)):
            s = self.f_tbl.render(lbl, True, GOLD)
            self.screen.blit(s, (cx + cw//2 - s.get_width()//2, headers_y+3))
            cx += cw

        # Data rows
        table = self.ls.sorted_table()
        ROW_H = 22
        for rank, rec in enumerate(table):
            ry  = headers_y + 24 + rank * ROW_H
            is_human = (rec.key == self.ls.human_key)
            row_bg   = (20, 50, 30, 180) if is_human else (10, 18, 45, 160)
            _panel(self.screen, (TBL_X, ry, TBL_W, ROW_H-1), alpha=row_bg[3], radius=4)
            if is_human:
                pygame.draw.rect(self.screen, (40,160,70),
                                 (TBL_X, ry, TBL_W, ROW_H-1), 1, border_radius=4)

            cx   = TBL_X + 4
            vals = [str(rank+1), rec.name, str(rec.P), str(rec.W), str(rec.D),
                    str(rec.L), str(rec.GF), str(rec.GA), str(rec.pts)]
            for i, (val, cw) in enumerate(zip(vals, col_widths)):
                col = GOLD if i == len(vals)-1 else (WHITE if is_human else GREY)
                # Truncate team name to fit
                txt = val
                if i == 1:
                    s = self.f_tbl_s.render(txt, True, rec.col if is_human else (180,180,200))
                    while s.get_width() > cw - 4 and len(txt) > 4:
                        txt = txt[:-1]
                        s   = self.f_tbl_s.render(txt+'…', True, rec.col if is_human else (180,180,200))
                    if txt != val:
                        s = self.f_tbl_s.render(txt+'…', True, rec.col if is_human else (180,180,200))
                else:
                    s = self.f_tbl_s.render(val, True, GOLD if (i == len(vals)-1) else col)
                self.screen.blit(s, (cx + cw//2 - s.get_width()//2, ry+4))
                cx += cw

        # ── Right: today's fixtures ───────────────────────────────
        FIX_X = TBL_X + TBL_W + 24
        FIX_W = SCR_W - FIX_X - 14
        fix_lbl = self.f_sub.render(
            f"Matchday {self.ls.matchday} Fixtures" if not self.ls.season_over else "Season Finished",
            True, (160, 180, 230))
        self.screen.blit(fix_lbl, (FIX_X, TBL_Y))

        fy = TBL_Y + 28
        fixtures_today = [f for f in self.ls.fixtures if f.matchday == self.ls.matchday]
        for fix in fixtures_today:
            is_human_fix = (fix.home == self.ls.human_key or fix.away == self.ls.human_key)
            fh = 34
            _panel(self.screen, (FIX_X, fy, FIX_W, fh), alpha=200, radius=8)
            if is_human_fix:
                pygame.draw.rect(self.screen, (40,160,70),
                                 (FIX_X, fy, FIX_W, fh), 1, border_radius=8)

            h_name = TEAMS[fix.home]['name']
            a_name = TEAMS[fix.away]['name']
            h_col  = TEAMS[fix.home]['hud_col']
            a_col  = TEAMS[fix.away]['hud_col']

            if fix.played:
                score_txt = f"{h_name}  {fix.home_goals} - {fix.away_goals}  {a_name}"
                sc = self.f_fix.render(score_txt, True, (180,220,180) if not is_human_fix else (120,255,120))
                self.screen.blit(sc, sc.get_rect(centerx=FIX_X+FIX_W//2, centery=fy+fh//2))
            else:
                hs = self.f_fix.render(h_name, True, h_col)
                vs = self.f_fix.render("vs", True, GREY)
                as_ = self.f_fix.render(a_name, True, a_col)
                mid = FIX_X + FIX_W//2
                self.screen.blit(vs, vs.get_rect(centerx=mid, centery=fy+fh//2))
                self.screen.blit(hs, hs.get_rect(right=mid-18, centery=fy+fh//2))
                self.screen.blit(as_, as_.get_rect(x=mid+18, centery=fy+fh//2))
                if is_human_fix:
                    you = self.f_small.render("← YOUR MATCH", True, (100,220,100))
                    self.screen.blit(you, you.get_rect(right=FIX_X+FIX_W-6, centery=fy+fh//2))

            fy += fh + 5
            if fy > SCR_H - 120:
                more = self.f_small.render(f"… and more fixtures", True, (70,80,110))
                self.screen.blit(more, (FIX_X, fy))
                break

        self.btn_play.draw(self.screen)
        self.btn_sim.draw(self.screen)
        self.btn_back.draw(self.screen)


# ── Post-Match Screen ─────────────────────────────────────────────
class PostMatchScreen:
    """Flash the result for 3 seconds then auto-continue."""

    def __init__(self, screen, clock, league: LeagueState, fixture: Fixture):
        self.screen  = screen
        self.clock   = clock
        self.ls      = league
        self.fixture = fixture
        self.f_xl    = pygame.font.SysFont("Georgia", 52, bold=True)
        self.f_big   = pygame.font.SysFont("Georgia", 32, bold=True)
        self.f_med   = pygame.font.SysFont("Georgia", 20, bold=True)
        self.f_btn   = pygame.font.SysFont("Georgia", 20, bold=True)
        self.f_small = pygame.font.SysFont("Arial",   13)
        self._timer  = FPS * 4   # 4 seconds auto-continue
        self.btn_cont = Btn("CONTINUE  →",
            (SCR_W//2 - 130, SCR_H - 74, 260, 50), self.f_btn,
            bg=(20,80,36), bg_h=(30,120,54), tc=GOLD, bc=(40,160,70))

    def run(self):
        while True:
            self.clock.tick(FPS)
            self._timer -= 1
            mx, my = pygame.mouse.get_pos()
            self.btn_cont.update(mx, my)

            for ev in pygame.event.get():
                if ev.type == pygame.QUIT:
                    pygame.quit(); sys.exit()
                if ev.type == pygame.KEYDOWN:
                    return
                if ev.type == pygame.MOUSEBUTTONDOWN and ev.button == 1:
                    if self.btn_cont.clicked(mx, my):
                        return

            if self._timer <= 0:
                return

            self._draw()
            pygame.display.flip()

    def _draw(self):
        _gradient_bg(self.screen)
        fix  = self.fixture
        h_n  = TEAMS[fix.home]['name']
        a_n  = TEAMS[fix.away]['name']
        h_c  = TEAMS[fix.home]['hud_col']
        a_c  = TEAMS[fix.away]['hud_col']

        is_hk = self.ls.human_key
        if fix.home_goals > fix.away_goals:
            winner = fix.home
        elif fix.away_goals > fix.home_goals:
            winner = fix.away
        else:
            winner = None

        result_txt = "DRAW!" if winner is None else \
                     ("WIN!" if winner == is_hk else "DEFEAT!")
        result_col = (255,220,0) if winner is None else \
                     ((100,255,120) if winner == is_hk else (255,80,80))

        rt = self.f_xl.render(result_txt, True, result_col)
        self.screen.blit(rt, rt.get_rect(centerx=SCR_W//2, y=140))

        hs = self.f_big.render(h_n, True, h_c)
        sc = self.f_big.render(f"{fix.home_goals}  –  {fix.away_goals}", True, WHITE)
        as_ = self.f_big.render(a_n, True, a_c)
        mid = SCR_W//2
        self.screen.blit(sc,  sc.get_rect(centerx=mid, y=230))
        self.screen.blit(hs,  hs.get_rect(right=mid-sc.get_width()//2-20, centery=246))
        self.screen.blit(as_, as_.get_rect(x=mid+sc.get_width()//2+20, centery=246))

        # League position
        table = self.ls.sorted_table()
        for pos, rec in enumerate(table):
            if rec.key == is_hk:
                pos_txt = f"Your position:  {pos+1} / {len(table)}   —   {rec.pts} pts"
                ps = self.f_med.render(pos_txt, True, (160,180,220))
                self.screen.blit(ps, ps.get_rect(centerx=SCR_W//2, y=310))
                break

        cd = max(0, self._timer // FPS)
        hint = self.f_small.render(f"Auto-continuing in {cd}s  ·  press any key or click", True, (80,90,120))
        self.screen.blit(hint, hint.get_rect(centerx=SCR_W//2, y=SCR_H-100))
        self.btn_cont.draw(self.screen)


# ── Season End Screen ─────────────────────────────────────────────
class SeasonEndScreen:
    def __init__(self, screen, clock, league: LeagueState):
        self.screen = screen
        self.clock  = clock
        self.ls     = league
        self.f_xl   = pygame.font.SysFont("Georgia", 56, bold=True)
        self.f_big  = pygame.font.SysFont("Georgia", 28, bold=True)
        self.f_tbl  = pygame.font.SysFont("Arial",   13, bold=True)
        self.f_btn  = pygame.font.SysFont("Georgia", 20, bold=True)
        self.btn_menu = Btn("← MAIN MENU",
            (SCR_W//2 - 140, SCR_H - 72, 280, 50), self.f_btn,
            bg=(26,26,52), bg_h=(44,44,90), tc=WHITE)

    def run(self):
        while True:
            self.clock.tick(FPS)
            mx, my = pygame.mouse.get_pos()
            self.btn_menu.update(mx, my)
            for ev in pygame.event.get():
                if ev.type == pygame.QUIT:
                    pygame.quit(); sys.exit()
                if ev.type == pygame.MOUSEBUTTONDOWN and ev.button == 1:
                    if self.btn_menu.clicked(mx, my):
                        return
            self._draw()
            pygame.display.flip()

    def _draw(self):
        _gradient_bg(self.screen)
        title = self.f_xl.render("SEASON OVER", True, GOLD)
        self.screen.blit(title, title.get_rect(centerx=SCR_W//2, y=20))

        table = self.ls.sorted_table()
        champ = table[0]
        is_champ = (champ.key == self.ls.human_key)
        sub_txt = f"🏆  {champ.name}  are Champions!" + ("  THAT'S YOU!" if is_champ else "")
        sub_col = (255,220,0) if is_champ else (200,200,200)
        sub = self.f_big.render(sub_txt, True, sub_col)
        self.screen.blit(sub, sub.get_rect(centerx=SCR_W//2, y=90))

        # Full table
        COL_W  = [28, 220, 34, 34, 34, 34, 44, 44, 50]
        LABELS = ['',  'Club', 'P', 'W', 'D', 'L','GF','GA','Pts']
        TX, TY, TW = SCR_W//2 - sum(COL_W)//2, 144, sum(COL_W)
        _panel(self.screen, (TX, TY, TW, 22), radius=6)
        cx = TX + 4
        for lbl, cw in zip(LABELS, COL_W):
            s = self.f_tbl.render(lbl, True, GOLD)
            self.screen.blit(s, (cx+cw//2-s.get_width()//2, TY+3))
            cx += cw

        ROW_H = 21
        for rank, rec in enumerate(table):
            ry  = TY + 24 + rank*ROW_H
            if ry > SCR_H - 80:
                break
            is_h = (rec.key == self.ls.human_key)
            bg_a = (20,50,30,180) if is_h else (10,18,45,160)
            _panel(self.screen, (TX, ry, TW, ROW_H-1), alpha=180, radius=3)
            if is_h:
                pygame.draw.rect(self.screen, (40,160,70), (TX, ry, TW, ROW_H-1), 1, border_radius=3)
            if rank == 0:
                pygame.draw.rect(self.screen, (180,150,0), (TX, ry, TW, ROW_H-1), 1, border_radius=3)

            vals = [str(rank+1), rec.name, str(rec.P), str(rec.W), str(rec.D),
                    str(rec.L), str(rec.GF), str(rec.GA), str(rec.pts)]
            cx = TX + 4
            for i, (val, cw) in enumerate(zip(vals, COL_W)):
                if i == 1:
                    txt = val
                    s   = self.f_tbl.render(txt, True, rec.col)
                    while s.get_width() > cw-4 and len(txt) > 4:
                        txt = txt[:-1]
                        s   = self.f_tbl.render(txt+'…', True, rec.col)
                else:
                    fc  = GOLD if i == len(vals)-1 else (WHITE if is_h else GREY)
                    s   = self.f_tbl.render(val, True, fc)
                self.screen.blit(s, (cx+cw//2-s.get_width()//2, ry+3))
                cx += cw

        self.btn_menu.draw(self.screen)
