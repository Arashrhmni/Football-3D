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
REAL_SECS_PER_HALF    = 180
HALF_FRAMES           = REAL_SECS_PER_HALF * FPS
MATCH_FRAMES          = HALF_FRAMES * 2

# ── Isometric projection ─────────────────────────────────────────
_SCALE  = 0.46
_COS30  = math.cos(math.radians(30)) * _SCALE
_SIN30  = math.sin(math.radians(30)) * _SCALE
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

# DB_LABELS is now built dynamically in Game using team names.
# Kept here as empty fallback so old imports don't break.
DB_LABELS = {}

# ── Shared skin/hair tones ───────────────────────────────────────
SKIN_LIGHT  = (222, 182, 142)
HAIR_DARK   = ( 38,  28,  18)
SKIN_MED    = (212, 176, 136)
HAIR_MED    = ( 58,  44,  20)
SKIN_OLIVE  = (198, 160, 110)
HAIR_BLACK  = ( 20,  14,   8)

# Legacy aliases (used by player.py gold_border branch)
SKIN_A = SKIN_LIGHT
HAIR_A = HAIR_DARK
SKIN_B = SKIN_MED
HAIR_B = HAIR_MED
RMA_GOLD = (198, 162, 0)
BAR_BLUE = (0, 82, 170)   # kept for hud import compat

# ── Team registry ─────────────────────────────────────────────────
# 'name'    → fictional/portfolio-safe display name
# 'inspo'   → real-world inspiration (comment only, not displayed)
# Kit flags → stripe / half_half / gold_border / hoops / sash
TEAMS = {

    # ── Premier League ───────────────────────────────────────────
    'sky_blues': {
        'name':    'Sky Blues FC',          # inspo: Man City
        'country': 'England',
        'shirt1':  ( 97, 195, 238),
        'shirt2':  (255, 255, 255),
        'shorts':  ( 97, 195, 238),
        'socks':   ( 97, 195, 238),
        'gk':      (255, 140,   0),
        'skin':    SKIN_MED,
        'hair':    HAIR_BLACK,
        'num_col': (255, 255, 255),
        'hud_col': ( 97, 195, 238),
        'half_half': True,
    },

    # ── Bundesliga ───────────────────────────────────────────────
    'fc_rot': {
        'name':    'FC Rot München',        # inspo: Bayern Munich
        'country': 'Germany',
        'shirt1':  (220,  16,  28),
        'shirt2':  (220,  16,  28),
        'shorts':  (220,  16,  28),
        'socks':   (220,  16,  28),
        'gk':      (255, 210,   0),
        'skin':    SKIN_LIGHT,
        'hair':    HAIR_DARK,
        'num_col': (255, 255, 255),
        'hud_col': (220,  16,  28),
    },

    # ── La Liga ─── Spanish teams ────────────────────────────────
    'fc_blaugrana': {
        'name':    'FC Blaugrana',          # inspo: Barcelona
        'country': 'Spain',
        'shirt1':  (  0,  82, 170),
        'shirt2':  (165,  17,  17),
        'shorts':  (  0,  82, 170),
        'socks':   (  0,  82, 170),
        'gk':      (255, 140,   0),
        'skin':    SKIN_LIGHT,
        'hair':    HAIR_DARK,
        'num_col': (255, 255, 255),
        'hud_col': (  0,  82, 170),
        'stripe':  True,
        'stripe_cols': [(0, 82, 170), (165, 17, 17), (0, 82, 170)],
    },

    'los_blancos': {
        'name':    'Los Blancos CF',        # inspo: Real Madrid
        'country': 'Spain',
        'shirt1':  (238, 238, 238),
        'shirt2':  (238, 238, 238),
        'shorts':  (215, 215, 215),
        'socks':   (215, 215, 215),
        'gk':      ( 40, 160,  60),
        'skin':    SKIN_MED,
        'hair':    HAIR_MED,
        'num_col': ( 30,  30,  30),
        'hud_col': (215, 215, 215),
        'gold_border': True,
    },

    'yellow_submarine': {
        'name':    'Yellow Submarine FC',   # inspo: Villarreal
        'country': 'Spain',
        'shirt1':  (255, 210,   0),
        'shirt2':  (255, 210,   0),
        'shorts':  ( 20,  20,  20),
        'socks':   (255, 210,   0),
        'gk':      ( 80, 160, 255),
        'skin':    SKIN_LIGHT,
        'hair':    HAIR_DARK,
        'num_col': ( 20,  20,  20),
        'hud_col': (220, 190,   0),
    },

    'colchoneros': {
        'name':    'Club Colchoneros',      # inspo: Atlético Madrid
        'country': 'Spain',
        'shirt1':  (206,  32,  44),
        'shirt2':  (255, 255, 255),
        'shorts':  ( 20,  20,  20),
        'socks':   (206,  32,  44),
        'gk':      (  0, 180, 120),
        'skin':    SKIN_MED,
        'hair':    HAIR_MED,
        'num_col': (255, 255, 255),
        'hud_col': (206,  32,  44),
        'stripe':  True,
        'stripe_cols': [(206, 32, 44), (255, 255, 255), (206, 32, 44)],
    },

    'los_verdiblancos': {
        'name':    'Los Verdiblancos',      # inspo: Real Betis
        'country': 'Spain',
        'shirt1':  ( 0, 130,  62),
        'shirt2':  (255, 255, 255),
        'shorts':  ( 20,  20,  20),
        'socks':   ( 0, 130,  62),
        'gk':      (220, 180,   0),
        'skin':    SKIN_OLIVE,
        'hair':    HAIR_BLACK,
        'num_col': (255, 255, 255),
        'hud_col': (  0, 130,  62),
        'stripe':  True,
        'stripe_cols': [(0, 130, 62), (255, 255, 255), (0, 130, 62)],
    },

    'los_celestes': {
        'name':    'Los Celestes SC',       # inspo: Celta Vigo
        'country': 'Spain',
        'shirt1':  (135, 206, 235),
        'shirt2':  (255, 255, 255),
        'shorts':  (135, 206, 235),
        'socks':   (135, 206, 235),
        'gk':      (255, 100,   0),
        'skin':    SKIN_LIGHT,
        'hair':    HAIR_DARK,
        'num_col': ( 20,  20,  20),
        'hud_col': (135, 206, 235),
        'half_half': True,
    },

    'la_real': {
        'name':    'La Real SC',            # inspo: Real Sociedad
        'country': 'Spain',
        'shirt1':  ( 20,  20,  20),
        'shirt2':  (255, 255, 255),
        'shorts':  ( 20,  20,  20),
        'socks':   ( 20,  20,  20),
        'gk':      (  0, 160, 100),
        'skin':    SKIN_LIGHT,
        'hair':    HAIR_DARK,
        'num_col': (255, 255, 255),
        'hud_col': ( 80,  80,  80),
        'stripe':  True,
        'stripe_cols': [(20, 20, 20), (255, 255, 255), (20, 20, 20)],
    },

    'azulones': {
        'name':    'FC Azulones',           # inspo: Getafe
        'country': 'Spain',
        'shirt1':  ( 20,  62, 134),
        'shirt2':  ( 20,  62, 134),
        'shorts':  ( 20,  62, 134),
        'socks':   ( 20,  62, 134),
        'gk':      (220,  80,   0),
        'skin':    SKIN_MED,
        'hair':    HAIR_MED,
        'num_col': (255, 255, 255),
        'hud_col': ( 20,  62, 134),
    },

    'los_rojillos': {
        'name':    'Los Rojillos CF',       # inspo: Osasuna
        'country': 'Spain',
        'shirt1':  (180,  20,  30),
        'shirt2':  (  0,   0,   0),
        'shorts':  (  0,   0,   0),
        'socks':   (180,  20,  30),
        'gk':      (  0, 160, 220),
        'skin':    SKIN_LIGHT,
        'hair':    HAIR_DARK,
        'num_col': (255, 255, 255),
        'hud_col': (180,  20,  30),
        'stripe':  True,
        'stripe_cols': [(180, 20, 30), (0, 0, 0), (180, 20, 30)],
    },

    'periquitos': {
        'name':    'Periquitos FC',         # inspo: Espanyol
        'country': 'Spain',
        'shirt1':  ( 40,  80, 160),
        'shirt2':  (255, 255, 255),
        'shorts':  (  0,   0,   0),
        'socks':   ( 40,  80, 160),
        'gk':      (  0, 180,  80),
        'skin':    SKIN_OLIVE,
        'hair':    HAIR_BLACK,
        'num_col': (255, 255, 255),
        'hud_col': ( 40,  80, 160),
        'stripe':  True,
        'stripe_cols': [(40, 80, 160), (255, 255, 255), (40, 80, 160)],
    },

    'los_leones': {
        'name':    'Los Leones AC',         # inspo: Athletic Club
        'country': 'Spain',
        'shirt1':  (210,  20,  30),
        'shirt2':  (255, 255, 255),
        'shorts':  (  0,   0,   0),
        'socks':   (  0,   0,   0),
        'gk':      (200, 200,   0),
        'skin':    SKIN_LIGHT,
        'hair':    HAIR_DARK,
        'num_col': (255, 255, 255),
        'hud_col': (210,  20,  30),
        'stripe':  True,
        'stripe_cols': [(210, 20, 30), (255, 255, 255), (210, 20, 30)],
    },

    'montilivi': {
        'name':    'FC Montilivi',          # inspo: Girona
        'country': 'Spain',
        'shirt1':  (190,   0,  30),
        'shirt2':  (255, 255, 255),
        'shorts':  (255, 255, 255),
        'socks':   (190,   0,  30),
        'gk':      ( 80, 200, 120),
        'skin':    SKIN_OLIVE,
        'hair':    HAIR_BLACK,
        'num_col': ( 20,  20,  20),
        'hud_col': (190,   0,  30),
        'half_half': True,
    },

    'franjirrojos': {
        'name':    'Franjirrojos FC',       # inspo: Rayo Vallecano
        'country': 'Spain',
        'shirt1':  (255, 255, 255),
        'shirt2':  (200,  20,  30),
        'shorts':  (255, 255, 255),
        'socks':   (255, 255, 255),
        'gk':      (220, 180,   0),
        'skin':    SKIN_LIGHT,
        'hair':    HAIR_DARK,
        'num_col': ( 20,  20,  20),
        'hud_col': (200,  20,  30),
        'sash':    True,   # diagonal red sash on white
    },

    'los_ches': {
        'name':    'Los Ches CF',           # inspo: Valencia
        'country': 'Spain',
        'shirt1':  (255, 255, 255),
        'shirt2':  (  0,   0,   0),
        'shorts':  (  0,   0,   0),
        'socks':   (  0,   0,   0),
        'gk':      (220, 120,   0),
        'skin':    SKIN_OLIVE,
        'hair':    HAIR_BLACK,
        'num_col': ( 20,  20,  20),
        'hud_col': (200, 200, 200),
    },

    'babazorros': {
        'name':    'FC Babazorros',         # inspo: Alavés
        'country': 'Spain',
        'shirt1':  (  0,  40, 130),
        'shirt2':  (255, 255, 255),
        'shorts':  (255, 255, 255),
        'socks':   (  0,  40, 130),
        'gk':      (220,  50,   0),
        'skin':    SKIN_LIGHT,
        'hair':    HAIR_DARK,
        'num_col': (255, 255, 255),
        'hud_col': (  0,  40, 130),
        'stripe':  True,
        'stripe_cols': [(0, 40, 130), (255, 255, 255), (0, 40, 130)],
    },

    'vermells': {
        'name':    'FC Vermells',           # inspo: Mallorca
        'country': 'Spain',
        'shirt1':  (210,  20,  40),
        'shirt2':  (  0,   0,   0),
        'shorts':  (  0,   0,   0),
        'socks':   (  0,   0,   0),
        'gk':      (  0, 180, 180),
        'skin':    SKIN_OLIVE,
        'hair':    HAIR_BLACK,
        'num_col': (255, 255, 255),
        'hud_col': (210,  20,  40),
    },

    'nervionenses': {
        'name':    'Club Nervionenses',     # inspo: Sevilla
        'country': 'Spain',
        'shirt1':  (255, 255, 255),
        'shirt2':  (255, 255, 255),
        'shorts':  (255, 255, 255),
        'socks':   (255, 255, 255),
        'gk':      (200,  20,  30),
        'skin':    SKIN_OLIVE,
        'hair':    HAIR_BLACK,
        'num_col': ( 20,  20,  20),
        'hud_col': (210, 210, 210),
        'gold_border': True,
    },

    'fc_ilicitano': {
        'name':    'FC Ilicitano',          # inspo: Elche
        'country': 'Spain',
        'shirt1':  ( 20,  20,  20),
        'shirt2':  (255, 255, 255),
        'shorts':  ( 20,  20,  20),
        'socks':   ( 20,  20,  20),
        'gk':      (  0, 160, 220),
        'skin':    SKIN_OLIVE,
        'hair':    HAIR_BLACK,
        'num_col': (255, 255, 255),
        'hud_col': ( 80,  80,  80),
        'half_half': True,
    },

    'granotes': {
        'name':    'FC Granotes',           # inspo: Levante
        'country': 'Spain',
        'shirt1':  ( 40,  90, 180),
        'shirt2':  (180,  20,  30),
        'shorts':  ( 40,  90, 180),
        'socks':   ( 40,  90, 180),
        'gk':      (  0, 180,  90),
        'skin':    SKIN_OLIVE,
        'hair':    HAIR_BLACK,
        'num_col': (255, 255, 255),
        'hud_col': ( 40,  90, 180),
        'stripe':  True,
        'stripe_cols': [(40, 90, 180), (180, 20, 30), (40, 90, 180)],
    },

    'carbayones': {
        'name':    'FC Carbayones',         # inspo: Real Oviedo
        'country': 'Spain',
        'shirt1':  ( 20,  90, 180),
        'shirt2':  ( 20,  90, 180),
        'shorts':  (  0,   0,   0),
        'socks':   ( 20,  90, 180),
        'gk':      (220, 180,   0),
        'skin':    SKIN_LIGHT,
        'hair':    HAIR_DARK,
        'num_col': (255, 255, 255),
        'hud_col': ( 20,  90, 180),
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
