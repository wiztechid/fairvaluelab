const fs=require('fs'),path=require('path'),{buildBatch}=require('./scanner-controlled-batch-handoff-v1'),{snapshotDigest,authorize}=require('./scanner-publication-authorization-v1');
const ROOT=path.resolve(__dirname,'..'),read=p=>JSON.parse(fs.readFileSync(path.join(ROOT,p),'utf8')),summary=read('data/summary.json'),registry=read('data/scanner/reason-registry.json');
const names=['AADI','AALI'],date='2026-09-29',generatedAt=date+'T03:00:00Z';
const seeds=names.map((ticker,i)=>({contractVersion:'PRIVATE_PUBLIC_SCANNER_SEED_V1',publicationStatus:'ELIGIBLE_FOR_PUBLIC_ENRICHMENT',ticker,evaluationDate:date,state:i?'RESEARCH_CONFIRMED':'WATCHLIST',researchLens:['UNDERVALUED'],reasonCodes:[i?'MULTI_DOMAIN_CONFIRMATION':'VALUATION_OPPORTUNITY'],caveatCodes:[],catalystFreshness:'SOURCE_UNAVAILABLE',stateHistory:[{state:i?'RESEARCH_CONFIRMED':'WATCHLIST',date}]}));
const fairValues=Object.fromEntries(names.map(t=>[t,read('data/'+t+'.json')])),evidenceByTicker={};
for(const ticker of names){const c=summary.stocks.find(x=>x.ticker===ticker);evidenceByTicker[ticker]={overall:'ADEQUATE',valuationContextEvidence:'ADEQUATE',quality:'MIXED',valuation:'SUPPORTIVE',price:'MIXED',catalyst:'NOT_AVAILABLE',overallFreshness:'CURRENT',valuationFreshness:'CURRENT',fundamentalsFreshness:'CURRENT',priceFreshness:'CURRENT',valuationStatus:c.status,lastEvaluatedAt:generatedAt}}
const batch=buildBatch({seeds,canonicalSummary:summary,fairValues,reasonRegistry:registry,evidenceByTicker,desAsOf:'2026-05-21',generatedAt,evaluatedUniverseCount:2});
const digest=snapshotDigest(batch),auth={authorizationId:'scanner-release-0001',status:'APPROVED_FOR_PUBLICATION',snapshotDigest:digest,authorizedAt:'2026-10-04T09:00:00Z',expiresAt:'2026-10-04T11:00:00Z'},now='2026-10-04T10:00:00Z';
authorize({batch,authorization:auth,now});
const reject=(name,b,a,n)=>{if(arguments.length<3)a=auth;if(arguments.length<4)n=now;let ok=false;try{authorize({batch:b,authorization:a,now:n})}catch(_){ok=true}if(!ok)throw new Error('authorization attack passed '+name)};
reject('missing authorization',batch,undefined);reject('wrong status',batch,{...auth,status:'PENDING'});reject('expired',batch,auth,'2026-10-04T12:00:00Z');reject('future authorization',batch,{...auth,authorizedAt:'2026-10-04T10:30:00Z'});reject('extra field',batch,{...auth,approver:'implicit'});
const changed=JSON.parse(JSON.stringify(batch));changed.summary.items[0].state='WAITING_CONFIRMATION';reject('snapshot replay after mutation',changed,auth);
const reordered=JSON.parse(JSON.stringify(batch));reordered.tickers=Object.fromEntries(Object.entries(reordered.tickers).reverse());if(snapshotDigest(reordered)!==digest)throw new Error('canonical digest changed on object key order');
if(read('data/scanner/summary.json').generationStatus!=='NOT_GENERATED')throw new Error('production PRE_ENGINE_LOCK changed');
console.log('SCANNER_PUBLICATION_AUTHORIZATION_V1_PASS snapshot-bound expiring fail-closed; production locked');
