"""
shared_ui.py – Shared visual primitives used by menu.py and league.py.
All drawing helpers, the animated background, football icon, etc.
"""
import pygame
import math
import random as _random

# ── Palette ──────────────────────────────────────────────────────
GOLD      = (255, 210,  40)
GOLD_DIM  = (160, 130,  20)
WHITE     = (240, 240, 240)
GREY      = (110, 110, 130)
DARK_NAVY = (  6,  10,  22)
MID_NAVY  = ( 12,  20,  48)
PANEL_BG  = ( 10,  16,  38)

# ── Stadium background ────────────────────────────────────────────
def draw_stadium_bg(surf, t, W, H, grass_frac=0.76):
    """Night stadium with stars, sweeping spotlights, grass strip."""
    # Sky gradient
    for y in range(H):
        f = y / H
        r = int(4  + 10*f)
        g = int(6  + 16*f)
        b = int(18 + 28*f)
        pygame.draw.line(surf, (r, g, b), (0, y), (W, y))

    # Stars
    rng = _random.Random(42)
    for _ in range(100):
        sx = rng.randint(0, W)
        sy = rng.randint(0, int(H * 0.5))
        bright = int(70 + 55 * math.sin(t * 0.7 + sx * 0.04))
        r2 = rng.randint(1, 2)
        s2 = pygame.Surface((r2*2+2, r2*2+2), pygame.SRCALPHA)
        pygame.draw.circle(s2, (bright, bright, min(255,bright+50), bright),
                           (r2+1, r2+1), r2)
        surf.blit(s2, (sx-r2, sy-r2))

    # Spotlights
    for ox, phase in [(int(W*0.12), 0.0), (int(W*0.88), math.pi)]:
        oy  = -30
        ang = math.radians(72) + math.sin(t*0.38 + phase) * math.radians(16)
        lx  = ox + math.cos(ang) * 900
        ly  = oy + math.sin(ang) * 900
        sp  = pygame.Surface((W, H), pygame.SRCALPHA)
        for w, a in [(110, 7), (65, 11), (28, 17)]:
            px = -math.sin(ang)*w; py = math.cos(ang)*w
            pts = [(ox, oy),
                   (int(lx+px), int(ly+py)),
                   (int(lx-px), int(ly-py))]
            pygame.draw.polygon(sp, (255, 248, 200, a), pts)
        surf.blit(sp, (0, 0))

    # Grass
    gy = int(H * grass_frac)
    for y in range(gy, H):
        f = (y - gy) / max(1, H - gy)
        pygame.draw.line(surf, (int(8+24*f), int(52+48*f), int(12+20*f)), (0, y), (W, y))
    sw = 70
    tmp = pygame.Surface((W, H - gy), pygame.SRCALPHA)
    for sx in range(0, W, sw*2):
        pygame.draw.rect(tmp, (255,255,255, 7), (sx, 0, sw, H-gy))
    surf.blit(tmp, (0, gy))
    pygame.draw.line(surf, (180, 210, 180), (0, gy), (W, gy), 2)
    # Centre circle ghost
    cc = pygame.Surface((280, 140), pygame.SRCALPHA)
    pygame.draw.ellipse(cc, (255,255,255,14), (0,0,280,140), 2)
    surf.blit(cc, (W//2-140, gy+8))


# ── Floating gold sparks ──────────────────────────────────────────
def make_particles(n=40, W=1280, H=800, seed=7):
    rng = _random.Random(seed)
    return [{'x': rng.uniform(0,W), 'y': rng.uniform(0,H*0.72),
             'vx': rng.uniform(-0.18,0.18), 'vy': rng.uniform(-0.38,-0.08),
             'r': rng.uniform(1,2.4), 'a': rng.uniform(0,math.pi*2)}
            for _ in range(n)]


def update_particles(parts, W=1280, H=800):
    for p in parts:
        p['x'] += p['vx']; p['y'] += p['vy']; p['a'] += 0.022
        if p['y'] < -10:
            p['y'] = H * 0.73
            p['x'] = _random.uniform(0, W)


def draw_particles(surf, parts):
    for p in parts:
        a = int(35 + 28*math.sin(p['a']))
        s = pygame.Surface((8,8), pygame.SRCALPHA)
        pygame.draw.circle(s, (255,210,60, a), (4,4), int(p['r']))
        surf.blit(s, (int(p['x'])-4, int(p['y'])-4))


# ── Football icon ─────────────────────────────────────────────────
def draw_football(surf, cx, cy, r, t):
    # Shadow
    shd = pygame.Surface((r*4, r*2), pygame.SRCALPHA)
    pygame.draw.ellipse(shd, (0,0,0,55), shd.get_rect())
    surf.blit(shd, (cx-r*2, cy+r-3))
    # Body layers
    for dr, dc in [(r,(255,255,255)),(r-2,(242,244,248)),(r-6,(228,232,238))]:
        pygame.draw.circle(surf, dc, (cx,cy), dr)
    # Sheen
    hl = pygame.Surface((r*2,r*2), pygame.SRCALPHA)
    pygame.draw.circle(hl, (255,255,255,65), (int(r*0.54),int(r*0.36)), int(r*0.30))
    surf.blit(hl, (cx-r, cy-r))
    # Patches
    _hex(surf, cx, cy, int(r*0.29), (22,22,30))
    for i in range(5):
        ang = math.radians(i*72-90) + math.sin(t*0.5)*0.07
        _hex(surf, cx+int(math.cos(ang)*r*0.57), cy+int(math.sin(ang)*r*0.57),
             int(r*0.21), (36,38,50))
    pygame.draw.circle(surf, (75,75,88), (cx,cy), r, 2)
    # Pulse ring
    ra = int(28+18*math.sin(t*1.7))
    rr = r + 7 + int(4*math.sin(t*1.7))
    rs = pygame.Surface((r*4,r*4), pygame.SRCALPHA)
    pygame.draw.circle(rs, (255,210,0,ra), (r*2,r*2), rr, 3)
    surf.blit(rs, (cx-r*2, cy-r*2))


def _hex(surf, cx, cy, r, col):
    pts = [(int(cx+r*math.cos(math.radians(60*i-30))),
            int(cy+r*math.sin(math.radians(60*i-30)))) for i in range(6)]
    pygame.draw.polygon(surf, col, pts)
    pygame.draw.polygon(surf, tuple(max(0,c-20) for c in col), pts, 1)


# ── Kit mini-preview ──────────────────────────────────────────────
def draw_kit(surf, cx, cy, kit):
    s1 = kit['shirt1']; s2 = kit.get('shirt2', s1)
    sh = kit['shorts'];  sk = kit['socks']
    body = pygame.Rect(cx-16, cy-13, 32, 26)
    if kit.get('stripe'):
        cols = kit.get('stripe_cols', [s1,s2,s1])
        sw   = max(2, body.w//len(cols))
        for si, sc in enumerate(cols):
            inter = body.clip(pygame.Rect(body.x+si*sw, body.y, sw, body.h))
            if inter.w > 0: pygame.draw.rect(surf, sc, inter, border_radius=3)
    elif kit.get('half_half'):
        pygame.draw.rect(surf, s1, (body.x, body.y, body.w//2, body.h), border_radius=3)
        pygame.draw.rect(surf, s2, (body.x+body.w//2, body.y, body.w//2, body.h), border_radius=3)
    elif kit.get('sash'):
        pygame.draw.rect(surf, s1, body, border_radius=3)
        pts = [(body.x+body.w//3,body.y),(body.x+body.w,body.y),(body.x+body.w,body.y+body.h//3)]
        pygame.draw.polygon(surf, s2, pts)
    else:
        pygame.draw.rect(surf, s1, body, border_radius=3)
    pygame.draw.rect(surf, (0,0,0), body, 1, border_radius=3)
    pygame.draw.rect(surf, s1, (cx-24, cy-7, 9, 13), border_radius=2)
    pygame.draw.rect(surf, s2, (cx+15, cy-7, 9, 13), border_radius=2)
    pygame.draw.rect(surf, sh, (cx-12, cy+12, 24, 10), border_radius=2)
    for so in (-6,6):
        pygame.draw.rect(surf, sk, (cx+so-3, cy+22, 6, 7), border_radius=1)


# ── Flag ─────────────────────────────────────────────────────────
FLAG_DATA = {
    'Spain':    {'cols': [((198,11,30),.25),((255,196,0),.5),((198,11,30),.25)]},
    'England':  {'cols': [((255,255,255),1.0)], 'cross': (198,11,30)},
    'Germany':  {'cols': [((0,0,0),.333),((221,0,0),.333),((255,206,0),.334)]},
    'Italy':    {'cols': [((0,140,69),.333),((255,255,255),.333),((206,43,55),.334)]},
    'Portugal': {'cols': [((0,102,0),.4),((220,20,60),.6)]},
}

def draw_flag(surf, rect, country):
    x,y,w,h = rect
    info = FLAG_DATA.get(country, {'cols': [((80,80,80),1.0)]})
    dx = x
    for col, frac in info['cols']:
        fw = int(w*frac)
        pygame.draw.rect(surf, col, (dx,y,fw,h))
        dx += fw
    if 'cross' in info:
        cc = info['cross']; cx2,cy2 = x+w//2, y+h//2
        pygame.draw.rect(surf, cc, (x, cy2-2, w, 5))
        pygame.draw.rect(surf, cc, (cx2-2, y, 5, h))
    pygame.draw.rect(surf, (60,60,70), rect, 1)


# ── Glassmorphism panel ───────────────────────────────────────────
def glass_panel(surf, rect, tint=(10,18,48), alpha=210, border=(50,70,120), radius=14):
    r = pygame.Rect(rect)
    s = pygame.Surface((r.w, r.h), pygame.SRCALPHA)
    pygame.draw.rect(s, (*tint, alpha), s.get_rect(), border_radius=radius)
    surf.blit(s, r.topleft)
    pygame.draw.rect(surf, border, r, 1, border_radius=radius)


# ── Divider line with gold centre ────────────────────────────────
def gold_divider(surf, y, W, margin=60):
    mx = W//2
    pygame.draw.line(surf, (40,55,100), (margin, y), (mx-30, y), 1)
    pygame.draw.line(surf, GOLD,        (mx-6,  y), (mx+6,  y), 2)
    pygame.draw.line(surf, (40,55,100), (mx+30, y), (W-margin, y), 1)


# ── Page title with decorative underline ─────────────────────────
def draw_page_title(surf, text, font, cx, y, col=GOLD, sub=None, sub_font=None):
    # Outer glow
    for r2, a in [(180, 12), (120, 20), (70, 32)]:
        g = pygame.Surface((r2*2, 60), pygame.SRCALPHA)
        pygame.draw.ellipse(g, (*col, a), g.get_rect())
        surf.blit(g, (cx-r2, y-6))
    # Shadow + title
    sh = font.render(text, True, (0,0,0))
    ti = font.render(text, True, col)
    surf.blit(sh, sh.get_rect(centerx=cx+2, y=y+2))
    surf.blit(ti, ti.get_rect(centerx=cx, y=y))
    tw = ti.get_width()
    # Triple underline
    uy = y + ti.get_height() + 4
    pygame.draw.line(surf, (40,55,100), (cx-tw//2-20, uy),   (cx+tw//2+20, uy),   1)
    pygame.draw.line(surf, col,         (cx-tw//2+10, uy+4),  (cx+tw//2-10, uy+4), 2)
    pygame.draw.line(surf, (40,55,100), (cx-tw//2-20, uy+8),  (cx+tw//2+20, uy+8), 1)
    if sub and sub_font:
        s = sub_font.render(sub, True, (130,155,200))
        surf.blit(s, s.get_rect(centerx=cx, y=uy+14))


# ── Fancy button ──────────────────────────────────────────────────
class FancyBtn:
    def __init__(self, label, rect, font, icon='',
                 bg=(22,40,90), bg_h=(36,66,155), bg_d=(16,22,40),
                 tc=WHITE, tc_d=(45,50,65), bc=(55,80,150), bc_h=None,
                 enabled=True, badge=None, badge_col=(255,160,0)):
        self.label, self.rect = label, pygame.Rect(rect)
        self.font = font; self.icon = icon
        self.bg,self.bg_h,self.bg_d = bg,bg_h,bg_d
        self.tc,self.tc_d = tc,tc_d
        self.bc = bc; self.bc_h = bc_h or GOLD
        self.enabled = enabled
        self.badge = badge; self.badge_col = badge_col
        self._hov = False; self._t = 0.0
        self._f_badge = None  # set on first draw

    def update(self, mx, my):
        self._hov = self.enabled and self.rect.collidepoint(mx, my)
        self._t   = (self._t + 0.06) % (math.pi*2)

    def draw(self, surf):
        if self._f_badge is None:
            self._f_badge = pygame.font.SysFont("Arial", 10, bold=True)
        col = self.bg_d if not self.enabled else (self.bg_h if self._hov else self.bg)
        pygame.draw.rect(surf, col, self.rect, border_radius=12)

        if self._hov and self.enabled:
            gs = pygame.Surface((self.rect.w+14, self.rect.h+14), pygame.SRCALPHA)
            pygame.draw.rect(gs, (*self.bc_h, int(24+16*math.sin(self._t))),
                             gs.get_rect(), border_radius=14)
            surf.blit(gs, (self.rect.x-7, self.rect.y-7))
            pygame.draw.rect(surf, self.bc_h, self.rect, 2, border_radius=12)
            # shimmer
            shim = pygame.Surface((self.rect.w, self.rect.h), pygame.SRCALPHA)
            sx = int((self._t/(math.pi*2)) * (self.rect.w+80)) - 40
            for sw2, sa in [(55,10),(28,18)]:
                pygame.draw.rect(shim, (255,255,255,sa), (sx,0,sw2,self.rect.h))
            surf.blit(shim, self.rect.topleft)
        else:
            bc = (32,38,58) if not self.enabled else self.bc
            pygame.draw.rect(surf, bc, self.rect, 2, border_radius=12)

        tc = self.tc if self.enabled else self.tc_d
        # Icon circle
        if self.icon:
            icx = self.rect.x + 32; icy = self.rect.centery
            if self.enabled:
                pygame.draw.circle(surf, tuple(min(255,c+28) for c in col), (icx,icy), 18)
                pygame.draw.circle(surf, self.bc_h if self._hov else self.bc, (icx,icy), 18, 2)
            ic = self.font.render(self.icon, True, tc)
            surf.blit(ic, ic.get_rect(center=(icx,icy)))
            lbl = self.font.render(self.label, True, tc)
            surf.blit(lbl, lbl.get_rect(x=self.rect.x+58, centery=self.rect.centery))
        else:
            lbl = self.font.render(self.label, True, tc)
            surf.blit(lbl, lbl.get_rect(center=self.rect.center))

        if self.badge:
            bw = self._f_badge.render(self.badge, True,(0,0,0)).get_width()+10
            bx = self.rect.right - bw - 8; by = self.rect.y + 7
            pygame.draw.rect(surf, self.badge_col, (bx,by,bw,16), border_radius=8)
            bs = self._f_badge.render(self.badge, True,(10,10,10))
            surf.blit(bs, bs.get_rect(centerx=bx+bw//2, centery=by+8))

    def clicked(self, mx, my):
        return self.enabled and self.rect.collidepoint(mx, my)


# ── Country tab button ────────────────────────────────────────────
class CountryTab:
    W, H = 188, 62

    def __init__(self, country, rect, font):
        self.country = country
        self.rect    = pygame.Rect(rect)
        self.font    = font
        self.selected = False
        self._hov     = False
        self._t       = 0.0

    def update(self, mx, my):
        self._hov = self.rect.collidepoint(mx, my)
        self._t   = (self._t + 0.05) % (math.pi*2)

    def draw(self, surf):
        if self.selected:
            bg = (26, 50, 108); bc = GOLD; bw = 3
        elif self._hov:
            bg = (18, 34, 80); bc = (100,140,220); bw = 2
        else:
            bg = (11, 20, 50); bc = (36,50,88); bw = 1
        pygame.draw.rect(surf, bg, self.rect, border_radius=12)
        pygame.draw.rect(surf, bc, self.rect, bw, border_radius=12)
        if self.selected:
            gs = pygame.Surface((self.rect.w+10, self.rect.h+10), pygame.SRCALPHA)
            pygame.draw.rect(gs, (*GOLD, int(18+12*math.sin(self._t))),
                             gs.get_rect(), border_radius=13)
            surf.blit(gs, (self.rect.x-5, self.rect.y-5))

        draw_flag(surf, (self.rect.x+10, self.rect.y+16, 40, 26), self.country)
        info = FLAG_DATA.get(self.country,{})
        lc   = {'Spain':(255,196,0),'England':(220,80,80),'Germany':(255,206,0)}.get(self.country, WHITE)
        lbl  = self.font.render(self.country, True, lc if self.selected else WHITE)
        surf.blit(lbl, lbl.get_rect(x=self.rect.x+60, centery=self.rect.centery))
        if self.selected:
            arr = self.font.render('▶', True, GOLD)
            surf.blit(arr, arr.get_rect(right=self.rect.right-8, centery=self.rect.centery))

    def clicked(self, mx, my):
        return self.rect.collidepoint(mx, my)


# ── Team card ─────────────────────────────────────────────────────
class TeamCard:
    W, H = 148, 118

    def __init__(self, key, rect, fn, fs):
        self.key = key; self.rect = pygame.Rect(rect)
        self.fn = fn; self.fs = fs
        self.selected = False; self._hov = False; self._t = 0.0

    def update(self, mx, my):
        self._hov = self.rect.collidepoint(mx, my)
        self._t   = (self._t + 0.05) % (math.pi*2)

    def draw(self, surf):
        from constants import TEAMS, get_stars
        kit = TEAMS[self.key]
        stars = get_stars(self.key)
        if self.selected:
            bg=(32,55,110); bc=GOLD; bw=3
        elif self._hov:
            bg=(20,35,78); bc=(90,130,210); bw=2
        else:
            bg=(12,20,50); bc=(35,48,85); bw=1
        pygame.draw.rect(surf, bg, self.rect, border_radius=12)
        if self.selected:
            gs = pygame.Surface((self.rect.w+8,self.rect.h+8), pygame.SRCALPHA)
            pygame.draw.rect(gs, (*GOLD, int(16+10*math.sin(self._t))), gs.get_rect(), border_radius=13)
            surf.blit(gs, (self.rect.x-4, self.rect.y-4))
        pygame.draw.rect(surf, bc, self.rect, bw, border_radius=12)

        draw_kit(surf, self.rect.centerx, self.rect.y+42, kit)

        name = kit['name']
        ns   = self.fn.render(name, True, WHITE if (self.selected or self._hov) else GREY)
        if ns.get_width() > self.rect.w-8:
            while ns.get_width() > self.rect.w-8 and len(name)>3:
                name = name[:-1]
            ns = self.fn.render(name+'…', True, WHITE if (self.selected or self._hov) else GREY)
        surf.blit(ns, ns.get_rect(centerx=self.rect.centerx, y=self.rect.bottom-30))

        # Star rating
        star_on  = (255, 210, 0)
        star_off = (40, 45, 65)
        sz = 8; gap = 2
        total_w = 5*(sz+gap)-gap
        sx = self.rect.centerx - total_w//2
        sy = self.rect.bottom - 16
        for i in range(5):
            c = star_on if i < stars else star_off
            pygame.draw.circle(surf, c, (sx + i*(sz+gap) + sz//2, sy + sz//2), sz//2)

        if self.selected:
            chk = self.fs.render('✓ SELECTED', True, GOLD)
            surf.blit(chk, chk.get_rect(centerx=self.rect.centerx, y=self.rect.y+5))

    def clicked(self, mx, my):
        return self.rect.collidepoint(mx, my)
