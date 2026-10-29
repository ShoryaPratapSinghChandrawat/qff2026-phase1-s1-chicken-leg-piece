#!/usr/bin/env python3
"""Generate the four required Stage-A Bell aggregates on frozen Processor D."""
import csv, sys
from collections import deque
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
import qff_sim as sim

def distances(n,edges):
    a={q:set() for q in range(n)}
    for x,y in edges: a[x].add(y);a[y].add(x)
    pairs={}
    for s in range(n):
        d={s:0};q=deque([s])
        while q:
            u=q.popleft()
            for v in sorted(a[u]):
                if v not in d:d[v]=d[u]+1;q.append(v)
        for t,dist in d.items():
            if s<t:pairs[(s,t)]=dist
    return pairs

def main():
    p=sim.load_processor(str(ROOT/'processors/processor_D.json'))
    d=distances(p['num_qubits'],p['edges'])
    near=min(tuple(sorted(e)) for e in p['edges'])
    maxd=max(d.values());far=min(k for k,v in d.items() if v==maxd)
    cols=['pair','pair_distance','condition','two_qubit_gates','XX','XX_se','YY','YY_se','ZZ','ZZ_se','fidelity','fidelity_se']
    rows=[]
    for pair in (near,far):
        for condition,noisy in (('ideal',False),('noisy',True)):
            r=sim.bell_experiment(p,pair,noisy,shots=4096)
            rows.append({'pair':f'{pair[0]}-{pair[1]}','pair_distance':r['pair_distance'],'condition':condition,
              'two_qubit_gates':r['cx'],'XX':r['XX'],'XX_se':r['XX_se'],'YY':r['YY'],'YY_se':r['YY_se'],
              'ZZ':r['ZZ'],'ZZ_se':r['ZZ_se'],'fidelity':r['fidelity'],'fidelity_se':r['fidelity_se']})
    out=ROOT/'results/tables/bell.csv'
    with out.open('w',newline='',encoding='utf-8') as f:
        w=csv.DictWriter(f,fieldnames=cols,lineterminator='\n');w.writeheader();w.writerows(rows)
    for r in rows: print(r)
    print(f'Wrote {len(rows)} aggregate rows to {out.relative_to(ROOT)}; shots per basis=4096')
if __name__=='__main__': main()
