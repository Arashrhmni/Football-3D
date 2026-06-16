"""player.py - clean top-down footballer sprites.

The old players were mainly circles with hard edges. This version draws each player on a
transparent mini-canvas first, then smooth-scales it onto the pitch. That gives much
cleaner edges and removes the ugly black square look.
"""
import pygame, math, random
from constants import PLAYER_R, AI_REACT, OUT_L, OUT_R, OUT_T, OUT_B, W_W, W_H, d2, clamp, w2s

_KIT_A = None
_KIT_B = None


def set_kits(kit_a, kit_b):
    global _KIT_A, _KIT_B
    _KIT_A = kit_a
    _KIT_B = kit_b


# Light from upper-left; shadows fall lower-right.
SUN_DX, SUN_DY = -0.55, -0.75
SHADOW_ALPHA = 70
SHADOW_DIST = 4


def _shade(col, t):
    """Lighten or darken an RGB colour. t=0.25 is lighter, t=-0.25 darker."""
    if t >= 0:
        return tuple(min(255, int(c + (255 - c) * t)) for c in col)
    return tuple(max(0, int(c * (1 + t))) for c in col)


def _draw_aa_circle(surf, col, pos, radius):
    """Filled circle with a small anti-aliased edge."""
    x, y = int(pos[0]), int(pos[1])
    r = int(radius)
    pygame.draw.circle(surf, col, (x, y), r)
    pygame.draw.circle(surf, _shade(col, -0.35), (x, y), r, max(1, r // 10))


class Player:
    def __init__(self, team, num, hx, hy, is_keeper=False):
        self.team = team
        self.num = num
        self.wx = float(hx)
        self.wy = float(hy)
        self.home_x = float(hx)
        self.home_y = float(hy)
        self.vx = 0.0
        self.vy = 0.0
        self.fdx = 1.0 if team == 'A' else -1.0
        self.fdy = 0.0
        self.is_keeper = is_keeper
        self.selected = False
        self.react = random.randint(0, AI_REACT)
        self.tackle_cd = 0
        self.anim_t = random.uniform(0, math.pi * 2)
        self.throw_anim = 0
        self.hold_timer = 0
        self.stamina = 1.0

    def _kit(self):
        cfg = _KIT_A if self.team == 'A' else _KIT_B
        if cfg is None:
            return (0, 82, 170), (20, 35, 80), (0, 82, 170), (222, 182, 142), (38, 28, 18)
        if self.is_keeper:
            gk = cfg['gk']
            dk = tuple(max(0, c - 45) for c in gk)
            return gk, dk, dk, cfg['skin'], cfg['hair']
        return cfg['shirt1'], cfg['shorts'], cfg['socks'], cfg['skin'], cfg['hair']

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

    # ── Sprite helpers ─────────────────────────────────────────────
    def _local_point(self, cx, cy, sc, x, y):
        """Convert a small local footballer coordinate into sprite pixels."""
        return (int(cx + x * sc), int(cy + y * sc))

    def _poly(self, surf, col, cx, cy, sc, pts):
        pygame.draw.polygon(surf, col, [self._local_point(cx, cy, sc, x, y) for x, y in pts])

    def _draw_body_pattern(self, surf, cx, cy, sc, cfg, shirt, shorts):
        """Draw shirt, stripes/halves, shorts and shirt highlights."""
        outline = (18, 18, 18)
        body = [(-7, -8), (5, -9), (12, -2), (11, 10), (4, 15), (-5, 15), (-11, 9), (-12, -2)]
        self._poly(surf, outline, cx, cy, sc, [(x * 1.10, y * 1.10) for x, y in body])
        self._poly(surf, shirt, cx, cy, sc, body)

        if not self.is_keeper and cfg.get('half_half'):
            shirt2 = cfg.get('shirt2', _shade(shirt, -0.15))
            self._poly(surf, shirt2, cx, cy, sc, [(0, -9), (5, -9), (12, -2), (11, 10), (4, 15), (0, 15)])
        elif not self.is_keeper and cfg.get('stripe'):
            cols = cfg.get('stripe_cols', [shirt, cfg.get('shirt2', _shade(shirt, -0.15)), shirt])
            stripe_w = 5
            for i, x in enumerate(range(-8, 9, stripe_w)):
                self._poly(surf, cols[i % len(cols)], cx, cy, sc, [(x, -8), (x + stripe_w, -8), (x + stripe_w - 1, 14), (x - 1, 14)])

        # Soft shirt highlight and darker lower body make the sprite read as 3D.
        hi = _shade(shirt, 0.35)
        lo = _shade(shirt, -0.25)
        pygame.draw.line(surf, hi, self._local_point(cx, cy, sc, -6, -5), self._local_point(cx, cy, sc, 4, -6), max(1, int(2 * sc)))
        pygame.draw.line(surf, lo, self._local_point(cx, cy, sc, -5, 13), self._local_point(cx, cy, sc, 7, 11), max(1, int(3 * sc)))

        # Shorts as a curved block near the bottom of the torso.
        self._poly(surf, shorts, cx, cy, sc, [(-8, 9), (8, 9), (7, 16), (1, 14), (-1, 14), (-7, 16)])

    def _draw_sprite(self, shirt, shorts, socks, skin, hair, cfg, moving, has_ball, fnt):
        """Return a polished transparent player sprite and its centre offset."""
        R = int(PLAYER_R * 1.55)
        scale = 3                         # draw large first, then smooth-scale down
        pad = 16
        size = (R * 2 + pad * 2) * scale
        cx = cy = size // 2
        sc = R / 18.0 * scale
        sprite = pygame.Surface((size, size), pygame.SRCALPHA)

        # Sprite shadow. It is transparent, so no black square can appear.
        shadow_rect = pygame.Rect(0, 0, int(R * 2.25 * scale), int(R * 1.10 * scale))
        shadow_rect.center = (cx + int(4 * scale), cy + int(7 * scale))
        pygame.draw.ellipse(sprite, (0, 0, 0, SHADOW_ALPHA), shadow_rect)

        # Small running animation: legs move opposite to each other.
        step = math.sin(self.anim_t) * (3.5 if moving else 0.8)
        side = 6.5
        boot = (18, 18, 18)
        for sign, phase in [(-1, step), (1, -step)]:
            x1, y1 = -3, 12
            x2, y2 = phase, 19
            foot_x, foot_y = phase + 2, 24
            pygame.draw.line(sprite, socks, self._local_point(cx, cy, sc, x1, y1), self._local_point(cx, cy, sc, x2, y2), max(2, int(3 * sc)))
            pygame.draw.ellipse(sprite, boot, pygame.Rect(*self._local_point(cx, cy, sc, foot_x - 3, foot_y - 2), int(6 * sc), int(4 * sc)))
            # Shift each leg sideways so it looks like two separate legs.
            # This tiny overlay keeps them readable even at small size.
            pygame.draw.circle(sprite, socks, self._local_point(cx, cy, sc, sign * side * 0.38, 15), max(1, int(1.4 * sc)))

        # Arms behind and beside the shirt.
        arm_dark = _shade(skin, -0.15)
        for sign in (-1, 1):
            swing = -step * 0.55 * sign
            shoulder = self._local_point(cx, cy, sc, sign * 9, -3)
            hand = self._local_point(cx, cy, sc, sign * (14 + swing), 9 - swing)
            pygame.draw.line(sprite, _shade(shirt, -0.12), shoulder, hand, max(2, int(3.0 * sc)))
            _draw_aa_circle(sprite, arm_dark, hand, max(2, int(2.2 * sc)))

        self._draw_body_pattern(sprite, cx, cy, sc, cfg, shirt, shorts)

        # Head and hair are drawn in front of the body. Slightly above centre = nicer top-down look.
        head_pos = self._local_point(cx, cy, sc, 0, -16)
        _draw_aa_circle(sprite, skin, head_pos, int(5.2 * sc))
        hair_pos = self._local_point(cx, cy, sc, 0, -19)
        pygame.draw.ellipse(sprite, hair, pygame.Rect(hair_pos[0] - int(4.6 * sc), hair_pos[1] - int(2.9 * sc), int(9.2 * sc), int(5.4 * sc)))

        # Tiny face direction marker. It helps the player look alive instead of like a flat coin.
        eye_col = (25, 25, 25)
        pygame.draw.circle(sprite, eye_col, self._local_point(cx, cy, sc, -1.6, -16.7), max(1, int(0.55 * sc)))
        pygame.draw.circle(sprite, eye_col, self._local_point(cx, cy, sc, 1.6, -16.7), max(1, int(0.55 * sc)))

        # Clean jersey number on a subtle dark mini-panel for readability.
        num_col = cfg.get('num_col', (255, 255, 255)) if not self.is_keeper else (255, 255, 255)
        number = fnt.render(str(self.num), True, num_col)
        number = pygame.transform.smoothscale(number, (max(7 * scale, number.get_width() * scale // 2), max(8 * scale, number.get_height() * scale // 2)))
        plate = pygame.Rect(0, 0, number.get_width() + 5 * scale, number.get_height() + 2 * scale)
        plate.center = self._local_point(cx, cy, sc, 0, 2)
        pygame.draw.rect(sprite, (0, 0, 0, 95), plate, border_radius=max(2, int(2 * sc)))
        sprite.blit(number, (plate.centerx - number.get_width() // 2, plate.centery - number.get_height() // 2))

        # Downscale for anti-aliased final sprite.
        final_size = size // scale
        sprite = pygame.transform.smoothscale(sprite, (final_size, final_size))
        return sprite, final_size // 2, R

    # ── Main draw ─────────────────────────────────────────────────
    def draw(self, surf, ball, fnt):
        shirt, shorts, socks, skin, hair = self._kit()
        cfg = (_KIT_A if self.team == 'A' else _KIT_B) or {}
        has_ball = (ball.owner is self)
        moving = math.hypot(self.vx, self.vy) > 0.2
        if moving:
            self.anim_t += 0.28

        gx, gy = w2s(self.wx, self.wy, 0)
        sprite, offset, R = self._draw_sprite(shirt, shorts, socks, skin, hair, cfg, moving, has_ball, fnt)

        # Rotate the polished sprite so the head points in the movement/facing direction.
        angle = -math.degrees(math.atan2(self.fdy, self.fdx)) + 90
        sprite = pygame.transform.rotozoom(sprite, angle, 1.0)
        rect = sprite.get_rect(center=(gx, gy))
        surf.blit(sprite, rect)

        # Throw-in animation arms.
        if self.throw_anim > 0:
            prog = min(1.0, self.throw_anim / 20.0)
            alen = int(R * (0.6 + 0.6 * prog))
            for sign in (-1, 1):
                ax = gx - self.fdy * sign * (R * 0.8)
                ay = gy + self.fdx * sign * (R * 0.8)
                ex = ax - self.fdx * alen * 0.3
                ey = ay - self.fdy * alen * 0.3
                pygame.draw.line(surf, shirt, (ax, ay), (ex, ey), 3)
                pygame.draw.circle(surf, skin, (int(ex), int(ey)), max(2, int(R * 0.22)))

        # Selection and ball possession rings stay outside the sprite and remain very clear.
        if self.selected:
            pulse = int(2 + 2 * math.sin(pygame.time.get_ticks() * 0.007))
            rc = (0, 255, 100) if self.team == 'A' else (255, 200, 0)
            pygame.draw.circle(surf, rc, (gx, gy), R + 4 + pulse, 2)

        if has_ball:
            pygame.draw.circle(surf, (255, 225, 0), (gx, gy), R + 6, 2)
