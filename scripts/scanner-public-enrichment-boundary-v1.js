#!/usr/bin/env node
const fail=m=>{throw new Error('[scanner-enrichment] '+m)};
const seedContract=require('../contracts/private-public-scanner-seed-v1.pinned.json');
const labels={WATCHLIST:'Daftar Pantau',RESEARCH_CONFIRMED:'Terkonfirmasi Riset',WAITING_CONFIRMATION:'Tunggu Konfirmasi',EXTENDED:'Extended',LIMITED_EVIDENCE:'Evidence Terbatas'};
const historicalReason={WATCHLIST:'VALUATION_OPPORTUNITY',WAITING_CONFIRMATION:'PRICE_CONFIRMATION_PENDING',EXTENDED:'PRICE_EXTENDED',LIMITED_EVIDENCE:'EVIDENCE_LIMITED'};
const seedKeys=seedContract.exactKeys;
const states=new Set(seedContract.states);
const lenses=new Set(seedContract.lenses);
const reasonCodes=new Set(seedContract.reasonCodes);
const caveatCodes=new Set(seedContract.caveatCodes);
const exact=(o,keys,n)=>{if(!o||Object.keys(o).length!==keys.length||keys.some(k=>!Object.prototype.hasOwnProperty.call(o,k)))fail(n+' shape')};
function validateSeed(seed){
 exact(seed,seedKeys,'seed');
 if(seed.contractVersion!==seedContract.contractVersion||seed.publicationStatus!==seedContract.publicationStatus)fail('eligible sanitized seed required');
 if(!/^[A-Z0-9]{4,6}$/.test(seed.ticker||''))fail('ticker');
 if(!/^\d{4}-\d{2}-\d{2}$/.test(seed.evaluationDate||'')||Number.isNaN(new Date(seed.evaluationDate+'T00:00:00Z').valueOf()))fail('evaluationDate');
 if(!states.has(seed.state))fail('public state');
 for(const [n,a,set,min,max] of [['researchLens',seed.researchLens,lenses,1,6],['reasonCodes',seed.reasonCodes,reasonCodes,1,4],['caveatCodes',seed.caveatCodes,caveatCodes,0,4]]){
  if(!Array.isArray(a)||a.length<min||a.length>max||new Set(a).size!==a.length||a.some(x=>!set.has(x)))fail(n);
 }
 if(!seedContract.catalystFreshness.includes(seed.catalystFreshness))fail('catalyst freshness');
 if(!Array.isArray(seed.stateHistory)||seed.stateHistory.length<seedContract.stateHistory.min||seed.stateHistory.length>seedContract.stateHistory.max)fail('stateHistory size');
 let prev=null,prevState=null;
 for(const h of seed.stateHistory){
  exact(h,seedContract.stateHistory.exactKeys,'stateHistory');
  if(!states.has(h.state)||!/^\d{4}-\d{2}-\d{2}$/.test(h.date||'')||Number.isNaN(new Date(h.date+'T00:00:00Z').valueOf()))fail('stateHistory entry');
  if(h.date>seed.evaluationDate||(prev&&h.date<prev)||h.state===prevState)fail('stateHistory chronology');
  prev=h.date;prevState=h.state;
 }
 const last=seed.stateHistory[seed.stateHistory.length-1];
 if(last.state!==seed.state||last.date!==seed.evaluationDate)fail('public history/current state/date');
}
const strength=new Set(['STRONG','ADEQUATE','LIMITED']),domain=new Set(['SUPPORTIVE','MIXED','WEAK','LIMITED','NOT_AVAILABLE']),fresh=new Set(['CURRENT','AGING','STALE','UNAVAILABLE']),catFresh=new Set(['CURRENT','NO_MATERIAL_EVENT','SOURCE_UNAVAILABLE','STALE']);
function enrich({seed,canonicalSummary,fairValue,reasonRegistry,publicEvidence,desAsOf}={}){
 validateSeed(seed);
 const c=(canonicalSummary?.stocks||[]).find(x=>x.ticker===seed.ticker);if(!c)fail('canonical summary identity missing');
 if(String(fairValue?.ticker||'').replace(/\.JK$/,'')!==seed.ticker||fairValue.name!==c.name||fairValue.companyProfile?.sector!==c.sector)fail('canonical Fair Value identity mismatch');
 if(!String(canonicalSummary.universeSource||'').startsWith('OJK ')||!String(canonicalSummary.universeSource).includes('DES'))fail('canonical DES source missing');
 if(!/^\d{4}-\d{2}-\d{2}$/.test(desAsOf||''))fail('explicit DES asOf required');
 const p=publicEvidence;if(!p)fail('public categorical evidence required');
 if(!strength.has(p.overall)||!strength.has(p.valuationContextEvidence))fail('public strength');
 for(const k of ['quality','valuation','price','catalyst'])if(!domain.has(p[k]))fail('public domain evidence '+k);
 for(const k of ['overallFreshness','valuationFreshness','fundamentalsFreshness','priceFreshness'])if(!fresh.has(p[k]))fail('public freshness '+k);
 if(!catFresh.has(seed.catalystFreshness))fail('catalyst freshness');
 if(c.status!==p.valuationStatus)fail('valuation status must bind canonical summary');
 if(typeof p.lastEvaluatedAt!=='string'||Number.isNaN(new Date(p.lastEvaluatedAt).valueOf())||p.lastEvaluatedAt.slice(0,10)!==seed.evaluationDate)fail('evaluation time/date binding');
 const why=seed.reasonCodes.map(code=>{const text=reasonRegistry?.whyWatching?.[code];if(!text)fail('reason registry '+code);return {code,text}});
 const verify=seed.caveatCodes.map(code=>{const text=reasonRegistry?.whatToVerify?.[code];if(!text)fail('caveat registry '+code);return {code,text}});
 const history=(seed.stateHistory||[]).map((h,i)=>{const isCurrent=i===seed.stateHistory.length-1;if(isCurrent){let reason;if(h.state==='RESEARCH_CONFIRMED')reason=seed.reasonCodes.includes('MULTI_DOMAIN_CONFIRMATION')?'MULTI_DOMAIN_CONFIRMATION':seed.reasonCodes.includes('VALUATION_OPPORTUNITY')?'VALUATION_OPPORTUNITY':null;else reason=historicalReason[h.state]||seed.reasonCodes[0];if(!reason)fail('current history reason unavailable');return {state:h.state,date:h.date,reason}};const reason=historicalReason[h.state];if(!reason)fail('historical reason unavailable for prior state '+h.state);return {state:h.state,date:h.date,reason}});
 if(!history.length||history[history.length-1].state!==seed.state)fail('public history/current state');
 return {schemaVersion:'scanner-ticker-v1',ticker:seed.ticker,name:c.name,sector:c.sector,industry:fairValue.companyProfile?.industry??null,des:{eligible:true,universe:canonicalSummary.universeSource,asOf:desAsOf},scanner:{state:seed.state,stateLabel:labels[seed.state],stateChangedDate:history[history.length-1].date},researchLens:[...seed.researchLens],evidenceStrength:{overall:p.overall,quality:p.quality,valuation:p.valuation,price:p.price,catalyst:p.catalyst},whyWatching:why,whatToVerify:verify,freshness:{overall:p.overallFreshness,valuation:p.valuationFreshness,fundamentals:p.fundamentalsFreshness,price:p.priceFreshness,catalyst:seed.catalystFreshness,lastEvaluatedAt:p.lastEvaluatedAt},valuationContext:{status:c.status,evidence:p.valuationContextEvidence},provenance:{valuation:'CANONICAL_FAIR_VALUE',price:'MARKET_DATA',des:'OJK_DES',catalyst:'PUBLIC_MATERIAL_EVENTS'},actions:{primary:{type:'FAIR_VALUE',label:'Cek Fair Value',url:'/fair-value/?ticker='+seed.ticker},secondary:{type:'QSTP',label:'Buka QSTP',url:'/qstp.html?ticker='+seed.ticker}},stateHistory:history};
}
module.exports={enrich,validateSeed};
