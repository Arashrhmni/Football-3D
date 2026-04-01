"""ai.py – All AI logic for both teams."""
import math
import random
from constants import (
    W_W, W_H, W_MX, W_MY, GOAL_TOP, GOAL_BOT,
    PASS_SPD, CROSS_SPD, SHOOT_SPD, CONTROL_R, TACKLE_R,
    AI_WALK, AI_JOG, AI_RUN, AI_REACT,
    d2, n2, clamp
)


# ── Scoring function: pick best pass target ───────────────────────
def best_pass_target(carrier, team, opponents):
    """
    Return the teammate most worth passing to.
    Scores: forward position, space from opponents, reasonable distance.
    """
    mates = [p for p in team if p is not carrier and not p.is_keeper]
    if not mates:
        return None

    attack_right = (team[0].team == 'A')   # A attacks right
    scored = []
    for p in mates:
        dd  = d2((carrier.wx, carrier.wy), (p.wx, p.wy))
        fwd = (p.wx - carrier.wx) if attack_right else (carrier.wx - p.wx)
        opp_d = min((d2((q.wx,q.wy),(p.wx,p.wy)) for q in opponents), default=999)
        if opp_d < 24:
            continue          # teammate is too closely marked
        score = fwd*1.4 + opp_d*0.30 - dd*0.06
        scored.append((score, p))

    if not scored:
        return min(mates, key=lambda p: d2((carrier.wx,carrier.wy),(p.wx,p.wy)))
    return max(scored, key=lambda x: x[0])[1]


# ── Keeper AI ────────────────────────────────────────────────────
def keeper_ai(keeper, goal_x, is_left, ball):
    """Move keeper: track ball height, rush to intercept incoming shots."""
    coming = False
    if ball.owner is None and ball.spd() > 0.9:
        future_x = ball.wx + ball.vx * 26
        coming = (future_x < W_MX) if is_left else (future_x > W_MX)

    if coming and abs(ball.vx) > 0.15:
        t = (goal_x - ball.wx) / ball.vx
        if 0 < t < 65:
            iy  = clamp(ball.wy + ball.vy * t, GOAL_TOP + 3, GOAL_BOT - 3)
            out = 38 if is_left else -38
            keeper.move_toward(goal_x + out, iy, AI_JOG * 1.3)
            return

    # Default: stay near goal line, track ball Y — gentle lateral movement only
    ky = clamp(ball.wy, GOAL_TOP + 22, GOAL_BOT - 22)
    in_half = (ball.wx < W_MX) if is_left else (ball.wx > W_MX)
    if is_left:
        kx = clamp(28 + (ball.wx * 0.055 if in_half else 0), 20, 82)
    else:
        kx = clamp(W_W - 28 - ((W_W - ball.wx)*0.055 if in_half else 0), W_W-82, W_W-20)
    keeper.move_toward(kx, ky, AI_WALK * 0.88)


# ── Team A (Barcelona) support when human has the ball ───────────
def team_a_support(team_a, sel, ball):
    """When a human carries the ball, Barcelona teammates make runs."""
    carrier = ball.owner
    has_ball_a = carrier and carrier.team == 'A'
    keeper_a = team_a[0]
    keeper_ai(keeper_a, 0, is_left=True, ball=ball)

    for p in team_a:
        if p is sel or p.is_keeper:
            continue
        if not has_ball_a:
            # Hold defensive shape behind ball
            tx = clamp(p.home_x, 30, ball.wx - 35)
            ty = p.home_y + (ball.wy - W_MY) * 0.12
            p.move_toward(tx, ty, AI_WALK * 0.82)
            continue

        role = p.num   # 2-5 defenders, 6-8 midfielders, 9-11 forwards
        if 2 <= role <= 5:
            # Push up slightly but stay behind ball carrier
            sx = min(carrier.wx - 52, p.home_x + 55)
            sx = max(sx, p.home_x)
            ty = p.home_y + (carrier.wy - W_MY) * 0.14
            p.move_toward(sx, ty, AI_JOG * 0.80)

        elif 6 <= role <= 8:
            # Midfielders fan out to form passing triangles
            angle = math.radians((role - 7) * 65 + 90)
            tx = clamp(carrier.wx + math.cos(angle)*95, 55, W_W - 55)
            ty = clamp(carrier.wy + math.sin(angle)*100, 18, W_H - 18)
            p.move_toward(tx, ty, AI_JOG)

        else:
            # Forwards: sprint into channels ahead
            channels = [GOAL_TOP + 28, W_MY, GOAL_BOT - 28]
            ch = channels[role - 9]
            rx = clamp(carrier.wx + 105, carrier.wx + 45, W_W - 38)
            ty = clamp(ch + random.uniform(-14, 14), 18, W_H - 18)
            p.move_toward(rx, ty, AI_RUN if rx > W_W*0.6 else AI_JOG)


# ── CPU (Real Madrid) full AI ─────────────────────────────────────
def cpu_ai(team_b, team_a, ball):
    """Full CPU AI: attacking build-up passing + defending."""
    # Keeper
    keeper_ai(team_b[0], W_W, is_left=False, ball=ball)

    outfield = team_b[1:]
    ball_b = ball.owner and ball.owner.team == 'B'
    ball_a = ball.owner and ball.owner.team == 'A'
    closest = min(outfield, key=lambda p: d2((p.wx,p.wy),(ball.wx,ball.wy)))

    for p in outfield:
        if p.tackle_cd > 0:
            p.tackle_cd -= 1

        # Reaction delay — simulate human latency
        if p.react > 0:
            p.react -= 1
            p.move_toward(p.home_x, p.home_y, AI_WALK * 0.72)
            continue

        if ball_b and ball.owner is p:
            _cpu_carry(p, team_b, team_a, ball)

        elif ball.owner is None:
            _cpu_chase_loose(p, outfield, ball)

        elif ball_a:
            _cpu_defend(p, closest, team_b, ball)


def _cpu_chase_loose(p, outfield, ball):
    dd = d2((p.wx,p.wy),(ball.wx,ball.wy))
    if dd < 155:
        p.move_toward(ball.wx, ball.wy, AI_JOG)
    else:
        p.move_toward(p.home_x, p.home_y, AI_WALK)
    if ball.wz < 12 and dd < CONTROL_R:
        ball.owner = p
        ball.last_toucher = p
        for q in outfield:
            q.react = random.randint(6, AI_REACT // 2)


def _cpu_carry(carrier, team_b, team_a, ball):
    """
    CPU ball-carrier logic:
    1. Pass proactively to a forward teammate (build-up play).
    2. Cross from wide positions.
    3. Shoot when close.
    4. Dribble if nothing else.
    """
    outfield = team_b[1:]
    goal_x  = 0.0
    d_goal  = d2((carrier.wx, carrier.wy), (goal_x, W_MY))
    pressers = [q for q in team_a if d2((q.wx,q.wy),(carrier.wx,carrier.wy)) < 70]

    # ── Shoot when in range ──────────────────────────────────────
    if d_goal < 280 and random.random() < 0.024:
        gy = clamp(carrier.wy, GOAL_TOP+12, GOAL_BOT-12) + random.randint(-22, 22)
        bx, by = n2(goal_x - carrier.wx, gy - carrier.wy)
        inac = clamp(d_goal / 1900, 0.06, 0.24)
        bx += random.uniform(-inac, inac)
        by += random.uniform(-inac, inac)
        bx, by = n2(bx, by)
        ball.release()
        ball.vx = bx * SHOOT_SPD * 0.82
        ball.vy = by * SHOOT_SPD * 0.82
        ball.vz = 4.5
        ball.last_toucher = carrier
        for q in outfield:
            q.react = random.randint(12, 32)
        return

    # ── Cross from wide positions (byline) ───────────────────────
    near_byline = (carrier.wx < W_W*0.18 and
                   (carrier.wy < W_MY-40 or carrier.wy > W_MY+40))
    if near_byline and random.random() < 0.030:
        tgt_y = GOAL_TOP+22 if carrier.wy > W_MY else GOAL_BOT-22
        ball.release()
        dx, dy = n2(0 - carrier.wx, tgt_y - carrier.wy)
        ball.vx = dx * CROSS_SPD
        ball.vy = dy * CROSS_SPD
        ball.vz = 8.5
        ball.last_toucher = carrier
        for q in outfield:
            q.react = random.randint(6, 18)
        return

    # ── Proactive build-up pass (not just under pressure) ────────
    # Pass more often when teammates are in better positions
    # Base pass chance is higher so CPU builds up play
    pass_chance = 0.025 if not pressers else 0.045
    if random.random() < pass_chance:
        tgt = best_pass_target(carrier, team_b, team_a)
        if tgt:
            # Lead the pass slightly ahead of where teammate is moving
            lead_x = tgt.wx + tgt.vx * 8
            lead_y = tgt.wy + tgt.vy * 8
            lead_x = clamp(lead_x, 10, W_W - 10)
            lead_y = clamp(lead_y, 10, W_H - 10)
            ball.release()
            dx, dy = n2(lead_x - ball.wx, lead_y - ball.wy)
            ball.vx = dx * PASS_SPD
            ball.vy = dy * PASS_SPD
            ball.vz = 2.0
            ball.last_toucher = carrier
            for q in outfield:
                q.react = random.randint(5, 18)
            return

    # ── Dribble toward goal with dodge ───────────────────────────
    dodge = 0.0
    if pressers:
        avg_y = sum(q.wy for q in pressers) / len(pressers)
        dodge = 30.0 if carrier.wy < avg_y else -30.0
    carrier.move_toward(goal_x + 55, W_MY + dodge, AI_RUN)


def _cpu_defend(p, closest, team_b, ball):
    """
    CPU defending: soft pressing — one player presses, others hold shape.
    Defenders block lanes, midfielders compact, forwards press lightly.
    """
    role = p.num
    dd   = d2((p.wx,p.wy),(ball.wx,ball.wy))

    if p is closest:
        if dd < 125:
            p.move_toward(ball.wx, ball.wy, AI_JOG)
            # Attempt soft tackle
            if dd < TACKLE_R and p.tackle_cd == 0 and random.random() < 0.010:
                if ball.owner:
                    prev = ball.owner
                    ball.release()
                    bx, by = n2(p.wx - prev.wx, p.wy - prev.wy)
                    ball.vx = bx*3.2 + random.uniform(-1, 1)
                    ball.vy = by*3.2 + random.uniform(-1, 1)
                    ball.last_toucher = p
                    p.tackle_cd = 55
        else:
            # Drift toward midpoint between home and ball
            p.move_toward(
                (p.home_x + ball.wx*0.55) / 1.55,
                (p.home_y + ball.wy*0.55) / 1.55,
                AI_WALK
            )

    elif 2 <= role <= 5:
        # Defenders: position between ball and own goal
        lx = clamp((ball.wx + W_W)*0.50, p.home_x, W_W - 38)
        ly = p.home_y + (ball.wy - W_MY)*0.20
        p.move_toward(lx, ly, AI_WALK)

    elif 6 <= role <= 8:
        # Midfielders: compact second line — don't rush
        mx = max(p.home_x, W_W - W_W*0.58)
        my = p.home_y + (ball.wy - W_MY)*0.18
        p.move_toward(mx, my, AI_WALK * 0.88)

    else:
        # Forwards: press high but not sprinting
        px = clamp(ball.wx + 55, W_MX, W_W - 48)
        py = p.home_y + (ball.wy - W_MY)*0.16
        p.move_toward(px, py, AI_JOG * 0.78)


# ── CPU attacking team-wide movement (called every frame) ────────
def cpu_attacking_shape(team_b, ball):
    """
    When any CPU player has the ball, the rest of the CPU team
    makes intelligent supporting runs — spread wide, push into
    half-spaces, strikers make diagonal runs.
    """
    carrier = ball.owner
    if not (carrier and carrier.team == 'B'):
        return

    for p in team_b:
        if p is carrier or p.is_keeper:
            continue

        role = p.num
        # Defend-side half of team stays back
        if 2 <= role <= 4:
            # Two CDs + one RB/LB stay back as a back-line
            tx = max(p.home_x - 30, W_W * 0.62)
            ty = p.home_y + (carrier.wy - W_MY)*0.10
            p.move_toward(tx, ty, AI_JOG * 0.75)

        elif role == 5:
            # One full-back can overlap
            tx = clamp(carrier.wx - 80, W_W*0.50, W_W*0.80)
            ty = clamp(carrier.wy + (1 if carrier.wy < W_MY else -1)*100,
                       10, W_H-10)
            p.move_toward(tx, ty, AI_JOG)

        elif 6 <= role <= 8:
            # Midfielders: triangle support — spread out around carrier
            angle = math.radians((role - 7)*70 + 90)
            spread = 120
            tx = clamp(carrier.wx + math.cos(angle)*spread, 20, W_W - 20)
            ty = clamp(carrier.wy + math.sin(angle)*spread*1.2, 10, W_H - 10)
            p.move_toward(tx, ty, AI_JOG)

        else:
            # Forwards (8=LW, 9=ST, 10=RW): make runs into attacking third
            channels = {
                8: clamp(GOAL_TOP - 15, 10, W_H-10),   # LW: top channel
                9: W_MY,                                  # ST: central
                10: clamp(GOAL_BOT + 15, 10, W_H-10),   # RW: bottom channel
            }
            ch = channels.get(role, W_MY)
            # Run beyond the ball toward the left goal
            tx = clamp(carrier.wx - 120 + (role-9)*30,
                       20, min(carrier.wx - 40, W_W*0.35))
            ty = clamp(ch + random.uniform(-12, 12), 10, W_H-10)
            p.move_toward(tx, ty, AI_RUN)
