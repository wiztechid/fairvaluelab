#!/usr/bin/env node
const fs=require('fs'),path=require('path'),M=require('./scanner-public-evidence-materializer-v1'),B=require('./scanner-controlled-batch-handoff-v1'),A=require('./scanner-publication-authorization-v1');
const ROOT=path.resolve(__dirname,'..'),read=p=>JSON.parse(fs.readFileSync(path.join(ROOT,p),'utf8'));
const seedFile=process.env.SCANNER_SEED_FILE;if(!seedFile)throw new Error('SCANNER_SEED_FILE required');
const seeds=JSON.parse(fs.readFileSync(seedFile,'utf8'));if(!Array.isArray(seeds)||seeds.length!==91)throw new Error('expected exact 91 seeds');
const summary=read('data/summary.json'),registry=read('data/scanner/reason-registry.json'),fairValues={},evidenceByTicker={};
const generatedAt=process.env.SCANNER_GENERATED_AT;if(!generatedAt||Number.isNaN(Date.parse(generatedAt)))throw new Error('SCANNER_GENERATED_AT required');
for(const seed of seeds){const fv=read('data/'+seed.ticker+'.json');fairValues[seed.ticker]=fv;evidenceByTicker[seed.ticker]=M.materialize({seed,canonicalSummary:summary,fairValue:fv,lastEvaluatedAt:seed.evaluationDate+'T14:45:00.000Z'});}
const batch=B.buildBatch({seeds,canonicalSummary:summary,fairValues,reasonRegistry:registry,evidenceByTicker,desAsOf:'2026-05-21',generatedAt,evaluatedUniverseCount:421});
const digest=A.snapshotDigest(batch),request={contractVersion:'SCANNER_RELEASE_REQUEST_V1',releaseId:'SCANNER-RELEASE-1',candidateCount:91,evaluatedUniverseCount:421,generatedAt,snapshotDigest:digest,authorizationRequired:true,activationRequired:true,productionMode:'CONTROLLED_ACTIVATION'};
if(process.env.RELEASE_REQUEST_OUTPUT)fs.writeFileSync(process.env.RELEASE_REQUEST_OUTPUT,JSON.stringify(request,null,2)+'\n');
if(process.env.BATCH_OUTPUT)fs.writeFileSync(process.env.BATCH_OUTPUT,JSON.stringify(batch,null,2)+'\n');
console.log(JSON.stringify(request,null,2));