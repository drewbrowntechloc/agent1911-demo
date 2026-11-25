"""Generate original Agent 1911 PWA icons (no engine branding). Usage: make_icons.py <outdir>"""
import sys, os
from PIL import Image, ImageDraw, ImageFont
out = sys.argv[1]; os.makedirs(out, exist_ok=True)
S = 1024
GOLD=(232,184,74); NAVY_T=(22,32,48); NAVY_B=(8,12,20); CYAN=(60,200,210)
FONT_BOLD='/usr/share/fonts/opentype/inter/Inter-Bold.otf'
FONT_SEMI='/usr/share/fonts/opentype/inter/Inter-SemiBold.otf'
def master():
    im = Image.new('RGB',(S,S),NAVY_B)
    px = im.load()
    for y in range(S):                         # vertical gradient
        t=y/(S-1); c=tuple(int(NAVY_T[i]*(1-t)+NAVY_B[i]*t) for i in range(3))
        for x in range(S): px[x,y]=c
    d = ImageDraw.Draw(im,'RGBA')
    cx=cy=S//2
    # everything stays inside the central 62% circle (maskable safe zone)
    R=300
    d.ellipse([cx-R,cy-R,cx+R,cy+R],outline=GOLD+(255,),width=14)
    d.ellipse([cx-R+34,cy-R+34,cx+R-34,cy+R-34],outline=GOLD+(90,),width=4)
    for a in (0,90,180,270):                   # crosshair ticks
        import math
        r1,r2=R-60,R+28
        x1=cx+r1*math.cos(math.radians(a)); y1=cy+r1*math.sin(math.radians(a))
        x2=cx+r2*math.cos(math.radians(a)); y2=cy+r2*math.sin(math.radians(a))
        d.line([x1,y1,x2,y2],fill=CYAN+(255,),width=12)
    f=ImageFont.truetype(FONT_BOLD,215)
    d.text((cx,cy+34),'1911',font=f,fill=GOLD,anchor='mm')
    f2=ImageFont.truetype(FONT_SEMI,62)
    txt='A G E N T'
    d.text((cx,cy-126),txt,font=f2,fill=(235,238,244),anchor='mm')
    d.line([cx-150,cy+150,cx+150,cy+150],fill=CYAN+(255,),width=8)
    return im
m=master()
for name,size in [('icon-512.png',512),('icon-192.png',192),('icon-maskable-512.png',512),('apple-touch-icon.png',180),('favicon-32.png',32)]:
    m.resize((size,size),Image.LANCZOS).save(os.path.join(out,name),optimize=True)
m.resize((1024,1024)).save(os.path.join(out,'icon-1024-source.png'),optimize=True)
print(os.listdir(out))
