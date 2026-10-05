#!/usr/bin/env node
const fs=require('fs'),path=require('path'),assert=require('assert'),R=require('./scanner-release1-package-v1');
const seeds=Array.from({length:91},(_,i)=>({ticker:'T'+String(i).padStart(3,'0'),evaluationDate:'2026-10-05',state:'RESEARCH_CONFIRMED'}));
const tickers=Object.fromEntries(seeds.map((s,i)=>[s.ticker,{ticker:s.ticker,ordinal:i}]));
const states={WATCHLIST:0,RESEARCH_CONFIRMED:91,WAITING_CONFIRMATION:0,EXTENDED:0,LIMITED_EVIDENCE:0};
const batch={summary:{generationStatus:'GENERATED',generatedAt:'2026-10-05T14:45:00.000Z',universe:{eligible:612,evaluated:421},watchlist:{count:91,states}},tickers};
const pub='a'.repeat(40),priv='b'.repeat(40);
const a=R.makeRequest({batch,seeds,publicCommit:pub,privateEngineCommit:priv});
const reordered=R.makeRequest({batch:{...batch,tickers:Object.fromEntries(Object.entries(tickers).reverse())},seeds:[...seeds].reverse(),publicCommit:pub,privateEngineCommit:priv});
assert.equal(a.snapshotDigest,reordered.snapshotDigest,'snapshot digest must be canonical');
assert.equal(a.seedDigest,reordered.seedDigest,'seed digest must be order invariant');
assert.equal(a.candidateCount,91);assert.equal(a.evaluatedUniverseCount,421);assert.equal(a.universeCount,612);
assert.equal(a.stateCounts.RESEARCH_CONFIRMED,91);assert.equal(a.publicationStatus,'AWAITING_AUTHORIZATION');
assert.equal(a.authorizationRequired,true);assert.equal(a.activationRequired,true);assert.equal(a.productionMode,'CONTROLLED_ACTIVATION');
const mutated=JSON.parse(JSON.stringify(batch));mutated.tickers.T000.ordinal=999;
assert.notEqual(R.makeRequest({batch:mutated,seeds,publicCommit:pub,privateEngineCommit:priv}).snapshotDigest,a.snapshotDigest,'snapshot mutation must change digest');
for(const run of [
 ()=>R.makeRequest({batch:{...batch,summary:{...batch.summary,universe:{eligible:612,evaluated:420}}},seeds,publicCommit:pub,privateEngineCommit:priv}),
 ()=>R.makeRequest({batch:{...batch,summary:{...batch.summary,watchlist:{count:91,states:{...states,RESEARCH_CONFIRMED:90,WATCHLIST:1}}}},seeds,publicCommit:pub,privateEngineCommit:priv}),
 ()=>R.makeRequest({batch,seeds:seeds.slice(1),publicCommit:pub,privateEngineCommit:priv}),
 ()=>R.makeRequest({batch,seeds,publicCommit:'bad',privateEngineCommit:priv})
]){let blocked=false;try{run()}catch(_){blocked=true}assert(blocked,'invalid release binding accepted')}
const src=fs.readFileSync(path.resolve(__dirname,'scanner-release1-package-v1.js'),'utf8');
for(const x of ['SCANNER_SEED_FILE required','SCANNER_GENERATED_AT required canonical ISO','SCANNER_PUBLIC_COMMIT','SCANNER_PRIVATE_ENGINE_COMMIT','seedDigest','snapshotDigest','RELEASE_PACKAGE_OUTPUT'])assert(src.includes(x),x);
for(const bad of ['activationAuthorityKey=','APPROVED_FOR_PUBLICATION','promoteStagedPublication(','signActivation('])assert(!src.includes(bad),'release package must not self-authorize/promote '+bad);
console.log('SCANNER_RELEASE1_PACKAGE_V1_PASS exact snapshot/cohort/commit binding; authority separated');
