"""Small read-only banner art sample from pinned cached ZIP indexes; no full archives."""
import json,sys,time
from pathlib import Path
from import_content import IOS,sha,download_member
from range_client import RangeClient
LOCK=Path(__file__).with_name('banner-research-art.lock.json')
ROOT=IOS/'.local/phase7a'
SELECTED={'9100203':['banner'],'49':['banner'],'9200001':['banner','detail_banner'],'9200023':['banner','detail_banner']}
def recover():
    ROOT.mkdir(exist_ok=True)
    if LOCK.exists():
        result=json.loads(LOCK.read_text());rows=result['artwork']
    else:
        by={str(r['id']):r for name in ['gacha_catalogue','gacha_community','gacha_named','gacha_authored'] for r in json.loads((IOS.parent/'server'/f'{name}.json').read_text())['banners']}
        indexes={name:json.loads((IOS/'.local/phase6a/source-indexes'/f'{name}-index.json').read_text()) for name in ['data-001','data-010']};rows=[]
        for uid,kinds in SELECTED.items():
            b=by[uid]
            for kind in kinds:
                name=b['art'][kind];community=name.startswith('Gacha-');archive='data-001' if community else 'data-010';idx=indexes[archive]
                prefix='static/gacha_community/art/' if community else 'native/en/sd/static_banner/gacha/'+('main/' if kind=='banner' else 'sub/')
                matches=[r for r in idx['entries'] if r['name']==prefix+name]
                if len(matches)!=1:raise ValueError('Missing/ambiguous exact banner source: '+name)
                expected=[r['sha256'] for r in b['sources'] if ('url' in r if community else Path(r.get('file','')).name==name) and (r.get('url','').startswith('https://static.wikia.') if community else True)]
                if len(expected)!=1:raise ValueError('No unique existing banner source pin')
                entry=dict(matches[0],archive=archive,url=idx['url'],archive_size=idx['archive_size'],sha256=expected[0])
                if entry['size']>512000 or entry['method'] not in (0,8):raise ValueError('Banner member format/budget')
                rows.append({'banner_id':uid,'role':kind,'provenance':'community-calendar-preservation' if community else 'global-targeted-preservation-en-static-banner','entry':entry,'index_path':str((IOS/'.local/phase6a/source-indexes'/f'{archive}-index.json').relative_to(IOS)),'index_sha256':sha((IOS/'.local/phase6a/source-indexes'/f'{archive}-index.json').read_bytes()),'cache_path':str((ROOT/'sources'/uid/(kind+'.png')).relative_to(IOS))})
        result={'schema':1,'scope':'Developer-only banner research; no production offers enabled','provenance_warning':'Global-targeted preservation is not proof of retail Global CDN byte identity. Community-calendar images are kept separately labeled; no Memorial artwork.','artwork':rows}
    client=RangeClient(interval=1,max_bytes=2000000,journal=ROOT/f'banner-ranges-{time.time_ns()}.json')
    from PIL import Image
    from png_validation import png_info
    for row in rows:
        if sha((IOS/row['index_path']).read_bytes())!=row['index_sha256']:raise ValueError('ZIP index changed')
        e=row['entry'];path=IOS/row['cache_path']
        if not path.exists():download_member(e,path,client=client)
        raw=path.read_bytes()
        if sha(raw)!=e['sha256']:raise ValueError('Banner cache changed')
        import zlib
        if len(raw)!=e['size'] or zlib.crc32(raw)!=e['crc32']:raise ValueError('Banner ZIP identity')
        with Image.open(path) as image:
            image.load();png_info(raw,require_transparency=False,raster=image);row['width'],row['height']=image.size
    text=json.dumps(result,indent=2)+'\n'
    if LOCK.exists() and LOCK.read_text()!=text:raise ValueError('Pinned banner lock changed')
    if not LOCK.exists():LOCK.write_text(text)
    print(json.dumps({'selected_images':len(rows),'network_bytes':client.transferred,'lock':str(LOCK)}))
    return result
if __name__=='__main__':recover()
