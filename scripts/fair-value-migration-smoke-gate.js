const fs=require('fs');
function fail(m){console.error('FAIL:',m);process.exitCode=1}
function ok(c,m){if(!c)fail(m)}
const mig=fs.readFileSync('fair-value/index.html','utf8');
// Pre-switch byte parity against root was proven before root promotion staging.
// Post-switch this gate protects the migrated engine's runtime contracts; browser parity is enforced separately.
const scripts=[...mig.matchAll(/<script([^>]*)>([\s\S]*?)<\/script>/gi)]
 .filter(x=>!/type=["']application\/ld\+json["']/i.test(x[1]||''))
 .map(x=>x[2]).filter(Boolean);
for(const [i,s] of scripts.entries()){try{new Function(s)}catch(e){fail('executable inline JS '+i+' parse: '+e.message)}}
const jsonLd=[...mig.matchAll(/<script[^>]*type=["']application\/ld\+json["'][^>]*>([\s\S]*?)<\/script>/gi)].map(x=>x[1]);
for(const [i,s] of jsonLd.entries()){try{JSON.parse(s)}catch(e){fail('JSON-LD '+i+' parse: '+e.message)}}
const fetches=[...mig.matchAll(/fetch\(([^)]{1,180})\)/g)].map(x=>x[0]);
ok(fetches.length===7,'expected 7 fetch contracts');
ok(fetches.every(x=>x.includes('../data/')),'all fetches must resolve through ../data/');
for(const p of ['data/summary.json','data/sector_mos.json','universe.html','methodology.html','assets/saweria-qr.svg']) ok(fs.existsSync(p),'missing dependency '+p);
const sum=JSON.parse(fs.readFileSync('data/summary.json','utf8')),rows=sum.stocks||[];
for(const st of ['SIAP','INDIKATIF','REVIEW','REFERENSI','BELUM_DINILAI']){
 const r=rows.find(x=>(x.analysisStatus||x.status)===st);ok(!!r,'no representative '+st);
 if(r){const t=String(r.ticker).replace(/\.JK$/i,'');ok(fs.existsSync('data/'+t+'.json'),'missing representative data '+st+' '+t)}
}
for(const s of ["URLSearchParams(location.search).get('ticker')",'history.replaceState',"addEventListener('popstate'",'href="?ticker=']) ok(mig.includes(s),'missing URL-state contract '+s);
ok(mig.includes('canonicalLink" href="https://wiztechid.github.io/fairvaluelab/fair-value/"'),'static canonical must be /fair-value/');
ok(mig.includes("base='https://wiztechid.github.io/fairvaluelab/'"),'dynamic ticker metadata baseline must remain preserved');
ok(mig.includes("ACTOR_CACHE_NOT_READY")&&mig.includes('Data terverifikasi sedang disinkronkan'),'market actor graceful fallback missing');
ok(mig.includes("GZ_CACHE")&&mig.includes('Golden Zone belum valid'),'golden-zone fallback missing');
ok(mig.includes("x.status===404")&&mig.includes('Belum ada katalis material terdeteksi'),'catalyst 404 fallback missing');
ok(mig.includes('@media'),'responsive media queries missing');
if(process.exitCode) process.exit(process.exitCode);
console.log('Fair Value migration smoke gate PASS');