#!/usr/bin/env node
const assert=require('assert'),E=require('./scanner-public-enrichment-boundary-v1');
const registry=require('../data/scanner/reason-registry.json'),summary=require('../data/summary.json'),fv=require('../data/AADI.json');
const ev={overall:'ADEQUATE',valuationContextEvidence:'ADEQUATE',quality:'MIXED',valuation:'SUPPORTIVE',price:'MIXED',catalyst:'NOT_AVAILABLE',overallFreshness:'CURRENT',valuationFreshness:'CURRENT',fundamentalsFreshness:'CURRENT',priceFreshness:'CURRENT',valuationStatus:summary.stocks.find(x=>x.ticker==='AADI').status,lastEvaluatedAt:'2026-09-29T03:00:00Z'};
const base={contractVersion:'PRIVATE_PUBLIC_SCANNER_SEED_V1',publicationStatus:'ELIGIBLE_FOR_PUBLIC_ENRICHMENT',ticker:'AADI',evaluationDate:'2026-09-29',state:'WATCHLIST',researchLens:['UNDERVALUED'],reasonCodes:['MATERIAL_CATALYST'],caveatCodes:['CATALYST_UNAVAILABLE'],catalystFreshness:'SOURCE_UNAVAILABLE',stateHistory:[{state:'WATCHLIST',date:'2026-09-29'}]};
const run=seed=>E.enrich({seed,canonicalSummary:summary,fairValue:fv,reasonRegistry:registry,publicEvidence:ev,desAsOf:'2026-05-21'});
let o=run(base);assert.equal(o.whyWatching[0].code,'MATERIAL_CATALYST');assert.equal(o.stateHistory[0].reason,'VALUATION_OPPORTUNITY');
const states=[['WATCHLIST','VALUATION_OPPORTUNITY'],['RESEARCH_CONFIRMED','MULTI_DOMAIN_CONFIRMATION'],['WAITING_CONFIRMATION','PRICE_CONFIRMATION_PENDING'],['LIMITED_EVIDENCE','EVIDENCE_LIMITED']];
for(const [state,reason] of states){const seed={...base,state,stateHistory:[{state,date:'2026-09-29'}]};o=run(seed);assert.equal(o.stateHistory[0].reason,reason);}
let failed=false;try{run({...base,stateHistory:[{state:'DETECTED',date:'2026-09-28'},{state:'WATCHLIST',date:'2026-09-29'}]})}catch(e){failed=true}assert(failed,'unsupported private history state crossed public boundary');
failed=false;try{E.enrich({seed:base,canonicalSummary:summary,fairValue:{...fv,name:'Private Alias'},reasonRegistry:registry,publicEvidence:ev,desAsOf:'2026-05-21'})}catch(e){failed=true}assert(failed,'canonical identity mismatch accepted');
failed=false;try{E.enrich({seed:base,canonicalSummary:summary,fairValue:fv,reasonRegistry:registry,publicEvidence:{...ev,lastEvaluatedAt:'2026-09-30T03:00:00Z'},desAsOf:'2026-05-21'})}catch(e){failed=true}assert(failed,'evaluation timestamp escaped sanitized seed date');
let ext=false;try{run({...base,state:'EXTENDED',stateHistory:[{state:'EXTENDED',date:'2026-09-29'}]})}catch(e){ext=true}assert(ext,'EXTENDED must not cross private seed ingress');
console.log('SCANNER_PUBLIC_ENRICHMENT_BOUNDARY_V1_PASS');

const mustFail=(seed,msg)=>{let x=false;try{run(seed)}catch(e){x=true}assert(x,msg)};
mustFail({...base,privateScore:'secret'},'unknown/private seed field accepted');
mustFail({...base,researchLens:['UNDERVALUED','UNDERVALUED']},'duplicate lens accepted');
mustFail({...base,reasonCodes:['VALUATION_OPPORTUNITY','VALUATION_OPPORTUNITY']},'duplicate reason accepted');
mustFail({...base,stateHistory:[{state:'WATCHLIST',date:'2026-09-26'},{state:'WAITING_CONFIRMATION',date:'2026-09-27'},{state:'RESEARCH_CONFIRMED',date:'2026-09-28'},{state:'WATCHLIST',date:'2026-09-29'}]},'history >3 accepted');
mustFail({...base,stateHistory:[{state:'WAITING_CONFIRMATION',date:'2026-09-29'},{state:'WATCHLIST',date:'2026-09-28'}]},'nonchronological history accepted');
mustFail({...base,stateHistory:[{state:'WATCHLIST',date:'2026-09-28'}]},'current state date not bound to evaluation date');
mustFail({...base,stateHistory:[{state:'WATCHLIST',date:'2026-09-28'},{state:'WATCHLIST',date:'2026-09-29'}]},'adjacent duplicate public states accepted');
