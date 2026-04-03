"""game.py – Main game orchestrator.

Bug fixes in this version
──────────────────────────
1. Kickoff freeze: AI is completely disabled during freeze so no player
   moves at all before the whistle.
2. Goalkeeper with ball: after saving the GK passes to the nearest
   outfield teammate within a few seconds; no more stuck keeper.
3. Throw-in: the player at the spot is forced to pass immediately;
   they cannot dribble with the ball.
4. Shooting: works from anywhere on the pitch at any time by tapping
   F/Shift (instant low-power shot) or holding for a charged shot.
"""

import pygame
import math
import random
import sys

from constants import (
    SCR_W, SCR_H, FPS, W_W, W_H, W_MX, W_MY,
    GOAL_TOP, GOAL_BOT, BALL_R, PLAYER_R,
    PLAYER_SPD, SPRINT_MULT, PASS_SPD, CROSS_SPD, SHOOT_SPD,
    CONTROL_R, TACKLE_R,
    FORM,
    DB_THROW_A, DB_THROW_B, DB_GK_A, DB_GK_B,
    DB_CORNER_A, DB_CORNER_B, DB_KICK_A, DB_KICK_B,
    BAR_BLUE, OUT_L, OUT_R, OUT_T, OUT_B,
    d2, n2, clamp, w2s
)
from ball   import Ball
from player import Player
from pitch  import bake_pitch
from ai     import best_pass_target, team_a_support, cpu_ai, cpu_attacking_shape
from hud    import HUD


class Game:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((SCR_W, SCR_H))
        pygame.display.set_caption("Football 3D — Barcelona vs Real Madrid")
        self.clock  = pygame.time.Clock()
        self.f_num  = pygame.font.SysFont("Arial", 9, bold=True)

        self.score      = [0, 0]
        self.match_time = 0
        self.msgs       = []

        # Dead-ball
        self.dead         = None
        self.dead_pos     = (W_MX, W_MY)
        self.dead_timer   = 0
        self.throw_player = None
        # Throw-in force-pass state
        self.throw_must_pass     = False
        self._throw_pass_thrower = None
        self._throw_pass_timer   = 0

        # Kickoff freeze: all players locked until this reaches 0
        self.kickoff_freeze = FPS * 2   # 2 seconds
        self.kickoff_side   = 'A'

        # Shoot charge
        self.charging     = False
        self.charge       = 0.0
        self._shot_queued = False   # tap-to-shoot flag

        # GK pass timer (fix bug 2)
        self.gk_hold_timer = 0      # frames GK has held the ball

        self.ball = Ball()
        self._build_teams()
        self._kickoff('A')

        self._pitch = bake_pitch()
        self._hud   = HUD(self.screen)

    # ── Team setup ────────────────────────────────────────────────
    def _build_teams(self):
        self.ta, self.tb = [], []
        for i, (rx, ry) in enumerate(FORM):
            hxa = rx * W_W * 0.47
            hxb = W_W - rx * W_W * 0.47
            hy  = ry * W_H
            self.ta.append(Player('A', i+1, hxa, hy, is_keeper=(i==0)))
            self.tb.append(Player('B', i+1, hxb, hy, is_keeper=(i==0)))
        self.sel = self.ta[9]
        self.sel.selected = True

    def _kickoff(self, side):
        """Hard reset for a new kickoff.  Everyone frozen for kickoff_freeze frames."""
        self.dead              = None
        self.charging          = False
        self.charge            = 0.0
        self._shot_queued      = False
        self.throw_player      = None
        self.throw_must_pass   = False
        self._throw_pass_thrower = None
        self._throw_pass_timer   = 0
        self.kickoff_side      = side
        self.kickoff_freeze    = FPS * 2
        self.gk_hold_timer     = 0

        self.ball.reset()
        for p in self.ta + self.tb:
            p.wx, p.wy = p.home_x, p.home_y
            p.vx = p.vy = 0.0

        kicker = self.ta[9] if side == 'A' else self.tb[9]
        kicker.wx = float(W_MX - (12 if side == 'A' else -12))
        kicker.wy = float(W_MY)
        self.ball.owner = kicker
        self.ball.last_toucher = kicker

    def msg(self, txt, col=(255, 255, 255)):
        self.msgs.append([txt, col, 220])

    # ── Draw ──────────────────────────────────────────────────────
    def _draw_scene(self):
        self.screen.blit(self._pitch, (0, 0))
        ents = [(p.wy, 'p', p) for p in self.ta + self.tb]
        ents.append((self.ball.wy, 'b', self.ball))
        ents.sort(key=lambda e: e[0])
        for _, k, o in ents:
            if k == 'p':
                o.draw(self.screen, self.ball, self.f_num)
            else:
                o.draw(self.screen)

        # Pass suggestion line when human has ball
        if (self.ball.owner and self.ball.owner.team == 'A'
                and not self.dead and not self.kickoff_freeze):
            tgt = best_pass_target(self.ball.owner, self.ta, self.tb)
            if tgt:
                s1 = w2s(self.ball.owner.wx, self.ball.owner.wy, 10)
                s2 = w2s(tgt.wx, tgt.wy, 10)
                dx2, dy2 = s2[0]-s1[0], s2[1]-s1[1]
                segs = max(3, int(math.hypot(dx2,dy2)//16))
                for i in range(segs):
                    if i % 2 == 0:
                        t0, t1 = i/segs, (i+0.55)/segs
                        pygame.draw.line(self.screen, (130,255,55),
                            (int(s1[0]+dx2*t0), int(s1[1]+dy2*t0)),
                            (int(s1[0]+dx2*t1), int(s1[1]+dy2*t1)), 2)
                pygame.draw.circle(self.screen, (130,255,55), s2, 9, 2)

    # ── Input: movement + shoot charge ────────────────────────────
    def _handle_input(self):
        """Process held keys every frame. ESC / TAB / SPACE handled in events."""

        # FREEZE: no input at all during kickoff countdown or dead ball
        if self.kickoff_freeze > 0 or self.dead:
            self.charging = False
            self.charge   = 0.0
            return

        # Throw-in active: thrower is locked in place, must only pass
        # (movement keys do nothing for the thrower)
        if self.throw_must_pass:
            # The thrower auto-passes after a short moment; nothing for human to do
            return

        keys = pygame.key.get_pressed()
        spd  = PLAYER_SPD * (SPRINT_MULT if keys[pygame.K_z] else 1.0)
        p    = self.sel

        # Movement
        dx, dy = 0.0, 0.0
        if keys[pygame.K_LEFT]  or keys[pygame.K_a]: dx -= 1
        if keys[pygame.K_RIGHT] or keys[pygame.K_d]: dx += 1
        if keys[pygame.K_UP]    or keys[pygame.K_w]: dy -= 1
        if keys[pygame.K_DOWN]  or keys[pygame.K_s]: dy += 1

        if dx or dy:
            nx, ny = n2(dx, dy)
            p.vx, p.vy   = nx*spd, ny*spd
            p.fdx, p.fdy = nx, ny
            p.wx = clamp(p.wx + p.vx, -OUT_L, W_W+OUT_R)
            p.wy = clamp(p.wy + p.vy, -OUT_T, W_H+OUT_B)
        else:
            p.vx *= 0.55
            p.vy *= 0.55

        # Shoot charge — works whenever ball owner is on team A
        # (no restriction on position or distance to goal)
        shooting = (keys[pygame.K_f] or
                    keys[pygame.K_LSHIFT] or
                    keys[pygame.K_RSHIFT])

        if shooting:
            if self.ball.owner and self.ball.owner.team == 'A':
                self.charging = True
                self.charge   = min(1.0, self.charge + 0.026)
        else:
            if self.charging:
                # Release: fire the shot at whatever power was built up
                # Minimum power 0.3 so even a tap does something
                if self.ball.owner and self.ball.owner.team == 'A':
                    self._shoot(max(0.30, self.charge))
            self.charging = False
            self.charge   = 0.0

        # Auto-collect loose ball
        if self.ball.owner is None and self.ball.wz < 10:
            if d2((p.wx,p.wy),(self.ball.wx,self.ball.wy)) < CONTROL_R:
                self.ball.owner = p
                self.ball.last_toucher = p

        if p.tackle_cd > 0:
            p.tackle_cd -= 1

    def _handle_events(self):
        for ev in pygame.event.get():
            if ev.type == pygame.QUIT:
                pygame.quit(); sys.exit()
            if ev.type == pygame.KEYDOWN:
                k = ev.key
                if k == pygame.K_ESCAPE:
                    pygame.quit(); sys.exit()

                # Ignore all input during freeze or dead ball (except ESC)
                if self.kickoff_freeze > 0 or self.dead:
                    continue

                if k == pygame.K_TAB:
                    self._switch()
                elif k == pygame.K_SPACE:
                    if self.ball.owner and self.ball.owner.team == 'A':
                        self._pass()
                elif k == pygame.K_c:
                    if self.ball.owner and self.ball.owner.team == 'A':
                        if self._near_byline(self.ball.owner):
                            self._cross(self.ball.owner)
                        else:
                            self._pass()
                elif k == pygame.K_x:
                    self._tackle()
                # All other keys: safe no-op

    # ── Player actions ────────────────────────────────────────────
    def _switch(self):
        self.sel.selected = False
        if self.ball.owner and self.ball.owner.team == 'A':
            self.sel = self.ball.owner
        else:
            cands = [p for p in self.ta if not p.is_keeper]
            cands.sort(key=lambda p: d2((p.wx,p.wy),(self.ball.wx,self.ball.wy)))
            idx  = cands.index(self.sel) if self.sel in cands else -1
            self.sel = cands[(idx+1) % len(cands)]
        self.sel.selected = True

    def _auto_switch(self, p):
        self.sel.selected = False
        self.sel = p
        self.sel.selected = True

    def _pass(self):
        carrier = self.ball.owner
        if not carrier or carrier.team != 'A':
            return
        tgt = best_pass_target(carrier, self.ta, self.tb)
        if not tgt:
            return
        # Lead pass ahead of receiver's movement
        lead_x = clamp(tgt.wx + tgt.vx * 10, 10, W_W - 10)
        lead_y = clamp(tgt.wy + tgt.vy * 10, 10, W_H - 10)
        self.ball.last_toucher = carrier
        self.ball.kick(lead_x, lead_y, PASS_SPD, 2.0)
        self._auto_switch(tgt)

    def _cross(self, carrier):
        tgt_y = GOAL_TOP+20 if carrier.wy > W_MY else GOAL_BOT-20
        tgt_y += random.randint(-18, 18)
        self.ball.release()
        bx, by = n2(W_W - carrier.wx, tgt_y - carrier.wy)
        self.ball.vx = bx * CROSS_SPD
        self.ball.vy = by * CROSS_SPD
        self.ball.vz = 9.0
        self.ball.last_toucher = carrier
        self.msg("CROSS! ⚽", (255, 200, 60))

    def _shoot(self, power):
        """
        Shoot toward the opponent's goal.
        Works from any position — no minimum distance required.
        power: 0.0–1.0
        """
        c = self.ball.owner
        if not c or c.team != 'A':
            return

        # Aim at goal: vertical aim tracks carrier's y, with slight randomness
        gy = clamp(c.wy, GOAL_TOP + 15, GOAL_BOT - 15) + random.randint(-12, 12)

        # Inaccuracy decreases with more power
        inac = clamp((1.0 - power) * 0.22, 0, 0.22)
        bx, by = n2(W_W - c.wx, gy - c.wy)
        bx += random.uniform(-inac, inac)
        by += random.uniform(-inac, inac)
        bx, by = n2(bx, by)

        spd = SHOOT_SPD * (0.45 + power * 0.55)
        self.ball.release()
        self.ball.vx = bx * spd
        self.ball.vy = by * spd
        self.ball.vz = 3.5 + power * 8.0
        self.ball.last_toucher = c

    def _tackle(self):
        p = self.sel
        if p.tackle_cd > 0:
            return
        for t in self.tb:
            if t.is_keeper:
                continue
            dd = d2((p.wx,p.wy),(t.wx,t.wy))
            if dd < TACKLE_R + 10 and self.ball.owner is t:
                ok = random.random() < 0.62
                if ok:
                    prev = t
                    self.ball.release()
                    bx, by = n2(p.wx-prev.wx, p.wy-prev.wy)
                    self.ball.vx = bx*4.5 + random.uniform(-1.5, 1.5)
                    self.ball.vy = by*4.5 + random.uniform(-1.5, 1.5)
                    self.ball.last_toucher = p
                    self.msg("TACKLE! Ball won!", (80,255,80))
                    self._auto_switch(p)
                else:
                    self.msg("Tackle missed!", (255,160,60))
                p.tackle_cd = 48
                return

    def _near_byline(self, p):
        return p.wx > W_W*0.82 and (p.wy < W_MY-40 or p.wy > W_MY+40)

    # ── GK pass timer (bug fix 2) ─────────────────────────────────
    def _update_gk_logic(self):
        """
        If a goalkeeper has held the ball for more than ~2 seconds,
        force them to pass to the nearest unmarked outfield teammate.
        This prevents the stuck-GK bug.
        """
        for gk, own_team, opp_team in [
            (self.ta[0], self.ta, self.tb),
            (self.tb[0], self.tb, self.ta),
        ]:
            if self.ball.owner is gk:
                self.gk_hold_timer += 1
                if self.gk_hold_timer >= FPS * 2:   # 2 seconds
                    # Find nearest unmarked teammate
                    mates = [p for p in own_team if p is not gk and not p.is_keeper]
                    if mates:
                        tgt = best_pass_target(gk, own_team, opp_team)
                        if tgt is None:
                            tgt = min(mates, key=lambda p: d2((gk.wx,gk.wy),(p.wx,p.wy)))
                        lead_x = clamp(tgt.wx + tgt.vx*8, 10, W_W-10)
                        lead_y = clamp(tgt.wy + tgt.vy*8, 10, W_H-10)
                        self.ball.kick(lead_x, lead_y, PASS_SPD, 2.0)
                        self.ball.last_toucher = gk
                        # Auto-switch to receiver if it's team A
                        if gk.team == 'A':
                            self._auto_switch(tgt)
                    self.gk_hold_timer = 0
            else:
                # Reset if ball changed hands
                if not (self.ball.owner and self.ball.owner.is_keeper):
                    self.gk_hold_timer = 0

    # ── Throw-in force-pass (bug fix 3) ───────────────────────────
    def _update_throw_in_pass(self):
        """
        After a throw-in the ball stays frozen (no owner).
        After a short delay the thrower auto-passes to a teammate.
        The thrower cannot dribble because they never receive ownership.
        """
        if not self.throw_must_pass:
            return

        self._throw_pass_timer -= 1
        if self._throw_pass_timer > 0:
            # Keep ball frozen at the throw spot
            tp = self._throw_pass_thrower
            self.ball.wx = tp.wx
            self.ball.wy = tp.wy
            self.ball.wz = 0.0
            self.ball.vx = self.ball.vy = self.ball.vz = 0.0
            return

        # Timer expired: find a receiver and kick
        tp   = self._throw_pass_thrower
        team = self.ta if tp.team == 'A' else self.tb
        opp  = self.tb if tp.team == 'A' else self.ta

        tgt = best_pass_target(tp, team, opp)
        if tgt is None:
            mates = [p for p in team if p is not tp]
            tgt = min(mates, key=lambda p: d2((tp.wx,tp.wy),(p.wx,p.wy))) if mates else None

        if tgt:
            lead_x = clamp(tgt.wx + tgt.vx * 8, 5, W_W - 5)
            lead_y = clamp(tgt.wy + tgt.vy * 8, 5, W_H - 5)
            self.ball.last_toucher = tp
            self.ball.kick(lead_x, lead_y, PASS_SPD, 2.0)
            tp.throw_anim = 0
            if tp.team == 'A':
                self._auto_switch(tgt)

        self.throw_must_pass        = False
        self._throw_pass_thrower    = None
        self._throw_pass_timer      = 0

    # ── Goals ─────────────────────────────────────────────────────
    def _check_goals(self):
        if self.dead or self.kickoff_freeze:
            return
        b = self.ball
        if b.wz > 26:
            return
        if b.wx <= -BALL_R and GOAL_TOP <= b.wy <= GOAL_BOT:
            self.score[1] += 1
            self.msg("⚽  GOAL! — REAL MADRID!", (215,215,215))
            self._start_dead(DB_KICK_A, None)
            return
        if b.wx >= W_W + BALL_R and GOAL_TOP <= b.wy <= GOAL_BOT:
            self.score[0] += 1
            self.msg("⚽  GOAL! — BARCELONA!", BAR_BLUE)
            self._start_dead(DB_KICK_B, None)

    # ── Out of bounds ─────────────────────────────────────────────
    def _check_out(self):
        if self.dead or self.ball.owner or self.kickoff_freeze:
            return
        b  = self.ball
        lt = b.last_toucher

        # Top/bottom → throw-in
        if b.wy < -BALL_R or b.wy > W_H + BALL_R:
            kind = DB_THROW_B if lt and lt.team == 'A' else DB_THROW_A
            tx = clamp(b.wx, 38, W_W - 38)
            ty = 10 if b.wy < 0 else W_H - 10
            self._start_dead(kind, (tx, ty))
            return

        # Left byline (B's goal end) — not inside goal
        if b.wx < -BALL_R and not (GOAL_TOP <= b.wy <= GOAL_BOT):
            # A attacked, B defended → who last touched?
            # If A last touched: A shot/passed it out → goal kick for B
            # If B last touched: B put it behind their own line → corner for A
            if lt and lt.team == 'A':
                self._start_dead(DB_GK_B, (34, clamp(b.wy, 38, W_H-38)))
            else:
                cy = 10 if b.wy < W_MY else W_H - 10
                self._start_dead(DB_CORNER_A, (8, cy))
            return

        # Right byline (A's goal end) — not inside goal
        if b.wx > W_W + BALL_R and not (GOAL_TOP <= b.wy <= GOAL_BOT):
            # If B last touched → shot/passed out → goal kick for A
            # If A last touched → A put it behind their own line → corner for B
            if lt and lt.team == 'B':
                self._start_dead(DB_GK_A, (W_W-34, clamp(b.wy, 38, W_H-38)))
            else:
                cy = 10 if b.wy < W_MY else W_H - 10
                self._start_dead(DB_CORNER_B, (W_W-8, cy))

    # ── Dead-ball ─────────────────────────────────────────────────
    def _start_dead(self, kind, pos):
        self.ball.owner = None
        self.ball.vx = self.ball.vy = self.ball.vz = 0.0
        self.dead             = kind
        self.dead_pos         = pos if pos else (W_MX, W_MY)
        self.ball.wx          = float(self.dead_pos[0])
        self.ball.wy          = float(self.dead_pos[1])
        self.ball.wz          = 0.0
        self.dead_timer       = FPS * 2 + 20
        self.throw_player     = None
        self.throw_must_pass  = False
        self._throw_pass_thrower = None
        self._throw_pass_timer   = 0
        self.gk_hold_timer    = 0
        self.charging         = False
        self.charge           = 0.0

    def _update_dead(self):
        if not self.dead:
            return
        self.dead_timer -= 1
        kind = self.dead
        bx, by = self.dead_pos

        # Assign the throw player once the pause starts
        if self.throw_player is None and self.dead_timer <= FPS * 2:
            if kind in (DB_THROW_A, DB_GK_A, DB_CORNER_A):
                team = self.ta
            elif kind in (DB_THROW_B, DB_GK_B, DB_CORNER_B):
                team = self.tb
            else:
                team = None
            if team:
                tp = min(team, key=lambda p: d2((p.wx,p.wy),(bx,by)))
                tp.wx = float(bx); tp.wy = float(by)
                self.throw_player = tp
                tp.throw_anim = 1

        if self.throw_player:
            self.throw_player.throw_anim = min(30, self.throw_player.throw_anim + 1)

        if self.dead_timer > 0:
            return

        # ── Resume play ──────────────────────────────────────────
        if kind in (DB_KICK_A, DB_KICK_B):
            if self.throw_player:
                self.throw_player.throw_anim = 0
            self._kickoff('A' if 'A' in kind else 'B')
            return

        # Corners → auto-cross
        if kind in (DB_CORNER_A, DB_CORNER_B):
            team = self.ta if kind == DB_CORNER_A else self.tb
            tp   = min(team, key=lambda p: d2((p.wx,p.wy),(bx,by)))
            tp.wx, tp.wy = float(bx), float(by)
            self.ball.wx, self.ball.wy, self.ball.wz = float(bx), float(by), 0.0
            tgt_y  = GOAL_TOP+22 if by < W_MY else GOAL_BOT-22
            tgt_y += random.randint(-16, 16)
            tgt_x  = W_W if kind == DB_CORNER_A else 0.0
            self.ball.kick(tgt_x, tgt_y, CROSS_SPD, 9.5)
            self.ball.last_toucher = tp
            if tp.throw_anim: tp.throw_anim = 0
            self.dead = None; self.throw_player = None
            return

        # Throw-ins & goal kicks → give ball to nearest; force a pass
        team    = self.ta if kind.endswith('_A') else self.tb
        nearest = min(team, key=lambda p: d2((p.wx,p.wy),(bx,by)))
        nearest.wx, nearest.wy = float(bx), float(by)
        self.ball.wx, self.ball.wy, self.ball.wz = float(bx), float(by), 0.0
        self.ball.owner = nearest
        self.ball.last_toucher = nearest
        nearest.throw_anim = 0
        if self.throw_player:
            self.throw_player.throw_anim = 0

        # Throw-ins must pass, not dribble
        if kind in (DB_THROW_A, DB_THROW_B):
            # Do NOT give ball ownership — we keep owner=None and use a timer
            # so the ball stays frozen at the spot. After half a second, auto-pass.
            self.ball.owner = None   # thrower does NOT own the ball yet
            self.ball.wx = float(bx)
            self.ball.wy = float(by)
            self.throw_must_pass = True
            self._throw_pass_thrower = nearest
            self._throw_pass_timer   = FPS // 2   # 0.5 s then kick
        else:
            # Goal kicks: give normal ball ownership
            self.throw_must_pass = False

        if nearest.team == 'A':
            self._auto_switch(nearest)
        self.dead = None
        self.throw_player = None

    # ── Main loop ─────────────────────────────────────────────────
    def run(self):
        while True:
            self.clock.tick(FPS)
            self.match_time += 1

            self._handle_events()
            self._handle_input()

            if self.kickoff_freeze > 0:
                # Decrement freeze counter; NO AI runs, NO physics, just draw
                self.kickoff_freeze -= 1

            elif not self.dead:
                # GK stuck fix
                self._update_gk_logic()

                # Throw-in force pass (ball frozen, auto-passes after timer)
                self._update_throw_in_pass()

                # AI only runs when not in a throw-in pause
                if not self.throw_must_pass:
                    cpu_ai(self.tb, self.ta, self.ball)
                    cpu_attacking_shape(self.tb, self.ball)
                    team_a_support(self.ta, self.sel, self.ball)

                self.ball.update()
                self._check_goals()
                self._check_out()

                # Auto-collect loose ball — but NOT during a throw-in
                # (ball has no owner but must stay frozen until the pass fires)
                if not self.throw_must_pass and self.ball.owner is None and self.ball.wz < 11:
                    all_p = self.ta + self.tb
                    all_p.sort(key=lambda p: d2((p.wx,p.wy),(self.ball.wx,self.ball.wy)))
                    for p in all_p:
                        if d2((p.wx,p.wy),(self.ball.wx,self.ball.wy)) < CONTROL_R:
                            self.ball.owner = p
                            self.ball.last_toucher = p
                            if p.team == 'B':
                                for q in self.tb[1:]:
                                    q.react = random.randint(7, 24)
                            elif p is not self.sel:
                                self._auto_switch(p)
                            break

            else:
                self._update_dead()

            self.msgs = [[t,c,n-1] for t,c,n in self.msgs if n > 0]
            self._draw_scene()
            self._hud.draw(self)
            pygame.display.flip()
