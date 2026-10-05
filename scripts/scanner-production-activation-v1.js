#!/usr/bin/env node
const crypto=require('crypto');
const fail=m=>{throw new Error('[scanner-activation] '+m)};
const EXACT=['activatedAt','activationId','authorizationId','expiresAt','signature','snapshotDigest','status'];
const payload=a=>[a.activationId,a.activatedAt,a.authorizationId,a.expiresAt,a.snapshotDigest,a.status].join('|');
function signActivation(a,key){
 if(typeof key!=='string'||key.length<32)fail('authority key');
 return crypto.createHmac('sha256',key).update(payload(a)).digest('hex');
}
function verifyActivation(a,key,{authorization,now}={}){
 if(!a||JSON.stringify(Object.keys(a).sort())!==JSON.stringify(EXACT.slice().sort()))fail('exact activation keys');
 if(a.status!=='ACTIVATED_FOR_AUTHORIZED_PUBLICATION')fail('status');
 if(!/^[A-Za-z0-9._-]{8,128}$/.test(a.activationId||''))fail('activationId');
 for(const k of ['activatedAt','expiresAt']){const t=Date.parse(a[k]);if(Number.isNaN(t)||new Date(t).toISOString()!==a[k])fail(k+' canonical ISO')}
 if(Date.parse(a.expiresAt)<=Date.parse(a.activatedAt))fail('activation window');
 if(typeof key!=='string'||key.length<32)fail('authority key');
 if(!/^[a-f0-9]{64}$/.test(a.snapshotDigest||'')||!/^[a-f0-9]{64}$/.test(a.signature||''))fail('digest/signature');
 if(!authorization||a.authorizationId!==authorization.authorizationId||a.snapshotDigest!==authorization.snapshotDigest||Date.parse(a.expiresAt)!==Date.parse(authorization.expiresAt))fail('release binding');
 const n=Date.parse(now);if(Number.isNaN(n)||n<Date.parse(a.activatedAt)||n>=Date.parse(a.expiresAt))fail('activation expired/not active');
 const expected=signActivation(a,key),got=Buffer.from(a.signature,'hex'),want=Buffer.from(expected,'hex');
 if(got.length!==want.length||!crypto.timingSafeEqual(got,want))fail('authority signature');
 return Object.freeze({activationId:a.activationId,activatedAt:a.activatedAt,authorizationId:a.authorizationId,expiresAt:a.expiresAt,snapshotDigest:a.snapshotDigest,status:a.status});
}
module.exports={signActivation,verifyActivation};