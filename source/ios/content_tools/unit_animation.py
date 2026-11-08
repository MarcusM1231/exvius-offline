"""Strict CGG/CGS research subset. Unknown transforms/pages are rejected."""
import csv
from PIL import Image

FIELDS = ('x','y','flip','blend','opacity','rotation','sx','sy','width','height','page')
def rows(text):
    if len(text)>2000000: raise ValueError('CSV too large')
    result=[]
    for line in csv.reader(text.splitlines()):
        if not line: continue
        while line and line[-1]=='':line.pop()
        if not line or any(not v or len(v)>12 for v in line): raise ValueError('Empty/oversized field')
        try: result.append([int(v) for v in line])
        except ValueError: raise ValueError('Noninteger field') from None
    if not result or len(result)>4096: raise ValueError('Row count')
    return result

def parse_cgg(text, size):
    result=[]
    for row in rows(text):
        if len(row)<2 or row[0]!=0 or not 1<=row[1]<=128 or len(row)!=2+11*row[1]: raise ValueError('Unsupported CGG structure/anchor')
        parts=[]
        for i in range(row[1]):
            p=dict(zip(FIELDS,row[2+11*i:13+11*i]));p['record_index']=i
            if p['page']!=0 or p['rotation'] not in (0,90,-90,180,-180,270,-270) or p['flip'] not in range(4) or p['blend'] not in (0,1): raise ValueError('Unsupported transform/blend/page: '+str({k:p[k] for k in ('flip','blend','rotation','page')}))
            if not 0<=p['opacity']<=100 or not all(-2048<=p[k]<=2048 for k in ('x','y')): raise ValueError('Position/opacity bounds')
            x,y,w,h=(p[k] for k in ('sx','sy','width','height'))
            if not (0<=x<x+w<=size[0] and 0<=y<y+h<=size[1]): raise ValueError(f'Sprite region out of bounds: {(x,y,w,h)} in texture {size}')
            parts.append(p)
        result.append(list(reversed(parts)))
    return result

def parse_cgs(text, compositions):
    sequence=[]
    for r in rows(text):
        if len(r)!=4 or not 0<=r[0]<compositions or not 1<=r[3]<=600 or any(abs(x)>2048 for x in r[1:3]): raise ValueError('CGS bounds/structure')
        sequence.append(dict(composition=r[0],offset_x=r[1],offset_y=r[2],ticks=r[3]))
    return sequence

def compose(texture, parts, offset=(0,0), canvas=(512,512), origin=(256,384)):
    out=Image.new('RGBA',canvas)
    for p in parts:
        x,y,w,h=(p[k] for k in ('sx','sy','width','height'));part=texture.crop((x,y,x+w,y+h)).convert('RGBA')
        if p['flip']&1: part=part.transpose(Image.Transpose.FLIP_LEFT_RIGHT)
        if p['flip']&2: part=part.transpose(Image.Transpose.FLIP_TOP_BOTTOM)
        if p['rotation']%360:
            part=part.transpose({90:Image.Transpose.ROTATE_90,180:Image.Transpose.ROTATE_180,270:Image.Transpose.ROTATE_270}[p['rotation']%360])
        if p['blend']==1:
            # Community assembler's portable luminous-pixel approximation; not
            # claimed to reproduce the original client's additive GPU blend.
            part.putdata([(r*a//255,g*a//255,b*a//255,(r+g+b)//3 if a else 0) for r,g,b,a in part.getdata()])
        part.putalpha(part.getchannel('A').point(lambda a:round(a*p['opacity']/100)))
        w,h=part.size
        dx,dy=p['x']+offset[0]+origin[0],p['y']+offset[1]+origin[1]
        if not (0<=dx<dx+w<=canvas[0] and 0<=dy<dy+h<=canvas[1]): raise ValueError('Composition canvas bounds')
        out.alpha_composite(part,(dx,dy))
    return out
