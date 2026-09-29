#!/usr/bin/env node
const fs=require('fs');
const file=process.argv[2];
if(!file){console.error('usage: node scripts/catalyst-context-validator.js <artifact.json>');process.exit(2)}
const x=JSON.parse(fs.readFileSync(file,'utf8'));
const fail=m=>{throw new Error('CATALYST_CONTEXT_INVALID: '+m)};
if(x.schemaVersion!=='catalyst-context-v1')fail('schemaVersion');
if(!Array.isArray(x.events))fail('events');
const events=new Map();
for(const e of x.events){
 if(!/^evt_[A-Za-z0-9_-]{12,64}$/.test(e.eventAnchorId||''))fail('eventAnchorId');
 if(events.has(e.eventAnchorId))fail('duplicate eventAnchorId '+e.eventAnchorId);
 events.set(e.eventAnchorId,e);
 if(!/^[a-f0-9]{64}$/.test(e.anchorFactsHash||''))fail('anchorFactsHash '+e.eventAnchorId);
 const rel=e.relatedEventIds||[];
 if(new Set(rel).size!==rel.length||rel.includes(e.eventAnchorId))fail('related-event identity '+e.eventAnchorId);
 const shared=e.sharedOriginDomains||[];
 if(new Set(shared).size!==shared.length||shared.some(d=>!['FUNDAMENTALS','PRICE'].includes(d)))fail('sharedOriginDomains');
 if(shared.length&&e.independenceStatus!=='DEPENDENT_SHARED_ORIGIN')fail('hidden shared-origin '+e.eventAnchorId);
 if(!shared.length&&e.independenceStatus==='DEPENDENT_SHARED_ORIGIN')fail('missing shared-origin domain '+e.eventAnchorId);
 const revs=[...(e.revisions||[])].sort((a,b)=>a.revisionNumber-b.revisionNumber);
 if(!revs.length)fail('no revisions '+e.eventAnchorId);
 const rm=new Map();
 revs.forEach((r,i)=>{
  if(rm.has(r.revisionId))fail('duplicate revision '+r.revisionId);rm.set(r.revisionId,r);
  if(r.revisionNumber!==i+1)fail('revision sequence '+e.eventAnchorId);
  if(i===0&&r.parentRevisionId!==null)fail('revision 1 parent');
  if(i>0&&r.parentRevisionId!==revs[i-1].revisionId)fail('exact parent binding '+r.revisionId);
 });
 const active=revs.filter(r=>r.revisionStatus==='ACTIVE');
 if(active.length!==1)fail('one ACTIVE revision required '+e.eventAnchorId);
 const live=revs.filter(r=>r.revisionStatus!=='WITHDRAWN');
 if(!live.length||active[0].revisionNumber!==Math.max(...live.map(r=>r.revisionNumber)))fail('ACTIVE is not latest '+e.eventAnchorId);
 if(e.canonicalRevisionId!==active[0].revisionId)fail('canonical revision mismatch '+e.eventAnchorId);
 for(const o of e.observations||[]){
  if(!rm.has(o.revisionId))fail('observation revision binding '+o.observationId);
  if(new Date(o.observedAt)<new Date(o.publishedAt))fail('PIT observedAt '+o.observationId);
  if(o.evidenceStatus==='SUPPORT'&&o.verificationStatus!=='VERIFIED')fail('SUPPORT requires VERIFIED '+o.observationId);
  if(o.evidenceStatus==='SUPPORT'&&['RUMOR','DERIVATIVE'].includes(o.sourceClass))fail('rumor/derivative SUPPORT laundering '+o.observationId);
  if(o.evidenceStatus==='SUPPORT'&&rm.get(o.revisionId).revisionStatus!=='ACTIVE')fail('superseded SUPPORT '+o.observationId);
 }
}
for(const e of x.events)for(const id of e.relatedEventIds||[])if(!events.has(id))fail('unknown related event '+id);
const visiting=new Set(),done=new Set();
function dfs(id){if(visiting.has(id))fail('related-event cycle '+id);if(done.has(id))return;visiting.add(id);for(const n of events.get(id).relatedEventIds||[])dfs(n);visiting.delete(id);done.add(id)}
for(const id of events.keys())dfs(id);
if(x.contextStatus==='NO_MATERIAL_EVENT'&&x.events.length)fail('NO_MATERIAL_EVENT cannot contain events');
console.log('CATALYST_CONTEXT_VALID',x.ticker,x.events.length);
