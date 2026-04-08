"""menu.py – Main menu and team selection screens."""
import pygame
import sys
import math

from constants import SCR_W, SCR_H, FPS, TEAMS

# ── Colour palette ────────────────────────────────────────────────
BG_TOP    = (6,  10,  22)
BG_BOT    = (14, 28,  52)
GOLD      = (255, 210,  40)
GOLD_DIM  = (160, 130,  20)
WHITE     = (240, 240, 240)
GREY      = (130, 130, 130)
DARK      = (20,  24,  38)
PANEL_BG  = (12,  18,  36, 210)
GREEN_F   = (30, 140,  60)


def _gradient_bg(surf):
    for y in range(SCR_H):
        t   = y / SCR_H
        col = tuple(int(BG_TOP[i] + (BG_BOT[i] - BG_TOP[i]) * t) for i in range(3))
        pygame.draw.line(surf, col, (0, y), (SCR_W, y))


def _draw_pitch_lines(surf):
    """Faint decorative pitch graphic behind the menu."""
    col = (255, 255, 255, 14)
    # We draw directly with low-alpha lines on a temp surface
    tmp = pygame.Surface((SCR_W, SCR_H), pygame.SRCALPHA)
    lc  = (255, 255, 255, 18)
    # outer rect
    pygame.draw.rect(tmp, lc, (120, 180, SCR_W - 240, SCR_H - 280), 2, border_radius=16)
    # centre line
    pygame.draw.line(tmp, lc, (SCR_W // 2, 180), (SCR_W // 2, SCR_H - 100), 2)
    # centre circle
    pygame.draw.circle(tmp, lc, (SCR_W // 2, SCR_H // 2 + 40), 80, 2)
    # penalty boxes
    pb_w, pb_h = 190, 120
    pygame.draw.rect(tmp, lc, (120, SCR_H // 2 - pb_h // 2 + 40, pb_w, pb_h), 2)
    pygame.draw.rect(tmp, lc, (SCR_W - 120 - pb_w, SCR_H // 2 - pb_h // 2 + 40, pb_w, pb_h), 2)
    surf.blit(tmp, (0, 0))


class Button:
    def __init__(self, text, rect, enabled=True,
                 col_normal=(30, 44, 80), col_hover=(50, 74, 140),
                 col_disabled=(28, 32, 44), text_col=WHITE,
                 text_col_disabled=(60, 60, 60), font=None, border_col=None):
        self.text      = text
        self.rect      = pygame.Rect(rect)
        self.enabled   = enabled
        self.cn        = col_normal
        self.ch        = col_hover
        self.cd        = col_disabled
        self.tc        = text_col
        self.tcd       = text_col_disabled
        self.font      = font
        self.border    = border_col
        self._hover    = False
        self._pulse    = 0.0

    def update(self, mx, my):
        self._hover = self.enabled and self.rect.collidepoint(mx, my)
        self._pulse = (self._pulse + 0.08) % (math.pi * 2)

    def draw(self, surf):
        if not self.enabled:
            col = self.cd
        elif self._hover:
            col = self.ch
        else:
            col = self.cn

        pygame.draw.rect(surf, col, self.rect, border_radius=10)
        bc = self.border if self.border else (
            GOLD if self._hover and self.enabled else (55, 68, 100)
        )
        if not self.enabled:
            bc = (38, 42, 58)
        pygame.draw.rect(surf, bc, self.rect, 2, border_radius=10)

        tc = self.tc if self.enabled else self.tcd
        lbl = self.font.render(self.text, True, tc)
        surf.blit(lbl, lbl.get_rect(center=self.rect.center))

        if self._hover and self.enabled:
            glow = pygame.Surface((self.rect.w + 12, self.rect.h + 12), pygame.SRCALPHA)
            alpha = int(30 + 20 * math.sin(self._pulse))
            pygame.draw.rect(glow, (*GOLD, alpha),
                             glow.get_rect(), border_radius=12)
            surf.blit(glow, (self.rect.x - 6, self.rect.y - 6))

    def clicked(self, mx, my):
        return self.enabled and self.rect.collidepoint(mx, my)


class TeamCard:
    """Clickable team card showing badge colours and name."""
    def __init__(self, team_key, rect, font_name, font_small):
        self.key       = team_key
        self.data      = TEAMS[team_key]
        self.rect      = pygame.Rect(rect)
        self.fn        = font_name
        self.fs        = font_small
        self._hover    = False
        self._selected = False
        self._pulse    = 0.0

    def update(self, mx, my):
        self._hover = self.rect.collidepoint(mx, my)
        self._pulse = (self._pulse + 0.07) % (math.pi * 2)

    def select(self, v):
        self._selected = v

    def draw(self, surf):
        kit    = self.data
        shirt1 = kit['shirt1']
        shirt2 = kit.get('shirt2', shirt1)
        shorts = kit['shorts']
        sock   = kit['socks']

        bg = (30, 44, 88) if self._hover or self._selected else (18, 26, 52)
        pygame.draw.rect(surf, bg, self.rect, border_radius=14)

        if self._selected:
            bc     = GOLD
            bwidth = 3
        elif self._hover:
            bc     = (120, 160, 240)
            bwidth = 2
        else:
            bc     = (45, 58, 90)
            bwidth = 1
        pygame.draw.rect(surf, bc, self.rect, bwidth, border_radius=14)

        # ── Kit mini-preview ──────────────────────────────────────
        cx = self.rect.centerx
        cy = self.rect.y + 68

        # Draw a simplified shirt shape
        shirt_rect = pygame.Rect(cx - 28, cy - 26, 56, 50)
        # Split shirt left/right for two-colour kits
        left_half  = pygame.Rect(cx - 28, cy - 26, 28, 50)
        right_half = pygame.Rect(cx,      cy - 26, 28, 50)
        pygame.draw.rect(surf, shirt1, left_half,  border_radius=8)
        pygame.draw.rect(surf, shirt2, right_half, border_radius=8)
        # Outline
        pygame.draw.rect(surf, (0, 0, 0, 120), shirt_rect, 1, border_radius=8)

        # Sleeves
        pygame.draw.rect(surf, shirt1, (cx - 42, cy - 18, 16, 24), border_radius=5)
        pygame.draw.rect(surf, shirt2, (cx + 26, cy - 18, 16, 24), border_radius=5)

        # Shorts
        pygame.draw.rect(surf, shorts, (cx - 22, cy + 22, 44, 24), border_radius=6)
        # Socks dots
        for sx_off in (-14, 14):
            pygame.draw.rect(surf, sock, (cx + sx_off - 7, cy + 46, 14, 16), border_radius=4)

        # Name
        name_surf = self.fn.render(self.data['name'], True, WHITE if self._selected or self._hover else GREY)
        surf.blit(name_surf, name_surf.get_rect(centerx=cx, y=self.rect.y + 130))

        # Country tag
        ctry_surf = self.fs.render(self.data['country'], True, GOLD if self._selected else (90, 110, 150))
        surf.blit(ctry_surf, ctry_surf.get_rect(centerx=cx, y=self.rect.y + 153))

        # Selected badge
        if self._selected:
            badge = self.fs.render("✓ SELECTED", True, GOLD)
            surf.blit(badge, badge.get_rect(centerx=cx, y=self.rect.y + 8))

    def clicked(self, mx, my):
        return self.rect.collidepoint(mx, my)


# ─────────────────────────────────────────────────────────────────
class MainMenu:
    def __init__(self, screen, clock):
        self.screen = screen
        self.clock  = clock

        self.f_title = pygame.font.SysFont("Georgia", 64, bold=True)
        self.f_sub   = pygame.font.SysFont("Georgia", 22, bold=True)
        self.f_btn   = pygame.font.SysFont("Georgia", 26, bold=True)
        self.f_tiny  = pygame.font.SysFont("Arial",   13)

        bw, bh = 320, 58
        bx     = SCR_W // 2 - bw // 2

        self.buttons = [
            Button("⚡  QUICK PLAY",
                   (bx, 330, bw, bh), enabled=True,
                   col_normal=(20, 80, 36), col_hover=(30, 120, 54),
                   text_col=GOLD, border_col=(40, 160, 70),
                   font=self.f_btn),
            Button("🏆  LEAGUE  (COMING SOON)",
                   (bx, 410, bw, bh), enabled=False,
                   font=self.f_btn),
            Button("⭐  CHAMPIONS LEAGUE  (COMING SOON)",
                   (bx - 40, 490, bw + 80, bh), enabled=False,
                   font=self.f_btn),
            Button("✕  QUIT",
                   (bx, 578, bw, bh), enabled=True,
                   col_normal=(60, 14, 14), col_hover=(100, 20, 20),
                   text_col=(240, 100, 100),
                   font=self.f_btn),
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
                if ev.type == pygame.KEYDOWN:
                    if ev.key == pygame.K_ESCAPE:
                        pygame.quit(); sys.exit()
                if ev.type == pygame.MOUSEBUTTONDOWN and ev.button == 1:
                    if self.buttons[0].clicked(mx, my):  # Quick play
                        return 'quick_play'
                    if self.buttons[3].clicked(mx, my):  # Quit
                        pygame.quit(); sys.exit()

            for b in self.buttons:
                b.update(mx, my)

            self._draw()
            pygame.display.flip()

    def _draw(self):
        _gradient_bg(self.screen)
        _draw_pitch_lines(self.screen)

        # Title glow
        glow = pygame.Surface((600, 120), pygame.SRCALPHA)
        ga = int(40 + 20 * math.sin(self._t))
        pygame.draw.ellipse(glow, (255, 200, 0, ga), glow.get_rect())
        self.screen.blit(glow, (SCR_W // 2 - 300, 130))

        # Title text
        title = self.f_title.render("FOOTBALL 3D", True, GOLD)
        shadow = self.f_title.render("FOOTBALL 3D", True, (40, 30, 0))
        self.screen.blit(shadow, shadow.get_rect(centerx=SCR_W // 2 + 3, y=153))
        self.screen.blit(title,  title.get_rect(centerx=SCR_W // 2, y=150))

        sub = self.f_sub.render("THE BEAUTIFUL GAME", True, (120, 150, 200))
        self.screen.blit(sub, sub.get_rect(centerx=SCR_W // 2, y=226))

        for b in self.buttons:
            b.draw(self.screen)

        ver = self.f_tiny.render("v2.0  ·  Use arrow keys / WASD in game", True, (55, 65, 90))
        self.screen.blit(ver, ver.get_rect(centerx=SCR_W // 2, y=SCR_H - 28))


# ─────────────────────────────────────────────────────────────────
class TeamSelectScreen:
    TEAM_KEYS = ['barcelona', 'real_madrid', 'bayern', 'man_city']

    def __init__(self, screen, clock):
        self.screen = screen
        self.clock  = clock

        self.f_title = pygame.font.SysFont("Georgia", 42, bold=True)
        self.f_sub   = pygame.font.SysFont("Georgia", 18, bold=True)
        self.f_card  = pygame.font.SysFont("Arial",   15, bold=True)
        self.f_small = pygame.font.SysFont("Arial",   12)
        self.f_btn   = pygame.font.SysFont("Georgia", 24, bold=True)

        self.player_team = None  # key string
        self.bot_team    = None

        # Layout: two rows of 4 cards
        cw, ch = 170, 190
        gap_x  = 22
        start_x = SCR_W // 2 - (4 * cw + 3 * gap_x) // 2

        # Player cards (top section)
        self.player_cards = []
        for i, key in enumerate(self.TEAM_KEYS):
            x = start_x + i * (cw + gap_x)
            self.player_cards.append(TeamCard(key, (x, 200, cw, ch), self.f_card, self.f_small))

        # Bot cards (bottom section)
        self.bot_cards = []
        for i, key in enumerate(self.TEAM_KEYS):
            x = start_x + i * (cw + gap_x)
            self.bot_cards.append(TeamCard(key, (x, 440, cw, ch), self.f_card, self.f_small))

        bw, bh = 240, 52
        self.btn_play = Button(
            "▶  KICK OFF!",
            (SCR_W // 2 - bw // 2, 660, bw, bh),
            enabled=False,
            col_normal=(20, 80, 36), col_hover=(30, 120, 54),
            col_disabled=(22, 32, 22),
            text_col=GOLD, text_col_disabled=(50, 70, 50),
            border_col=(40, 160, 70),
            font=self.f_btn
        )
        self.btn_back = Button(
            "← BACK",
            (30, 660, 140, 52),
            enabled=True,
            col_normal=(30, 30, 60), col_hover=(50, 50, 100),
            text_col=WHITE,
            font=self.f_btn
        )
        self._t = 0.0

    def _refresh_play_button(self):
        self.btn_play.enabled = (
            self.player_team is not None and
            self.bot_team    is not None and
            self.player_team != self.bot_team
        )

    def run(self):
        while True:
            self.clock.tick(FPS)
            mx, my = pygame.mouse.get_pos()
            self._t += 0.03

            for ev in pygame.event.get():
                if ev.type == pygame.QUIT:
                    pygame.quit(); sys.exit()
                if ev.type == pygame.KEYDOWN:
                    if ev.key == pygame.K_ESCAPE:
                        return None   # back to main menu

                if ev.type == pygame.MOUSEBUTTONDOWN and ev.button == 1:
                    # Back
                    if self.btn_back.clicked(mx, my):
                        return None

                    # Play
                    if self.btn_play.clicked(mx, my):
                        return (self.player_team, self.bot_team)

                    # Player team cards
                    for c in self.player_cards:
                        if c.clicked(mx, my):
                            # Deselect same key from bot if clash
                            self.player_team = c.key
                            if self.bot_team == c.key:
                                self.bot_team = None
                                for bc in self.bot_cards:
                                    bc.select(False)
                            for oc in self.player_cards:
                                oc.select(oc.key == c.key)
                            self._refresh_play_button()

                    # Bot team cards
                    for c in self.bot_cards:
                        if c.clicked(mx, my):
                            self.bot_team = c.key
                            if self.player_team == c.key:
                                self.player_team = None
                                for pc in self.player_cards:
                                    pc.select(False)
                            for oc in self.bot_cards:
                                oc.select(oc.key == c.key)
                            self._refresh_play_button()

            for c in self.player_cards + self.bot_cards:
                c.update(mx, my)
            self.btn_play.update(mx, my)
            self.btn_back.update(mx, my)

            self._draw()
            pygame.display.flip()

    def _draw(self):
        _gradient_bg(self.screen)
        _draw_pitch_lines(self.screen)

        # Section labels
        title = self.f_title.render("CHOOSE YOUR TEAMS", True, GOLD)
        self.screen.blit(title, title.get_rect(centerx=SCR_W // 2, y=38))

        # Player section label
        pl_lbl = self.f_sub.render("YOUR TEAM  (You control team A)", True, (120, 200, 120))
        self.screen.blit(pl_lbl, pl_lbl.get_rect(centerx=SCR_W // 2, y=168))

        for c in self.player_cards:
            c.draw(self.screen)

        # Bot section label
        bt_lbl = self.f_sub.render("OPPONENT  (CPU controls team B)", True, (200, 130, 120))
        self.screen.blit(bt_lbl, bt_lbl.get_rect(centerx=SCR_W // 2, y=410))

        for c in self.bot_cards:
            c.draw(self.screen)

        # Clash warning
        if (self.player_team and self.bot_team and
                self.player_team == self.bot_team):
            warn = self.f_small.render("Teams must be different!", True, (255, 80, 80))
            self.screen.blit(warn, warn.get_rect(centerx=SCR_W // 2, y=638))

        self.btn_play.draw(self.screen)
        self.btn_back.draw(self.screen)
