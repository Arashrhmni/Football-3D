"""ball.py – Ball physics and rendering."""
import pygame
import math
from constants import (
    W_MX, W_MY, BALL_R, PLAYER_R, BALL_FRIC, BALL_GRAV, w2s, n2, clamp
)


class Ball:
    def __init__(self):
        self.reset()

    def reset(self):
        self.wx = float(W_MX)
        self.wy = float(W_MY)
        self.wz = 0.0
        self.vx = 0.0
        self.vy = 0.0
        self.vz = 0.0
        self.owner        = None   # Player or None
        self.last_toucher = None   # Player or None

    def spd(self):
        return math.hypot(self.vx, self.vy)

    def update(self):
        if self.owner:
            fx, fy = n2(self.owner.fdx, self.owner.fdy)
            self.wx = self.owner.wx + fx * (PLAYER_R + BALL_R + 1)
            self.wy = self.owner.wy + fy * (PLAYER_R + BALL_R + 1)
            self.wz = self.vx = self.vy = self.vz = 0.0
            return

        self.wx += self.vx
        self.wy += self.vy
        self.wz += self.vz

        if self.wz > 0:
            self.vz -= BALL_GRAV
            self.vx *= 0.999
            self.vy *= 0.999
        else:
            self.wz = 0.0
            self.vz = abs(self.vz) * 0.30 if self.vz < -0.6 else 0.0
            self.vx *= BALL_FRIC
            self.vy *= BALL_FRIC

        if self.spd() < 0.08 and self.wz == 0:
            self.vx = self.vy = 0.0

    def release(self):
        if self.owner:
            self.vx = self.owner.vx * 0.22
            self.vy = self.owner.vy * 0.22
            self.owner = None

    def kick(self, tx, ty, spd, vz_init=2.5):
        """Kick toward world position (tx, ty) with given speed and arc."""
        self.release()
        dx, dy = n2(tx - self.wx, ty - self.wy)
        self.vx = dx * spd
        self.vy = dy * spd
        self.vz = vz_init

    def draw(self, surf):
        gx, gy = w2s(self.wx, self.wy, 0)
        bx, by = w2s(self.wx, self.wy, self.wz)
        sr = BALL_R

        # Ground shadow
        shw = pygame.Surface((sr*5, sr*3), pygame.SRCALPHA)
        alp = max(15, int(110 - self.wz * 1.4))
        pygame.draw.ellipse(shw, (0, 0, 0, alp), shw.get_rect())
        surf.blit(shw, (gx - sr*5//2, gy - sr*3//2))

        # Height thread
        if self.wz > 3:
            pygame.draw.line(surf, (140, 140, 140), (gx, gy), (bx, by), 1)

        br = max(4, int(BALL_R * (1 + self.wz * 0.007)))
        pygame.draw.circle(surf, (255, 255, 255), (bx, by), br)
        pygame.draw.circle(surf, (180, 180, 180), (bx, by), br, 1)

        # Rotating pentagon patches
        t_ang = pygame.time.get_ticks() * 0.018
        for ang in [0, 72, 144, 216, 288]:
            a  = math.radians(ang + t_ang)
            px = bx + int(math.cos(a) * br * 0.52)
            py = by + int(math.sin(a) * br * 0.52)
            pygame.draw.circle(surf, (55, 55, 55), (px, py), max(1, br // 3))
