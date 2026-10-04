#!/usr/bin/env node
const {enrich}=require('./scanner-public-enrichment-boundary-v1');
const fail=m=>{throw new Error('[scanner-batch] '+m)};
function buildBatch({seeds,canonicalSummary,fairValues,reasonRegistry,evidenceByTicker,desAsOf,generatedAt,evaluatedUniverseCount}={}){
 if(!Array.isArray(seeds)||!seeds.length)fail('non-empty seeds required');
 if(typeof generatedAt!=='string'||Number.isNaN(new Date(generatedAt).valueOf()))fail('generatedAt');
 if(!Number.isInteger(evaluatedUniverseCount)||evaluatedUniverseCount<seeds.length||evaluatedUniverseCount>canonicalSummary.requested)fail('evaluatedUniverseCount');
 const seen=new Set(),tickers=[];
 for(const s of seeds){if(!s||seen.has(s.ticker))fail('duplicate/invalid ticker '+(s&&s.ticker));seen.add(s.ticker);tickers.push(s.ticker)}
 const out=[];
 for(const seed of seeds){
  const fairValue=fairValues&&fairValues[seed.ticker], publicEvidence=evidenceByTicker&&evidenceByTicker[seed.ticker];
  if(!fairValue||!publicEvidence)fail('incomplete batch input '+seed.ticker);
  out.push(enrich({seed,canonicalSummary,fairValue,reasonRegistry,publicEvidence,desAsOf}));
 }
 const stateKeys=['WATCHLIST','RESEARCH_CONFIRMED','WAITING_CONFIRMATION','EXTENDED','LIMITED_EVIDENCE'];
 const states=Object.fromEntries(stateKeys.map(k=>[k,0])); for(const t of out)states[t.scanner.state]++;
 const items=out.map(t=>({ticker:t.ticker,name:t.name,sector:t.sector,state:t.scanner.state,stateLabel:t.scanner.stateLabel,researchLens:t.researchLens,evidenceStrength:t.evidenceStrength.overall,primaryReason:t.whyWatching[0].code,freshness:t.freshness.overall,detail:'/scanner/'+t.ticker+'.json',fairValue:'/fair-value/?ticker='+t.ticker}));
 return {summary:{schemaVersion:'scanner-summary-v1',generationStatus:'GENERATED',generatedAt,universe:{name:canonicalSummary.universeSource,eligible:canonicalSummary.requested,evaluated:evaluatedUniverseCount},watchlist:{count:out.length,states},items},tickers:Object.fromEntries(out.map(t=>[t.ticker,t]))};
}
module.exports={buildBatch};
