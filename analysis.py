"""Read-only descriptive analysis for Paper 2: no modeling, no data mutation."""
from collections import Counter, defaultdict
import csv
from pathlib import Path

HERE = Path(__file__).resolve().parent
DATA = HERE / 'data'

def read_csv(filename):
    with (DATA / filename).open('r', encoding='utf-8-sig', newline='') as f:
        return list(csv.DictReader(f))

def filtered_pairs(rows, sectors, quarters, exclude_gotom=False):
    return [r for r in rows if r['Sector'] in sectors and r['Quarter'] in quarters
            and not (exclude_gotom and r['Code'] == 'GOTOM')]

def counts(rows):
    t = Counter(r['Transition'] for r in rows)
    rr=t['Rugi -> Rugi']; rec=t['Rugi -> Laba']
    onset=t['Laba -> Rugi']; lp=t['Laba -> Laba']
    loss_risk=rec+rr; profit_risk=onset+lp
    return {'pairs':len(rows),'firms':len({r['Code'] for r in rows}),
            'rec':rec,'rr':rr,'onset':onset,'lp':lp,
            'at_risk_loss':loss_risk,'at_risk_profit':profit_risk,
            'zero':len(rows)-rr-rec-onset-lp,
            'rec_rate':rec/loss_risk if loss_risk else None,
            'onset_rate':onset/profit_risk if profit_risk else None}

def group_counts(rows, field):
    groups=defaultdict(list)
    for r in rows: groups[r[field]].append(r)
    return {key:counts(group) for key,group in sorted(groups.items())}

def followup_counts(rows, followup_rows):
    eligible={(r['Code'],r['Quarter']) for r in rows if r['Transition']=='Rugi -> Laba'}
    selected=[r for r in followup_rows if (r['Code'],r['Recovery_Quarter']) in eligible]
    c=Counter(r['Followup_Status'] for r in selected)
    return {'recovery':len(eligible),'observed':len(selected),
            'still_profit':c['Laba'],'relapse':c['Rugi'],'zero':c['Nol'],
            'missing':len(eligible)-len(selected),
            'right_censored':sum(q=='2026Q3' for code,q in eligible if (code,q) not in
                       {(f['Code'],f['Recovery_Quarter']) for f in selected})}
