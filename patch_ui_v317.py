from pathlib import Path
p=Path('index.html');s=p.read_text(encoding='utf-8')
# Indicative FV is visible, but clearly distinguished from fully confirmed composite FV.
s=s.replace("hasFV=!!f.available,confidence=hasFV", "hasFV=!!(f.available||f.indicative),confidence=hasFV",1)
s=s.replace("status:zone==='discount'?'MURAH':zone==='expensive'?'MAHAL':'WAJAR'", "status:D?.fairValue?.indicative?'FV INDIKATIF':zone==='discount'?'MURAH':zone==='expensive'?'MAHAL':'WAJAR'",1)
s=s.replace('<div class=section>Estimasi Harga Wajar Gabungan</div><div class=hint>Gabungan metode aktif berdasarkan bobot sektor. Pilih skenario untuk mengubah patokan.</div>', '<div class=section>${f.indicative?\'Estimasi Fair Value Indikatif\':\'Estimasi Harga Wajar Gabungan\'}</div><div class=hint>${f.indicative?\'Metode valuasi valid tersedia, tetapi bukti keluarga independen belum cukup. Range tetap ditampilkan dengan confidence lebih rendah.\':\'Gabungan metode aktif berdasarkan bobot sektor. Pilih skenario untuk mengubah patokan.\'}</div>',1)
# Add verified controller/broker profile inside the IDX catalyst block.
old='<section class="card full" id=catalystCard><div class=section>Katalis & Keterbukaan IDX · 3 Tahun</div><div class=hint id=catalystBody>Memuat cache keterbukaan untuk ticker ini…</div></section>'
new='<section class="card full" id=catalystCard><div class=section>Katalis & Keterbukaan IDX · 3 Tahun</div><div id=marketActorBody class=hint style="margin-bottom:10px">Memuat profil pengendali & market actors…</div><div class=hint id=catalystBody>Memuat cache keterbukaan untuk ticker ini…</div></section>'
if old not in s: raise SystemExit('catalyst card anchor missing')
s=s.replace(old,new,1)
s=s.replace('render();loadCatalysts(q)', 'render();loadCatalysts(q);loadMarketActors(q)',1)
anchor="async function loadCatalysts(q)"
if anchor not in s: raise SystemExit('loadCatalysts anchor missing')
js=r'''async function loadMarketActors(q){let el=document.getElementById('marketActorBody');if(!el)return;try{let x=await fetch('data/market_actors/'+q+'.json?x='+Date.now(),{cache:'no-store'});if(!x.ok)throw Error('ACTOR_CACHE_NOT_READY');let a=await x.json(),c=a.controller||{},bs=Array.isArray(a.brokers)?a.brokers:[],ev=Array.isArray(a.actorEvents)?a.actorEvents:[],esc=v=>String(v??'').replace(/[&<>"']/g,m=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[m]));let ctrl=c.status==='VERIFIED'?(c.direct||'Terverifikasi'):'Belum terverifikasi';let ult=c.status==='VERIFIED'?(c.ultimate||'Belum tersedia'):'Belum terverifikasi';let brokers=bs.length?bs.map(b=>`<span class=actorChip>${esc(b.code)}${b.name?' · '+esc(b.name):''}</span>`).join(''):'<span class=hint>Belum ada kode broker yang terhubung melalui keterbukaan resmi.</span>';el.innerHTML=`<div class=actorGrid><div class=actorBox><span class=lbl>Pengendali Terverifikasi</span><b>${esc(ctrl)}</b><small>Ultimate: ${esc(ult)}${c.ownershipPct!=null?' · '+esc(c.ownershipPct)+'%':''}</small></div><div class=actorBox><span class=lbl>Broker / Anggota Bursa Terkait Disclosure</span><div class=actorChips>${brokers}</div><small>${ev.length} event ownership/market-actor terhubung</small></div></div><div class=hint style="margin-top:7px">Kode broker hanya identitas Anggota Bursa. Tidak dianggap bukti akumulasi, afiliasi, atau aksi pengendali tanpa keterbukaan eksplisit.</div>`}catch(e){el.innerHTML='<div class=actorGrid><div class=actorBox><span class=lbl>Pengendali & Broker</span><b>Data terverifikasi sedang disinkronkan</b><small>Tidak ada identitas yang ditebak dari nama grup, broker summary, atau transaksi pasar.</small></div></div>'}}
'''
s=s.replace(anchor,js+anchor,1)
css='.actorGrid{display:grid;grid-template-columns:1fr 2fr;gap:9px;margin:10px 0}.actorBox{background:#f6f8fb;border-radius:10px;padding:11px}.actorBox b{display:block;margin:4px 0;font-size:13px}.actorBox small{display:block;color:#8a96a7;font-size:10px}.actorChips{display:flex;gap:6px;flex-wrap:wrap;margin:6px 0}.actorChip{font-size:10px;font-weight:900;background:#e8fbf5;color:#087c61;padding:5px 8px;border-radius:999px}'
needle='@media(max-width:760px){'
if needle not in s: raise SystemExit('css anchor missing')
s=s.replace(needle,css+needle,1)
s=s.replace('.catGrid,.catSummary{grid-template-columns:1fr}', '.catGrid,.catSummary,.actorGrid{grid-template-columns:1fr}',1)
p.write_text(s,encoding='utf-8');print('UI_PATCH_V317_OK')
