"""player.py – Player entity: top-down drawing, movement, animation.

Top-down design philosophy
───────────────────────────
Viewed directly from above, a footballer mostly reads as:
  - a coloured disc (shirt + shoulders)
  - a jersey number on the chest
  - two small "feet" dots that animate when running
  - a tiny head/hair circle peeking out the top of the shirt
  - a soft drop-shadow offset toward a fixed "sun" direction,
    giving subtle depth without breaking the flat look

Kits are still fully supported (solid, stripes, half-half, gold trim).
"""
import pygame
import math
import random
from constants import (
    PLAYER_R, AI_REACT, OUT_L, OUT_R, OUT_T, OUT_B,
    W_W, W_H, d2, n2, clamp, w2s
)

# Module-level kit config – set by Game before building teams
_KIT_A = None   # TEAMS dict entry for team A
_KIT_B = None   # TEAMS dict entry for team B

def set_kits(kit_a, kit_b):
    global _KIT_A, _KIT_B
    _KIT_A = kit_a
    _KIT_B = kit_b


# ── Shared "sun" direction for all drop-shadows ────────────────────
# Light comes from the upper-left, so shadows fall toward lower-right.
SUN_DX, SUN_DY = 0.55, 0.75     # offset direction (screen-space)
SHADOW_DIST    = 4               # px the shadow is offset from the body
SHADOW_ALPHA   = 70


class Player:
    def __init__(self, team, num, hx, hy, is_keeper=False):
        self.team      = team
        self.num       = num
        self.wx        = float(hx)
        self.wy        = float(hy)
        self.home_x    = float(hx)
        self.home_y    = float(hy)
        self.vx        = 0.0
        self.vy        = 0.0
        self.fdx       = 1.0 if team == 'A' else -1.0
        self.fdy       = 0.0
        self.is_keeper = is_keeper
        self.selected  = False
        self.react     = random.randint(0, AI_REACT)
        self.tackle_cd = 0
        self.anim_t    = random.uniform(0, math.pi * 2)
        self.throw_anim = 0   # >0 while raising arms for throw-in
        self.hold_timer = 0   # CPU dribble hold counter
        self.stamina = 1.0

    # ── Kit ──────────────────────────────────────────────────────
    def _kit(self):
        cfg = _KIT_A if self.team == 'A' else _KIT_B
        if cfg is None:
            return (0, 82, 170), (0, 82, 170), (0, 82, 170), (222, 182, 142), (38, 28, 18)
        if self.is_keeper:
            gk = cfg['gk']
            dark = tuple(max(0, c - 40) for c in gk)
            return gk, dark, dark, cfg['skin'], cfg['hair']
        return cfg['shirt1'], cfg['shorts'], cfg['socks'], cfg['skin'], cfg['hair']

    # ── Movement ─────────────────────────────────────────────────
    def move_toward(self, tx, ty, spd):
        dd = d2((self.wx, self.wy), (tx, ty))
        if dd < 0.5:
            self.vx = self.vy = 0.0
            return
        r = min(spd / dd, 1.0)
        self.vx = (tx - self.wx) * r
        self.vy = (ty - self.wy) * r
        ln = math.hypot(self.vx, self.vy)
        if ln > 0:
            self.fdx = self.vx / ln
            self.fdy = self.vy / ln
        self.wx += self.vx
        self.wy += self.vy
        self.wx = clamp(self.wx, -OUT_L, W_W + OUT_R)
        self.wy = clamp(self.wy, -OUT_T, W_H + OUT_B)

    # ── Helpers for kit fills on a circular body ──────────────────
    def _draw_striped_body(self, surf, cx, cy, r, cfg, shirt):
        """Vertical stripes clipped to the body circle via alpha mask."""
        cols = cfg.get('stripe_cols', [shirt, cfg.get('shirt2', shirt), shirt])
        n = max(1, len(cols))
        size = r * 2 + 2
        stripe_w = max(2, size // n)
        body = pygame.Surface((size, size), pygame.SRCALPHA)
        body.fill((0, 0, 0, 0))
        for i, col in enumerate(cols):
            sx = i * stripe_w
            w = stripe_w if i < n - 1 else size - sx
            pygame.draw.rect(body, (col[0], col[1], col[2], 255), (sx, 0, w, size))
        # Circular alpha mask
        mask = pygame.Surface((size, size), pygame.SRCALPHA)
        mask.fill((0, 0, 0, 0))
        pygame.draw.circle(mask, (255, 255, 255, 255), (r + 1, r + 1), r)
        body.blit(mask, (0, 0), special_flags=pygame.BLEND_RGBA_MIN)
        surf.blit(body, (cx - r - 1, cy - r - 1))

    def _draw_half_half_body(self, surf, cx, cy, r, cfg, shirt):
        """Left/right two-tone split, clipped to the body circle."""
        s1 = cfg['shirt1']
        s2 = cfg.get('shirt2', shirt)
        size = r * 2 + 2
        body = pygame.Surface((size, size), pygame.SRCALPHA)
        body.fill((0, 0, 0, 0))
        pygame.draw.rect(body, (s1[0], s1[1], s1[2], 255), (0, 0, size // 2, size))
        pygame.draw.rect(body, (s2[0], s2[1], s2[2], 255), (size // 2, 0, size - size // 2, size))
        mask = pygame.Surface((size, size), pygame.SRCALPHA)
        mask.fill((0, 0, 0, 0))
        pygame.draw.circle(mask, (255, 255, 255, 255), (r + 1, r + 1), r)
        body.blit(mask, (0, 0), special_flags=pygame.BLEND_RGBA_MIN)
        surf.blit(body, (cx - r - 1, cy - r - 1))

    # ── Draw ─────────────────────────────────────────────────────
    def draw(self, surf, ball, fnt):
        shirt, shorts, socks, skin, hair = self._kit()
        cfg = (_KIT_A if self.team == 'A' else _KIT_B) or {}
        has_ball = (ball.owner is self)
        moving   = math.hypot(self.vx, self.vy) > 0.2
        if moving:
            self.anim_t += 0.28

        gx, gy = w2s(self.wx, self.wy, 0)

        R = int(PLAYER_R * 1.35)     # body radius (shirt/shoulders disc) — slightly larger for readability
        FOOT_R = max(2, int(R * 0.20))
        HEAD_R = max(3, int(R * 0.30))

        # ── Drop shadow (offset toward fixed "sun" direction) ──────
        shadow_r = int(R * 1.05)
        shw = pygame.Surface((shadow_r * 2 + 6, shadow_r * 2 + 6), pygame.SRCALPHA)
        shw.fill((0, 0, 0, 0))
        pygame.draw.ellipse(
            shw, (0, 0, 0, SHADOW_ALPHA),
            (3, 3, shadow_r * 2, int(shadow_r * 1.7))
        )
        surf.blit(
            shw,
            (gx - shadow_r - 3 + int(SUN_DX * SHADOW_DIST),
             gy - shadow_r - 3 + int(SUN_DY * SHADOW_DIST) + int(R * 0.25))
        )

        # ── Feet (two small dots, animate fore/aft when moving) ────
        foot_spread = R * 0.55
        for sign in (-1, 1):
            ph = self.anim_t + (0 if sign == -1 else math.pi)
            stride = math.sin(ph) * (R * 0.35) if moving else 0.0
            fx = gx + self.fdx * stride - self.fdy * sign * foot_spread
            fy = gy + self.fdy * stride + self.fdx * sign * foot_spread
            bcol = tuple(max(0, c - 60) for c in
                          (shorts if not self.is_keeper else (30, 30, 30)))
            pygame.draw.circle(surf, bcol, (int(fx), int(fy)), FOOT_R)
            pygame.draw.circle(surf, (0, 0, 0), (int(fx), int(fy)), FOOT_R, 1)

        # ── Main body disc (shirt) ──────────────────────────────────
        if not self.is_keeper and cfg.get('stripe'):
            self._draw_striped_body(surf, gx, gy, R, cfg, shirt)
            pygame.draw.circle(surf, tuple(max(0, c - 35) for c in shirt), (gx, gy), R, 2)
        elif not self.is_keeper and cfg.get('half_half'):
            self._draw_half_half_body(surf, gx, gy, R, cfg, shirt)
            pygame.draw.circle(surf, tuple(max(0, c - 30) for c in cfg['shirt1']), (gx, gy), R, 2)
        elif not self.is_keeper and cfg.get('gold_border'):
            pygame.draw.circle(surf, shirt, (gx, gy), R)
            from constants import RMA_GOLD
            pygame.draw.circle(surf, RMA_GOLD, (gx, gy), R, 2)
        else:
            pygame.draw.circle(surf, shirt, (gx, gy), R)
            pygame.draw.circle(surf, tuple(max(0, c - 35) for c in shirt), (gx, gy), R, 2)

        # ── Shorts hem (thin arc at the bottom edge of the disc) ────
        hem_rect = pygame.Rect(gx - R, gy - R, R * 2, R * 2)
        pygame.draw.arc(surf, shorts, hem_rect, math.radians(200), math.radians(340), 4)

        # ── Head (small circle at the edge, toward facing direction) ─
        head_off = R * 0.78
        hx_ = gx + self.fdx * head_off
        hy_ = gy + self.fdy * head_off
        pygame.draw.circle(surf, skin, (int(hx_), int(hy_)), HEAD_R)
        pygame.draw.circle(surf, tuple(max(0, c - 18) for c in skin), (int(hx_), int(hy_)), HEAD_R, 1)
        # Hair: small crescent on the back of the head (opposite facing dir)
        hair_off = HEAD_R * 0.55
        hxh = hx_ - self.fdx * hair_off
        hyh = hy_ - self.fdy * hair_off
        pygame.draw.circle(surf, hair, (int(hxh), int(hyh)), max(2, int(HEAD_R * 0.70)))

        # ── Jersey number on the chest ──────────────────────────────
        num_col = cfg.get('num_col', (255, 255, 255)) if not self.is_keeper else (255, 255, 255)
        ns = fnt.render(str(self.num), True, num_col)
        surf.blit(ns, (gx - ns.get_width() // 2, gy - ns.get_height() // 2 + 2))

        # ── Throw-in: small raised-arm indicators ────────────────────
        if self.throw_anim > 0:
            progress = min(1.0, self.throw_anim / 20.0)
            arm_len = int(R * (0.6 + 0.6 * progress))
            for sign in (-1, 1):
                ax = gx - self.fdy * sign * (R * 0.8)
                ay = gy + self.fdx * sign * (R * 0.8)
                ex = ax - self.fdx * arm_len * 0.3
                ey = ay - self.fdy * arm_len * 0.3
                pygame.draw.line(surf, shirt, (ax, ay), (ex, ey), 3)
                pygame.draw.circle(surf, skin, (int(ex), int(ey)), max(2, int(R * 0.22)))

        # ── Selection ring ───────────────────────────────────────────
        if self.selected:
            t_ms  = pygame.time.get_ticks()
            pulse = int(2 + 2 * math.sin(t_ms * 0.007))
            rc    = (0, 255, 100) if self.team == 'A' else (255, 200, 0)
            pygame.draw.circle(surf, rc, (gx, gy), R + 4 + pulse, 2)

        # ── Ball possession glow ───────────────────────────────────
        if has_ball:
            pygame.draw.circle(surf, (255, 225, 0), (gx, gy), R + 6, 2)
