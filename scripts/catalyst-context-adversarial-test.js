#!/usr/bin/env node
const fs=require('fs'),os=require('os'),path=require('path'),cp=require('child_process'),crypto=require('crypto');
const H=s=>crypto.createHash('sha256').update(s).digest('hex');
const base=()=>({schemaVersion:'catalyst-context-v1',ticker:'TEST.JK',asOf:'2026-09-30T00:00:00Z',contextStatus:'CURRENT_MATERIAL_EVIDENCE',events:[{eventAnchorId:'evt_123456789abc',eventType:'EARNINGS',economicSubject:'Q2 earnings',anchorFactsHash:H('anchor'),firstObservedAt:'2026-09-01T01:00:00Z',canonicalRevisionId:'rev_00000001',independenceStatus:'INDEPENDENT_EVENT',sharedOriginDomains:[],relatedEventIds:[],revisions:[{revisionId:'rev_00000001',revisionNumber:1,parentRevisionId:null,revisionStatus:'ACTIVE',contentHash:H('r1')}],observations:[{observationId:'obs_00000001',revisionId:'rev_00000001',sourceClass:'PRIMARY',sourceLocator:'issuer://disclosure/1',publishedAt:'2026-09-01T00:00:00Z',observedAt:'2026-09-01T01:00:00Z',verificationStatus:'VERIFIED',evidenceStatus:'SUPPORT'}]}]});
function valid(x){const p=path.join(os.tmpdir(),'catalyst-'+process.pid+'-'+Math.random()+'.json');fs.writeFileSync(p,JSON.stringify(x));const r=cp.spawnSync(process.execPath,['scripts/catalyst-context-validator.js',p]);fs.unlinkSync(p);return r.status===0}
if(!valid(base()))throw Error('baseline rejected');
const attacks=[];let x;
x=base();x.events[0].observations[0].sourceClass='RUMOR';attacks.push(['rumor SUPPORT laundering',x]);
x=base();x.events[0].observations[0].sourceClass='DERIVATIVE';attacks.push(['syndication SUPPORT laundering',x]);
x=base();x.events[0].sharedOriginDomains=['FUNDAMENTALS'];attacks.push(['hidden shared-origin independence',x]);
x=base();x.events[0].revisions[0].revisionStatus='SUPERSEDED';x.events[0].revisions.push({revisionId:'rev_00000002',revisionNumber:2,parentRevisionId:'rev_WRONG000',revisionStatus:'ACTIVE',contentHash:H('r2')});x.events[0].canonicalRevisionId='rev_00000002';attacks.push(['exact parent revision spoof',x]);
x=base();x.events[0].relatedEventIds=['evt_123456789abc'];attacks.push(['related-event self cycle',x]);
x=base();x.events[0].observations[0].verificationStatus='UNVERIFIED';attacks.push(['unverified SUPPORT',x]);
x=base();x.events[0].revisions[0].revisionStatus='SUPERSEDED';attacks.push(['superseded revision SUPPORT',x]);
for(const [name,a] of attacks){if(valid(a))throw Error('FALSE PASS: '+name);console.log('REJECTED',name)}
console.log('CATALYST_CONTEXT_ADVERSARIAL_PASS',attacks.length);
