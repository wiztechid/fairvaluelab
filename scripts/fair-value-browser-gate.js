const { chromium } = require('playwright');
const assert = require('assert');
const base='http://127.0.0.1:4173/fair-value/';
const states={SIAP:'ACES',INDIKATIF:'ADCP',REVIEW:'AADI',REFERENSI:'AKSI',BELUM_DINILAI:'AEGS'};
(async()=>{
 const browser=await chromium.launch({headless:true});
 const page=await browser.newPage({viewport:{width:1440,height:1000}});
 const consoleErrors=[],failed=[],httpErrors=[];
 page.on('console',m=>{if(m.type()==='error') consoleErrors.push(m.text())});
 page.on('requestfailed',r=>failed.push(r.url()+' :: '+(r.failure()?.errorText||'')));
 page.on('response',r=>{if(r.status()>=400)httpErrors.push({status:r.status(),url:r.url()})});
 let r=await page.goto(base,{waitUntil:'networkidle'}); assert(r&&r.ok(),'initial /fair-value/ must load');
 assert(await page.locator('#ticker').count()===1,'ticker input missing');
 for(const [st,t] of Object.entries(states)){
   r=await page.goto(base+'?ticker='+t,{waitUntil:'networkidle'}); assert(r&&r.ok(),st+' direct ticker page failed');
   assert((await page.locator('#ticker').inputValue()).toUpperCase()===t,st+' ticker state not reflected');
   const body=(await page.locator('body').innerText()).toUpperCase();
   assert(body.includes(t),st+' ticker not rendered in page');
 }
 await page.goto(base+'?ticker=ACES',{waitUntil:'networkidle'});
 await page.locator('#ticker').fill('AADI');
 await page.waitForTimeout(400);
 await page.locator('#ticker').press('Enter');
 await page.waitForTimeout(900);
 assert(new URL(page.url()).searchParams.get('ticker')==='AADI','ticker change did not replace URL');
 await page.goBack({waitUntil:'networkidle'}).catch(()=>{});
 // replaceState does not add a history entry; verify page remains operational rather than requiring a false back-navigation contract.
 assert(await page.locator('#ticker').count()===1,'page broke after browser back');
 for(const href of ['../universe.html','../methodology.html']){
   const el=page.locator('a[href="'+href+'"]').first(); assert(await el.count(),href+' link missing');
   const target=new URL(await el.getAttribute('href'),page.url()).href;
   const rr=await page.request.get(target); assert(rr.ok(),href+' target failed '+rr.status());
 }
 const qr=await page.request.get('http://127.0.0.1:4173/assets/saweria-qr.svg'); assert(qr.ok(),'QR asset failed');
 await page.goto(base+'?ticker=AADI',{waitUntil:'networkidle'});
 const aadi=(await page.locator('body').innerText()).toLowerCase();
 assert(aadi.includes('data terverifikasi sedang disinkronkan')||aadi.includes('market'),'Market Actor fallback/section not observable');
 const sectorLinks=page.locator('a.mosStockLink'); if(await sectorLinks.count()){const href=await sectorLinks.first().getAttribute('href');assert(/^\?ticker=/.test(href),'sector MoS link must stay local');}
 const mobile=await browser.newPage({viewport:{width:390,height:844},isMobile:true});
 r=await mobile.goto(base+'?ticker=ACES',{waitUntil:'networkidle'}); assert(r&&r.ok(),'mobile page failed');
 assert((await mobile.locator('body').evaluate(el=>el.scrollWidth))<=390+2,'mobile horizontal overflow');
 assert(await mobile.locator('#ticker').isVisible(),'ticker input not visible on mobile');
 // Ignore browser noise from external optional resources only; local migration-caused failures are fatal.
 const localFailed=failed.filter(x=>x.includes('127.0.0.1:4173'));
 assert.deepStrictEqual(localFailed,[],'local request failures: '+localFailed.join('\n'));
 const allowed404=u=>/\/data\/(golden_zone|market_actors|catalysts)\//.test(u)||/\/favicon(?:\.ico)?(?:\?|$)/.test(u);
 const fatalHttp=httpErrors.filter(x=>!(x.status===404&&allowed404(x.url)));
 assert.deepStrictEqual(fatalHttp,[],'unexpected HTTP errors: '+JSON.stringify(fatalHttp));
 // Chromium emits generic console errors for expected 404 responses without the URL.
 // Pair generic 404 console noise with observed allowed HTTP 404s; all other console errors remain fatal.
 const allowed404Count=httpErrors.filter(x=>x.status===404&&allowed404(x.url)).length;
 const generic404=consoleErrors.filter(x=>/Failed to load resource: the server responded with a status of 404/i.test(x)).length;
 assert(generic404<=allowed404Count,'unattributed console 404 errors: '+generic404+' > allowed observed 404s '+allowed404Count);
 const fatalConsole=consoleErrors.filter(x=>!/Failed to load resource: the server responded with a status of 404/i.test(x)&&!/third-party|net::ERR/i.test(x));
 assert.deepStrictEqual(fatalConsole,[],'console errors: '+fatalConsole.join('\n'));
 await browser.close();
 console.log('Fair Value browser interaction gate PASS');
})().catch(e=>{console.error(e.stack||e);process.exit(1)});