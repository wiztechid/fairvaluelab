from pathlib import Path
p=Path('index.html')
s=p.read_text(encoding='utf-8')
url='https://saweria.co/kopilatte'
old='<img class=supportQR src="assets/saweria-qr.svg" alt="QR Saweria WISS">'
new=f'<a class=supportQRLink href="{url}" target=_blank rel="noopener noreferrer" aria-label="Buka Saweria kopilatte"><img class=supportQR src="assets/saweria-qr.svg" alt="QR Saweria WISS — ketuk untuk membuka Saweria"></a>'
if new not in s:
    if old not in s: raise SystemExit('support QR anchor not found')
    s=s.replace(old,new,1)
css='.supportQRLink{display:block;width:fit-content;margin:8px auto 12px;border-radius:12px;text-decoration:none}.supportQRLink:focus-visible{outline:3px solid #08a982;outline-offset:3px}.supportQRLink .supportQR{margin:0;cursor:pointer}'
if '.supportQRLink{' not in s:
    anchor='.supportActions{display:flex'
    if anchor not in s: raise SystemExit('support CSS anchor not found')
    s=s.replace(anchor,css+anchor,1)
p.write_text(s,encoding='utf-8')
print('SAWERIA_CLICKABLE',new in s,url in s)
