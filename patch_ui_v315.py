from pathlib import Path
p=Path('index.html')
s=p.read_text(encoding='utf-8')

# 1) Replace upside KPI with true margin-of-safety against Base FV.
old='<section class="card kpi"><div class=lbl>Potensi ke ${sn}</div><div class="big ${s.potential==null?\'\':cl(s.potential)}">${pct(s.potential)}</div><div class=note>${rup(d.price)} → ${rup(s.fv)}</div></section>'
new='<section class="card kpi"><div class=lbl>Margin of Safety</div><div class="big ${f.base&&d.price?cl(1-d.price/f.base):\'\'}">${f.base&&d.price?pct(1-d.price/f.base):\'—\'}</div><div class=note>Harga ${rup(d.price)} vs FV Base ${rup(f.base)}</div></section>'
if old not in s: raise SystemExit('MOS KPI anchor not found')
s=s.replace(old,new,1)

# 2) Always show the catalyst/controller card. It has an honest syncing empty state.
footer='<section class="card full footer">WISS Fair Value Engine · Estimasi, bukan target harga.'
card='''<section class="card full" id=catalystCard><div class=section>Katalis & Keterbukaan IDX · 3 Tahun</div><div class=hint id=catalystBody>Memuat cache keterbukaan untuk ticker ini…</div></section>'''
if footer not in s: raise SystemExit('footer anchor not found')
s=s.replace(footer,card+footer,1)

# 3) Load per-ticker verified catalyst cache after the valuation card renders.
oldgo='scenario=\'base\';remember(q);render()'
newgo='scenario=\'base\';remember(q);render();loadCatalysts(q)'
if oldgo not in s: raise SystemExit('go anchor not found')
s=s.replace(oldgo,newgo,1)

# 4) Add renderer before event listeners.
anchor="ticker.addEventListener('keydown'"
js=r'''async function loadCatalysts(q){let el=document.getElementById('catalystBody');if(!el)return;try{let x=await fetch('data/catalysts/'+q+'.json?x='+Date.now(),{cache:'no-store'});if(!x.ok)throw Error('CACHE_NOT_READY');let c=await x.json(),ev=Array.isArray(c.events)?c.events:[],ctrl=c.controllerProfile||{},ctrlText=ctrl.status==='VERIFIED'?(ctrl.controller||'Terverifikasi'):'Belum terverifikasi';let items=ev.slice(0,8).map(e=>{let dt=e.publishedAt?new Date(e.publishedAt).toLocaleDateString('id-ID'):'—',cats=(e.categories||[]).join(' · '),link=e.sourceUrl?`<a href="${e.sourceUrl}" target="_blank" rel="noopener" style="color:#087c61;font-weight:800;text-decoration:none">Buka sumber ↗</a>`:'';return `<div style="padding:11px 0;border-bottom:1px solid #edf0f4"><div style="font-size:10px;color:#8491a4;font-weight:800">${dt}${cats?' · '+cats:''}</div><div style="font-size:13px;font-weight:800;margin:4px 0">${e.title||'Keterbukaan IDX'}</div><div class=hint>${(e.causalLinks||[]).join(' · ')}</div>${link?`<div style="margin-top:5px;font-size:11px">${link}</div>`:''}</div>`}).join('');el.innerHTML=`<div style="display:flex;gap:18px;flex-wrap:wrap;margin-bottom:8px"><div><span class=lbl>Pengendali</span><div style="font-weight:900;margin-top:3px">${ctrlText}</div></div><div><span class=lbl>Disclosure 3Y</span><div style="font-weight:900;margin-top:3px">${ev.length}</div></div></div>${items||'<div class=hint>Belum ada keterbukaan terverifikasi di cache 3 tahun untuk ticker ini.</div>'}<div class=hint style="margin-top:10px">Katalis adalah konteks analisis; tidak otomatis mengubah Fair Value tanpa dampak fundamental yang dapat diukur.</div>`}catch(e){el.innerHTML='<div style="padding:10px 0"><b>Data IDX sedang disinkronkan</b><div class=hint style="margin-top:5px">Collector belum memiliki cache keterbukaan terverifikasi untuk ticker ini. Kondisi ini tidak berarti emiten tidak memiliki berita atau keterbukaan.</div></div>'}}
'''
if anchor not in s: raise SystemExit('listener anchor not found')
s=s.replace(anchor,js+anchor,1)
p.write_text(s,encoding='utf-8')
print('UI_PATCH_OK: Margin of Safety + always-visible IDX Catalyst 3Y card')
