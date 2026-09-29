const fs=require('fs'),path=require('path'),os=require('os'),cp=require('child_process');
const REPO=path.resolve(__dirname,'..'), gate=path.join(REPO,'scripts/scanner-publication-gate.js');
const base=fs.mkdtempSync(path.join(os.tmpdir(),'scanner-adversarial-'));
const clone=o=>JSON.parse(JSON.stringify(o));
const canonicalSummary=JSON.parse(fs.readFileSync(path.join(REPO,'data/summary.json'),'utf8'));
const registry=JSON.parse(fs.readFileSync(path.join(REPO,'data/scanner/reason-registry.json'),'utf8'));
const schemaS=JSON.parse(fs.readFileSync(path.join(REPO,'contracts/scanner-summary-v1.schema.json'),'utf8'));
const schemaT=JSON.parse(fs.readFileSync(path.join(REPO,'contracts/scanner-ticker-v1.schema.json'),'utf8'));
const canon=canonicalSummary.stocks.find(x=>x.ticker==='AADI');
const fv=JSON.parse(fs.readFileSync(path.join(REPO,'data/AADI.json'),'utf8'));
const today='2026-09-29', evaluated=today+'T03:00:00Z';
function valid(){
 const t={schemaVersion:'scanner-ticker-v1',ticker:'AADI',name:canon.name,sector:canon.sector,industry:fv.companyProfile.industry,
 des:{eligible:true,universe:canonicalSummary.universeSource,asOf:'2026-05-21'},
 scanner:{state:'WATCHLIST',stateLabel:'Daftar Pantau',stateChangedDate:today},
 researchLens:['UNDERVALUED'],evidenceStrength:{overall:'ADEQUATE',quality:'MIXED',valuation:'SUPPORTIVE',price:'MIXED',catalyst:'NOT_AVAILABLE'},
 whyWatching:[{code:'VALUATION_OPPORTUNITY',text:registry.whyWatching.VALUATION_OPPORTUNITY}],whatToVerify:[{code:'PRICE_CONFIRMATION_PENDING',text:registry.whatToVerify.PRICE_CONFIRMATION_PENDING}],
 freshness:{overall:'CURRENT',valuation:'CURRENT',fundamentals:'CURRENT',price:'CURRENT',catalyst:'SOURCE_UNAVAILABLE',lastEvaluatedAt:evaluated},
 valuationContext:{status:canon.status,evidence:'ADEQUATE'},provenance:{valuation:'CANONICAL_FAIR_VALUE',price:'MARKET_DATA',des:'OJK_DES',catalyst:'PUBLIC_MATERIAL_EVENTS'},
 actions:{primary:{type:'FAIR_VALUE',label:'Cek Fair Value',url:'/fair-value/?ticker=AADI'},secondary:{type:'QSTP',label:'Buka QSTP',url:'/qstp.html?ticker=AADI'}},
 stateHistory:[{state:'WATCHLIST',date:today,reason:'VALUATION_OPPORTUNITY'}]};
 const s={schemaVersion:'scanner-summary-v1',generationStatus:'GENERATED',generatedAt:evaluated,universe:{name:canonicalSummary.universeSource,eligible:canonicalSummary.requested,evaluated:1},watchlist:{count:1,states:{WATCHLIST:1,RESEARCH_CONFIRMED:0,WAITING_CONFIRMATION:0,EXTENDED:0,LIMITED_EVIDENCE:0}},items:[{ticker:'AADI',name:t.name,sector:t.sector,state:'WATCHLIST',stateLabel:'Daftar Pantau',researchLens:['UNDERVALUED'],evidenceStrength:'ADEQUATE',primaryReason:'VALUATION_OPPORTUNITY',freshness:'CURRENT',detail:'/scanner/AADI.json',fairValue:'/fair-value/?ticker=AADI'}]};
 return {s,t,r:clone(registry)};
}
function materialize(name,mutate){
 const root=path.join(base,name);fs.mkdirSync(path.join(root,'data/scanner/tickers'),{recursive:true});fs.mkdirSync(path.join(root,'contracts'),{recursive:true});fs.mkdirSync(path.join(root,'scripts'),{recursive:true});
 const x=valid(); if(mutate)mutate(x,root);
 fs.writeFileSync(path.join(root,'data/summary.json'),JSON.stringify(canonicalSummary));fs.writeFileSync(path.join(root,'data/AADI.json'),JSON.stringify(fv));fs.writeFileSync(path.join(root,'data/scanner/summary.json'),JSON.stringify(x.s));fs.writeFileSync(path.join(root,'data/scanner/reason-registry.json'),JSON.stringify(x.r));fs.writeFileSync(path.join(root,'data/scanner/tickers/AADI.json'),JSON.stringify(x.t));
 fs.writeFileSync(path.join(root,'contracts/scanner-summary-v1.schema.json'),JSON.stringify(schemaS));fs.writeFileSync(path.join(root,'contracts/scanner-ticker-v1.schema.json'),JSON.stringify(schemaT));
 return root;
}
function run(name,mutate,shouldPass=false){
 const root=materialize(name,mutate);let ok=true;
 try{cp.execFileSync(process.execPath,[gate],{stdio:'pipe',env:{...process.env,SCANNER_PUBLICATION_ROOT:root}})}catch(e){ok=false}
 if(ok!==shouldPass)throw new Error(name+' expected '+(shouldPass?'PASS':'FAIL')+' but '+(ok?'PASSED':'FAILED'));
 console.log((shouldPass?'PASS ':'BLOCK ')+name);
}
run('valid-generated',null,true);
run('score-leak',x=>x.t.internalScore=0.91);
run('registry-leak',x=>{x.r.whyWatching.VALUATION_OPPORTUNITY='Valuasi lolos threshold > 24%';x.t.whyWatching[0].text=x.r.whyWatching.VALUATION_OPPORTUNITY});
run('orphan',(_x,root)=>fs.writeFileSync(path.join(root,'data/scanner/tickers/ZZZZ.json'),'{}'));
run('missing',x=>x.s.items[0].ticker='AALI');
run('parity-mismatch',x=>x.s.items[0].evidenceStrength='STRONG');
run('fake-des',x=>{x.t.des.universe='FAKE DES'});
run('fake-fv-identity',x=>{x.t.name='Private Alias';x.s.items[0].name='Private Alias'});
run('history-future',x=>{x.t.stateHistory[0].date='2026-09-30';x.t.scanner.stateChangedDate='2026-09-30'});
run('history-state-mismatch',x=>{x.t.stateHistory[0].state='EXTENDED'});
run('path-trick',(_x,root)=>fs.writeFileSync(path.join(root,'data/scanner/tickers/private-score.txt'),'secret'));
run('action-label-mismatch',x=>{x.t.actions.primary.label='Buka QSTP'});
run('action-url-mismatch',x=>{x.t.actions.primary.url='/fair-value/?ticker=ZZZZ'});
run('registry-key-drift',x=>{delete x.r.whyWatching.QUALITY_SUPPORT});
run('uncontrolled-reason-copy',x=>{x.t.whyWatching[0].text='Copy bebas yang tidak berasal dari registry'});
run('history-adjacent-duplicate',x=>{x.t.stateHistory=[{state:'WATCHLIST',date:'2026-09-28',reason:'VALUATION_OPPORTUNITY'},{state:'WATCHLIST',date:today,reason:'VALUATION_OPPORTUNITY'}]});
run('history-chronology-reversed',x=>{x.t.stateHistory=[{state:'WAITING_CONFIRMATION',date:today,reason:'PRICE_CONFIRMATION_PENDING'},{state:'WATCHLIST',date:'2026-09-28',reason:'VALUATION_OPPORTUNITY'}];x.t.scanner.state='WATCHLIST';x.t.scanner.stateLabel='Daftar Pantau';x.t.scanner.stateChangedDate='2026-09-28';x.s.items[0].state='WATCHLIST';x.s.items[0].stateLabel='Daftar Pantau'});
run('filename-ticker-mismatch',x=>{x.t.ticker='AALI'});
console.log('SCANNER_ADVERSARIAL_SUITE_PASS');
