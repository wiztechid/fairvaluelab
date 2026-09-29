const fs=require('fs'),path=require('path');
const ROOT=path.resolve(__dirname,'..');
const read=p=>JSON.parse(fs.readFileSync(path.join(ROOT,p),'utf8'));
const fail=m=>{throw new Error('[scanner-contract] '+m)};
const summarySchema=read('contracts/scanner-summary-v1.schema.json');
const tickerSchema=read('contracts/scanner-ticker-v1.schema.json');
const summary=read('data/scanner/summary.json');
const labels={WATCHLIST:'Daftar Pantau',RESEARCH_CONFIRMED:'Terkonfirmasi Riset',WAITING_CONFIRMATION:'Tunggu Konfirmasi',EXTENDED:'Extended',LIMITED_EVIDENCE:'Evidence Terbatas'};
const states=new Set(Object.keys(labels));
const lenses=new Set(['UNDERVALUED','QUALITY_VALUE','DIVIDEND_QUALITY','QUALITY_GROWTH','VALUE_MOMENTUM','HIDDEN_OPPORTUNITY']);
const reasons=new Set(['VALUATION_OPPORTUNITY','PEER_RELATIVE_VALUE','QUALITY_SUPPORT','CASHFLOW_SUPPORT','SUSTAINABLE_GROWTH','PRICE_STRUCTURE_SUPPORT','MOMENTUM_CONFIRMATION','MATERIAL_CATALYST','MULTI_DOMAIN_CONFIRMATION']);
const caveats=new Set(['PRICE_CONFIRMATION_PENDING','VALUATION_DISAGREEMENT','LIMITED_VALUATION_EVIDENCE','FUNDAMENTAL_EVIDENCE_MIXED','PRICE_EXTENDED','CATALYST_UNVERIFIED','CATALYST_UNAVAILABLE','DATA_STALE','LIQUIDITY_CAUTION','MATERIAL_EVENT_REVIEW']);
const forbidden=/\b(score|rank|weight|threshold|penalty|normalization|featureContribution|promotionMargin|demotionMargin|sortScore|opportunityScore|qualityScore|valuationScore|priority|strengthValue)\b/i;
const walk=(v,p='root')=>{if(Array.isArray(v))return v.forEach((x,i)=>walk(x,p+'['+i+']'));if(v&&typeof v==='object')for(const[k,x]of Object.entries(v)){if(forbidden.test(k))fail('forbidden public field '+p+'.'+k);walk(x,p+'.'+k)}};
const exactKeys=(o,allowed,p)=>{for(const k of Object.keys(o||{}))if(!allowed.includes(k))fail('unexpected field '+p+'.'+k);for(const k of allowed)if(!(k in (o||{})))fail('missing field '+p+'.'+k)};
if(summarySchema.$id!=='https://cekvaluasi.com/contracts/scanner-summary-v1.schema.json')fail('summary schema id');
if(tickerSchema.$id!=='https://cekvaluasi.com/contracts/scanner-ticker-v1.schema.json')fail('ticker schema id');
walk(summary);
exactKeys(summary,['schemaVersion','generationStatus','generatedAt','universe','watchlist','items'],'summary');
if(summary.schemaVersion!=='scanner-summary-v1')fail('summary version');
if(!['NOT_GENERATED','GENERATED'].includes(summary.generationStatus))fail('generationStatus');
exactKeys(summary.universe,['name','eligible','evaluated'],'universe');
exactKeys(summary.watchlist,['count','states'],'watchlist');
exactKeys(summary.watchlist.states,[...states],'watchlist.states');
if(summary.generationStatus==='NOT_GENERATED'){
 if(summary.generatedAt!==null||summary.universe.eligible!==null||summary.universe.evaluated!==null||summary.watchlist.count!==null)fail('NOT_GENERATED must use null unknowns');
 if(Object.values(summary.watchlist.states).some(v=>v!==null)||summary.items.length)fail('NOT_GENERATED must not fabricate counts/candidates');
}else{
 for(const [k,v] of [['eligible',summary.universe.eligible],['evaluated',summary.universe.evaluated],['count',summary.watchlist.count]])if(!Number.isInteger(v)||v<0)fail('invalid '+k);
 if(summary.universe.evaluated>summary.universe.eligible)fail('evaluated > eligible');
 if(summary.watchlist.count>summary.universe.evaluated)fail('watchlist > evaluated');
 const vals=Object.values(summary.watchlist.states);if(vals.some(v=>!Number.isInteger(v)||v<0))fail('invalid state counts');
 if(vals.reduce((a,b)=>a+b,0)!==summary.watchlist.count)fail('state count mismatch');
 if(summary.items.length!==summary.watchlist.count)fail('items count mismatch');
}
const seen=new Set();
for(const x of summary.items){
 walk(x,'item');
 exactKeys(x,['ticker','name','sector','state','stateLabel','researchLens','evidenceStrength','primaryReason','freshness','detail','fairValue'],'item');
 if(seen.has(x.ticker))fail('duplicate ticker '+x.ticker);seen.add(x.ticker);
 if(!/^[A-Z0-9]{4,6}$/.test(x.ticker))fail('ticker');
 if(!states.has(x.state)||x.stateLabel!==labels[x.state])fail('state/label mismatch '+x.ticker);
 if(!Array.isArray(x.researchLens)||!x.researchLens.length||new Set(x.researchLens).size!==x.researchLens.length||x.researchLens.some(v=>!lenses.has(v)))fail('researchLens '+x.ticker);
 if(!reasons.has(x.primaryReason))fail('primaryReason '+x.ticker);
 if(x.detail!=='/scanner/'+x.ticker+'.json')fail('noncanonical detail link '+x.ticker);
 if(x.fairValue!=='/fair-value/?ticker='+x.ticker)fail('noncanonical FV link '+x.ticker);
}
function validateTicker(t){
 walk(t,'ticker');
 exactKeys(t,['schemaVersion','ticker','name','sector','industry','des','scanner','researchLens','evidenceStrength','whyWatching','whatToVerify','freshness','valuationContext','provenance','actions','stateHistory'],'ticker');
 if(t.schemaVersion!=='scanner-ticker-v1'||!states.has(t.scanner?.state)||t.scanner.stateLabel!==labels[t.scanner.state])fail('ticker state contract');
 if(!Array.isArray(t.researchLens)||!t.researchLens.length||t.researchLens.some(v=>!lenses.has(v)))fail('ticker lens');
 if(!Array.isArray(t.whyWatching)||!t.whyWatching.length||t.whyWatching.some(r=>!reasons.has(r.code)))fail('whyWatching');
 if(!Array.isArray(t.whatToVerify)||t.whatToVerify.some(r=>!caveats.has(r.code)))fail('whatToVerify');
 if(t.provenance?.valuation!=='CANONICAL_FAIR_VALUE')fail('noncanonical valuation provenance');
 if(t.actions?.primary?.type!=='FAIR_VALUE'||t.actions.primary.url!=='/fair-value/?ticker='+t.ticker)fail('primary action must be canonical Fair Value');
 if(t.actions.secondary&&t.actions.secondary.type==='QSTP'&&t.actions.secondary.url!=='/qstp.html?ticker='+t.ticker)fail('noncanonical QSTP link');
 if(!['CURRENT','NO_MATERIAL_EVENT','SOURCE_UNAVAILABLE','STALE'].includes(t.freshness?.catalyst))fail('catalyst freshness semantics');
}
const tickerDir=path.join(ROOT,'data/scanner/tickers');
if(fs.existsSync(tickerDir))for(const f of fs.readdirSync(tickerDir).filter(f=>f.endsWith('.json'))){const t=read('data/scanner/tickers/'+f);validateTicker(t);if(f!==t.ticker+'.json')fail('ticker filename mismatch '+f)}
console.log('SCANNER_CONTRACT_PASS',summary.generationStatus,summary.items.length,'public candidates');
