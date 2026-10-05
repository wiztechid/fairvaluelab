#!/usr/bin/env node
const fs=require('fs'),assert=require('assert');const s=fs.readFileSync(require('path').resolve(__dirname,'scanner-release1-package-v1.js'),'utf8');
for(const x of ['SCANNER_SEED_FILE required','expected exact 91 seeds','SCANNER_GENERATED_AT required','authorizationRequired:true','activationRequired:true','CONTROLLED_ACTIVATION','snapshotDigest'])assert(s.includes(x),x);
for(const bad of ['activationAuthorityKey=','APPROVED_FOR_PUBLICATION\',snapshotDigest','promoteStagedPublication('])assert(!s.includes(bad),'release package must not self-authorize/promote '+bad);
console.log('SCANNER_RELEASE1_PACKAGE_V1_PASS');