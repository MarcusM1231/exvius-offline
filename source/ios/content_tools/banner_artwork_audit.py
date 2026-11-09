"""Exhaustive cached-index classification. Exact definition filenames, never name guesses."""
import json,hashlib
from pathlib import Path
from import_content import IOS,sha
ROOT=IOS/'.local/phase7c/artwork'

def inventory():
 ROOT.mkdir(parents=True,exist_ok=True)
 old=json.loads((IOS/'.local/phase7a/banner-catalogue.json').read_text())
 refs={}
 for b in old['records']:
  for r in b['artwork_references']:
   refs.setdefault(r['filename'],[]).append({'banner_id':b['id'],'role':r['role'],'panel_name':r['filename'],'name':b['name']})
 candidates=[];tables=[];indexes={}
 for p in sorted((IOS/'.local/phase6a/source-indexes').glob('*.json')):
  idx=json.loads(p.read_text());indexes[idx['id']]={'path':str(p.relative_to(IOS)),'sha256':sha(p.read_bytes()),'archive_size':idx['archive_size'],'url':idx['url']}
  for e in idx['entries']:
   n=e['name'];name=Path(n).name
   if n.startswith('static/mst_decoded/') and n.endswith('.ndjson') and any(x in name for x in ['UNIT','TICKET','ITEM','LIMITBURST','VISION_CARD']):tables.append(dict(e,archive=idx['id']))
   relevant=name in refs or any(v in n for v in ['static_banner/gacha/','gacha_community/art/','gacha_wiki_extra/']) and n.lower().endswith('.png')
   if not relevant:continue
   provenance='global-targeted-preservation-en-static-banner' if n.startswith('native/en/sd/static_banner/gacha/') else 'community-calendar-preservation' if n.startswith(('static/gacha_community/art/','static/gacha_wiki_extra/')) else 'unverified-language-or-namespace'
   mappings=[]
   for r in refs.get(name,[]):
    if provenance=='global-targeted-preservation-en-static-banner' and ('/main/' in n)!=(r['role']=='banner'):continue
    if provenance=='unverified-language-or-namespace':continue
    mappings.append(r)
   candidates.append({'key':idx['id']+':'+n,'entry':dict(e,archive=idx['id'],url=idx['url'],archive_size=idx['archive_size']),'index':indexes[idx['id']],'mapping':mappings,'provenance':provenance,'status':'indexed_pending_recovery' if mappings else 'unmatched_or_unverified_language','language':'English source namespace' if provenance!='unverified-language-or-namespace' else 'unverified','filename_referenced':name in refs})
 report={'schema':1,'candidates':candidates,'index_pins':indexes,'metadata_tables':tables,'scope':'All eleven cached verified indexes; all current definition references plus banner namespaces; index presence is not PNG verification','counts':{'all_candidates':len(candidates),'referenced_index_paths':sum(r['filename_referenced'] for r in candidates),'eligible_paths':sum(bool(r['mapping']) for r in candidates),'unmatched_or_unverified':sum(not r['mapping'] for r in candidates)}}
 (ROOT/'inventory.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report['counts']));return report
if __name__=='__main__':inventory()
