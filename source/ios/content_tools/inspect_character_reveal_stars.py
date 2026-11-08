"""Read bounded SS5 v1 default cells; no animation-frame/keyframe decoding."""
import json
import struct
from import_reveal_research import CACHE,sha
from import_character_reveal import LOCK
from import_summon_ui import decode

def run():
    lock=json.loads(LOCK.read_text());row=lock['sources'][0];stored=(CACHE/row['cache_path']).read_bytes()
    if sha(stored)!=row['sha256_stored']:raise ValueError('Source checksum')
    b=decode(stored)
    if sha(b)!=row['sha256_decoded'] or b[:4]!=b'SSPB' or struct.unpack_from('<I',b,4)[0]!=1:raise ValueError('Unsupported SS5 v1')
    cells,packs,ncells,npacks=struct.unpack_from('<IIHH',b,16)
    if cells+ncells*20>len(b) or packs+npacks*16>len(b):raise ValueError('Table bounds')
    def string(offset):
        end=b.find(b'\0',offset,min(len(b),offset+1024))
        if offset<=0 or end<offset:raise ValueError('Name bounds')
        return b[offset:end].decode('utf-8')
    names=[string(struct.unpack_from('<I',b,cells+i*20)[0]) for i in range(ncells)];result=[]
    for i in range(npacks):
        n,parts,animation,nparts,nanimations=struct.unpack_from('<IIIhh',b,packs+i*16)
        name=string(n)
        if name not in ['gacha_star'+str(n) for n in range(1,8)]:continue
        if not 0<nparts<256 or nanimations<1 or parts+nparts*20>len(b) or animation+28>len(b):raise ValueError('Part bounds')
        initial=struct.unpack_from('<I',b,animation+4)[0]
        if initial+nparts*80>len(b):raise ValueError('Initial-data bounds')
        defaults=[]
        for j in range(nparts):
            part=string(struct.unpack_from('<I',b,parts+j*20)[0]);cell=struct.unpack_from('<h',b,initial+j*80+8)[0]
            if 0<=cell<ncells:defaults.append({'part':part,'default_cell':names[cell]})
        result.append({'pack':name,'default_cells':defaults})
    return {'source':row,'container':lock['container'],'archive':lock['archive'],'note':'Defaults only. Original placement/timing/runtime routing is not recovered. Code 7/NV mapping remains intentionally numeric.','packs':result}
if __name__=='__main__':print(json.dumps(run(),indent=2))
