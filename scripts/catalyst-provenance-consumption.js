#!/usr/bin/env node
const crypto=require('crypto');
const H=s=>crypto.createHash('sha256').update(s).digest('hex');
function canonical(v){if(Array.isArray(v))return v.map(canonical);if(v&&typeof v==='object')return Object.keys(v).sort().reduce((o,k)=>(o[k]=canonical(v[k]),o),{});return v}
const stable=v=>JSON.stringify(canonical(v));
const iso=(s,n)=>{const d=new Date(s);if(Number.isNaN(+d))throw Error('invalid '+n);return d};
const fact=id=>typeof id==='string'&&/^fact_[A-Za-z0-9_-]{8,64}$/.test(id);
const hex=s=>typeof s==='string'&&/^[a-f0-9]{64}$/.test(s);
function originBinding(o){return stable({ticker:String(o.ticker||'').normalize('NFKC').trim().toUpperCase(),observationId:o.observationId,sourceLocator:o.sourceLocator,contentHash:o.contentHash,observedAt:new Date(o.observedAt).toISOString()})}
function resolveProvenance(observations){
 const map=new Map();
 for(const o of observations){
  if(map.has(o.observationId))throw Error('duplicate provenance observation '+o.observationId);
  if(!hex(o.contentHash)||typeof o.sourceLocator!=='string'||!o.sourceLocator.trim())throw Error('invalid provenance source '+o.observationId);
  iso(o.observedAt,'observedAt'); map.set(o.observationId,o);
 }
 const memo=new Map(),visiting=new Set();
 function root(id){
  if(memo.has(id))return memo.get(id); if(visiting.has(id))throw Error('provenance cycle '+id);
  const o=map.get(id);if(!o)throw Error('unknown provenance observation '+id);visiting.add(id);
  let r;
  if(o.sourceClass==='DERIVATIVE'){
   if(!o.originObservationId||o.originObservationId===id)throw Error('derivative missing origin '+id);
   const parent=map.get(o.originObservationId);if(!parent)throw Error('unknown derivative origin '+id);
   if(iso(parent.observedAt,'origin observedAt')>iso(o.observedAt,'derivative observedAt'))throw Error('future origin lineage '+id);
   r=root(o.originObservationId);
  } else {
   if(o.originObservationId)throw Error('non-derivative cannot claim origin '+id);
   r=id;
  }
  visiting.delete(id);memo.set(id,r);return r;
 }
 return [...map.values()].sort((a,b)=>a.observationId.localeCompare(b.observationId)).map(o=>{
  const rid=root(o.observationId),ro=map.get(rid);
  return {observationId:o.observationId,originObservationId:rid,provenanceFamilyId:'prov_'+H(originBinding(ro)).slice(0,20),originBindingHash:H(originBinding(ro))};
 });
}
function receiptPayload(r){return {receiptId:r.receiptId,factId:r.factId,domain:r.domain,consumerArtifactId:r.consumerArtifactId,consumerRevisionId:r.consumerRevisionId,consumerSnapshotHash:r.consumerSnapshotHash,consumedAt:new Date(r.consumedAt).toISOString()}}
function verifyConsumption({events,receipts,asOf}){
 const cutoff=iso(asOf,'asOf'),facts=new Map();
 for(const e of events||[])for(const id of e.originFactIds||[]){if(!fact(id))throw Error('invalid event fact '+id);const t=iso(e.firstObservedAt,'event firstObservedAt');if(!facts.has(id)||t<facts.get(id))facts.set(id,t)}
 const seen=new Set(),valid=[];
 for(const r of receipts||[]){
  if(seen.has(r.receiptId))throw Error('duplicate receipt '+r.receiptId);seen.add(r.receiptId);
  if(!/^rcpt_[A-Za-z0-9_-]{8,64}$/.test(r.receiptId||'')||!fact(r.factId)||!['FUNDAMENTALS','PRICE'].includes(r.domain))throw Error('invalid receipt identity');
  if(!r.consumerArtifactId||!r.consumerRevisionId||!hex(r.consumerSnapshotHash))throw Error('incomplete receipt binding '+r.receiptId);
  const t=iso(r.consumedAt,'consumedAt');if(t>cutoff)throw Error('future consumption '+r.receiptId);
  if(!facts.has(r.factId))throw Error('receipt fact not in Catalyst '+r.receiptId);
  if(t<facts.get(r.factId))throw Error('consumption predates fact '+r.receiptId);
  const expected=H(stable(receiptPayload(r)));if(r.receiptHash!==expected)throw Error('receipt hash mismatch '+r.receiptId);
  valid.push({...receiptPayload(r),receiptHash:r.receiptHash});
 }
 const byFact={};for(const r of valid){if(!byFact[r.factId])byFact[r.factId]=[];byFact[r.factId].push(r)}
 const domains=[...new Set(valid.map(r=>r.domain))].sort();
 return {schemaVersion:'catalyst-consumption-proof-v1',asOf:new Date(cutoff).toISOString(),sharedOriginDomains:domains,receipts:valid.sort((a,b)=>a.receiptId.localeCompare(b.receiptId)),byFact};
}
module.exports={resolveProvenance,verifyConsumption,receiptPayload,canonical};
