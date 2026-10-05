#!/usr/bin/env node
const assert=require('assert'),A=require('./scanner-production-activation-v1');
const key='scanner-activation-authority-test-key-0123456789abcdef',base={activationId:'SCANNER-ACTIVATION-V1',activatedAt:'2026-10-05T08:30:00.000Z',status:'ACTIVATED_FOR_AUTHORIZED_PUBLICATION'};
const good={...base,signature:A.signActivation(base,key)};assert.equal(A.verifyActivation(good,key).activationId,good.activationId);
for(const run of [()=>A.verifyActivation({...good,status:'LOCKED'},key),()=>A.verifyActivation({...good,signature:'0'.repeat(64)},key),()=>A.verifyActivation(good,'wrong-key-that-is-long-enough-0123456789'),()=>A.verifyActivation({...good,extra:true},key),()=>A.verifyActivation({...good,activatedAt:'2026-10-05T08:30:00Z'},key)]){let ok=false;try{run()}catch(_){ok=true}assert(ok)}
console.log('SCANNER_PRODUCTION_ACTIVATION_V1_PASS signed authority required');