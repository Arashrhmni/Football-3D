"""ai.py – All AI logic, star-rating aware."""
import math
import random
from constants import (
    W_W, W_H, W_MX, W_MY, GOAL_TOP, GOAL_BOT,
    PASS_SPD, CROSS_SPD, SHOOT_SPD, CONTROL_R, TACKLE_R,
    AI_WALK, AI_JOG, AI_RUN, AI_REACT,
    d2, n2, clamp,
)

# ── Default AI param dict (used when no star override is given) ───
_DEFAULT = {
    'walk': AI_WALK, 'jog': AI_JOG, 'run': AI_RUN, 'sprint': AI_RUN,
    'react': AI_REACT, 'press_r': 90, 'shoot_r': 230,
    'pass_chance': 0.022, 'shoot_chance': 0.022,
    'tackle_prob': 0.012, 'inaccuracy': 0.18, 'cross_chance': 0.020,
}


# ── Direction helpers ─────────────────────────────────────────────
def _team_attacks_right(team): return team[0].home_x < W_MX
def _team_goal_x(team):        return float(W_W) if _team_attacks_right(team) else 0.0
def _own_goal_x(team):         return 0.0 if _team_attacks_right(team) else float(W_W)


# ── Pass scoring ──────────────────────────────────────────────────
def best_pass_target(carrier, team, opponents):
    """Best teammate to pass to: forward, open, reasonable distance."""
    mates = [p for p in team if p is not carrier and not p.is_keeper]
    if not mates:
        return None
    attack_right = _team_attacks_right(team)
    scored = []
    for p in mates:
        dd  = d2((carrier.wx, carrier.wy), (p.wx, p.wy))
        fwd = (p.wx - carrier.wx) if attack_right else (carrier.wx - p.wx)
        opp_d = min((d2((q.wx,q.wy),(p.wx,p.wy)) for q in opponents), default=999)
        if opp_d < 24:
            continue
        scored.append((fwd*1.4 + opp_d*0.30 - dd*0.06, p))
    if not scored:
        return min(mates, key=lambda p: d2((carrier.wx,carrier.wy),(p.wx,p.wy)))
    return max(scored, key=lambda x: x[0])[1]


# ── Keeper ────────────────────────────────────────────────────────
def keeper_ai(keeper, goal_x, is_left, ball, p=None):
    ap = p or _DEFAULT
    coming = False
    if ball.owner is None and ball.spd() > 0.9:
        fx = ball.wx + ball.vx * 26
        coming = (fx < W_MX) if is_left else (fx > W_MX)
    if coming and abs(ball.vx) > 0.15:
        t2 = (goal_x - ball.wx) / ball.vx
        if 0 < t2 < 65:
            iy  = clamp(ball.wy + ball.vy*t2, GOAL_TOP+3, GOAL_BOT-3)
            out = 38 if is_left else -38
            keeper.move_toward(goal_x+out, iy, ap['jog']*1.3)
            return
    ky = clamp(ball.wy, GOAL_TOP+22, GOAL_BOT-22)
    in_half = (ball.wx < W_MX) if is_left else (ball.wx > W_MX)
    if is_left:
        kx = clamp(28+(ball.wx*0.055 if in_half else 0), 20, 82)
    else:
        kx = clamp(W_W-28-((W_W-ball.wx)*0.055 if in_half else 0), W_W-82, W_W-20)
    keeper.move_toward(kx, ky, ap['walk']*0.88)


# ── Team A support (Barcelona / human team) ───────────────────────
def team_a_support(team_a, sel, ball, p=None):
    ap = p or _DEFAULT
    carrier     = ball.owner
    has_ball_a  = carrier and carrier.team == 'A'
    keeper_ai(team_a[0], 0, is_left=True, ball=ball, p=ap)

    for pl in team_a:
        if pl is sel or pl.is_keeper:
            continue
        if not has_ball_a:
            tx = clamp(pl.home_x, 30, ball.wx-35)
            ty = pl.home_y + (ball.wy-W_MY)*0.12
            pl.move_toward(tx, ty, ap['walk']*0.82)
            continue
        role = pl.num
        if 2 <= role <= 5:
            sx = min(carrier.wx-52, pl.home_x+55); sx = max(sx, pl.home_x)
            ty = pl.home_y + (carrier.wy-W_MY)*0.14
            pl.move_toward(sx, ty, ap['jog']*0.80)
        elif 6 <= role <= 8:
            import math as _m
            ang = _m.radians((role-7)*65+90)
            tx  = clamp(carrier.wx+_m.cos(ang)*95, 55, W_W-55)
            ty  = clamp(carrier.wy+_m.sin(ang)*100, 18, W_H-18)
            pl.move_toward(tx, ty, ap['jog'])
        else:
            channels = [GOAL_TOP+28, W_MY, GOAL_BOT-28]
            ch = channels[role-9]
            rx = clamp(carrier.wx+105, carrier.wx+45, W_W-38)
            ty = clamp(ch+random.uniform(-14,14), 18, W_H-18)
            fast = rx > W_W*0.6
            pl.move_toward(rx, ty, ap['run'] if fast else ap['jog'])


# ── CPU AI entry point ────────────────────────────────────────────
def cpu_ai(team_b, team_a, ball, p=None):
    """Full CPU AI: keeper + outfield, behaviour scaled by ai_params p."""
    ap = p or _DEFAULT
    own_left = team_b[0].home_x < W_MX
    keeper_ai(team_b[0], 0.0 if own_left else float(W_W),
              is_left=own_left, ball=ball, p=ap)

    outfield = team_b[1:]
    ball_b   = ball.owner and ball.owner.team == 'B'
    ball_a   = ball.owner and ball.owner.team == 'A'
    closest  = min(outfield, key=lambda q: d2((q.wx,q.wy),(ball.wx,ball.wy)))

    for pl in outfield:
        if pl.tackle_cd > 0:
            pl.tackle_cd -= 1
        if pl.react > 0:
            pl.react -= 1
            pl.move_toward(pl.home_x, pl.home_y, ap['walk']*0.72)
            continue

        if ball_b and ball.owner is pl:
            _cpu_carry(pl, team_b, team_a, ball, ap)
        elif ball.owner is None:
            _cpu_chase_loose(pl, outfield, ball, ap)
        elif ball_a:
            _cpu_defend(pl, closest, team_b, ball, ap)


def _cpu_chase_loose(pl, outfield, ball, ap):
    dd = d2((pl.wx,pl.wy),(ball.wx,ball.wy))
    if dd < 155:
        pl.move_toward(ball.wx, ball.wy, ap['jog'])
    else:
        pl.move_toward(pl.home_x, pl.home_y, ap['walk'])
    if ball.wz < 12 and dd < CONTROL_R:
        ball.owner = pl; ball.last_toucher = pl
        for q in outfield:
            q.react = random.randint(6, ap['react']//2)


def _cpu_carry(carrier, team_b, team_a, ball, ap):
    """Ball-carrier: shoot, cross, pass, or dribble — scaled by stars."""
    outfield  = team_b[1:]
    goal_x    = _team_goal_x(team_b)
    d_goal    = d2((carrier.wx,carrier.wy),(goal_x, W_MY))
    pressers  = [q for q in team_a if d2((q.wx,q.wy),(carrier.wx,carrier.wy)) < 68]

    # Shoot
    if d_goal < ap['shoot_r'] and random.random() < ap['shoot_chance']:
        gy = clamp(carrier.wy, GOAL_TOP+12, GOAL_BOT-12) + random.randint(-22,22)
        bx, by = n2(goal_x-carrier.wx, gy-carrier.wy)
        inac = clamp(ap['inaccuracy'] * (d_goal/200), 0.03, 0.32)
        bx += random.uniform(-inac,inac); by += random.uniform(-inac,inac)
        bx, by = n2(bx, by)
        ball.release()
        ball.vx = bx*SHOOT_SPD*0.82; ball.vy = by*SHOOT_SPD*0.82; ball.vz = 4.5
        ball.last_toucher = carrier
        for q in outfield: q.react = random.randint(12,32)
        return

    # Cross from wide positions
    attacks_right = _team_attacks_right(team_b)
    near_byline = (
        (carrier.wx < W_W*0.18 and not attacks_right) or
        (carrier.wx > W_W*0.82 and attacks_right)
    ) and (carrier.wy < W_MY-40 or carrier.wy > W_MY+40)

    if near_byline and random.random() < ap['cross_chance']:
        tgt_y = GOAL_TOP+22 if carrier.wy > W_MY else GOAL_BOT-22
        bx2, by2 = n2(goal_x-carrier.wx, tgt_y-carrier.wy)
        ball.release()
        ball.vx = bx2*CROSS_SPD; ball.vy = by2*CROSS_SPD; ball.vz = 8.5
        ball.last_toucher = carrier
        for q in outfield: q.react = random.randint(6,18)
        return

    # Proactive pass (higher for better teams)
    pass_chance = ap['pass_chance'] if not pressers else ap['pass_chance']*2
    if random.random() < pass_chance:
        tgt = best_pass_target(carrier, team_b, team_a)
        if tgt:
            lead_x = clamp(tgt.wx+tgt.vx*8, 10, W_W-10)
            lead_y = clamp(tgt.wy+tgt.vy*8, 10, W_H-10)
            ball.release()
            dx2,dy2 = n2(lead_x-ball.wx, lead_y-ball.wy)
            ball.vx=dx2*PASS_SPD; ball.vy=dy2*PASS_SPD; ball.vz=2.0
            ball.last_toucher=carrier
            for q in outfield: q.react=random.randint(5,18)
            return

    # Dribble
    dodge=0.
    if pressers:
        avg=sum(q.wy for q in pressers)/len(pressers)
        dodge=30. if carrier.wy<avg else -30.
    target_x = goal_x + (55 if goal_x == 0 else -55)
    carrier.move_toward(target_x, W_MY+dodge, ap['run'])


def _cpu_defend(pl, closest, team_b, ball, ap):
    """Defending: one presser, others hold shape — proportional to stars."""
    role = pl.num
    dd   = d2((pl.wx,pl.wy),(ball.wx,ball.wy))

    if pl is closest:
        if dd < ap['press_r']:
            pl.move_toward(ball.wx, ball.wy, ap['jog'])
            # Tackle attempt
            if dd < TACKLE_R and pl.tackle_cd == 0 and random.random() < ap['tackle_prob']:
                if ball.owner:
                    prev=ball.owner; ball.release()
                    bx2,by2=n2(pl.wx-prev.wx, pl.wy-prev.wy)
                    ball.vx=bx2*3.2+random.uniform(-1,1)
                    ball.vy=by2*3.2+random.uniform(-1,1)
                    ball.last_toucher=pl; pl.tackle_cd=55
        else:
            pl.move_toward((pl.home_x+ball.wx*0.55)/1.55,
                           (pl.home_y+ball.wy*0.55)/1.55, ap['walk'])
    elif 2 <= role <= 5:
        lx = clamp((ball.wx+W_W)*0.50, pl.home_x, W_W-38)
        ly = pl.home_y+(ball.wy-W_MY)*0.20
        pl.move_toward(lx, ly, ap['walk'])
    elif 6 <= role <= 8:
        mx = max(pl.home_x, W_W-W_W*0.58)
        my = pl.home_y+(ball.wy-W_MY)*0.18
        pl.move_toward(mx, my, ap['walk']*0.88)
    else:
        px = clamp(ball.wx+55, W_MX, W_W-48)
        py = pl.home_y+(ball.wy-W_MY)*0.16
        pl.move_toward(px, py, ap['jog']*0.78)


def cpu_attacking_shape(team_b, ball, p=None):
    """When CPU has the ball, teammates make intelligent runs."""
    ap = p or _DEFAULT
    carrier = ball.owner
    if not (carrier and carrier.team == 'B'):
        return
    for pl in team_b:
        if pl is carrier or pl.is_keeper:
            continue
        role = pl.num
        if 2 <= role <= 4:
            tx = max(pl.home_x-30, W_W*0.62)
            ty = pl.home_y+(carrier.wy-W_MY)*0.10
            pl.move_toward(tx, ty, ap['jog']*0.75)
        elif role == 5:
            import math as _m
            tx = clamp(carrier.wx-80, W_W*0.50, W_W*0.80)
            ty = clamp(carrier.wy+(1 if carrier.wy<W_MY else -1)*100, 10, W_H-10)
            pl.move_toward(tx, ty, ap['jog'])
        elif 6 <= role <= 8:
            import math as _m
            ang = _m.radians((role-7)*70+90)
            tx  = clamp(carrier.wx+_m.cos(ang)*120, 20, W_W-20)
            ty  = clamp(carrier.wy+_m.sin(ang)*120*1.2, 10, W_H-10)
            pl.move_toward(tx, ty, ap['jog'])
        else:
            channels = {8: GOAL_TOP-15, 9: W_MY, 10: GOAL_BOT+15}
            ch = clamp(channels.get(role, W_MY), 10, W_H-10)
            goal_x = _team_goal_x(team_b)
            tx = clamp(carrier.wx-(120-(role-9)*30),
                       20, min(carrier.wx-40, W_W*0.45))
            ty = clamp(ch+random.uniform(-12,12), 10, W_H-10)
            pl.move_toward(tx, ty, ap['run'])
