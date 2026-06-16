"""player.py - Top-down 3D-shaded players. No SRCALPHA mask surfaces."""
import pygame, math, random
from constants import PLAYER_R, AI_REACT, OUT_L, OUT_R, OUT_T, OUT_B, W_W, W_H, d2, n2, clamp, w2s

_KIT_A = None
_KIT_B = None

def set_kits(kit_a, kit_b):
    global _KIT_A, _KIT_B
    _KIT_A = kit_a; _KIT_B = kit_b

# Light from upper-left; shadows fall lower-right
SUN_DX, SUN_DY = -0.55, -0.75
SHADOW_ALPHA   = 80
SHADOW_DIST    = 4

def _shade(col, t):
    if t >= 0:
        return tuple(min(255, int(c + (255-c)*t)) for c in col)
    return tuple(max(0, int(c*(1+t))) for c in col)

class Player:
    def __init__(self, team, num, hx, hy, is_keeper=False):
        self.team=team; self.num=num
        self.wx=float(hx); self.wy=float(hy)
        self.home_x=float(hx); self.home_y=float(hy)
        self.vx=0.; self.vy=0.
        self.fdx=1. if team=='A' else -1.; self.fdy=0.
        self.is_keeper=is_keeper; self.selected=False
        self.react=random.randint(0,AI_REACT); self.tackle_cd=0
        self.anim_t=random.uniform(0,math.pi*2)
        self.throw_anim=0; self.hold_timer=0; self.stamina=1.0

    def _kit(self):
        cfg=_KIT_A if self.team=='A' else _KIT_B
        if cfg is None:
            return (0,82,170),(0,82,170),(0,82,170),(222,182,142),(38,28,18)
        if self.is_keeper:
            gk=cfg['gk']; dk=tuple(max(0,c-40) for c in gk)
            return gk,dk,dk,cfg['skin'],cfg['hair']
        return cfg['shirt1'],cfg['shorts'],cfg['socks'],cfg['skin'],cfg['hair']

    def move_toward(self, tx, ty, spd):
        dd=d2((self.wx,self.wy),(tx,ty))
        if dd<0.5: self.vx=self.vy=0.; return
        r=min(spd/dd,1.)
        self.vx=(tx-self.wx)*r; self.vy=(ty-self.wy)*r
        ln=math.hypot(self.vx,self.vy)
        if ln>0: self.fdx=self.vx/ln; self.fdy=self.vy/ln
        self.wx+=self.vx; self.wy+=self.vy
        self.wx=clamp(self.wx,-OUT_L,W_W+OUT_R)
        self.wy=clamp(self.wy,-OUT_T,W_H+OUT_B)

    # ── Sphere-shaded disc helpers (ALL mask-free) ─────────────────
    def _sphere_disc(self, surf, cx, cy, r, col):
        """Single-colour disc with 3D sphere shading."""
        pygame.draw.circle(surf, col, (cx,cy), r)
        # shading crescent (lower-right)
        sc=_shade(col,-0.30)
        ox=int(-SUN_DX*r*0.32); oy=int(-SUN_DY*r*0.32)
        pygame.draw.circle(surf, sc, (cx+ox,cy+oy), int(r*0.90))
        pygame.draw.circle(surf, col, (cx,cy), int(r*0.80))
        # highlight (upper-left)
        hc=_shade(col, 0.38)
        hox=int(SUN_DX*r*0.40); hoy=int(SUN_DY*r*0.40)
        pygame.draw.circle(surf, hc, (cx+hox,cy+hoy), int(r*0.38))

    def _stripe_disc(self, surf, cx, cy, r, cfg, shirt):
        """Vertical stripes via set_clip rectangles - no alpha surfaces."""
        cols=cfg.get('stripe_cols',[shirt, cfg.get('shirt2',shirt), shirt])
        n=max(1,len(cols)); bw=(2*r)/n
        pygame.draw.circle(surf, cols[0], (cx,cy), r)
        old=surf.get_clip()
        for i in range(1,n):
            x0=cx+int(-r+i*bw)
            clip=pygame.Rect(x0, cy-r-1, int(bw)+2, 2*r+3)
            surf.set_clip(clip)
            pygame.draw.circle(surf, cols[i], (cx,cy), r)
        surf.set_clip(old)
        self._arc_shading(surf, cx, cy, r, cols[0])

    def _half_disc(self, surf, cx, cy, r, cfg, shirt):
        """Left/right two-tone via set_clip rectangle - no alpha surfaces."""
        s1=cfg['shirt1']; s2=cfg.get('shirt2',shirt)
        pygame.draw.circle(surf, s1, (cx,cy), r)
        old=surf.get_clip()
        surf.set_clip(pygame.Rect(cx, cy-r-1, r+2, 2*r+3))
        pygame.draw.circle(surf, s2, (cx,cy), r)
        surf.set_clip(old)
        self._arc_shading(surf, cx, cy, r, s1)

    def _arc_shading(self, surf, cx, cy, r, ref):
        """Add 3D shading to a patterned disc using arc strokes."""
        rect=pygame.Rect(cx-r,cy-r,2*r,2*r)
        # shading arc (lower-right)
        sc=_shade(ref,-0.32)
        pygame.draw.arc(surf,sc,rect,math.radians(-45),math.radians(135),max(2,r//3))
        # highlight arc (upper-left)
        hc=_shade(ref, 0.34)
        pygame.draw.arc(surf,hc,rect,math.radians(135),math.radians(315),max(2,r//3))

    # ── Main draw ─────────────────────────────────────────────────
    def draw(self, surf, ball, fnt):
        shirt,shorts,socks,skin,hair=self._kit()
        cfg=(_KIT_A if self.team=='A' else _KIT_B) or {}
        has_ball=(ball.owner is self)
        moving=math.hypot(self.vx,self.vy)>0.2
        if moving: self.anim_t+=0.28
        gx,gy=w2s(self.wx,self.wy,0)
        R=int(PLAYER_R*1.35)
        FOOT_R=max(2,int(R*0.20))
        HEAD_R=max(3,int(R*0.30))

        # Shadow (SRCALPHA surface is safe here - it's a standalone blit, not clip-masked)
        sr=int(R*1.05)
        sox=int(-SUN_DX*SHADOW_DIST); soy=int(-SUN_DY*SHADOW_DIST)+int(R*0.25)
        shw=pygame.Surface((sr*2+6,sr*2+6),pygame.SRCALPHA)
        shw.fill((0,0,0,0))
        pygame.draw.ellipse(shw,(0,0,0,SHADOW_ALPHA),(3,3,sr*2,int(sr*1.7)))
        surf.blit(shw,(gx-sr-3+sox, gy-sr-3+soy))

        # Feet
        fs=R*0.55
        for sign in(-1,1):
            ph=self.anim_t+(0 if sign==-1 else math.pi)
            st=math.sin(ph)*(R*0.35) if moving else 0.
            fx=gx+self.fdx*st-self.fdy*sign*fs
            fy=gy+self.fdy*st+self.fdx*sign*fs
            fc=tuple(max(0,c-60) for c in (shorts if not self.is_keeper else (30,30,30)))
            pygame.draw.circle(surf,fc,(int(fx),int(fy)),FOOT_R)
            pygame.draw.circle(surf,(0,0,0),(int(fx),int(fy)),FOOT_R,1)

        # Body disc
        if not self.is_keeper and cfg.get('stripe'):
            self._stripe_disc(surf,gx,gy,R,cfg,shirt)
        elif not self.is_keeper and cfg.get('half_half'):
            self._half_disc(surf,gx,gy,R,cfg,shirt)
        elif not self.is_keeper and cfg.get('gold_border'):
            self._sphere_disc(surf,gx,gy,R,shirt)
            try:
                from constants import RMA_GOLD
                pygame.draw.circle(surf,RMA_GOLD,(gx,gy),R,2)
            except Exception:
                pass
        else:
            self._sphere_disc(surf,gx,gy,R,shirt)

        # Border
        border=tuple(max(0,c-40) for c in shirt)
        pygame.draw.circle(surf,border,(gx,gy),R,2)

        # Shorts hem arc
        hem=pygame.Rect(gx-R,gy-R,R*2,R*2)
        pygame.draw.arc(surf,shorts,hem,math.radians(200),math.radians(340),4)

        # Head at edge in facing direction
        hoff=R*0.78
        hx_=gx+self.fdx*hoff; hy_=gy+self.fdy*hoff
        pygame.draw.circle(surf,skin,(int(hx_),int(hy_)),HEAD_R)
        pygame.draw.circle(surf,tuple(max(0,c-18) for c in skin),(int(hx_),int(hy_)),HEAD_R,1)
        # Hair crescent
        hxh=hx_-self.fdx*HEAD_R*0.55; hyh=hy_-self.fdy*HEAD_R*0.55
        pygame.draw.circle(surf,hair,(int(hxh),int(hyh)),max(2,int(HEAD_R*0.70)))

        # Jersey number
        nc=cfg.get('num_col',(255,255,255)) if not self.is_keeper else (255,255,255)
        ns=fnt.render(str(self.num),True,nc)
        surf.blit(ns,(gx-ns.get_width()//2, gy-ns.get_height()//2+2))

        # Throw-in animation
        if self.throw_anim>0:
            prog=min(1.,self.throw_anim/20.)
            alen=int(R*(0.6+0.6*prog))
            for sign in(-1,1):
                ax=gx-self.fdy*sign*(R*0.8); ay=gy+self.fdx*sign*(R*0.8)
                ex=ax-self.fdx*alen*0.3; ey=ay-self.fdy*alen*0.3
                pygame.draw.line(surf,shirt,(ax,ay),(ex,ey),3)
                pygame.draw.circle(surf,skin,(int(ex),int(ey)),max(2,int(R*0.22)))

        # Selection ring
        if self.selected:
            pulse=int(2+2*math.sin(pygame.time.get_ticks()*0.007))
            rc=(0,255,100) if self.team=='A' else (255,200,0)
            pygame.draw.circle(surf,rc,(gx,gy),R+4+pulse,2)

        # Ball glow
        if has_ball:
            pygame.draw.circle(surf,(255,225,0),(gx,gy),R+6,2)
