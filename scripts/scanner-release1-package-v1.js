#!/usr/bin/env node
const fs=require('fs'),path=require('path'),crypto=require('crypto');
const M=require('./scanner-public-evidence-materializer-v1'),B=require('./scanner-controlled-batch-handoff-v1'),A=require('./scanner-publication-authorization-v1');
const ROOT=path.resolve(__dirname,'..'),read=p=>JSON.parse(fs.readFileSync(path.join(ROOT,p),'utf8'));
const canonical=v=>Array.isArray(v)?v.map(canonical):v&&typeof v==='object'?Object.fromEntries(Object.keys(v).sort().map(k=>[k,canonical(v[k])])):v;
const digest=v=>crypto.createHash('sha256').update(JSON.stringify(canonical(v))).digest('hex');
const commit=x=>typeof x==='string'&&/^[a-f0-9]{40}$/.test(x);
function makeRequest({batch,seeds,publicCommit,privateEngineCommit}={}){
 if(!Array.isArray(seeds)||seeds.length!==91)throw new Error('expected exact 91 seeds');
 if(!batch||batch.summary?.generationStatus!=='GENERATED'||!batch.tickers)throw new Error('generated batch required');
 const tickers=Object.keys(batch.tickers).sort(),seedTickers=seeds.map(s=>s&&s.ticker).sort();
 if(tickers.length!==91||batch.summary.watchlist?.count!==91||JSON.stringify(tickers)!==JSON.stringify(seedTickers))throw new Error('exact 91 cohort binding');
 if(batch.summary.universe?.eligible!==612||batch.summary.universe?.evaluated!==421)throw new Error('exact universe accounting');
 const states=batch.summary.watchlist?.states||{},expectedStates={WATCHLIST:0,RESEARCH_CONFIRMED:91,WAITING_CONFIRMATION:0,EXTENDED:0,LIMITED_EVIDENCE:0};
 if(JSON.stringify(states)!==JSON.stringify(expectedStates))throw new Error('release state accounting');
 if(typeof batch.summary.generatedAt!=='string'||Number.isNaN(Date.parse(batch.summary.generatedAt))||new Date(Date.parse(batch.summary.generatedAt)).toISOString()!==batch.summary.generatedAt)throw new Error('canonical generatedAt');
 if(!commit(publicCommit)||!commit(privateEngineCommit))throw new Error('exact release commit binding');
 const orderedSeeds=[...seeds].sort((a,b)=>a.ticker.localeCompare(b.ticker));
 return Object.freeze({
  contractVersion:'SCANNER_RELEASE_REQUEST_V1',
  releaseId:'SCANNER-RELEASE-1',
  publicationStatus:'AWAITING_AUTHORIZATION',
  publicCommit,
  privateEngineCommit,
  universeCount:612,
  evaluatedUniverseCount:421,
  candidateCount:91,
  stateCounts:Object.freeze({...states}),
  generatedAt:batch.summary.generatedAt,
  seedDigest:digest(orderedSeeds),
  snapshotDigest:A.snapshotDigest(batch),
  authorizationRequired:true,
  activationRequired:true,
  productionMode:'CONTROLLED_ACTIVATION'
 });
}
function buildPackage({seeds,generatedAt,publicCommit,privateEngineCommit}={}){
 if(!Array.isArray(seeds)||seeds.length!==91)throw new Error('expected exact 91 seeds');
 if(!generatedAt||Number.isNaN(Date.parse(generatedAt))||new Date(Date.parse(generatedAt)).toISOString()!==generatedAt)throw new Error('SCANNER_GENERATED_AT required canonical ISO');
 const summary=read('data/summary.json'),registry=read('data/scanner/reason-registry.json'),fairValues={},evidenceByTicker={};
 for(const seed of seeds){const fv=read('data/'+seed.ticker+'.json');fairValues[seed.ticker]=fv;evidenceByTicker[seed.ticker]=M.materialize({seed,canonicalSummary:summary,fairValue:fv,lastEvaluatedAt:seed.evaluationDate+'T14:45:00.000Z'});}
 const batch=B.buildBatch({seeds,canonicalSummary:summary,fairValues,reasonRegistry:registry,evidenceByTicker,desAsOf:'2026-05-21',generatedAt,evaluatedUniverseCount:421});
 return Object.freeze({request:makeRequest({batch,seeds,publicCommit,privateEngineCommit}),batch});
}
if(require.main===module){
 const seedFile=process.env.SCANNER_SEED_FILE;if(!seedFile)throw new Error('SCANNER_SEED_FILE required');
 const seeds=JSON.parse(fs.readFileSync(seedFile,'utf8')),generatedAt=process.env.SCANNER_GENERATED_AT;
 const publicCommit=process.env.SCANNER_PUBLIC_COMMIT,privateEngineCommit=process.env.SCANNER_PRIVATE_ENGINE_COMMIT;
 const out=buildPackage({seeds,generatedAt,publicCommit,privateEngineCommit});
 if(process.env.RELEASE_REQUEST_OUTPUT)fs.writeFileSync(process.env.RELEASE_REQUEST_OUTPUT,JSON.stringify(out.request,null,2)+'\n');
 if(process.env.BATCH_OUTPUT)fs.writeFileSync(process.env.BATCH_OUTPUT,JSON.stringify(out.batch,null,2)+'\n');
 if(process.env.RELEASE_PACKAGE_OUTPUT)fs.writeFileSync(process.env.RELEASE_PACKAGE_OUTPUT,JSON.stringify(out,null,2)+'\n');
 console.log(JSON.stringify(out.request,null,2));
}
module.exports={makeRequest,buildPackage};
