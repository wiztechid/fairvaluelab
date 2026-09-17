from pathlib import Path
p=Path('index.html')
s=p.read_text(encoding='utf-8')

# v3.16 UI patch
# 1) Margin of Safety follows the selected valuation scenario (bear/base/bull).
old='<section class="card kpi"><div class=lbl>Margin of Safety</div><div class="big ${f.base&&d.price?cl(1-d.price/f.base):\'\'}">${f.base&&d.price?pct(1-d.price/f.base):\'—\'}</div><div class=note>Harga ${rup(d.price)} vs FV Base ${rup(f.base)}</div></section>'
new='<section class="card kpi"><div class=lbl>Margin of Safety · ${sn}</div><div class="big ${s.fv&&d.price?cl(1-d.price/s.fv):\'\'}">${s.fv&&d.price?pct(1-d.price/s.fv):\'—\'}</div><div class=note>Harga ${rup(d.price)} vs FV ${sn} ${rup(s.fv)}</div></section>'
if old not in s: raise SystemExit('scenario MOS anchor not found')
s=s.replace(old,new,1)

# 2) Move IDX catalyst block above the fair-value method calculation table.
card='<section class="card full" id=catalystCard><div class=section>Katalis & Keterbukaan IDX · 3 Tahun</div><div class=hint id=catalystBody>Memuat cache keterbukaan untuk ticker ini…</div></section>'
if card not in s: raise SystemExit('catalyst card anchor not found')
s=s.replace(card,'',1)
model='<section class="card full"><div class=section>Model Valuasi Sesuai Sektor</div>'
if model not in s: raise SystemExit('model section anchor not found')
s=s.replace(model,card+model,1)

# 3) Replace single long catalyst list with grouped action cards.
start=s.find('async function loadCatalysts(q)')
end=s.find("ticker.addEventListener('keydown'",start)
if start<0 or end<0: raise SystemExit('catalyst renderer anchor not found')
js=r'''async function loadCatalysts(q){let el=document.getElementById('catalystBody');if(!el)return;try{let x=await fetch('data/catalysts/'+q+'.json?x='+Date.now(),{cache:'no-store'});if(!x.ok)throw Error('CACHE_NOT_READY');let c=await x.json(),ev=Array.isArray(c.events)?c.events:[],ctrl=c.controllerProfile||{},ctrlText=ctrl.status==='VERIFIED'?(ctrl.controller||'Terverifikasi'):'Belum terverifikasi';const groups=[['Earnings & Kinerja',['EARNINGS']],['Corporate Action',['BUYBACK','RIGHTS','DIVIDEND','MNA','RUPS']],['Ekspansi · Capex · Kontrak',['CAPEX_EXPANSION','CONTRACT']],['Financing & Utang',['DEBT_FINANCING']],['Insider · Pengendali · Afiliasi',['INSIDER','CONTROLLER','AFFILIATE']],['Legal & Regulatory',['LEGAL_REGULATORY','SUSPENSION']],['Lainnya',['MATERIAL','PUBLIC_EXPOSE','OTHER']]];let esc=v=>String(v??'').replace(/[&<>"']/g,m=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[m]));let eventHtml=e=>{let dt=e.publishedAt?new Date(e.publishedAt).toLocaleDateString('id-ID'):'—',cats=(e.categories||[]).join(' · '),link=e.sourceUrl?`<a href="${esc(e.sourceUrl)}" target="_blank" rel="noopener" style="color:#087c61;font-weight:800;text-decoration:none">Sumber IDX ↗</a>`:'';return `<div class=catevent><div class=catmeta>${esc(dt)}${cats?' · '+esc(cats):''}</div><div class=cattitle>${esc(e.title||'Keterbukaan IDX')}</div>${(e.causalLinks||[]).length?`<div class=hint>${esc((e.causalLinks||[]).join(' · '))}</div>`:''}${link?`<div class=catlink>${link}</div>`:''}</div>`};let cards=groups.map(([name,cats])=>{let items=ev.filter(e=>(e.categories||[]).some(c=>cats.includes(c)));if(!items.length)return'';return `<div class=catAction><div class=catActionHead><b>${name}</b><span>${items.length}</span></div>${items.slice(0,4).map(eventHtml).join('')}${items.length>4?`<div class=hint>+${items.length-4} keterbukaan lain dalam 3 tahun</div>`:''}</div>`}).join('');el.innerHTML=`<div class=catSummary><div><span class=lbl>Pengendali</span><b>${esc(ctrlText)}</b></div><div><span class=lbl>Disclosure 3Y</span><b>${ev.length}</b></div><div><span class=lbl>Status Sumber</span><b>${ev.length?'TERVERIFIKASI':'CACHE KOSONG'}</b></div></div><div class=catGrid>${cards||'<div class="catAction catEmpty"><b>Belum ada action terverifikasi di cache</b><div class=hint>Ini tidak berarti emiten tidak memiliki berita/keterbukaan.</div></div>'}</div><div class=hint style="margin-top:10px">Katalis memberi konteks sebab-akibat. Fair Value hanya berubah bila dampak fundamentalnya dapat diukur.</div>`}catch(e){el.innerHTML='<div class=catSummary><div><span class=lbl>Status Sumber</span><b>SEDANG DISINKRONKAN</b></div></div><div class="catAction catEmpty"><b>Data IDX sedang disinkronkan</b><div class=hint>Collector belum memiliki cache keterbukaan terverifikasi untuk ticker ini. Kondisi ini tidak berarti emiten tidak memiliki berita atau keterbukaan.</div></div>'}}
'''
s=s[:start]+js+s[end:]

# 4) Styling for catalyst action cards, responsive on mobile.
css='.catSummary{display:grid;grid-template-columns:repeat(3,1fr);gap:9px;margin:12px 0}.catSummary>div{background:#f6f8fb;border-radius:10px;padding:11px}.catSummary b{display:block;margin-top:4px;font-size:13px}.catGrid{display:grid;grid-template-columns:repeat(3,1fr);gap:10px}.catAction{border:1px solid #e5eaf1;border-radius:11px;padding:12px;background:#fbfcfe}.catActionHead{display:flex;justify-content:space-between;gap:8px;align-items:center;margin-bottom:5px}.catActionHead span{font-size:10px;font-weight:900;background:#e8fbf5;color:#087c61;padding:4px 7px;border-radius:999px}.catevent{padding:9px 0;border-top:1px solid #edf0f4}.catmeta{font-size:9px;color:#8491a4;font-weight:800}.cattitle{font-size:12px;font-weight:850;margin:3px 0}.catlink{margin-top:4px;font-size:10px}.catEmpty{grid-column:1/-1}.catAction a{color:#087c61}'
needle='@media(max-width:760px){'
if needle not in s: raise SystemExit('mobile css anchor not found')
s=s.replace(needle,css+needle,1)
s=s.replace('.raw,.quickgrid{grid-template-columns:repeat(2,1fr)}table{display:block;', '.raw,.quickgrid{grid-template-columns:repeat(2,1fr)}.catGrid,.catSummary{grid-template-columns:1fr}table{display:block;',1)

p.write_text(s,encoding='utf-8')
print('UI_PATCH_V316_OK: scenario-aware MOS + grouped IDX action cards above valuation methods')
