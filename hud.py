"""hud.py – Heads-up display rendering."""
import pygame
from constants import (
    SCR_W, SCR_H, FPS, BAR_BLUE, DB_LABELS, w2s
)


class HUD:
    def __init__(self, screen):
        self.screen = screen
        self.f_hud = pygame.font.SysFont("Arial",  13, bold=True)
        self.f_big = pygame.font.SysFont("Georgia", 38, bold=True)
        self.f_med = pygame.font.SysFont("Georgia", 24, bold=True)

    def draw(self, game):
        s = game.screen
        mins = game.match_time // (FPS*60)
        secs = (game.match_time // FPS) % 60

        # ── Scoreboard
        bw = 340; bx = SCR_W//2 - bw//2
        pygame.draw.rect(s, (8,8,8),   (bx, 4, bw, 46), border_radius=10)
        pygame.draw.rect(s, (65,65,65),(bx, 4, bw, 46), 2, border_radius=10)
        ta_l = self.f_hud.render("BARCELONA",  True, BAR_BLUE)
        tb_l = self.f_hud.render("REAL MADRID",True, (215,215,215))
        s.blit(ta_l, (bx+10, 14))
        s.blit(tb_l, (bx+bw-tb_l.get_width()-10, 14))
        sc = self.f_big.render(f"{game.score[0]}  -  {game.score[1]}", True, (255,255,255))
        s.blit(sc, (SCR_W//2 - sc.get_width()//2, 4))
        tc = self.f_hud.render(f"{mins:02d}:{secs:02d}", True, (170,170,170))
        s.blit(tc, (SCR_W//2 - tc.get_width()//2, 48))

        # ── Controls panel
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

        # ── Shoot power bar
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

        # ── Dead-ball banner
        if game.dead:
            lbl = DB_LABELS.get(game.dead, '')
            ds  = self.f_med.render(lbl, True, (255,225,0))
            bx3 = SCR_W//2 - ds.get_width()//2
            pygame.draw.rect(s, (0,0,0), (bx3-14, SCR_H-64, ds.get_width()+28, 36), border_radius=8)
            s.blit(ds, (bx3, SCR_H-60))
            cd = max(0, game.dead_timer//FPS + 1)
            ts = self.f_hud.render(f"Resuming in {cd}s…", True, (150,150,150))
            s.blit(ts, (SCR_W//2 - ts.get_width()//2, SCR_H-27))

        # ── Messages
        for i, m in enumerate(game.msgs):
            ms = self.f_med.render(m[0], True, m[1])
            ms.set_alpha(min(255, m[2]*3))
            s.blit(ms, (SCR_W//2 - ms.get_width()//2, SCR_H//2 - 110 + i*42))

        # ── Possession indicator
        if game.ball.owner:
            side = "BARCELONA" if game.ball.owner.team == 'A' else "REAL MADRID"
            col  = BAR_BLUE if game.ball.owner.team == 'A' else (215,215,215)
            ps = self.f_hud.render(f"Ball: {side} #{game.ball.owner.num}", True, col)
            s.blit(ps, (SCR_W//2 - ps.get_width()//2, 68))

        # ── Kickoff countdown overlay (freeze phase)
        if game.kickoff_freeze > 0:
            overlay = pygame.Surface((SCR_W, SCR_H), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 0))
            s.blit(overlay, (0, 0))
            msg = self.f_med.render("WHISTLE — KICK OFF!", True, (255,230,0))
            s.blit(msg, (SCR_W//2 - msg.get_width()//2, SCR_H//2 - 20))
