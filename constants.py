"""constants.py – world settings, colours, all 60 teams."""
import math

# ── World dimensions ─────────────────────────────────────────────
W_W, W_H   = 1260, 810
W_MX, W_MY = W_W // 2, W_H // 2

GOAL_W       = 88     # 7.32m  (real ratio of pitch width 68m)
GOAL_TOP     = W_MY - GOAL_W // 2
GOAL_BOT     = W_MY + GOAL_W // 2
GOAL_DEPTH_W = 24     # ~2m goal depth
GOAL_H_Z     = 0      # unused in top-down view (kept for compatibility)

PA_W, PA_H = 198, 480   # 16.5m x 40.32m penalty area
SB_W, SB_H =  66, 218   # 5.5m  x 18.32m six-yard box
CTR_R       = 110        # 9.15m centre-circle / penalty-arc radius
PEN_SPOT_D  = 132        # 11m penalty spot distance from goal line
OUT_L = OUT_R = OUT_T = OUT_B = 90

# ── Screen ───────────────────────────────────────────────────────
SCR_W, SCR_H = 1280, 800
FPS = 60

# ── Match timing ─────────────────────────────────────────────────
REAL_SECS_PER_HALF = 180
HALF_FRAMES        = REAL_SECS_PER_HALF * FPS
MATCH_FRAMES       = HALF_FRAMES * 2

# ── Top-down orthographic projection ──────────────────────────────
# A clean bird's-eye view: world (x,y) maps directly to screen with a
# single uniform scale. wz (height) only gives a small visual lift
# for the ball and player animation "hop" — it does NOT skew the pitch.
PITCH_SCALE = 0.70
ISO_CX = SCR_W // 2
ISO_CY = SCR_H // 2 - 10
Z_LIFT = 0.5   # pixels of vertical lift per world-unit of height

def w2s(wx, wy, wz=0.0):
    sx = (wx - W_MX) * PITCH_SCALE + ISO_CX
    sy = (wy - W_MY) * PITCH_SCALE + ISO_CY - wz * Z_LIFT
    return int(sx), int(sy)

# ── Physics ──────────────────────────────────────────────────────
PLAYER_R         = 14
BALL_R           = 7
PLAYER_SPD       = 3.6
SPRINT_MULT      = 1.62
BALL_FRIC        = 0.978
BALL_GRAV        = 0.52
PASS_SPD         = 11.0
CROSS_SPD        = 13.0
SHOOT_SPD        = 19.0
THROUGH_PASS_SPD = 13.4
CONTROL_R        = 21
TACKLE_R         = 26

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
DB_LABELS   = {}   # built dynamically by Game using team names

# ── Shared skin/hair tones ───────────────────────────────────────
SKIN_LIGHT = (222, 182, 142)
HAIR_DARK  = ( 38,  28,  18)
SKIN_MED   = (212, 176, 136)
HAIR_MED   = ( 58,  44,  20)
SKIN_OLIVE = (198, 160, 110)
HAIR_BLACK = ( 20,  14,   8)

# Legacy aliases
SKIN_A   = SKIN_LIGHT
HAIR_A   = HAIR_DARK
SKIN_B   = SKIN_MED
HAIR_B   = HAIR_MED
RMA_GOLD = (198, 162,   0)
BAR_BLUE = (  0,  82, 170)

# ═════════════════════════════════════════════════════════════════
# TEAM REGISTRY  –  60 clubs, portfolio-safe names
# Kit flags: stripe / half_half / gold_border / sash / hoops
# ═════════════════════════════════════════════════════════════════
TEAMS = {

    # ══════════════════════════════════════════════════════════
    # ENGLAND  (20 clubs)
    # ══════════════════════════════════════════════════════════

    'the_gunners': {
        'name':    'The Gunners FC',        # Arsenal
        'country': 'England',
        'shirt1':  (239,   1,   7),
        'shirt2':  (239,   1,   7),
        'shorts':  (239,   1,   7),
        'socks':   (239,   1,   7),
        'gk':      (255, 210,   0),
        'skin':    SKIN_LIGHT, 'hair': HAIR_DARK,
        'num_col': (255, 255, 255),
        'hud_col': (200,   0,   0),
    },

    'sky_blues': {
        'name':    'Sky Blues FC',          # Man City
        'country': 'England',
        'shirt1':  ( 97, 195, 238),
        'shirt2':  (255, 255, 255),
        'shorts':  ( 97, 195, 238),
        'socks':   ( 97, 195, 238),
        'gk':      (255, 140,   0),
        'skin':    SKIN_MED, 'hair': HAIR_BLACK,
        'num_col': (255, 255, 255),
        'hud_col': ( 97, 195, 238),
        'half_half': True,
    },

    'red_devils': {
        'name':    'Red Devils FC',         # Man United
        'country': 'England',
        'shirt1':  (218,   0,  24),
        'shirt2':  (218,   0,  24),
        'shorts':  ( 20,  20,  20),
        'socks':   ( 20,  20,  20),
        'gk':      (  0, 160, 100),
        'skin':    SKIN_LIGHT, 'hair': HAIR_DARK,
        'num_col': (255, 255, 255),
        'hud_col': (200,   0,  20),
    },

    'the_villans': {
        'name':    'The Villans AC',        # Aston Villa
        'country': 'England',
        'shirt1':  (149,  14,  46),
        'shirt2':  (105, 175, 238),
        'shorts':  (255, 255, 255),
        'socks':   (149,  14,  46),
        'gk':      (  0, 200, 120),
        'skin':    SKIN_MED, 'hair': HAIR_MED,
        'num_col': (255, 255, 255),
        'hud_col': (149,  14,  46),
        'half_half': True,
    },

    'the_reds': {
        'name':    'The Reds FC',           # Liverpool
        'country': 'England',
        'shirt1':  (200,  16,  46),
        'shirt2':  (200,  16,  46),
        'shorts':  (200,  16,  46),
        'socks':   (200,  16,  46),
        'gk':      (  0, 180, 220),
        'skin':    SKIN_LIGHT, 'hair': HAIR_DARK,
        'num_col': (255, 255, 255),
        'hud_col': (200,  16,  46),
    },

    'the_blues': {
        'name':    'The Blues FC',          # Chelsea
        'country': 'England',
        'shirt1':  (  3,  70, 148),
        'shirt2':  (  3,  70, 148),
        'shorts':  (  3,  70, 148),
        'socks':   (  3,  70, 148),
        'gk':      (255, 200,   0),
        'skin':    SKIN_MED, 'hair': HAIR_BLACK,
        'num_col': (255, 255, 255),
        'hud_col': (  3,  70, 148),
    },

    'the_bees': {
        'name':    'The Bees FC',           # Brentford
        'country': 'England',
        'shirt1':  (210,  20,  30),
        'shirt2':  (255, 255, 255),
        'shorts':  ( 20,  20,  20),
        'socks':   (210,  20,  30),
        'gk':      (  0, 180, 100),
        'skin':    SKIN_LIGHT, 'hair': HAIR_DARK,
        'num_col': (255, 255, 255),
        'hud_col': (210,  20,  30),
        'stripe':  True,
        'stripe_cols': [(210, 20, 30), (255, 255, 255), (210, 20, 30)],
    },

    'the_toffees': {
        'name':    'The Toffees FC',        # Everton
        'country': 'England',
        'shirt1':  ( 39,  68, 136),
        'shirt2':  ( 39,  68, 136),
        'shorts':  (255, 255, 255),
        'socks':   ( 39,  68, 136),
        'gk':      (255, 140,   0),
        'skin':    SKIN_LIGHT, 'hair': HAIR_DARK,
        'num_col': (255, 255, 255),
        'hud_col': ( 39,  68, 136),
    },

    'the_seagulls': {
        'name':    'The Seagulls FC',       # Brighton
        'country': 'England',
        'shirt1':  (  0, 122, 183),
        'shirt2':  (255, 255, 255),
        'shorts':  (  0, 122, 183),
        'socks':   (255, 255, 255),
        'gk':      (255, 180,   0),
        'skin':    SKIN_MED, 'hair': HAIR_MED,
        'num_col': (255, 255, 255),
        'hud_col': (  0, 122, 183),
        'stripe':  True,
        'stripe_cols': [(0, 122, 183), (255, 255, 255), (0, 122, 183)],
    },

    'the_black_cats': {
        'name':    'Black Cats FC',         # Sunderland
        'country': 'England',
        'shirt1':  (210,   0,  10),
        'shirt2':  ( 20,  20,  20),
        'shorts':  ( 20,  20,  20),
        'socks':   (210,   0,  10),
        'gk':      (  0, 180, 180),
        'skin':    SKIN_LIGHT, 'hair': HAIR_DARK,
        'num_col': (255, 255, 255),
        'hud_col': (180,   0,  10),
        'stripe':  True,
        'stripe_cols': [(210, 0, 10), (20, 20, 20), (210, 0, 10)],
    },

    'the_cherries': {
        'name':    'The Cherries FC',       # Bournemouth
        'country': 'England',
        'shirt1':  (218,  41,  28),
        'shirt2':  ( 20,  20,  20),
        'shorts':  ( 20,  20,  20),
        'socks':   ( 20,  20,  20),
        'gk':      (  0, 180, 120),
        'skin':    SKIN_LIGHT, 'hair': HAIR_DARK,
        'num_col': (255, 255, 255),
        'hud_col': (200,  30,  20),
        'stripe':  True,
        'stripe_cols': [(218, 41, 28), (20, 20, 20), (218, 41, 28)],
    },

    'the_cottagers': {
        'name':    'The Cottagers FC',      # Fulham
        'country': 'England',
        'shirt1':  (255, 255, 255),
        'shirt2':  (255, 255, 255),
        'shorts':  ( 20,  20,  20),
        'socks':   (255, 255, 255),
        'gk':      (255, 180,   0),
        'skin':    SKIN_MED, 'hair': HAIR_MED,
        'num_col': ( 20,  20,  20),
        'hud_col': (200, 200, 200),
    },

    'the_eagles': {
        'name':    'The Eagles FC',         # Crystal Palace
        'country': 'England',
        'shirt1':  (  1,  90, 165),
        'shirt2':  (210,   0,  10),
        'shorts':  (  1,  90, 165),
        'socks':   (  1,  90, 165),
        'gk':      (  0, 180, 100),
        'skin':    SKIN_LIGHT, 'hair': HAIR_DARK,
        'num_col': (255, 255, 255),
        'hud_col': (  1,  90, 165),
        'stripe':  True,
        'stripe_cols': [(1, 90, 165), (210, 0, 10), (1, 90, 165)],
    },

    'the_magpies': {
        'name':    'The Magpies FC',        # Newcastle
        'country': 'England',
        'shirt1':  ( 20,  20,  20),
        'shirt2':  (255, 255, 255),
        'shorts':  ( 20,  20,  20),
        'socks':   ( 20,  20,  20),
        'gk':      (  0, 160, 220),
        'skin':    SKIN_MED, 'hair': HAIR_BLACK,
        'num_col': (255, 255, 255),
        'hud_col': (100, 100, 100),
        'stripe':  True,
        'stripe_cols': [(20, 20, 20), (255, 255, 255), (20, 20, 20)],
    },

    'the_whites': {
        'name':    'The Whites FC',         # Leeds
        'country': 'England',
        'shirt1':  (255, 255, 255),
        'shirt2':  (255, 255, 255),
        'shorts':  (255, 255, 255),
        'socks':   (255, 255, 255),
        'gk':      (255, 180,   0),
        'skin':    SKIN_LIGHT, 'hair': HAIR_DARK,
        'num_col': ( 20,  20,  20),
        'hud_col': (200, 200, 200),
        'gold_border': True,
    },

    'the_tricky_trees': {
        'name':    'Tricky Trees FC',       # Nottm Forest
        'country': 'England',
        'shirt1':  (220,  20,  30),
        'shirt2':  (220,  20,  30),
        'shorts':  (255, 255, 255),
        'socks':   (220,  20,  30),
        'gk':      (  0, 160, 220),
        'skin':    SKIN_LIGHT, 'hair': HAIR_DARK,
        'num_col': (255, 255, 255),
        'hud_col': (200,  10,  20),
    },

    'the_hammers': {
        'name':    'The Hammers FC',        # West Ham
        'country': 'England',
        'shirt1':  (122,  24,  48),
        'shirt2':  (105, 165, 195),
        'shorts':  ( 20,  20,  20),
        'socks':   (122,  24,  48),
        'gk':      (  0, 200, 120),
        'skin':    SKIN_MED, 'hair': HAIR_MED,
        'num_col': (255, 255, 255),
        'hud_col': (122,  24,  48),
        'half_half': True,
    },

    'the_spurs': {
        'name':    'The Spurs FC',          # Tottenham
        'country': 'England',
        'shirt1':  (255, 255, 255),
        'shirt2':  (255, 255, 255),
        'shorts':  (  0,   0,   0),
        'socks':   (255, 255, 255),
        'gk':      (255, 150,   0),
        'skin':    SKIN_MED, 'hair': HAIR_BLACK,
        'num_col': ( 10,  10,  10),
        'hud_col': (200, 200, 200),
    },

    'the_clarets': {
        'name':    'The Clarets FC',        # Burnley
        'country': 'England',
        'shirt1':  (110,  20,  46),
        'shirt2':  (105, 165, 195),
        'shorts':  (255, 255, 255),
        'socks':   (110,  20,  46),
        'gk':      (  0, 200, 120),
        'skin':    SKIN_LIGHT, 'hair': HAIR_DARK,
        'num_col': (255, 255, 255),
        'hud_col': (110,  20,  46),
        'half_half': True,
    },

    'the_wolves': {
        'name':    'The Wolves FC',         # Wolves
        'country': 'England',
        'shirt1':  (253, 185,  19),
        'shirt2':  (253, 185,  19),
        'shorts':  ( 20,  20,  20),
        'socks':   (253, 185,  19),
        'gk':      (  0, 160, 220),
        'skin':    SKIN_LIGHT, 'hair': HAIR_DARK,
        'num_col': ( 20,  20,  20),
        'hud_col': (220, 165,  10),
    },

    # ══════════════════════════════════════════════════════════
    # GERMANY  (18 clubs)
    # ══════════════════════════════════════════════════════════

    'fc_rot': {
        'name':    'FC Rot München',        # Bayern Munich
        'country': 'Germany',
        'shirt1':  (220,  16,  28),
        'shirt2':  (220,  16,  28),
        'shorts':  (220,  16,  28),
        'socks':   (220,  16,  28),
        'gk':      (255, 210,   0),
        'skin':    SKIN_LIGHT, 'hair': HAIR_DARK,
        'num_col': (255, 255, 255),
        'hud_col': (220,  16,  28),
    },

    'die_borussen': {
        'name':    'Die Borussen',          # Dortmund
        'country': 'Germany',
        'shirt1':  (255, 215,   0),
        'shirt2':  (255, 215,   0),
        'shorts':  ( 20,  20,  20),
        'socks':   (255, 215,   0),
        'gk':      (  0, 160, 220),
        'skin':    SKIN_LIGHT, 'hair': HAIR_DARK,
        'num_col': ( 20,  20,  20),
        'hud_col': (220, 185,   0),
    },

    'die_schwaben': {
        'name':    'Die Schwaben VfB',      # VfB Stuttgart
        'country': 'Germany',
        'shirt1':  (255, 255, 255),
        'shirt2':  (210,  16,  32),
        'shorts':  ( 20,  20,  20),
        'socks':   (255, 255, 255),
        'gk':      (  0, 180, 120),
        'skin':    SKIN_LIGHT, 'hair': HAIR_DARK,
        'num_col': ( 20,  20,  20),
        'hud_col': (200, 200, 200),
        'stripe':  True,
        'stripe_cols': [(255, 255, 255), (210, 16, 32), (255, 255, 255)],
    },

    'die_bullen': {
        'name':    'Die Bullen RB',         # RB Leipzig
        'country': 'Germany',
        'shirt1':  (255, 255, 255),
        'shirt2':  (210,  16,  32),
        'shorts':  (255, 255, 255),
        'socks':   (255, 255, 255),
        'gk':      (255, 165,   0),
        'skin':    SKIN_MED, 'hair': HAIR_MED,
        'num_col': (210,  16,  32),
        'hud_col': (200,   0,  20),
        'half_half': True,
    },

    'die_werkself': {
        'name':    'Die Werkself',          # Leverkusen
        'country': 'Germany',
        'shirt1':  (210,   0,  30),
        'shirt2':  ( 20,  20,  20),
        'shorts':  ( 20,  20,  20),
        'socks':   (210,   0,  30),
        'gk':      (  0, 180, 220),
        'skin':    SKIN_LIGHT, 'hair': HAIR_DARK,
        'num_col': (255, 255, 255),
        'hud_col': (200,   0,  20),
        'stripe':  True,
        'stripe_cols': [(210, 0, 30), (20, 20, 20), (210, 0, 30)],
    },

    'die_kraichgauer': {
        'name':    'Die Kraichgauer',       # Hoffenheim
        'country': 'Germany',
        'shirt1':  ( 31,  61, 143),
        'shirt2':  (255, 255, 255),
        'shorts':  ( 31,  61, 143),
        'socks':   ( 31,  61, 143),
        'gk':      (255, 165,   0),
        'skin':    SKIN_MED, 'hair': HAIR_MED,
        'num_col': (255, 255, 255),
        'hud_col': ( 31,  61, 143),
    },

    'die_adler': {
        'name':    'Die Adler Frankfurt',   # Eintracht Frankfurt
        'country': 'Germany',
        'shirt1':  ( 20,  20,  20),
        'shirt2':  (255, 255, 255),
        'shorts':  ( 20,  20,  20),
        'socks':   (210,   0,  10),
        'gk':      (  0, 180, 120),
        'skin':    SKIN_LIGHT, 'hair': HAIR_DARK,
        'num_col': (255, 255, 255),
        'hud_col': ( 80,  80,  80),
        'stripe':  True,
        'stripe_cols': [(20, 20, 20), (255, 255, 255), (20, 20, 20)],
    },

    'die_breisgauer': {
        'name':    'Die Breisgauer SC',     # SC Freiburg
        'country': 'Germany',
        'shirt1':  (210,   0,  10),
        'shirt2':  (255, 255, 255),
        'shorts':  ( 20,  20,  20),
        'socks':   (210,   0,  10),
        'gk':      (  0, 160, 220),
        'skin':    SKIN_LIGHT, 'hair': HAIR_DARK,
        'num_col': (255, 255, 255),
        'hud_col': (180,   0,  10),
        'stripe':  True,
        'stripe_cols': [(210, 0, 10), (255, 255, 255), (210, 0, 10)],
    },

    'die_nullfunfer': {
        'name':    'Die Nullfünfer',        # Mainz
        'country': 'Germany',
        'shirt1':  (210,   0,  20),
        'shirt2':  (255, 255, 255),
        'shorts':  (255, 255, 255),
        'socks':   (210,   0,  20),
        'gk':      (  0, 180, 120),
        'skin':    SKIN_LIGHT, 'hair': HAIR_DARK,
        'num_col': (255, 255, 255),
        'hud_col': (190,   0,  15),
        'half_half': True,
    },

    'die_fuggerstadter': {
        'name':    'FC Fuggerstadt',        # Augsburg
        'country': 'Germany',
        'shirt1':  (210,   0,  20),
        'shirt2':  (  0,   0, 155),
        'shorts':  (255, 255, 255),
        'socks':   (210,   0,  20),
        'gk':      (  0, 200, 130),
        'skin':    SKIN_MED, 'hair': HAIR_MED,
        'num_col': (255, 255, 255),
        'hud_col': (180,   0,  15),
        'stripe':  True,
        'stripe_cols': [(210, 0, 20), (0, 0, 155), (210, 0, 20)],
    },

    'die_eisernen': {
        'name':    'Die Eisernen Berlin',   # Union Berlin
        'country': 'Germany',
        'shirt1':  (210,   0,  20),
        'shirt2':  (210,   0,  20),
        'shorts':  (255, 255, 255),
        'socks':   (210,   0,  20),
        'gk':      (  0, 180, 220),
        'skin':    SKIN_LIGHT, 'hair': HAIR_DARK,
        'num_col': (255, 255, 255),
        'hud_col': (180,   0,  10),
    },

    'die_dinos': {
        'name':    'Die Dinos Hamburg',     # Hamburg
        'country': 'Germany',
        'shirt1':  (255, 255, 255),
        'shirt2':  (255, 255, 255),
        'shorts':  (255, 255, 255),
        'socks':   (255, 255, 255),
        'gk':      (255, 165,   0),
        'skin':    SKIN_LIGHT, 'hair': HAIR_DARK,
        'num_col': (210,   0,  20),
        'hud_col': (200, 200, 200),
        'gold_border': True,
    },

    'die_geissböcke': {
        'name':    'Die Geissbocke',        # Köln
        'country': 'Germany',
        'shirt1':  (255, 255, 255),
        'shirt2':  (210,   0,  20),
        'shorts':  (255, 255, 255),
        'socks':   (255, 255, 255),
        'gk':      (  0, 160, 220),
        'skin':    SKIN_MED, 'hair': HAIR_MED,
        'num_col': ( 20,  20,  20),
        'hud_col': (200, 200, 200),
        'stripe':  True,
        'stripe_cols': [(255, 255, 255), (210, 0, 20), (255, 255, 255)],
    },

    'die_fohlen': {
        'name':    'Die Fohlen',            # Mönchengladbach
        'country': 'Germany',
        'shirt1':  (255, 255, 255),
        'shirt2':  ( 20,  20,  20),
        'shorts':  (255, 255, 255),
        'socks':   (255, 255, 255),
        'gk':      (255, 165,   0),
        'skin':    SKIN_LIGHT, 'hair': HAIR_DARK,
        'num_col': ( 20,  20,  20),
        'hud_col': (200, 200, 200),
        'stripe':  True,
        'stripe_cols': [(255, 255, 255), (20, 20, 20), (255, 255, 255)],
    },

    'die_werderaner': {
        'name':    'Die Werderaner',        # Werder Bremen
        'country': 'Germany',
        'shirt1':  (  0, 148,  68),
        'shirt2':  (255, 255, 255),
        'shorts':  (255, 255, 255),
        'socks':   (  0, 148,  68),
        'gk':      (255, 165,   0),
        'skin':    SKIN_MED, 'hair': HAIR_MED,
        'num_col': (255, 255, 255),
        'hud_col': (  0, 130,  60),
        'stripe':  True,
        'stripe_cols': [(0, 148, 68), (255, 255, 255), (0, 148, 68)],
    },

    'die_kieze': {
        'name':    'FC St. Kieze',          # St. Pauli
        'country': 'Germany',
        'shirt1':  (110,  30,  30),
        'shirt2':  (255, 255, 255),
        'shorts':  ( 20,  20,  20),
        'socks':   (110,  30,  30),
        'gk':      (  0, 180, 120),
        'skin':    SKIN_LIGHT, 'hair': HAIR_DARK,
        'num_col': (255, 255, 255),
        'hud_col': (110,  30,  30),
        'stripe':  True,
        'stripe_cols': [(110, 30, 30), (255, 255, 255), (110, 30, 30)],
    },

    'die_wolfe': {
        'name':    'Die Wölfe FC',          # Wolfsburg
        'country': 'Germany',
        'shirt1':  ( 65, 182,  71),
        'shirt2':  (255, 255, 255),
        'shorts':  ( 65, 182,  71),
        'socks':   ( 65, 182,  71),
        'gk':      (255, 165,   0),
        'skin':    SKIN_MED, 'hair': HAIR_MED,
        'num_col': (255, 255, 255),
        'hud_col': ( 55, 160,  60),
        'half_half': True,
    },

    'die_storche': {
        'name':    'Die Störche FC',        # Heidenheim
        'country': 'Germany',
        'shirt1':  (210,  60,   0),
        'shirt2':  (  0,  70, 150),
        'shorts':  (210,  60,   0),
        'socks':   (210,  60,   0),
        'gk':      (  0, 180, 120),
        'skin':    SKIN_LIGHT, 'hair': HAIR_DARK,
        'num_col': (255, 255, 255),
        'hud_col': (190,  50,   0),
        'stripe':  True,
        'stripe_cols': [(210, 60, 0), (0, 70, 150), (210, 60, 0)],
    },

    # ══════════════════════════════════════════════════════════
    # SPAIN  (20 clubs)
    # ══════════════════════════════════════════════════════════

    'fc_blaugrana': {
        'name':    'FC Blaugrana',          # Barcelona
        'country': 'Spain',
        'shirt1':  (  0,  82, 170),
        'shirt2':  (165,  17,  17),
        'shorts':  (  0,  82, 170),
        'socks':   (  0,  82, 170),
        'gk':      (255, 140,   0),
        'skin':    SKIN_LIGHT, 'hair': HAIR_DARK,
        'num_col': (255, 255, 255),
        'hud_col': (  0,  82, 170),
        'stripe':  True,
        'stripe_cols': [(0, 82, 170), (165, 17, 17), (0, 82, 170)],
    },

    'los_blancos': {
        'name':    'Los Blancos CF',        # Real Madrid
        'country': 'Spain',
        'shirt1':  (238, 238, 238),
        'shirt2':  (238, 238, 238),
        'shorts':  (215, 215, 215),
        'socks':   (215, 215, 215),
        'gk':      ( 40, 160,  60),
        'skin':    SKIN_MED, 'hair': HAIR_MED,
        'num_col': ( 30,  30,  30),
        'hud_col': (215, 215, 215),
        'gold_border': True,
    },

    'yellow_submarine': {
        'name':    'Yellow Submarine FC',   # Villarreal
        'country': 'Spain',
        'shirt1':  (255, 210,   0),
        'shirt2':  (255, 210,   0),
        'shorts':  ( 20,  20,  20),
        'socks':   (255, 210,   0),
        'gk':      ( 80, 160, 255),
        'skin':    SKIN_LIGHT, 'hair': HAIR_DARK,
        'num_col': ( 20,  20,  20),
        'hud_col': (220, 190,   0),
    },

    'colchoneros': {
        'name':    'Club Colchoneros',      # Atlético Madrid
        'country': 'Spain',
        'shirt1':  (206,  32,  44),
        'shirt2':  (255, 255, 255),
        'shorts':  ( 20,  20,  20),
        'socks':   (206,  32,  44),
        'gk':      (  0, 180, 120),
        'skin':    SKIN_MED, 'hair': HAIR_MED,
        'num_col': (255, 255, 255),
        'hud_col': (206,  32,  44),
        'stripe':  True,
        'stripe_cols': [(206, 32, 44), (255, 255, 255), (206, 32, 44)],
    },

    'los_verdiblancos': {
        'name':    'Los Verdiblancos',      # Real Betis
        'country': 'Spain',
        'shirt1':  (  0, 130,  62),
        'shirt2':  (255, 255, 255),
        'shorts':  ( 20,  20,  20),
        'socks':   (  0, 130,  62),
        'gk':      (220, 180,   0),
        'skin':    SKIN_OLIVE, 'hair': HAIR_BLACK,
        'num_col': (255, 255, 255),
        'hud_col': (  0, 130,  62),
        'stripe':  True,
        'stripe_cols': [(0, 130, 62), (255, 255, 255), (0, 130, 62)],
    },

    'los_celestes': {
        'name':    'Los Celestes SC',       # Celta Vigo
        'country': 'Spain',
        'shirt1':  (135, 206, 235),
        'shirt2':  (255, 255, 255),
        'shorts':  (135, 206, 235),
        'socks':   (135, 206, 235),
        'gk':      (255, 100,   0),
        'skin':    SKIN_LIGHT, 'hair': HAIR_DARK,
        'num_col': ( 20,  20,  20),
        'hud_col': (135, 206, 235),
        'half_half': True,
    },

    'la_real': {
        'name':    'La Real SC',            # Real Sociedad
        'country': 'Spain',
        'shirt1':  ( 20,  20,  20),
        'shirt2':  (255, 255, 255),
        'shorts':  ( 20,  20,  20),
        'socks':   ( 20,  20,  20),
        'gk':      (  0, 160, 100),
        'skin':    SKIN_LIGHT, 'hair': HAIR_DARK,
        'num_col': (255, 255, 255),
        'hud_col': ( 80,  80,  80),
        'stripe':  True,
        'stripe_cols': [(20, 20, 20), (255, 255, 255), (20, 20, 20)],
    },

    'azulones': {
        'name':    'FC Azulones',           # Getafe
        'country': 'Spain',
        'shirt1':  ( 20,  62, 134),
        'shirt2':  ( 20,  62, 134),
        'shorts':  ( 20,  62, 134),
        'socks':   ( 20,  62, 134),
        'gk':      (220,  80,   0),
        'skin':    SKIN_MED, 'hair': HAIR_MED,
        'num_col': (255, 255, 255),
        'hud_col': ( 20,  62, 134),
    },

    'los_rojillos': {
        'name':    'Los Rojillos CF',       # Osasuna
        'country': 'Spain',
        'shirt1':  (180,  20,  30),
        'shirt2':  (  0,   0,   0),
        'shorts':  (  0,   0,   0),
        'socks':   (180,  20,  30),
        'gk':      (  0, 160, 220),
        'skin':    SKIN_LIGHT, 'hair': HAIR_DARK,
        'num_col': (255, 255, 255),
        'hud_col': (180,  20,  30),
        'stripe':  True,
        'stripe_cols': [(180, 20, 30), (0, 0, 0), (180, 20, 30)],
    },

    'periquitos': {
        'name':    'Periquitos FC',         # Espanyol
        'country': 'Spain',
        'shirt1':  ( 40,  80, 160),
        'shirt2':  (255, 255, 255),
        'shorts':  (  0,   0,   0),
        'socks':   ( 40,  80, 160),
        'gk':      (  0, 180,  80),
        'skin':    SKIN_OLIVE, 'hair': HAIR_BLACK,
        'num_col': (255, 255, 255),
        'hud_col': ( 40,  80, 160),
        'stripe':  True,
        'stripe_cols': [(40, 80, 160), (255, 255, 255), (40, 80, 160)],
    },

    'los_leones': {
        'name':    'Los Leones AC',         # Athletic Club
        'country': 'Spain',
        'shirt1':  (210,  20,  30),
        'shirt2':  (255, 255, 255),
        'shorts':  (  0,   0,   0),
        'socks':   (  0,   0,   0),
        'gk':      (200, 200,   0),
        'skin':    SKIN_LIGHT, 'hair': HAIR_DARK,
        'num_col': (255, 255, 255),
        'hud_col': (210,  20,  30),
        'stripe':  True,
        'stripe_cols': [(210, 20, 30), (255, 255, 255), (210, 20, 30)],
    },

    'montilivi': {
        'name':    'FC Montilivi',          # Girona
        'country': 'Spain',
        'shirt1':  (190,   0,  30),
        'shirt2':  (255, 255, 255),
        'shorts':  (255, 255, 255),
        'socks':   (190,   0,  30),
        'gk':      ( 80, 200, 120),
        'skin':    SKIN_OLIVE, 'hair': HAIR_BLACK,
        'num_col': ( 20,  20,  20),
        'hud_col': (190,   0,  30),
        'half_half': True,
    },

    'franjirrojos': {
        'name':    'Franjirrojos FC',       # Rayo Vallecano
        'country': 'Spain',
        'shirt1':  (255, 255, 255),
        'shirt2':  (200,  20,  30),
        'shorts':  (255, 255, 255),
        'socks':   (255, 255, 255),
        'gk':      (220, 180,   0),
        'skin':    SKIN_LIGHT, 'hair': HAIR_DARK,
        'num_col': ( 20,  20,  20),
        'hud_col': (200,  20,  30),
        'sash':    True,
    },

    'los_ches': {
        'name':    'Los Ches CF',           # Valencia
        'country': 'Spain',
        'shirt1':  (255, 255, 255),
        'shirt2':  (  0,   0,   0),
        'shorts':  (  0,   0,   0),
        'socks':   (  0,   0,   0),
        'gk':      (220, 120,   0),
        'skin':    SKIN_OLIVE, 'hair': HAIR_BLACK,
        'num_col': ( 20,  20,  20),
        'hud_col': (200, 200, 200),
    },

    'babazorros': {
        'name':    'FC Babazorros',         # Alavés
        'country': 'Spain',
        'shirt1':  (  0,  40, 130),
        'shirt2':  (255, 255, 255),
        'shorts':  (255, 255, 255),
        'socks':   (  0,  40, 130),
        'gk':      (220,  50,   0),
        'skin':    SKIN_LIGHT, 'hair': HAIR_DARK,
        'num_col': (255, 255, 255),
        'hud_col': (  0,  40, 130),
        'stripe':  True,
        'stripe_cols': [(0, 40, 130), (255, 255, 255), (0, 40, 130)],
    },

    'vermells': {
        'name':    'FC Vermells',           # Mallorca
        'country': 'Spain',
        'shirt1':  (210,  20,  40),
        'shirt2':  (  0,   0,   0),
        'shorts':  (  0,   0,   0),
        'socks':   (  0,   0,   0),
        'gk':      (  0, 180, 180),
        'skin':    SKIN_OLIVE, 'hair': HAIR_BLACK,
        'num_col': (255, 255, 255),
        'hud_col': (210,  20,  40),
    },

    'nervionenses': {
        'name':    'Club Nervionenses',     # Sevilla
        'country': 'Spain',
        'shirt1':  (255, 255, 255),
        'shirt2':  (255, 255, 255),
        'shorts':  (255, 255, 255),
        'socks':   (255, 255, 255),
        'gk':      (200,  20,  30),
        'skin':    SKIN_OLIVE, 'hair': HAIR_BLACK,
        'num_col': ( 20,  20,  20),
        'hud_col': (210, 210, 210),
        'gold_border': True,
    },

    'fc_ilicitano': {
        'name':    'FC Ilicitano',          # Elche
        'country': 'Spain',
        'shirt1':  ( 20,  20,  20),
        'shirt2':  (255, 255, 255),
        'shorts':  ( 20,  20,  20),
        'socks':   ( 20,  20,  20),
        'gk':      (  0, 160, 220),
        'skin':    SKIN_OLIVE, 'hair': HAIR_BLACK,
        'num_col': (255, 255, 255),
        'hud_col': ( 80,  80,  80),
        'half_half': True,
    },

    'granotes': {
        'name':    'FC Granotes',           # Levante
        'country': 'Spain',
        'shirt1':  ( 40,  90, 180),
        'shirt2':  (180,  20,  30),
        'shorts':  ( 40,  90, 180),
        'socks':   ( 40,  90, 180),
        'gk':      (  0, 180,  90),
        'skin':    SKIN_OLIVE, 'hair': HAIR_BLACK,
        'num_col': (255, 255, 255),
        'hud_col': ( 40,  90, 180),
        'stripe':  True,
        'stripe_cols': [(40, 90, 180), (180, 20, 30), (40, 90, 180)],
    },

    'carbayones': {
        'name':    'FC Carbayones',         # Real Oviedo
        'country': 'Spain',
        'shirt1':  ( 20,  90, 180),
        'shirt2':  ( 20,  90, 180),
        'shorts':  (  0,   0,   0),
        'socks':   ( 20,  90, 180),
        'gk':      (220, 180,   0),
        'skin':    SKIN_LIGHT, 'hair': HAIR_DARK,
        'num_col': (255, 255, 255),
        'hud_col': ( 20,  90, 180),
    },

    # ══════════════════════════════════════════════════════════
    # ITALY  — Serie A 2024-25  (20 clubs)
    # ══════════════════════════════════════════════════════════

    'inter': {
        'name':    'Internazionale',
        'country': 'Italy',
        'shirt1':  (  0,  60, 120),  # navy blue
        'shirt2':  (  0,  60, 120),
        'shorts':  (  0,  60, 120),
        'socks':   (  0,  60, 120),
        'gk':      (255, 200,   0),
        'skin':    SKIN_OLIVE, 'hair': HAIR_BLACK,
        'num_col': (255, 255, 255),
        'hud_col': (  0,  60, 120),
        'stripe': True,
        'stripe_cols': [(0,60,120),(255,255,255),(0,60,120)],
    },

    'napoli': {
        'name':    'Napoli',
        'country': 'Italy',
        'shirt1':  (  0, 155, 218),  # sky blue
        'shirt2':  (  0, 155, 218),
        'shorts':  (  0, 155, 218),
        'socks':   (  0, 155, 218),
        'gk':      (255, 140,   0),
        'skin':    SKIN_OLIVE, 'hair': HAIR_BLACK,
        'num_col': (255, 255, 255),
        'hud_col': (  0, 155, 218),
    },

    'ac_milan': {
        'name':    'AC Milan',
        'country': 'Italy',
        'shirt1':  (200,  15,  15),
        'shirt2':  (200,  15,  15),
        'shorts':  ( 10,  10,  10),
        'socks':   (200,  15,  15),
        'gk':      (  0, 180, 120),
        'skin':    SKIN_OLIVE, 'hair': HAIR_BLACK,
        'num_col': (255, 255, 255),
        'hud_col': (200,  15,  15),
        'stripe': True,
        'stripe_cols': [(200,15,15),(0,0,0),(200,15,15)],
    },

    'as_roma': {
        'name':    'AS Roma',
        'country': 'Italy',
        'shirt1':  (160,  30,  30),  # dark red
        'shirt2':  (255, 165,   0),
        'shorts':  (255, 165,   0),
        'socks':   (160,  30,  30),
        'gk':      (  0, 180, 220),
        'skin':    SKIN_OLIVE, 'hair': HAIR_DARK,
        'num_col': (255, 255, 255),
        'hud_col': (160,  30,  30),
    },

    'como': {
        'name':    'Como',
        'country': 'Italy',
        'shirt1':  (  0,  30,  80),
        'shirt2':  (255, 255, 255),
        'shorts':  (  0,  30,  80),
        'socks':   (  0,  30,  80),
        'gk':      (255, 180,   0),
        'skin':    SKIN_LIGHT, 'hair': HAIR_MED,
        'num_col': (255, 255, 255),
        'hud_col': (  0,  30,  80),
        'half_half': True,
    },

    'juventus': {
        'name':    'Juventus',
        'country': 'Italy',
        'shirt1':  ( 20,  20,  20),
        'shirt2':  (255, 255, 255),
        'shorts':  ( 20,  20,  20),
        'socks':   ( 20,  20,  20),
        'gk':      (255, 180,   0),
        'skin':    SKIN_LIGHT, 'hair': HAIR_DARK,
        'num_col': (255, 255, 255),
        'hud_col': ( 20,  20,  20),
        'stripe': True,
        'stripe_cols': [(20,20,20),(255,255,255),(20,20,20)],
    },

    'atalanta': {
        'name':    'Atalanta',
        'country': 'Italy',
        'shirt1':  (  0,   0,  80),
        'shirt2':  (  0, 100, 180),
        'shorts':  (  0,   0,  80),
        'socks':   (  0,   0,  80),
        'gk':      (255, 200,   0),
        'skin':    SKIN_OLIVE, 'hair': HAIR_BLACK,
        'num_col': (255, 255, 255),
        'hud_col': (  0,   0,  80),
        'stripe': True,
        'stripe_cols': [(0,0,80),(0,100,180),(0,0,80)],
    },

    'bologna': {
        'name':    'Bologna',
        'country': 'Italy',
        'shirt1':  (140,  20,  20),
        'shirt2':  ( 10,  10,  10),
        'shorts':  ( 10,  10,  10),
        'socks':   (140,  20,  20),
        'gk':      (255, 200,   0),
        'skin':    SKIN_OLIVE, 'hair': HAIR_DARK,
        'num_col': (255, 255, 255),
        'hud_col': (140,  20,  20),
        'half_half': True,
    },

    'lazio': {
        'name':    'Lazio',
        'country': 'Italy',
        'shirt1':  (135, 195, 220),  # light blue
        'shirt2':  (255, 255, 255),
        'shorts':  (255, 255, 255),
        'socks':   (135, 195, 220),
        'gk':      (  0, 180,  60),
        'skin':    SKIN_OLIVE, 'hair': HAIR_DARK,
        'num_col': (  0,  70, 140),
        'hud_col': (135, 195, 220),
    },

    'udinese': {
        'name':    'Udinese',
        'country': 'Italy',
        'shirt1':  ( 10,  10,  10),
        'shirt2':  (255, 255, 255),
        'shorts':  (255, 255, 255),
        'socks':   ( 10,  10,  10),
        'gk':      (255, 150,   0),
        'skin':    SKIN_LIGHT, 'hair': HAIR_MED,
        'num_col': (255, 255, 255),
        'hud_col': ( 10,  10,  10),
        'stripe': True,
        'stripe_cols': [(10,10,10),(255,255,255),(10,10,10)],
    },

    'sassuolo': {
        'name':    'Sassuolo',
        'country': 'Italy',
        'shirt1':  ( 20, 100,  40),
        'shirt2':  (  0,   0,   0),
        'shorts':  (  0,   0,   0),
        'socks':   ( 20, 100,  40),
        'gk':      (255, 180,   0),
        'skin':    SKIN_OLIVE, 'hair': HAIR_BLACK,
        'num_col': (255, 255, 255),
        'hud_col': ( 20, 100,  40),
        'stripe': True,
        'stripe_cols': [(20,100,40),(0,0,0),(20,100,40)],
    },

    'torino': {
        'name':    'Torino',
        'country': 'Italy',
        'shirt1':  (140,  40,  20),  # dark maroon
        'shirt2':  (140,  40,  20),
        'shorts':  ( 10,  10,  10),
        'socks':   (140,  40,  20),
        'gk':      (  0, 160, 220),
        'skin':    SKIN_OLIVE, 'hair': HAIR_DARK,
        'num_col': (255, 255, 255),
        'hud_col': (140,  40,  20),
    },

    'parma': {
        'name':    'Parma',
        'country': 'Italy',
        'shirt1':  (255, 220,   0),
        'shirt2':  (  0,  60, 130),
        'shorts':  (255, 220,   0),
        'socks':   (255, 220,   0),
        'gk':      (  0, 160,  80),
        'skin':    SKIN_LIGHT, 'hair': HAIR_MED,
        'num_col': (  0,  60, 130),
        'hud_col': (255, 220,   0),
        'stripe': True,
        'stripe_cols': [(255,220,0),(0,60,130),(255,220,0)],
    },

    'genoa': {
        'name':    'Genoa',
        'country': 'Italy',
        'shirt1':  (180,  15,  15),
        'shirt2':  (  0,  50, 120),
        'shorts':  (  0,  50, 120),
        'socks':   (180,  15,  15),
        'gk':      (255, 200,   0),
        'skin':    SKIN_OLIVE, 'hair': HAIR_DARK,
        'num_col': (255, 255, 255),
        'hud_col': (180,  15,  15),
        'stripe': True,
        'stripe_cols': [(180,15,15),(0,50,120),(180,15,15)],
    },

    'fiorentina': {
        'name':    'Fiorentina',
        'country': 'Italy',
        'shirt1':  ( 80,  30, 160),  # purple
        'shirt2':  ( 80,  30, 160),
        'shorts':  ( 80,  30, 160),
        'socks':   ( 80,  30, 160),
        'gk':      (255, 200,   0),
        'skin':    SKIN_OLIVE, 'hair': HAIR_BLACK,
        'num_col': (255, 255, 255),
        'hud_col': ( 80,  30, 160),
    },

    'cagliari': {
        'name':    'Cagliari',
        'country': 'Italy',
        'shirt1':  (180,  10,  30),
        'shirt2':  (  0,  50, 120),
        'shorts':  (  0,  50, 120),
        'socks':   (180,  10,  30),
        'gk':      (255, 180,   0),
        'skin':    SKIN_OLIVE, 'hair': HAIR_DARK,
        'num_col': (255, 255, 255),
        'hud_col': (180,  10,  30),
        'half_half': True,
    },

    'lecce': {
        'name':    'Lecce',
        'country': 'Italy',
        'shirt1':  (255, 220,   0),
        'shirt2':  (160,  10,  10),
        'shorts':  (160,  10,  10),
        'socks':   (255, 220,   0),
        'gk':      (  0, 160,  80),
        'skin':    SKIN_OLIVE, 'hair': HAIR_BLACK,
        'num_col': (160,  10,  10),
        'hud_col': (255, 220,   0),
        'stripe': True,
        'stripe_cols': [(255,220,0),(160,10,10),(255,220,0)],
    },

    'cremonese': {
        'name':    'Cremonese',
        'country': 'Italy',
        'shirt1':  (200,  15,  15),
        'shirt2':  (255, 255, 255),
        'shorts':  (200,  15,  15),
        'socks':   (200,  15,  15),
        'gk':      (  0, 180, 220),
        'skin':    SKIN_LIGHT, 'hair': HAIR_MED,
        'num_col': (255, 255, 255),
        'hud_col': (200,  15,  15),
        'stripe': True,
        'stripe_cols': [(200,15,15),(255,255,255),(200,15,15)],
    },

    'hellas_verona': {
        'name':    'Hellas Verona',
        'country': 'Italy',
        'shirt1':  (  0,  60, 140),
        'shirt2':  (255, 220,   0),
        'shorts':  (  0,  60, 140),
        'socks':   (  0,  60, 140),
        'gk':      (  0, 180,  60),
        'skin':    SKIN_OLIVE, 'hair': HAIR_DARK,
        'num_col': (255, 255, 255),
        'hud_col': (  0,  60, 140),
        'stripe': True,
        'stripe_cols': [(0,60,140),(255,220,0),(0,60,140)],
    },

    'pisa': {
        'name':    'Pisa',
        'country': 'Italy',
        'shirt1':  (  0,  40, 120),
        'shirt2':  (  0,  40, 120),
        'shorts':  (  0,  40, 120),
        'socks':   (  0,  40, 120),
        'gk':      (255, 200,   0),
        'skin':    SKIN_LIGHT, 'hair': HAIR_DARK,
        'num_col': (255, 255, 255),
        'hud_col': (  0,  40, 120),
    },

    # ══════════════════════════════════════════════════════════
    # PORTUGAL  — Primeira Liga 2024-25  (18 clubs)
    # ══════════════════════════════════════════════════════════

    'porto': {
        'name':    'Porto',
        'country': 'Portugal',
        'shirt1':  ( 10,  10,  10),  # traditional blue/white — wearing blue
        'shirt2':  (  0,  70, 160),
        'shorts':  (  0,  70, 160),
        'socks':   (  0,  70, 160),
        'gk':      (255, 210,   0),
        'skin':    SKIN_OLIVE, 'hair': HAIR_BLACK,
        'num_col': (255, 255, 255),
        'hud_col': (  0,  70, 160),
        'stripe': True,
        'stripe_cols': [(0,70,160),(255,255,255),(0,70,160)],
    },

    'sporting_cp': {
        'name':    'Sporting CP',
        'country': 'Portugal',
        'shirt1':  ( 20, 130,  40),
        'shirt2':  (255, 255, 255),
        'shorts':  ( 20, 130,  40),
        'socks':   ( 20, 130,  40),
        'gk':      (255, 180,   0),
        'skin':    SKIN_OLIVE, 'hair': HAIR_DARK,
        'num_col': (255, 255, 255),
        'hud_col': ( 20, 130,  40),
    },

    'benfica': {
        'name':    'Benfica',
        'country': 'Portugal',
        'shirt1':  (195,  15,  15),
        'shirt2':  (195,  15,  15),
        'shorts':  (195,  15,  15),
        'socks':   (195,  15,  15),
        'gk':      (  0, 180, 220),
        'skin':    SKIN_OLIVE, 'hair': HAIR_BLACK,
        'num_col': (255, 255, 255),
        'hud_col': (195,  15,  15),
    },

    'braga': {
        'name':    'Braga',
        'country': 'Portugal',
        'shirt1':  (180,  10,  10),
        'shirt2':  (255, 255, 255),
        'shorts':  (255, 255, 255),
        'socks':   (180,  10,  10),
        'gk':      (255, 200,   0),
        'skin':    SKIN_OLIVE, 'hair': HAIR_DARK,
        'num_col': (255, 255, 255),
        'hud_col': (180,  10,  10),
        'stripe': True,
        'stripe_cols': [(180,10,10),(255,255,255),(180,10,10)],
    },

    'famalicao': {
        'name':    'Famalicão',
        'country': 'Portugal',
        'shirt1':  (  0,  60, 130),
        'shirt2':  (255, 255, 255),
        'shorts':  (  0,  60, 130),
        'socks':   (  0,  60, 130),
        'gk':      (255, 180,   0),
        'skin':    SKIN_OLIVE, 'hair': HAIR_DARK,
        'num_col': (255, 255, 255),
        'hud_col': (  0,  60, 130),
        'stripe': True,
        'stripe_cols': [(0,60,130),(255,255,255),(0,60,130)],
    },

    'gil_vicente': {
        'name':    'Gil Vicente',
        'country': 'Portugal',
        'shirt1':  (  0, 100, 180),
        'shirt2':  (255, 255, 255),
        'shorts':  (  0, 100, 180),
        'socks':   (  0, 100, 180),
        'gk':      (255, 200,   0),
        'skin':    SKIN_LIGHT, 'hair': HAIR_MED,
        'num_col': (255, 255, 255),
        'hud_col': (  0, 100, 180),
        'half_half': True,
    },

    'moreirense': {
        'name':    'Moreirense',
        'country': 'Portugal',
        'shirt1':  ( 20, 100,  40),
        'shirt2':  (255, 255, 255),
        'shorts':  (255, 255, 255),
        'socks':   ( 20, 100,  40),
        'gk':      (  0, 180, 220),
        'skin':    SKIN_OLIVE, 'hair': HAIR_DARK,
        'num_col': (255, 255, 255),
        'hud_col': ( 20, 100,  40),
    },

    'arouca': {
        'name':    'Arouca',
        'country': 'Portugal',
        'shirt1':  (255, 200,   0),
        'shirt2':  (  0,  50, 120),
        'shorts':  (255, 200,   0),
        'socks':   (  0,  50, 120),
        'gk':      (200,  15,  15),
        'skin':    SKIN_OLIVE, 'hair': HAIR_BLACK,
        'num_col': (  0,  50, 120),
        'hud_col': (255, 200,   0),
    },

    'vitoria_sc': {
        'name':    'Vitória SC',
        'country': 'Portugal',
        'shirt1':  (255, 225,   0),
        'shirt2':  (  0,  80,  20),
        'shorts':  (255, 225,   0),
        'socks':   (255, 225,   0),
        'gk':      (  0, 160, 220),
        'skin':    SKIN_OLIVE, 'hair': HAIR_DARK,
        'num_col': (  0,  80,  20),
        'hud_col': (255, 225,   0),
        'stripe': True,
        'stripe_cols': [(255,225,0),(0,80,20),(255,225,0)],
    },

    'estoril': {
        'name':    'Estoril Praia',
        'country': 'Portugal',
        'shirt1':  (255, 220,   0),
        'shirt2':  (255, 220,   0),
        'shorts':  ( 10,  10,  10),
        'socks':   (255, 220,   0),
        'gk':      (200,  15,  15),
        'skin':    SKIN_OLIVE, 'hair': HAIR_DARK,
        'num_col': (  0,   0,   0),
        'hud_col': (255, 220,   0),
    },

    'alverca': {
        'name':    'Alverca',
        'country': 'Portugal',
        'shirt1':  (255,  80,  10),
        'shirt2':  (  0,  50, 120),
        'shorts':  (  0,  50, 120),
        'socks':   (255,  80,  10),
        'gk':      (  0, 180,  80),
        'skin':    SKIN_OLIVE, 'hair': HAIR_BLACK,
        'num_col': (255, 255, 255),
        'hud_col': (255,  80,  10),
        'stripe': True,
        'stripe_cols': [(255,80,10),(0,50,120),(255,80,10)],
    },

    'rio_ave': {
        'name':    'Rio Ave',
        'country': 'Portugal',
        'shirt1':  ( 50, 160,  70),
        'shirt2':  (255, 255, 255),
        'shorts':  ( 50, 160,  70),
        'socks':   ( 50, 160,  70),
        'gk':      (255, 200,   0),
        'skin':    SKIN_LIGHT, 'hair': HAIR_MED,
        'num_col': (255, 255, 255),
        'hud_col': ( 50, 160,  70),
        'stripe': True,
        'stripe_cols': [(50,160,70),(255,255,255),(50,160,70)],
    },

    'santa_clara': {
        'name':    'Santa Clara',
        'country': 'Portugal',
        'shirt1':  (180,  15,  15),
        'shirt2':  (  0,   0,   0),
        'shorts':  (180,  15,  15),
        'socks':   (180,  15,  15),
        'gk':      (255, 200,   0),
        'skin':    SKIN_OLIVE, 'hair': HAIR_DARK,
        'num_col': (255, 255, 255),
        'hud_col': (180,  15,  15),
        'stripe': True,
        'stripe_cols': [(180,15,15),(0,0,0),(180,15,15)],
    },

    'nacional': {
        'name':    'Nacional',
        'country': 'Portugal',
        'shirt1':  (  0,  50, 120),
        'shirt2':  (255, 255, 255),
        'shorts':  ( 10,  10,  10),
        'socks':   (  0,  50, 120),
        'gk':      (255, 180,   0),
        'skin':    SKIN_OLIVE, 'hair': HAIR_BLACK,
        'num_col': (255, 255, 255),
        'hud_col': (  0,  50, 120),
        'stripe': True,
        'stripe_cols': [(0,50,120),(255,255,255),(0,50,120)],
    },

    'estrela_amadora': {
        'name':    'Estrela Amadora',
        'country': 'Portugal',
        'shirt1':  (200,  15,  15),
        'shirt2':  (255, 220,   0),
        'shorts':  (200,  15,  15),
        'socks':   (200,  15,  15),
        'gk':      (  0, 180, 220),
        'skin':    SKIN_OLIVE, 'hair': HAIR_DARK,
        'num_col': (255, 255, 255),
        'hud_col': (200,  15,  15),
        'stripe': True,
        'stripe_cols': [(200,15,15),(255,220,0),(200,15,15)],
    },

    'casa_pia': {
        'name':    'Casa Pia',
        'country': 'Portugal',
        'shirt1':  (  0,  80, 170),
        'shirt2':  (255, 255, 255),
        'shorts':  (  0,  80, 170),
        'socks':   (  0,  80, 170),
        'gk':      (255, 180,   0),
        'skin':    SKIN_OLIVE, 'hair': HAIR_DARK,
        'num_col': (255, 255, 255),
        'hud_col': (  0,  80, 170),
    },

    'tondela': {
        'name':    'Tondela',
        'country': 'Portugal',
        'shirt1':  (255, 200,   0),
        'shirt2':  (  0,   0,   0),
        'shorts':  (  0,   0,   0),
        'socks':   (255, 200,   0),
        'gk':      (  0, 160, 220),
        'skin':    SKIN_LIGHT, 'hair': HAIR_MED,
        'num_col': (  0,   0,   0),
        'hud_col': (255, 200,   0),
        'stripe': True,
        'stripe_cols': [(255,200,0),(0,0,0),(255,200,0)],
    },

    'avs': {
        'name':    'AVS',
        'country': 'Portugal',
        'shirt1':  (  0, 120, 200),
        'shirt2':  (255, 255, 255),
        'shorts':  (  0, 120, 200),
        'socks':   (  0, 120, 200),
        'gk':      (255, 200,   0),
        'skin':    SKIN_OLIVE, 'hair': HAIR_BLACK,
        'num_col': (255, 255, 255),
        'hud_col': (  0, 120, 200),
    },
}

# ── Formation 4-3-3 ──────────────────────────────────────────────
FORM = [
    (0.055, 0.50),  # 0  GK
    (0.22,  0.13),  # 1  LB
    (0.22,  0.37),  # 2  CB
    (0.22,  0.63),  # 3  CB
    (0.22,  0.87),  # 4  RB
    (0.46,  0.20),  # 5  LM
    (0.46,  0.50),  # 6  CM
    (0.46,  0.80),  # 7  RM
    (0.72,  0.15),  # 8  LW
    (0.72,  0.50),  # 9  ST
    (0.72,  0.85),  # 10 RW
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


# ── Team star ratings 1-5 ────────────────────────────────────────
# 5=elite  4=top-six  3=mid-table  2=lower-table  1=relegation
TEAM_STARS = {
    # Spain
    'fc_blaugrana':5,'los_blancos':5,'colchoneros':4,'nervionenses':4,
    'la_real':4,'los_leones':3,'los_verdiblancos':3,'los_ches':3,
    'azulones':3,'babazorros':3,'carbayones':2,'franjirrojos':2,
    'granotes':2,'montilivi':2,'fc_rot':2,'fc_ilicitano':2,
    'los_rojillos':2,'los_celestes':2,'periquitos':2,'sky_blues':4,
    # England
    'the_reds':5,'red_devils':4,'the_blues':4,'the_spurs':4,
    'the_gunners':5,'the_villans':4,'the_magpies':4,'the_hammers':3,
    'the_wolves':3,'the_cottagers':3,'the_bees':3,'the_seagulls':3,
    'the_eagles':3,'the_whites':3,'the_toffees':2,'the_clarets':2,
    'the_cherries':2,'the_tricky_trees':2,'the_black_cats':2,
    # Germany
    'die_nullfunfer':5,'die_werkself':5,'die_borussen':4,'die_bullen':4,
    'die_adler':3,'die_wolfe':4,'die_fohlen':3,'die_breisgauer':3,
    'die_eisernen':3,'die_kraichgauer':2,'die_schwaben':2,'die_storche':2,
    'die_dinos':2,'die_fuggerstadter':2,'die_geissböcke':2,'die_kieze':2,
    'die_werderaner':3,
    # Italy
    'inter':5,'napoli':5,'ac_milan':5,'juventus':5,'atalanta':4,
    'as_roma':4,'lazio':4,'fiorentina':3,'bologna':3,'torino':3,
    'udinese':2,'sassuolo':2,'parma':2,'genoa':2,'como':3,
    'cagliari':2,'lecce':2,'cremonese':1,'hellas_verona':2,'pisa':1,
    # Portugal
    'porto':5,'sporting_cp':5,'benfica':5,'braga':4,'famalicao':3,
    'vitoria_sc':3,'gil_vicente':2,'moreirense':2,'arouca':2,
    'estoril':2,'rio_ave':2,'santa_clara':2,'nacional':2,'alverca':2,
    'estrela_amadora':1,'casa_pia':1,'tondela':1,'avs':1,
    # Spain (additional)
    'yellow_submarine':3,'vermells':2,
}

def get_stars(key):
    """Return star rating 1-5 (default 2)."""
    return TEAM_STARS.get(key, 2)

def ai_params(stars):
    """
    Return AI behaviour dict scaled by stars 1-5.
    Higher stars = faster, smarter, more aggressive.
    """
    t = (max(1,min(5,stars)) - 1) / 4.0
    return {
        'walk':        1.40 + t*0.90,   # 1.40-2.30
        'jog':         2.10 + t*1.10,   # 2.10-3.20
        'run':         2.80 + t*1.20,   # 2.80-4.00
        'sprint':      3.40 + t*1.00,   # 3.40-4.40
        'react':       int(70-t*40),     # 70-30 frames
        'press_r':     60   + t*100,     # 60-160
        'shoot_r':     160  + t*180,     # 160-340
        'pass_chance': 0.010+t*0.030,    # 0.010-0.040
        'shoot_chance':0.012+t*0.025,    # 0.012-0.037
        'tackle_prob': 0.006+t*0.016,    # 0.006-0.022
        'inaccuracy':  0.30 -t*0.22,     # 0.30-0.08
        'cross_chance':0.012+t*0.025,
    }
