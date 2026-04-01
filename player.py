"""player.py – Player entity: drawing, movement, animation."""
import pygame
import math
import random
from constants import (
    PLAYER_R, AI_REACT, OUT_L, OUT_R, OUT_T, OUT_B,
    BAR_BLUE, BAR_RED, BAR_SHORTS, BAR_SOCKS,
    RMA_SHIRT, RMA_GOLD, RMA_SHORTS, RMA_SOCKS,
    GK_A, GK_B, SKIN_A, HAIR_A, SKIN_B, HAIR_B,
    W_W, W_H, d2, n2, clamp, w2s
)


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

    # ── Kit ──────────────────────────────────────────────────────
    def _kit(self):
        if self.team == 'A':
            if self.is_keeper:
                return GK_A, GK_A, (50, 50, 50), SKIN_A, HAIR_A
            return BAR_BLUE, BAR_SHORTS, BAR_SOCKS, SKIN_A, HAIR_A
        else:
            if self.is_keeper:
                return GK_B, (80, 80, 80), (80, 80, 80), SKIN_B, HAIR_B
            return RMA_SHIRT, RMA_SHORTS, RMA_SOCKS, SKIN_B, HAIR_B

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

    # ── Draw ─────────────────────────────────────────────────────
    def draw(self, surf, ball, fnt):
        shirt, shorts, socks, skin, hair = self._kit()
        has_ball = (ball.owner is self)
        moving   = math.hypot(self.vx, self.vy) > 0.2
        if moving:
            self.anim_t += 0.28
        bob = math.sin(self.anim_t) * 3.2 if moving else 0.0

        gx, gy = w2s(self.wx, self.wy, 0)
        bx, by = w2s(self.wx, self.wy, max(0, bob + 4))

        # Shadow
        shw = pygame.Surface((PLAYER_R*4, PLAYER_R*2), pygame.SRCALPHA)
        pygame.draw.ellipse(shw, (0, 0, 0, 58), shw.get_rect())
        surf.blit(shw, (gx - PLAYER_R*2, gy - PLAYER_R))

        # Legs
        foot_r = max(3, int(PLAYER_R * 0.40))
        l_fwd  = PLAYER_R - 2
        l_off  = int(PLAYER_R * 0.38)
        for sign in (-1, 1):
            ph = self.anim_t + (0 if sign == -1 else math.pi)
            lb = math.sin(ph) * 5 if moving else 0
            lx = bx + int(self.fdx*l_fwd) + int(self.fdy*sign*l_off)
            ly = by + int(self.fdy*l_fwd) - int(self.fdx*sign*l_off) + PLAYER_R + int(lb)
            pygame.draw.line(surf, socks, (lx, by+PLAYER_R-3), (lx, ly-foot_r+1), 5)
            bcol = (25, 25, 25) if self.team == 'A' else (210, 210, 210)
            pygame.draw.circle(surf, bcol, (lx, ly), foot_r)
            pygame.draw.circle(surf, (0, 0, 0), (lx, ly), foot_r, 1)

        # Shorts
        sw = int(PLAYER_R*1.25); sh = int(PLAYER_R*0.9)
        pygame.draw.ellipse(surf, shorts, (bx-sw, by+sh//4, sw*2, sh))

        # Torso
        tw = int(PLAYER_R*1.38); th = int(PLAYER_R*1.48)
        t_y  = by - th + sh//4
        torso = (bx-tw, t_y, tw*2, th)
        pygame.draw.ellipse(surf, shirt, torso)

        if self.team == 'A' and not self.is_keeper:
            sw2 = max(4, tw//3)
            for si, sc in enumerate([BAR_BLUE, BAR_RED, BAR_BLUE]):
                rx   = bx - tw + si*sw2*2
                clip = pygame.Rect(rx, t_y, sw2*2, th)
                inter = pygame.Rect(*torso).clip(clip)
                if inter.w > 0 and inter.h > 0:
                    sub = pygame.Surface((inter.w, inter.h), pygame.SRCALPHA)
                    sub.fill(sc)
                    surf.blit(sub, (inter.x, inter.y))
            pygame.draw.ellipse(surf, tuple(max(0,c-28) for c in shirt), torso, 2)
        elif self.team == 'B' and not self.is_keeper:
            pygame.draw.ellipse(surf, RMA_SHIRT, torso)
            pygame.draw.ellipse(surf, RMA_GOLD, torso, 2)
        else:
            pygame.draw.ellipse(surf, tuple(max(0,c-20) for c in shirt), torso, 2)

        # Jersey number
        ns = fnt.render(str(self.num), True,
                        (255,255,255) if self.team == 'A' else (30,30,30))
        surf.blit(ns, (bx - ns.get_width()//2, t_y + th//2 - ns.get_height()//2))

        # Arms (attached, not floating)
        arm_col = shirt
        for sign in (-1, 1):
            arm_swing = math.sin(self.anim_t + sign*math.pi*0.5)*5 if moving else 0
            sx2 = bx + sign*(tw-2)
            sy2 = t_y + th//4
            ex2 = sx2 + sign*5
            ey2 = sy2 + th//2 + int(arm_swing*0.6)
            pygame.draw.line(surf, arm_col, (sx2, sy2), (ex2, ey2),
                             max(4, int(PLAYER_R*0.32)))
            pygame.draw.circle(surf, skin, (ex2, ey2+3),
                               max(3, int(PLAYER_R*0.24)))

        # Throw-in arms raised
        if self.throw_anim > 0:
            progress  = min(1.0, self.throw_anim / 20.0)
            raise_y   = int(progress * 20)
            for sign in (-1, 1):
                ax = bx + sign*(tw-2)
                ay = t_y + th//4 - raise_y
                pygame.draw.line(surf, arm_col,
                                 (ax, t_y+th//4), (ax, ay),
                                 max(4, int(PLAYER_R*0.32)))
                pygame.draw.circle(surf, skin, (ax, ay),
                                   max(3, int(PLAYER_R*0.24)))

        # Neck + head
        neck_top = t_y - 1
        pygame.draw.line(surf, skin, (bx, neck_top), (bx, neck_top-5), 4)
        hr  = int(PLAYER_R*0.70)
        hcy = neck_top - hr - 1
        pygame.draw.circle(surf, skin, (bx, hcy), hr)
        pygame.draw.circle(surf, tuple(max(0,c-18) for c in skin), (bx,hcy), hr, 1)
        pygame.draw.arc(surf, hair,
                        (bx-hr, hcy-hr, hr*2, hr*2),
                        math.radians(20), math.radians(160), hr)
        # Eyes
        eo = max(2, hr//3)
        for sg in (-1, 1):
            ex3 = bx + int(self.fdx*eo*0.5) + sg*int(abs(self.fdy)*eo*0.5 + max(2, hr//4))
            pygame.draw.circle(surf, (25,25,25), (ex3, hcy+2), 2)

        # Selection ring
        if self.selected:
            t_ms  = pygame.time.get_ticks()
            pulse = int(3 + 2*math.sin(t_ms*0.007))
            rc    = (0, 255, 100) if self.team == 'A' else (255, 200, 0)
            pygame.draw.ellipse(surf, rc,
                (gx-PLAYER_R-pulse, gy-(PLAYER_R+pulse)//2,
                 (PLAYER_R+pulse)*2, PLAYER_R+pulse), 3)

        # Ball glow
        if has_ball:
            pygame.draw.ellipse(surf, (255, 225, 0),
                (gx-PLAYER_R-6, gy-(PLAYER_R+6)//2, (PLAYER_R+6)*2, PLAYER_R+6), 2)
