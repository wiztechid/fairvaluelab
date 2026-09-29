#!/usr/bin/env node
const crypto=require('crypto');
const H=s=>crypto.createHash('sha256').update(s).digest('hex');
function canonical(v){if(Array.isArray(v))return v.map(canonical);if(v&&typeof v==='object')return Object.keys(v).sort().reduce((o,k)=>(o[k]=canonical(v[k]),o),{});return v}
const stable=v=>JSON.stringify(canonical(v));
function adapt({context,lifecycle}){
 if(!context||!lifecycle)throw Error('missing frozen Catalyst input');
 const ticker=String(context.ticker||'').replace(/\.JK$/,'').toUpperCase(),lt=String(lifecycle.ticker||'').replace(/\.JK$/,'').toUpperCase();
 if(!/^[A-Z0-9]{4,6}$/.test(ticker)||ticker!==lt)throw Error('Catalyst ticker binding mismatch');
 const ca=new Date(context.asOf),la=new Date(lifecycle.asOf);if(Number.isNaN(+ca)||Number.isNaN(+la)||ca.toISOString()!==la.toISOString())throw Error('Catalyst PIT asOf mismatch');
 if(typeof lifecycle.snapshotHash!=='string'||!/^[a-f0-9]{64}$/.test(lifecycle.snapshotHash))throw Error('invalid lifecycle snapshotHash');
 const body={schemaVersion:lifecycle.schemaVersion,ticker:lifecycle.ticker,asOf:lifecycle.asOf,contextStatus:lifecycle.contextStatus,events:lifecycle.events};
 if(H(stable(body))!==lifecycle.snapshotHash)throw Error('lifecycle snapshotHash mismatch');
 const states=new Set((lifecycle.events||[]).map(x=>x.pitState));
 const current=states.has('CURRENT'),review=states.has('SUPERSEDED')||states.has('WITHDRAWN');
 let catalystEvidence,catalystFreshness,reasonCodes=[],caveatCodes=[];
 if(context.contextStatus==='SOURCE_UNAVAILABLE'||lifecycle.contextStatus==='SOURCE_UNAVAILABLE'){catalystEvidence='NOT_AVAILABLE';catalystFreshness='SOURCE_UNAVAILABLE';caveatCodes=['CATALYST_UNAVAILABLE']}
 else if(context.contextStatus==='CURRENT_MATERIAL_EVIDENCE'&&current&&lifecycle.contextStatus==='CURRENT_MATERIAL_EVIDENCE'){catalystEvidence='SUPPORTIVE';catalystFreshness='CURRENT';reasonCodes=['MATERIAL_CATALYST']}
 else if(context.contextStatus==='STALE_EVIDENCE'||states.has('STALE')){catalystEvidence='LIMITED';catalystFreshness='STALE';caveatCodes=['DATA_STALE']}
 else if(context.contextStatus==='NO_MATERIAL_EVENT'||lifecycle.contextStatus==='NO_MATERIAL_EVENT'){catalystEvidence='LIMITED';catalystFreshness='NO_MATERIAL_EVENT'}
 else {catalystEvidence='LIMITED';catalystFreshness='NO_MATERIAL_EVENT';caveatCodes=['CATALYST_UNVERIFIED']}
 if(review&&!caveatCodes.includes('MATERIAL_EVENT_REVIEW'))caveatCodes.push('MATERIAL_EVENT_REVIEW');
 if(reasonCodes.includes('MATERIAL_CATALYST')&&!current)throw Error('positive Catalyst reason without CURRENT lifecycle');
 return {schemaVersion:'scanner-catalyst-evidence-v1',ticker,asOf:ca.toISOString(),catalystEvidence,catalystFreshness,reasonCodes,caveatCodes,sourceBinding:{contextAsOf:ca.toISOString(),lifecycleSnapshotHash:lifecycle.snapshotHash}};
}
module.exports={adapt,canonical};
