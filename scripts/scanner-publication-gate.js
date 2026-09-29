const fs=require('fs'),path=require('path'),cp=require('child_process');
const ROOT=path.resolve(__dirname,'..');
const fail=m=>{throw new Error('[scanner-publication] '+m)};
const read=p=>JSON.parse(fs.readFileSync(path.join(ROOT,p),'utf8'));
cp.execFileSync(process.execPath,[path.join(ROOT,'scripts/scanner-contract-validator.js')],{stdio:'inherit'});
const summary=read('data/scanner/summary.json');
const canonicalSummary=read('data/summary.json');
const canonicalByTicker=new Map((canonicalSummary.stocks||[]).map(x=>[x.ticker,x]));
const desSource=String(canonicalSummary.universeSource||'');
if(!desSource.startsWith('OJK ')||!desSource.includes('DES'))fail('canonical DES universe source unavailable');
const registry=read('data/scanner/reason-registry.json');
const allowedWhy=new Set(Object.keys(registry.whyWatching||{}));
const allowedVerify=new Set(Object.keys(registry.whatToVerify||{}));
if(registry.schemaVersion!=='scanner-reason-registry-v1')fail('reason registry version');
const exactKeys=(o,expected,label)=>{
 const got=Object.keys(o||{}).sort(), want=[...expected].sort();
 if(JSON.stringify(got)!==JSON.stringify(want))fail(label+' key-set drift');
};
const schemaWhy=new Set(tickerSchemaCodes('reason'));
const schemaVerify=new Set(tickerSchemaCodes('caveat'));
function tickerSchemaCodes(kind){
 const schema=read('contracts/scanner-ticker-v1.schema.json');
 return schema.$defs[kind].properties.code.enum;
}
exactKeys(registry.whyWatching,schemaWhy,'whyWatching registry');
exactKeys(registry.whatToVerify,schemaVerify,'whatToVerify registry');
const unsafeCopy=/(?:\b(?:score|rank|weight|threshold|percentile|cutoff|normalization|penalty|margin|coefficient)\b|[<>]=?\s*\d|\b\d+(?:\.\d+)?\s*%|https?:\/\/|<\/?(?:script|iframe|style)\b)/i;
for(const [group,entries] of Object.entries({whyWatching:registry.whyWatching,whatToVerify:registry.whatToVerify}))
 for(const [code,copy] of Object.entries(entries)){
  if(typeof copy!=='string'||!copy.trim()||copy.length>240)fail('unsafe registry copy '+group+'.'+code);
  if(unsafeCopy.test(copy))fail('possible moat/active-content leakage in registry '+group+'.'+code);
 }
const tickerDir=path.join(ROOT,'data/scanner/tickers');
const files=fs.existsSync(tickerDir)?fs.readdirSync(tickerDir).filter(f=>f.endsWith('.json')).sort():[];
if(summary.generationStatus==='NOT_GENERATED'){
 if(files.length)fail('PRE_ENGINE_LOCK: ticker artifacts exist while Scanner is NOT_GENERATED');
 console.log('SCANNER_PUBLICATION_PASS PRE_ENGINE_LOCK');
 process.exit(0);
}
if(summary.generationStatus!=='GENERATED')fail('unknown generationStatus');
const expected=new Set(summary.items.map(x=>x.ticker+'.json'));
if(files.length!==expected.size)fail('publication set is not atomic: ticker file count mismatch');
for(const f of files)if(!expected.has(f))fail('orphan ticker artifact '+f);
for(const item of summary.items){
 const file=item.ticker+'.json'; if(!files.includes(file))fail('missing ticker artifact '+file);
 const t=read('data/scanner/tickers/'+file);
 const canonical=canonicalByTicker.get(t.ticker);
 if(!canonical)fail('ticker is not present in canonical DES/Fair Value universe '+item.ticker);
 if(t.name!==canonical.name||t.sector!==canonical.sector)fail('canonical identity mismatch '+item.ticker);
 if(t.des.eligible!==true||t.des.universe!==desSource)fail('canonical DES binding mismatch '+item.ticker);
 const canonicalDetailPath='data/'+t.ticker+'.json';
 if(!fs.existsSync(path.join(ROOT,canonicalDetailPath)))fail('canonical Fair Value record missing '+item.ticker);
 const fv=read(canonicalDetailPath);
 if(String(fv.ticker||'').replace(/\.JK$/,'')!==t.ticker)fail('canonical Fair Value ticker mismatch '+item.ticker);
 if(fv.name!==t.name)fail('canonical Fair Value name mismatch '+item.ticker);
 const fvSector=fv.companyProfile&&fv.companyProfile.sector;
 const fvIndustry=fv.companyProfile&&fv.companyProfile.industry;
 if(fvSector!==t.sector)fail('canonical Fair Value sector mismatch '+item.ticker);
 if((t.industry??null)!==(fvIndustry??null))fail('canonical Fair Value industry mismatch '+item.ticker);
 if(t.provenance.valuation!=='CANONICAL_FAIR_VALUE'||t.provenance.des!=='OJK_DES')fail('canonical provenance binding mismatch '+item.ticker);
 const sameArray=(a,b)=>Array.isArray(a)&&Array.isArray(b)&&a.length===b.length&&a.every((v,i)=>v===b[i]);
 if(t.ticker!==item.ticker||
    t.name!==item.name||
    t.sector!==item.sector||
    t.scanner.state!==item.state||
    t.scanner.stateLabel!==item.stateLabel||
    !sameArray(t.researchLens,item.researchLens)||
    t.evidenceStrength.overall!==item.evidenceStrength||
    t.freshness.overall!==item.freshness)
   fail('summary/ticker parity '+item.ticker);
 for(const r of t.whyWatching)if(!allowedWhy.has(r.code)||r.text!==registry.whyWatching[r.code])fail('uncontrolled whyWatching copy '+item.ticker);
 for(const r of t.whatToVerify)if(!allowedVerify.has(r.code)||r.text!==registry.whatToVerify[r.code])fail('uncontrolled whatToVerify copy '+item.ticker);
 if(item.primaryReason!==t.whyWatching[0].code)fail('primaryReason parity '+item.ticker);
 const history=t.stateHistory;
 if(!Array.isArray(history)||history.length<1||history.length>3)fail('stateHistory must contain 1..3 public transitions '+item.ticker);
 const evalDate=String(t.freshness.lastEvaluatedAt||'').slice(0,10);
 for(let i=0;i<history.length;i++){
  const h=history[i];
  if(h.date>evalDate)fail('stateHistory future/evaluation-date violation '+item.ticker);
  if(i>0){
   if(history[i-1].date>h.date)fail('stateHistory chronology violation '+item.ticker);
   if(history[i-1].state===h.state)fail('stateHistory adjacent duplicate state '+item.ticker);
  }
 }
 const latestHistory=history[history.length-1];
 if(latestHistory.state!==t.scanner.state)fail('stateHistory current-state mismatch '+item.ticker);
 if(latestHistory.date!==t.scanner.stateChangedDate)fail('stateHistory stateChangedDate mismatch '+item.ticker);
 const bindAction=(a,label)=>{
  if(a===null)return;
  if(!a||!['FAIR_VALUE','QSTP'].includes(a.type))fail('invalid '+label+' action '+item.ticker);
  const expectedLabel=a.type==='FAIR_VALUE'?'Cek Fair Value':'Buka QSTP';
  if(a.label!==expectedLabel)fail('action type/label mismatch '+label+' '+item.ticker);
 };
 bindAction(t.actions.primary,'primary');
 bindAction(t.actions.secondary,'secondary');
 if(t.actions.primary.type!=='FAIR_VALUE')fail('primary action must remain Fair Value '+item.ticker);
 if(t.actions.secondary&&t.actions.secondary.type!=='QSTP')fail('secondary action must remain QSTP '+item.ticker);
}
console.log('SCANNER_PUBLICATION_PASS',files.length,'ticker artifacts');
