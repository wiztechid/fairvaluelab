#!/usr/bin/env node
const fs=require('fs'),path=require('path'),crypto=require('crypto'),os=require('os');
const M=require('./scanner-public-evidence-materializer-v1'),B=require('./scanner-controlled-batch-handoff-v1'),A=require('./scanner-publication-authorization-v1'),P=require('./scanner-atomic-authorized-publisher-v1');
const ROOT=path.resolve(__dirname,'..'),read=p=>JSON.parse(fs.readFileSync(path.join(ROOT,p),'utf8'));
const seeds=JSON.parse(fs.readFileSync(process.env.SCANNER_SEED_FILE,'utf8'));if(!Array.isArray(seeds)||seeds.length!==91)throw new Error('expected 91 seeds');
const summary=read('data/summary.json'),registry=read('data/scanner/reason-registry.json'),fairValues={},evidenceByTicker={};
for(const seed of seeds){const fv=read('data/'+seed.ticker+'.json');fairValues[seed.ticker]=fv;evidenceByTicker[seed.ticker]=M.materialize({seed,canonicalSummary:summary,fairValue:fv,lastEvaluatedAt:seed.evaluationDate+'T14:45:00.000Z'});}
const batch=B.buildBatch({seeds,canonicalSummary:summary,fairValues,reasonRegistry:registry,evidenceByTicker,desAsOf:'2026-05-21',generatedAt:'2026-10-03T14:47:00.000Z',evaluatedUniverseCount:421});
if(batch.summary.watchlist.count!==91||Object.keys(batch.tickers).length!==91)throw new Error('batch count');
const digest=A.snapshotDigest(batch),authorization={authorizationId:'STAGING-REHEARSAL-91-V1',authorizedAt:'2026-10-03T14:48:00.000Z',expiresAt:'2026-10-03T15:30:00.000Z',snapshotDigest:digest,status:'APPROVED_FOR_PUBLICATION'};
const root=fs.mkdtempSync(path.join(os.tmpdir(),'scanner-rehearsal-root-'));fs.mkdirSync(path.join(root,'data'),{recursive:true});
const staged=P.stageAuthorizedPublication({batch,authorization,now:'2026-10-03T14:49:00.000Z',root,sourceRoot:ROOT});
if(!fs.existsSync(path.join(staged.stage,'data/scanner/summary.json')))throw new Error('stage missing');
const ss=JSON.parse(fs.readFileSync(path.join(staged.stage,'data/scanner/summary.json'),'utf8'));if(ss.watchlist.count!==91)throw new Error('staged count');
const counts=ss.watchlist.states;console.log(JSON.stringify({contractVersion:'SCANNER_91_STAGING_REHEARSAL_V1',seedCount:seeds.length,stagedCount:ss.watchlist.count,states:counts,snapshotDigest:digest,authorizationId:staged.proof.authorizationId,productionPromoted:false},null,2));
fs.rmSync(staged.stage,{recursive:true,force:true});fs.rmSync(root,{recursive:true,force:true});