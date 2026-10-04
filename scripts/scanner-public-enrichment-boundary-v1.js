#!/usr/bin/env node
const fail=m=>{throw new Error('[scanner-enrichment] '+m)};
const labels={WATCHLIST:'Daftar Pantau',RESEARCH_CONFIRMED:'Terkonfirmasi Riset',WAITING_CONFIRMATION:'Tunggu Konfirmasi',EXTENDED:'Extended',LIMITED_EVIDENCE:'Evidence Terbatas'};
const historyReason={WATCHLIST:'VALUATION_OPPORTUNITY',RESEARCH_CONFIRMED:'MULTI_DOMAIN_CONFIRMATION',WAITING_CONFIRMATION:'PRICE_CONFIRMATION_PENDING',EXTENDED:'PRICE_EXTENDED',LIMITED_EVIDENCE:'EVIDENCE_LIMITED'};
const strength=new Set(['STRONG','ADEQUATE','LIMITED']),domain=new Set(['SUPPORTIVE','MIXED','WEAK','LIMITED','NOT_AVAILABLE']),fresh=new Set(['CURRENT','AGING','STALE','UNAVAILABLE']),catFresh=new Set(['CURRENT','NO_MATERIAL_EVENT','SOURCE_UNAVAILABLE','STALE']);
function enrich({seed,canonicalSummary,fairValue,reasonRegistry,publicEvidence,desAsOf}={}){
 if(!seed||seed.contractVersion!=='PRIVATE_PUBLIC_SCANNER_SEED_V1'||seed.publicationStatus!=='ELIGIBLE_FOR_PUBLIC_ENRICHMENT')fail('eligible sanitized seed required');
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
 const why=seed.reasonCodes.map(code=>{const text=reasonRegistry?.whyWatching?.[code];if(!text)fail('reason registry '+code);return {code,text}});
 const verify=seed.caveatCodes.map(code=>{const text=reasonRegistry?.whatToVerify?.[code];if(!text)fail('caveat registry '+code);return {code,text}});
 const history=(seed.stateHistory||[]).map(h=>{const reason=historyReason[h.state];if(!reason)fail('unsupported public history state '+h.state);return {state:h.state,date:h.date,reason}});
 if(!history.length||history[history.length-1].state!==seed.state)fail('public history/current state');
 return {schemaVersion:'scanner-ticker-v1',ticker:seed.ticker,name:c.name,sector:c.sector,industry:fairValue.companyProfile?.industry??null,des:{eligible:true,universe:canonicalSummary.universeSource,asOf:desAsOf},scanner:{state:seed.state,stateLabel:labels[seed.state],stateChangedDate:history[history.length-1].date},researchLens:[...seed.researchLens],evidenceStrength:{overall:p.overall,quality:p.quality,valuation:p.valuation,price:p.price,catalyst:p.catalyst},whyWatching:why,whatToVerify:verify,freshness:{overall:p.overallFreshness,valuation:p.valuationFreshness,fundamentals:p.fundamentalsFreshness,price:p.priceFreshness,catalyst:seed.catalystFreshness,lastEvaluatedAt:p.lastEvaluatedAt},valuationContext:{status:c.status,evidence:p.valuationContextEvidence},provenance:{valuation:'CANONICAL_FAIR_VALUE',price:'MARKET_DATA',des:'OJK_DES',catalyst:'PUBLIC_MATERIAL_EVENTS'},actions:{primary:{type:'FAIR_VALUE',label:'Cek Fair Value',url:'/fair-value/?ticker='+seed.ticker},secondary:{type:'QSTP',label:'Buka QSTP',url:'/qstp.html?ticker='+seed.ticker}},stateHistory:history};
}
module.exports={enrich};
