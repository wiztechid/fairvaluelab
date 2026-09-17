# Build a strict market-actor layer from verified cached evidence only.
# Broker code identifies an exchange member/securities firm; it is NOT evidence of controller activity by itself.
import json
from pathlib import Path
from des_universe import TICKERS

DATA=Path('data'); CAT=DATA/'catalysts'; OUT=DATA/'market_actors'; OUT.mkdir(parents=True,exist_ok=True)

def clean_controller(c):
    if not isinstance(c,dict): return {'status':'UNVERIFIED','direct':None,'ultimate':None,'ownershipPct':None,'sourceUrl':None,'sourceDate':None}
    verified=c.get('status')=='VERIFIED' and bool(c.get('sourceUrl'))
    return {'status':'VERIFIED' if verified else 'UNVERIFIED','direct':(c.get('controller') or c.get('direct')) if verified else None,'ultimate':c.get('ultimate') if verified else None,'ownershipPct':c.get('ownershipPct') if verified else None,'sourceUrl':c.get('sourceUrl') if verified else None,'sourceDate':c.get('sourceDate') if verified else None}

def actor_event(e):
    cats=e.get('categories') or []
    actor=any(x in cats for x in ['INSIDER','CONTROLLER','AFFILIATE','RIGHTS','BUYBACK','MNA'])
    # A broker relationship is displayed only when the source record explicitly supplies the code/name.
    bc=e.get('brokerCode'); bn=e.get('brokerName')
    return {'date':e.get('publishedAt'),'title':e.get('title'),'categories':cats,'sourceUrl':e.get('sourceUrl'),'controllerRelated':bool(e.get('controllerRelated') or actor),'relatedParty':e.get('relatedParty'),'brokerCode':bc if bc else None,'brokerName':bn if bc and bn else None,'brokerVerified':bool(bc and e.get('brokerVerification') in ('OFFICIAL_IDX','OFFICIAL_EXCHANGE_MEMBER','VERIFIED'))}

summary=[]
for t in TICKERS:
    cp=CAT/f'{t}.json'; c={}
    if cp.exists():
        try:c=json.load(open(cp,encoding='utf-8'))
        except: c={}
    controller=clean_controller(c.get('controllerProfile') or {})
    events=[actor_event(e) for e in (c.get('events') or []) if isinstance(e,dict)]
    related=[e for e in events if e['controllerRelated'] or e['brokerCode']]
    brokers=[]; seen=set()
    for e in related:
        if e['brokerCode'] and e['brokerVerified'] and e['brokerCode'] not in seen:
            seen.add(e['brokerCode']);brokers.append({'code':e['brokerCode'],'name':e['brokerName'],'verification':'VERIFIED','sourceUrl':e['sourceUrl'],'note':'Kode broker adalah identitas Anggota Bursa; bukan bukti afiliasi/pengendali tanpa keterbukaan eksplisit.'})
    out={'ticker':t,'controller':controller,'brokers':brokers,'actorEvents':related,'policy':{'controller':'Only official/verified disclosure may identify controller or ultimate owner.','broker':'Broker code is descriptive market-actor metadata only. Never infer accumulation, affiliation, or controller activity from broker code alone.'}}
    json.dump(out,open(OUT/f'{t}.json','w',encoding='utf-8'),ensure_ascii=False,indent=2)
    summary.append({'ticker':t,'controllerStatus':controller['status'],'verifiedBrokerCodes':len(brokers),'actorEvents':len(related)})
json.dump({'sourcePolicy':'IDX/KSEI/issuer official evidence only','stocks':summary},open(OUT/'summary.json','w',encoding='utf-8'),ensure_ascii=False,indent=2)
print('MARKET_ACTORS_DONE',len(summary))
