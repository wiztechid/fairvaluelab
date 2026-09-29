#!/usr/bin/env node
const crypto=require('crypto');
const H=s=>crypto.createHash('sha256').update(s).digest('hex');
function canonical(v){if(Array.isArray(v))return v.map(canonical);if(v&&typeof v==='object')return Object.keys(v).sort().reduce((o,k)=>(o[k]=canonical(v[k]),o),{});return v}
const stable=v=>JSON.stringify(canonical(v));
const iso=(s,n)=>{const d=new Date(s);if(Number.isNaN(+d))throw Error('invalid '+n);return d};
const fact=id=>typeof id==='string'&&/^fact_[A-Za-z0-9_-]{8,64}$/.test(id);
const hex=s=>typeof s==='string'&&/^[a-f0-9]{64}$/.test(s);
function originBinding(o){return stable({ticker:String(o.ticker||'').normalize('NFKC').trim().toUpperCase(),observationId:o.observationId,sourceLocator:o.sourceLocator,contentHash:o.contentHash,observedAt:new Date(o.observedAt).toISOString()})}
function resolveProvenance(observations,{trustedOriginClasses=['PRIMARY','CORRECTION']}={}){
 const map=new Map();
 for(const o of observations){
  if(map.has(o.observationId))throw Error('duplicate provenance observation '+o.observationId);
  if(!['PRIMARY','CORRECTION','CORROBORATION','DERIVATIVE','RUMOR'].includes(o.sourceClass))throw Error('invalid sourceClass '+o.observationId);
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
   if(!trustedOriginClasses.includes(o.sourceClass))throw Error('unproven origin class '+id);
   r=id;
  }
  visiting.delete(id);memo.set(id,r);return r;
 }
 return [...map.values()].sort((a,b)=>a.observationId.localeCompare(b.observationId)).map(o=>{
  const rid=root(o.observationId),ro=map.get(rid);
  return {observationId:o.observationId,originObservationId:rid,provenanceFamilyId:'prov_'+H(originBinding(ro)).slice(0,20),originBindingHash:H(originBinding(ro))};
 });
}
function receiptPayload(r){return {receiptId:r.receiptId,parentReceiptId:r.parentReceiptId||null,receiptStatus:r.receiptStatus||'ACTIVE',ticker:String(r.ticker||'').normalize('NFKC').trim().toUpperCase(),eventAnchorId:r.eventAnchorId,factId:r.factId,domain:r.domain,consumerArtifactId:r.consumerArtifactId,consumerRevisionId:r.consumerRevisionId,consumerSnapshotHash:r.consumerSnapshotHash,consumedAt:new Date(r.consumedAt).toISOString()}}
function verifyConsumption({ticker,events,receipts,asOf}){
 const cutoff=iso(asOf,'asOf'),facts=new Map(),normTicker=String(ticker||'').normalize('NFKC').trim().toUpperCase();if(!/^[A-Z0-9]{1,12}(\.JK)?$/.test(normTicker))throw Error('invalid consumption ticker');
 for(const e of events||[]){if(!/^evt_[A-Za-z0-9_-]{8,64}$/.test(e.eventAnchorId||''))throw Error('invalid event anchor');for(const id of e.originFactIds||[]){if(!fact(id))throw Error('invalid event fact '+id);const t=iso(e.firstObservedAt,'event firstObservedAt'),prior=facts.get(id);if(prior&&prior.eventAnchorId!==e.eventAnchorId)throw Error('fact bound to multiple event anchors '+id);facts.set(id,{firstObservedAt:prior&&prior.firstObservedAt<t?prior.firstObservedAt:t,eventAnchorId:e.eventAnchorId})}}
 const seen=new Set(),all=[];
 for(const r of receipts||[]){
  if(seen.has(r.receiptId))throw Error('duplicate receipt '+r.receiptId);seen.add(r.receiptId);
  if(!['ACTIVE','SUPERSEDED','REVOKED'].includes(r.receiptStatus||'ACTIVE'))throw Error('invalid receipt status '+r.receiptId);
  if(!/^rcpt_[A-Za-z0-9_-]{8,64}$/.test(r.receiptId||'')||!fact(r.factId)||!['FUNDAMENTALS','PRICE'].includes(r.domain))throw Error('invalid receipt identity');
  if(String(r.ticker||'').normalize('NFKC').trim().toUpperCase()!==normTicker)throw Error('receipt ticker mismatch '+r.receiptId);
  if(!r.eventAnchorId||!r.consumerArtifactId||!r.consumerRevisionId||!hex(r.consumerSnapshotHash))throw Error('incomplete receipt binding '+r.receiptId);
  const t=iso(r.consumedAt,'consumedAt');if(t>cutoff)throw Error('future consumption '+r.receiptId);
  if(!facts.has(r.factId))throw Error('receipt fact not in Catalyst '+r.receiptId);
  if(r.eventAnchorId!==facts.get(r.factId).eventAnchorId)throw Error('receipt event mismatch '+r.receiptId);
  if(t<facts.get(r.factId).firstObservedAt)throw Error('consumption predates fact '+r.receiptId);
  const expected=H(stable(receiptPayload(r)));if(r.receiptHash!==expected)throw Error('receipt hash mismatch '+r.receiptId);
  all.push({...receiptPayload(r),receiptHash:r.receiptHash});
 }
 const byId=new Map(all.map(r=>[r.receiptId,r])),children=new Map();
 for(const r of all){
  if(r.parentReceiptId){
   const p=byId.get(r.parentReceiptId);if(!p)throw Error('unknown receipt parent '+r.receiptId);
   if(p.ticker!==r.ticker||p.eventAnchorId!==r.eventAnchorId||p.factId!==r.factId||p.domain!==r.domain||p.consumerArtifactId!==r.consumerArtifactId)throw Error('receipt lineage key mutation '+r.receiptId);
   if(new Date(p.consumedAt)>=new Date(r.consumedAt))throw Error('receipt lineage time rollback '+r.receiptId);
   if(!children.has(p.receiptId))children.set(p.receiptId,[]);children.get(p.receiptId).push(r.receiptId);
  }
 }
 for(const [id,kids] of children)if(kids.length>1)throw Error('receipt lineage fork '+id);
 const keys=new Map();for(const r of all){const k=[r.ticker,r.eventAnchorId,r.factId,r.domain,r.consumerArtifactId].join('|');if(!keys.has(k))keys.set(k,[]);keys.get(k).push(r)}
 const active=[];
 for(const chain of keys.values()){
  const roots=chain.filter(r=>!r.parentReceiptId);if(roots.length!==1)throw Error('receipt lineage requires one root');
  const tips=chain.filter(r=>!(children.get(r.receiptId)||[]).length);if(tips.length!==1)throw Error('receipt lineage requires one tip');
  const tip=tips[0];if(tip.receiptStatus==='ACTIVE')active.push(tip);
  for(const r of chain)if(r!==tip&&r.receiptStatus==='ACTIVE')throw Error('superseded receipt remains ACTIVE '+r.receiptId);
 }
 const byFact={};for(const r of active){if(!byFact[r.factId])byFact[r.factId]=[];byFact[r.factId].push(r)}
 const domains=[...new Set(active.map(r=>r.domain))].sort();
 return {schemaVersion:'catalyst-consumption-proof-v1',asOf:new Date(cutoff).toISOString(),sharedOriginDomains:domains,receipts:all.sort((a,b)=>a.receiptId.localeCompare(b.receiptId)),activeReceipts:active.sort((a,b)=>a.receiptId.localeCompare(b.receiptId)),byFact};
}
module.exports={resolveProvenance,verifyConsumption,receiptPayload,canonical};
