#!/usr/bin/env node
const fs=require('fs'),crypto=require('crypto');
const fail=m=>{throw new Error('[scanner-release-preflight] '+m)};
const releaseId=process.env.RELEASE_ID,digest=process.env.SNAPSHOT_DIGEST,key=process.env.SCANNER_ACTIVATION_AUTHORITY_KEY;
if(!/^[A-Za-z0-9._-]{8,128}$/.test(releaseId||''))fail('release_id');
if(!/^[a-f0-9]{64}$/.test(digest||''))fail('snapshot_digest');
if(typeof key!=='string'||key.length<32)fail('SCANNER_ACTIVATION_AUTHORITY_KEY missing/too short');
const mode=JSON.parse(fs.readFileSync('contracts/scanner-production-mode-v1.json','utf8'));if(mode.mode!=='CONTROLLED_ACTIVATION')fail('production mode');
console.log('SCANNER_PRODUCTION_RELEASE_PREFLIGHT_PASS',releaseId,digest.slice(0,12)+'…','authority-key-present');