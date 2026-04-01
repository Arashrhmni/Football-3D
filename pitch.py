"""pitch.py – Bake the static pitch surface once at startup."""
import pygame
import math
from constants import (
    SCR_W, SCR_H, W_W, W_H, W_MX, W_MY,
    GOAL_TOP, GOAL_BOT, GOAL_DEPTH_W, GOAL_H_Z,
    PA_W, PA_H, SB_W, SB_H, CTR_R,
    OUT_L, OUT_T, OUT_R, OUT_B,
    w2s, lerpc
)


def bake_pitch() -> pygame.Surface:
    """Return a fully drawn static pitch Surface."""
    surf = pygame.Surface((SCR_W, SCR_H))

    # ── Sky gradient
    for row in range(SCR_H):
        t = row / SCR_H
        pygame.draw.line(surf, lerpc((95,165,225),(38,58,98),t), (0,row),(SCR_W,row))

    # ── Outside run-off (darker green)
    out_corners = [
        w2s(-OUT_L, -OUT_T), w2s(W_W+OUT_R, -OUT_T),
        w2s(W_W+OUT_R, W_H+OUT_B), w2s(-OUT_L, W_H+OUT_B)
    ]
    pygame.draw.polygon(surf, (28, 100, 28), out_corners)

    # ── Grass stripes
    step = W_W / 12
    for i in range(12):
        x0, x1 = i*step, (i+1)*step
        col = (36,125,36) if i%2==0 else (46,145,46)
        pygame.draw.polygon(surf, col,
            [w2s(x0,0), w2s(x1,0), w2s(x1,W_H), w2s(x0,W_H)])

    # ── Pitch boundary
    pygame.draw.polygon(surf, (255,255,255),
        [w2s(0,0), w2s(W_W,0), w2s(W_W,W_H), w2s(0,W_H)], 2)

    # ── Halfway line + centre circle
    pygame.draw.line(surf, (255,255,255), w2s(W_MX,0), w2s(W_MX,W_H), 2)
    pts = [w2s(W_MX + CTR_R*math.cos(a), W_MY + CTR_R*math.sin(a))
           for a in [i*math.pi/24 for i in range(49)]]
    pygame.draw.lines(surf, (255,255,255), False, pts, 2)
    pygame.draw.circle(surf, (255,255,255), w2s(W_MX, W_MY), 5)

    # ── Penalty areas, arcs, spots, six-yard boxes
    for sx, sg in [(0, 1), (W_W, -1)]:
        x1  = sx + sg*PA_W
        y0, y1 = W_MY-PA_H//2, W_MY+PA_H//2
        pygame.draw.lines(surf, (255,255,255), True,
            [w2s(sx,y0), w2s(x1,y0), w2s(x1,y1), w2s(sx,y1)], 2)
        spot = sx + sg*110
        pygame.draw.circle(surf, (255,255,255), w2s(spot, W_MY), 4)
        arc = [w2s(spot+90*math.cos(math.radians(a)), W_MY+90*math.sin(math.radians(a)))
               for a in range(-62, 63, 4)]
        if len(arc) > 1:
            pygame.draw.lines(surf, (255,255,255), False, arc, 2)
        x1b = sx + sg*SB_W
        y0b, y1b = W_MY-SB_H//2, W_MY+SB_H//2
        pygame.draw.lines(surf, (255,255,255), True,
            [w2s(sx,y0b), w2s(x1b,y0b), w2s(x1b,y1b), w2s(sx,y1b)], 2)

    # ── Corner arcs
    for cx, cy in [(0,0),(W_W,0),(0,W_H),(W_W,W_H)]:
        sxs = 1 if cx==0 else -1
        sys2 = 1 if cy==0 else -1
        arc = [w2s(cx+sxs*12*math.cos(math.radians(a)),
                   cy+sys2*12*math.sin(math.radians(a)))
               for a in range(91)]
        if len(arc) > 1:
            pygame.draw.lines(surf, (255,255,255), False, arc, 2)

    # ── Goals (3-D box + net)
    gd = GOAL_DEPTH_W; gh = GOAL_H_Z
    for sx, sg in [(0, -1), (W_W, 1)]:
        ft  = w2s(sx, GOAL_TOP);        fb  = w2s(sx, GOAL_BOT)
        bt  = w2s(sx+sg*gd, GOAL_TOP);  bb  = w2s(sx+sg*gd, GOAL_BOT)
        ftt = w2s(sx, GOAL_TOP, gh);    fbt = w2s(sx, GOAL_BOT, gh)
        btt = w2s(sx+sg*gd, GOAL_TOP, gh); bbt = w2s(sx+sg*gd, GOAL_BOT, gh)
        for base, top in [(ft,ftt),(fb,fbt),(bt,btt),(bb,bbt)]:
            pygame.draw.line(surf, (245,245,245), base, top, 3)
        pygame.draw.line(surf, (245,245,245), ftt, fbt, 3)
        for a, b in [(btt,bbt),(ftt,btt),(fbt,bbt)]:
            pygame.draw.line(surf, (200,200,200), a, b, 2)
        nc = (185, 185, 185)
        for ni in range(8):
            t2 = ni/7; gy2 = GOAL_TOP + t2*(GOAL_BOT-GOAL_TOP)
            pygame.draw.line(surf, nc, w2s(sx,gy2), w2s(sx,gy2,gh), 1)
            pygame.draw.line(surf, nc, w2s(sx,gy2,gh), w2s(sx+sg*gd,gy2,gh), 1)
        for ni in range(6):
            t2 = ni/5; gz = t2*gh
            pygame.draw.line(surf, nc, w2s(sx,GOAL_TOP,gz), w2s(sx,GOAL_BOT,gz), 1)

    return surf
