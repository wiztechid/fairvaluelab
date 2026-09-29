#!/usr/bin/env node
const fs=require('fs'),os=require('os'),path=require('path'),cp=require('child_process'),crypto=require('crypto');
const H=s=>crypto.createHash('sha256').update(s).digest('hex'), stable=o=>JSON.stringify(o,Object.keys(o).sort());
const base=()=>{const facts={period:'2026Q2',issuer:'TEST.JK',subject:'earnings'};return {schemaVersion:'catalyst-context-v1',ticker:'TEST.JK',asOf:'2026-09-30T00:00:00Z',contextStatus:'CURRENT_MATERIAL_EVIDENCE',domainEvidenceRefs:{FUNDAMENTALS:[],PRICE:[]},events:[{eventAnchorId:'evt_123456789abc',eventType:'EARNINGS',economicSubject:'Q2 earnings',anchorFacts:facts,anchorFactsHash:H(stable(facts)),firstObservedAt:'2026-09-01T01:00:00Z',canonicalRevisionId:'rev_00000001',independenceStatus:'INDEPENDENT_EVENT',originFactIds:['fact_earnings001'],sharedOriginDomains:[],relatedEventIds:[],revisions:[{revisionId:'rev_00000001',revisionNumber:1,parentRevisionId:null,revisionStatus:'ACTIVE',contentHash:H('r1')}],observations:[{observationId:'obs_00000001',revisionId:'rev_00000001',sourceClass:'PRIMARY',sourceLocator:'issuer://disclosure/1',publishedAt:'2026-09-01T00:00:00Z',observedAt:'2026-09-01T01:00:00Z',verificationStatus:'VERIFIED',evidenceStatus:'SUPPORT'}]}]}}
function valid(x){const p=path.join(os.tmpdir(),'catalyst-'+process.pid+'-'+Math.random()+'.json');fs.writeFileSync(p,JSON.stringify(x));const r=cp.spawnSync(process.execPath,['scripts/catalyst-context-validator.js',p]);fs.unlinkSync(p);return r.status===0}
if(!valid(base()))throw Error('baseline rejected');
const attacks=[],add=(n,x)=>attacks.push([n,x]);let x;
x=base();x.events[0].observations[0].sourceClass='RUMOR';add('rumor SUPPORT laundering',x);
x=base();x.events[0].observations[0].sourceClass='DERIVATIVE';add('syndication SUPPORT laundering',x);
x=base();x.domainEvidenceRefs.FUNDAMENTALS=['fact_earnings001'];add('automatic hidden shared-origin independence',x);
x=base();x.events[0].sharedOriginDomains=['FUNDAMENTALS'];add('spoofed shared-origin declaration',x);
x=base();x.events[0].revisions[0].revisionStatus='SUPERSEDED';x.events[0].revisions.push({revisionId:'rev_00000002',revisionNumber:2,parentRevisionId:'rev_WRONG000',revisionStatus:'ACTIVE',contentHash:H('r2')});x.events[0].canonicalRevisionId='rev_00000002';add('exact parent revision spoof',x);
x=base();x.events[0].relatedEventIds=['evt_123456789abc'];add('related-event self cycle',x);
x=base();x.events[0].observations[0].verificationStatus='UNVERIFIED';add('unverified SUPPORT',x);
x=base();x.events[0].revisions[0].revisionStatus='SUPERSEDED';add('superseded revision SUPPORT',x);
x=base();x.events[0].anchorFacts.subject='dividend';add('canonical thesis mutation without rehash',x);
x=base();x.events[0].observations[0].sourceClass='FAKE_PRIMARY';add('source-class alias',x);
x=base();x.events[0].observations.push({...x.events[0].observations[0]});add('duplicate observation identity',x);
x=base();x.events[0].observations[0].observedAt='2026-10-01T00:00:00Z';x.events[0].firstObservedAt='2026-10-01T00:00:00Z';add('future PIT observation',x);
x=base();x.events[0].firstObservedAt='2026-09-02T00:00:00Z';add('firstObservedAt spoof',x);
x=base();x.contextStatus='NO_MATERIAL_EVENT';add('missingness with hidden events',x);
x=base();x.events[0].revisions[0].contentHash='not-a-hash';add('revision hash alias',x);
x=base();x.events.push(JSON.parse(JSON.stringify(x.events[0])));add('eventAnchorId collision',x);
x=base();x.events[0].observations[0].sourceLocator='';add('source completeness',x);
x=base();x.domainEvidenceRefs.PRICE=['fact_earnings001'];add('automatic PRICE shared-origin independence',x);
x=base();const e2=JSON.parse(JSON.stringify(x.events[0]));e2.eventAnchorId='evt_abcdef123456';e2.relatedEventIds=['evt_123456789abc'];e2.observations[0].observationId='obs_00000002';x.events[0].relatedEventIds=['evt_abcdef123456'];x.events.push(e2);add('multi-event related cycle',x);
for(const [name,a] of attacks){if(valid(a))throw Error('FALSE PASS: '+name);console.log('REJECTED',name)}
console.log('CATALYST_CONTEXT_ADVERSARIAL_PASS',attacks.length);
