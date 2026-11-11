"""Standard-library, no-Streamlit QA of issuer-level dashboard data & locked model tables."""
import csv, sys
from pathlib import Path
from analysis import read_csv, filtered_pairs, counts, followup_counts
p=read_csv('Paper2_TahapA_v0_3_Pasangan.csv')
f=read_csv('Paper2_TahapA_v0_3_Followup.csv')
entity=filtered_pairs(p,{r['Sector'] for r in p},{r['Quarter'] for r in p},True)
c=counts(entity)
assert (c['pairs'],c['firms'],c['rec'],c['rr'],c['onset'],c['lp'],c['zero'])==(4463,761,425,855,388,2788,7)
ff=followup_counts(entity,f)
assert (ff['recovery'],ff['observed'],ff['still_profit'],ff['relapse'],ff['zero'],ff['missing'])==(425,346,233,112,1,79)
with (Path('data')/'Table_Model_Diagnostics_and_Robustness.csv').open(encoding='utf-8-sig') as h: d=list(csv.DictReader(h))
assert len(d)==16 and all(r['Status']=='ok' for r in d)
print('PASS | entity pairs=4,463 | recovery=425 | onset=388 | follow-up=346 | 16 model scenarios')
