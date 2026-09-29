#!/usr/bin/env node
const crypto=require('crypto');
const H=s=>crypto.createHash('sha256').update(s).digest('hex');
const stable=o=>JSON.stringify(o,Object.keys(o).sort());
const norm=s=>String(s||'').normalize('NFKC').trim().replace(/\s+/g,' ').toUpperCase();
const opaque=(p,s,n=20)=>p+H(s).slice(0,n);
function eventKey(o){return stable({ticker:norm(o.ticker),eventType:norm(o.eventType),economicSubject:norm(o.economicSubject),anchorFacts:o.anchorFacts})}
function resolve(input){
 const asOf=new Date(input.asOf);if(Number.isNaN(+asOf))throw Error('invalid asOf');
 const refs=input.domainEvidenceRefs||{FUNDAMENTALS:[],PRICE:[]},groups=new Map();
 for(const o of input.observations||[]){
  if(new Date(o.observedAt)>asOf)continue;
  const k=eventKey(o);if(!groups.has(k))groups.set(k,[]);groups.get(k).push(o);
 }
 const events=[];
 for(const [key,obs] of groups){
  obs.sort((a,b)=>new Date(a.observedAt)-new Date(b.observedAt)||String(a.sourceLocator).localeCompare(String(b.sourceLocator)));
  const first=obs[0],eventAnchorId=opaque('evt_',key,20),factsHash=H(stable(first.anchorFacts));
  const authoritative=obs.filter(o=>['PRIMARY','CORRECTION'].includes(o.sourceClass)&&o.verificationStatus==='VERIFIED');
  const revisions=[];let lastHash=null;
  for(const o of authoritative){
   if(o.correctionOfObservationId&&!obs.some(z=>z.observationId===o.correctionOfObservationId))throw Error('cross-event/unknown correction lineage '+o.observationId);
   if(o.contentHash===lastHash)continue;
   if(revisions.length)revisions[revisions.length-1].revisionStatus='SUPERSEDED';
   const n=revisions.length+1,id=opaque('rev_',eventAnchorId+'|'+n+'|'+o.contentHash,16);
   revisions.push({revisionId:id,revisionNumber:n,parentRevisionId:n===1?null:revisions[n-2].revisionId,revisionStatus:'ACTIVE',contentHash:o.contentHash});
   lastHash=o.contentHash;
  }
  if(!revisions.length){
   const seed=H('UNRESOLVED|'+eventAnchorId);
   revisions.push({revisionId:opaque('rev_',eventAnchorId+'|1|'+seed,16),revisionNumber:1,parentRevisionId:null,revisionStatus:'ACTIVE',contentHash:seed});
  }
  const active=revisions[revisions.length-1];
  const originFactIds=[...new Set(obs.flatMap(o=>o.originFactIds||[]))].sort();
  const shared=['FUNDAMENTALS','PRICE'].filter(d=>originFactIds.some(id=>(refs[d]||[]).includes(id)));
  const observations=obs.map(o=>{
   let rev=active.revisionId;
   const idx=authoritative.findIndex(a=>a.observationId===o.observationId);
   if(idx>=0){
    const upto=authoritative.slice(0,idx+1).filter((a,i,arr)=>i===0||a.contentHash!==arr[i-1].contentHash);
    rev=revisions[Math.max(0,upto.length-1)].revisionId;
   }
   const support=['PRIMARY','CORRECTION'].includes(o.sourceClass)&&o.verificationStatus==='VERIFIED'&&rev===active.revisionId;
   return {observationId:o.observationId,revisionId:rev,sourceClass:o.sourceClass,sourceLocator:o.sourceLocator,publishedAt:o.publishedAt,observedAt:o.observedAt,verificationStatus:o.verificationStatus,evidenceStatus:support?'SUPPORT':(o.sourceClass==='RUMOR'?'REJECTED':'CONTEXT_ONLY')};
  });
  events.push({eventAnchorId,eventType:first.eventType,economicSubject:first.economicSubject,anchorFacts:first.anchorFacts,anchorFactsHash:factsHash,firstObservedAt:obs[0].observedAt,canonicalRevisionId:active.revisionId,independenceStatus:shared.length?'DEPENDENT_SHARED_ORIGIN':(authoritative.length?'INDEPENDENT_EVENT':'UNRESOLVED'),originFactIds,sharedOriginDomains:shared,relatedEventIds:[],revisions,observations});
 }
 return {schemaVersion:'catalyst-context-v1',ticker:input.ticker,asOf:input.asOf,contextStatus:events.length?'CURRENT_MATERIAL_EVIDENCE':(input.sourceAvailable===false?'SOURCE_UNAVAILABLE':'NO_MATERIAL_EVENT'),domainEvidenceRefs:{FUNDAMENTALS:[...new Set(refs.FUNDAMENTALS||[])],PRICE:[...new Set(refs.PRICE||[])]},events};
}
if(require.main===module){const fs=require('fs');const x=JSON.parse(fs.readFileSync(process.argv[2],'utf8'));process.stdout.write(JSON.stringify(resolve(x),null,2))}
module.exports={resolve,eventKey};
