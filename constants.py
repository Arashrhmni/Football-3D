"""constants.py – shared world settings, colours, formation."""
import math

# ── World dimensions ─────────────────────────────────────────────
W_W, W_H   = 1260, 810
W_MX, W_MY = W_W // 2, W_H // 2

GOAL_W       = 145
GOAL_TOP     = W_MY - GOAL_W // 2
GOAL_BOT     = W_MY + GOAL_W // 2
GOAL_DEPTH_W = 40
GOAL_H_Z     = 78

PA_W, PA_H = 190, 400   # penalty area
SB_W, SB_H =  62, 180   # six-yard box
CTR_R       =  92        # centre circle radius
OUT_L = OUT_R = OUT_T = OUT_B = 90   # run-off border

# ── Screen ───────────────────────────────────────────────────────
SCR_W, SCR_H = 1280, 800
FPS = 60

# ── Match timing ─────────────────────────────────────────────────
# 3 real minutes per half → 6 real minutes total = 90 game-minutes
REAL_SECS_PER_HALF    = 180                          # 3 min real time
HALF_FRAMES           = REAL_SECS_PER_HALF * FPS     # frames per half
MATCH_FRAMES          = HALF_FRAMES * 2              # total frames

# ── Isometric projection ─────────────────────────────────────────
# Standard dimetric (cabinet) projection:
#   screen_x = (world_x - world_y) * cos30 * scale  +  cx
#   screen_y = (world_x + world_y) * sin30 * scale  -  wz * vz_scale  +  cy
# Using the SAME cos30 scale for both x and y world axes guarantees
# that equal-length edges in world space appear equal-length on screen
# and that the pitch boundary forms a proper parallelogram (not a skewed shape).
_SCALE  = 0.46
_COS30  = math.cos(math.radians(30)) * _SCALE   # ≈ 0.3985
_SIN30  = math.sin(math.radians(30)) * _SCALE   # ≈ 0.2300
ISO_CX  = SCR_W // 2
ISO_CY  = 490
ISO_VZ  = 1.10

def w2s(wx, wy, wz=0.0):
    sx = (wx - W_MX) * _COS30 - (wy - W_MY) * _COS30 + ISO_CX
    sy = (wx - W_MX) * _SIN30 + (wy - W_MY) * _SIN30 - wz * ISO_VZ + ISO_CY
    return int(sx), int(sy)

# ── Physics ──────────────────────────────────────────────────────
PLAYER_R    = 14
BALL_R      = 7
PLAYER_SPD  = 3.6
SPRINT_MULT = 1.62
BALL_FRIC   = 0.978
BALL_GRAV   = 0.52
PASS_SPD    = 11.0
CROSS_SPD   = 13.0
SHOOT_SPD   = 19.0
THROUGH_PASS_SPD = 13.4
CONTROL_R   = 21
TACKLE_R    = 26

# ── Stamina ──────────────────────────────────────────────────────
STAMINA_DRAIN = 0.0095
STAMINA_REGEN = 0.0048

# ── AI ───────────────────────────────────────────────────────────
AI_WALK  = 1.9
AI_JOG   = 2.75
AI_RUN   = 3.55
AI_REACT = 44

# ── Dead-ball state labels ────────────────────────────────────────
DB_THROW_A  = 'throw_in_A'
DB_THROW_B  = 'throw_in_B'
DB_GK_A     = 'goal_kick_A'
DB_GK_B     = 'goal_kick_B'
DB_CORNER_A = 'corner_A'
DB_CORNER_B = 'corner_B'
DB_KICK_A   = 'kickoff_A'
DB_KICK_B   = 'kickoff_B'

DB_LABELS = {
    DB_THROW_A:  "THROW-IN → BARCELONA",
    DB_THROW_B:  "THROW-IN → REAL MADRID",
    DB_GK_A:     "GOAL KICK → BARCELONA",
    DB_GK_B:     "GOAL KICK → REAL MADRID",
    DB_CORNER_A: "CORNER → BARCELONA",
    DB_CORNER_B: "CORNER → REAL MADRID",
    DB_KICK_A:   "KICK OFF → BARCELONA",
    DB_KICK_B:   "KICK OFF → REAL MADRID",
}

# ── Kit colours ──────────────────────────────────────────────────
BAR_BLUE   = (0,  82, 170)
BAR_RED    = (165, 17,  17)
BAR_SHORTS = (0,  82, 170)
BAR_SOCKS  = (0,  82, 170)
RMA_SHIRT  = (238,238,238)
RMA_GOLD   = (198,162,  0)
RMA_SHORTS = (215,215,215)
RMA_SOCKS  = (215,215,215)
GK_A       = (255,140,  0)
GK_B       = ( 40,160, 60)
SKIN_A     = (222,182,142)
HAIR_A     = ( 38, 28, 18)
SKIN_B     = (212,176,136)
HAIR_B     = ( 58, 44, 20)

# Bayern Munich
BAY_RED    = (220,  16,  28)
BAY_WHITE  = (255, 255, 255)
BAY_SHORTS = (220,  16,  28)
BAY_SOCKS  = (220,  16,  28)

# Manchester City
MCI_BLUE   = ( 97, 195, 238)
MCI_WHITE  = (255, 255, 255)
MCI_SHORTS = ( 97, 195, 238)
MCI_SOCKS  = ( 97, 195, 238)

# ── Team registry ─────────────────────────────────────────────────
# Each entry carries display info (for the menu) and kit colours (for player.py).
TEAMS = {
    'barcelona': {
        'name':    'Barcelona',
        'country': 'Spain',
        'shirt1':  BAR_BLUE,
        'shirt2':  BAR_RED,
        'shorts':  BAR_SHORTS,
        'socks':   BAR_SOCKS,
        'gk':      GK_A,
        'skin':    SKIN_A,
        'hair':    HAIR_A,
        'num_col': (255, 255, 255),
        'hud_col': BAR_BLUE,
        'stripe':  True,          # blaugrana vertical stripes
        'stripe_cols': [BAR_BLUE, BAR_RED, BAR_BLUE],
    },
    'real_madrid': {
        'name':    'Real Madrid',
        'country': 'Spain',
        'shirt1':  RMA_SHIRT,
        'shirt2':  RMA_SHIRT,
        'shorts':  RMA_SHORTS,
        'socks':   RMA_SOCKS,
        'gk':      GK_B,
        'skin':    SKIN_B,
        'hair':    HAIR_B,
        'num_col': (30, 30, 30),
        'hud_col': (215, 215, 215),
        'stripe':  False,
        'gold_border': True,      # white shirt with gold border
    },
    'bayern': {
        'name':    'Bayern Munich',
        'country': 'Germany',
        'shirt1':  BAY_RED,
        'shirt2':  BAY_RED,
        'shorts':  BAY_SHORTS,
        'socks':   BAY_SOCKS,
        'gk':      (255, 210, 0),
        'skin':    SKIN_A,
        'hair':    HAIR_A,
        'num_col': (255, 255, 255),
        'hud_col': BAY_RED,
        'stripe':  False,
    },
    'man_city': {
        'name':    'Man City',
        'country': 'England',
        'shirt1':  MCI_BLUE,
        'shirt2':  MCI_WHITE,
        'shorts':  MCI_SHORTS,
        'socks':   MCI_SOCKS,
        'gk':      (255, 140, 0),
        'skin':    SKIN_B,
        'hair':    (20, 14, 8),
        'num_col': (255, 255, 255),
        'hud_col': MCI_BLUE,
        'stripe':  False,
        'half_half': True,        # left-right split shirt
    },
}

# ── Formation 4-3-3 (rel x 0→1 from own goal, rel y 0→1 top→bot)
FORM = [
    (0.055, 0.50),   # 0  GK
    (0.22,  0.13),   # 1  LB
    (0.22,  0.37),   # 2  CB
    (0.22,  0.63),   # 3  CB
    (0.22,  0.87),   # 4  RB
    (0.46,  0.20),   # 5  LM
    (0.46,  0.50),   # 6  CM
    (0.46,  0.80),   # 7  RM
    (0.72,  0.15),   # 8  LW
    (0.72,  0.50),   # 9  ST
    (0.72,  0.85),   # 10 RW
]

# ── Helpers ──────────────────────────────────────────────────────
def d2(a, b):
    return math.hypot(a[0]-b[0], a[1]-b[1])

def n2(vx, vy):
    m = math.hypot(vx, vy)
    return (vx/m, vy/m) if m > 1e-9 else (0.0, 0.0)

def clamp(v, lo, hi):
    return max(lo, min(hi, v))

def lerpc(a, b, t):
    return tuple(int(a[i]+(b[i]-a[i])*t) for i in range(3))
