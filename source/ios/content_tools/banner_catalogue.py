"""Read-only research projection of existing Python banner definitions, never a roll engine."""
import copy,hashlib,json,os,sys,tempfile
from pathlib import Path
IOS=Path(__file__).resolve().parents[1]
SERVER=IOS.parent/'server'
DOCS=['gacha_catalogue.json','gacha_community.json','gacha_named.json','gacha_authored.json','gacha_standard.json']
def sha(data):return hashlib.sha256(data).hexdigest()
def canonical(value):return json.dumps(value,sort_keys=True,separators=(',',':'),ensure_ascii=False)
def referenced_units(value):
    out=set()
    if isinstance(value,dict):
        if 'unit_id' in value:out.add(str(value['unit_id']))
        for key in ['units','featured','any_of']:
            if isinstance(value.get(key),list):out.update(str(v) for v in value[key] if isinstance(v,(str,int)))
        for child in value.values():out.update(referenced_units(child))
    elif isinstance(value,list):
        for child in value:out.update(referenced_units(child))
    return out

def project(banners,groups,source_documents,wire_type,supported,art_candidates=(),artwork=(),demo_ids=(),ios_unit_ids=()):
    """All inputs are copied/observed; no player, save, RNG, network or transaction API."""
    if len({str(b["id"]) for b in banners})!=len(banners):raise ValueError("Duplicate resolved banner IDs")
    source_map={};disabled=[]
    for filename,doc in source_documents.items():
        for n,b in enumerate(doc.get('banners',[])):
            source_map.setdefault(str(b['id']),[]).append({'file':'source/server/'+filename,'pointer':f'/banners/{n}','definition_sha256':sha(canonical(b).encode())})
            if not b.get('serve',True):disabled.append({'id':str(b['id']),'name':b.get('name'),'source':source_map[str(b['id'])][-1],'reason':b.get('serve_note','explicitly disabled')})
    memberships={str(b['id']):[g['id'] for g in groups if str(b['id']) in g['ids']] for b in banners}
    aliases={str(a):str(b['id']) for b in banners for a in b.get('alias_ids',[]) if str(a)!=str(b['id'])}
    retrieved={}
    for row in artwork:retrieved.setdefault(row['banner_id'],[]).append(copy.deepcopy(row))
    candidates={}
    for row in art_candidates:candidates.setdefault(Path(row['name']).name,[]).append({'archive':row['archive'],'path':row['name'],'bytes':row['size'],'state':'ZIP index only; body not verified'})
    result=[];required=set();known=set(ios_unit_ids)
    for b in banners:
        uid=str(b['id']);steps=b.get('steps') or [];code=wire_type(b)
        tab='standard' if code in (0,6,900) else 'limited' if code in (50,7) else 'rare'
        offers=[]
        if steps:
            for i,s in enumerate(steps):offers.append({'id':str(int(uid)*10+i+1),'kind':'step','step':i+1,'draws':s.get('draws',b.get('draws',1)),'cost':s.get('cost',b.get('cost')),'guarantee':s.get('guarantee',b.get('guarantee',{})),'guarantee_slots':s.get('guarantee_slots',b.get('guarantee_slots',[])),'pool_override_present':bool(s.get('pool'))})
        else:
            offers.append({'id':str(b.get('detail_id','')),'kind':'primary','draws':b.get('draws',1),'cost':b.get('cost'),'guarantee':b.get('guarantee',{}),'guarantee_slots':b.get('guarantee_slots',[])})
            if b.get('secondary_offer'):
                s=b['secondary_offer'];offers.append({'id':s.get('detail_id',str(int(uid)*10+9)),'kind':'secondary','draws':s.get('draws',1),'cost':s.get('cost'),'guarantee':s.get('guarantee',b.get('guarantee',{})),'guarantee_slots':s.get('guarantee_slots',[])})
        featured=set(str(v) for v in (b.get('community') or {}).get('unit_ids',[]))
        for t in (b.get('pool') or {}).get('tiers',[]) if isinstance(b.get('pool'),dict) else []:featured.update(map(str,t.get('featured',[])))
        units=referenced_units(b.get('pool'));units.update(referenced_units(steps));units.update(featured);required.update(units)
        pool=b.get('pool');tiers=pool.get('tiers',[]) if isinstance(pool,dict) else []
        issues=[]
        if any(s.get('pool') for s in steps):issues.append('Local roll_gacha expands banner.pool instead of step.pool; upstream fixes this. Do not enable these steps yet.')
        if uid=='9200023':issues.append('Local B-ticket item/currency is corrected upstream; current definition is not validated for iOS.')
        if b.get('selection'):handler='exvius_gacha_select._execute; separate selected-unit/prism handler'
        elif b.get('boxes'):handler='gacha_box.roll + next_box; separate box state/advance handler'
        else:handler='player_state.PlayerState.roll_gacha'
        structural=bool(supported(b));ios=uid in demo_ids and structural
        refs=[]
        for role,v in (b.get('art') or {}).items():
            for name in v if isinstance(v,list) else [v]:
                if isinstance(name,str) and name.endswith('.png'):refs.append({'role':role,'filename':name,'indexed_candidates':candidates.get(name,[])})
        missing=[]
        if not ios:missing.append('Not enabled in current iOS demo facade')
        if units-known:missing.append(f'{len(units-known)} explicitly referenced IDs absent from current 423-ID iOS metadata')
        if tiers and any(not t.get('units') for t in tiers):missing.append('Full base-unit/rarity/name master data required to expand generic tiers')
        if b.get('ticket_group_id'):missing.append('F_TICKET_MST + inventory counts + native ticket DTO/command')
        if steps:missing.append('Native step/lap quote and stale-step validation')
        if b.get('reward_pool') or b.get('bonus_rewards') or b.get('bonus_choice') or b.get('milestone_bonus'):missing.append('Mixed/bonus reward inventory metadata and native reward presentation')
        if not retrieved.get(uid):missing.append('Exact banner artwork not yet retrieved/verified')
        result.append({'id':uid,'name':b.get('name',uid),'source_definitions':source_map.get(uid,[]),'type':b.get('type'),'global_tab':tab,'wire_type':code,'archive_groups':memberships[uid],'visible_in_archive':bool(memberships[uid]),'alias_target':aliases.get(uid),'availability':{'schedule_definition':b.get('schedule'),'release':(b.get('community') or {}).get('release',b.get('release')),'limits':{k:b[k] for k in ['single_only','daily_limit','weekly_limit','purchase_limit','lap_limit','state_id'] if k in b},'note':'Account eligibility not evaluated; date fields do not prove roll_gacha enforces historical availability'},'artwork':retrieved.get(uid,[]),'artwork_references':refs,'single':any(int(o['draws'])==1 for o in offers),'multi':any(int(o['draws'])>1 for o in offers),'offers':offers,'ticket_group_id':b.get('ticket_group_id'),'ticket_costs':[o['cost'] for o in offers if isinstance(o.get('cost'),dict) and o['cost'].get('kind') in ['item','important','ticket']],'step_up':bool(steps),'steps':len(steps),'rate_source':copy.deepcopy(b.get('rate_source')),'rate_notice':b.get('rate_notice') or b.get('historical_notice'),'rate_data':{'pool_sha256':sha(canonical(pool).encode()),'explicit_row_count':len(pool) if isinstance(pool,list) else None,'tiers':[{k:t[k] for k in ['rarity','rate','featured_share'] if k in t} for t in tiers],'note':'Definition weights only; not final guaranteed-slot probabilities or proof of original server rates'},'featured_unit_ids':sorted(featured),'guarantee':copy.deepcopy(b.get('guarantee',{})),'guarantee_slots':copy.deepcopy(b.get('guarantee_slots',[])),'backend_handler':handler,'backend_status':'implemented path; conditional on complete master data and validations','known_issues':issues,'facade_structurally_supported':structural,'ios_integration':'existing production demo primary/secondary only' if ios else 'research only; no new production options enabled','missing_dependencies':missing})
    return copy.deepcopy({'schema':1,'scope':'read-only banner research; no account access or eligibility claim','groups':copy.deepcopy(groups),'records':sorted(result,key=lambda r:int(r['id'])),'disabled_definitions':disabled,'required_unit_ids':sorted(required),'source_counts':{f:len(d.get('banners',[])) for f,d in source_documents.items()}})

def snapshot():
    """CLI/build-time ONLY: caller must use a fresh process before legacy imports."""
    if 'player_state' in sys.modules:raise RuntimeError('Use a fresh process for banner research')
    with tempfile.TemporaryDirectory(prefix='ffbe-banner-metadata-') as temp:
        os.environ.update(FFBE_DATA=temp,MST_DIR=temp+'/mst_decoded',TEXT_DIR=temp+'/text_decoded',STATE_FILE=temp+'/unused-campaign.json',GACHA_ONLY='all',GACHA_CAMPAIGN='all',GACHA_STANDARD='1',EXVIUS_SUMMON_ARCHIVE='1')
        sys.path.insert(0,str(SERVER));sys.path.insert(0,str(IOS/'prototype'))
        import ffbe_gacha,gacha_archive,ffbe_state
        from summon_service import SummonService
        from demo_data import BANNER_IDS
        from unittest.mock import patch
        # Any accidental creation of an account or roll is a hard failure.
        import player_state
        with patch.object(player_state.PlayerState,'__init__',side_effect=AssertionError('Research must not create a player')),patch.object(player_state.PlayerState,'roll_gacha',side_effect=AssertionError('Research must not summon')),patch.object(player_state.PlayerState,'save',side_effect=AssertionError('Research must not save')):
            banners=ffbe_gacha.all_banners();groups=gacha_archive.catalogue(banners)
            docs={name:json.loads((SERVER/name).read_text()) for name in DOCS}
            root=IOS/'.local/phase7a';art_lock=IOS/'content_tools/banner-research-art.lock.json'
            artwork=json.loads(art_lock.read_text())['artwork'] if art_lock.exists() else []
            names={name for b in banners for value in (b.get('art') or {}).values() for name in (value if isinstance(value,list) else [value]) if isinstance(name,str) and name.endswith('.png')}
            candidates=[]
            for index_path in sorted((IOS/'.local/phase6a/source-indexes').glob('*.json')):
                index=json.loads(index_path.read_text())
                candidates.extend(dict(row,archive=index['id']) for row in index['entries'] if Path(row['name']).name in names)
            ids=json.loads((IOS/'content_tools/content.lock.json').read_text())['targets']['demo_ids']
            result=project(banners,groups,docs,ffbe_gacha.gacha_type_code,SummonService._supported,candidates,artwork,BANNER_IDS,ids)
            assert ffbe_state.State.player is None
        assert not list(Path(temp).iterdir()),'Metadata access wrote into data/state root'
        result['campaign_accessed']=False;result['transactions']=0
        result['source_hashes']={str(p.relative_to(IOS.parent.parent)):sha(p.read_bytes()) for p in [*(SERVER/n for n in DOCS),SERVER/'ffbe_gacha.py',SERVER/'gacha_archive.py',SERVER/'ffbe_config.py',IOS/'prototype/summon_service.py',IOS/'prototype/demo_data.py',IOS/'content_tools/content.lock.json']}
        return result
if __name__=='__main__':
    import argparse
    p=argparse.ArgumentParser();p.add_argument('--output',type=Path,required=True);a=p.parse_args();r=snapshot();a.output.parent.mkdir(parents=True,exist_ok=True);a.output.write_text(json.dumps(r,indent=2,ensure_ascii=False)+'\n');print(json.dumps({'records':len(r['records']),'archive_visible':sum(v['visible_in_archive'] for v in r['records']),'source_counts':r['source_counts']}))
