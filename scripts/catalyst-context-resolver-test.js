#!/usr/bin/env node
const {resolve,eventKey}=require('./catalyst-context-resolver');
const cp=require('child_process'),fs=require('fs'),os=require('os'),path=require('path'),crypto=require('crypto');
const H=s=>crypto.createHash('sha256').update(s).digest('hex'),A=(v,m)=>{if(!v)throw Error(m)};
const obs=(id,source,loc,hash,extra={})=>({observationId:id,ticker:'TEST.JK',eventType:'EARNINGS',economicSubject:'Q2 earnings',anchorFacts:{issuer:'TEST.JK',period:'2026Q2',subject:'earnings'},originFactIds:['fact_earnings001'],sourceClass:source,sourceLocator:loc,publishedAt:'2026-09-01T00:00:00Z',observedAt:'2026-09-01T01:00:00Z',verificationStatus:source==='RUMOR'?'UNVERIFIED':'VERIFIED',contentHash:hash,...extra});
const input=o=>({ticker:'TEST.JK',asOf:'2026-09-30T00:00:00Z',sourceAvailable:true,domainEvidenceRefs:{FUNDAMENTALS:[],PRICE:[]},observations:o});
function valid(x){const p=path.join(os.tmpdir(),'resolved-'+process.pid+'.json');fs.writeFileSync(p,JSON.stringify(x));const r=cp.spawnSync(process.execPath,['scripts/catalyst-context-validator.js',p]);fs.unlinkSync(p);return r.status===0}
const rejects=(fn,m)=>{let y=false;try{fn()}catch(e){y=true}A(y,m)};
let p=obs('obs_primary001','PRIMARY','issuer://1',H('v1')),d=obs('obs_media0001','DERIVATIVE','media://mirror',H('mirror'));
let x=resolve(input([p,d]));A(x.events.length===1,'syndication split');A(x.events[0].revisions.length===1,'derivative revision');A(valid(x),'baseline contract');
let rev=resolve(input([d,p]));A(JSON.stringify(x)===JSON.stringify(rev),'observation-order nondeterminism');
const a=obs('obs_anchor0001','PRIMARY','issuer://a',H('v1'),{anchorFacts:{issuer:'TEST.JK',nested:{b:2,a:1},period:'2026Q2',subject:'earnings'}});
const b=obs('obs_anchor0002','PRIMARY','issuer://b',H('v1'),{anchorFacts:{subject:'earnings',period:'2026Q2',nested:{a:1,b:2},issuer:'TEST.JK'}});
A(eventKey(a)===eventKey(b),'recursive anchor canonicalization failed');
let c=obs('obs_correct001','CORRECTION','issuer://2',H('v2'),{observedAt:'2026-09-02T01:00:00Z',publishedAt:'2026-09-02T00:00:00Z',correctionOfObservationId:'obs_primary001'});
x=resolve(input([p,c]));A(x.events[0].revisions.length===2,'correction missing');A(x.events[0].revisions[0].revisionStatus==='SUPERSEDED','not superseded');A(valid(x),'revision contract');
let future=obs('obs_future0001','CORRECTION','issuer://future',H('v2'),{publishedAt:'2026-10-01T00:00:00Z',observedAt:'2026-10-01T01:00:00Z',correctionOfObservationId:'obs_primary001'});
x=resolve(input([p,future]));A(x.events[0].revisions.length===1,'future PIT leak');
x=resolve(input([obs('obs_rumor0001','RUMOR','social://1',H('rumor'))]));A(x.events[0].independenceStatus==='UNRESOLVED','rumor independent');A(valid(x),'unresolved contract');
let i=input([p]);i.domainEvidenceRefs.FUNDAMENTALS=['fact_earnings001'];x=resolve(i);A(x.events[0].independenceStatus==='DEPENDENT_SHARED_ORIGIN','fundamentals origin');A(valid(x),'fundamentals contract');
i=input([p]);i.domainEvidenceRefs.PRICE=['fact_earnings001'];x=resolve(i);A(x.events[0].sharedOriginDomains[0]==='PRICE','price origin');
let fork=obs('obs_primary002','PRIMARY','issuer://other',H('different'),{observedAt:'2026-09-02T01:00:00Z',publishedAt:'2026-09-02T00:00:00Z'});
rejects(()=>resolve(input([p,fork])),'conflicting PRIMARY silently revised');
let badCorrection={...c,correctionOfObservationId:'obs_other0001'};rejects(()=>resolve(input([p,badCorrection])),'cross-event correction accepted');
let branch=obs('obs_correct002','CORRECTION','issuer://3',H('v3'),{observedAt:'2026-09-03T01:00:00Z',publishedAt:'2026-09-03T00:00:00Z',correctionOfObservationId:'obs_primary001'});rejects(()=>resolve(input([p,c,branch])),'correction fork accepted');
rejects(()=>resolve(input([{...p,observedAt:'bad-time'}])),'invalid timestamp accepted');
rejects(()=>resolve(input([p,{...p}])),'duplicate observation replay accepted');
console.log('CATALYST_CONTEXT_RESOLVER_TEST_PASS');
