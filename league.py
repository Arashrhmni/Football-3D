"""league.py – League season system with beautiful screens."""
import pygame, sys, math, random, itertools
from constants import SCR_W, SCR_H, FPS, TEAMS
from shared_ui import (
    GOLD, WHITE, GREY, PANEL_BG,
    draw_stadium_bg, make_particles, update_particles, draw_particles,
    draw_football, draw_kit, draw_flag, glass_panel, gold_divider,
    draw_page_title, FancyBtn, CountryTab, TeamCard, FLAG_DATA
)

COUNTRY_TEAMS = {}
for _k,_d in TEAMS.items():
    COUNTRY_TEAMS.setdefault(_d['country'],[]).append(_k)

LEAGUE_NAMES = {
    'Spain':   'La Primera',
    'England': 'The Premier League',
    'Germany': 'Die Bundesliga',
}
LEAGUE_ACCENT = {
    'Spain':   (230,  60,  40),
    'England': ( 60, 120, 220),
    'Germany': (220, 185,   0),
}


# ── Data model ────────────────────────────────────────────────────
class TeamRecord:
    def __init__(self, key):
        self.key=key; self.name=TEAMS[key]['name']; self.col=TEAMS[key]['hud_col']
        self.P=self.W=self.D=self.L=self.GF=self.GA=self.pts=0
    @property
    def GD(self): return self.GF-self.GA
    def add_result(self,gf,ga):
        self.P+=1; self.GF+=gf; self.GA+=ga
        if gf>ga:   self.W+=1; self.pts+=3
        elif gf==ga: self.D+=1; self.pts+=1
        else:        self.L+=1

class Fixture:
    def __init__(self,home,away,md):
        self.home=home; self.away=away; self.matchday=md
        self.played=False; self.home_goals=self.away_goals=0
    def simulate(self):
        h,a=random.randint(0,3),random.randint(0,3)
        self.home_goals=h; self.away_goals=a; self.played=True
        return h,a
    def set_result(self,h,a):
        self.home_goals=h; self.away_goals=a; self.played=True

class LeagueState:
    def __init__(self,country,human_key):
        self.country=country; self.human_key=human_key
        self.league_name=LEAGUE_NAMES.get(country,country)
        self.team_keys=COUNTRY_TEAMS[country][:]
        self.records={k:TeamRecord(k) for k in self.team_keys}
        self.fixtures=[]; self.matchday=1
        self._gen_fixtures()

    def _gen_fixtures(self):
        teams=self.team_keys[:]
        if len(teams)%2==1: teams.append('__bye__')
        n2=len(teams); half=n2//2; lst=teams[1:]
        days1=[]
        for rnd in range(n2-1):
            rot=lst[rnd:]+lst[:rnd]
            pairs=[(teams[0],rot[0])]+[(rot[i],rot[n2-2-i]) for i in range(1,half)]
            days1.append(pairs)
        all_days=days1+[[(b,a) for a,b in day] for day in days1]
        md=1
        for day in all_days:
            for h,a in day:
                if '__bye__' not in (h,a):
                    self.fixtures.append(Fixture(h,a,md))
            md+=1
        self.total_matchdays=md-1

    def current_fixtures(self):
        return [f for f in self.fixtures if f.matchday==self.matchday and not f.played]
    def human_fixture_today(self):
        for f in self.current_fixtures():
            if self.human_key in (f.home,f.away): return f
        return None
    def simulate_matchday(self,skip_human=True):
        for f in self.current_fixtures():
            if skip_human and self.human_key in (f.home,f.away): continue
            h,a=f.simulate()
            self.records[f.home].add_result(h,a)
            self.records[f.away].add_result(a,h)
    def apply_result(self,fix,hg,ag):
        fix.set_result(hg,ag)
        self.records[fix.home].add_result(hg,ag)
        self.records[fix.away].add_result(ag,hg)
    def advance_matchday(self): self.matchday+=1
    def sorted_table(self):
        recs=list(self.records.values())
        recs.sort(key=lambda r:(-r.pts,-r.GD,-r.GF,r.name))
        return recs
    @property
    def season_over(self): return self.matchday>self.total_matchdays


# ── LEAGUE SETUP SCREEN ───────────────────────────────────────────
class LeagueSetupScreen:
    COUNTRY_ORDER=['Spain','England','Germany']
    CW,CH=140,108; CGAP=10

    def __init__(self,screen,clock):
        self.screen=screen; self.clock=clock
        self.f_title  = pygame.font.SysFont("Georgia",40,bold=True)
        self.f_sub    = pygame.font.SysFont("Georgia",16,italic=True)
        self.f_ctry   = pygame.font.SysFont("Arial",  14,bold=True)
        self.f_card   = pygame.font.SysFont("Arial",  11,bold=True)
        self.f_small  = pygame.font.SysFont("Arial",  10)
        self.f_btn    = pygame.font.SysFont("Georgia",22,bold=True)
        self.f_lname  = pygame.font.SysFont("Georgia",28,bold=True)

        self.sel_country=None; self.sel_team=None; self._scroll=0
        self._tabs=[]; self._cards=[]

        # Country tabs — horizontal row near top
        tab_w,tab_h,tab_gap=195,64,14
        total_w=len(self.COUNTRY_ORDER)*(tab_w+tab_gap)-tab_gap
        tx=SCR_W//2-total_w//2
        for country in self.COUNTRY_ORDER:
            self._tabs.append(CountryTab(country,(tx,115,tab_w,tab_h),self.f_ctry))
            tx+=tab_w+tab_gap

        self.GRID_X=55; self.GRID_Y=210
        self.GRID_W=SCR_W-110; self.GRID_H=SCR_H-290

        bh=50
        self.btn_start=FancyBtn("▶  START SEASON",
            (SCR_W//2-140,SCR_H-bh-10,280,bh),self.f_btn,
            bg=(16,76,34),bg_h=(26,116,50),tc=GOLD,bc=(40,155,65),bc_h=(80,220,100),
            enabled=False)
        self.btn_back=FancyBtn("← BACK",
            (18,SCR_H-bh-10,120,bh),self.f_btn,
            bg=(24,24,50),bg_h=(40,40,88),tc=WHITE)
        self._t=0.0
        self._parts=make_particles(35,SCR_W,SCR_H)

    def _build_cards(self):
        self._cards=[]; self._scroll=0
        if not self.sel_country: return
        keys=COUNTRY_TEAMS.get(self.sel_country,[])
        gw=self.GRID_W; cw,ch=self.CW,self.CH; g=self.CGAP
        cols=max(1,(gw+g)//(cw+g))
        for i,key in enumerate(keys):
            c2=i%cols; r2=i//cols
            x=self.GRID_X+c2*(cw+g); y=self.GRID_Y+r2*(ch+g)
            card=TeamCard(key,(x,y,cw,ch),self.f_card,self.f_small)
            if key==self.sel_team: card.selected=True
            self._cards.append(card)

    def _max_scroll(self):
        if not self._cards: return 0
        return max(0,max(c.rect.bottom for c in self._cards)-(self.GRID_Y+self.GRID_H))

    def _grid_rect(self):
        return pygame.Rect(self.GRID_X,self.GRID_Y,self.GRID_W,self.GRID_H)

    def handle_event(self,ev):
        gr=self._grid_rect()
        if ev.type==pygame.MOUSEBUTTONDOWN:
            if ev.button==4 and gr.collidepoint(ev.pos):
                self._scroll=max(0,self._scroll-38)
            elif ev.button==5 and gr.collidepoint(ev.pos):
                self._scroll=min(self._max_scroll(),self._scroll+38)
            elif ev.button==1:
                for tab in self._tabs:
                    if tab.clicked(*ev.pos):
                        if tab.country!=self.sel_country:
                            self.sel_country=tab.country; self.sel_team=None
                            self._build_cards()
                        for t in self._tabs: t.selected=(t.country==tab.country)
                        self.btn_start.enabled=False
                        return
                for card in self._cards:
                    sr=pygame.Rect(card.rect.x,card.rect.y-self._scroll,card.rect.w,card.rect.h)
                    if sr.collidepoint(*ev.pos) and gr.collidepoint(*ev.pos):
                        for c in self._cards: c.selected=False
                        card.selected=True; self.sel_team=card.key
                        self.btn_start.enabled=True

    def update(self,mx,my):
        for tab in self._tabs: tab.update(mx,my)
        gr=self._grid_rect()
        for card in self._cards:
            sr=pygame.Rect(card.rect.x,card.rect.y-self._scroll,card.rect.w,card.rect.h)
            card._hov=sr.collidepoint(mx,my) and gr.collidepoint(mx,my)
        self.btn_start.update(mx,my); self.btn_back.update(mx,my)

    def run(self):
        while True:
            self.clock.tick(FPS)
            mx,my=pygame.mouse.get_pos(); self._t+=0.04
            for ev in pygame.event.get():
                if ev.type==pygame.QUIT: pygame.quit();sys.exit()
                if ev.type==pygame.KEYDOWN and ev.key==pygame.K_ESCAPE: return None
                self.handle_event(ev)
                if ev.type==pygame.MOUSEBUTTONDOWN and ev.button==1:
                    if self.btn_back.clicked(mx,my): return None
                    if self.btn_start.clicked(mx,my):
                        return LeagueState(self.sel_country,self.sel_team)
            self.update(mx,my)
            update_particles(self._parts,SCR_W,SCR_H)
            self._draw()
            pygame.display.flip()

    def _draw(self):
        draw_stadium_bg(self.screen,self._t,SCR_W,SCR_H)
        draw_particles(self.screen,self._parts)
        draw_football(self.screen,SCR_W//2,38,26,self._t)
        draw_page_title(self.screen,"LEAGUE MODE",
            pygame.font.SysFont("Georgia",38,bold=True),
            SCR_W//2,48,GOLD,
            sub="Choose a league, then pick your club",
            sub_font=pygame.font.SysFont("Georgia",14,italic=True))

        # Country tabs
        for tab in self._tabs: tab.draw(self.screen)

        # League name banner when country picked
        if self.sel_country:
            accent=LEAGUE_ACCENT.get(self.sel_country,GOLD)
            lname=LEAGUE_NAMES.get(self.sel_country,'')
            banner=pygame.Surface((SCR_W-80,32),pygame.SRCALPHA)
            pygame.draw.rect(banner,(*accent,22),banner.get_rect(),border_radius=8)
            self.screen.blit(banner,(40,193))
            ln=self.f_lname.render(lname,True,accent)
            self.screen.blit(ln,ln.get_rect(centerx=SCR_W//2,centery=209))

        # Team card grid
        gr=self._grid_rect()
        if not self.sel_country:
            glass_panel(self.screen,gr,alpha=100)
            h=pygame.font.SysFont("Georgia",18,italic=True).render(
                "← Select a league above",True,(60,80,140))
            self.screen.blit(h,h.get_rect(centerx=gr.centerx,centery=gr.centery))
        else:
            clip=pygame.Surface((gr.w,gr.h),pygame.SRCALPHA)
            for card in self._cards:
                cr=pygame.Rect(card.rect.x-gr.x,card.rect.y-gr.y-self._scroll,
                               card.rect.w,card.rect.h)
                if cr.bottom<0 or cr.top>gr.h: continue
                tmp=TeamCard(card.key,cr,self.f_card,self.f_small)
                tmp.selected=card.selected; tmp._hov=card._hov; tmp._t=card._t
                tmp.draw(clip)
            self.screen.blit(clip,gr.topleft)
            total=self._max_scroll()+gr.h
            if total>gr.h:
                sbx=gr.right+4; bh2=max(20,int(gr.h*gr.h/total))
                by2=gr.y+int(self._scroll/total*gr.h)
                pygame.draw.rect(self.screen,(22,36,72),(sbx,gr.y,4,gr.h),border_radius=2)
                pygame.draw.rect(self.screen,GOLD,(sbx,by2,4,bh2),border_radius=2)

        self.btn_start.draw(self.screen); self.btn_back.draw(self.screen)


# ── LEAGUE HUB SCREEN ────────────────────────────────────────────
class LeagueHubScreen:
    def __init__(self,screen,clock,ls):
        self.screen=screen; self.clock=clock; self.ls=ls
        self.f_head = pygame.font.SysFont("Georgia",30,bold=True)
        self.f_sub  = pygame.font.SysFont("Georgia",15,bold=True)
        self.f_tbl  = pygame.font.SysFont("Arial",  13,bold=True)
        self.f_tbl_s= pygame.font.SysFont("Arial",  12)
        self.f_fix  = pygame.font.SysFont("Arial",  13,bold=True)
        self.f_btn  = pygame.font.SysFont("Georgia",19,bold=True)
        self.f_small= pygame.font.SysFont("Arial",  11)
        self._t=0.0
        self._parts=make_particles(25,SCR_W,SCR_H)
        bh=46
        self.btn_play=FancyBtn("▶  PLAY MY MATCH",
            (SCR_W-308,SCR_H-bh-10,288,bh),self.f_btn,
            bg=(16,76,34),bg_h=(26,116,50),tc=GOLD,bc=(40,155,65),bc_h=(80,220,100))
        self.btn_sim=FancyBtn("⏩  SIMULATE MATCHDAY",
            (SCR_W-308,SCR_H-bh*2-22,288,bh),self.f_btn,
            bg=(28,28,80),bg_h=(48,48,140),tc=WHITE)
        self.btn_back=FancyBtn("← MENU",
            (14,SCR_H-bh-10,115,bh),self.f_btn,
            bg=(24,24,50),bg_h=(40,40,88),tc=WHITE)
        self._refresh()

    def _refresh(self):
        hf=self.ls.human_fixture_today()
        self.btn_play.enabled=(hf is not None) and not self.ls.season_over
        self.btn_sim.enabled=not self.ls.season_over

    def run(self):
        self._refresh()
        while True:
            self.clock.tick(FPS)
            mx,my=pygame.mouse.get_pos(); self._t+=0.04
            for ev in pygame.event.get():
                if ev.type==pygame.QUIT: pygame.quit();sys.exit()
                if ev.type==pygame.KEYDOWN and ev.key==pygame.K_ESCAPE: return'back'
                if ev.type==pygame.MOUSEBUTTONDOWN and ev.button==1:
                    if self.btn_back.clicked(mx,my): return'back'
                    if self.btn_play.clicked(mx,my): return'play'
                    if self.btn_sim.clicked(mx,my): return'sim'
            self.btn_play.update(mx,my)
            self.btn_sim.update(mx,my)
            self.btn_back.update(mx,my)
            update_particles(self._parts,SCR_W,SCR_H)
            self._draw()
            pygame.display.flip()

    def _draw(self):
        draw_stadium_bg(self.screen,self._t,SCR_W,SCR_H,grass_frac=0.88)
        draw_particles(self.screen,self._parts)
        accent=LEAGUE_ACCENT.get(self.ls.country,GOLD)

        # Header bar
        hbar=pygame.Surface((SCR_W,50),pygame.SRCALPHA)
        pygame.draw.rect(hbar,(*accent,28),(0,0,SCR_W,50))
        self.screen.blit(hbar,(0,0))
        draw_football(self.screen,38,25,18,self._t)
        ht=self.f_head.render(
            f"{self.ls.league_name}   Matchday {self.ls.matchday} / {self.ls.total_matchdays}",
            True,accent)
        self.screen.blit(ht,ht.get_rect(x=66,centery=25))
        if self.ls.season_over:
            done=self.f_sub.render("SEASON COMPLETE",True,(120,230,120))
            self.screen.blit(done,done.get_rect(right=SCR_W-14,centery=25))
        gold_divider(self.screen,52,SCR_W,margin=20)

        # ── LEFT: Standings table ────────────────────────────────
        TBL_X,TBL_Y=12,60; TBL_W=580
        COL_W=[26,196,28,28,28,28,42,42,46]
        LABELS=['','Club','P','W','D','L','GF','GA','Pts']
        # Header
        glass_panel(self.screen,(TBL_X,TBL_Y,TBL_W,22),tint=(8,14,38),alpha=220,
                    border=accent,radius=6)
        cx2=TBL_X+4
        for lbl,cw in zip(LABELS,COL_W):
            s=self.f_tbl.render(lbl,True,accent)
            self.screen.blit(s,(cx2+cw//2-s.get_width()//2,TBL_Y+3))
            cx2+=cw

        table=self.ls.sorted_table(); ROW_H=21
        for rank,rec in enumerate(table):
            ry=TBL_Y+24+rank*ROW_H
            if ry>SCR_H-110: break
            is_h=(rec.key==self.ls.human_key)
            glass_panel(self.screen,(TBL_X,ry,TBL_W,ROW_H-1),
                        tint=(18,44,26) if is_h else (8,14,40),
                        alpha=190,border=accent if rank==0 else
                        ((40,155,65) if is_h else (28,38,72)),radius=4)
            cx2=TBL_X+4
            vals=[str(rank+1),rec.name,str(rec.P),str(rec.W),str(rec.D),
                  str(rec.L),str(rec.GF),str(rec.GA),str(rec.pts)]
            for i,(val,cw) in enumerate(zip(vals,COL_W)):
                if i==1:
                    txt=val
                    s=self.f_tbl_s.render(txt,True,rec.col if is_h else (175,180,205))
                    while s.get_width()>cw-4 and len(txt)>4:
                        txt=txt[:-1]; s=self.f_tbl_s.render(txt+'…',True,rec.col if is_h else (175,180,205))
                else:
                    fc=accent if i==len(vals)-1 else (WHITE if is_h else GREY)
                    s=self.f_tbl_s.render(val,True,fc)
                self.screen.blit(s,(cx2+cw//2-s.get_width()//2,ry+4))
                cx2+=cw

        # ── RIGHT: Fixtures panel ────────────────────────────────
        FIX_X=TBL_X+TBL_W+18; FIX_W=SCR_W-FIX_X-14
        glass_panel(self.screen,(FIX_X,TBL_Y,FIX_W,SCR_H-TBL_Y-110),
                    tint=(8,14,38),alpha=210,border=(40,56,100))
        # Section label
        sec=self.f_sub.render(
            f"Matchday {self.ls.matchday} Fixtures" if not self.ls.season_over else "Season Complete",
            True,accent)
        self.screen.blit(sec,sec.get_rect(x=FIX_X+10,y=TBL_Y+6))
        pygame.draw.line(self.screen,(*accent,120),
                         (FIX_X+8,TBL_Y+26),(FIX_X+FIX_W-8,TBL_Y+26),1)

        fy=TBL_Y+32
        fixtures_today=[f for f in self.ls.fixtures if f.matchday==self.ls.matchday]
        for fix in fixtures_today:
            is_hf=(fix.home==self.ls.human_key or fix.away==self.ls.human_key)
            fh=33
            tint=(16,46,22) if is_hf else (10,16,42)
            bc2=(50,180,70) if is_hf else (36,50,88)
            glass_panel(self.screen,(FIX_X+6,fy,FIX_W-12,fh),tint=tint,alpha=210,
                        border=bc2,radius=8)
            h_n=TEAMS[fix.home]['name']; a_n=TEAMS[fix.away]['name']
            h_c=TEAMS[fix.home]['hud_col']; a_c=TEAMS[fix.away]['hud_col']
            mid=FIX_X+FIX_W//2
            if fix.played:
                st=self.f_fix.render(
                    f"{h_n}  {fix.home_goals} – {fix.away_goals}  {a_n}",
                    True,(140,230,140) if is_hf else (160,175,200))
                self.screen.blit(st,st.get_rect(centerx=mid,centery=fy+fh//2))
            else:
                hs=self.f_fix.render(h_n,True,h_c)
                vs=self.f_fix.render("vs",True,(80,90,120))
                as_=self.f_fix.render(a_n,True,a_c)
                self.screen.blit(vs,vs.get_rect(centerx=mid,centery=fy+fh//2))
                self.screen.blit(hs,hs.get_rect(right=mid-16,centery=fy+fh//2))
                self.screen.blit(as_,as_.get_rect(x=mid+16,centery=fy+fh//2))
                if is_hf:
                    you=self.f_small.render("YOUR MATCH",True,(90,215,90))
                    self.screen.blit(you,you.get_rect(right=FIX_X+FIX_W-10,centery=fy+fh//2))
            fy+=fh+4
            if fy>SCR_H-120:
                more=self.f_small.render("…more fixtures",True,(55,68,100))
                self.screen.blit(more,(FIX_X+8,fy)); break

        # Kit previews for human fixture
        hf=self.ls.human_fixture_today()
        if hf:
            ky=SCR_H-100; kx=FIX_X+FIX_W//2
            draw_kit(self.screen,kx-44,ky,TEAMS[hf.home])
            draw_kit(self.screen,kx+44,ky,TEAMS[hf.away])
            vs2=self.f_small.render("vs",True,(80,90,120))
            self.screen.blit(vs2,vs2.get_rect(centerx=kx,centery=ky))

        self.btn_play.draw(self.screen)
        self.btn_sim.draw(self.screen)
        self.btn_back.draw(self.screen)


# ── POST-MATCH SCREEN ────────────────────────────────────────────
class PostMatchScreen:
    def __init__(self,screen,clock,ls,fixture):
        self.screen=screen; self.clock=clock; self.ls=ls; self.fix=fixture
        self.f_xl   = pygame.font.SysFont("Georgia",58,bold=True)
        self.f_big  = pygame.font.SysFont("Georgia",34,bold=True)
        self.f_score= pygame.font.SysFont("Georgia",52,bold=True)
        self.f_med  = pygame.font.SysFont("Georgia",20,bold=True)
        self.f_btn  = pygame.font.SysFont("Georgia",20,bold=True)
        self.f_small= pygame.font.SysFont("Arial",  13)
        self._timer =FPS*4
        self._t=0.0
        self._parts=make_particles(50,SCR_W,SCR_H,seed=99)
        self.btn=FancyBtn("CONTINUE  →",
            (SCR_W//2-130,SCR_H-72,260,50),self.f_btn,
            bg=(16,76,34),bg_h=(26,116,50),tc=GOLD,bc=(40,155,65),bc_h=(80,220,100))

    def run(self):
        while True:
            self.clock.tick(FPS); self._timer-=1; self._t+=0.05
            mx,my=pygame.mouse.get_pos(); self.btn.update(mx,my)
            for ev in pygame.event.get():
                if ev.type==pygame.QUIT: pygame.quit();sys.exit()
                if ev.type==pygame.KEYDOWN: return
                if ev.type==pygame.MOUSEBUTTONDOWN and ev.button==1:
                    if self.btn.clicked(mx,my): return
            if self._timer<=0: return
            update_particles(self._parts,SCR_W,SCR_H)
            self._draw()
            pygame.display.flip()

    def _draw(self):
        fix=self.fix; hk=self.ls.human_key
        winner=(fix.home if fix.home_goals>fix.away_goals else
                fix.away if fix.away_goals>fix.home_goals else None)
        is_win=(winner==hk); is_draw=(winner is None)
        result_txt="DRAW!" if is_draw else ("VICTORY!" if is_win else "DEFEAT!")
        result_col=(255,215,0) if is_draw else ((80,240,120) if is_win else (255,75,75))
        accent_bg =(10,60,20) if is_win else ((30,30,10) if is_draw else (60,10,10))

        # Background — tinted by result
        for y in range(SCR_H):
            f=y/SCR_H
            r=int(accent_bg[0]+10*f); g2=int(accent_bg[1]+16*f); b=int(accent_bg[2]+30*f)
            pygame.draw.line(self.screen,(r,g2,b),(0,y),(SCR_W,y))
        draw_stadium_bg(self.screen,self._t,SCR_W,SCR_H,grass_frac=0.92)
        draw_particles(self.screen,self._parts)

        # Result word — large glow
        cx=SCR_W//2
        for r2,a in [(240,14),(170,24),(100,38)]:
            g3=pygame.Surface((r2*2,90),pygame.SRCALPHA)
            pygame.draw.ellipse(g3,(*result_col,a),g3.get_rect())
            self.screen.blit(g3,(cx-r2,120))
        for dx,dy,col in [(4,4,(0,0,0)),(0,0,result_col)]:
            rs=self.f_xl.render(result_txt,True,col)
            self.screen.blit(rs,rs.get_rect(centerx=cx+dx,y=130+dy))

        # Score box
        glass_panel(self.screen,(cx-280,230,560,90),tint=(8,14,40),alpha=230,
                    border=result_col,radius=16)
        # Kit previews
        draw_kit(self.screen,cx-200,275,TEAMS[fix.home])
        draw_kit(self.screen,cx+200,275,TEAMS[fix.away])
        # Score
        sc=self.f_score.render(f"{fix.home_goals}  –  {fix.away_goals}",True,WHITE)
        self.screen.blit(sc,sc.get_rect(centerx=cx,y=238))
        # Team names
        hn=self.f_med.render(TEAMS[fix.home]['name'],True,TEAMS[fix.home]['hud_col'])
        an=self.f_med.render(TEAMS[fix.away]['name'],True,TEAMS[fix.away]['hud_col'])
        self.screen.blit(hn,hn.get_rect(right=cx-160,centery=275))
        self.screen.blit(an,an.get_rect(x=cx+160,centery=275))

        # League position strip
        table=self.ls.sorted_table()
        for pos,rec in enumerate(table):
            if rec.key==hk:
                glass_panel(self.screen,(cx-220,344,440,36),tint=(8,14,48),alpha=220,
                            border=(50,70,120),radius=10)
                pt=self.f_med.render(
                    f"League Position:  {pos+1} / {len(table)}   ·   {rec.pts} pts   ·   GD {rec.GD:+d}",
                    True,(155,175,220))
                self.screen.blit(pt,pt.get_rect(centerx=cx,centery=362))
                break

        # Next matchday teaser
        next_md=self.ls.matchday+1
        if next_md<=self.ls.total_matchdays:
            nxt=self.f_small.render(f"Next:  Matchday {next_md}",True,(80,100,150))
            self.screen.blit(nxt,nxt.get_rect(centerx=cx,y=400))

        cd=max(0,self._timer//FPS)
        hint=self.f_small.render(f"Auto-continuing in {cd}s  ·  any key or click",True,(65,80,115))
        self.screen.blit(hint,hint.get_rect(centerx=cx,y=SCR_H-100))
        self.btn.draw(self.screen)


# ── SEASON END SCREEN ────────────────────────────────────────────
class SeasonEndScreen:
    def __init__(self,screen,clock,ls):
        self.screen=screen; self.clock=clock; self.ls=ls
        self.f_xl  = pygame.font.SysFont("Georgia",54,bold=True)
        self.f_big = pygame.font.SysFont("Georgia",28,bold=True)
        self.f_tbl = pygame.font.SysFont("Arial",  13,bold=True)
        self.f_tbl2= pygame.font.SysFont("Arial",  12)
        self.f_btn = pygame.font.SysFont("Georgia",20,bold=True)
        self._t=0.0
        self._parts=make_particles(60,SCR_W,SCR_H,seed=123)
        self.btn=FancyBtn("← MAIN MENU",
            (SCR_W//2-140,SCR_H-68,280,50),self.f_btn,
            bg=(24,24,50),bg_h=(40,40,88),tc=WHITE)

    def run(self):
        while True:
            self.clock.tick(FPS); self._t+=0.04
            mx,my=pygame.mouse.get_pos(); self.btn.update(mx,my)
            for ev in pygame.event.get():
                if ev.type==pygame.QUIT: pygame.quit();sys.exit()
                if ev.type==pygame.MOUSEBUTTONDOWN and ev.button==1:
                    if self.btn.clicked(mx,my): return
            update_particles(self._parts,SCR_W,SCR_H)
            self._draw()
            pygame.display.flip()

    def _draw(self):
        draw_stadium_bg(self.screen,self._t,SCR_W,SCR_H,grass_frac=0.9)
        draw_particles(self.screen,self._parts)
        accent=LEAGUE_ACCENT.get(self.ls.country,GOLD)

        # Trophy glow
        cx=SCR_W//2
        for r2,a in [(300,10),(220,18),(140,30)]:
            g=pygame.Surface((r2*2,100),pygame.SRCALPHA)
            pygame.draw.ellipse(g,(*accent,a),g.get_rect())
            self.screen.blit(g,(cx-r2,8))

        draw_page_title(self.screen,"SEASON OVER",
            pygame.font.SysFont("Georgia",50,bold=True),
            cx,14,accent)

        table=self.ls.sorted_table(); champ=table[0]
        is_champ=(champ.key==self.ls.human_key)
        glass_panel(self.screen,(cx-320,98,640,44),
                    tint=(18,14,4) if is_champ else (8,14,40),
                    alpha=230,border=GOLD if is_champ else (50,70,120),radius=12)
        sub_txt=f"🏆  {champ.name}  are Champions!"+("   THAT'S YOU!" if is_champ else "")
        sub=self.f_big.render(sub_txt,True,GOLD if is_champ else (190,195,215))
        self.screen.blit(sub,sub.get_rect(centerx=cx,centery=120))

        # Full table
        COL_W=[26,208,30,30,30,30,40,40,48]
        LABELS=['','Club','P','W','D','L','GF','GA','Pts']
        TW=sum(COL_W); TX=cx-TW//2; TY=152
        glass_panel(self.screen,(TX,TY,TW,22),tint=(8,14,38),alpha=230,
                    border=accent,radius=6)
        cx2=TX+4
        for lbl,cw in zip(LABELS,COL_W):
            s=self.f_tbl.render(lbl,True,accent)
            self.screen.blit(s,(cx2+cw//2-s.get_width()//2,TY+3)); cx2+=cw

        ROW_H=20
        for rank,rec in enumerate(table):
            ry=TY+24+rank*ROW_H
            if ry>SCR_H-80: break
            is_h=(rec.key==self.ls.human_key)
            glass_panel(self.screen,(TX,ry,TW,ROW_H-1),
                        tint=(18,44,26) if is_h else (8,14,40),
                        alpha=195,
                        border=GOLD if rank==0 else ((40,155,65) if is_h else (28,38,72)),
                        radius=4)
            vals=[str(rank+1),rec.name,str(rec.P),str(rec.W),str(rec.D),
                  str(rec.L),str(rec.GF),str(rec.GA),str(rec.pts)]
            cx2=TX+4
            for i,(val,cw) in enumerate(zip(vals,COL_W)):
                if i==1:
                    txt=val; s=self.f_tbl2.render(txt,True,rec.col)
                    while s.get_width()>cw-4 and len(txt)>4:
                        txt=txt[:-1]; s=self.f_tbl2.render(txt+'…',True,rec.col)
                else:
                    fc=accent if i==len(vals)-1 else (WHITE if is_h else GREY)
                    s=self.f_tbl2.render(val,True,fc)
                self.screen.blit(s,(cx2+cw//2-s.get_width()//2,ry+3)); cx2+=cw

        self.btn.draw(self.screen)
