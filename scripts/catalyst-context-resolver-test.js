#!/usr/bin/env node
const {resolve}=require('./catalyst-context-resolver');
const cp=require('child_process'),fs=require('fs'),os=require('os'),path=require('path'),crypto=require('crypto');
const H=s=>crypto.createHash('sha256').update(s).digest('hex');
const obs=(id,source,loc,hash,extra={})=>({observationId:id,ticker:'TEST.JK',eventType:'EARNINGS',economicSubject:'Q2 earnings',anchorFacts:{issuer:'TEST.JK',period:'2026Q2',subject:'earnings'},originFactIds:['fact_earnings001'],sourceClass:source,sourceLocator:loc,publishedAt:'2026-09-01T00:00:00Z',observedAt:'2026-09-01T01:00:00Z',verificationStatus:source==='RUMOR'?'UNVERIFIED':'VERIFIED',contentHash:hash,...extra});
const input=(observations)=>({ticker:'TEST.JK',asOf:'2026-09-30T00:00:00Z',sourceAvailable:true,domainEvidenceRefs:{FUNDAMENTALS:[],PRICE:[]},observations});
const assert=(v,m)=>{if(!v)throw Error(m)};
function contractValid(x){const p=path.join(os.tmpdir(),'resolved-'+process.pid+'.json');fs.writeFileSync(p,JSON.stringify(x));const r=cp.spawnSync(process.execPath,['scripts/catalyst-context-validator.js',p]);fs.unlinkSync(p);return r.status===0}
let x=resolve(input([obs('obs_primary001','PRIMARY','issuer://1',H('v1')),obs('obs_media0001','DERIVATIVE','media://mirror',H('mirror'))]));
assert(x.events.length===1,'syndication split event');assert(x.events[0].revisions.length===1,'derivative created revision');assert(contractValid(x),'baseline output violates frozen contract');
x=resolve(input([obs('obs_primary001','PRIMARY','issuer://1',H('v1')),obs('obs_correct001','CORRECTION','issuer://2',H('v2'),{observedAt:'2026-09-02T01:00:00Z',publishedAt:'2026-09-02T00:00:00Z',correctionOfObservationId:'obs_primary001'})]));
assert(x.events[0].revisions.length===2,'correction revision missing');assert(x.events[0].revisions[0].revisionStatus==='SUPERSEDED','parent not superseded');assert(contractValid(x),'revision output invalid');
x=resolve(input([obs('obs_primary001','PRIMARY','issuer://1',H('v1')),obs('obs_future0001','CORRECTION','issuer://future',H('v2'),{publishedAt:'2026-10-01T00:00:00Z',observedAt:'2026-10-01T01:00:00Z'})]));
assert(x.events[0].revisions.length===1,'future evidence leaked into PIT');
x=resolve(input([obs('obs_rumor0001','RUMOR','social://1',H('rumor'))]));assert(x.events[0].independenceStatus==='UNRESOLVED','rumor became independent');assert(x.events[0].observations[0].evidenceStatus==='REJECTED','rumor became support');assert(contractValid(x),'unresolved output invalid');
let i=input([obs('obs_primary001','PRIMARY','issuer://1',H('v1'))]);i.domainEvidenceRefs.FUNDAMENTALS=['fact_earnings001'];x=resolve(i);assert(x.events[0].independenceStatus==='DEPENDENT_SHARED_ORIGIN','fundamentals shared origin missed');assert(contractValid(x),'fundamentals adapter invalid');
i=input([obs('obs_primary001','PRIMARY','issuer://1',H('v1'))]);i.domainEvidenceRefs.PRICE=['fact_earnings001'];x=resolve(i);assert(x.events[0].sharedOriginDomains[0]==='PRICE','price shared origin missed');
let threw=false;try{resolve(input([obs('obs_correct001','CORRECTION','issuer://2',H('v2'),{correctionOfObservationId:'obs_other0001'})]))}catch(e){threw=true}assert(threw,'unknown correction lineage accepted');
console.log('CATALYST_CONTEXT_RESOLVER_TEST_PASS');
