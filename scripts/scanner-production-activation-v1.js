#!/usr/bin/env node
const fail=m=>{throw new Error('[scanner-activation] '+m)};
const EXACT=['activatedAt','activationId','status'];
function verifyActivation(a){
 if(!a||JSON.stringify(Object.keys(a).sort())!==JSON.stringify(EXACT.slice().sort()))fail('exact activation keys');
 if(a.status!=='ACTIVATED_FOR_AUTHORIZED_PUBLICATION')fail('status');
 if(!/^[A-Za-z0-9._-]{8,128}$/.test(a.activationId||''))fail('activationId');
 const t=Date.parse(a.activatedAt);if(Number.isNaN(t))fail('activatedAt');
 return Object.freeze({activationId:a.activationId,activatedAt:new Date(t).toISOString(),status:a.status});
}
module.exports={verifyActivation};