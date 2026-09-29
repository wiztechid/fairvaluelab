const fs=require('fs'),path=require('path'),cp=require('child_process');
const ROOT=path.resolve(__dirname,'..');
const fail=m=>{throw new Error('[scanner-publication] '+m)};
const read=p=>JSON.parse(fs.readFileSync(path.join(ROOT,p),'utf8'));
cp.execFileSync(process.execPath,[path.join(ROOT,'scripts/scanner-contract-validator.js')],{stdio:'inherit'});
const summary=read('data/scanner/summary.json');
const registry=read('data/scanner/reason-registry.json');
const allowedWhy=new Set(Object.keys(registry.whyWatching||{}));
const allowedVerify=new Set(Object.keys(registry.whatToVerify||{}));
if(registry.schemaVersion!=='scanner-reason-registry-v1')fail('reason registry version');
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
 if(t.ticker!==item.ticker||t.scanner.state!==item.state||t.scanner.stateLabel!==item.stateLabel)fail('summary/ticker parity '+item.ticker);
 for(const r of t.whyWatching)if(!allowedWhy.has(r.code)||r.text!==registry.whyWatching[r.code])fail('uncontrolled whyWatching copy '+item.ticker);
 for(const r of t.whatToVerify)if(!allowedVerify.has(r.code)||r.text!==registry.whatToVerify[r.code])fail('uncontrolled whatToVerify copy '+item.ticker);
 if(item.primaryReason!==t.whyWatching[0].code)fail('primaryReason parity '+item.ticker);
}
console.log('SCANNER_PUBLICATION_PASS',files.length,'ticker artifacts');
