"""
╔══════════════════════════════════════════════════════════╗
║    FOOTBALL 3D — Barcelona vs Real Madrid  (11v11)       ║
╠══════════════════════════════════════════════════════════╣
║  MOVE        Arrow Keys / WASD                           ║
║  SPRINT      Z  (hold)                                   ║
║  PASS        SPACE  → auto-switches to receiver          ║
║  CROSS       C  (near byline, whips ball into box)       ║
║  SHOOT       Hold F/Shift → release for power shot       ║
║  TACKLE      X  (near opponent)                          ║
║  SWITCH      TAB                                         ║
║  QUIT        ESC  only                                   ║
╚══════════════════════════════════════════════════════════╝
"""

import pygame, math, random, sys

# ═══════════════════════════════════════════════════════════════════
#  WORLD DIMENSIONS
# ═══════════════════════════════════════════════════════════════════
W_W, W_H = 1260, 810
W_MX, W_MY = W_W//2, W_H//2

GOAL_W       = 145
GOAL_TOP     = W_MY - GOAL_W//2
GOAL_BOT     = W_MY + GOAL_W//2
GOAL_DEPTH_W = 40
GOAL_H_Z     = 78

# Pitch markings
PA_W, PA_H   = 190, 400
SB_W, SB_H   =  62, 180
CTR_R        =  92

# Outside area (run-off around pitch)
OUT_L, OUT_T   = 90, 70      # extra space left/top
OUT_R, OUT_B   = 90, 70      # extra space right/bottom

# ═══════════════════════════════════════════════════════════════════
#  ISOMETRIC PROJECTION
# ═══════════════════════════════════════════════════════════════════
SCR_W, SCR_H = 1280, 800
_SC   = 0.60
ISO_SX = math.cos(math.radians(30)) * _SC
ISO_SY = math.sin(math.radians(30)) * _SC
ISO_CX = SCR_W // 2
ISO_CY = SCR_H // 2 + 55
ISO_VZ = 1.08

def w2s(wx, wy, wz=0.0):
    sx = (wx - W_MX)*ISO_SX - (wy - W_MY)*ISO_SX + ISO_CX
    sy = (wx - W_MX)*ISO_SY + (wy - W_MY)*ISO_SY - wz*ISO_VZ + ISO_CY
    return int(sx), int(sy)

# ═══════════════════════════════════════════════════════════════════
#  PHYSICS CONSTANTS
# ═══════════════════════════════════════════════════════════════════
FPS          = 60
PLAYER_R     = 14
BALL_R       = 7
PLAYER_SPD   = 3.6
SPRINT_MULT  = 1.62
BALL_FRIC    = 0.978
BALL_GRAV    = 0.52
PASS_SPD     = 11.0
CROSS_SPD    = 13.0
SHOOT_SPD    = 19.0
CONTROL_R    = 21
TACKLE_R     = 26

# AI constants
AI_WALK  = 1.9
AI_JOG   = 2.75
AI_RUN   = 3.55
AI_REACT = 44

# Dead-ball states
DB_THROW_A  = 'throw_in_A'
DB_THROW_B  = 'throw_in_B'
DB_GK_A     = 'goal_kick_A'
DB_GK_B     = 'goal_kick_B'
DB_CORNER_A = 'corner_A'
DB_CORNER_B = 'corner_B'
DB_KICK_A   = 'kickoff_A'
DB_KICK_B   = 'kickoff_B'

DB_LABELS = {
    DB_THROW_A:  "THROW-IN → BARCELONA",
    DB_THROW_B:  "THROW-IN → REAL MADRID",
    DB_GK_A:     "GOAL KICK → BARCELONA",
    DB_GK_B:     "GOAL KICK → REAL MADRID",
    DB_CORNER_A: "CORNER → BARCELONA",
    DB_CORNER_B: "CORNER → REAL MADRID",
    DB_KICK_A:   "KICK OFF → BARCELONA",
    DB_KICK_B:   "KICK OFF → REAL MADRID",
}

# ═══════════════════════════════════════════════════════════════════
#  KIT COLOURS
# ═══════════════════════════════════════════════════════════════════
BAR_BLUE   = (0, 82, 170);   BAR_RED  = (165, 17, 17)
BAR_SHORTS = (0, 82, 170);   BAR_SOCKS = (0, 82, 170)
RMA_SHIRT  = (238,238,238);  RMA_GOLD = (198,162,0)
RMA_SHORTS = (215,215,215);  RMA_SOCKS = (215,215,215)
GK_A = (255,140,0);          GK_B = (40,160,60)
SKIN_A = (222,182,142);      HAIR_A = (38,28,18)
SKIN_B = (212,176,136);      HAIR_B = (58,44,20)

# ═══════════════════════════════════════════════════════════════════
#  FORMATION 4-3-3
# ═══════════════════════════════════════════════════════════════════
FORM = [
    (0.055,0.50),  # 0  GK
    (0.22, 0.13),  # 1  LB
    (0.22, 0.37),  # 2  CB
    (0.22, 0.63),  # 3  CB
    (0.22, 0.87),  # 4  RB
    (0.46, 0.20),  # 5  LM
    (0.46, 0.50),  # 6  CM
    (0.46, 0.80),  # 7  RM
    (0.72, 0.15),  # 8  LW
    (0.72, 0.50),  # 9  ST
    (0.72, 0.85),  # 10 RW
]

# ═══════════════════════════════════════════════════════════════════
#  HELPERS
# ═══════════════════════════════════════════════════════════════════
def d2(a,b): return math.hypot(a[0]-b[0], a[1]-b[1])
def n2(vx,vy):
    m=math.hypot(vx,vy); return (vx/m,vy/m) if m>1e-9 else (0.,0.)
def clamp(v,lo,hi): return max(lo,min(hi,v))
def lerpc(a,b,t): return tuple(int(a[i]+(b[i]-a[i])*t) for i in range(3))

# ═══════════════════════════════════════════════════════════════════
#  BALL
# ═══════════════════════════════════════════════════════════════════
class Ball:
    def __init__(self): self.reset()
    def reset(self):
        self.wx=float(W_MX); self.wy=float(W_MY); self.wz=0.
        self.vx=0.; self.vy=0.; self.vz=0.
        self.owner=None; self.last_toucher=None
    def spd(self): return math.hypot(self.vx,self.vy)

    def update(self):
        if self.owner:
            fx,fy=n2(self.owner.fdx,self.owner.fdy)
            self.wx=self.owner.wx+fx*(PLAYER_R+BALL_R+1)
            self.wy=self.owner.wy+fy*(PLAYER_R+BALL_R+1)
            self.wz=self.vx=self.vy=self.vz=0.; return
        self.wx+=self.vx; self.wy+=self.vy; self.wz+=self.vz
        if self.wz>0:
            self.vz-=BALL_GRAV; self.vx*=0.999; self.vy*=0.999
        else:
            self.wz=0.
            self.vz=abs(self.vz)*0.30 if self.vz<-0.6 else 0.
            self.vx*=BALL_FRIC; self.vy*=BALL_FRIC
        if self.spd()<0.08 and self.wz==0: self.vx=self.vy=0.

    def release(self):
        if self.owner:
            self.vx=self.owner.vx*0.22; self.vy=self.owner.vy*0.22
            self.owner=None

    def kick(self,tx,ty,spd,vz_init=2.5):
        self.release()
        dx,dy=n2(tx-self.wx,ty-self.wy)
        self.vx=dx*spd; self.vy=dy*spd; self.vz=vz_init

    def draw(self,surf):
        gx,gy=w2s(self.wx,self.wy,0)
        bx,by=w2s(self.wx,self.wy,self.wz)
        sr=BALL_R
        # Shadow
        shw=pygame.Surface((sr*5,sr*3),pygame.SRCALPHA)
        alp=max(15,int(110-self.wz*1.4))
        pygame.draw.ellipse(shw,(0,0,0,alp),shw.get_rect())
        surf.blit(shw,(gx-sr*5//2,gy-sr*3//2))
        if self.wz>3:
            pygame.draw.line(surf,(140,140,140),(gx,gy),(bx,by),1)
        br=max(4,int(BALL_R*(1+self.wz*0.007)))
        # White ball
        pygame.draw.circle(surf,(255,255,255),(bx,by),br)
        pygame.draw.circle(surf,(180,180,180),(bx,by),br,1)
        # Rotating patches
        t_ang=pygame.time.get_ticks()*0.018
        for ang in [0,72,144,216,288]:
            a=math.radians(ang+t_ang)
            px=bx+int(math.cos(a)*br*0.52)
            py=by+int(math.sin(a)*br*0.52)
            pygame.draw.circle(surf,(55,55,55),(px,py),max(1,br//3))

# ═══════════════════════════════════════════════════════════════════
#  PLAYER — clean humanoid silhouette, no distracting arms
# ═══════════════════════════════════════════════════════════════════
class Player:
    def __init__(self,team,num,hx,hy,is_keeper=False):
        self.team=team; self.num=num
        self.wx=float(hx); self.wy=float(hy)
        self.home_x=float(hx); self.home_y=float(hy)
        self.vx=0.; self.vy=0.
        self.fdx=1. if team=='A' else -1.; self.fdy=0.
        self.is_keeper=is_keeper; self.selected=False
        self.react=random.randint(0,AI_REACT); self.tackle_cd=0
        self.anim_t=random.uniform(0,math.pi*2)
        # throw-in / corner animation
        self.throw_anim=0   # 0=none, 1..30=raising, -1=done
        # CPU build-up state
        self.hold_timer=0

    def _kit(self):
        if self.team=='A':
            if self.is_keeper: return GK_A,GK_A,(50,50,50),SKIN_A,HAIR_A
            return BAR_BLUE,BAR_SHORTS,BAR_SOCKS,SKIN_A,HAIR_A
        else:
            if self.is_keeper: return GK_B,(80,80,80),(80,80,80),SKIN_B,HAIR_B
            return RMA_SHIRT,RMA_SHORTS,RMA_SOCKS,SKIN_B,HAIR_B

    def move_toward(self,tx,ty,spd):
        dd=d2((self.wx,self.wy),(tx,ty))
        if dd<0.5: self.vx=self.vy=0.; return
        r=min(spd/dd,1.)
        self.vx=(tx-self.wx)*r; self.vy=(ty-self.wy)*r
        ln=math.hypot(self.vx,self.vy)
        if ln>0: self.fdx=self.vx/ln; self.fdy=self.vy/ln
        self.wx+=self.vx; self.wy+=self.vy
        # Players can go into the outside area (run-off)
        self.wx=clamp(self.wx,-OUT_L,W_W+OUT_R)
        self.wy=clamp(self.wy,-OUT_T,W_H+OUT_B)

    def draw(self,surf,ball,fnt):
        shirt,shorts,socks,skin,hair=self._kit()
        has_ball=(ball.owner is self)
        moving=math.hypot(self.vx,self.vy)>0.2
        if moving: self.anim_t+=0.28
        bob=math.sin(self.anim_t)*3.2 if moving else 0.

        gx,gy=w2s(self.wx,self.wy,0)
        bx,by=w2s(self.wx,self.wy,max(0,bob+4))

        # Ground shadow
        shw=pygame.Surface((PLAYER_R*4,PLAYER_R*2),pygame.SRCALPHA)
        pygame.draw.ellipse(shw,(0,0,0,60),shw.get_rect())
        surf.blit(shw,(gx-PLAYER_R*2,gy-PLAYER_R))

        # ── Legs (two cylinders)
        foot_r=max(3,int(PLAYER_R*0.40))
        l_fwd=PLAYER_R-2
        l_off=int(PLAYER_R*0.38)
        for sign in(-1,1):
            ph=self.anim_t+(0 if sign==-1 else math.pi)
            lb=math.sin(ph)*5 if moving else 0
            lx=bx+int(self.fdx*l_fwd)+int(self.fdy*sign*l_off)
            ly=by+int(self.fdy*l_fwd)-int(self.fdx*sign*l_off)+PLAYER_R+int(lb)
            # Sock stripe
            pygame.draw.line(surf,socks,(lx,by+PLAYER_R-3),(lx,ly-foot_r+1),5)
            # Boot
            bcol=(25,25,25) if self.team=='A' else (210,210,210)
            pygame.draw.circle(surf,bcol,(lx,ly),foot_r)
            pygame.draw.circle(surf,(0,0,0),(lx,ly),foot_r,1)

        # ── Shorts
        sw=int(PLAYER_R*1.25); sh=int(PLAYER_R*0.9)
        pygame.draw.ellipse(surf,shorts,(bx-sw,by+sh//4,sw*2,sh))

        # ── Torso (ellipse)
        tw=int(PLAYER_R*1.38); th=int(PLAYER_R*1.48)
        t_y=by-th+sh//4
        torso=(bx-tw,t_y,tw*2,th)
        pygame.draw.ellipse(surf,shirt,torso)

        # Barcelona vertical stripes
        if self.team=='A' and not self.is_keeper:
            sw2=max(4,tw//3)
            stripe_cols=[BAR_BLUE,BAR_RED,BAR_BLUE]
            for si,sc in enumerate(stripe_cols):
                rx=bx-tw+si*sw2*2
                clip=pygame.Rect(rx,t_y,sw2*2,th)
                inter=pygame.Rect(*torso).clip(clip)
                if inter.w>0 and inter.h>0:
                    sub=pygame.Surface((inter.w,inter.h),pygame.SRCALPHA)
                    sub.fill(sc)
                    surf.blit(sub,(inter.x,inter.y))
            pygame.draw.ellipse(surf,tuple(max(0,c-28) for c in shirt),torso,2)
        elif self.team=='B' and not self.is_keeper:
            pygame.draw.ellipse(surf,RMA_SHIRT,torso)
            pygame.draw.ellipse(surf,RMA_GOLD,torso,2)
        else:
            pygame.draw.ellipse(surf,tuple(max(0,c-20) for c in shirt),torso,2)

        # Jersey number
        ns=fnt.render(str(self.num),True,
                       (255,255,255) if self.team=='A' else (30,30,30))
        surf.blit(ns,(bx-ns.get_width()//2,t_y+th//2-ns.get_height()//2))

        # ── Arms — drawn as part of the torso silhouette, NOT floating circles
        # Two tapered arm shapes attached to torso sides
        arm_col=shirt
        for sign in(-1,1):
            arm_swing=math.sin(self.anim_t+sign*math.pi*0.5)*5 if moving else 0
            # Shoulder point
            sx2=bx+sign*(tw-2)
            sy2=t_y+th//4
            # Elbow point
            ex2=sx2+sign*5
            ey2=sy2+th//2+int(arm_swing*0.6)
            # Draw arm as a thick line (foreground part of body)
            pygame.draw.line(surf,arm_col,(sx2,sy2),(ex2,ey2),max(4,int(PLAYER_R*0.32)))
            # Wrist/hand — skin tone dot, small and close to body
            pygame.draw.circle(surf,skin,(ex2,ey2+3),max(3,int(PLAYER_R*0.24)))

        # ── Neck
        neck_top=t_y-1
        pygame.draw.line(surf,skin,(bx,neck_top),(bx,neck_top-5),4)

        # ── Head
        hr=int(PLAYER_R*0.70)
        hcy=neck_top-hr-1
        pygame.draw.circle(surf,skin,(bx,hcy),hr)
        pygame.draw.circle(surf,tuple(max(0,c-18) for c in skin),(bx,hcy),hr,1)
        # Hair cap
        pygame.draw.arc(surf,hair,
                        (bx-hr,hcy-hr,hr*2,hr*2),
                        math.radians(20),math.radians(160),hr)
        # Eyes (two dots, direction-aware)
        eo=max(2,hr//3)
        for sg in(-1,1):
            ex3=bx+int(self.fdx*eo*0.5)+sg*int(abs(self.fdy)*eo*0.5+max(2,hr//4))
            ey3=hcy+2
            pygame.draw.circle(surf,(25,25,25),(ex3,ey3),2)

        # ── Throw-in animation (arms raised)
        if self.throw_anim>0:
            progress=min(1.,self.throw_anim/20.)
            raise_y=int(progress*20)
            for sign in(-1,1):
                ax=bx+sign*(tw-2)
                ay=t_y+th//4-raise_y
                pygame.draw.line(surf,arm_col,(ax,t_y+th//4),(ax,ay),
                                 max(4,int(PLAYER_R*0.32)))
                pygame.draw.circle(surf,skin,(ax,ay),max(3,int(PLAYER_R*0.24)))

        # ── Selection ring
        if self.selected:
            t_ms=pygame.time.get_ticks()
            pulse=int(3+2*math.sin(t_ms*0.007))
            rc=(0,255,100) if self.team=='A' else (255,200,0)
            pygame.draw.ellipse(surf,rc,
                (gx-PLAYER_R-pulse,gy-(PLAYER_R+pulse)//2,
                 (PLAYER_R+pulse)*2,PLAYER_R+pulse),3)

        # Ball glow
        if has_ball:
            pygame.draw.ellipse(surf,(255,225,0),
                (gx-PLAYER_R-6,gy-(PLAYER_R+6)//2,(PLAYER_R+6)*2,PLAYER_R+6),2)

# ═══════════════════════════════════════════════════════════════════
#  GAME
# ═══════════════════════════════════════════════════════════════════
class Game:
    def __init__(self):
        pygame.init()
        self.screen=pygame.display.set_mode((SCR_W,SCR_H))
        pygame.display.set_caption("Football 3D — Barcelona vs Real Madrid")
        self.clock=pygame.time.Clock()
        self.f_hud=pygame.font.SysFont("Arial",13,bold=True)
        self.f_big=pygame.font.SysFont("Georgia",38,bold=True)
        self.f_med=pygame.font.SysFont("Georgia",24,bold=True)
        self.f_num=pygame.font.SysFont("Arial",9,bold=True)

        self.score=[0,0]; self.match_time=0; self.msgs=[]
        self.dead=None; self.dead_pos=(W_MX,W_MY); self.dead_timer=0
        self.throw_player=None  # player doing throw-in / corner animation
        self.charging=False; self.charge=0.
        self.ball=Ball()
        self._build_teams()
        self._kickoff('A')
        self._pitch=pygame.Surface((SCR_W,SCR_H))
        self._bake_pitch()

    # ─── Team setup ────────────────────────────────────────────────
    def _build_teams(self):
        self.ta,self.tb=[],[]
        for i,(rx,ry) in enumerate(FORM):
            hxa=rx*W_W*0.47; hxb=W_W-rx*W_W*0.47; hy=ry*W_H
            self.ta.append(Player('A',i+1,hxa,hy,is_keeper=(i==0)))
            self.tb.append(Player('B',i+1,hxb,hy,is_keeper=(i==0)))
        self.sel=self.ta[9]; self.sel.selected=True

    def _kickoff(self,side):
        self.dead=None; self.charging=False; self.charge=0.; self.throw_player=None
        self.ball.reset()
        for p in self.ta+self.tb: p.wx,p.wy=p.home_x,p.home_y; p.vx=p.vy=0.
        k=self.ta[9] if side=='A' else self.tb[9]
        k.wx=float(W_MX-(12 if side=='A' else -12)); k.wy=float(W_MY)
        self.ball.owner=k; self.ball.last_toucher=k

    def msg(self,txt,col=(255,255,255)): self.msgs.append([txt,col,220])

    # ─── Bake pitch ────────────────────────────────────────────────
    def _bake_pitch(self):
        s=self._pitch
        # Sky
        for row in range(SCR_H):
            t=row/SCR_H
            pygame.draw.line(s,lerpc((95,165,225),(38,58,98),t),(0,row),(SCR_W,row))

        # Outside area (run-off, slightly darker/different green)
        outside_corners=[
            w2s(-OUT_L,-OUT_T), w2s(W_W+OUT_R,-OUT_T),
            w2s(W_W+OUT_R,W_H+OUT_B), w2s(-OUT_L,W_H+OUT_B)
        ]
        pygame.draw.polygon(s,(28,100,28),outside_corners)

        # Grass stripes (12)
        step=W_W/12
        for i in range(12):
            x0,x1=i*step,(i+1)*step
            col=(36,125,36) if i%2==0 else (46,145,46)
            pygame.draw.polygon(s,col,[w2s(x0,0),w2s(x1,0),w2s(x1,W_H),w2s(x0,W_H)])

        # Pitch boundary
        pygame.draw.polygon(s,(255,255,255),
            [w2s(0,0),w2s(W_W,0),w2s(W_W,W_H),w2s(0,W_H)],2)

        # Halfway line + circle
        pygame.draw.line(s,(255,255,255),w2s(W_MX,0),w2s(W_MX,W_H),2)
        pts=[w2s(W_MX+CTR_R*math.cos(a),W_MY+CTR_R*math.sin(a))
             for a in[i*math.pi/24 for i in range(49)]]
        pygame.draw.lines(s,(255,255,255),False,pts,2)
        pygame.draw.circle(s,(255,255,255),w2s(W_MX,W_MY),5)

        # Penalty areas + arcs + spots
        for sx,sg in[(0,1),(W_W,-1)]:
            x1=sx+sg*PA_W; y0=W_MY-PA_H//2; y1=W_MY+PA_H//2
            pygame.draw.lines(s,(255,255,255),True,
                [w2s(sx,y0),w2s(x1,y0),w2s(x1,y1),w2s(sx,y1)],2)
            spot=sx+sg*110
            pygame.draw.circle(s,(255,255,255),w2s(spot,W_MY),4)
            arc=[w2s(spot+90*math.cos(math.radians(a)),W_MY+90*math.sin(math.radians(a)))
                 for a in range(-62,63,4)]
            if len(arc)>1: pygame.draw.lines(s,(255,255,255),False,arc,2)
            # 6-yard box
            x1b=sx+sg*SB_W; y0b=W_MY-SB_H//2; y1b=W_MY+SB_H//2
            pygame.draw.lines(s,(255,255,255),True,
                [w2s(sx,y0b),w2s(x1b,y0b),w2s(x1b,y1b),w2s(sx,y1b)],2)

        # Corner arcs
        for cx,cy in[(0,0),(W_W,0),(0,W_H),(W_W,W_H)]:
            sxs=1 if cx==0 else -1; sys2=1 if cy==0 else -1
            arc=[w2s(cx+sxs*12*math.cos(math.radians(a)),cy+sys2*12*math.sin(math.radians(a)))
                 for a in range(91)]
            if len(arc)>1: pygame.draw.lines(s,(255,255,255),False,arc,2)

        # Goals 3D
        gd=GOAL_DEPTH_W; gh=GOAL_H_Z
        for sx,sg in[(0,-1),(W_W,1)]:
            ft=w2s(sx,GOAL_TOP);   fb=w2s(sx,GOAL_BOT)
            bt=w2s(sx+sg*gd,GOAL_TOP); bb=w2s(sx+sg*gd,GOAL_BOT)
            ftt=w2s(sx,GOAL_TOP,gh);  fbt=w2s(sx,GOAL_BOT,gh)
            btt=w2s(sx+sg*gd,GOAL_TOP,gh); bbt=w2s(sx+sg*gd,GOAL_BOT,gh)
            for base,top in[(ft,ftt),(fb,fbt),(bt,btt),(bb,bbt)]:
                pygame.draw.line(s,(245,245,245),base,top,3)
            pygame.draw.line(s,(245,245,245),ftt,fbt,3)
            for a,b in[(btt,bbt),(ftt,btt),(fbt,bbt)]:
                pygame.draw.line(s,(200,200,200),a,b,2)
            # Net
            nc=(185,185,185)
            for ni in range(8):
                t2=ni/7; gy2=GOAL_TOP+t2*(GOAL_BOT-GOAL_TOP)
                pygame.draw.line(s,nc,w2s(sx,gy2),w2s(sx,gy2,gh),1)
                pygame.draw.line(s,nc,w2s(sx,gy2,gh),w2s(sx+sg*gd,gy2,gh),1)
            for ni in range(6):
                t2=ni/5; gz=t2*gh
                pygame.draw.line(s,nc,w2s(sx,GOAL_TOP,gz),w2s(sx,GOAL_BOT,gz),1)

    # ─── Draw scene ────────────────────────────────────────────────
    def draw_scene(self):
        self.screen.blit(self._pitch,(0,0))
        ents=[(p.wy,'p',p) for p in self.ta+self.tb]
        ents.append((self.ball.wy,'b',self.ball))
        ents.sort(key=lambda e:e[0])
        for _,k,o in ents:
            o.draw(self.screen,self.ball,self.f_num) if k=='p' else o.draw(self.screen)

        # Pass suggestion
        if self.ball.owner and self.ball.owner.team=='A' and not self.dead:
            tgt=self._best_pass(self.ball.owner)
            if tgt:
                s1=w2s(self.ball.owner.wx,self.ball.owner.wy,10)
                s2=w2s(tgt.wx,tgt.wy,10)
                dx,dy=s2[0]-s1[0],s2[1]-s1[1]
                n=max(3,int(math.hypot(dx,dy)//16))
                for i in range(n):
                    if i%2==0:
                        t0,t1=i/n,(i+0.55)/n
                        pygame.draw.line(self.screen,(130,255,55),
                            (int(s1[0]+dx*t0),int(s1[1]+dy*t0)),
                            (int(s1[0]+dx*t1),int(s1[1]+dy*t1)),2)
                pygame.draw.circle(self.screen,(130,255,55),w2s(tgt.wx,tgt.wy),9,2)

    # ─── HUD ───────────────────────────────────────────────────────
    def draw_hud(self):
        s=self.screen
        mins=self.match_time//(FPS*60); secs=(self.match_time//FPS)%60
        bw=340; bx=SCR_W//2-bw//2
        pygame.draw.rect(s,(8,8,8),(bx,4,bw,46),border_radius=10)
        pygame.draw.rect(s,(65,65,65),(bx,4,bw,46),2,border_radius=10)
        ta_l=self.f_hud.render("BARCELONA",True,BAR_BLUE)
        tb_l=self.f_hud.render("REAL MADRID",True,(215,215,215))
        s.blit(ta_l,(bx+10,14)); s.blit(tb_l,(bx+bw-tb_l.get_width()-10,14))
        sc=self.f_big.render(f"{self.score[0]}  -  {self.score[1]}",True,(255,255,255))
        s.blit(sc,(SCR_W//2-sc.get_width()//2,4))
        tc=self.f_hud.render(f"{mins:02d}:{secs:02d}",True,(170,170,170))
        s.blit(tc,(SCR_W//2-tc.get_width()//2,48))

        # Controls
        ctrl=[("WASD/↑↓","Move"),("Z","Sprint"),("SPACE","Pass"),
              ("C","Cross (near wing)"),("F/Shift","Shoot (hold=power)"),
              ("X","Tackle"),("TAB","Switch")]
        px,py=8,SCR_H-130
        pygame.draw.rect(s,(0,0,0),(px-4,py-4,234,134),border_radius=6)
        pygame.draw.rect(s,(48,48,48),(px-4,py-4,234,134),1,border_radius=6)
        for i,(k,d) in enumerate(ctrl):
            ks=self.f_hud.render(k,True,(255,218,0))
            ds=self.f_hud.render(d,True,(170,170,170))
            s.blit(ks,(px,py+i*18)); s.blit(ds,(px+84,py+i*18))

        # Shoot power bar
        if self.charging:
            bw2,bh=210,20; bx2=SCR_W//2-bw2//2; by2=SCR_H-58
            pygame.draw.rect(s,(20,20,20),(bx2-2,by2-2,bw2+4,bh+4),border_radius=6)
            fill=int(bw2*self.charge)
            gc=(int(55+200*self.charge),int(200*(1-self.charge**0.5)),0)
            pygame.draw.rect(s,gc,(bx2,by2,fill,bh),border_radius=4)
            pygame.draw.rect(s,(190,190,190),(bx2-2,by2-2,bw2+4,bh+4),1,border_radius=6)
            lbl=self.f_hud.render(f"SHOOT  {int(self.charge*100)}%",True,(255,255,255))
            s.blit(lbl,(SCR_W//2-lbl.get_width()//2,by2-18))

        # Dead ball banner
        if self.dead:
            lbl=DB_LABELS.get(self.dead,'')
            ds=self.f_med.render(lbl,True,(255,225,0))
            bx3=SCR_W//2-ds.get_width()//2
            pygame.draw.rect(s,(0,0,0),(bx3-14,SCR_H-64,ds.get_width()+28,36),border_radius=8)
            s.blit(ds,(bx3,SCR_H-60))
            cd=max(0,self.dead_timer//FPS+1)
            ts=self.f_hud.render(f"Resuming in {cd}s…",True,(150,150,150))
            s.blit(ts,(SCR_W//2-ts.get_width()//2,SCR_H-27))

        # Messages
        for i,m in enumerate(self.msgs):
            ms=self.f_med.render(m[0],True,m[1]); ms.set_alpha(min(255,m[2]*3))
            s.blit(ms,(SCR_W//2-ms.get_width()//2,SCR_H//2-110+i*42))

        # Possession
        if self.ball.owner:
            side="BARCELONA" if self.ball.owner.team=='A' else "REAL MADRID"
            col=BAR_BLUE if self.ball.owner.team=='A' else (215,215,215)
            ps=self.f_hud.render(f"Ball: {side} #{self.ball.owner.num}",True,col)
            s.blit(ps,(SCR_W//2-ps.get_width()//2,68))

    # ─── Pass / Cross helpers ──────────────────────────────────────
    def _best_pass(self,carrier,team=None):
        if team is None: team=self.ta
        opp=self.tb if team is self.ta else self.ta
        mates=[p for p in team if p is not carrier and not p.is_keeper]
        if not mates: return None
        scored=[]
        for p in mates:
            dd=d2((carrier.wx,carrier.wy),(p.wx,p.wy))
            fwd=(p.wx-carrier.wx)*(1.5 if team is self.ta else -1.5)
            opp_d=min((d2((q.wx,q.wy),(p.wx,p.wy)) for q in opp),default=999)
            if opp_d<26: continue
            scored.append((fwd+opp_d*0.32-dd*0.07,p))
        if not scored:
            return min(mates,key=lambda p:d2((carrier.wx,carrier.wy),(p.wx,p.wy)))
        return max(scored,key=lambda x:x[0])[1]

    def _near_byline(self,p):
        """True if player A is near the right byline, ready to cross."""
        return p.wx > W_W*0.82 and (p.wy < W_MY-40 or p.wy > W_MY+40)

    def _do_cross(self,carrier):
        """Whip ball into the box from a wide position."""
        # Aim at far post / near post alternating
        tgt_y=GOAL_TOP+20 if carrier.wy>W_MY else GOAL_BOT-20
        tgt_y+=random.randint(-18,18)
        tgt_x=float(W_W)+5
        bx,by=n2(tgt_x-carrier.wx,tgt_y-carrier.wy)
        self.ball.release()
        self.ball.vx=bx*CROSS_SPD; self.ball.vy=by*CROSS_SPD
        self.ball.vz=9.0  # high arc
        self.ball.last_toucher=carrier
        self.msg("CROSS!  ⚽",(255,200,60))

    # ─── Human input ──────────────────────────────────────────────
    def handle_input(self):
        if self.dead: return
        keys=pygame.key.get_pressed()
        spd=PLAYER_SPD*(SPRINT_MULT if keys[pygame.K_z] else 1.)
        p=self.sel
        dx,dy=0.,0.
        if keys[pygame.K_LEFT] or keys[pygame.K_a]: dx-=1
        if keys[pygame.K_RIGHT] or keys[pygame.K_d]: dx+=1
        if keys[pygame.K_UP] or keys[pygame.K_w]: dy-=1
        if keys[pygame.K_DOWN] or keys[pygame.K_s]: dy+=1
        if dx or dy:
            nx,ny=n2(dx,dy); p.vx,p.vy=nx*spd,ny*spd
            p.fdx,p.fdy=nx,ny; p.wx+=p.vx; p.wy+=p.vy
            p.wx=clamp(p.wx,-OUT_L,W_W+OUT_R)
            p.wy=clamp(p.wy,-OUT_T,W_H+OUT_B)
        else: p.vx*=0.5; p.vy*=0.5

        # Shoot charge
        shooting=keys[pygame.K_f] or keys[pygame.K_LSHIFT] or keys[pygame.K_RSHIFT]
        if shooting and self.ball.owner and self.ball.owner.team=='A':
            self.charging=True; self.charge=min(1.,self.charge+0.024)
        else:
            if self.charging and self.ball.owner and self.ball.owner.team=='A':
                self._human_shoot(self.charge)
            self.charging=False; self.charge=0.

        # Auto-collect
        if self.ball.owner is None and self.ball.wz<10:
            if d2((p.wx,p.wy),(self.ball.wx,self.ball.wy))<CONTROL_R:
                self.ball.owner=p; self.ball.last_toucher=p

        if p.tackle_cd>0: p.tackle_cd-=1

    def handle_events(self):
        for ev in pygame.event.get():
            if ev.type==pygame.QUIT: pygame.quit(); sys.exit()
            if ev.type==pygame.KEYDOWN:
                k=ev.key
                if k==pygame.K_ESCAPE: pygame.quit(); sys.exit()
                elif k==pygame.K_TAB and not self.dead:
                    self._switch()
                elif k==pygame.K_SPACE and not self.dead:
                    if self.ball.owner and self.ball.owner.team=='A':
                        self._human_pass()
                elif k==pygame.K_c and not self.dead:
                    if self.ball.owner and self.ball.owner.team=='A':
                        if self._near_byline(self.ball.owner):
                            self._do_cross(self.ball.owner)
                        else:
                            self._human_pass()  # C = pass if not near byline
                elif k==pygame.K_x and not self.dead:
                    self._human_tackle()
                # All other keys: safe no-op

    def _switch(self):
        self.sel.selected=False
        if self.ball.owner and self.ball.owner.team=='A':
            self.sel=self.ball.owner
        else:
            cands=[p for p in self.ta if not p.is_keeper]
            cands.sort(key=lambda p:d2((p.wx,p.wy),(self.ball.wx,self.ball.wy)))
            idx=cands.index(self.sel) if self.sel in cands else -1
            self.sel=cands[(idx+1)%len(cands)]
        self.sel.selected=True

    def _auto_switch(self,p):
        self.sel.selected=False; self.sel=p; self.sel.selected=True

    def _human_pass(self):
        carrier=self.ball.owner
        tgt=self._best_pass(carrier)
        if not tgt: return
        self.ball.last_toucher=carrier
        self.ball.kick(tgt.wx,tgt.wy,PASS_SPD,2.0)
        self._auto_switch(tgt)

    def _human_shoot(self,power):
        c=self.ball.owner
        if not c: return
        gy=clamp(c.wy,GOAL_TOP+15,GOAL_BOT-15)+random.randint(-14,14)
        inac=clamp((1.-power)*0.28,0,0.26)
        bx,by=n2(W_W-c.wx,gy-c.wy)
        bx+=random.uniform(-inac,inac); by+=random.uniform(-inac,inac)
        bx,by=n2(bx,by); spd=SHOOT_SPD*(0.52+power*0.48)
        self.ball.release()
        self.ball.vx=bx*spd; self.ball.vy=by*spd
        self.ball.vz=4.+power*8.; self.ball.last_toucher=c

    def _human_tackle(self):
        p=self.sel
        if p.tackle_cd>0: return
        for t in self.tb:
            if t.is_keeper: continue
            dd=d2((p.wx,p.wy),(t.wx,t.wy))
            if dd<TACKLE_R+10 and self.ball.owner is t:
                ok=random.random()<0.62
                if ok:
                    prev=t
                    self.ball.release()
                    bx,by=n2(p.wx-prev.wx,p.wy-prev.wy)
                    self.ball.vx=bx*4.5+random.uniform(-1.5,1.5)
                    self.ball.vy=by*4.5+random.uniform(-1.5,1.5)
                    self.ball.last_toucher=p
                    self.msg("TACKLE! Ball won!",(80,255,80))
                    self._auto_switch(p)
                else:
                    self.msg("Tackle missed!",(255,160,60))
                p.tackle_cd=48; return

    # ─── Keeper AI ────────────────────────────────────────────────
    def _keeper_ai(self,keeper,gx,is_left):
        b=self.ball
        coming=False
        if b.owner is None and b.spd()>0.9:
            fx=b.wx+b.vx*26
            coming=(fx<W_MX) if is_left else (fx>W_MX)
        if coming and abs(b.vx)>0.15:
            t2=(gx-b.wx)/b.vx
            if 0<t2<65:
                iy=clamp(b.wy+b.vy*t2,GOAL_TOP+3,GOAL_BOT-3)
                out=38 if is_left else -38
                keeper.move_toward(gx+out,iy,AI_JOG*1.3); return
        ky=clamp(b.wy,GOAL_TOP+22,GOAL_BOT-22)
        in_half=(b.wx<W_MX) if is_left else (b.wx>W_MX)
        if is_left: kx=clamp(28+(b.wx*0.055 if in_half else 0),20,82)
        else: kx=clamp(W_W-28-((W_W-b.wx)*0.055 if in_half else 0),W_W-82,W_W-20)
        keeper.move_toward(kx,ky,AI_WALK*0.88)

    # ─── Team A support AI ────────────────────────────────────────
    def update_team_a_ai(self):
        carrier=self.ball.owner
        has_ball_a=carrier and carrier.team=='A'
        for p in self.ta:
            if p is self.sel or p.is_keeper: continue
            if not has_ball_a:
                # Hold shape, stay behind ball
                tx=clamp(p.home_x,30,self.ball.wx-35)
                ty=p.home_y+(self.ball.wy-W_MY)*0.12
                p.move_toward(tx,ty,AI_WALK*0.82)
                continue
            role=p.num  # 2-5=def,6-8=mid,9-11=fwd
            if 2<=role<=5:
                sx=min(carrier.wx-52,p.home_x+55); sx=max(sx,p.home_x)
                ty=p.home_y+(carrier.wy-W_MY)*0.14
                p.move_toward(sx,ty,AI_JOG*0.80)
            elif 6<=role<=8:
                ang=math.radians((role-7)*65+90)
                tx=clamp(carrier.wx+math.cos(ang)*95,55,W_W-55)
                ty=clamp(carrier.wy+math.sin(ang)*100,18,W_H-18)
                p.move_toward(tx,ty,AI_JOG)
            else:
                ch=[GOAL_TOP+28,W_MY,GOAL_BOT-28][role-9]
                rx=clamp(carrier.wx+105,carrier.wx+45,W_W-38)
                ty=clamp(ch+random.uniform(-14,14),18,W_H-18)
                p.move_toward(rx,ty,AI_RUN if rx>W_W*0.6 else AI_JOG)
        self._keeper_ai(self.ta[0],0,is_left=True)

    # ─── CPU AI — build-up play ───────────────────────────────────
    def update_cpu(self):
        if self.dead: return
        self._keeper_ai(self.tb[0],W_W,is_left=False)
        outfield=self.tb[1:]
        ball_b=self.ball.owner and self.ball.owner.team=='B'
        ball_a=self.ball.owner and self.ball.owner.team=='A'
        closest=min(outfield,key=lambda p:d2((p.wx,p.wy),(self.ball.wx,self.ball.wy)))

        for p in outfield:
            if p.tackle_cd>0: p.tackle_cd-=1
            if p.react>0:
                p.react-=1
                p.move_toward(p.home_x,p.home_y,AI_WALK*0.72); continue

            if ball_b and self.ball.owner is p:
                self._cpu_carry(p)
            elif self.ball.owner is None:
                dd=d2((p.wx,p.wy),(self.ball.wx,self.ball.wy))
                if dd<150: p.move_toward(self.ball.wx,self.ball.wy,AI_JOG)
                else: p.move_toward(p.home_x,p.home_y,AI_WALK)
                if self.ball.wz<12 and dd<CONTROL_R:
                    self.ball.owner=p; self.ball.last_toucher=p
                    for q in outfield: q.react=random.randint(6,AI_REACT//2)
            elif ball_a:
                self._cpu_defend(p,closest)

    def _cpu_carry(self,p):
        """CPU carrier: build-up passes + dribble + shoot."""
        b=self.ball; goal_x=0.; d_goal=d2((p.wx,p.wy),(goal_x,W_MY))
        pres=[q for q in self.ta if d2((q.wx,q.wy),(p.wx,p.wy))<68]

        # Shoot when in range
        if d_goal<280 and random.random()<0.022:
            gy=clamp(p.wy,GOAL_TOP+12,GOAL_BOT-12)+random.randint(-22,22)
            bx,by=n2(goal_x-p.wx,gy-p.wy)
            inac=clamp(d_goal/1900,0.06,0.24)
            bx+=random.uniform(-inac,inac); by+=random.uniform(-inac,inac)
            bx,by=n2(bx,by); b.release()
            b.vx=bx*SHOOT_SPD*0.82; b.vy=by*SHOOT_SPD*0.82; b.vz=4.5
            b.last_toucher=p
            for q in self.tb[1:]: q.react=random.randint(12,32)
            return

        # Cross from wide positions
        near_byline=(p.wx<W_W*0.18 and
                     (p.wy<W_MY-38 or p.wy>W_MY+38))
        if near_byline and random.random()<0.025:
            tgt_y=GOAL_TOP+20 if p.wy>W_MY else GOAL_BOT-20
            bx,by=n2(W_W-p.wx-(W_W+10)+p.wx, tgt_y-p.wy)
            # Actually kick toward left goal
            bx,by=n2(0-p.wx,tgt_y-p.wy)
            b.release(); b.vx=bx*CROSS_SPD; b.vy=by*CROSS_SPD; b.vz=8.5
            b.last_toucher=p
            for q in self.tb[1:]: q.react=random.randint(6,18)
            return

        # Build-up pass (pass more often, not just under pressure)
        pass_chance=0.018 if not pres else 0.032
        if random.random()<pass_chance:
            tgt=self._best_pass(p,team=self.tb)
            if tgt:
                b.kick(tgt.wx,tgt.wy,PASS_SPD,2.0); b.last_toucher=p
                for q in self.tb[1:]: q.react=random.randint(5,18)
                return

        # Dribble with dodge
        dodge=0.
        if pres:
            avg=sum(q.wy for q in pres)/len(pres)
            dodge=30. if p.wy<avg else -30.
        p.move_toward(goal_x+55,W_MY+dodge,AI_RUN)

    def _cpu_defend(self,p,closest):
        """CPU defending: soft pressing, don't all rush."""
        b=self.ball; role=p.num
        dd=d2((p.wx,p.wy),(b.wx,b.wy))

        if p is closest:
            # One player presses hard
            if dd<125:
                p.move_toward(b.wx,b.wy,AI_JOG)
                # Soft tackle — won't always succeed (prevents wall)
                if dd<TACKLE_R and p.tackle_cd==0 and random.random()<0.010:
                    if b.owner:
                        prev=b.owner; b.release()
                        bx,by=n2(p.wx-prev.wx,p.wy-prev.wy)
                        b.vx=bx*3.2+random.uniform(-1,1)
                        b.vy=by*3.2+random.uniform(-1,1)
                        b.last_toucher=p; p.tackle_cd=55
            else:
                p.move_toward((p.home_x+b.wx*0.55)/1.55,
                              (p.home_y+b.wy*0.55)/1.55,AI_WALK)
        elif 2<=role<=5:
            # Defenders: block passing lane between ball and goal
            lx=clamp((b.wx+W_W)*0.50,p.home_x,W_W-38)
            ly=p.home_y+(b.wy-W_MY)*0.20
            p.move_toward(lx,ly,AI_WALK)
        elif 6<=role<=8:
            # Midfielders: compact block second line — SOFT press, stay in shape
            mx=max(p.home_x,W_W-W_W*0.58)
            my=p.home_y+(b.wy-W_MY)*0.18
            p.move_toward(mx,my,AI_WALK*0.88)
        else:
            # Forwards: press high to cut long balls, but don't sprint
            px=clamp(b.wx+55,W_MX,W_W-48)
            py=p.home_y+(b.wy-W_MY)*0.16
            p.move_toward(px,py,AI_JOG*0.78)

    # ─── Dead ball (throw-in / corner animation) ──────────────────
    def _start_dead(self,kind,pos):
        self.ball.owner=None; self.ball.vx=self.ball.vy=self.ball.vz=0.
        self.dead=kind; self.dead_pos=pos if pos else (W_MX,W_MY)
        self.ball.wx=float(self.dead_pos[0]); self.ball.wy=float(self.dead_pos[1])
        self.ball.wz=0.; self.dead_timer=FPS*2+20
        self.throw_player=None

    def update_dead(self):
        if not self.dead: return
        self.dead_timer-=1

        # Show throw animation during waiting period
        kind=self.dead; bx,by=self.dead_pos
        if self.throw_player is None and self.dead_timer<=FPS*2:
            # Pick the player who will do the throw/corner
            if kind in(DB_THROW_A,DB_GK_A,DB_CORNER_A): team=self.ta
            elif kind in(DB_THROW_B,DB_GK_B,DB_CORNER_B): team=self.tb
            else: team=None
            if team:
                tp=min(team,key=lambda p:d2((p.wx,p.wy),(bx,by)))
                tp.wx=float(bx); tp.wy=float(by)
                self.throw_player=tp; tp.throw_anim=1

        if self.throw_player:
            self.throw_player.throw_anim=min(30,self.throw_player.throw_anim+1)

        if self.dead_timer>0: return

        # Resume play
        if kind in(DB_KICK_A,DB_KICK_B):
            if self.throw_player: self.throw_player.throw_anim=0
            self._kickoff('A' if 'A' in kind else 'B'); return

        team=self.ta if kind.endswith('_A') else self.tb
        nearest=min(team,key=lambda p:d2((p.wx,p.wy),(bx,by)))
        nearest.wx,nearest.wy=float(bx),float(by)
        self.ball.wx,self.ball.wy,self.ball.wz=float(bx),float(by),0.
        self.ball.owner=nearest; self.ball.last_toucher=nearest
        nearest.throw_anim=0
        if self.throw_player: self.throw_player.throw_anim=0

        # For corners: automatically cross the ball (AI and human)
        if kind in(DB_CORNER_A,DB_CORNER_B):
            # Aim at near/far post
            tgt_y=GOAL_TOP+22 if nearest.wy<W_MY else GOAL_BOT-22
            tgt_y+=random.randint(-16,16)
            if kind==DB_CORNER_A:
                self.ball.kick(float(W_W),tgt_y,CROSS_SPD,9.5)
            else:
                self.ball.kick(0.,tgt_y,CROSS_SPD,9.5)
            self.ball.last_toucher=nearest
            nearest.throw_anim=0; self.dead=None; self.throw_player=None
            return

        if nearest.team=='A': self._auto_switch(nearest)
        self.dead=None; self.throw_player=None

    # ─── Goals & out ──────────────────────────────────────────────
    def check_goals(self):
        if self.dead: return
        b=self.ball
        if b.wz>24: return
        if b.wx<=-BALL_R and GOAL_TOP<=b.wy<=GOAL_BOT:
            self.score[1]+=1; self.msg("⚽  GOAL! — REAL MADRID!",(215,215,215))
            self._start_dead(DB_KICK_A,None)
        elif b.wx>=W_W+BALL_R and GOAL_TOP<=b.wy<=GOAL_BOT:
            self.score[0]+=1; self.msg("⚽  GOAL! — BARCELONA!",BAR_BLUE)
            self._start_dead(DB_KICK_B,None)

    def check_out(self):
        if self.dead or self.ball.owner: return
        b=self.ball; lt=b.last_toucher

        # Top/bottom → throw-in
        if b.wy<-BALL_R or b.wy>W_H+BALL_R:
            kind=DB_THROW_B if lt and lt.team=='A' else DB_THROW_A
            tx=clamp(b.wx,38,W_W-38)
            ty=10 if b.wy<0 else W_H-10
            self._start_dead(kind,(tx,ty)); return

        # Left byline
        if b.wx<-BALL_R and not(GOAL_TOP<=b.wy<=GOAL_BOT):
            if lt and lt.team=='A':
                self._start_dead(DB_GK_B,(34,clamp(b.wy,38,W_H-38)))
            else:
                cy=10 if b.wy<W_MY else W_H-10
                self._start_dead(DB_CORNER_A,(8,cy))
            return

        # Right byline
        if b.wx>W_W+BALL_R and not(GOAL_TOP<=b.wy<=GOAL_BOT):
            if lt and lt.team=='B':
                self._start_dead(DB_GK_A,(W_W-34,clamp(b.wy,38,W_H-38)))
            else:
                cy=10 if b.wy<W_MY else W_H-10
                self._start_dead(DB_CORNER_B,(W_W-8,cy))

    # ─── Main loop ────────────────────────────────────────────────
    def run(self):
        while True:
            self.clock.tick(FPS)
            self.match_time+=1
            self.handle_events()
            self.handle_input()

            if not self.dead:
                self.update_cpu()
                self.update_team_a_ai()
                self.ball.update()
                self.check_goals()
                self.check_out()

                # Auto-collect loose ball
                if self.ball.owner is None and self.ball.wz<11:
                    all_p=self.ta+self.tb
                    all_p.sort(key=lambda p:d2((p.wx,p.wy),(self.ball.wx,self.ball.wy)))
                    for p in all_p:
                        if d2((p.wx,p.wy),(self.ball.wx,self.ball.wy))<CONTROL_R:
                            self.ball.owner=p; self.ball.last_toucher=p
                            if p.team=='B':
                                for q in self.tb[1:]: q.react=random.randint(7,24)
                            elif p is not self.sel:
                                self._auto_switch(p)
                            break
            else:
                self.update_dead()

            self.msgs=[[t,c,n-1] for t,c,n in self.msgs if n>0]
            self.draw_scene()
            self.draw_hud()
            pygame.display.flip()


if __name__=="__main__":
    try:
        Game().run()
    except SystemExit:
        pass