#!/usr/bin/env python3
"""Exact-reference checks and locked PS-S1 N=4 HVA sweep (L=1..4, seeds 0..2)."""
from __future__ import annotations
import csv, json, math, sys, time
from pathlib import Path
import numpy as np
from scipy.optimize import minimize
from qiskit.quantum_info import SparsePauliOp, Statevector, state_fidelity
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
import qff_sim as sim
GS=[0.25,0.50,0.75,1.00,1.25,1.50,2.00]
SEEDS=[0,1,2]
LAYERS=range(1,5)
OPTIONS={"maxiter":250,"maxfun":30000,"ftol":1e-12,"gtol":1e-7,"finite_difference":"3-point"}
RAW=ROOT/'results/raw/s1_seed_runs.csv'
EXACT=ROOT/'results/tables/s1_exact_reference.csv'
AGG=ROOT/'results/tables/s1_results.csv'
LAYER=ROOT/'results/tables/layer_study.csv'
RAW_COLS=['N','g','layers','seed','energy','exact_E0','energy_err','fidelity','fidelity_2','mx','czz_nn','mz2','mz','optimizer_calls','n_params','two_q_on_D','success','status','message','runtime_seconds','theta_json']
AGG_COLS=['N','g','layers','best_energy','exact_E0','energy_err','fidelity','fidelity_2','mx','mx_exact','czz_nn','czz_nn_exact','mz2','mz2_exact','mz','optimizer_calls','n_params','two_q_on_D']


def get_reference(g):
    name=f"tfim_open_N4_g{g:.2f}.json"
    obj=json.loads((ROOT/'data/s1'/name).read_text(encoding='utf-8'))
    meta=obj['meta']
    H=SparsePauliOp.from_list([(label,float(coeff)) for label,coeff in obj['operator']])
    vals,states=sim.exact_spectrum(H,2)
    e0=float(vals[0]);e1=float(vals[1])
    d0=abs(e0-float(meta['E0_exact']));d1=abs(e1-float(meta['E1_exact']))
    if d0>1e-9 or d1>1e-9:
        raise RuntimeError(f"exact mismatch {name}: E0 diff={d0:.3e}, E1 diff={d1:.3e}")
    ops=sim.observable_ops(4)
    ex=sim.expectations(states[0],ops)
    return H,meta,vals,states,ex


def minimize_one(H, g, layers, seed, method='L-BFGS-B'):
    qc,params=sim.hva_ansatz(4,layers,zz_mode='cx')
    theta0=np.random.default_rng(seed).uniform(-np.pi,np.pi,len(params))
    cost=sim.CountedCost(lambda th: sim.energy_statevector(qc.assign_parameters(dict(zip(params,th))),H))
    t0=time.perf_counter()
    if method=='L-BFGS-B':
        res=minimize(cost,theta0,method=method,jac='3-point',
            options={k:v for k,v in OPTIONS.items() if k!='finite_difference'})
    else:
        res=minimize(cost,theta0,method=method,options={'maxiter':2500,'tol':1e-8})
    elapsed=time.perf_counter()-t0
    theta=np.asarray(res.x,dtype=float)
    bound=qc.assign_parameters(dict(zip(params,theta)))
    state=Statevector(bound)
    vals,states=sim.exact_spectrum(H,2)
    ops=sim.observable_ops(4)
    obs=sim.expectations(state,ops)
    f=float(state_fidelity(states[0],state))
    f2=f+float(state_fidelity(states[1],state))
    # D-native resource measurement; RZZ is the frozen candidate's native ZZ form.
    qd,pd=sim.hva_ansatz(4,layers,zz_mode='rzz')
    bd=qd.assign_parameters(dict(zip(pd,theta)))
    m=sim.circuit_metrics(bd,sim.load_processor(str(ROOT/'processors/processor_D.json')))
    return {'N':4,'g':g,'layers':layers,'seed':seed,'energy':float(res.fun),
      'exact_E0':float(vals[0]),'energy_err':float(res.fun-vals[0]),'fidelity':f,'fidelity_2':f2,
      'mx':obs['mx'],'czz_nn':obs['czz_nn'],'mz2':obs['mz2'],'mz':obs['mz'],
      'optimizer_calls':cost.calls,'n_params':len(params),'two_q_on_D':m['cx'],
      'success':bool(res.success),'status':int(res.status),'message':str(res.message),
      'runtime_seconds':elapsed,'theta_json':json.dumps(theta.tolist(),separators=(',',':'))}


def write_rows(path,cols,rows):
    with path.open('w',newline='',encoding='utf-8') as f:
        w=csv.DictWriter(f,fieldnames=cols,lineterminator='\n');w.writeheader();w.writerows(rows)


def main():
    ROOT.joinpath('results/raw').mkdir(parents=True,exist_ok=True)
    ROOT.joinpath('results/tables').mkdir(parents=True,exist_ok=True)
    refs={}; exact_rows=[]
    for g in GS:
        H,meta,vals,states,ex=get_reference(g);refs[g]=(H,meta,vals,states,ex)
        row={'N':4,'g':g,'exact_E0':float(vals[0]),'exact_E1':float(vals[1]),
             'E0_metadata':float(meta['E0_exact']),'E1_metadata':float(meta['E1_exact']),
             'E0_abs_diff':abs(float(vals[0])-float(meta['E0_exact'])),
             'E1_abs_diff':abs(float(vals[1])-float(meta['E1_exact'])),
             'mx_exact':ex['mx'],'czz_nn_exact':ex['czz_nn'],'mz2_exact':ex['mz2'],'mz_exact':ex['mz']}
        exact_rows.append(row)
    write_rows(EXACT,list(exact_rows[0]),exact_rows)
    print('EXACT REFERENCES: 7/7 N=4 operator spectra matched metadata at abs tolerance 1e-9')
    # Pilot using seed 0, g=1, L=2. Compare COBYLA only if finite-difference pilot fails.
    pilot=minimize_one(refs[1.0][0],1.0,2,0,'L-BFGS-B')
    method='L-BFGS-B'
    if not pilot['success']:
        alt=minimize_one(refs[1.0][0],1.0,2,0,'COBYLA')
        print(f"PILOT L-BFGS-B success={pilot['success']} E={pilot['energy']:.12g}; COBYLA success={alt['success']} E={alt['energy']:.12g}")
        method='COBYLA' if (alt['success'] and alt['energy']<pilot['energy']) else 'L-BFGS-B'
        pilot=alt if method=='COBYLA' else pilot
    else:
        print(f"PILOT L-BFGS-B success=True E={pilot['energy']:.12g} calls={pilot['optimizer_calls']} seconds={pilot['runtime_seconds']:.3f}")
    print(f"SELECTED optimizer={method}; options={OPTIONS if method=='L-BFGS-B' else {'maxiter':2500,'tol':1e-8}}")
    done={};
    if RAW.exists():
        with RAW.open(newline='',encoding='utf-8') as f:
            for r in csv.DictReader(f): done[(float(r['g']),int(r['layers']),int(r['seed']))]=r
    if (1.0,2,0) not in done:
        done[(1.0,2,0)]=pilot
        # checkpoint pilot immediately
        write_rows(RAW,RAW_COLS,list(done.values()))
    for g in GS:
      for L in LAYERS:
       for seed in SEEDS:
        key=(g,L,seed)
        if key in done: continue
        r=minimize_one(refs[g][0],g,L,seed,method)
        done[key]=r
        # Persist every start as soon as it returns.
        write_rows(RAW,RAW_COLS,list(done.values()))
        print(f"RUN g={g:.2f} L={L} seed={seed} E={r['energy']:.12g} err={r['energy_err']:.4g} success={r['success']} calls={r['optimizer_calls']} sec={r['runtime_seconds']:.2f}",flush=True)
    # Deterministic aggregation: lowest final energy of the three required starts.
    agg=[]; layer_rows=[]
    for g in GS:
      exact=refs[g][4]
      for L in LAYERS:
        starts=[done[(g,L,s)] for s in SEEDS]
        winner=min(starts,key=lambda r:float(r['energy']))
        agg.append({'N':4,'g':g,'layers':L,'best_energy':winner['energy'],'exact_E0':winner['exact_E0'],
          'energy_err':winner['energy_err'],'fidelity':winner['fidelity'],'fidelity_2':winner['fidelity_2'],
          'mx':winner['mx'],'mx_exact':exact['mx'],'czz_nn':winner['czz_nn'],'czz_nn_exact':exact['czz_nn'],
          'mz2':winner['mz2'],'mz2_exact':exact['mz2'],'mz':winner['mz'],
          'optimizer_calls':winner['optimizer_calls'],'n_params':winner['n_params'],'two_q_on_D':winner['two_q_on_D']})
      for L in LAYERS:
        rows=[done[(g,L,s)] for s in SEEDS]
        win=min(rows,key=lambda r:float(r['energy']))
        layer_rows.append({'g':g,'layers':L,'best_seed':win['seed'],'best_energy':win['energy'],
          'energy_err':win['energy_err'],'abs_energy_err':abs(float(win['energy_err'])),
          'any_seed_success':any(str(r['success']).lower() in ('true','1') for r in rows),
          'optimizer_calls_winner':win['optimizer_calls']})
    write_rows(AGG,AGG_COLS,agg)
    layer_cols=list(layer_rows[0])
    write_rows(LAYER,layer_cols,layer_rows)
    print(f"RAW rows={len(done)}; aggregate rows={len(agg)}; layer-study rows={len(layer_rows)}")
    for g in GS:
        passing=[int(r['layers']) for r in layer_rows if float(r['g'])==g and float(r['abs_energy_err'])<1e-3]
        print(f"g={g:.2f} smallest_L_under_1e-3={min(passing) if passing else 'NOT REACHED through L=4'}")
    total=sum(float(r['runtime_seconds']) for r in done.values())
    print(f"sum optimizer wall-times={total:.2f}s; selected method={method}")

if __name__=='__main__':main()
