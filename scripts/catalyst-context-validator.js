#!/usr/bin/env node
const fs=require('fs'),crypto=require('crypto');
const file=process.argv[2];
if(!file){console.error('usage: node scripts/catalyst-context-validator.js <artifact.json>');process.exit(2)}
const x=JSON.parse(fs.readFileSync(file,'utf8'));
const fail=m=>{throw new Error('CATALYST_CONTEXT_INVALID: '+m)};
const iso=s=>typeof s==='string'&&!Number.isNaN(Date.parse(s));
const hash=s=>crypto.createHash('sha256').update(s).digest('hex');
const stable=o=>JSON.stringify(o,Object.keys(o).sort());
const enums=(v,a,n)=>{if(!a.includes(v))fail(n+' enum')};
if(x.schemaVersion!=='catalyst-context-v1')fail('schemaVersion');
if(!/^[A-Z0-9]{1,12}(\.JK)?$/.test(x.ticker||''))fail('ticker');
if(!iso(x.asOf))fail('asOf');
enums(x.contextStatus,['CURRENT_MATERIAL_EVIDENCE','NO_MATERIAL_EVENT','SOURCE_UNAVAILABLE','STALE_EVIDENCE','NOT_EVALUATED'],'contextStatus');
if(!Array.isArray(x.events))fail('events');
if(x.contextStatus!=='CURRENT_MATERIAL_EVIDENCE'&&x.events.length)fail('non-current status cannot publish active events');
const asOf=new Date(x.asOf),events=new Map(),globalObs=new Set();
for(const e of x.events){
 const required=['eventAnchorId','eventType','economicSubject','anchorFacts','anchorFactsHash','firstObservedAt','canonicalRevisionId','independenceStatus','sharedOriginDomains','relatedEventIds','revisions','observations'];
 for(const k of required)if(!(k in e))fail('missing '+k);
 if(!/^evt_[A-Za-z0-9_-]{12,64}$/.test(e.eventAnchorId))fail('eventAnchorId');
 if(events.has(e.eventAnchorId))fail('duplicate eventAnchorId '+e.eventAnchorId);events.set(e.eventAnchorId,e);
 if(!e.anchorFacts||typeof e.anchorFacts!=='object'||Array.isArray(e.anchorFacts))fail('anchorFacts object');
 if(!/^[a-f0-9]{64}$/.test(e.anchorFactsHash)||hash(stable(e.anchorFacts))!==e.anchorFactsHash)fail('anchorFacts binding '+e.eventAnchorId);
 if(!iso(e.firstObservedAt)||new Date(e.firstObservedAt)>asOf)fail('firstObservedAt PIT '+e.eventAnchorId);
 enums(e.independenceStatus,['INDEPENDENT_EVENT','DEPENDENT_SHARED_ORIGIN','CONTEXT_ONLY','UNRESOLVED'],'independenceStatus');
 const rel=e.relatedEventIds;
 if(!Array.isArray(rel)||new Set(rel).size!==rel.length||rel.includes(e.eventAnchorId))fail('related-event identity '+e.eventAnchorId);
 const shared=e.sharedOriginDomains;
 if(!Array.isArray(shared)||new Set(shared).size!==shared.length||shared.some(d=>!['FUNDAMENTALS','PRICE'].includes(d)))fail('sharedOriginDomains');
 if(shared.length&&e.independenceStatus!=='DEPENDENT_SHARED_ORIGIN')fail('hidden shared-origin '+e.eventAnchorId);
 if(!shared.length&&e.independenceStatus==='DEPENDENT_SHARED_ORIGIN')fail('missing shared-origin domain '+e.eventAnchorId);
 const revs=[...e.revisions].sort((a,b)=>a.revisionNumber-b.revisionNumber);if(!revs.length)fail('no revisions '+e.eventAnchorId);
 const rm=new Map();
 revs.forEach((r,i)=>{
  if(!/^rev_[A-Za-z0-9_-]{8,64}$/.test(r.revisionId||''))fail('revisionId');
  if(rm.has(r.revisionId))fail('duplicate revision '+r.revisionId);rm.set(r.revisionId,r);
  if(r.revisionNumber!==i+1)fail('revision sequence '+e.eventAnchorId);
  if(i===0&&r.parentRevisionId!==null)fail('revision 1 parent');
  if(i>0&&r.parentRevisionId!==revs[i-1].revisionId)fail('exact parent binding '+r.revisionId);
  enums(r.revisionStatus,['ACTIVE','SUPERSEDED','WITHDRAWN'],'revisionStatus');
  if(!/^[a-f0-9]{64}$/.test(r.contentHash||''))fail('revision contentHash');
 });
 const active=revs.filter(r=>r.revisionStatus==='ACTIVE');if(active.length!==1)fail('one ACTIVE revision required '+e.eventAnchorId);
 const live=revs.filter(r=>r.revisionStatus!=='WITHDRAWN');if(!live.length||active[0].revisionNumber!==Math.max(...live.map(r=>r.revisionNumber)))fail('ACTIVE is not latest '+e.eventAnchorId);
 if(e.canonicalRevisionId!==active[0].revisionId)fail('canonical revision mismatch '+e.eventAnchorId);
 if(!Array.isArray(e.observations)||!e.observations.length)fail('observations');
 let minObserved=null;
 for(const o of e.observations){
  for(const k of ['observationId','revisionId','sourceClass','sourceLocator','publishedAt','observedAt','verificationStatus','evidenceStatus'])if(!(k in o))fail('observation missing '+k);
  if(!/^obs_[A-Za-z0-9_-]{8,64}$/.test(o.observationId))fail('observationId');
  if(globalObs.has(o.observationId))fail('duplicate observationId '+o.observationId);globalObs.add(o.observationId);
  if(!rm.has(o.revisionId))fail('observation revision binding '+o.observationId);
  enums(o.sourceClass,['PRIMARY','CORROBORATION','DERIVATIVE','RUMOR','CORRECTION'],'sourceClass');
  enums(o.verificationStatus,['VERIFIED','UNVERIFIED','CONFLICTING'],'verificationStatus');
  enums(o.evidenceStatus,['SUPPORT','CONTEXT_ONLY','REJECTED'],'evidenceStatus');
  if(typeof o.sourceLocator!=='string'||!o.sourceLocator.trim())fail('sourceLocator');
  if(!iso(o.publishedAt)||!iso(o.observedAt))fail('observation timestamp '+o.observationId);
  const pub=new Date(o.publishedAt),obs=new Date(o.observedAt);
  if(obs<pub)fail('observedAt before publishedAt '+o.observationId);
  if(obs>asOf)fail('future observation vs asOf '+o.observationId);
  if(minObserved===null||obs<minObserved)minObserved=obs;
  if(o.evidenceStatus==='SUPPORT'&&o.verificationStatus!=='VERIFIED')fail('SUPPORT requires VERIFIED '+o.observationId);
  if(o.evidenceStatus==='SUPPORT'&&['RUMOR','DERIVATIVE'].includes(o.sourceClass))fail('rumor/derivative SUPPORT laundering '+o.observationId);
  if(o.evidenceStatus==='SUPPORT'&&rm.get(o.revisionId).revisionStatus!=='ACTIVE')fail('superseded SUPPORT '+o.observationId);
 }
 if(!minObserved||new Date(e.firstObservedAt).getTime()!==minObserved.getTime())fail('firstObservedAt binding '+e.eventAnchorId);
}
for(const e of x.events)for(const id of e.relatedEventIds)if(!events.has(id))fail('unknown related event '+id);
const visiting=new Set(),done=new Set();function dfs(id){if(visiting.has(id))fail('related-event cycle '+id);if(done.has(id))return;visiting.add(id);for(const n of events.get(id).relatedEventIds)dfs(n);visiting.delete(id);done.add(id)}for(const id of events.keys())dfs(id);
console.log('CATALYST_CONTEXT_VALID',x.ticker,x.events.length);
