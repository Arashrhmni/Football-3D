"""pitch.py – Bake the static top-down pitch surface once at startup.

Drawn as a clean bird's-eye-view football pitch matching real-world
proportions (105m x 68m), in the style of a standard pitch diagram:
  - alternating mowed-grass stripes
  - crisp white boundary, halfway line, centre circle + spot
  - penalty areas with arcs ("the D") and spots
  - six-yard boxes
  - corner arcs
  - simple rectangular goal frames at each end
"""
import pygame
import math
from constants import (
    SCR_W, SCR_H, W_W, W_H, W_MX, W_MY,
    GOAL_TOP, GOAL_BOT, GOAL_DEPTH_W,
    PA_W, PA_H, SB_W, SB_H, CTR_R, PEN_SPOT_D,
    OUT_L, OUT_T, OUT_R, OUT_B,
    PITCH_SCALE, w2s, lerpc
)

WHITE      = (255, 255, 255)
LINE_W     = 3
GRASS_DARK  = (46, 142, 46)
GRASS_LIGHT = (58, 168, 58)
OUTSIDE_COL = (30, 95, 32)
NET_COL     = (215, 225, 215)

# ── Grass texture tuning ──────────────────────────────────────────
MOW_BAND_H    = 14     # world units per cross-mow band (horizontal bands)
MOW_SHIFT     = 2       # tonal shift per band (subtle)
NOISE_CELL    = 4      # screen-px cell size for fine blade-noise
NOISE_ALPHA   = 10      # max alpha of noise speckle overlay
VIGNETTE_ALPHA= 55      # darkness at the pitch corners (max alpha)


def _arc_points(center_wx, center_wy, radius, a0, a1, steps=24):
    """World-space arc points from angle a0 to a1 (degrees), projected to screen."""
    pts = []
    for i in range(steps + 1):
        a = math.radians(a0 + (a1 - a0) * i / steps)
        wx = center_wx + radius * math.cos(a)
        wy = center_wy + radius * math.sin(a)
        pts.append(w2s(wx, wy))
    return pts


def _draw_mow_bands(surf, x0, x1, y_top_world, y_bot_world, base_col):
    """
    Draw subtle horizontal 'cross-mow' bands within a vertical grass stripe,
    alternating between base_col and a slightly lighter/darker shade.
    x0, x1: screen-space x bounds of this stripe (already projected).
    y_top_world, y_bot_world: world-space y range of the pitch.
    """
    n_bands = max(1, int((y_bot_world - y_top_world) / MOW_BAND_H))
    for bi in range(n_bands):
        wy0 = y_top_world + bi * MOW_BAND_H
        wy1 = min(y_bot_world, wy0 + MOW_BAND_H)
        p0 = w2s(W_MX, wy0)
        p1 = w2s(W_MX, wy1)
        # Alternate a faint tonal shift every other band
        if bi % 2 == 0:
            col = tuple(min(255, c + MOW_SHIFT) for c in base_col)
        else:
            col = tuple(max(0, c - MOW_SHIFT) for c in base_col)
        rect = pygame.Rect(x0, p0[1], x1 - x0, max(1, p1[1] - p0[1]))
        pygame.draw.rect(surf, col, rect)


def _apply_grass_noise(surf, pitch_rect, seed=1234):
    """
    Overlay a sparse speckle of slightly lighter/darker cells across the
    pitch to simulate blade-level texture variation. Cheap & deterministic.
    """
    import random
    rng = random.Random(seed)
    noise_layer = pygame.Surface((pitch_rect.w, pitch_rect.h), pygame.SRCALPHA)
    cols = max(1, pitch_rect.w // NOISE_CELL)
    rows = max(1, pitch_rect.h // NOISE_CELL)
    for ry in range(rows):
        for rx in range(cols):
            if rng.random() < 0.10:   # sparse speckling
                shade = rng.choice([-1, 1])
                alpha = rng.randint(NOISE_ALPHA // 2, NOISE_ALPHA)
                col = (255, 255, 255, alpha) if shade > 0 else (0, 0, 0, alpha)
                pygame.draw.rect(
                    noise_layer, col,
                    (rx * NOISE_CELL, ry * NOISE_CELL, NOISE_CELL, NOISE_CELL)
                )
    surf.blit(noise_layer, pitch_rect.topleft)


def _apply_vignette(surf, pitch_rect):
    """
    Soft radial darkening toward the pitch corners for depth/realism.
    Built once as a small low-res gradient then smooth-scaled up,
    avoiding banding/ring artefacts from drawing many rectangles.
    """
    GRID = 32   # low-res gradient grid (fast to compute, smooth when scaled)
    small = pygame.Surface((GRID, GRID), pygame.SRCALPHA)
    cx, cy = (GRID - 1) / 2, (GRID - 1) / 2
    max_dist = math.hypot(cx, cy)
    for gy in range(GRID):
        for gx in range(GRID):
            d = math.hypot(gx - cx, gy - cy) / max_dist   # 0 centre -> 1 corner
            alpha = int(VIGNETTE_ALPHA * (d ** 2.2))
            small.set_at((gx, gy), (0, 0, 0, alpha))
    big = pygame.transform.smoothscale(small, (pitch_rect.w, pitch_rect.h))
    surf.blit(big, pitch_rect.topleft)


def bake_pitch() -> pygame.Surface:
    """Return a fully drawn static top-down pitch Surface."""
    surf = pygame.Surface((SCR_W, SCR_H))

    # ── Background gradient (area outside the stadium) ──────────
    for row in range(SCR_H):
        t = row / SCR_H
        pygame.draw.line(surf, lerpc((34, 60, 36), (18, 36, 22), t), (0, row), (SCR_W, row))

    # ── Outside run-off (track / surrounds) ──────────────────────
    out_tl = w2s(-OUT_L, -OUT_T)
    out_br = w2s(W_W + OUT_R, W_H + OUT_B)
    out_rect = pygame.Rect(out_tl[0], out_tl[1],
                            out_br[0] - out_tl[0], out_br[1] - out_tl[1])
    pygame.draw.rect(surf, OUTSIDE_COL, out_rect)

    # ── Grass stripes (vertical mowed bands across the pitch) ────
    # Each vertical stripe is further subdivided into horizontal
    # cross-mow bands for a realistic checkerboard-mowed look.
    n_stripes = 12
    step = W_W / n_stripes
    for i in range(n_stripes):
        x0, x1 = i * step, (i + 1) * step
        p0 = w2s(x0, 0)
        p1 = w2s(x1, W_H)
        base_col = GRASS_DARK if i % 2 == 0 else GRASS_LIGHT
        _draw_mow_bands(surf, p0[0], p1[0], 0, W_H, base_col)

    # ── Pitch outer boundary ──────────────────────────────────────
    tl = w2s(0, 0)
    br = w2s(W_W, W_H)
    pitch_rect = pygame.Rect(tl[0], tl[1], br[0] - tl[0], br[1] - tl[1])
    pygame.draw.rect(surf, WHITE, pitch_rect, LINE_W)

    # Fine speckle texture across the grass (drawn before line markings
    # so the white lines stay crisp on top)
    _apply_grass_noise(surf, pitch_rect)

    # ── Halfway line ───────────────────────────────────────────────
    pygame.draw.line(surf, WHITE, w2s(W_MX, 0), w2s(W_MX, W_H), LINE_W)

    # ── Centre circle + spot ────────────────────────────────────────
    c_px = w2s(W_MX, W_MY)
    r_px = int(CTR_R * PITCH_SCALE)
    pygame.draw.circle(surf, WHITE, c_px, r_px, LINE_W)
    pygame.draw.circle(surf, WHITE, c_px, 4)

    # ── Penalty areas, arcs ("the D"), spots, six-yard boxes ────────
    for side_x, sign, arc_center_ang in [(0, 1, 0.0), (W_W, -1, 180.0)]:
        # Penalty area
        x1 = side_x + sign * PA_W
        y0, y1 = W_MY - PA_H // 2, W_MY + PA_H // 2
        p0 = w2s(side_x, y0)
        p1 = w2s(x1, y1)
        rect = pygame.Rect(min(p0[0], p1[0]), min(p0[1], p1[1]),
                            abs(p1[0]-p0[0]), abs(p1[1]-p0[1]))
        pygame.draw.rect(surf, WHITE, rect, LINE_W)

        # Six-yard box
        x1b = side_x + sign * SB_W
        y0b, y1b = W_MY - SB_H // 2, W_MY + SB_H // 2
        p0b = w2s(side_x, y0b)
        p1b = w2s(x1b, y1b)
        rectb = pygame.Rect(min(p0b[0], p1b[0]), min(p0b[1], p1b[1]),
                             abs(p1b[0]-p0b[0]), abs(p1b[1]-p0b[1]))
        pygame.draw.rect(surf, WHITE, rectb, LINE_W)

        # Penalty spot
        spot_wx = side_x + sign * PEN_SPOT_D
        pygame.draw.circle(surf, WHITE, w2s(spot_wx, W_MY), 4)

        # Penalty arc ("the D") — only the portion outside the box
        dx = abs(PA_W - PEN_SPOT_D)
        half_ang = math.degrees(math.acos(clamp_ratio(dx / CTR_R)))
        a0 = arc_center_ang - half_ang
        a1 = arc_center_ang + half_ang
        pts = _arc_points(spot_wx, W_MY, CTR_R, a0, a1)
        if len(pts) > 1:
            pygame.draw.lines(surf, WHITE, False, pts, LINE_W)

    # ── Corner arcs (quarter circles, radius 1m) ─────────────────────
    corner_r = 12
    for (cx, cy), (a0, a1) in [
        ((0, 0),       (0, 90)),     # top-left    -> bulges toward (+x,+y)
        ((W_W, 0),     (90, 180)),   # top-right   -> bulges toward (-x,+y)
        ((W_W, W_H),   (180, 270)),  # bottom-right-> bulges toward (-x,-y)
        ((0, W_H),     (270, 360)),  # bottom-left -> bulges toward (+x,-y)
    ]:
        pts = _arc_points(cx, cy, corner_r, a0, a1, steps=10)
        if len(pts) > 1:
            pygame.draw.lines(surf, WHITE, False, pts, LINE_W)

    # ── Goals: simple rectangular frames poking out of the pitch ─────
    for side_x, sign in [(0, -1), (W_W, 1)]:
        x1 = side_x + sign * GOAL_DEPTH_W
        p0 = w2s(side_x, GOAL_TOP)
        p1 = w2s(x1, GOAL_BOT)
        rect = pygame.Rect(min(p0[0], p1[0]), min(p0[1], p1[1]),
                            abs(p1[0]-p0[0]), abs(p1[1]-p0[1]))
        pygame.draw.rect(surf, WHITE, rect, LINE_W)

        # Simple net mesh inside the goal frame
        n_v, n_h = 3, 2
        for vi in range(1, n_v):
            wx = side_x + sign * GOAL_DEPTH_W * vi / n_v
            pygame.draw.line(surf, NET_COL, w2s(wx, GOAL_TOP), w2s(wx, GOAL_BOT), 1)
        for hi in range(1, n_h + 1):
            wy = GOAL_TOP + (GOAL_BOT - GOAL_TOP) * hi / (n_h + 1)
            pygame.draw.line(surf, NET_COL, w2s(side_x, wy), w2s(x1, wy), 1)

    # ── Soft vignette for depth (applied last, over everything) ────
    _apply_vignette(surf, pitch_rect)

    return surf


def clamp_ratio(v):
    """Clamp a cosine ratio to the valid [-1, 1] domain."""
    return max(-1.0, min(1.0, v))
