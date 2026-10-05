#!/usr/bin/env node
const crypto=require('crypto');
const fail=m=>{throw new Error('[scanner-activation] '+m)};
const EXACT=['activatedAt','activationId','signature','status'];
const payload=a=>[a.activationId,a.activatedAt,a.status].join('|');
function signActivation(a,key){
 if(typeof key!=='string'||key.length<32)fail('authority key');
 return crypto.createHmac('sha256',key).update(payload(a)).digest('hex');
}
function verifyActivation(a,key){
 if(!a||JSON.stringify(Object.keys(a).sort())!==JSON.stringify(EXACT.slice().sort()))fail('exact activation keys');
 if(a.status!=='ACTIVATED_FOR_AUTHORIZED_PUBLICATION')fail('status');
 if(!/^[A-Za-z0-9._-]{8,128}$/.test(a.activationId||''))fail('activationId');
 const t=Date.parse(a.activatedAt);if(Number.isNaN(t)||new Date(t).toISOString()!==a.activatedAt)fail('activatedAt canonical ISO');
 if(typeof key!=='string'||key.length<32)fail('authority key');
 if(!/^[a-f0-9]{64}$/.test(a.signature||''))fail('signature');
 const expected=signActivation(a,key),got=Buffer.from(a.signature,'hex'),want=Buffer.from(expected,'hex');
 if(got.length!==want.length||!crypto.timingSafeEqual(got,want))fail('authority signature');
 return Object.freeze({activationId:a.activationId,activatedAt:a.activatedAt,status:a.status});
}
module.exports={signActivation,verifyActivation};