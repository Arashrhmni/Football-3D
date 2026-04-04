"""hud.py – Heads-up display rendering."""
import pygame
import math
from constants import (
    SCR_W, SCR_H, FPS, BAR_BLUE, DB_LABELS,
    HALF_FRAMES, MATCH_FRAMES
)


class HUD:
    def __init__(self, screen):
        self.screen = screen
        self.f_hud  = pygame.font.SysFont("Arial",  13, bold=True)
        self.f_big  = pygame.font.SysFont("Georgia", 38, bold=True)
        self.f_med  = pygame.font.SysFont("Georgia", 24, bold=True)
        self.f_xl   = pygame.font.SysFont("Georgia", 52, bold=True)

    def draw(self, game):
        s = game.screen

        # ── Convert frame time to game minutes ───────────────────
        # Each half = 45 game-minutes = HALF_FRAMES real frames
        # 1 game-minute = HALF_FRAMES / 45 frames
        frames_per_gmin = HALF_FRAMES / 45.0
        raw_gmin = game.match_time / frames_per_gmin   # 0–45 within the half
        if game.half == 1:
            game_min = int(raw_gmin) + 1             # 1–45
        else:
            game_min = int(raw_gmin) + 46            # 46–90
        game_min = min(game_min, 45 if game.half == 1 else 90)

        # ── Scoreboard ────────────────────────────────────────────
        bw = 370; bx = SCR_W//2 - bw//2
        pygame.draw.rect(s, (8,8,8),   (bx, 4, bw, 52), border_radius=10)
        pygame.draw.rect(s, (65,65,65),(bx, 4, bw, 52), 2, border_radius=10)

        ta_l = self.f_hud.render("BARCELONA",   True, BAR_BLUE)
        tb_l = self.f_hud.render("REAL MADRID", True, (215,215,215))
        s.blit(ta_l, (bx+10, 16))
        s.blit(tb_l, (bx+bw-tb_l.get_width()-10, 16))

        sc = self.f_big.render(f"{game.score[0]}  -  {game.score[1]}", True, (255,255,255))
        s.blit(sc, (SCR_W//2 - sc.get_width()//2, 4))

        # Game clock + half indicator
        half_col = (255,200,0) if game.half == 1 else (0,200,255)
        half_lbl = self.f_hud.render(f"{'1ST' if game.half==1 else '2ND'} HALF", True, half_col)
        clock_lbl = self.f_hud.render(f"{game_min}'", True, (220,220,220))
        s.blit(clock_lbl, (SCR_W//2 - clock_lbl.get_width()//2, 48))
        s.blit(half_lbl,  (SCR_W//2 + clock_lbl.get_width()//2 + 6, 48))

        # ── Half progress bar ─────────────────────────────────────
        bar_w = 300; bar_h = 4
        bar_x = SCR_W//2 - bar_w//2; bar_y = 64
        pygame.draw.rect(s, (40,40,40), (bar_x, bar_y, bar_w, bar_h), border_radius=2)
        progress = min(1.0, game.match_time / HALF_FRAMES)
        fill_col = (255,200,0) if game.half == 1 else (0,180,255)
        if progress > 0:
            pygame.draw.rect(s, fill_col, (bar_x, bar_y, int(bar_w*progress), bar_h), border_radius=2)

        # ── Controls panel ────────────────────────────────────────
        ctrl = [
            ("WASD/↑↓", "Move"),
            ("Z",        "Sprint"),
            ("SPACE",    "Pass"),
            ("C",        "Cross (near wing)"),
            ("F/Shift",  "Shoot (hold=power)"),
            ("X",        "Tackle"),
            ("TAB",      "Switch player"),
        ]
        px, py = 8, SCR_H - 136
        pygame.draw.rect(s, (0,0,0),    (px-4, py-4, 238, 140), border_radius=6)
        pygame.draw.rect(s, (48,48,48), (px-4, py-4, 238, 140), 1, border_radius=6)
        for i, (k, d) in enumerate(ctrl):
            ks = self.f_hud.render(k, True, (255,218,0))
            ds = self.f_hud.render(d, True, (170,170,170))
            s.blit(ks, (px,    py + i*18))
            s.blit(ds, (px+86, py + i*18))

        # ── Shoot power bar ───────────────────────────────────────
        if game.charging:
            bw2, bh = 210, 20
            bx2 = SCR_W//2 - bw2//2; by2 = SCR_H - 58
            pygame.draw.rect(s, (20,20,20), (bx2-2, by2-2, bw2+4, bh+4), border_radius=6)
            fill = int(bw2 * game.charge)
            gc   = (int(55+200*game.charge), int(200*(1-game.charge**0.5)), 0)
            pygame.draw.rect(s, gc, (bx2, by2, fill, bh), border_radius=4)
            pygame.draw.rect(s, (190,190,190), (bx2-2,by2-2,bw2+4,bh+4), 1, border_radius=6)
            lbl = self.f_hud.render(f"SHOOT  {int(game.charge*100)}%", True, (255,255,255))
            s.blit(lbl, (SCR_W//2 - lbl.get_width()//2, by2-18))

        # ── Dead-ball banner ──────────────────────────────────────
        if game.dead:
            lbl = DB_LABELS.get(game.dead, '')
            ds  = self.f_med.render(lbl, True, (255,225,0))
            bx3 = SCR_W//2 - ds.get_width()//2
            pygame.draw.rect(s, (0,0,0), (bx3-14, SCR_H-64, ds.get_width()+28, 36), border_radius=8)
            s.blit(ds, (bx3, SCR_H-60))
            cd = max(0, game.dead_timer//FPS + 1)
            ts = self.f_hud.render(f"Resuming in {cd}s…", True, (150,150,150))
            s.blit(ts, (SCR_W//2 - ts.get_width()//2, SCR_H-27))

        # ── Messages ─────────────────────────────────────────────
        for i, m in enumerate(game.msgs):
            ms = self.f_med.render(m[0], True, m[1])
            ms.set_alpha(min(255, m[2]*3))
            s.blit(ms, (SCR_W//2 - ms.get_width()//2, SCR_H//2 - 110 + i*42))

        # ── Possession indicator ──────────────────────────────────
        if game.ball.owner:
            side = "BARCELONA" if game.ball.owner.team == 'A' else "REAL MADRID"
            col  = BAR_BLUE if game.ball.owner.team == 'A' else (215,215,215)
            ps = self.f_hud.render(f"Ball: {side} #{game.ball.owner.num}", True, col)
            s.blit(ps, (SCR_W//2 - ps.get_width()//2, 72))

        # ── Kickoff whistle overlay ───────────────────────────────
        if game.kickoff_freeze > 0:
            msg = self.f_med.render("WHISTLE — KICK OFF!", True, (255,230,0))
            s.blit(msg, (SCR_W//2 - msg.get_width()//2, SCR_H//2 - 20))

        # ── Half-time overlay ─────────────────────────────────────
        if game.match_state == 'half_time':
            self._draw_overlay(s, (0,0,0,160))
            ht = self.f_xl.render("HALF TIME", True, (255,220,0))
            s.blit(ht, (SCR_W//2 - ht.get_width()//2, SCR_H//2 - 60))
            sc2 = self.f_big.render(
                f"BARCELONA  {game.score[0]}  —  {game.score[1]}  REAL MADRID",
                True, (255,255,255))
            s.blit(sc2, (SCR_W//2 - sc2.get_width()//2, SCR_H//2))
            cd2 = max(0, game.half_time_timer // FPS + 1)
            ts2 = self.f_hud.render(f"2nd half starts in {cd2}s…", True, (180,180,180))
            s.blit(ts2, (SCR_W//2 - ts2.get_width()//2, SCR_H//2 + 55))

        # ── Full-time overlay ─────────────────────────────────────
        if game.match_state == 'full_time':
            self._draw_overlay(s, (0,0,0,200))
            ft = self.f_xl.render("FULL TIME", True, (255,220,0))
            s.blit(ft, (SCR_W//2 - ft.get_width()//2, SCR_H//2 - 80))
            sc3 = self.f_big.render(
                f"BARCELONA  {game.score[0]}  —  {game.score[1]}  REAL MADRID",
                True, (255,255,255))
            s.blit(sc3, (SCR_W//2 - sc3.get_width()//2, SCR_H//2 - 10))
            # Result line
            if game.score[0] > game.score[1]:
                result = "BARCELONA WIN!";  rc = BAR_BLUE
            elif game.score[1] > game.score[0]:
                result = "REAL MADRID WIN!"; rc = (215,215,215)
            else:
                result = "IT'S A DRAW!";    rc = (255,220,0)
            rl = self.f_med.render(result, True, rc)
            s.blit(rl, (SCR_W//2 - rl.get_width()//2, SCR_H//2 + 50))
            quit_lbl = self.f_hud.render("Press ESC to quit", True, (140,140,140))
            s.blit(quit_lbl, (SCR_W//2 - quit_lbl.get_width()//2, SCR_H//2 + 95))

    # ── Helper ────────────────────────────────────────────────────
    def _draw_overlay(self, surf, col_alpha):
        overlay = pygame.Surface((SCR_W, SCR_H), pygame.SRCALPHA)
        overlay.fill(col_alpha)
        surf.blit(overlay, (0, 0))
