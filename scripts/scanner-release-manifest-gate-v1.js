#!/usr/bin/env node
const fs=require('fs'),path=require('path'),fail=m=>{throw new Error('[scanner-release-manifest] '+m)};
const ROOT=path.resolve(__dirname,'..'),m=JSON.parse(fs.readFileSync(path.join(ROOT,'contracts/scanner-release-manifest-v1.json'),'utf8')),mode=JSON.parse(fs.readFileSync(path.join(ROOT,'contracts/scanner-production-mode-v1.json'),'utf8'));
const keys=['candidateCount','candidateState','canonicalDataCommit','contractVersion','evaluatedCount','notEvaluableCount','privateEngineCommit','productionMode','publicPipelineCommit','publicationStatus','releaseId','universeCount'].sort();
if(JSON.stringify(Object.keys(m).sort())!==JSON.stringify(keys))fail('exact keys');
if(m.contractVersion!=='SCANNER_RELEASE_MANIFEST_V1'||m.releaseId!=='SCANNER-PROD-001')fail('identity');
for(const k of ['canonicalDataCommit','privateEngineCommit','publicPipelineCommit'])if(!/^[a-f0-9]{40}$/.test(m[k]))fail(k);
if(m.universeCount!==612||m.evaluatedCount!==421||m.notEvaluableCount!==191||m.evaluatedCount+m.notEvaluableCount!==m.universeCount)fail('universe accounting');
if(m.candidateCount!==91||m.candidateState!=='RESEARCH_CONFIRMED')fail('candidate accounting');
if(m.productionMode!==mode.mode||m.productionMode!=='CONTROLLED_ACTIVATION')fail('production mode');
if(m.publicationStatus!=='PENDING_AUTHORIZATION')fail('publication status');
console.log('SCANNER_RELEASE_MANIFEST_V1_PASS',m.releaseId,m.candidateCount);
