#!/usr/bin/env node
const crypto=require('crypto');
const fail=m=>{throw new Error('[scanner-authorization] '+m)};
const canonical=v=>Array.isArray(v)?v.map(canonical):v&&typeof v==='object'?Object.fromEntries(Object.keys(v).sort().map(k=>[k,canonical(v[k])])):v;
const snapshotDigest=batch=>crypto.createHash('sha256').update(JSON.stringify(canonical(batch))).digest('hex');
function authorize({batch,authorization,now}={}){
 if(!batch||batch.summary?.generationStatus!=='GENERATED'||!batch.tickers)fail('generated batch required');
 const keys=Object.keys(authorization||{}).sort(), expected=['authorizationId','authorizedAt','expiresAt','snapshotDigest','status'].sort();
 if(JSON.stringify(keys)!==JSON.stringify(expected))fail('authorization exact keys');
 if(authorization.status!=='APPROVED_FOR_PUBLICATION')fail('status');
 if(!/^[A-Za-z0-9._-]{8,128}$/.test(authorization.authorizationId||''))fail('authorizationId');
 const at=Date.parse(authorization.authorizedAt), exp=Date.parse(authorization.expiresAt), n=Date.parse(now);
 if([at,exp,n].some(Number.isNaN)||at>n||exp<=n||exp<=at)fail('authorization time window');
 const digest=snapshotDigest(batch);if(authorization.snapshotDigest!==digest)fail('snapshot binding');
 return {authorizationId:authorization.authorizationId,snapshotDigest:digest,authorizedAt:authorization.authorizedAt,expiresAt:authorization.expiresAt};
}
module.exports={snapshotDigest,authorize};
