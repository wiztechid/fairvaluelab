#!/usr/bin/env node
const fs=require('fs'),path=require('path');
const ROOT=path.resolve(__dirname,'..'),fail=m=>{throw new Error('[scanner-production-mode] '+m)};
const p=path.join(ROOT,'contracts/scanner-production-mode-v1.json'),c=JSON.parse(fs.readFileSync(p,'utf8'));
if(JSON.stringify(Object.keys(c).sort())!==JSON.stringify(['contractVersion','mode'].sort()))fail('exact keys');
if(c.contractVersion!=='SCANNER_PRODUCTION_MODE_V1')fail('version');
if(!['LOCKED','CONTROLLED_ACTIVATION'].includes(c.mode))fail('mode');
console.log('SCANNER_PRODUCTION_MODE_PASS',c.mode);
module.exports=c;
