"""Cache-only candidate contact sheets; no runtime or campaign access."""
from pathlib import Path
import sys,json,struct,re,hashlib,plistlib,io
from PIL import Image,ImageOps,ImageDraw
R=Path(__file__).resolve().parents[3]; C=R/'source/ios/.local/phase6a'
import argparse
parser=argparse.ArgumentParser();parser.add_argument('--output',type=Path,default=R/'source/ios/.local/phase6d1/contact-sheets');O=parser.parse_args().output;O.mkdir(exist_ok=True,parents=True)
sys.path.insert(0,str(R/'source/ios/content_tools'))
from import_summon_ui import decode,frame_image
from crystal_formats import ibmb_info
rows=[]; tiles=[]
def add(im,label,source,kind):
 im=im.convert('RGBA'); i=len(rows); im.save(O/f'candidate-{i:03}.png'); rows.append(dict(id=i,label=label,source=str(source.relative_to(R)),kind=kind,width=im.width,height=im.height,sha256=hashlib.sha256(source.read_bytes()).hexdigest())); tiles.append((im,label))
for p in sorted(C.glob('preservation/extracted/**/*.png')):
 if p.stat().st_size>8000000:continue
 if re.search(r'gacha|base|stage|circle|plate|result',p.name,re.I):
  try:add(Image.open(p),p.parent.name+'/'+p.name,p,'whole texture')
  except Exception as e:print(e)
for p in sorted(C.glob('preservation/extracted/**/*.ssbp')):
 if not re.search('gacha',p.name):continue
 b=decode(p.read_bytes()); cells,packs,nc,np=struct.unpack_from('<IIHH',b,16)
 def s(n):return b[n:b.index(b'\0',n)].decode()
 for i in range(nc):
  n,m,idx,x,y,w,h,res=struct.unpack_from('<IIhhhHHh',b,cells+i*20); mn,img=struct.unpack_from('<II',b,m); name=s(n); image=s(img)
  if re.search('base|stage|circle|floor|stand|plate|pedestal|magic|ground',name,re.I):
   paths=list(p.parent.glob(Path(image).name)); tex=paths[0] if paths else None
   print('CELL',p.parent.name,name,image,x,y,w,h)
   if tex:
    im=Image.open(tex); assert x>=0 and y>=0 and x+w<=im.width and y+h<=im.height
    add(im.crop((x,y,x+w,y+h)),p.parent.name+':'+name,p,'SSBP cell '+image+str((x,y,w,h)))
refs=[]
for p in C.glob('preservation/extracted/Ver31*/*.bmb'):
 if re.search('base|stage|unit_get',p.name):
  try: names=[x['name'] for x in ibmb_info(decode(p.read_bytes()))['names']];refs.append({'file':p.name,'names':names});print('BMB',p.name,names)
  except Exception as e:print('ERR',p,e)
(O/'BMB-References.json').write_text(json.dumps(refs,indent=2));(O/'Probe-Manifest.json').write_text(json.dumps(rows,indent=2))
for start in range(0,len(tiles),24):
 sheet=Image.new('RGB',(1200,((min(24,len(tiles)-start)+3)//4)*230),(24,27,37));d=ImageDraw.Draw(sheet)
 for j,(im,label) in enumerate(tiles[start:start+24]):
  x=j%4*300;y=j//4*230;im.thumbnail((285,178));sheet.paste(im,(x+(300-im.width)//2,y),im)
  for k,line in enumerate([label[a:a+45] for a in range(0,min(len(label),135),45)]):d.text((x+5,y+180+k*13),line,fill='white')
 sheet.save(O/f'contact-{start//24+1}.jpg')
print('IMAGES',len(rows))

rows=[];tiles=[];seen=set()
for p in sorted((R/'source/ios/.local/phase6a').glob('*/extracted/**/gacha*.plist')):
 b=decode(p.read_bytes());kind='Memorial JP English patched' if '/memorial/' in str(p) else 'Global-targeted preservation';key=(kind,hashlib.sha256(b).hexdigest())
 if key in seen:continue
 seen.add(key);frames=plistlib.loads(b)['frames'];atlas=Image.open(io.BytesIO(decode(p.with_suffix('.png').read_bytes()))).convert('RGBA')
 for name,frame in frames.items():
  if not re.search('base|plate|circle|unitname|select_unitbg',name,re.I):continue
  im=frame_image(atlas,frame);f='atlas-region-%03d.png'%len(rows);im.save(O/f);rows.append({'source':str(p.relative_to(R)),'texture':str(p.with_suffix('.png').relative_to(R)),'resource_id':name,'format':'PNG derivative from TexturePacker metadata','dimensions':list(im.size),'provenance':kind,'sha256_source':hashlib.sha256(p.read_bytes()).hexdigest(),'confidence':'unrelated to under-character pedestal: UI plate or name panel candidate','image':f});tiles.append((im,kind+':'+name))
for start in range(0,len(tiles),24):
 a=tiles[start:start+24];sheet=Image.new('RGB',(1200,((len(a)+3)//4)*190),(23,26,38));draw=ImageDraw.Draw(sheet)
 for j,(im,label) in enumerate(a):
  im.thumbnail((286,130));x=j%4*300;y=j//4*190;sheet.paste(im,(x+(300-im.width)//2,y),im)
  for k in range(3):draw.text((x+4,y+135+k*14),label[k*43:(k+1)*43],fill='white')
 sheet.save(O/f'ui-plates-{start//24+1}.jpg')
(O/'UI-Plate-Manifest.json').write_text(json.dumps(rows,indent=2));print(len(rows))

# Show every bounded result cell, including numerically named/misleading candidates.
from import_reveal_research import cells as result_cells
tiles=[];rows=[]
for p in sorted(C.glob('preservation/extracted/**/gacha_result_animation.ssbp')):
    textures={q.name:Image.open(io.BytesIO(decode(q.read_bytes()))).convert('RGBA') for q in p.parent.glob('gacha_result_animation*.png')}
    # Phase 6A verified this newer atlas page as a separate resources-package dependency.
    if 'Ver162_resources_tutorial' in str(p):
        page=C/'preservation/extracted/Ver202_resources/spritestudio/gacha_result_animation/gacha_result_animation2.png'
        textures[page.name]=Image.open(io.BytesIO(decode(page.read_bytes()))).convert('RGBA')
    for name,(im,metadata) in result_cells(decode(p.read_bytes()),textures).items():
        filename='cell-%03d.png'%len(rows);im.save(O/filename)
        rows.append(dict(name=name,ssbp=str(p.relative_to(R)),image=filename,**metadata))
        tiles.append((im,p.parent.name+':'+name))
for start in range(0,len(tiles),24):
    group=tiles[start:start+24];sheet=Image.new('RGB',(1200,((len(group)+3)//4)*215),(23,26,38));draw=ImageDraw.Draw(sheet)
    for j,(im,label) in enumerate(group):
        im=im.copy();im.thumbnail((285,160));x=j%4*300;y=j//4*215;sheet.paste(im,(x+(300-im.width)//2,y),im)
        for k in range(3):draw.text((x+4,y+164+k*14),label[k*43:(k+1)*43],fill='white')
    sheet.save(O/f'result-cells-{start//24+1}.jpg')
(O/'Result-Cells.json').write_text(json.dumps(rows,indent=2)+'\n')
