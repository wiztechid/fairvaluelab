#!/usr/bin/env node
const crypto=require('crypto');
const H=s=>crypto.createHash('sha256').update(s).digest('hex');
function canonical(v){if(Array.isArray(v))return v.map(canonical);if(v&&typeof v==='object')return Object.keys(v).sort().reduce((o,k)=>(o[k]=canonical(v[k]),o),{});return v}
const stable=v=>JSON.stringify(canonical(v));
const time=(s,n)=>{const d=new Date(s);if(Number.isNaN(+d))throw Error('invalid '+n);return d};
const hex=s=>typeof s==='string'&&/^[a-f0-9]{64}$/.test(s);
function assertionPayload(a){return {eventAnchorId:a.eventAnchorId,lifecycleAssertionId:a.lifecycleAssertionId,parentAssertionId:a.parentAssertionId||null,lifecycleStatus:a.lifecycleStatus,assertedAt:new Date(a.assertedAt).toISOString(),effectiveAt:new Date(a.effectiveAt).toISOString(),materialUntil:a.materialUntil===null?null:new Date(a.materialUntil).toISOString(),supersededByEventAnchorId:a.supersededByEventAnchorId||null}}
function resolveLifecycle({ticker,asOf,events,assertions,sourceAvailable=true}){
 const cutoff=time(asOf,'asOf'),eventMap=new Map(),seen=new Set(),allAssertions=new Map(),byEvent=new Map();
 for(const e of events||[]){if(!/^evt_[A-Za-z0-9_-]{8,64}$/.test(e.eventAnchorId||'')||eventMap.has(e.eventAnchorId))throw Error('invalid/duplicate eventAnchorId');eventMap.set(e.eventAnchorId,e)}
 for(const a of assertions||[]){
  if(seen.has(a.lifecycleAssertionId))throw Error('duplicate lifecycle assertion '+a.lifecycleAssertionId);seen.add(a.lifecycleAssertionId);
  if(!/^life_[A-Za-z0-9_-]{8,64}$/.test(a.lifecycleAssertionId||'')||!eventMap.has(a.eventAnchorId))throw Error('invalid lifecycle identity');
  if(!['ACTIVE','SUPERSEDED','WITHDRAWN'].includes(a.lifecycleStatus))throw Error('invalid lifecycle status');
  const asserted=time(a.assertedAt,'assertedAt'),effective=time(a.effectiveAt,'effectiveAt');if(effective>asserted)throw Error('effectiveAt after assertedAt '+a.lifecycleAssertionId);
  if(a.materialUntil!==null&&a.materialUntil!==undefined){const m=time(a.materialUntil,'materialUntil');if(m<effective)throw Error('materialUntil before effectiveAt')}
  if(a.lifecycleStatus==='SUPERSEDED'){if(!a.supersededByEventAnchorId||a.supersededByEventAnchorId===a.eventAnchorId||!eventMap.has(a.supersededByEventAnchorId))throw Error('invalid supersession target')}
  else if(a.supersededByEventAnchorId)throw Error('unexpected supersession target');
  const expected=H(stable(assertionPayload(a)));if(!hex(a.assertionHash)||a.assertionHash!==expected)throw Error('assertion hash mismatch '+a.lifecycleAssertionId);
  allAssertions.set(a.lifecycleAssertionId,{...assertionPayload(a),assertionHash:a.assertionHash});
  if(asserted>cutoff||effective>cutoff)continue;
  if(!byEvent.has(a.eventAnchorId))byEvent.set(a.eventAnchorId,[]);byEvent.get(a.eventAnchorId).push({...assertionPayload(a),assertionHash:a.assertionHash});
 }
 for(const a of allAssertions.values())if(a.parentAssertionId){const p=allAssertions.get(a.parentAssertionId);if(!p)throw Error('unknown lifecycle parent '+a.lifecycleAssertionId);if(p.eventAnchorId!==a.eventAnchorId)throw Error('cross-event lifecycle parent '+a.lifecycleAssertionId);if(time(p.assertedAt,'parent assertedAt')>=time(a.assertedAt,'assertedAt'))throw Error('lifecycle parent time rollback '+a.lifecycleAssertionId)}
 const out=[];
 for(const id of [...eventMap.keys()].sort()){
  const xs=(byEvent.get(id)||[]).sort((a,b)=>+time(a.effectiveAt,'effectiveAt')-+time(b.effectiveAt,'effectiveAt')||+time(a.assertedAt,'assertedAt')-+time(b.assertedAt,'assertedAt')||a.lifecycleAssertionId.localeCompare(b.lifecycleAssertionId));
  if(!xs.length){out.push({eventAnchorId:id,pitState:'NOT_EVALUATED',activeAssertionId:null});continue}
  for(let i=1;i<xs.length;i++)if(xs[i].parentAssertionId!==xs[i-1].lifecycleAssertionId)throw Error('lifecycle assertion lineage gap '+id);
  if(xs[0].parentAssertionId)throw Error('PIT lifecycle root missing '+id);
  const latest=xs[xs.length-1];
  const same=xs.filter(x=>+time(x.effectiveAt,'effectiveAt')===+time(latest.effectiveAt,'effectiveAt')&&+time(x.assertedAt,'assertedAt')===+time(latest.assertedAt,'assertedAt'));
  if(same.length>1)throw Error('ambiguous same-time lifecycle assertions '+id);
  let state;if(latest.lifecycleStatus==='WITHDRAWN')state='WITHDRAWN';else if(latest.lifecycleStatus==='SUPERSEDED')state='SUPERSEDED';else state=latest.materialUntil!==null&&time(latest.materialUntil,'materialUntil')<cutoff?'STALE':'CURRENT';
  out.push({eventAnchorId:id,pitState:state,activeAssertionId:latest.lifecycleAssertionId,materialUntil:latest.materialUntil,supersededByEventAnchorId:latest.supersededByEventAnchorId});
 }
 const stateMap=new Map(out.map(x=>[x.eventAnchorId,x])),visiting=new Set(),done=new Set();function walk(id){if(visiting.has(id))throw Error('supersession cycle '+id);if(done.has(id))return;visiting.add(id);const s=stateMap.get(id);if(s&&s.pitState==='SUPERSEDED'){const t=stateMap.get(s.supersededByEventAnchorId);if(!t)throw Error('missing successor state '+id);walk(t.eventAnchorId)}visiting.delete(id);done.add(id)}for(const id of stateMap.keys())walk(id);
 const current=out.filter(x=>x.pitState==='CURRENT');
 const contextStatus=!sourceAvailable?'SOURCE_UNAVAILABLE':current.length?'CURRENT_MATERIAL_EVIDENCE':'NO_MATERIAL_EVENT';
 return {schemaVersion:'catalyst-lifecycle-v1',ticker:String(ticker||'').normalize('NFKC').trim().toUpperCase(),asOf:new Date(cutoff).toISOString(),contextStatus,events:out};
}
module.exports={resolveLifecycle,assertionPayload,canonical};
