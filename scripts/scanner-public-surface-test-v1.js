#!/usr/bin/env node
const fs=require('fs'),assert=require('assert'),p=require('path').resolve(__dirname,'../scanner/index.html'),s=fs.readFileSync(p,'utf8');
for(const x of ['fetch(\'/data/scanner/summary.json\'','generationStatus!==\'GENERATED\'','Cek Fair Value','Status di halaman ini adalah prioritas riset, bukan rekomendasi beli atau jual.','href="/fair-value/"','href="/qstp.html"'])assert(s.includes(x),x);
for(const bad of ['opportunityScore','qualityScore','valuationScore','sortScore','threshold','STRONG BUY','rekomendasi beli</'])assert(!s.includes(bad),'private/recommendation leak '+bad);
console.log('SCANNER_PUBLIC_SURFACE_V1_PASS');