"""menu.py – Main menu and two-step country → team selection."""
import pygame
import sys
import math

from constants import SCR_W, SCR_H, FPS, TEAMS

# ── Palette ──────────────────────────────────────────────────────
BG_TOP  = (6,  10,  22)
BG_BOT  = (14, 28,  52)
GOLD    = (255, 210,  40)
WHITE   = (240, 240, 240)
GREY    = (110, 110, 130)
GREEN   = ( 30, 140,  60)
RED_COL = (160,  30,  30)

# ── Country metadata ─────────────────────────────────────────────
# flag_cols: list of (colour, fraction) left→right stripes
COUNTRIES = {
    'Spain': {
        'flag_cols': [
            ((198,  11,  30), 0.25),
            ((255, 196,   0), 0.50),
            ((198,  11,  30), 0.25),
        ],
        'label_col': (255, 196, 0),
    },
    'England': {
        'flag_cols': [
            ((255, 255, 255), 1.0),   # white base – cross drawn separately
        ],
        'cross': (198, 11, 30),
        'label_col': (220, 60, 60),
    },
    'Germany': {
        'flag_cols': [
            ((0,   0,   0), 0.333),
            ((221, 0,   0), 0.333),
            ((255, 206,  0), 0.334),
        ],
        'label_col': (255, 206, 0),
    },
}

# ── Group teams by country ────────────────────────────────────────
def _teams_by_country():
    grouped = {}
    for key, data in TEAMS.items():
        c = data['country']
        grouped.setdefault(c, []).append(key)
    return grouped

TEAMS_BY_COUNTRY = _teams_by_country()
COUNTRY_ORDER    = ['Spain', 'England', 'Germany']


# ── Helpers ──────────────────────────────────────────────────────
def _gradient_bg(surf):
    for y in range(SCR_H):
        t   = y / SCR_H
        col = tuple(int(BG_TOP[i] + (BG_BOT[i] - BG_TOP[i]) * t) for i in range(3))
        pygame.draw.line(surf, col, (0, y), (SCR_W, y))


def _draw_pitch_lines(surf):
    tmp = pygame.Surface((SCR_W, SCR_H), pygame.SRCALPHA)
    lc  = (255, 255, 255, 14)
    pygame.draw.rect(tmp, lc, (80, 100, SCR_W - 160, SCR_H - 160), 2, border_radius=16)
    pygame.draw.line(tmp, lc, (SCR_W//2, 100), (SCR_W//2, SCR_H - 60), 2)
    pygame.draw.circle(tmp, lc, (SCR_W//2, SCR_H//2), 70, 2)
    surf.blit(tmp, (0, 0))


def _draw_flag(surf, rect, country):
    """Draw a mini flag inside rect."""
    info = COUNTRIES.get(country, {})
    cols = info.get('flag_cols', [((100, 100, 100), 1.0)])
    x, y, w, h = rect
    dx = x
    for col, frac in cols:
        fw = int(w * frac)
        pygame.draw.rect(surf, col, (dx, y, fw, h))
        dx += fw
    # England cross
    if info.get('cross'):
        cc = info['cross']
        cx2, cy2 = x + w//2, y + h//2
        pygame.draw.rect(surf, cc, (x, cy2-2, w, 5))
        pygame.draw.rect(surf, cc, (cx2-2, y, 5, h))
    # Border
    pygame.draw.rect(surf, (80, 80, 80), rect, 1)


def draw_kit_preview(surf, cx, cy, kit):
    """Mini shirt/shorts/socks preview centred at (cx, cy)."""
    shirt1 = kit['shirt1']
    shirt2 = kit.get('shirt2', shirt1)
    shorts = kit['shorts']
    sock   = kit['socks']
    body   = pygame.Rect(cx-22, cy-20, 44, 40)

    if kit.get('stripe'):
        cols = kit.get('stripe_cols', [shirt1, shirt2, shirt1])
        sw   = max(2, body.w // len(cols))
        for si, sc in enumerate(cols):
            clip  = pygame.Rect(body.x + si*sw, body.y, sw, body.h)
            inter = body.clip(clip)
            if inter.w > 0:
                pygame.draw.rect(surf, sc, inter, border_radius=4)
    elif kit.get('half_half'):
        pygame.draw.rect(surf, shirt1, pygame.Rect(body.x, body.y, body.w//2, body.h), border_radius=4)
        pygame.draw.rect(surf, shirt2, pygame.Rect(body.x+body.w//2, body.y, body.w//2, body.h), border_radius=4)
    elif kit.get('sash'):
        pygame.draw.rect(surf, shirt1, body, border_radius=4)
        pts = [(body.x+body.w//3, body.y), (body.x+body.w, body.y), (body.x+body.w, body.y+body.h//3)]
        pygame.draw.polygon(surf, shirt2, pts)
    else:
        pygame.draw.rect(surf, shirt1, body, border_radius=4)

    pygame.draw.rect(surf, (0,0,0), body, 1, border_radius=4)
    # Sleeves
    pygame.draw.rect(surf, shirt1, (cx-32, cy-12, 11, 18), border_radius=3)
    pygame.draw.rect(surf, shirt2, (cx+21, cy-12, 11, 18), border_radius=3)
    # Shorts
    pygame.draw.rect(surf, shorts, (cx-16, cy+18, 32, 17), border_radius=3)
    # Socks
    for so in (-8, 8):
        pygame.draw.rect(surf, sock, (cx+so-4, cy+35, 8, 10), border_radius=2)


# ── Generic button ───────────────────────────────────────────────
class Button:
    def __init__(self, text, rect, enabled=True,
                 col_normal=(30,44,80), col_hover=(50,74,140),
                 col_disabled=(24,28,40), text_col=WHITE,
                 text_col_disabled=(50,50,50), font=None, border_col=None):
        self.text, self.rect   = text, pygame.Rect(rect)
        self.enabled           = enabled
        self.cn, self.ch, self.cd  = col_normal, col_hover, col_disabled
        self.tc, self.tcd      = text_col, text_col_disabled
        self.font, self.border = font, border_col
        self._hover = False
        self._pulse = 0.0

    def update(self, mx, my):
        self._hover = self.enabled and self.rect.collidepoint(mx, my)
        self._pulse = (self._pulse + 0.08) % (math.pi*2)

    def draw(self, surf):
        col = self.cd if not self.enabled else (self.ch if self._hover else self.cn)
        pygame.draw.rect(surf, col, self.rect, border_radius=10)
        bc  = self.border if self.border else (GOLD if self._hover and self.enabled else (52,65,100))
        if not self.enabled: bc = (36,40,56)
        pygame.draw.rect(surf, bc, self.rect, 2, border_radius=10)
        tc  = self.tc if self.enabled else self.tcd
        lbl = self.font.render(self.text, True, tc)
        surf.blit(lbl, lbl.get_rect(center=self.rect.center))
        if self._hover and self.enabled:
            g = pygame.Surface((self.rect.w+12, self.rect.h+12), pygame.SRCALPHA)
            pygame.draw.rect(g, (*GOLD, int(28+18*math.sin(self._pulse))), g.get_rect(), border_radius=12)
            surf.blit(g, (self.rect.x-6, self.rect.y-6))

    def clicked(self, mx, my):
        return self.enabled and self.rect.collidepoint(mx, my)


# ── Country button (flag + name) ─────────────────────────────────
class CountryButton:
    W, H = 180, 72

    def __init__(self, country, rect, font):
        self.country  = country
        self.rect     = pygame.Rect(rect)
        self.font     = font
        self.selected = False
        self._hover   = False

    def update(self, mx, my):
        self._hover = self.rect.collidepoint(mx, my)

    def draw(self, surf):
        if self.selected:
            bg = (30, 55, 110)
            bc = GOLD
            bw = 3
        elif self._hover:
            bg = (22, 40, 80)
            bc = (120, 160, 220)
            bw = 2
        else:
            bg = (14, 22, 50)
            bc = (40, 55, 90)
            bw = 1

        pygame.draw.rect(surf, bg, self.rect, border_radius=12)
        pygame.draw.rect(surf, bc, self.rect, bw, border_radius=12)

        # Flag
        flag_r = (self.rect.x+10, self.rect.y+18, 48, 30)
        _draw_flag(surf, flag_r, self.country)

        # Label
        info    = COUNTRIES.get(self.country, {})
        lc      = info.get('label_col', WHITE)
        lbl     = self.font.render(self.country, True, lc if self.selected else WHITE)
        surf.blit(lbl, lbl.get_rect(x=self.rect.x+68, centery=self.rect.centery))

        if self.selected:
            chk = self.font.render('▶', True, GOLD)
            surf.blit(chk, chk.get_rect(right=self.rect.right-8, centery=self.rect.centery))

    def clicked(self, mx, my):
        return self.rect.collidepoint(mx, my)


# ── Team card ────────────────────────────────────────────────────
class TeamCard:
    W, H = 148, 122

    def __init__(self, key, rect, font_name, font_small):
        self.key      = key
        self.rect     = pygame.Rect(rect)
        self.fn       = font_name
        self.fs       = font_small
        self.selected = False
        self._hover   = False

    def update(self, mx, my):
        self._hover = self.rect.collidepoint(mx, my)

    def draw(self, surf):
        kit = TEAMS[self.key]
        if self.selected:
            bg, bc, bw = (34, 58, 108), GOLD, 3
        elif self._hover:
            bg, bc, bw = (22, 38, 80), (100, 140, 210), 2
        else:
            bg, bc, bw = (14, 22, 50), (38, 52, 86), 1

        pygame.draw.rect(surf, bg, self.rect, border_radius=12)
        pygame.draw.rect(surf, bc, self.rect, bw, border_radius=12)

        draw_kit_preview(surf, self.rect.centerx, self.rect.y+48, kit)

        name = kit['name']
        ns   = self.fn.render(name, True, WHITE if (self.selected or self._hover) else GREY)
        if ns.get_width() > self.rect.w - 8:
            while ns.get_width() > self.rect.w - 8 and len(name) > 3:
                name = name[:-1]
            ns = self.fn.render(name+'…', True, WHITE if (self.selected or self._hover) else GREY)
        surf.blit(ns, ns.get_rect(centerx=self.rect.centerx, y=self.rect.y+85))

        if self.selected:
            chk = self.fs.render('✓ PICKED', True, GOLD)
            surf.blit(chk, chk.get_rect(centerx=self.rect.centerx, y=self.rect.y+6))

    def clicked(self, mx, my):
        return self.rect.collidepoint(mx, my)


# ── Side panel: country list + team grid for ONE side ───────────
class SidePanel:
    """
    Left column  : country buttons (stacked)
    Right area   : team cards for selected country (grid, scrollable)
    """
    COUNTRY_COL_W = 200
    CARD_COLS     = 4
    CARD_GAP      = 10

    def __init__(self, rect, label, label_col, font_title, font_country, font_card, font_small):
        self.rect       = pygame.Rect(rect)
        self.label      = label
        self.label_col  = label_col
        self.ft         = font_title
        self.fc         = font_country
        self.fcard      = font_card
        self.fsmall     = font_small

        self.selected_country = None
        self.selected_team    = None   # key string
        self._scroll          = 0

        # Build country buttons (left column)
        self._country_btns = []
        cb_h   = 64
        cb_gap = 10
        cy     = self.rect.y + 36
        for country in COUNTRY_ORDER:
            if country not in TEAMS_BY_COUNTRY:
                continue
            self._country_btns.append(
                CountryButton(country,
                              (self.rect.x + 6, cy, self.COUNTRY_COL_W - 12, cb_h),
                              font_country))
            cy += cb_h + cb_gap

        self._team_cards = []   # rebuilt when country changes

    # ── internal helpers ──────────────────────────────────────────
    def _team_area(self):
        """pygame.Rect of the team-card display area."""
        tx = self.rect.x + self.COUNTRY_COL_W + 8
        ty = self.rect.y + 36
        tw = self.rect.right - tx - 4
        th = self.rect.h - 40
        return pygame.Rect(tx, ty, tw, th)

    def _rebuild_cards(self, exclude_key=None):
        self._team_cards = []
        self._scroll     = 0
        if not self.selected_country:
            return
        keys   = [k for k in TEAMS_BY_COUNTRY.get(self.selected_country, [])
                  if k != exclude_key]
        ta     = self._team_area()
        cw, ch = TeamCard.W, TeamCard.H
        gap    = self.CARD_GAP
        cols   = max(1, (ta.w + gap) // (cw + gap))
        for i, key in enumerate(keys):
            col = i % cols
            row = i // cols
            x   = ta.x + col*(cw+gap)
            y   = ta.y + row*(ch+gap)
            card = TeamCard(key, (x, y, cw, ch), self.fcard, self.fsmall)
            if key == self.selected_team:
                card.selected = True
            self._team_cards.append(card)

    def _card_rows_height(self):
        if not self._team_cards:
            return 0
        ta   = self._team_area()
        cw   = TeamCard.W
        gap  = self.CARD_GAP
        cols = max(1, (ta.w + gap) // (cw + gap))
        rows = math.ceil(len(self._team_cards) / cols)
        return rows * (TeamCard.H + gap)

    # ── public API ───────────────────────────────────────────────
    def set_exclude(self, key):
        """Call when the other panel picks a team."""
        self._rebuild_cards(exclude_key=key)

    def handle_event(self, ev):
        """Returns selected team key if changed, else None."""
        mx, my = pygame.mouse.get_pos()

        if ev.type == pygame.MOUSEBUTTONDOWN:
            # Scroll in team area
            ta = self._team_area()
            if ev.button == 4 and ta.collidepoint(ev.pos):
                self._scroll = max(0, self._scroll - 36)
            elif ev.button == 5 and ta.collidepoint(ev.pos):
                max_s = max(0, self._card_rows_height() - ta.h)
                self._scroll = min(max_s, self._scroll + 36)

            elif ev.button == 1:
                # Country buttons
                for cb in self._country_btns:
                    if cb.clicked(*ev.pos):
                        if cb.country != self.selected_country:
                            self.selected_country = cb.country
                            old_team = self.selected_team
                            if old_team and TEAMS[old_team]['country'] != cb.country:
                                self.selected_team = None
                            self._rebuild_cards()
                            for c in self._country_btns:
                                c.selected = (c.country == cb.country)
                        return None

                # Team cards (apply scroll offset for hit-test)
                ta = self._team_area()
                for card in self._team_cards:
                    hit = pygame.Rect(card.rect.x, card.rect.y - self._scroll,
                                      card.rect.w, card.rect.h)
                    if hit.collidepoint(*ev.pos) and ta.collidepoint(*ev.pos):
                        for c in self._team_cards:
                            c.selected = False
                        card.selected  = True
                        self.selected_team = card.key
                        return card.key

        return None

    def update(self, mx, my):
        for cb in self._country_btns:
            cb.update(mx, my)
        ta = self._team_area()
        for card in self._team_cards:
            hit = pygame.Rect(card.rect.x, card.rect.y - self._scroll,
                              card.rect.w, card.rect.h)
            card._hover = hit.collidepoint(mx, my) and ta.collidepoint(mx, my)

    def draw(self, surf):
        # Panel background
        pygame.draw.rect(surf, (10, 16, 38), self.rect, border_radius=14)
        pygame.draw.rect(surf, (40, 55, 100), self.rect, 1, border_radius=14)

        # Label
        lbl = self.ft.render(self.label, True, self.label_col)
        surf.blit(lbl, lbl.get_rect(x=self.rect.x+10, y=self.rect.y+8))

        # Divider between country col and card area
        dx = self.rect.x + self.COUNTRY_COL_W + 2
        pygame.draw.line(surf, (40, 55, 100),
                         (dx, self.rect.y+6), (dx, self.rect.bottom-6), 1)

        # Country buttons
        for cb in self._country_btns:
            cb.draw(surf)

        # Prompt if no country picked
        ta = self._team_area()
        if not self.selected_country:
            hint = self.fsmall.render('← Pick a country', True, (70, 90, 140))
            surf.blit(hint, hint.get_rect(centerx=ta.centerx, centery=ta.centery))
        else:
            # Team cards (clipped + scrolled)
            clip_surf = pygame.Surface((ta.w, ta.h), pygame.SRCALPHA)
            for card in self._team_cards:
                cr = pygame.Rect(card.rect.x - ta.x,
                                 card.rect.y - ta.y - self._scroll,
                                 card.rect.w, card.rect.h)
                if cr.bottom < 0 or cr.top > ta.h:
                    continue
                # draw into clip surface
                tmp_card = TeamCard(card.key, cr, self.fcard, self.fsmall)
                tmp_card.selected = card.selected
                tmp_card._hover   = card._hover
                tmp_card.draw(clip_surf)
            surf.blit(clip_surf, ta.topleft)

            # Scroll bar
            total = self._card_rows_height()
            if total > ta.h:
                sb_x  = ta.right + 3
                bar_h = max(20, int(ta.h * ta.h / total))
                bar_y = ta.y + int(self._scroll / total * ta.h)
                pygame.draw.rect(surf, (30,45,80),  (sb_x, ta.y, 4, ta.h), border_radius=2)
                pygame.draw.rect(surf, GOLD, (sb_x, bar_y, 4, bar_h), border_radius=2)

            # "No teams available" message
            if not self._team_cards:
                msg = self.fsmall.render('All teams in this country are taken', True, (120,80,80))
                surf.blit(msg, msg.get_rect(centerx=ta.centerx, centery=ta.centery))


# ── Main Menu ─────────────────────────────────────────────────────
class MainMenu:
    def __init__(self, screen, clock):
        self.screen = screen
        self.clock  = clock
        self.f_title = pygame.font.SysFont("Georgia", 64, bold=True)
        self.f_sub   = pygame.font.SysFont("Georgia", 22, bold=True)
        self.f_btn   = pygame.font.SysFont("Georgia", 26, bold=True)
        self.f_tiny  = pygame.font.SysFont("Arial",   13)

        bw, bh = 320, 58
        bx     = SCR_W//2 - bw//2
        self.buttons = [
            Button("⚡  QUICK PLAY", (bx, 330, bw, bh), enabled=True,
                   col_normal=(20,80,36), col_hover=(30,120,54),
                   text_col=GOLD, border_col=(40,160,70), font=self.f_btn),
            Button("🏆  LEAGUE  (COMING SOON)", (bx, 410, bw, bh),
                   enabled=False, font=self.f_btn),
            Button("⭐  CHAMPIONS LEAGUE  (COMING SOON)", (bx-40, 490, bw+80, bh),
                   enabled=False, font=self.f_btn),
            Button("✕  QUIT", (bx, 578, bw, bh), enabled=True,
                   col_normal=(60,14,14), col_hover=(100,20,20),
                   text_col=(240,100,100), font=self.f_btn),
        ]
        self._t = 0.0

    def run(self):
        while True:
            self.clock.tick(FPS)
            mx, my = pygame.mouse.get_pos()
            self._t += 0.03
            for ev in pygame.event.get():
                if ev.type == pygame.QUIT:
                    pygame.quit(); sys.exit()
                if ev.type == pygame.KEYDOWN and ev.key == pygame.K_ESCAPE:
                    pygame.quit(); sys.exit()
                if ev.type == pygame.MOUSEBUTTONDOWN and ev.button == 1:
                    if self.buttons[0].clicked(mx, my): return 'quick_play'
                    if self.buttons[3].clicked(mx, my): pygame.quit(); sys.exit()
            for b in self.buttons: b.update(mx, my)
            self._draw()
            pygame.display.flip()

    def _draw(self):
        _gradient_bg(self.screen)
        _draw_pitch_lines(self.screen)
        glow = pygame.Surface((600, 120), pygame.SRCALPHA)
        pygame.draw.ellipse(glow, (255,200,0, int(40+20*math.sin(self._t))), glow.get_rect())
        self.screen.blit(glow, (SCR_W//2-300, 130))
        shadow = self.f_title.render("FOOTBALL 3D", True, (40,30,0))
        title  = self.f_title.render("FOOTBALL 3D", True, GOLD)
        self.screen.blit(shadow, shadow.get_rect(centerx=SCR_W//2+3, y=153))
        self.screen.blit(title,  title.get_rect(centerx=SCR_W//2,    y=150))
        sub = self.f_sub.render("THE BEAUTIFUL GAME", True, (120,150,200))
        self.screen.blit(sub, sub.get_rect(centerx=SCR_W//2, y=226))
        for b in self.buttons: b.draw(self.screen)
        ver = self.f_tiny.render("v2.0  ·  22 clubs  ·  WASD / arrows in game", True, (55,65,90))
        self.screen.blit(ver, ver.get_rect(centerx=SCR_W//2, y=SCR_H-28))


# ── Team Selection ────────────────────────────────────────────────
class TeamSelectScreen:
    """
    Two side-by-side SidePanels.
    Left panel  = your team  (green header)
    Right panel = CPU team   (red header)

    Each panel: country column on its left, team card grid on its right.
    Step 1 → click a country flag
    Step 2 → click a team card
    """

    PAD    = 14
    GAP    = 14   # gap between the two panels

    def __init__(self, screen, clock):
        self.screen = screen
        self.clock  = clock

        # Fonts
        self.f_title   = pygame.font.SysFont("Georgia", 36, bold=True)
        self.f_panel   = pygame.font.SysFont("Georgia", 14, bold=True)
        self.f_country = pygame.font.SysFont("Arial",   13, bold=True)
        self.f_card    = pygame.font.SysFont("Arial",   11, bold=True)
        self.f_small   = pygame.font.SysFont("Arial",   10)
        self.f_btn     = pygame.font.SysFont("Georgia", 22, bold=True)

        # Layout
        title_h  = 52
        bottom_h = 62
        panel_h  = SCR_H - title_h - bottom_h - self.PAD*2
        panel_w  = (SCR_W - self.PAD*2 - self.GAP) // 2

        self.panel_a = SidePanel(
            (self.PAD, title_h + self.PAD, panel_w, panel_h),
            "YOUR TEAM", (100, 220, 120),
            self.f_panel, self.f_country, self.f_card, self.f_small)

        self.panel_b = SidePanel(
            (self.PAD + panel_w + self.GAP, title_h + self.PAD, panel_w, panel_h),
            "CPU OPPONENT", (220, 110, 100),
            self.f_panel, self.f_country, self.f_card, self.f_small)

        bh = 48
        self.btn_play = Button("▶  KICK OFF!",
            (SCR_W//2 - 120, SCR_H - bh - 8, 240, bh), enabled=False,
            col_normal=(20,80,36), col_hover=(30,120,54), col_disabled=(20,30,20),
            text_col=GOLD, text_col_disabled=(40,60,40),
            border_col=(40,160,70), font=self.f_btn)
        self.btn_back = Button("← BACK",
            (self.PAD, SCR_H - bh - 8, 120, bh), enabled=True,
            col_normal=(26,26,52), col_hover=(44,44,90), text_col=WHITE,
            font=self.f_btn)
        self.f_summary = pygame.font.SysFont("Arial", 13, bold=True)

    def _refresh(self):
        ka = self.panel_a.selected_team
        kb = self.panel_b.selected_team
        self.panel_a.set_exclude(kb)
        self.panel_b.set_exclude(ka)
        self.btn_play.enabled = (ka is not None and kb is not None and ka != kb)

    def run(self):
        while True:
            self.clock.tick(FPS)
            mx, my = pygame.mouse.get_pos()

            for ev in pygame.event.get():
                if ev.type == pygame.QUIT:
                    pygame.quit(); sys.exit()
                if ev.type == pygame.KEYDOWN and ev.key == pygame.K_ESCAPE:
                    return None

                r = self.panel_a.handle_event(ev)
                if r: self._refresh()
                r = self.panel_b.handle_event(ev)
                if r: self._refresh()

                if ev.type == pygame.MOUSEBUTTONDOWN and ev.button == 1:
                    if self.btn_back.clicked(mx, my): return None
                    if self.btn_play.clicked(mx, my):
                        return (self.panel_a.selected_team, self.panel_b.selected_team)

            self.panel_a.update(mx, my)
            self.panel_b.update(mx, my)
            self.btn_play.update(mx, my)
            self.btn_back.update(mx, my)
            self._draw()
            pygame.display.flip()

    def _draw(self):
        _gradient_bg(self.screen)
        _draw_pitch_lines(self.screen)

        # Title
        title = self.f_title.render("CHOOSE YOUR TEAMS", True, GOLD)
        self.screen.blit(title, title.get_rect(centerx=SCR_W//2, y=10))

        self.panel_a.draw(self.screen)
        self.panel_b.draw(self.screen)

        # VS divider
        vs = self.f_title.render("VS", True, (60, 80, 140))
        self.screen.blit(vs, vs.get_rect(centerx=SCR_W//2, centery=SCR_H//2))

        # Summary strip
        ka = self.panel_a.selected_team
        kb = self.panel_b.selected_team
        a_name = TEAMS[ka]['name'] if ka else '—  (pick country then team)'
        b_name = TEAMS[kb]['name'] if kb else '—  (pick country then team)'
        summary = self.f_summary.render(
            f"You: {a_name}    vs    CPU: {b_name}", True, (160,170,200))
        self.screen.blit(summary, summary.get_rect(centerx=SCR_W//2, y=SCR_H - 62))

        self.btn_play.draw(self.screen)
        self.btn_back.draw(self.screen)
