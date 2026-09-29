const fs=require('fs');
const path=require('path');

const ROOT=path.resolve(__dirname,'..');
const schema=JSON.parse(fs.readFileSync(path.join(ROOT,'contracts/scanner-output-v1.schema.json'),'utf8'));
const data=JSON.parse(fs.readFileSync(path.join(ROOT,'data/scanner/summary.json'),'utf8'));

const fail=(m)=>{throw new Error('[scanner-contract] '+m)};
const eq=(a,b,m)=>{if(a!==b)fail(m)};
const enums={
 states:new Set(['WATCHLIST','RESEARCH_CONFIRMED','WAITING_CONFIRMATION','EXTENDED','LIMITED_EVIDENCE']),
 lenses:new Set(['UNDERVALUED','QUALITY_VALUE','DIVIDEND_QUALITY','QUALITY_GROWTH','VALUE_MOMENTUM','HIDDEN_OPPORTUNITY']),
 evidence:new Set(['STRONG','ADEQUATE','LIMITED']),
 freshness:new Set(['CURRENT','AGING','STALE','UNAVAILABLE'])
};
eq(schema.$id,'https://cekvaluasi.com/contracts/scanner-output-v1.schema.json','unexpected schema id');
eq(data.schemaVersion,'scanner-summary-v1','schemaVersion mismatch');
if(!data.universe||!Number.isInteger(data.universe.eligible)||!Number.isInteger(data.universe.evaluated))fail('invalid universe counts');
if(!data.watchlist||!Number.isInteger(data.watchlist.count)||!Array.isArray(data.items))fail('invalid watchlist envelope');
for(const s of enums.states)if(!Number.isInteger(data.watchlist.states?.[s]))fail('missing state count '+s);
const sum=[...enums.states].reduce((n,s)=>n+data.watchlist.states[s],0);
eq(sum,data.watchlist.count,'state counts must equal watchlist count');
eq(data.items.length,data.watchlist.count,'items length must equal watchlist count');
const forbidden=/\b(score|rank|weight|threshold|penalty|normalization|featureContribution|promotionMargin|demotionMargin|sortScore|opportunityScore|qualityScore|valuationScore)\b/i;
const walk=(v,p='root')=>{
 if(Array.isArray(v))return v.forEach((x,i)=>walk(x,p+'['+i+']'));
 if(v&&typeof v==='object')for(const [k,x] of Object.entries(v)){if(forbidden.test(k))fail('forbidden public field '+p+'.'+k);walk(x,p+'.'+k)}
};
walk(data);
for(const x of data.items){
 if(!/^[A-Z0-9]{4,6}$/.test(x.ticker))fail('invalid ticker');
 if(!enums.states.has(x.state))fail('invalid public state '+x.state);
 if(!Array.isArray(x.researchLens)||!x.researchLens.length||x.researchLens.some(l=>!enums.lenses.has(l)))fail('invalid research lens');
 if(!enums.evidence.has(x.evidenceStrength))fail('invalid evidence strength');
 if(!enums.freshness.has(x.freshness))fail('invalid freshness');
 if(!/^\/fair-value\//.test(x.fairValue))fail('Fair Value link must use canonical route');
}
console.log('SCANNER_CONTRACT_PASS',data.items.length,'public candidates');
