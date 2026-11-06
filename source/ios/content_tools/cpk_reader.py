"""Read-only CRI UTF/CPK file-table inspector. No native code execution."""
import hashlib,struct
from pathlib import Path

def utf(b):
 if b[:4]!=b'@UTF':
  key=0x655f;out=bytearray()
  for v in b:out.append(v^(key&255));key=key*0x4115&0xffffffff
  b=bytes(out)
 if b[:4]!=b'@UTF':raise ValueError('Not a CRI UTF table')
 size,ro,so,do,name,cols,width,rows=struct.unpack_from('>IIIIIHHI',b,4);ro+=8;so+=8;do+=8
 if rows>100000 or cols>256:raise ValueError('Implausible UTF size')
 def string(offset):
  p=so+offset;end=b.index(b'\0',p);return b[p:end].decode('utf-8')
 def value(pos,t):
  formats=['B','b','H','h','I','i','Q','q','f','d','I']
  if t==11:
   off,length=struct.unpack_from('>II',b,pos);return {'data_offset':do+off,'length':length},pos+8
  fmt='>'+formats[t];v=struct.unpack_from(fmt,b,pos)[0];pos+=struct.calcsize(fmt)
  return (string(v) if t==10 else v),pos
 columns=[];pos=32
 for i in range(cols):
  flags=b[pos];pos+=1
  if flags==0:pos+=3;flags=b[pos];pos+=1
  offset=struct.unpack_from('>I',b,pos)[0];pos+=4;kind=flags&15;storage=flags&240
  constant=None
  if storage==0x30:constant,pos=value(pos,kind)
  columns.append((string(offset),storage,kind,constant))
 result=[]
 for i in range(rows):
  pos=ro+i*width;row={}
  for name,storage,kind,constant in columns:
   if storage==0x50:v,pos=value(pos,kind)
   elif storage==0x30:v=constant
   elif storage in (0,0x10):v=0
   else:raise ValueError('Unsupported UTF storage '+str(storage))
   row[name]=v
  if pos>ro+(i+1)*width:raise ValueError('Row overflow')
  result.append(row)
 return result

def chunk(b,offset=0):
 length=struct.unpack_from('<Q',b,offset+8)[0]
 if length>len(b)-offset-16:raise ValueError('Chunk overflow')
 return utf(b[offset+16:offset+16+length])

def index(path):
 b=path.read_bytes()
 if b[:4]!=b'CPK ':raise ValueError('Not CPK')
 header=chunk(b)[0];toc=header.get('TocOffset')
 if not toc:raise ValueError('No named TOC; ITOC not implemented')
 rows=chunk(b,toc);base=min(toc,header['ContentOffset']);result=[]
 for r in rows:
  name='/'.join(str(r.get(k,'')) for k in ['DirName','FileName'] if r.get(k))
  off=r['FileOffset']+base;size=r['FileSize']
  if off+size>len(b):raise ValueError('File range overflow')
  result.append({'name':name,'offset':off,'size':size,'unpacked':r['ExtractSize'],'magic':b[off:off+16].hex(),'sha256_stored':hashlib.sha256(b[off:off+size]).hexdigest()})
 return {'cpk':str(path),'header':header,'entries':result}
