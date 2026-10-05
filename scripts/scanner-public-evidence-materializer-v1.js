#!/usr/bin/env node
const fail=m=>{throw new Error('[scanner-public-evidence] '+m)};
const strengthByStatus={SIAP:'STRONG',REVIEW:'ADEQUATE'};
const freshMap={FRESH:'CURRENT',AGING:'AGING',STALE:'STALE'};
function materialize({seed,canonicalSummary,fairValue,lastEvaluatedAt}={}){
 if(!seed||seed.contractVersion!=='PRIVATE_PUBLIC_SCANNER_SEED_V1'||seed.publicationStatus!=='ELIGIBLE_FOR_PUBLIC_ENRICHMENT')fail('sanitized seed required');
 const c=(canonicalSummary?.stocks||[]).find(x=>x.ticker===seed.ticker);if(!c)fail('canonical identity');
 if(!['SIAP','REVIEW'].includes(c.status))fail('valued canonical status required');
 if(String(fairValue?.ticker||'').replace(/\.JK$/,'')!==seed.ticker||fairValue.name!==c.name||fairValue.companyProfile?.sector!==c.sector)fail('fair value identity');
 if(fairValue.analysisStatus!==c.status||fairValue.fairValue?.available!==true)fail('canonical valuation availability');
 if(!seed.researchLens.includes('UNDERVALUED')||!seed.reasonCodes.includes('VALUATION_OPPORTUNITY'))fail('valuation-backed seed required');
 if(typeof lastEvaluatedAt!=='string'||Number.isNaN(Date.parse(lastEvaluatedAt))||lastEvaluatedAt.slice(0,10)!==seed.evaluationDate)fail('evaluation binding');
 const valuationFreshness=freshMap[fairValue.freshnessStatus];if(!valuationFreshness)fail('canonical freshness');
 const valuationContextEvidence=strengthByStatus[c.status];
 return Object.freeze({
  overall:valuationContextEvidence,
  valuationContextEvidence,
  quality:'NOT_AVAILABLE',
  valuation:'SUPPORTIVE',
  price:'NOT_AVAILABLE',
  catalyst:'NOT_AVAILABLE',
  overallFreshness:valuationFreshness,
  valuationFreshness,
  fundamentalsFreshness:'UNAVAILABLE',
  priceFreshness:'UNAVAILABLE',
  valuationStatus:c.status,
  lastEvaluatedAt
 });
}
module.exports={materialize};