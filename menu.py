"""menu.py – All selection screens: Main Menu, Quick Play team pick."""
import pygame, sys, math, random
from constants import SCR_W, SCR_H, FPS, TEAMS
from shared_ui import (
    GOLD, WHITE, GREY, PANEL_BG,
    draw_stadium_bg, make_particles, update_particles, draw_particles,
    draw_football, draw_kit, draw_flag, glass_panel, gold_divider,
    draw_page_title, FancyBtn, CountryTab, TeamCard, FLAG_DATA
)

TEAMS_BY_COUNTRY = {}
for _k, _d in TEAMS.items():
    TEAMS_BY_COUNTRY.setdefault(_d['country'], []).append(_k)
COUNTRY_ORDER = ['Spain', 'England', 'Germany']


# ═══════════════════════════════════════════════════════════════════
# SIDE PANEL  (country tabs + scrollable team grid for one slot)
# ═══════════════════════════════════════════════════════════════════
class SidePanel:
    COL_W    = 196
    CARD_GAP = 10

    def __init__(self, rect, label, label_col, fn, fc, fcard, fsmall):
        self.rect  = pygame.Rect(rect)
        self.label = label; self.label_col = label_col
        self.fn=fn; self.fc=fc; self.fcard=fcard; self.fsmall=fsmall
        self.selected_country = None
        self.selected_team    = None
        self._scroll = 0
        self._tabs   = []
        self._cards  = []
        ty = self.rect.y + 36
        for country in COUNTRY_ORDER:
            if country not in TEAMS_BY_COUNTRY: continue
            self._tabs.append(CountryTab(country,
                (self.rect.x+6, ty, self.COL_W-12, 60), fc))
            ty += 70

    def _ta(self):          # team-card area rect
        tx = self.rect.x + self.COL_W + 8
        return pygame.Rect(tx, self.rect.y+36,
                           self.rect.right-tx-4, self.rect.h-40)

    def _rebuild(self, exclude=None):
        self._cards=[]; self._scroll=0
        if not self.selected_country: return
        keys = [k for k in TEAMS_BY_COUNTRY.get(self.selected_country,[]) if k!=exclude]
        ta   = self._ta()
        cw,ch= TeamCard.W, TeamCard.H
        g    = self.CARD_GAP
        cols = max(1,(ta.w+g)//(cw+g))
        for i,key in enumerate(keys):
            c2=i%cols; r2=i//cols
            x=ta.x+c2*(cw+g); y=ta.y+r2*(ch+g)
            card = TeamCard(key,(x,y,cw,ch),self.fcard,self.fsmall)
            if key==self.selected_team: card.selected=True
            self._cards.append(card)

    def set_exclude(self, key):
        self._rebuild(exclude=key)

    def _max_scroll(self):
        if not self._cards: return 0
        bottom = max(c.rect.bottom for c in self._cards)
        ta = self._ta()
        return max(0, bottom - ta.bottom)

    def handle_event(self, ev):
        ta = self._ta()
        if ev.type == pygame.MOUSEBUTTONDOWN:
            if ev.button==4 and ta.collidepoint(ev.pos):
                self._scroll=max(0,self._scroll-38)
            elif ev.button==5 and ta.collidepoint(ev.pos):
                self._scroll=min(self._max_scroll(),self._scroll+38)
            elif ev.button==1:
                for tab in self._tabs:
                    if tab.clicked(*ev.pos):
                        if tab.country != self.selected_country:
                            self.selected_country = tab.country
                            old = self.selected_team
                            if old and TEAMS[old]['country'] != tab.country:
                                self.selected_team = None
                            self._rebuild()
                        for t in self._tabs: t.selected=(t.country==tab.country)
                        return None
                for card in self._cards:
                    hr = pygame.Rect(card.rect.x, card.rect.y-self._scroll, card.rect.w, card.rect.h)
                    if hr.collidepoint(*ev.pos) and ta.collidepoint(*ev.pos):
                        for c in self._cards: c.selected=False
                        card.selected=True; self.selected_team=card.key
                        return card.key
        return None

    def update(self, mx, my):
        for tab in self._tabs: tab.update(mx,my)
        ta = self._ta()
        for card in self._cards:
            hr = pygame.Rect(card.rect.x, card.rect.y-self._scroll, card.rect.w, card.rect.h)
            card._hov = hr.collidepoint(mx,my) and ta.collidepoint(mx,my)

    def draw(self, surf):
        # Panel glass background
        glass_panel(surf, self.rect, tint=(8,14,38), alpha=220, border=(44,62,110))
        # Header bar
        hbar = pygame.Surface((self.rect.w, 28), pygame.SRCALPHA)
        pygame.draw.rect(hbar, (*self.label_col, 30), hbar.get_rect(), border_radius=12)
        surf.blit(hbar, self.rect.topleft)
        lbl = self.fn.render(self.label, True, self.label_col)
        surf.blit(lbl, lbl.get_rect(x=self.rect.x+10, y=self.rect.y+6))
        # Divider between country col and card area
        dx = self.rect.x + self.COL_W + 2
        pygame.draw.line(surf,(38,54,100),(dx,self.rect.y+4),(dx,self.rect.bottom-4),1)
        # Tabs
        for tab in self._tabs: tab.draw(surf)
        # Cards
        ta = self._ta()
        if not self.selected_country:
            hint = self.fsmall.render('← Pick a country', True,(55,75,140))
            surf.blit(hint, hint.get_rect(centerx=ta.centerx, centery=ta.centery))
        else:
            clip = pygame.Surface((ta.w,ta.h), pygame.SRCALPHA)
            for card in self._cards:
                cr = pygame.Rect(card.rect.x-ta.x, card.rect.y-ta.y-self._scroll,
                                 card.rect.w, card.rect.h)
                if cr.bottom<0 or cr.top>ta.h: continue
                tmp = TeamCard(card.key, cr, self.fcard, self.fsmall)
                tmp.selected=card.selected; tmp._hov=card._hov; tmp._t=card._t
                tmp.draw(clip)
            surf.blit(clip, ta.topleft)
            if not self._cards:
                msg=self.fsmall.render('All clubs taken',True,(120,70,70))
                surf.blit(msg,msg.get_rect(centerx=ta.centerx,centery=ta.centery))
            # Scroll bar
            total = self._max_scroll() + ta.h
            if total > ta.h:
                sbx=ta.right+3
                bh=max(20,int(ta.h*ta.h/total))
                by=ta.y+int(self._scroll/total*ta.h)
                pygame.draw.rect(surf,(25,40,75),(sbx,ta.y,4,ta.h),border_radius=2)
                pygame.draw.rect(surf,GOLD,(sbx,by,4,bh),border_radius=2)


# ═══════════════════════════════════════════════════════════════════
# MAIN MENU
# ═══════════════════════════════════════════════════════════════════
class MainMenu:
    def __init__(self, screen, clock):
        self.screen=screen; self.clock=clock
        self.f_title = pygame.font.SysFont("Georgia", 72, bold=True)
        self.f_sub   = pygame.font.SysFont("Georgia", 18, italic=True)
        self.f_btn   = pygame.font.SysFont("Georgia", 24, bold=True)
        self.f_badge = pygame.font.SysFont("Arial",   11, bold=True)
        self.f_tiny  = pygame.font.SysFont("Arial",   12)

        BW,BH,GAP = 340,60,14
        bx = SCR_W//2-BW//2
        base_y = 320

        self._entries = [
            ("QUICK PLAY",       'quick_play','▶',(12,88,40),(20,130,58),(255,220,60),(50,180,80),True,''),
            ("LEAGUE MODE",      'league',    '🏆',(16,38,110),(26,62,170),(200,220,255),(70,110,220),True,'NEW'),
            ("CHAMPIONS LEAGUE", None,        '⭐',(18,18,40),(18,18,40),(55,60,82),(34,38,60),False,'SOON'),
            ("QUIT",             'quit',      '✕',(70,12,12),(110,20,20),(255,110,110),(160,30,30),True,''),
        ]
        self._rects = [pygame.Rect(bx, base_y+i*(BH+GAP), BW, BH)
                       for i in range(len(self._entries))]
        self._t=0.0; self._hover=-1; self._flash={}
        self._parts = make_particles(40, SCR_W, SCR_H)

    def run(self):
        while True:
            self.clock.tick(FPS)
            mx,my=pygame.mouse.get_pos()
            self._t+=0.04; self._hover=-1
            for i,r in enumerate(self._rects):
                if r.collidepoint(mx,my) and self._entries[i][7]: self._hover=i
            for k in list(self._flash):
                self._flash[k]-=1
                if self._flash[k]<=0: del self._flash[k]
            for ev in pygame.event.get():
                if ev.type==pygame.QUIT: pygame.quit();sys.exit()
                if ev.type==pygame.KEYDOWN and ev.key==pygame.K_ESCAPE:
                    pygame.quit();sys.exit()
                if ev.type==pygame.MOUSEBUTTONDOWN and ev.button==1:
                    for i,r in enumerate(self._rects):
                        if r.collidepoint(mx,my):
                            tag=self._entries[i][1]
                            if tag and self._entries[i][7]:
                                self._flash[i]=8
                                if tag=='quit': pygame.quit();sys.exit()
                                return tag
            update_particles(self._parts, SCR_W, SCR_H)
            self._draw()
            pygame.display.flip()

    def _draw(self):
        draw_stadium_bg(self.screen, self._t, SCR_W, SCR_H)
        draw_particles(self.screen, self._parts)
        draw_football(self.screen, SCR_W//2, 62, 36, self._t)
        self._draw_title()
        for i,r in enumerate(self._rects): self._draw_btn(i,r)
        ver=self.f_tiny.render("v2.0  ·  58 clubs  ·  3 leagues  ·  WASD/arrows in game",True,(42,52,78))
        self.screen.blit(ver,ver.get_rect(centerx=SCR_W//2,y=SCR_H-20))

    def _draw_title(self):
        cx=SCR_W//2
        for r2,a in [(260,14),(190,24),(120,36)]:
            g=pygame.Surface((r2*2,r2),pygame.SRCALPHA)
            pygame.draw.ellipse(g,(255,190,20,a),g.get_rect())
            self.screen.blit(g,(cx-r2,86))
        for dx,dy,col in [(4,4,(0,0,0)),(2,2,(45,22,0)),(0,0,GOLD)]:
            ts=self.f_title.render("FOOTBALL 3D",True,col)
            self.screen.blit(ts,ts.get_rect(centerx=cx+dx,y=98+dy))
        sub=self.f_sub.render("T H E   B E A U T I F U L   G A M E",True,(135,162,210))
        self.screen.blit(sub,sub.get_rect(centerx=cx,y=186))
        lw=sub.get_width()+60; lx=cx-lw//2
        for lo,lc,lh in [(0,(55,75,130),1),(4,GOLD,2),(8,(55,75,130),1)]:
            pygame.draw.line(self.screen,lc,(lx,212+lo),(lx+lw,212+lo),lh)

    def _draw_btn(self,idx,rect):
        label,tag,icon,bg,bg_h,tc,bc,enabled,badge=self._entries[idx]
        hov  = self._hover==idx and enabled
        flash= self._flash.get(idx,0)
        col  = bg_h if hov else bg
        if flash>0:
            col=tuple(int(c*(1-flash/8)+255*(flash/8)*0.25) for c in col)
        pygame.draw.rect(self.screen,col,rect,border_radius=14)
        if hov:
            gs=pygame.Surface((rect.w+14,rect.h+14),pygame.SRCALPHA)
            pygame.draw.rect(gs,(*bc,int(22+16*math.sin(self._t*2.4))),gs.get_rect(),border_radius=16)
            self.screen.blit(gs,(rect.x-7,rect.y-7))
            pygame.draw.rect(self.screen,bc,rect,3,border_radius=14)
            shim=pygame.Surface((rect.w,rect.h),pygame.SRCALPHA)
            sx=int((self._t*58)%(rect.w+90))-45
            for sw,sa in [(58,9),(30,17)]:
                pygame.draw.rect(shim,(255,255,255,sa),(sx,0,sw,rect.h))
            self.screen.blit(shim,rect.topleft)
        else:
            pygame.draw.rect(self.screen,bc if enabled else (32,38,58),rect,2,border_radius=14)
        # Icon circle
        icx=rect.x+36; icy=rect.centery
        if enabled:
            pygame.draw.circle(self.screen,tuple(min(255,c+28) for c in col),(icx,icy),19)
            pygame.draw.circle(self.screen,bc,(icx,icy),19,2)
        ic=self.f_btn.render(icon,True,tc if enabled else (48,52,68))
        self.screen.blit(ic,ic.get_rect(center=(icx,icy)))
        lbl=self.f_btn.render(label,True,tc if enabled else (48,52,68))
        self.screen.blit(lbl,lbl.get_rect(x=rect.x+66,centery=rect.centery))
        if badge:
            bc2=(255,55,55) if badge=="SOON" else (255,175,0)
            bw=self.f_badge.render(badge,True,(0,0,0)).get_width()+10
            bx2=rect.right-bw-8; by=rect.y+8
            pygame.draw.rect(self.screen,bc2,(bx2,by,bw,17),border_radius=9)
            bs=self.f_badge.render(badge,True,(10,10,10))
            self.screen.blit(bs,bs.get_rect(centerx=bx2+bw//2,centery=by+8))


# ═══════════════════════════════════════════════════════════════════
# QUICK PLAY TEAM SELECTION
# ═══════════════════════════════════════════════════════════════════
class TeamSelectScreen:
    PAD=14; GAP=14

    def __init__(self, screen, clock):
        self.screen=screen; self.clock=clock
        self.f_title  = pygame.font.SysFont("Georgia",36,bold=True)
        self.f_panel  = pygame.font.SysFont("Georgia",14,bold=True)
        self.f_country= pygame.font.SysFont("Arial",  13,bold=True)
        self.f_card   = pygame.font.SysFont("Arial",  11,bold=True)
        self.f_small  = pygame.font.SysFont("Arial",  10)
        self.f_btn    = pygame.font.SysFont("Georgia",22,bold=True)
        self.f_sum    = pygame.font.SysFont("Arial",  13,bold=True)

        self.title_zone_h = 98
        self.bottom_zone_h = 86
        ph = SCR_H - self.title_zone_h - self.bottom_zone_h - self.PAD * 2
        pw = (SCR_W-self.PAD*2-self.GAP)//2

        self.panel_a = SidePanel((self.PAD, self.title_zone_h, pw, ph),
            "YOUR TEAM",(90,210,110),
            self.f_panel,self.f_country,self.f_card,self.f_small)
        self.panel_b = SidePanel((self.PAD+pw+self.GAP,self.title_zone_h,pw,ph),
            "CPU OPPONENT",(210,100,90),
            self.f_panel,self.f_country,self.f_card,self.f_small)

        bh=54
        self.btn_play = FancyBtn("▶  KICK OFF!",
            (SCR_W//2-150,SCR_H-bh-8,300,bh),self.f_btn,
            bg=(16,76,34),bg_h=(26,116,50),tc=GOLD,bc=(40,155,65),bc_h=(80,220,100),enabled=False)
        self.btn_back = FancyBtn("← BACK",
            (self.PAD,SCR_H-bh-8,130,bh),self.f_btn,
            bg=(24,24,50),bg_h=(40,40,88),tc=WHITE)
        self._t=0.0
        self._parts=make_particles(30,SCR_W,SCR_H)

    def _refresh(self):
        ka=self.panel_a.selected_team; kb=self.panel_b.selected_team
        self.panel_a.set_exclude(kb); self.panel_b.set_exclude(ka)
        self.btn_play.enabled=(ka is not None and kb is not None and ka!=kb)

    def run(self):
        while True:
            self.clock.tick(FPS)
            mx,my=pygame.mouse.get_pos(); self._t+=0.04
            for ev in pygame.event.get():
                if ev.type==pygame.QUIT: pygame.quit();sys.exit()
                if ev.type==pygame.KEYDOWN and ev.key==pygame.K_ESCAPE: return None
                r=self.panel_a.handle_event(ev)
                if r: self._refresh()
                r=self.panel_b.handle_event(ev)
                if r: self._refresh()
                if ev.type==pygame.MOUSEBUTTONDOWN and ev.button==1:
                    if self.btn_back.clicked(mx,my): return None
                    if self.btn_play.clicked(mx,my):
                        return(self.panel_a.selected_team,self.panel_b.selected_team)
            self.panel_a.update(mx,my); self.panel_b.update(mx,my)
            self.btn_play.update(mx,my); self.btn_back.update(mx,my)
            update_particles(self._parts,SCR_W,SCR_H)
            self._draw()
            pygame.display.flip()

    def _draw(self):
        draw_stadium_bg(self.screen,self._t,SCR_W,SCR_H,grass_frac=0.82)
        draw_particles(self.screen,self._parts)

        draw_page_title(self.screen,"CHOOSE YOUR TEAMS",
            pygame.font.SysFont("Georgia",34,bold=True),
            SCR_W//2, 8, GOLD,
            sub="Pick a country, then select your club",
            sub_font=pygame.font.SysFont("Georgia",14,italic=True))

        self.panel_a.draw(self.screen)
        self.panel_b.draw(self.screen)

        # VS badge
        cx=SCR_W//2
        vs_surf=pygame.Surface((54,54),pygame.SRCALPHA)
        pygame.draw.circle(vs_surf,(14,22,55,230),(27,27),27)
        pygame.draw.circle(vs_surf,GOLD,(27,27),27,2)
        self.screen.blit(vs_surf,(cx-27,SCR_H//2-27))
        vs=pygame.font.SysFont("Georgia",18,bold=True).render("VS",True,GOLD)
        self.screen.blit(vs,vs.get_rect(centerx=cx,centery=SCR_H//2))

        # Bottom action shelf
        shelf_y = SCR_H - self.bottom_zone_h + 6
        glass_panel(self.screen,(16,shelf_y,SCR_W-32,self.bottom_zone_h-14),tint=(6,12,34),alpha=208,border=(38,54,100),radius=18)

        # Summary bar
        ka=self.panel_a.selected_team; kb=self.panel_b.selected_team
        a_n=TEAMS[ka]['name'] if ka else 'pick country then club'
        b_n=TEAMS[kb]['name'] if kb else 'pick country then club'
        glass_panel(self.screen,(SCR_W//2-340,shelf_y+4,680,30),tint=(8,14,40),alpha=220,border=(34,48,88),radius=12)
        sum_s=self.f_sum.render(f"You: {a_n}    vs    CPU: {b_n}",True,(170,184,214))
        self.screen.blit(sum_s,sum_s.get_rect(centerx=SCR_W//2,centery=shelf_y+19))

        self.btn_play.draw(self.screen)
        self.btn_back.draw(self.screen)
