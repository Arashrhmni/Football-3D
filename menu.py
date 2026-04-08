"""menu.py – Main menu and team selection screens."""
import pygame
import sys
import math

from constants import SCR_W, SCR_H, FPS, TEAMS

# ── Palette ──────────────────────────────────────────────────────
BG_TOP   = (6,  10,  22)
BG_BOT   = (14, 28,  52)
GOLD     = (255, 210,  40)
WHITE    = (240, 240, 240)
GREY     = (120, 120, 120)

TEAM_KEYS = list(TEAMS.keys())   # stable ordering


# ── Helpers ──────────────────────────────────────────────────────
def _gradient_bg(surf):
    for y in range(SCR_H):
        t   = y / SCR_H
        col = tuple(int(BG_TOP[i] + (BG_BOT[i] - BG_TOP[i]) * t) for i in range(3))
        pygame.draw.line(surf, col, (0, y), (SCR_W, y))


def _draw_pitch_lines(surf):
    tmp = pygame.Surface((SCR_W, SCR_H), pygame.SRCALPHA)
    lc  = (255, 255, 255, 18)
    pygame.draw.rect(tmp, lc, (120, 180, SCR_W - 240, SCR_H - 280), 2, border_radius=16)
    pygame.draw.line(tmp, lc, (SCR_W // 2, 180), (SCR_W // 2, SCR_H - 100), 2)
    pygame.draw.circle(tmp, lc, (SCR_W // 2, SCR_H // 2 + 40), 80, 2)
    pb_w, pb_h = 190, 120
    pygame.draw.rect(tmp, lc, (120, SCR_H // 2 - pb_h // 2 + 40, pb_w, pb_h), 2)
    pygame.draw.rect(tmp, lc, (SCR_W - 120 - pb_w, SCR_H // 2 - pb_h // 2 + 40, pb_w, pb_h), 2)
    surf.blit(tmp, (0, 0))


# ── Button ───────────────────────────────────────────────────────
class Button:
    def __init__(self, text, rect, enabled=True,
                 col_normal=(30, 44, 80), col_hover=(50, 74, 140),
                 col_disabled=(28, 32, 44), text_col=WHITE,
                 text_col_disabled=(55, 55, 55), font=None, border_col=None):
        self.text    = text
        self.rect    = pygame.Rect(rect)
        self.enabled = enabled
        self.cn, self.ch, self.cd = col_normal, col_hover, col_disabled
        self.tc, self.tcd         = text_col, text_col_disabled
        self.font    = font
        self.border  = border_col
        self._hover  = False
        self._pulse  = 0.0

    def update(self, mx, my):
        self._hover = self.enabled and self.rect.collidepoint(mx, my)
        self._pulse = (self._pulse + 0.08) % (math.pi * 2)

    def draw(self, surf):
        col = self.cd if not self.enabled else (self.ch if self._hover else self.cn)
        pygame.draw.rect(surf, col, self.rect, border_radius=10)
        bc = self.border if self.border else (
            GOLD if self._hover and self.enabled else (55, 68, 100))
        if not self.enabled:
            bc = (38, 42, 58)
        pygame.draw.rect(surf, bc, self.rect, 2, border_radius=10)
        tc  = self.tc if self.enabled else self.tcd
        lbl = self.font.render(self.text, True, tc)
        surf.blit(lbl, lbl.get_rect(center=self.rect.center))
        if self._hover and self.enabled:
            glow = pygame.Surface((self.rect.w + 12, self.rect.h + 12), pygame.SRCALPHA)
            alpha = int(30 + 20 * math.sin(self._pulse))
            pygame.draw.rect(glow, (*GOLD, alpha), glow.get_rect(), border_radius=12)
            surf.blit(glow, (self.rect.x - 6, self.rect.y - 6))

    def clicked(self, mx, my):
        return self.enabled and self.rect.collidepoint(mx, my)


# ── Kit mini-preview (shared by card & panel) ────────────────────
def draw_kit_preview(surf, cx, cy, kit):
    """Draw a small shirt/shorts/socks preview centred at (cx, cy)."""
    shirt1 = kit['shirt1']
    shirt2 = kit.get('shirt2', shirt1)
    shorts = kit['shorts']
    sock   = kit['socks']

    body = pygame.Rect(cx - 24, cy - 22, 48, 44)
    left_r  = pygame.Rect(cx - 24, cy - 22, 24, 44)
    right_r = pygame.Rect(cx,      cy - 22, 24, 44)

    if kit.get('stripe'):
        cols = kit.get('stripe_cols', [shirt1, shirt2, shirt1])
        sw = max(3, body.w // len(cols))
        for si, sc in enumerate(cols):
            rx = body.x + si * sw
            clip = pygame.Rect(rx, body.y, sw, body.h)
            inter = body.clip(clip)
            if inter.w > 0:
                pygame.draw.rect(surf, sc, inter, border_radius=4)
    elif kit.get('half_half'):
        pygame.draw.rect(surf, shirt1, left_r,  border_radius=4)
        pygame.draw.rect(surf, shirt2, right_r, border_radius=4)
    elif kit.get('sash'):
        pygame.draw.rect(surf, shirt1, body, border_radius=4)
        pts = [(body.x + body.w//3, body.y),
               (body.x + body.w, body.y),
               (body.x + body.w, body.y + body.h//3)]
        if len(pts) >= 3:
            pygame.draw.polygon(surf, shirt2, pts)
    else:
        pygame.draw.rect(surf, shirt1, body, border_radius=4)

    pygame.draw.rect(surf, (0, 0, 0), body, 1, border_radius=4)

    # Sleeves
    pygame.draw.rect(surf, shirt1, (cx - 36, cy - 14, 13, 20), border_radius=4)
    pygame.draw.rect(surf, shirt2, (cx + 23, cy - 14, 13, 20), border_radius=4)

    # Shorts
    pygame.draw.rect(surf, shorts, (cx - 18, cy + 20, 36, 20), border_radius=4)

    # Socks
    for sx_off in (-10, 10):
        pygame.draw.rect(surf, sock, (cx + sx_off - 5, cy + 40, 10, 12), border_radius=3)


# ── Scrollable team picker panel ─────────────────────────────────
class TeamPicker:
    """A scrollable grid of team cards for one side (player or CPU)."""

    COLS   = 6
    CW, CH = 178, 130     # card width / height
    GAP    = 8
    ROWS_VISIBLE = 3      # how many rows fit on screen

    def __init__(self, x, y, w, h, font_name, font_small, exclude_key=None):
        self.rect      = pygame.Rect(x, y, w, h)
        self.fn        = font_name
        self.fs        = font_small
        self.selected  = None        # selected team key
        self.exclude   = exclude_key
        self._scroll   = 0           # pixel scroll offset
        self._drag     = False
        self._drag_y   = 0

    def set_exclude(self, key):
        self.exclude = key
        if self.selected == key:
            self.selected = None

    @property
    def _keys(self):
        return [k for k in TEAM_KEYS if k != self.exclude]

    def _card_rect(self, idx):
        """Card rect in the scrollable surface coordinate space."""
        col = idx % self.COLS
        row = idx // self.COLS
        x   = col * (self.CW + self.GAP)
        y   = row * (self.CH + self.GAP)
        return pygame.Rect(x, y, self.CW, self.CH)

    def _total_height(self):
        keys  = self._keys
        rows  = math.ceil(len(keys) / self.COLS)
        return rows * (self.CH + self.GAP)

    def _max_scroll(self):
        return max(0, self._total_height() - self.rect.h)

    def handle_event(self, ev):
        """Returns selected key if a card was clicked, else None."""
        if ev.type == pygame.MOUSEBUTTONDOWN:
            if ev.button == 4:   # scroll up
                if self.rect.collidepoint(ev.pos):
                    self._scroll = max(0, self._scroll - 40)
            elif ev.button == 5: # scroll down
                if self.rect.collidepoint(ev.pos):
                    self._scroll = min(self._max_scroll(), self._scroll + 40)
            elif ev.button == 1:
                if self.rect.collidepoint(ev.pos):
                    lx = ev.pos[0] - self.rect.x
                    ly = ev.pos[1] - self.rect.y + self._scroll
                    for i, key in enumerate(self._keys):
                        cr = self._card_rect(i)
                        if cr.collidepoint(lx, ly):
                            self.selected = key
                            return key
        return None

    def draw(self, surf):
        keys = self._keys

        # Clip region
        clip_surf = pygame.Surface((self.rect.w, self.rect.h), pygame.SRCALPHA)

        for i, key in enumerate(keys):
            cr  = self._card_rect(i)
            cr.y -= self._scroll
            if cr.bottom < 0 or cr.top > self.rect.h:
                continue

            kit       = TEAMS[key]
            selected  = (key == self.selected)
            hover_pos = pygame.mouse.get_pos()
            lx = hover_pos[0] - self.rect.x
            ly = hover_pos[1] - self.rect.y
            hovered   = pygame.Rect(cr).collidepoint(lx, ly)

            # Card background
            bg = (35, 52, 100) if selected else (22, 30, 58) if hovered else (16, 22, 46)
            pygame.draw.rect(clip_surf, bg, cr, border_radius=10)

            bc     = GOLD if selected else ((100, 140, 220) if hovered else (40, 52, 88))
            bwidth = 2 if selected else 1
            pygame.draw.rect(clip_surf, bc, cr, bwidth, border_radius=10)

            # Kit preview
            draw_kit_preview(clip_surf, cr.centerx, cr.y + 46, kit)

            # Name (may need truncation for long names)
            name = kit['name']
            ns   = self.fn.render(name, True, WHITE if (selected or hovered) else GREY)
            if ns.get_width() > cr.w - 8:
                # Truncate with ellipsis
                while ns.get_width() > cr.w - 8 and len(name) > 4:
                    name = name[:-1]
                ns = self.fn.render(name + '…', True, WHITE if (selected or hovered) else GREY)
            clip_surf.blit(ns, ns.get_rect(centerx=cr.centerx, y=cr.y + 90))

            # Country
            cs = self.fs.render(kit['country'], True, GOLD if selected else (70, 90, 130))
            clip_surf.blit(cs, cs.get_rect(centerx=cr.centerx, y=cr.y + 108))

            # Checkmark
            if selected:
                chk = self.fs.render('✓', True, GOLD)
                clip_surf.blit(chk, chk.get_rect(right=cr.right - 6, y=cr.y + 4))

        surf.blit(clip_surf, self.rect.topleft)

        # Scroll indicator
        total = self._total_height()
        if total > self.rect.h:
            bar_h   = max(30, int(self.rect.h * self.rect.h / total))
            bar_y   = self.rect.y + int(self._scroll / total * self.rect.h)
            pygame.draw.rect(surf, (60, 80, 130),
                             (self.rect.right + 4, self.rect.y, 5, self.rect.h), border_radius=3)
            pygame.draw.rect(surf, GOLD,
                             (self.rect.right + 4, bar_y, 5, bar_h), border_radius=3)


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
        bx     = SCR_W // 2 - bw // 2
        self.buttons = [
            Button("⚡  QUICK PLAY",
                   (bx, 330, bw, bh), enabled=True,
                   col_normal=(20, 80, 36), col_hover=(30, 120, 54),
                   text_col=GOLD, border_col=(40, 160, 70), font=self.f_btn),
            Button("🏆  LEAGUE  (COMING SOON)",
                   (bx, 410, bw, bh), enabled=False, font=self.f_btn),
            Button("⭐  CHAMPIONS LEAGUE  (COMING SOON)",
                   (bx - 40, 490, bw + 80, bh), enabled=False, font=self.f_btn),
            Button("✕  QUIT",
                   (bx, 578, bw, bh), enabled=True,
                   col_normal=(60, 14, 14), col_hover=(100, 20, 20),
                   text_col=(240, 100, 100), font=self.f_btn),
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
                    if self.buttons[0].clicked(mx, my):
                        return 'quick_play'
                    if self.buttons[3].clicked(mx, my):
                        pygame.quit(); sys.exit()
            for b in self.buttons:
                b.update(mx, my)
            self._draw()
            pygame.display.flip()

    def _draw(self):
        _gradient_bg(self.screen)
        _draw_pitch_lines(self.screen)
        glow = pygame.Surface((600, 120), pygame.SRCALPHA)
        ga   = int(40 + 20 * math.sin(self._t))
        pygame.draw.ellipse(glow, (255, 200, 0, ga), glow.get_rect())
        self.screen.blit(glow, (SCR_W // 2 - 300, 130))
        title  = self.f_title.render("FOOTBALL 3D", True, GOLD)
        shadow = self.f_title.render("FOOTBALL 3D", True, (40, 30, 0))
        self.screen.blit(shadow, shadow.get_rect(centerx=SCR_W // 2 + 3, y=153))
        self.screen.blit(title,  title.get_rect(centerx=SCR_W // 2, y=150))
        sub = self.f_sub.render("THE BEAUTIFUL GAME", True, (120, 150, 200))
        self.screen.blit(sub, sub.get_rect(centerx=SCR_W // 2, y=226))
        for b in self.buttons:
            b.draw(self.screen)
        ver = self.f_tiny.render("v2.0  ·  WASD / arrows in game  ·  22 clubs", True, (55, 65, 90))
        self.screen.blit(ver, ver.get_rect(centerx=SCR_W // 2, y=SCR_H - 28))


# ── Team Selection ────────────────────────────────────────────────
class TeamSelectScreen:
    # Layout constants
    PANEL_TOP  = 130
    PANEL_H    = 270
    PANEL_GAP  = 50       # vertical gap between the two pickers
    PICKER_W   = 1150
    PICKER_X   = (SCR_W - 1150) // 2

    def __init__(self, screen, clock):
        self.screen = screen
        self.clock  = clock

        self.f_title  = pygame.font.SysFont("Georgia", 38, bold=True)
        self.f_label  = pygame.font.SysFont("Georgia", 16, bold=True)
        self.f_card   = pygame.font.SysFont("Arial",   12, bold=True)
        self.f_small  = pygame.font.SysFont("Arial",   11)
        self.f_btn    = pygame.font.SysFont("Georgia", 24, bold=True)

        py1 = self.PANEL_TOP + 28
        py2 = py1 + self.PANEL_H + self.PANEL_GAP + 28

        self.picker_a = TeamPicker(
            self.PICKER_X, py1, self.PICKER_W, self.PANEL_H,
            self.f_card, self.f_small)
        self.picker_b = TeamPicker(
            self.PICKER_X, py2, self.PICKER_W, self.PANEL_H,
            self.f_card, self.f_small)

        bw, bh = 220, 50
        self.btn_play = Button("▶  KICK OFF!",
            (SCR_W // 2 - bw // 2, SCR_H - 68, bw, bh), enabled=False,
            col_normal=(20, 80, 36), col_hover=(30, 120, 54),
            col_disabled=(22, 32, 22), text_col=GOLD,
            text_col_disabled=(45, 65, 45),
            border_col=(40, 160, 70), font=self.f_btn)
        self.btn_back = Button("← BACK",
            (28, SCR_H - 68, 130, 50), enabled=True,
            col_normal=(28, 28, 58), col_hover=(48, 48, 100),
            text_col=WHITE, font=self.f_btn)

    def _refresh(self):
        ka = self.picker_a.selected
        kb = self.picker_b.selected
        self.picker_a.set_exclude(kb)
        self.picker_b.set_exclude(ka)
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

                # Pickers handle their own scroll/click
                r = self.picker_a.handle_event(ev)
                if r:
                    self._refresh()
                r = self.picker_b.handle_event(ev)
                if r:
                    self._refresh()

                if ev.type == pygame.MOUSEBUTTONDOWN and ev.button == 1:
                    if self.btn_back.clicked(mx, my):
                        return None
                    if self.btn_play.clicked(mx, my):
                        return (self.picker_a.selected, self.picker_b.selected)

            self.btn_play.update(mx, my)
            self.btn_back.update(mx, my)
            self._draw()
            pygame.display.flip()

    def _draw(self):
        _gradient_bg(self.screen)
        _draw_pitch_lines(self.screen)

        title = self.f_title.render("CHOOSE YOUR TEAMS", True, GOLD)
        self.screen.blit(title, title.get_rect(centerx=SCR_W // 2, y=14))

        py1 = self.PANEL_TOP
        py2 = py1 + self.PANEL_H + self.PANEL_GAP + 28

        # Section headers
        lbl_a = self.f_label.render("YOUR TEAM  (you control)  —  scroll to browse all 22 clubs", True, (100, 200, 110))
        self.screen.blit(lbl_a, lbl_a.get_rect(x=self.PICKER_X, y=py1 + 4))

        lbl_b = self.f_label.render("OPPONENT  (CPU)  —  scroll to browse", True, (200, 110, 100))
        self.screen.blit(lbl_b, lbl_b.get_rect(x=self.PICKER_X, y=py2 + 4))

        self.picker_a.draw(self.screen)
        self.picker_b.draw(self.screen)

        # Selected summary bar
        ka = self.picker_a.selected
        kb = self.picker_b.selected
        if ka or kb:
            a_name = TEAMS[ka]['name'] if ka else '—'
            b_name = TEAMS[kb]['name'] if kb else '—'
            summary = self.f_label.render(
                f"You:  {a_name}    vs    CPU:  {b_name}", True, (180, 180, 200))
            self.screen.blit(summary, summary.get_rect(centerx=SCR_W // 2, y=SCR_H - 82))

        self.btn_play.draw(self.screen)
        self.btn_back.draw(self.screen)

        hint = self.f_small.render("Scroll inside each panel to see all clubs", True, (55, 65, 90))
        self.screen.blit(hint, hint.get_rect(right=SCR_W - 20, y=SCR_H - 22))
