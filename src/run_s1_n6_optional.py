#!/usr/bin/env python3
"""Optional, supplemental PS-S1 N=6 exact-reference and VQE tier.

Never writes to the required N=4 result tables. Uses the same locked g grid,
seeds 0..2, HVA initialization and optimizer settings as src/run_s1.py.
"""
from __future__ import annotations
import csv, json, math, sys, time
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from scipy.optimize import minimize
from qiskit.quantum_info import SparsePauliOp, Statevector, state_fidelity
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
import qff_sim as sim
GS=[0.25,0.50,0.75,1.00,1.25,1.50,2.00]
SEEDS=[0,1,2]
LAYERS=range(1,9)
OPTIONS={"maxiter":250,"maxfun":30000,"ftol":1e-12,"gtol":1e-7}
OUT=ROOT/'results/additional'
RAW=OUT/'s1_n6_seed_runs.csv'
EXACT=OUT/'s1_n6_exact_reference.csv'
AGG=OUT/'s1_n6_results.csv'
LAYER=OUT/'s1_n6_layer_study.csv'
RAW_COLS=['N','g','layers','seed','energy','exact_E0','exact_E1','energy_err','fidelity','fidelity_2','mx','czz_nn','mz2','mz','optimizer_calls','n_params','success','status','message','runtime_seconds','theta_json']

def minimal_threshold_layer(layer_rows, g, threshold=1e-3):
    """Return the smallest tested layer with a strict absolute-error threshold hit."""
    passing = [int(row['layers']) for row in layer_rows
               if float(row['g']) == float(g) and abs(float(row['energy_err'])) < threshold]
    return min(passing) if passing else None

def write(path, cols, rows):
    with path.open('w',newline='',encoding='utf-8') as f:
        w=csv.DictWriter(f,fieldnames=cols,lineterminator='\n');w.writeheader();w.writerows(rows)

def main():
    OUT.mkdir(parents=True,exist_ok=True)
    refs={}; erows=[]
    for g in GS:
        name=f'tfim_open_N6_g{g:.2f}.json'; obj=json.loads((ROOT/'data/s1'/name).read_text())
        H=SparsePauliOp.from_list([(lab,float(c)) for lab,c in obj['operator']])
        vals,states=sim.exact_spectrum(H,2)
        d0=abs(float(vals[0])-float(obj['meta']['E0_exact']));d1=abs(float(vals[1])-float(obj['meta']['E1_exact']))
        if d0>1e-9 or d1>1e-9: raise RuntimeError(f'{name}: exact metadata mismatch E0={d0} E1={d1}')
        ex=sim.expectations(states[0],sim.observable_ops(6))
        refs[g]=(H,vals,states,ex)
        erows.append({'N':6,'g':g,'exact_E0':float(vals[0]),'exact_E1':float(vals[1]),'E0_metadata':float(obj['meta']['E0_exact']),'E1_metadata':float(obj['meta']['E1_exact']),'E0_abs_diff':d0,'E1_abs_diff':d1,'mx_exact':ex['mx'],'czz_nn_exact':ex['czz_nn'],'mz2_exact':ex['mz2'],'mz_exact':ex['mz']})
    write(EXACT,list(erows[0]),erows)
    done={}
    if RAW.exists():
        with RAW.open(newline='',encoding='utf-8') as f:
            for r in csv.DictReader(f): done[(float(r['g']),int(r['layers']),int(r['seed']))]=r
    print(f'EXACT N=6 references validated {len(erows)}/7 at 1e-9; resuming {len(done)} starts',flush=True)
    for g in GS:
      H,vals,states,ex=refs[g]
      for L in LAYERS:
       qc,params=sim.hva_ansatz(6,L,zz_mode='cx')
       for seed in SEEDS:
        key=(g,L,seed)
        if key in done: continue
        x0=np.random.default_rng(seed).uniform(-np.pi,np.pi,len(params))
        cost=sim.CountedCost(lambda x:sim.energy_statevector(qc.assign_parameters(dict(zip(params,x))),H))
        t0=time.perf_counter()
        res=minimize(cost,x0,method='L-BFGS-B',jac='3-point',options=OPTIONS)
        elapsed=time.perf_counter()-t0
        theta=np.asarray(res.x,dtype=float); state=Statevector(qc.assign_parameters(dict(zip(params,theta))))
        obs=sim.expectations(state,sim.observable_ops(6)); f=float(state_fidelity(states[0],state)); f2=f+float(state_fidelity(states[1],state))
        row={'N':6,'g':g,'layers':L,'seed':seed,'energy':float(res.fun),'exact_E0':float(vals[0]),'exact_E1':float(vals[1]),'energy_err':float(res.fun-float(vals[0])),'fidelity':f,'fidelity_2':f2,'mx':obs['mx'],'czz_nn':obs['czz_nn'],'mz2':obs['mz2'],'mz':obs['mz'],'optimizer_calls':cost.calls,'n_params':len(params),'success':bool(res.success),'status':int(res.status),'message':str(res.message),'runtime_seconds':elapsed,'theta_json':json.dumps(theta.tolist(),separators=(',',':'))}
        done[key]=row; write(RAW,RAW_COLS,list(done.values()))
        print(f"N6 g={g:.2f} L={L} seed={seed} Eerr={row['energy_err']:.5g} success={row['success']} calls={cost.calls} sec={elapsed:.2f}",flush=True)
    ag=[];lr=[]
    for g in GS:
      ex=refs[g][3]
      for L in LAYERS:
        rr=[done[(g,L,s)] for s in SEEDS];win=min(rr,key=lambda x:float(x['energy']))
        ag.append({'N':6,'g':g,'layers':L,'best_seed':int(win['seed']),'best_energy':float(win['energy']),'exact_E0':float(win['exact_E0']),'energy_err':float(win['energy_err']),'fidelity':float(win['fidelity']),'fidelity_2':float(win['fidelity_2']),'mx':float(win['mx']),'mx_exact':ex['mx'],'czz_nn':float(win['czz_nn']),'czz_nn_exact':ex['czz_nn'],'mz2':float(win['mz2']),'mz2_exact':ex['mz2'],'mz':float(win['mz']),'optimizer_calls':int(win['optimizer_calls']),'n_params':int(win['n_params'])})
        lr.append({'N':6,'g':g,'layers':L,'best_seed':int(win['seed']),'best_energy':float(win['energy']),'energy_err':float(win['energy_err']),'abs_energy_err':abs(float(win['energy_err'])),'any_seed_success':any(str(r['success']).strip().lower() in ('true','1') for r in rr),'optimizer_calls_winner':int(win['optimizer_calls'])})
    write(AGG,list(ag[0]),ag);write(LAYER,list(lr[0]),lr)
    failed=[r for r in done.values() if str(r['success']).lower() not in ('true','1')]
    print(f'OPTIONAL N=6 sweep complete: raw={len(done)} aggregates={len(ag)} layer_rows={len(lr)} failed_starts_retained={len(failed)} total_optimizer_seconds={sum(float(r["runtime_seconds"]) for r in done.values()):.2f}',flush=True)
    minimal=[]
    resource_rows=[]
    p_b=sim.PROCESSOR_B
    p_d=sim.load_processor(str(ROOT/'processors/processor_D.json'))
    for g in GS:
        layer_rows=[r for r in lr if float(r['g'])==g]
        chosen_layer=minimal_threshold_layer(layer_rows,g)
        passing=[r for r in layer_rows if float(r['g'])==g and float(r['abs_energy_err'])<1e-3]
        if chosen_layer is not None:
            candidates=[done[(g,chosen_layer,seed)] for seed in SEEDS]
            winner=min(candidates,key=lambda r:float(r['energy']))
            role='first_threshold_layer'
            min_field=chosen_layer
        else:
            winner=min((r for key,r in done.items() if key[0]==g),key=lambda r:abs(float(r['energy_err'])))
            chosen_layer=int(winner['layers'])
            role='best_available_threshold_not_reached'
            min_field='NOT_REACHED_L<=8'
        chosen_seed=int(winner['seed'])
        selected_error=float(winner['energy_err'])
        selected_success=str(winner['success']).lower() in ('true','1')
        at_layer=[done[(g,chosen_layer,seed)] for seed in SEEDS]
        minimal.append({
            'scope':'additional, not part of the official required results',
            'N':6,'g':g,'minimal_L_abs_err_lt_1e-3':min_field,
            'threshold_met_within_L1_to_L8':bool(passing),'selected_seed':chosen_seed,
            'selected_L':chosen_layer,'selected_energy_error':selected_error,
            'selected_optimizer_success':selected_success,
            'failed_starts_at_selected_L':sum(str(r['success']).lower() not in ('true','1') for r in at_layer),
            'selection_rule':'lowest L meeting strict threshold; best energy among its seeds; otherwise smallest absolute error over L=1..8 and seeds 0..2'
        })
        print(f'N6 g={g:.2f}: smallest L <1e-3 = {min_field}; selected seed={chosen_seed} success={selected_success}')
        for proc,mode in ((p_b,'cx'),(p_d,'rzz')):
            qc,params=sim.hva_ansatz(6,chosen_layer,zz_mode=mode)
            bound=qc.assign_parameters(dict(zip(params,json.loads(winner['theta_json']))))
            metrics=sim.circuit_metrics(bound,proc)
            if not metrics.get('executable'):
                raise RuntimeError(f'Processor {proc["name"]} cannot compile selected N=6 circuit for g={g}')
            resource_rows.append({
                'scope':'additional, not part of the official required results',
                'circuit_label':f'n6_hva_g{g:.2f}_L{chosen_layer}_best_seed{chosen_seed}_{mode}',
                'N':6,'g':g,'layers':chosen_layer,'seed':chosen_seed,
                'selection_status':role,'processor':proc['name'][-1],'zz_mode':mode,
                'executable':True,'reason':'','logical_qubits':metrics['logical_qubits'],
                'physical_qubits':metrics['physical_qubits'],'logical_2q':metrics['logical_cx'],
                'two_q':metrics['cx'],'depth':metrics['depth'],'two_q_depth':metrics['two_q_depth'],
                'swaps':metrics['swaps'],'routing_overhead_2q':metrics['cx_overhead'],
                'selected_energy_error':selected_error,'optimizer_success':selected_success
            })
    minimal_cols=list(minimal[0])
    write(OUT/'s1_n6_minimal_layers.csv',minimal_cols,minimal)
    capacity={
        'scope':'additional, not part of the official required results',
        'circuit_label':'n6_optional_capacity_check','N':6,'g':'all','layers':'N/A','seed':'N/A',
        'selection_status':'processor_capacity','processor':'A','zz_mode':'N/A','executable':False,
        'reason':'not executable: needs 6 qubits, has 5','logical_qubits':6,'physical_qubits':5,
        'logical_2q':'NA','two_q':'NA','depth':'NA','two_q_depth':'NA','swaps':'NA',
        'routing_overhead_2q':'NA','selected_energy_error':'NA','optimizer_success':'NA'
    }
    resource_rows.insert(0,capacity)
    resource_cols=list(resource_rows[0])
    write(OUT/'s1_n6_resources.csv',resource_cols,resource_rows)
    fig,ax=plt.subplots(figsize=(9,5.5),constrained_layout=True)
    for g in GS:
        rr=sorted((r for r in lr if float(r['g'])==g),key=lambda r:int(r['layers']))
        ys=[max(float(r['abs_energy_err']),1e-16) for r in rr]
        ax.plot([int(r['layers']) for r in rr],ys,marker='o',label=f'g={g:g}')
    ax.axhline(1e-3,color='black',linestyle='--',linewidth=1,label='strict threshold 1e-3')
    ax.set_yscale('log');ax.set_xticks(list(LAYERS))
    ax.set(xlabel='HVA layers L (N=6)',ylabel='Absolute energy error',
        title='Additional, not part of the official required results: N=6 VQE layer study (seeds 0,1,2)')
    ax.grid(True,which='both',alpha=.25);ax.legend(ncol=2,fontsize=8)
    fig.savefig(ROOT/'results/figures/additional_n6_layer_study.png',dpi=300)
    plt.close(fig)
    print(f'ADDITIONAL N=6 resources: B/D rows={len(resource_rows)-1}; Processor A: {capacity["reason"]}')
    print(f'ADDITIONAL N=6 figure saved at 300 DPI: results/figures/additional_n6_layer_study.png')
if __name__=='__main__':main()
