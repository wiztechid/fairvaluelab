#!/usr/bin/env node
const assert=require('assert'),A=require('./scanner-production-activation-v1');
const good={activationId:'SCANNER-ACTIVATION-V1',activatedAt:'2026-10-05T08:30:00.000Z',status:'ACTIVATED_FOR_AUTHORIZED_PUBLICATION'};
assert.equal(A.verifyActivation(good).activationId,good.activationId);
for(const bad of [{...good,status:'LOCKED'},{...good,extra:true},{...good,activatedAt:'bad'}]){let ok=false;try{A.verifyActivation(bad)}catch(_){ok=true}assert(ok)}
console.log('SCANNER_PRODUCTION_ACTIVATION_V1_PASS');