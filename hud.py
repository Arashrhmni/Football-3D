"""hud.py – Heads-up display rendering."""
import pygame
from constants import (
    SCR_W, SCR_H, FPS,
    HALF_FRAMES, W_W, W_H, get_stars
)


class HUD:
    def __init__(self, screen):
        self.screen     = screen
        self.league_mode = False
        self.f_hud  = pygame.font.SysFont("Arial",  13, bold=True)
        self.f_big  = pygame.font.SysFont("Georgia", 38, bold=True)
        self.f_med  = pygame.font.SysFont("Georgia", 24, bold=True)
        self.f_xl   = pygame.font.SysFont("Georgia", 52, bold=True)

    def draw(self, game):
        s = game.screen

        ta_name = game.team_a_name
        tb_name = game.team_b_name
        ta_col  = game.team_a_col
        tb_col  = game.team_b_col

        frames_per_gmin = HALF_FRAMES / 45.0
        raw_gmin = game.match_time / frames_per_gmin
        if game.half == 1:
            game_min = int(raw_gmin) + 1
        else:
            game_min = int(raw_gmin) + 46
        game_min = min(game_min, 45 if game.half == 1 else 90)

        bw = 420; bx = SCR_W//2 - bw//2
        pygame.draw.rect(s, (8,8,8),   (bx, 4, bw, 52), border_radius=10)
        pygame.draw.rect(s, (65,65,65),(bx, 4, bw, 52), 2, border_radius=10)

        ta_l = self.f_hud.render(ta_name, True, ta_col)
        tb_l = self.f_hud.render(tb_name, True, tb_col)
        s.blit(ta_l, (bx+10, 12))
        s.blit(tb_l, (bx+bw-tb_l.get_width()-10, 12))

        # Star dots under each team name
        def _draw_hud_stars(surf, sx, sy, n):
            for i in range(5):
                c = (255,210,0) if i < n else (40,45,65)
                pygame.draw.circle(surf, c, (sx+i*9+4, sy), 3)
        _draw_hud_stars(s, bx+10, 36, game.stars_a)
        _draw_hud_stars(s, bx+bw-tb_l.get_width()-10, 36, game.stars_b)

        sc = self.f_big.render(f"{game.score[0]}  -  {game.score[1]}", True, (255,255,255))
        s.blit(sc, (SCR_W//2 - sc.get_width()//2, 4))

        half_col  = (255,200,0) if game.half == 1 else (0,200,255)
        half_lbl  = self.f_hud.render(f"{'1ST' if game.half==1 else '2ND'} HALF", True, half_col)
        clock_lbl = self.f_hud.render(f"{game_min}'", True, (220,220,220))
        s.blit(clock_lbl, (SCR_W//2 - clock_lbl.get_width()//2, 48))
        s.blit(half_lbl,  (SCR_W//2 + clock_lbl.get_width()//2 + 6, 48))

        bar_w = 300; bar_h = 4
        bar_x = SCR_W//2 - bar_w//2; bar_y = 64
        pygame.draw.rect(s, (40,40,40), (bar_x, bar_y, bar_w, bar_h), border_radius=2)
        progress = min(1.0, game.match_time / HALF_FRAMES)
        fill_col = (255,200,0) if game.half == 1 else (0,180,255)
        if progress > 0:
            pygame.draw.rect(s, fill_col, (bar_x, bar_y, int(bar_w*progress), bar_h), border_radius=2)

        ctrl = [
            ("WASD/arrows", "Move"),
            ("Z",           "Sprint"),
            ("SPACE",       "Pass"),
            ("Q",           "Through pass"),
            ("C",           "Cross / pass"),
            ("F / Shift",   "Shoot (hold=power)"),
            ("X",           "Tackle"),
            ("TAB",         "Switch player"),
            ("P",           "Pause"),
            ("ESC",         "Main menu"),
        ]
        px, py = 8, SCR_H - 170
        pygame.draw.rect(s, (0,0,0),    (px-4, py-4, 248, 174), border_radius=6)
        pygame.draw.rect(s, (48,48,48), (px-4, py-4, 248, 174), 1, border_radius=6)
        for i, (k, d) in enumerate(ctrl):
            ks = self.f_hud.render(k, True, (255,218,0))
            ds = self.f_hud.render(d, True, (170,170,170))
            s.blit(ks, (px,     py + i*16))
            s.blit(ds, (px+100, py + i*16))

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

        if game.dead:
            lbl = game._db_labels.get(game.dead, '')
            ds  = self.f_med.render(lbl, True, (255,225,0))
            bx3 = SCR_W//2 - ds.get_width()//2
            pygame.draw.rect(s, (0,0,0), (bx3-14, SCR_H-64, ds.get_width()+28, 36), border_radius=8)
            s.blit(ds, (bx3, SCR_H-60))
            cd = max(0, game.dead_timer//FPS + 1)
            ts = self.f_hud.render(f"Resuming in {cd}s…", True, (150,150,150))
            s.blit(ts, (SCR_W//2 - ts.get_width()//2, SCR_H-27))

        for i, m in enumerate(game.msgs):
            ms = self.f_med.render(m[0], True, m[1])
            ms.set_alpha(min(255, m[2]*3))
            s.blit(ms, (SCR_W//2 - ms.get_width()//2, SCR_H//2 - 110 + i*42))

        if game.ball.owner:
            side = ta_name if game.ball.owner.team == 'A' else tb_name
            col  = ta_col  if game.ball.owner.team == 'A' else tb_col
            ps = self.f_hud.render(f"Ball: {side} #{game.ball.owner.num}", True, col)
            s.blit(ps, (SCR_W//2 - ps.get_width()//2, 72))

        self._draw_stamina(game)
        self._draw_radar(game, ta_col, tb_col)

        if game.kickoff_freeze > 0:
            msg = self.f_med.render("WHISTLE — KICK OFF!", True, (255,230,0))
            s.blit(msg, (SCR_W//2 - msg.get_width()//2, SCR_H//2 - 20))

        if game.match_state == 'half_time':
            self._draw_overlay(s, (0,0,0,160))
            ht = self.f_xl.render("HALF TIME", True, (255,220,0))
            s.blit(ht, (SCR_W//2 - ht.get_width()//2, SCR_H//2 - 60))
            sc2 = self.f_med.render(
                f"{ta_name}  {game.score[0]}  —  {game.score[1]}  {tb_name}",
                True, (255,255,255))
            s.blit(sc2, (SCR_W//2 - sc2.get_width()//2, SCR_H//2))
            cd2 = max(0, game.half_time_timer // FPS + 1)
            ts2 = self.f_hud.render(f"2nd half starts in {cd2}s…", True, (180,180,180))
            s.blit(ts2, (SCR_W//2 - ts2.get_width()//2, SCR_H//2 + 55))

        if game.match_state == 'full_time':
            self._draw_overlay(s, (0,0,0,200))
            ft = self.f_xl.render("FULL TIME", True, (255,220,0))
            s.blit(ft, (SCR_W//2 - ft.get_width()//2, SCR_H//2 - 80))
            sc3 = self.f_med.render(
                f"{ta_name}  {game.score[0]}  —  {game.score[1]}  {tb_name}",
                True, (255,255,255))
            s.blit(sc3, (SCR_W//2 - sc3.get_width()//2, SCR_H//2 - 10))
            if game.score[0] > game.score[1]:
                result = f"{ta_name} WIN!";  rc = ta_col
            elif game.score[1] > game.score[0]:
                result = f"{tb_name} WIN!";  rc = tb_col
            else:
                result = "IT'S A DRAW!";     rc = (255,220,0)
            rl = self.f_med.render(result, True, rc)
            s.blit(rl, (SCR_W//2 - rl.get_width()//2, SCR_H//2 + 50))
            quit_lbl = self.f_hud.render(
                "SPACE / ENTER to continue  ·  ESC to forfeit & skip" if self.league_mode
                else "Press R to restart · ESC for main menu",
                True, (140,140,140))
            s.blit(quit_lbl, (SCR_W//2 - quit_lbl.get_width()//2, SCR_H//2 + 95))

        if game.match_state == 'paused':
            self._draw_overlay(s, (0,0,0,160))
            pt = self.f_xl.render("PAUSED", True, (255,255,255))
            s.blit(pt, (SCR_W//2 - pt.get_width()//2, SCR_H//2 - 70))
            hint = self.f_med.render(
                "P to resume · R to restart · ESC for menu", True, (210,210,210))
            s.blit(hint, (SCR_W//2 - hint.get_width()//2, SCR_H//2 + 10))

    def _draw_stamina(self, game):
        bw, bh = 180, 14
        bx, by = SCR_W - bw - 18, 18
        pygame.draw.rect(self.screen, (0,0,0), (bx-3, by-3, bw+6, bh+6), border_radius=5)
        pygame.draw.rect(self.screen, (50,50,50), (bx-3, by-3, bw+6, bh+6), 1, border_radius=5)
        fill = int(bw * game.sel.stamina)
        col = (60, 210, 90) if game.sel.stamina > 0.55 else (
              (255, 190, 60) if game.sel.stamina > 0.25 else (230, 70, 70))
        pygame.draw.rect(self.screen, col, (bx, by, fill, bh), border_radius=4)
        label = self.f_hud.render(f"STAMINA #{game.sel.num}", True, (230,230,230))
        self.screen.blit(label, (bx, by - 15))

    def _draw_radar(self, game, ta_col, tb_col):
        rw, rh = 190, 118
        rx, ry = SCR_W - rw - 14, SCR_H - rh - 14
        pygame.draw.rect(self.screen, (10,10,10), (rx, ry, rw, rh), border_radius=8)
        pygame.draw.rect(self.screen, (70,70,70), (rx, ry, rw, rh), 1, border_radius=8)
        inner = pygame.Rect(rx + 8, ry + 8, rw - 16, rh - 16)
        pygame.draw.rect(self.screen, (26, 82, 36), inner, border_radius=5)
        pygame.draw.rect(self.screen, (180,180,180), inner, 1, border_radius=5)
        pygame.draw.line(self.screen, (180,180,180),
                         (inner.centerx, inner.top), (inner.centerx, inner.bottom), 1)
        pygame.draw.circle(self.screen, (180,180,180), inner.center, 13, 1)

        def rp(wx, wy):
            x = inner.left + int((wx / W_W) * inner.width)
            y = inner.top  + int((wy / W_H) * inner.height)
            return x, y

        for p in game.ta:
            pygame.draw.circle(self.screen, ta_col, rp(p.wx, p.wy), 3 if not p.selected else 4)
        for p in game.tb:
            pygame.draw.circle(self.screen, tb_col, rp(p.wx, p.wy), 3)
        pygame.draw.circle(self.screen, (255, 215, 0), rp(game.ball.wx, game.ball.wy), 3)

    def _draw_overlay(self, surf, col_alpha):
        overlay = pygame.Surface((SCR_W, SCR_H), pygame.SRCALPHA)
        overlay.fill(col_alpha)
        surf.blit(overlay, (0, 0))
