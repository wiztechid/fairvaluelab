#!/usr/bin/env node
const crypto=require('crypto');
const H=s=>crypto.createHash('sha256').update(s).digest('hex');
function canonical(v){if(Array.isArray(v))return v.map(canonical);if(v&&typeof v==='object')return Object.keys(v).sort().reduce((o,k)=>(o[k]=canonical(v[k]),o),{});return v}
const stable=o=>JSON.stringify(canonical(o));
const norm=s=>String(s||'').normalize('NFKC').trim().replace(/\s+/g,' ').toUpperCase();
const opaque=(p,s,n=20)=>p+H(s).slice(0,n);
const time=(s,n)=>{const d=new Date(s);if(Number.isNaN(+d))throw Error('invalid '+n);return d};
function normValue(v){if(typeof v==='string')return v.normalize('NFKC').trim().replace(/\\s+/g,' ');if(Array.isArray(v))return v.map(normValue);if(v&&typeof v==='object')return Object.keys(v).sort().reduce((o,k)=>(o[k.normalize('NFKC').trim()]=normValue(v[k]),o),{});return v}\nfunction eventKey(o){return stable({ticker:norm(o.ticker),eventType:norm(o.eventType),economicSubject:norm(o.economicSubject),anchorFacts:normValue(o.anchorFacts)})}
function resolve(input){
 const asOf=time(input.asOf,'asOf'),refs=input.domainEvidenceRefs||{FUNDAMENTALS:[],PRICE:[]},groups=new Map(),ids=new Set();\n for(const d of ['FUNDAMENTALS','PRICE'])for(const id of refs[d]||[])if(typeof id!=='string'||!/^fact_[A-Za-z0-9_-]{8,64}$/.test(id))throw Error('invalid domain fact id '+d);
 for(const o of input.observations||[]){\n  if(norm(o.ticker)!==norm(input.ticker))throw Error('observation ticker mismatch '+o.observationId);\n  if(!Array.isArray(o.originFactIds)||!o.originFactIds.length||o.originFactIds.some(id=>typeof id!=='string'||!/^fact_[A-Za-z0-9_-]{8,64}$/.test(id)))throw Error('invalid originFactIds '+o.observationId);
  if(ids.has(o.observationId))throw Error('duplicate observationId '+o.observationId);ids.add(o.observationId);
  const pub=time(o.publishedAt,'publishedAt'),seen=time(o.observedAt,'observedAt');if(seen<pub)throw Error('observedAt before publishedAt '+o.observationId);if(seen>asOf)continue;
  const k=eventKey(o);if(!groups.has(k))groups.set(k,[]);groups.get(k).push(o);
 }
 const events=[];
 for(const [key,raw] of [...groups.entries()].sort((a,b)=>a[0].localeCompare(b[0]))){
  const obs=[...raw].sort((a,b)=>+time(a.observedAt,'observedAt')-+time(b.observedAt,'observedAt')||String(a.observationId).localeCompare(String(b.observationId)));
  const first=obs[0],eventAnchorId=opaque('evt_',key,20),facts=normValue(first.anchorFacts),factsHash=H(stable(facts));
  const authoritative=obs.filter(o=>['PRIMARY','CORRECTION'].includes(o.sourceClass)&&o.verificationStatus==='VERIFIED');
  const revisions=[],obsRevision=new Map();let lastAuth=null;
  for(const o of authoritative){
   if(!lastAuth){
    if(o.sourceClass==='CORRECTION'&&o.correctionOfObservationId)throw Error('correction without authoritative parent '+o.observationId);
   }else if(o.contentHash!==lastAuth.contentHash){
    if(o.sourceClass!=='CORRECTION'||o.correctionOfObservationId!==lastAuth.observationId)throw Error('authoritative fork requires exact correction lineage '+o.observationId);
   }else if(o.sourceClass==='CORRECTION'&&o.correctionOfObservationId!==lastAuth.observationId)throw Error('duplicate-content correction parent mismatch '+o.observationId);
   if(o.correctionOfObservationId&&!obs.some(z=>z.observationId===o.correctionOfObservationId))throw Error('cross-event/unknown correction lineage '+o.observationId);
   if(!lastAuth||o.contentHash!==lastAuth.contentHash){
    if(revisions.length)revisions[revisions.length-1].revisionStatus='SUPERSEDED';
    const n=revisions.length+1,id=opaque('rev_',eventAnchorId+'|'+n+'|'+o.contentHash,16);
    revisions.push({revisionId:id,revisionNumber:n,parentRevisionId:n===1?null:revisions[n-2].revisionId,revisionStatus:'ACTIVE',contentHash:o.contentHash});
   }
   obsRevision.set(o.observationId,revisions[revisions.length-1].revisionId);lastAuth=o;
  }
  if(!revisions.length){const seed=H('UNRESOLVED|'+eventAnchorId);revisions.push({revisionId:opaque('rev_',eventAnchorId+'|1|'+seed,16),revisionNumber:1,parentRevisionId:null,revisionStatus:'ACTIVE',contentHash:seed})}
  const active=revisions[revisions.length-1],originFactIds=[...new Set(obs.flatMap(o=>o.originFactIds||[]))].sort();
  const shared=['FUNDAMENTALS','PRICE'].filter(d=>originFactIds.some(id=>(refs[d]||[]).includes(id)));
  const observations=obs.map(o=>{const rev=obsRevision.get(o.observationId)||active.revisionId;const support=['PRIMARY','CORRECTION'].includes(o.sourceClass)&&o.verificationStatus==='VERIFIED'&&rev===active.revisionId;return {observationId:o.observationId,revisionId:rev,sourceClass:o.sourceClass,sourceLocator:o.sourceLocator,publishedAt:o.publishedAt,observedAt:o.observedAt,verificationStatus:o.verificationStatus,evidenceStatus:support?'SUPPORT':(o.sourceClass==='RUMOR'?'REJECTED':'CONTEXT_ONLY')}});
  events.push({eventAnchorId,eventType:norm(first.eventType),economicSubject:norm(first.economicSubject),anchorFacts:facts,anchorFactsHash:factsHash,firstObservedAt:new Date(Math.min(...obs.map(o=>+time(o.observedAt,'observedAt')))).toISOString(),canonicalRevisionId:active.revisionId,independenceStatus:shared.length?'DEPENDENT_SHARED_ORIGIN':(authoritative.length?'INDEPENDENT_EVENT':'UNRESOLVED'),originFactIds,sharedOriginDomains:shared,relatedEventIds:[],revisions,observations});
 }
 return {schemaVersion:'catalyst-context-v1',ticker:norm(input.ticker),asOf:new Date(asOf).toISOString(),contextStatus:events.length?'CURRENT_MATERIAL_EVIDENCE':(input.sourceAvailable===false?'SOURCE_UNAVAILABLE':'NO_MATERIAL_EVENT'),domainEvidenceRefs:{FUNDAMENTALS:[...new Set(refs.FUNDAMENTALS||[])].sort(),PRICE:[...new Set(refs.PRICE||[])].sort()},events};
}
if(require.main===module){const fs=require('fs');const x=JSON.parse(fs.readFileSync(process.argv[2],'utf8'));process.stdout.write(JSON.stringify(resolve(x),null,2))}
module.exports={resolve,eventKey,canonical,normValue};
