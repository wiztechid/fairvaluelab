#!/usr/bin/env node
const cp=require('child_process'),assert=require('assert'),path=require('path'),script=path.resolve(__dirname,'scanner-production-release-preflight-v1.js');
const base={...process.env,RELEASE_ID:'SCANNER-RELEASE-001',SNAPSHOT_DIGEST:'a'.repeat(64),SCANNER_ACTIVATION_AUTHORITY_KEY:'scanner-production-test-authority-key-0123456789'};
cp.execFileSync(process.execPath,[script],{env:base,stdio:'pipe'});
for(const patch of [{SNAPSHOT_DIGEST:'bad'},{RELEASE_ID:'x'},{SCANNER_ACTIVATION_AUTHORITY_KEY:''}]){let blocked=false;try{cp.execFileSync(process.execPath,[script],{env:{...base,...patch},stdio:'pipe'})}catch(_){blocked=true}assert(blocked)}
console.log('SCANNER_PRODUCTION_RELEASE_PREFLIGHT_V1_PASS');