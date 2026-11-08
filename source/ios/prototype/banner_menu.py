"""Read-only native menu and live quotes. Historical definitions never authorize a roll."""
import copy
from summon_service import SummonService, SummonError

VALIDATED = frozenset(('9100203', '49'))

def text_guarantee(value):
    if not value: return 'No additional guaranteed slot.'
    if value.get('rarity'): return f"At least {value.get('count', 1)} unit(s) of {value['rarity']}★ or higher."
    if value.get('unit_id'): return 'Includes a specified unit: ' + str(value['unit_id'])
    return 'Special guaranteed pool; see rates.'

class MenuSummonService(SummonService):
    def _definitions(self):
        # No gacha_archive.menu/player access: catalogue is a pure definition projection.
        if hasattr(self, '_menu_definitions'): return self._menu_definitions
        rows = {str(b['id']): copy.deepcopy(b) for b in self.gacha.all_banners()}
        rows.update(copy.deepcopy(self.catalogue))
        # Upstream v0.1.25 correction, isolated to iOS projection while tickets stay disabled.
        if '9200023' in rows: rows['9200023']['cost'] = {'kind':'item','item_id':1209001902,'amount':10}
        self._menu_definitions=rows
        return rows

    def quote(self, banner_id, offer='primary'):
        with self.lock:
            rows=self._definitions()
            if str(banner_id) not in rows: raise SummonError('unknown_banner','Unknown banner')
            b=rows[str(banner_id)];steps=b.get('steps') or []
            allowed = ['primary'] + (['secondary'] if b.get('secondary_offer') else [])
            if offer not in allowed: raise SummonError('invalid_offer','This offer is unavailable; refresh the menu')
            sid=str(b.get('state_id',b['id']));g=self.player.data.get('gacha',{})
            step=int(g.get('step',{}).get(sid,0)) if isinstance(g.get('step'),dict) else 0
            # Existing engine uses gacha.steps; read without setdefault/banner_state.
            step=int(g.get('steps',{}).get(sid,step)) if isinstance(g.get('steps'),dict) else step
            step=step % len(steps) if steps else 0
            chosen=(steps[step] if steps else self._offer(b,offer)) or b
            cost=copy.deepcopy(chosen.get('cost',b.get('cost')) or {'kind':'ticket' if b.get('ticket_group_id') else 'free','amount':0})
            if not isinstance(cost,dict): cost={'kind':'unsupported','amount':0}
            kind=cost.get('kind','unknown');amount=int(cost.get('amount') or 0)
            cur=self.player.data.get('currencies',{})
            balance=sum(int(cur.get(k,0)) for k in ('lapis_free','lapis_paid')) if kind=='lapis' else int(cur.get(kind,0))
            item=str(cost.get('item_id',''))
            if kind in ('item','important'):
                inventory=self.player.data.get('inventory',{})
                balance=sum(int(r.get('count',0)) for r in inventory.get('items',[]) if str(r.get('item_id'))==item and int(r.get('item_type',0))==(20 if kind=='item' else 23))
            reason='';supported=str(b['id']) in VALIDATED and str(b['id']) in self.catalogue and self._supported(b)
            if not supported:
                reason=('Step-up summons are not yet enabled.' if steps else 'Ticket/box/selection handling is not yet enabled.' if b.get('boxes') or b.get('selection') or kind in ('item','important','unsupported') or not b.get('cost') and b.get('ticket_group_id') else 'Historical banner: complete unit data and transaction validation required.')
            elif self.player.mode=='frozen':reason='Campaign is read-only.'
            else:
                pool=self.engine.expand_pool(b)
                if not pool or any(not self.engine.unit_mst(r['unit_id']) for r in pool): supported=False;reason='Required unit metadata is unavailable.'
                elif balance<amount:reason='Insufficient ' + ('Lapis' if kind=='lapis' else kind) + '.'
                cap=int(b.get('purchase_limit') or 0)
                used=int(g.get('user_banners',{}).get(sid,{}).get('total_exe_count',0))
                period,_start,_end=self.engine.gacha_period(b)
                daily=g.get('daily',{}).get(sid,{})
                limit=int(b.get('weekly_limit') or b.get('daily_limit') or 0)
                if cap and used>=cap:reason='Purchase limit reached.'
                if limit and daily.get('date')==period and int(daily.get('count',0))>=limit:reason='Usage limit reached.'
            guarantee=chosen.get('guarantee',b.get('guarantee',{}))
            slots=chosen.get('guarantee_slots',b.get('guarantee_slots',[]))
            return {'banner_id':str(b['id']),'offer':offer,'detail_id':str(chosen.get('detail_id',b.get('detail_id',''))),'draws':int(chosen.get('draws',b.get('draws',1))), 'cost':cost,'balance':balance,'supported':supported,'eligible':supported and not reason,'reason':reason,'guarantee':text_guarantee(guarantee),'guarantee_slots':copy.deepcopy(slots),'step':step+1 if steps else 0,'steps':len(steps),'lap':int(g.get('completed_laps',{}).get(sid,0))+1 if steps else 0,'ticket_group':str(b.get('ticket_group_id') or ''),'tickets':self._tickets(b),'usage':int(g.get('user_banners',{}).get(sid,{}).get('total_exe_count',0)),'purchase_limit':int(b.get('purchase_limit') or 0)}

    def _tickets(self,b):
        if not b.get('ticket_group_id'):return []
        try:
            rows=self.engine._load_ndjson('F_TICKET_MST.ndjson').get('__rows__',[])
        except OSError:return []
        inv=self.player.data.get('inventory',{})
        result=[]
        for r in rows:
            if str(r.get('zF6QIY2r'))!=str(b['ticket_group_id']):continue
            typ=int(r.get('89EvGKHx',23));uid=str(r.get('tL6G9egd',''))
            result.append({'id':str(r.get('zJ1A6HXm','')),'item_id':uid,'balance':sum(int(v.get('count',0)) for v in inv.get('items',[]) if str(v.get('item_id'))==uid and int(v.get('item_type',0))==typ),'enabled':False})
        return result

    def menu(self):
        with self.lock:
            import gacha_archive
            definitions=self._definitions();groups=gacha_archive.catalogue(list(definitions.values()))
            memberships={uid:[g['id'] for g in groups if uid in g['ids']] for uid in definitions}
            records=[]
            for uid,b in definitions.items():
                # Keep the two validated demo definitions visible even when archive aliases hide them.
                if not memberships[uid] and uid not in VALIDATED:continue
                code=self.gacha.gacha_type_code(b)
                tab='standard' if code in (0,6,900) else 'limited' if code in (50,7) else 'rare'
                # Production demos preserve their original wire tab (not community archive override).
                offers=[self.quote(uid,o) for o in ['primary']+(['secondary'] if b.get('secondary_offer') else [])]
                featured=[]
                pool=b.get('pool') or {}
                if isinstance(pool,dict):
                    for t in pool.get('tiers',[]):
                        for mid in t.get('featured',[]):
                            if str(mid) not in featured:featured.append(str(mid))
                rates=[]
                if isinstance(pool,dict):
                    rates=[{'rarity':int(t.get('rarity',0)),'weight':float(t.get('rate',0))} for t in pool.get('tiers',[])]
                records.append({'id':uid,'name':b.get('name',uid),'category':tab,'groups':memberships[uid],'playable':uid in VALIDATED and uid in self.catalogue,'offers':offers,'featured':featured,'rates':rates,'notice':b.get('rate_notice') or b.get('historical_notice') or 'Repository-defined rates; guaranteed slots may alter final probabilities.','description':b.get('description') if isinstance(b.get('description'),str) else '', 'availability':'Available' if uid in VALIDATED else offers[0]['reason']})
            return {'banners':sorted(records,key=lambda r:(not r['playable'],int(r['id']))),'groups':[{'id':g['id'],'label':g['label']} for g in groups]}

    def summon(self,banner_id,offer='primary'):
        # Preserve the pre-existing full-data HTTP development facade. The new
        # native menu still only enables VALIDATED; embedded iOS always uses demo.
        if not self.demo:
            return super().summon(banner_id,offer)
        with self.lock:
            q=self.quote(banner_id,offer)
            if not q['supported']:raise SummonError('unsupported_banner',q['reason'])
            if not q['eligible']:raise SummonError('summon_refused',q['reason'])
            return super().summon(banner_id,offer)
