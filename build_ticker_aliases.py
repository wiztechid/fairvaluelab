import json,re
from pathlib import Path
from des_universe import TICKERS

DATA=Path('data')
ALIASES={
 'PGAS':['Perusahaan Gas Negara','PGN','Subholding Gas Pertamina','Pertamina Gas Negara'],
 'ANTM':['Aneka Tambang','Antam'],'BRIS':['Bank Syariah Indonesia','BSI'],
 'PTBA':['Bukit Asam'],'TLKM':['Telkom Indonesia','Telkom'],'TINS':['Timah'],
 'SMGR':['Semen Indonesia','SIG'],'INDF':['Indofood Sukses Makmur'],
 'ICBP':['Indofood CBP'],'UNTR':['United Tractors'],'KLBF':['Kalbe Farma'],
 'MEDC':['Medco Energi','MedcoEnergi'],'ADRO':['Alamtri Resources Indonesia','Adaro Energy'],
 'AADI':['Adaro Andalan Indonesia'],'ADMR':['Adaro Minerals Indonesia'],
}
LEGAL=re.compile(r'\b(pt|tbk|persero|perseroan|terbuka|indonesia)\b',re.I)
def company_aliases(t):
 p=DATA/f'{t}.json'; out=list(ALIASES.get(t,[]))
 try:
  d=json.load(open(p,encoding='utf-8')); name=str(d.get('name') or '')
  if name:
   clean=' '.join(LEGAL.sub(' ',name).split())
   if len(clean)>=5:out.append(clean)
 except:pass
 # Keep only meaningful phrases. Single generic words are intentionally rejected.
 seen=[]
 for a in out:
  a=' '.join(str(a).split())
  if len(a)>=4 and a.lower() not in [x.lower() for x in seen]:seen.append(a)
 return seen
def build():
 m={t:company_aliases(t) for t in TICKERS}
 Path('data').mkdir(exist_ok=True)
 json.dump(m,open(DATA/'ticker_aliases.json','w',encoding='utf-8'),ensure_ascii=False,indent=2)
 print('ALIASES',sum(bool(v) for v in m.values()),'tickers',sum(len(v) for v in m.values()),'phrases')
if __name__=='__main__':build()
