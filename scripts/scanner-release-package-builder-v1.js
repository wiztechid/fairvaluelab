#!/usr/bin/env node
const fs=require('fs'),path=require('path'),crypto=require('crypto');
const M=require('./scanner-public-evidence-materializer-v1'),B=require('./scanner-controlled-batch-handoff-v1'),A=require('./scanner-publication-authorization-v1');
const ROOT=path.resolve(__dirname,'..'),read=p=>JSON.parse(fs.readFileSync(path.join(ROOT,p),'utf8'));
function canonical(v){if(Array.isArray(v))return v.map(canonical);if(v&&typeof v==='object')return Object.fromEntries(Object.keys(v).sort().map(k=>[k,canonical(v[k])]));return v}
function build({seeds,generatedAt,lastEvaluatedAt,evaluatedUniverseCount=421}={}){
 if(!Array.isArray(seeds)||seeds.length!==91)throw new Error('release package requires exactly 91 reviewed seeds');
 const summary=read('data/summary.json'),registry=read('data/scanner/reason-registry.json'),fairValues={},evidenceByTicker={};
 for(const seed of seeds){const fv=read('data/'+seed.ticker+'.json');fairValues[seed.ticker]=fv;evidenceByTicker[seed.ticker]=M.materialize({seed,canonicalSummary:summary,fairValue:fv,lastEvaluatedAt});}
 const batch=B.buildBatch({seeds,canonicalSummary:summary,fairValues,reasonRegistry:registry,evidenceByTicker,desAsOf:'2026-05-21',generatedAt,evaluatedUniverseCount});
 if(batch.summary.watchlist.count!==91||Object.keys(batch.tickers).length!==91)throw new Error('release package count');
 const snapshotDigest=A.snapshotDigest(batch),tickerSet=Object.keys(batch.tickers).sort(),tickerSetDigest=crypto.createHash('sha256').update(tickerSet.join('\n')).digest('hex');
 const manifest=Object.freeze({contractVersion:'SCANNER_RELEASE_PACKAGE_V1',publicationStatus:'AWAITING_AUTHORIZATION',generatedAt,batchSnapshotDigest:snapshotDigest,tickerSetDigest,tickerCount:tickerSet.length,evaluatedUniverseCount,states:batch.summary.watchlist.states});
 return {batch,manifest};
}
if(require.main===module){const seeds=JSON.parse(fs.readFileSync(process.env.SCANNER_SEED_FILE,'utf8')),generatedAt=process.env.SCANNER_GENERATED_AT,lastEvaluatedAt=process.env.SCANNER_LAST_EVALUATED_AT;if(!generatedAt||!lastEvaluatedAt)throw new Error('release timestamps required');const out=build({seeds,generatedAt,lastEvaluatedAt});const target=process.env.SCANNER_RELEASE_OUTPUT||'scanner-release-package.json';fs.writeFileSync(target,JSON.stringify(canonical(out),null,2)+'\n');console.log(JSON.stringify(out.manifest,null,2))}
module.exports={build};