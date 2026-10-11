#!/usr/bin/env node
const fs=require('fs'),assert=require('assert'),path=require('path');
const ROOT=path.resolve(__dirname,'..'),p=path.join(ROOT,'scanner/index.html'),s=fs.readFileSync(p,'utf8');
for(const x of ['fetch(\'/data/scanner/summary.json\'','generationStatus!==\'GENERATED\'','Cek Fair Value','Alasan &amp; bukti','/data/scanner/tickers/\'+encodeURIComponent(ticker)+\'.json','detail.whatToVerify','Status di halaman ini adalah prioritas riset, bukan rekomendasi beli atau jual.','href="/fair-value/"','href="/qstp.html"'])assert(s.includes(x),x);
for(const bad of ['opportunityScore','qualityScore','valuationScore','sortScore','threshold','STRONG BUY','rekomendasi beli</'])assert(!s.includes(bad),'private/recommendation leak '+bad);
const summary=JSON.parse(fs.readFileSync(path.join(ROOT,'data/scanner/summary.json'),'utf8'));
for(const item of summary.items){
 const file=path.join(ROOT,'data/scanner/tickers',item.ticker+'.json');
 assert(fs.existsSync(file),'missing detail file '+item.ticker);
 const detail=JSON.parse(fs.readFileSync(file,'utf8'));
 assert.strictEqual(detail.ticker,item.ticker,'detail ticker mismatch '+item.ticker);
}
console.log('SCANNER_PUBLIC_SURFACE_V1_PASS',summary.items.length);
