"""
╔══════════════════════════════════════════════════════╗
║         FOOTBALL 3D  —  11 vs 11  (Isometric)        ║
╠══════════════════════════════════════════════════════╣
║  MOVE          Arrow Keys / WASD                     ║
║  SPRINT        Z (hold)                              ║
║  PASS          SPACE  (to best open teammate)        ║
║  SHOOT         F  or  Left-Shift                     ║
║  TACKLE        X  (when defending, near opponent)    ║
║  SWITCH        TAB  (nearest to ball)                ║
║  QUIT          ESC                                   ║
╚══════════════════════════════════════════════════════╝

3-D isometric projection:
  World coords  (wx, wy)  — the flat pitch plane
  Screen coords (sx, sy)  — projected + height offset for ball arc

Perspective:
  sx = (wx - wy) * cos30  +  cx
  sy = (wx + wy) * sin30  -  wz * vscale  +  cy
"""

import pygame, math, random, sys

# ─────────────────────────────────────────────────────────────────────────────
#  WORLD DIMENSIONS  (flat 2-D world used for all physics / AI)
# ─────────────────────────────────────────────────────────────────────────────
W_W   = 900          # world width  (x-axis → right)
W_H   = 560          # world height (y-axis → down)
W_MX  = W_W // 2
W_MY  = W_H // 2

GOAL_W   = 110       # world units
GOAL_TOP = W_MY - GOAL_W // 2
GOAL_BOT = W_MY + GOAL_W // 2

# ─────────────────────────────────────────────────────────────────────────────
#  ISO PROJECTION
# ─────────────────────────────────────────────────────────────────────────────
SCR_W, SCR_H = 1200, 740

ISO_ANG  = math.radians(30)
ISO_CX   = SCR_W // 2       # screen origin x
ISO_CY   = SCR_H // 2 + 40  # screen origin y  (shifted down so pitch fits)
ISO_SX   = math.cos(ISO_ANG) * 0.72   # x scale
ISO_SY   = math.sin(ISO_ANG) * 0.72   # y scale
ISO_VZ   = 1.1               # vertical (height) scale on screen

def world_to_screen(wx, wy, wz=0.0):
    """Convert world (x,y,z) → screen (sx,sy).  z=0 is the ground plane."""
    sx = (wx - W_MX) * ISO_SX - (wy - W_MY) * ISO_SX + ISO_CX
    sy = (wx - W_MX) * ISO_SY + (wy - W_MY) * ISO_SY - wz * ISO_VZ + ISO_CY
    return int(sx), int(sy)

def w2s(wx, wy, wz=0.0):
    return world_to_screen(wx, wy, wz)

# ─────────────────────────────────────────────────────────────────────────────
#  CONSTANTS
# ─────────────────────────────────────────────────────────────────────────────
FPS            = 60
PLAYER_R       = 13      # world-unit radius for player
BALL_R         = 6
PLAYER_SPD     = 3.4
SPRINT_MULT    = 1.6
BALL_FRIC      = 0.977
BALL_GRAV      = 0.55    # gravity pulling wz toward 0
PASS_SPD       = 10.0
SHOOT_SPD      = 17.0
CONTROL_R      = 18
TACKLE_R       = 22
SHOOT_POWER_MAX= 1.0
SHOOT_POWER_MIN= 0.55

# CPU knobs
AI_WALK   = 1.9
AI_JOG    = 2.6
AI_RUN    = 3.4
AI_PRESS  = 85
AI_SHOOT_R= 230
AI_TACKLE = 0.013
AI_REACT  = 38

# ─────────────────────────────────────────────────────────────────────────────
#  PALETTE
# ─────────────────────────────────────────────────────────────────────────────
C_SKY       = (120, 185, 240)
C_GRASS_D   = (38, 130, 38)
C_GRASS_L   = (50, 155, 50)
C_LINE      = (255, 255, 255)
C_WHITE     = (255, 255, 255)
C_BLACK     = (0, 0, 0)
C_YELLOW    = (255, 228, 0)
C_LIME      = (170, 255, 50)
C_GRAY      = (160, 160, 160)
C_DGRAY     = (70, 70, 70)
C_TEAM_A    = (30,  110, 230)    # human – blue
C_TEAM_A2   = (15,  55,  130)
C_TEAM_B    = (215,  35,  35)    # cpu – red
C_TEAM_B2   = (110,  18,  18)
C_KEEPER    = (255, 200,  0)
C_KEEPER2   = (160, 120,  0)
C_NET       = (200, 200, 200)
C_SHADOW    = (0, 0, 0)
C_BALL      = (255, 255, 255)
C_BALL2     = (60, 60, 60)
C_SHOOT_BAR = (255, 80, 0)
C_PRESS_BAR = (0, 200, 255)
C_PASS_LINE = (180, 255, 60)

# ─────────────────────────────────────────────────────────────────────────────
#  FORMATION  (rel x 0→1 from own goal, rel y 0→1 top→bot)
# ─────────────────────────────────────────────────────────────────────────────
FORM = [
    (0.05, 0.50),  # 0  GK
    (0.22, 0.14),  # 1  LB
    (0.22, 0.38),  # 2  CB
    (0.22, 0.62),  # 3  CB
    (0.22, 0.86),  # 4  RB
    (0.46, 0.22),  # 5  LM
    (0.46, 0.50),  # 6  CM
    (0.46, 0.78),  # 7  RM
    (0.70, 0.15),  # 8  LW
    (0.70, 0.50),  # 9  ST
    (0.70, 0.85),  # 10 RW
]

# ─────────────────────────────────────────────────────────────────────────────
def dist2(a, b):
    return math.hypot(a[0]-b[0], a[1]-b[1])

def norm2(vx, vy):
    m = math.hypot(vx, vy)
    return (vx/m, vy/m) if m > 1e-9 else (0.0, 0.0)

def clamp(v, lo, hi):
    return max(lo, min(hi, v))

def world_clamp(wx, wy, r=PLAYER_R):
    return clamp(wx, r, W_W-r), clamp(wy, r, W_H-r)

# ─────────────────────────────────────────────────────────────────────────────
#  BALL
# ─────────────────────────────────────────────────────────────────────────────
class Ball:
    def __init__(self):
        self.reset()

    def reset(self):
        self.wx  = float(W_MX)
        self.wy  = float(W_MY)
        self.wz  = 0.0          # height above ground
        self.vx  = 0.0
        self.vy  = 0.0
        self.vz  = 0.0          # vertical velocity
        self.owner        = None
        self.last_toucher = None

    def spd(self):
        return math.hypot(self.vx, self.vy)

    def update(self):
        if self.owner:
            ox, oy = self.owner.wx, self.owner.wy
            fx, fy = norm2(self.owner.fdx, self.owner.fdy)
            self.wx = ox + fx * (PLAYER_R + BALL_R + 1)
            self.wy = oy + fy * (PLAYER_R + BALL_R + 1)
            self.wz  = 0.0
            self.vx = self.vy = self.vz = 0.0
            return

        self.wx += self.vx
        self.wy += self.vy
        self.wz += self.vz

        # Gravity
        if self.wz > 0:
            self.vz -= BALL_GRAV
        else:
            self.wz  = 0.0
            self.vz  = max(0.0, self.vz)
            if abs(self.vz) < 0.5:
                self.vz = 0.0
            else:
                self.vz *= -0.35   # bounce

        # Ground friction only when on ground
        if self.wz == 0.0:
            self.vx *= BALL_FRIC
            self.vy *= BALL_FRIC
            if self.spd() < 0.1:
                self.vx = self.vy = 0.0

    def release(self):
        if self.owner:
            self.vx = self.owner.vx * 0.3
            self.vy = self.owner.vy * 0.3
            self.owner = None

    def shoot(self, tx, ty, arc=True):
        """Launch ball toward (tx,ty) with a parabolic arc."""
        self.release()
        dx, dy = norm2(tx - self.wx, ty - self.wy)
        d = dist2((self.wx, self.wy), (tx, ty))
        spd = SHOOT_SPD * clamp(0.5 + d/W_W, 0.55, 1.0)
        self.vx = dx * spd
        self.vy = dy * spd
        self.vz = 8.0 if arc else 2.0   # loft

    def pass_to(self, tx, ty):
        self.release()
        dx, dy = norm2(tx - self.wx, ty - self.wy)
        self.vx = dx * PASS_SPD
        self.vy = dy * PASS_SPD
        self.vz = 1.5

    def draw(self, surf):
        # Shadow on ground
        sx, sy  = w2s(self.wx, self.wy, 0)
        bx, by  = w2s(self.wx, self.wy, self.wz)
        sr = max(4, int(BALL_R * 1.1))
        shadow_surf = pygame.Surface((sr*4, sr*2), pygame.SRCALPHA)
        pygame.draw.ellipse(shadow_surf, (0,0,0,90), (0,0,sr*4,sr*2))
        surf.blit(shadow_surf, (sx - sr*2, sy - sr))

        # Height line
        if self.wz > 2:
            pygame.draw.line(surf, (160,160,160), (sx, sy), (bx, by), 1)

        # Ball body
        br = max(4, int(BALL_R * (1 + self.wz * 0.012)))
        pygame.draw.circle(surf, C_BALL,  (bx, by), br)
        pygame.draw.circle(surf, C_BALL2, (bx, by), br, 1)
        pygame.draw.circle(surf, C_DGRAY, (bx-1, by-1), max(2, br//3))

# ─────────────────────────────────────────────────────────────────────────────
#  PLAYER
# ─────────────────────────────────────────────────────────────────────────────
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
        self.fdx       = 1.0 if team == 'A' else -1.0   # facing dir
        self.fdy       = 0.0
        self.is_keeper = is_keeper
        self.selected  = False
        self.react     = random.randint(0, AI_REACT)
        # Shoot power charge
        self.charging  = False
        self.charge    = 0.0
        # Tackle cooldown
        self.tackle_cd = 0
        # Bobbing animation
        self.anim_t    = random.uniform(0, math.pi*2)

    def move_toward(self, tx, ty, spd):
        d = dist2((self.wx, self.wy), (tx, ty))
        if d < 0.5:
            return
        r = min(spd / d, 1.0)
        self.vx = (tx - self.wx) * r
        self.vy = (ty - self.wy) * r
        ln = math.hypot(self.vx, self.vy)
        if ln > 0:
            self.fdx = self.vx / ln
            self.fdy = self.vy / ln
        self.wx += self.vx
        self.wy += self.vy
        self.wx, self.wy = world_clamp(self.wx, self.wy)

    def draw(self, surf, ball, font_small):
        has_ball = (ball.owner is self)
        moving   = math.hypot(self.vx, self.vy) > 0.3

        # Body bob
        if moving:
            self.anim_t += 0.28
        bob = math.sin(self.anim_t) * 3.0 if moving else 0.0

        # Colors
        if self.is_keeper:
            body_col, dark_col = C_KEEPER, C_KEEPER2
        elif self.team == 'A':
            body_col, dark_col = C_TEAM_A, C_TEAM_A2
        else:
            body_col, dark_col = C_TEAM_B, C_TEAM_B2

        # Screen pos
        sx, sy = w2s(self.wx, self.wy, 0)
        # 3-D body at height bob
        bsx, bsy = w2s(self.wx, self.wy, max(0, bob + 4))

        # Ground shadow
        shw = pygame.Surface((PLAYER_R*3, PLAYER_R*2), pygame.SRCALPHA)
        pygame.draw.ellipse(shw, (0,0,0,70), (0,0,PLAYER_R*3, PLAYER_R*2))
        surf.blit(shw, (sx - PLAYER_R*3//2, sy - PLAYER_R))

        # Legs (two small ellipses)
        lleg_off = int(PLAYER_R * 0.4)
        leg_h    = int(PLAYER_R * 0.55)
        for sign in (-1, 1):
            phase = self.anim_t + (0 if sign == -1 else math.pi)
            lbob  = math.sin(phase) * 4 if moving else 0
            lx = bsx + int(self.fdx * leg_h) + int(self.fdy * sign * lleg_off)
            ly = bsy + int(self.fdy * leg_h) - int(self.fdx * sign * lleg_off) + int(lbob) + PLAYER_R - 2
            pygame.draw.circle(surf, dark_col, (lx, ly), int(PLAYER_R * 0.45))

        # Torso (main body ellipse — wider than tall in iso)
        tw = int(PLAYER_R * 1.55)
        th = int(PLAYER_R * 1.9)
        torso_rect = (bsx - tw, bsy - th, tw*2, th)
        pygame.draw.ellipse(surf, body_col, torso_rect)
        pygame.draw.ellipse(surf, dark_col, torso_rect, 2)

        # Head
        hrad = int(PLAYER_R * 0.7)
        head_y = bsy - th
        pygame.draw.circle(surf, (240, 200, 160), (bsx, head_y), hrad)
        pygame.draw.circle(surf, (180, 140, 100), (bsx, head_y), hrad, 1)

        # Jersey number on torso
        ns = font_small.render(str(self.num), True, C_WHITE)
        surf.blit(ns, (bsx - ns.get_width()//2, bsy - th + 3))

        # Selection ring
        if self.selected:
            t = pygame.time.get_ticks()
            pulse = int(3 + 2*math.sin(t * 0.006))
            pygame.draw.ellipse(surf, C_LIME,
                (sx - PLAYER_R - pulse, sy - (PLAYER_R+pulse)//2,
                 (PLAYER_R+pulse)*2, PLAYER_R+pulse), 2)

        # Ball possession ring
        if has_ball:
            pygame.draw.ellipse(surf, C_YELLOW,
                (sx - PLAYER_R - 5, sy - (PLAYER_R+5)//2,
                 (PLAYER_R+5)*2, PLAYER_R+5), 2)

# ─────────────────────────────────────────────────────────────────────────────
#  GAME
# ─────────────────────────────────────────────────────────────────────────────
class FootballGame:
    def __init__(self):
        pygame.init()
        self.screen  = pygame.display.set_mode((SCR_W, SCR_H))
        pygame.display.set_caption("Football 3D — 11 vs 11")
        self.clock   = pygame.time.Clock()

        self.font_hud   = pygame.font.SysFont("Arial", 13, bold=True)
        self.font_big   = pygame.font.SysFont("Georgia", 38, bold=True)
        self.font_med   = pygame.font.SysFont("Georgia", 24, bold=True)
        self.font_num   = pygame.font.SysFont("Arial", 9,  bold=True)

        self.score      = [0, 0]
        self.match_time = 0
        self.messages   = []   # [text, color, ttl]

        self.dead_ball       = None
        self.dead_ball_pos   = (W_MX, W_MY)
        self.dead_ball_timer = 0

        # Shoot charge
        self.charging        = False
        self.charge          = 0.0

        self.ball = Ball()
        self._build_teams()
        self._kickoff('A')

        # Pre-build pitch surface once
        self.pitch_surf = pygame.Surface((SCR_W, SCR_H), pygame.SRCALPHA)
        self._bake_pitch(self.pitch_surf)

    # ── Team setup ────────────────────────────────────────────────────────────
    def _build_teams(self):
        self.team_a, self.team_b = [], []
        for i, (rx, ry) in enumerate(FORM):
            hx_a = rx * W_W * 0.47
            hx_b = W_W - rx * W_W * 0.47
            hy   = ry * W_H
            self.team_a.append(Player('A', i+1, hx_a, hy, is_keeper=(i==0)))
            self.team_b.append(Player('B', i+1, hx_b, hy, is_keeper=(i==0)))
        self.sel = self.team_a[9]
        self.sel.selected = True

    def _kickoff(self, kicking):
        self.dead_ball = None
        self.charging  = False
        self.charge    = 0.0
        self.ball.reset()
        for p in self.team_a + self.team_b:
            p.wx, p.wy = p.home_x, p.home_y
            p.vx = p.vy = 0.0
        kicker = self.team_a[9] if kicking == 'A' else self.team_b[9]
        kicker.wx = float(W_MX - (10 if kicking == 'A' else -10))
        kicker.wy = float(W_MY)
        self.ball.owner = kicker
        self.ball.last_toucher = kicker

    def add_msg(self, text, col=C_WHITE):
        self.messages.append([text, col, 210])

    # ── Pitch baking ─────────────────────────────────────────────────────────
    def _bake_pitch(self, surf):
        surf.fill((0, 0, 0, 0))

        # ── Sky gradient  (background, not part of pitch polygon)
        for row in range(SCR_H // 2):
            t = row / (SCR_H // 2)
            r = int(C_SKY[0] * (1-t) + 60*t)
            g = int(C_SKY[1] * (1-t) + 80*t)
            b = int(C_SKY[2] * (1-t) + 120*t)
            pygame.draw.line(surf, (r,g,b), (0, row), (SCR_W, row))

        # Pitch polygon corners in world coords
        corners_w = [(0,0),(W_W,0),(W_W,W_H),(0,W_H)]
        corners_s = [w2s(wx, wy) for wx, wy in corners_w]

        # Draw grass stripes (10 along x)
        stripe_n = 10
        step = W_W / stripe_n
        for i in range(stripe_n):
            x0, x1 = i*step, (i+1)*step
            quad = [w2s(x0,0), w2s(x1,0), w2s(x1,W_H), w2s(x0,W_H)]
            col = C_GRASS_D if i%2==0 else C_GRASS_L
            pygame.draw.polygon(surf, col, quad)

        # Outer boundary
        pygame.draw.polygon(surf, C_LINE, corners_s, 2)

        # Halfway line
        pygame.draw.line(surf, C_LINE, w2s(W_MX,0), w2s(W_MX,W_H), 2)

        # Centre circle (approximate with polyline)
        cr = 70
        pts = [w2s(W_MX + cr*math.cos(a), W_MY + cr*math.sin(a))
               for a in [i*math.pi/18 for i in range(37)]]
        pygame.draw.lines(surf, C_LINE, False, pts, 2)
        pygame.draw.circle(surf, C_LINE, w2s(W_MX, W_MY), 4)

        # Penalty areas
        pa_w, pa_h = 130, 280
        for side_x, sign in [(0, 1), (W_W, -1)]:
            x0 = side_x
            x1 = side_x + sign * pa_w
            y0 = W_MY - pa_h//2
            y1 = W_MY + pa_h//2
            box = [w2s(x0,y0), w2s(x1,y0), w2s(x1,y1), w2s(x0,y1)]
            pygame.draw.lines(surf, C_LINE, True, box, 2)
            # Penalty spot
            pygame.draw.circle(surf, C_LINE, w2s(side_x + sign*85, W_MY), 4)

        # 6-yard boxes
        sb_w, sb_h = 42, 130
        for side_x, sign in [(0, 1), (W_W, -1)]:
            x0 = side_x
            x1 = side_x + sign * sb_w
            y0 = W_MY - sb_h//2
            y1 = W_MY + sb_h//2
            box = [w2s(x0,y0), w2s(x1,y0), w2s(x1,y1), w2s(x0,y1)]
            pygame.draw.lines(surf, C_LINE, True, box, 2)

        # Corner arcs
        for cx, cy in [(0,0),(W_W,0),(0,W_H),(W_W,W_H)]:
            arc_pts = []
            for a_deg in range(0, 91, 5):
                a = math.radians(a_deg)
                sign_x = 1 if cx == 0 else -1
                sign_y = 1 if cy == 0 else -1
                arc_pts.append(w2s(cx + sign_x*10*math.cos(a),
                                   cy + sign_y*10*math.sin(a)))
            if len(arc_pts) > 1:
                pygame.draw.lines(surf, C_LINE, False, arc_pts, 2)

        # Goals (3-D box)
        gd = 26    # depth in world units
        gh = 55    # height in world units (screen z)

        for side_x, sign in [(0, -1), (W_W, 1)]:
            # Posts
            for gy in [GOAL_TOP, GOAL_BOT]:
                base  = w2s(side_x, gy)
                back  = w2s(side_x + sign*gd, gy)
                top_f = w2s(side_x, gy, gh)
                top_b = w2s(side_x + sign*gd, gy, gh)
                pygame.draw.line(surf, C_WHITE, base,  top_f,  3)
                pygame.draw.line(surf, C_WHITE, top_f, top_b,  2)
                pygame.draw.line(surf, C_WHITE, back,  top_b,  2)

            # Crossbar
            tl = w2s(side_x, GOAL_TOP, gh)
            tr = w2s(side_x, GOAL_BOT, gh)
            pygame.draw.line(surf, C_WHITE, tl, tr, 3)

            # Net lines (vertical)
            net_col = (180, 180, 180, 100)
            net_n   = 6
            for ni in range(net_n+1):
                t = ni / net_n
                gy = GOAL_TOP + t*(GOAL_BOT-GOAL_TOP)
                pygame.draw.line(surf, C_NET,
                    w2s(side_x, gy),
                    w2s(side_x + sign*gd, gy), 1)
                pygame.draw.line(surf, C_NET,
                    w2s(side_x, gy),
                    w2s(side_x, gy, gh), 1)

    # ── Drawing ───────────────────────────────────────────────────────────────
    def draw_scene(self):
        self.screen.blit(self.pitch_surf, (0, 0))

        # Collect all drawables sorted by world_y (painter's order)
        drawables = []
        for p in self.team_a + self.team_b:
            drawables.append((p.wy, 'player', p))
        drawables.append((self.ball.wy, 'ball', self.ball))
        drawables.sort(key=lambda d: d[0])

        for _, kind, obj in drawables:
            if kind == 'player':
                obj.draw(self.screen, self.ball, self.font_num)
            else:
                obj.draw(self.screen)

        # Pass suggestion lines
        if self.ball.owner and self.ball.owner.team == 'A' and not self.dead_ball:
            self._draw_pass_lines()

    def _draw_pass_lines(self):
        carrier = self.ball.owner
        mates = [p for p in self.team_a if p is not carrier]
        if not mates:
            return
        best = self._best_pass_target(carrier)
        if best:
            bsx, bsy = w2s(carrier.wx, carrier.wy, 8)
            tsx, tsy = w2s(best.wx, best.wy, 8)
            # Dashed line
            dx = tsx - bsx; dy = tsy - bsy
            segs = max(4, int(math.hypot(dx,dy)//20))
            for i in range(segs):
                if i % 2 == 0:
                    t0, t1 = i/segs, (i+0.5)/segs
                    x0,y0 = int(bsx+dx*t0), int(bsy+dy*t0)
                    x1,y1 = int(bsx+dx*t1), int(bsy+dy*t1)
                    pygame.draw.line(self.screen, C_PASS_LINE, (x0,y0),(x1,y1), 2)

    def draw_hud(self):
        s = self.screen
        # Score board
        mins = self.match_time // (FPS*60)
        secs = (self.match_time // FPS) % 60
        bw = 310
        bx = SCR_W//2 - bw//2
        pygame.draw.rect(s, (8,8,8),   (bx,4,bw,44), border_radius=10)
        pygame.draw.rect(s, (70,70,70),(bx,4,bw,44), 2, border_radius=10)
        sc = self.font_big.render(f"  {self.score[0]}  :  {self.score[1]}  ", True, C_WHITE)
        s.blit(sc, (SCR_W//2 - sc.get_width()//2, 5))
        tc = self.font_hud.render(f"{mins:02d}:{secs:02d}", True, C_GRAY)
        s.blit(tc, (SCR_W//2 - tc.get_width()//2, 48))

        # Team labels
        ta = self.font_hud.render("YOU (Blue)", True, (120, 180, 255))
        tb = self.font_hud.render("CPU (Red)",  True, (255, 120, 120))
        s.blit(ta, (20, 10))
        s.blit(tb, (SCR_W - tb.get_width() - 20, 10))

        # Controls
        ctrl = [
            ("WASD/↑↓←→", "Move"),
            ("Z",          "Sprint"),
            ("SPACE",      "Pass"),
            ("F/Shift",    "Shoot (hold=power)"),
            ("X",          "Tackle"),
            ("TAB",        "Switch player"),
        ]
        panel_x, panel_y = 10, SCR_H - 130
        pygame.draw.rect(s,(0,0,0),(panel_x-4, panel_y-4, 220, 125), border_radius=6)
        pygame.draw.rect(s,(50,50,50),(panel_x-4, panel_y-4, 220, 125), 1, border_radius=6)
        for i,(key,desc) in enumerate(ctrl):
            ks = self.font_hud.render(key, True, C_YELLOW)
            ds = self.font_hud.render(desc, True, C_GRAY)
            s.blit(ks, (panel_x, panel_y + i*18))
            s.blit(ds, (panel_x + 85, panel_y + i*18))

        # Shoot power bar
        if self.charging:
            bw2 = 200
            bh  = 18
            bx2 = SCR_W//2 - bw2//2
            by2 = SCR_H - 60
            pygame.draw.rect(s,(30,30,30),(bx2-2,by2-2,bw2+4,bh+4),border_radius=5)
            fill = int(bw2 * self.charge)
            col  = (int(255*self.charge), int(200*(1-self.charge)), 0)
            pygame.draw.rect(s, col, (bx2, by2, fill, bh), border_radius=4)
            pygame.draw.rect(s, C_WHITE, (bx2-2,by2-2,bw2+4,bh+4), 1, border_radius=5)
            label = self.font_hud.render("SHOOT POWER", True, C_WHITE)
            s.blit(label, (SCR_W//2-label.get_width()//2, by2-20))

        # Dead-ball banner
        if self.dead_ball:
            labels = {
                'throw_in_A':'THROW-IN → YOU','throw_in_B':'THROW-IN → CPU',
                'goal_kick_A':'GOAL KICK → YOU','goal_kick_B':'GOAL KICK → CPU',
                'corner_A':'CORNER → YOU','corner_B':'CORNER → CPU',
                'kickoff_A':'KICK OFF → YOU','kickoff_B':'KICK OFF → CPU',
            }
            lbl = labels.get(self.dead_ball,'')
            ds  = self.font_med.render(lbl, True, C_YELLOW)
            bx3 = SCR_W//2-ds.get_width()//2
            pygame.draw.rect(s,(0,0,0),(bx3-12,SCR_H-62,ds.get_width()+24,34),border_radius=7)
            s.blit(ds,(bx3, SCR_H-58))
            cntd = max(0, self.dead_ball_timer//FPS + 1)
            ts   = self.font_hud.render(f"Resuming in {cntd}s…", True, C_GRAY)
            s.blit(ts,(SCR_W//2-ts.get_width()//2, SCR_H-28))

        # Messages
        for i,msg in enumerate(self.messages):
            ms = self.font_med.render(msg[0], True, msg[1])
            ms.set_alpha(min(255, msg[2]*3))
            s.blit(ms,(SCR_W//2-ms.get_width()//2, SCR_H//2-80+i*38))

        # Ball possession
        if self.ball.owner:
            side = "YOU" if self.ball.owner.team=='A' else "CPU"
            col  = (120,180,255) if self.ball.owner.team=='A' else (255,120,120)
            ps = self.font_hud.render(f"Ball: {side} #{self.ball.owner.num}", True, col)
            s.blit(ps,(SCR_W//2-ps.get_width()//2, 66))

    # ── Pass logic ────────────────────────────────────────────────────────────
    def _best_pass_target(self, carrier):
        """Find best pass target: forward, open, in space."""
        mates = [p for p in self.team_a if p is not carrier and not p.is_keeper]
        if not mates:
            return None

        carrier_attacking = carrier.wx  # higher = more forward for team A

        scored = []
        for p in mates:
            d = dist2((carrier.wx,carrier.wy),(p.wx,p.wy))
            # Prefer players ahead of ball carrier
            forward_bonus = (p.wx - carrier.wx) * 0.8
            # Penalise if opponent is close to recipient
            opp_dist = min(dist2((q.wx,q.wy),(p.wx,p.wy)) for q in self.team_b)
            if opp_dist < 30:
                continue   # skip marked players
            score = forward_bonus + opp_dist * 0.3 - d * 0.1
            scored.append((score, p))

        if not scored:
            # Fallback: nearest
            return min(mates, key=lambda p: dist2((carrier.wx,carrier.wy),(p.wx,p.wy)))

        scored.sort(key=lambda x: -x[0])
        return scored[0][1]

    # ── Human input ───────────────────────────────────────────────────────────
    def handle_input(self):
        if self.dead_ball:
            return
        keys  = pygame.key.get_pressed()
        spd   = PLAYER_SPD * (SPRINT_MULT if keys[pygame.K_z] else 1.0)
        p     = self.sel

        dx, dy = 0.0, 0.0
        if keys[pygame.K_LEFT]  or keys[pygame.K_a]: dx -= 1
        if keys[pygame.K_RIGHT] or keys[pygame.K_d]: dx += 1
        if keys[pygame.K_UP]    or keys[pygame.K_w]: dy -= 1
        if keys[pygame.K_DOWN]  or keys[pygame.K_s]: dy += 1

        if dx or dy:
            nx, ny = norm2(dx, dy)
            p.vx, p.vy = nx*spd, ny*spd
            p.fdx, p.fdy = nx, ny
            p.wx += p.vx
            p.wy += p.vy
            p.wx, p.wy = world_clamp(p.wx, p.wy)
        else:
            p.vx *= 0.6
            p.vy *= 0.6

        # Shoot charge
        if keys[pygame.K_f] or keys[pygame.K_LSHIFT] or keys[pygame.K_RSHIFT]:
            if self.ball.owner and self.ball.owner.team == 'A':
                self.charging = True
                self.charge   = min(1.0, self.charge + 0.025)
        else:
            if self.charging and self.ball.owner and self.ball.owner.team == 'A':
                self._human_shoot(self.charge)
            self.charging = False
            self.charge   = 0.0

        # Auto-collect loose ball
        if self.ball.owner is None and self.ball.wz < 8:
            if dist2((p.wx,p.wy),(self.ball.wx,self.ball.wy)) < CONTROL_R:
                self.ball.owner = p
                self.ball.last_toucher = p

        # Tackle cooldown
        if p.tackle_cd > 0:
            p.tackle_cd -= 1

    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit(); sys.exit()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    pygame.quit(); sys.exit()

                if event.key == pygame.K_TAB:
                    self._switch_player()

                if event.key == pygame.K_SPACE and not self.dead_ball:
                    if self.ball.owner and self.ball.owner.team == 'A':
                        self._human_pass()

                # Tackle
                if event.key == pygame.K_x and not self.dead_ball:
                    self._human_tackle()

    def _switch_player(self):
        self.sel.selected = False
        if self.ball.owner and self.ball.owner.team == 'A':
            self.sel = self.ball.owner
        else:
            cands = [p for p in self.team_a if not p.is_keeper]
            cands.sort(key=lambda p: dist2((p.wx,p.wy),(self.ball.wx,self.ball.wy)))
            idx = cands.index(self.sel) if self.sel in cands else -1
            self.sel = cands[(idx+1)%len(cands)]
        self.sel.selected = True

    def _human_pass(self):
        carrier = self.ball.owner
        target  = self._best_pass_target(carrier)
        if not target:
            return
        self.ball.last_toucher = carrier
        self.ball.pass_to(target.wx, target.wy)
        self.sel.selected = False
        self.sel = target
        self.sel.selected = True

    def _human_shoot(self, power):
        carrier = self.ball.owner
        if not carrier:
            return
        # Right goal = x=W_W side, aim at best spot
        gx = float(W_W)
        gy = clamp(carrier.wy, GOAL_TOP+15, GOAL_BOT-15) + random.randint(-15,15)
        inac = clamp((1.0 - power)*0.35, 0, 0.3)
        bx, by = norm2(gx - carrier.wx, gy - carrier.wy)
        bx += random.uniform(-inac, inac)
        by += random.uniform(-inac, inac)
        bx, by = norm2(bx, by)
        spd = SHOOT_SPD * (SHOOT_POWER_MIN + power * (SHOOT_POWER_MAX - SHOOT_POWER_MIN))
        self.ball.release()
        self.ball.vx = bx * spd
        self.ball.vy = by * spd
        self.ball.vz = 5.0 + power * 4.0
        self.ball.last_toucher = carrier

    def _human_tackle(self):
        p = self.sel
        if p.tackle_cd > 0:
            return
        # Find nearest opponent with the ball, or near ball
        targets = [q for q in self.team_b if not q.is_keeper]
        for t in targets:
            if dist2((p.wx,p.wy),(t.wx,t.wy)) < TACKLE_R + 8:
                if self.ball.owner is t:
                    # Tackle the ball
                    success = random.random() < 0.62
                    if success:
                        self.ball.release()
                        bx, by = norm2(p.wx-t.wx, p.wy-t.wy)
                        self.ball.vx = bx*4 + random.uniform(-1.5,1.5)
                        self.ball.vy = by*4 + random.uniform(-1.5,1.5)
                        self.ball.last_toucher = p
                        self.add_msg("TACKLE! Ball won!", C_LIME)
                    else:
                        self.add_msg("Tackle missed!", (255,180,80))
                    p.tackle_cd = 45
                    return

    # ── Team A attack support AI ──────────────────────────────────────────────
    def update_team_a_ai(self):
        """When a human player has the ball, teammates make intelligent runs."""
        carrier = self.ball.owner
        if not (carrier and carrier.team == 'A'):
            return

        for p in self.team_a:
            if p is carrier or p is self.sel:
                continue
            if p.is_keeper:
                # Keeper stays back, tracks ball height
                gkx = clamp(carrier.wx*0.15, 15, 80)
                gky = clamp(carrier.wy, GOAL_TOP+20, GOAL_BOT-20)
                p.move_toward(gkx, gky, AI_WALK*0.9)
                continue

            # Role index: 1-4 = defenders, 5-7 = midfielders, 8-10 = forwards
            role = p.num - 1   # 1..10
            if role <= 4:
                # Defenders: push up slightly but stay behind ball
                safe_x = min(carrier.wx - 60, p.home_x + 40)
                safe_x = max(safe_x, p.home_x - 20)
                ty = p.home_y + (carrier.wy - W_MY) * 0.15
                p.move_toward(safe_x, ty, AI_WALK)
            elif role <= 7:
                # Midfielders: spread wide, offer triangle passes
                angle = math.radians((role - 6) * 60)
                offset_x = math.cos(angle) * 80
                offset_y = math.sin(angle) * 90
                tx = clamp(carrier.wx + offset_x, 50, W_W-50)
                ty = clamp(carrier.wy + offset_y, 20, W_H-20)
                p.move_toward(tx, ty, AI_JOG*0.85)
            else:
                # Forwards: make forward runs into channels
                channel_y = GOAL_TOP + 20 if p.num == 9 else \
                            (GOAL_TOP - 25 if p.num == 8 else GOAL_BOT + 25)
                tx = clamp(carrier.wx + 90 + (p.num-9)*20, carrier.wx+30, W_W-30)
                ty = clamp(channel_y, 20, W_H-20)
                p.move_toward(tx, ty, AI_JOG)

    # ── Keeper AI ─────────────────────────────────────────────────────────────
    def _update_keeper(self, keeper, goal_x, is_left):
        ball = self.ball

        # Is ball heading toward our goal?
        ball_coming = False
        if ball.owner is None and ball.spd() > 1.0:
            future_x = ball.wx + ball.vx * 25
            ball_coming = (future_x < W_MX) if is_left else (future_x > W_MX)

        if ball_coming and abs(ball.vx) > 0.2:
            t = (goal_x - ball.wx) / ball.vx
            if 0 < t < 60:
                iy = clamp(ball.wy + ball.vy*t, GOAL_TOP+5, GOAL_BOT-5)
                # Move out slightly to intercept
                out = 35 if is_left else -35
                keeper.move_toward(goal_x + out, iy, AI_JOG * 1.4)
                return

        # Keeper: stay near goal line, gentle lateral tracking only
        ky = clamp(ball.wy, GOAL_TOP+20, GOAL_BOT-20)
        # Only come off line if ball is in their half
        in_half = (ball.wx < W_MX) if is_left else (ball.wx > W_MX)
        if is_left:
            kx = GOAL_TOP*0 + 28   # fixed x near left goal
            # Small come-out
            if in_half:
                kx = clamp(ball.wx*0.12 + 20, 20, 80)
        else:
            kx = W_W - 28
            if in_half:
                kx = clamp(W_W - ball.wx*0.12 - 20, W_W-80, W_W-20)

        keeper.move_toward(kx, ky, AI_WALK * 0.95)

    # ── CPU AI ────────────────────────────────────────────────────────────────
    def update_ai(self):
        if self.dead_ball:
            return

        ball = self.ball

        # Team A keeper
        self._update_keeper(self.team_a[0], 0, is_left=True)
        # Team B keeper
        self._update_keeper(self.team_b[0], W_W, is_left=False)

        outfield_b = self.team_b[1:]
        ball_b = ball.owner and ball.owner.team == 'B'
        ball_a = ball.owner and ball.owner.team == 'A'

        closest_b = min(outfield_b, key=lambda p: dist2((p.wx,p.wy),(ball.wx,ball.wy)))

        for p in outfield_b:
            if p.tackle_cd > 0:
                p.tackle_cd -= 1

            if p.react > 0:
                p.react -= 1
                p.move_toward(p.home_x, p.home_y, AI_WALK*0.8)
                continue

            if ball_b and ball.owner is p:
                self._cpu_carry(p)

            elif ball.owner is None:
                d = dist2((p.wx,p.wy),(ball.wx,ball.wy))
                if d < AI_PRESS * 1.4:
                    p.move_toward(ball.wx, ball.wy, AI_JOG)
                else:
                    p.move_toward(p.home_x, p.home_y, AI_WALK)
                if ball.wz < 12 and d < CONTROL_R:
                    ball.owner = p
                    ball.last_toucher = p
                    for q in outfield_b:
                        q.react = random.randint(8, AI_REACT//2)

            elif ball_a:
                if p is closest_b:
                    d = dist2((p.wx,p.wy),(ball.wx,ball.wy))
                    if d < AI_PRESS:
                        p.move_toward(ball.wx, ball.wy, AI_JOG)
                        # CPU tackle attempt
                        if d < TACKLE_R and p.tackle_cd == 0 and random.random() < AI_TACKLE:
                            if ball.owner:
                                ball.release()
                                bx,by = norm2(p.wx-ball.owner.wx, p.wy-ball.owner.wy)
                                ball.vx = bx*3+random.uniform(-1,1)
                                ball.vy = by*3+random.uniform(-1,1)
                                ball.last_toucher = p
                                p.tackle_cd = 50
                    else:
                        mx = (p.home_x+ball.wx)/2
                        my = (p.home_y+ball.wy)/2
                        p.move_toward(mx, my, AI_WALK)
                else:
                    # Hold shape
                    tx = max(p.home_x, W_W - W_W*0.55)
                    ty = p.home_y + (ball.wy-W_MY)*0.18
                    p.move_toward(tx, ty, AI_WALK*0.85)

    def _cpu_carry(self, p):
        ball   = self.ball
        goal_x = 0.0
        goal_y = float(W_MY)
        d_g    = dist2((p.wx,p.wy),(goal_x,goal_y))
        pres   = [q for q in self.team_a if dist2((q.wx,q.wy),(p.wx,p.wy)) < 60]

        # Shoot
        if d_g < AI_SHOOT_R and random.random() < 0.024:
            gy = clamp(p.wy, GOAL_TOP+12, GOAL_BOT-12) + random.randint(-22,22)
            bx,by = norm2(goal_x-p.wx, gy-p.wy)
            inac = clamp(d_g/1800, 0.06, 0.26)
            bx += random.uniform(-inac,inac); by += random.uniform(-inac,inac)
            bx,by = norm2(bx,by)
            ball.release()
            ball.vx = bx*SHOOT_SPD*0.84
            ball.vy = by*SHOOT_SPD*0.84
            ball.vz = 4.0
            ball.last_toucher = p
            for q in self.team_b[1:]:
                q.react = random.randint(15,35)
            return

        # Pass under pressure
        if pres and random.random() < 0.02:
            mates = [q for q in self.team_b if q is not p and not q.is_keeper]
            if mates:
                tgt = min(mates, key=lambda q: q.wx+random.uniform(-25,25))
                ball.pass_to(tgt.wx, tgt.wy)
                ball.last_toucher = p
                for q in self.team_b[1:]:
                    q.react = random.randint(8,22)
                return

        # Dribble
        dodge = 0.0
        if pres:
            avg = sum(q.wy for q in pres)/len(pres)
            dodge = 28 if p.wy < avg else -28
        p.move_toward(goal_x+55, goal_y+dodge, AI_RUN)

    # ── Physics / events ─────────────────────────────────────────────────────
    def check_goals(self):
        if self.dead_ball:
            return
        b = self.ball
        if b.wz > 20:
            return   # too high

        # Left goal (B scores)
        if b.wx <= -BALL_R and GOAL_TOP <= b.wy <= GOAL_BOT:
            self.score[1] += 1
            self.add_msg("⚽  GOAL! — CPU scores!", (255,100,100))
            self._start_dead('kickoff_A', None); return

        # Right goal (A scores)
        if b.wx >= W_W + BALL_R and GOAL_TOP <= b.wy <= GOAL_BOT:
            self.score[0] += 1
            self.add_msg("⚽  GOAL! — YOU score!", C_LIME)
            self._start_dead('kickoff_B', None); return

    def check_out(self):
        if self.dead_ball or self.ball.owner:
            return
        b    = self.ball
        last = b.last_toucher

        # Top/Bottom
        if b.wy < -BALL_R or b.wy > W_H + BALL_R:
            kind = 'throw_in_B' if last and last.team=='A' else 'throw_in_A'
            tx = clamp(b.wx, 30, W_W-30)
            ty = 8 if b.wy < 0 else W_H-8
            self._start_dead(kind, (tx,ty)); return

        # Left byline (not goal)
        if b.wx < -BALL_R and not (GOAL_TOP<=b.wy<=GOAL_BOT):
            if last and last.team=='A':
                pos=(30, clamp(b.wy,30,W_H-30)); self._start_dead('goal_kick_B',pos)
            else:
                cy=8 if b.wy<W_MY else W_H-8; self._start_dead('corner_A',(8,cy))
            return

        # Right byline (not goal)
        if b.wx > W_W+BALL_R and not (GOAL_TOP<=b.wy<=GOAL_BOT):
            if last and last.team=='B':
                pos=(W_W-30, clamp(b.wy,30,W_H-30)); self._start_dead('goal_kick_A',pos)
            else:
                cy=8 if b.wy<W_MY else W_H-8; self._start_dead('corner_B',(W_W-8,cy))

    def _start_dead(self, kind, pos):
        self.ball.owner = None
        self.ball.vx = self.ball.vy = self.ball.vz = 0.0
        self.dead_ball = kind
        if pos:
            self.dead_ball_pos = pos
            self.ball.wx, self.ball.wy = float(pos[0]), float(pos[1])
        else:
            self.dead_ball_pos = (float(W_MX), float(W_MY))
            self.ball.wx, self.ball.wy = float(W_MX), float(W_MY)
        self.ball.wz = 0.0
        self.dead_ball_timer = FPS * 2

    def update_dead(self):
        if not self.dead_ball:
            return
        self.dead_ball_timer -= 1
        if self.dead_ball_timer > 0:
            return
        kind = self.dead_ball
        bx, by = self.dead_ball_pos
        if kind in ('kickoff_A','kickoff_B'):
            self._kickoff('A' if 'A' in kind else 'B'); return
        team = self.team_a if kind.endswith('_A') else self.team_b
        nearest = min(team, key=lambda p: dist2((p.wx,p.wy),(bx,by)))
        nearest.wx, nearest.wy = float(bx), float(by)
        self.ball.wx, self.ball.wy, self.ball.wz = float(bx), float(by), 0.0
        self.ball.owner = nearest
        self.ball.last_toucher = nearest
        self.dead_ball = None

    # ── Main loop ─────────────────────────────────────────────────────────────
    def run(self):
        while True:
            self.clock.tick(FPS)
            self.match_time += 1

            self.handle_events()
            self.handle_input()

            if not self.dead_ball:
                self.update_ai()
                self.update_team_a_ai()
                self.ball.update()
                self.check_goals()
                self.check_out()

                # AI auto-collect
                if self.ball.owner is None and self.ball.wz < 10:
                    for p in self.team_a + self.team_b:
                        if dist2((p.wx,p.wy),(self.ball.wx,self.ball.wy)) < CONTROL_R:
                            self.ball.owner = p
                            self.ball.last_toucher = p
                            if p.team=='B':
                                for q in self.team_b[1:]:
                                    q.react = random.randint(8,28)
                            break
            else:
                self.update_dead()

            self.messages = [[t,c,n-1] for t,c,n in self.messages if n>0]

            self.draw_scene()
            self.draw_hud()
            pygame.display.flip()


if __name__ == "__main__":
    game = FootballGame()
    game.run()