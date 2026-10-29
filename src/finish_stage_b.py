#!/usr/bin/env python3
"""Produce official noisy S1 rows, A/B/D resources, and required Phase-2 figures."""
from __future__ import annotations
import csv,json,sys
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
import qff_sim as sim


def readcsv(p):
    with p.open(newline='',encoding='utf-8') as f:return list(csv.DictReader(f))
def writecsv(p,cols,rows):
    p.parent.mkdir(parents=True,exist_ok=True)
    with p.open('w',newline='',encoding='utf-8') as f:
        w=csv.DictWriter(f,fieldnames=cols,lineterminator='\n');w.writeheader();w.writerows(rows)

def instance(g):
    obj=json.loads((ROOT/'data/s1'/f'tfim_open_N4_g{g:.2f}.json').read_text(encoding='utf-8'))
    return obj,sim.SparsePauliOp.from_list([(lab,float(c)) for lab,c in obj['operator']])

def main():
    raw=readcsv(ROOT/'results/raw/s1_seed_runs.csv')
    agg=readcsv(ROOT/'results/tables/s1_results.csv')
    layers=readcsv(ROOT/'results/tables/layer_study.csv')
    exact=readcsv(ROOT/'results/tables/s1_exact_reference.csv')
    procD=sim.load_processor(str(ROOT/'processors/processor_D.json'))
    ops=sim.observable_ops(4)
    # Official density-matrix noisy runs: choose first threshold-passing layer; otherwise best actual layer.
    noisy_rows=[]; winner_details={}
    for g in (0.5,1.0,2.0):
        candidate=[r for r in layers if abs(float(r['g'])-g)<1e-9]
        passes=[r for r in candidate if float(r['abs_energy_err'])<1e-3]
        L=min(int(r['layers']) for r in passes) if passes else min(candidate,key=lambda r:float(r['abs_energy_err']))['layers']
        L=int(L)
        row=next(r for r in agg if abs(float(r['g'])-g)<1e-9 and int(r['layers'])==L)
        seed=min((r for r in raw if abs(float(r['g'])-g)<1e-9 and int(r['layers'])==L),key=lambda r:float(r['energy']))
        theta=np.asarray(json.loads(seed['theta_json']),dtype=float)
        qc,params=sim.hva_ansatz(4,L,zz_mode='rzz')
        bound=qc.assign_parameters(dict(zip(params,theta)))
        obj,H=instance(g)
        rho=sim.noisy_density_matrix(bound,procD)
        energy=float(np.real(rho.expectation_value(H)))
        noisy=sim.noisy_expectations(bound,ops,procD)
        fid=sim.noisy_state_fidelity(bound,sim.exact_spectrum(H,2)[1][0],procD)
        noisy_rows.append({'g':g,'layers':L,'mx_noisy':noisy['mx'],'czz_nn_noisy':noisy['czz_nn'],
          'mz2_noisy':noisy['mz2'],'energy_noisy':energy,'fidelity_noisy_dm':fid})
        winner_details[g]={'layers':L,'seed':int(seed['seed']),'ideal_energy':float(seed['energy']),
                           'energy_err':float(seed['energy_err']),'theta':theta.tolist()}
        print(f"NOISY g={g:.2f} L={L} seed={seed['seed']} E_noisy={energy:.12g} F_dm={fid:.8f}")
    noisy_cols=['g','layers','mx_noisy','czz_nn_noisy','mz2_noisy','energy_noisy','fidelity_noisy_dm']
    writecsv(ROOT/'results/tables/s1_noisy.csv',noisy_cols,noisy_rows)
    (ROOT/'results/raw/s1_noisy_selection.json').write_text(json.dumps(winner_details,indent=2)+'\n',encoding='utf-8')

    # Architecture resource rows: same selected N=4 HVA logical parameters on A/B/D, plus Bell auto-layout.
    hrow=next(r for r in agg if abs(float(r['g'])-1.0)<1e-9 and int(r['layers'])==3)
    seed=min((r for r in raw if abs(float(r['g'])-1.0)<1e-9 and int(r['layers'])==3),key=lambda r:float(r['energy']))
    theta=np.asarray(json.loads(seed['theta_json']),dtype=float)
    processors=[sim.PROCESSOR_A,sim.PROCESSOR_B,procD]
    resources=[]
    for p in processors:
        mode='rzz' if p['name']=='Processor D' and 'rzz' in p['basis_gates'] else 'cx'
        qc,params=sim.hva_ansatz(4,3,zz_mode=mode)
        bound=qc.assign_parameters(dict(zip(params,theta)))
        m=sim.circuit_metrics(bound,p)
        resources.append({'ps':'PS-S1','circuit_label':'s1_hva_g1.00_L3_best_seed'+str(seed['seed']),
          'processor':p['name'][-1],'executable':m.get('executable'),'logical_qubits':m.get('logical_qubits','NA'),
          'physical_qubits':p['num_qubits'],'logical_2q':m.get('logical_cx','NA'),'two_q':m.get('cx','NA'),
          'depth':m.get('depth','NA'),'two_q_depth':m.get('two_q_depth','NA'),'swaps':m.get('swaps','NA'),
          'routing_overhead_2q':m.get('cx_overhead','NA')})
        bell=sim.circuit_metrics(sim.bell_circuit('ZZ'),p)
        resources.append({'ps':'PS-S1','circuit_label':'bell_auto_layout_ZZ','processor':p['name'][-1],
          'executable':bell.get('executable'),'logical_qubits':bell.get('logical_qubits','NA'),
          'physical_qubits':p['num_qubits'],'logical_2q':bell.get('logical_cx','NA'),'two_q':bell.get('cx','NA'),
          'depth':bell.get('depth','NA'),'two_q_depth':bell.get('two_q_depth','NA'),'swaps':bell.get('swaps','NA'),
          'routing_overhead_2q':bell.get('cx_overhead','NA')})
    res_cols=['ps','circuit_label','processor','executable','logical_qubits','physical_qubits','logical_2q','two_q','depth','two_q_depth','swaps','routing_overhead_2q']
    writecsv(ROOT/'results/tables/resources.csv',res_cols,resources)

    # Required figures, all values sourced from generated CSV files.
    figdir=ROOT/'results/figures';figdir.mkdir(parents=True,exist_ok=True)
    # Phase observables, L=4 best-of-three vs exact.
    vqe4=[r for r in agg if int(r['layers'])==4]
    xs=[float(r['g']) for r in vqe4]
    erows=sorted(exact,key=lambda r:float(r['g']))
    fig,axs=plt.subplots(2,2,figsize=(11,8),constrained_layout=True)
    for ax,col,exactcol,title in [(axs[0,0],'mx','mx_exact','$m_x$'),(axs[0,1],'czz_nn','czz_nn_exact','$C_{zz}$ nearest-neighbour'),(axs[1,0],'mz2','mz2_exact','Mz squared / N squared')]:
        ax.plot(xs,[float(r[col]) for r in vqe4],'o-',label='VQE, L=4 (best of 3)')
        ax.plot([float(r['g']) for r in erows],[float(r[exactcol]) for r in erows],'s--',label='Exact')
        ax.set(xlabel='g',ylabel=title);ax.grid(alpha=.25);ax.legend(fontsize=8)
    axs[1,1].plot(xs,[float(r['best_energy']) for r in vqe4],'o-',label='VQE, L=4 (best of 3)')
    axs[1,1].plot([float(r['g']) for r in erows],[float(r['exact_E0']) for r in erows],'s--',label='Exact E0')
    axs[1,1].set(xlabel='g',ylabel='Energy');axs[1,1].grid(alpha=.25);axs[1,1].legend(fontsize=8)
    fig.suptitle('PS-S1 open-chain TFIM: phase observables and energy (N=4)')
    fig.savefig(figdir/'phase_observables_vs_g.png',dpi=170);plt.close(fig)
    # Layer study uses unmodified CSV errors; symlog handles exact/near-zero points.
    ls=readcsv(ROOT/'results/tables/layer_study.csv')
    fig,ax=plt.subplots(figsize=(9,5.5),constrained_layout=True)
    for g in sorted({float(r['g']) for r in ls}):
        rr=sorted((r for r in ls if float(r['g'])==g),key=lambda r:int(r['layers']))
        ax.plot([int(r['layers']) for r in rr],[float(r['abs_energy_err']) for r in rr],marker='o',label=f'g={g:g}')
    ax.set_yscale('symlog',linthresh=1e-5);ax.axhline(1e-3,color='black',ls='--',lw=1,label='1e-3 threshold')
    ax.set(xlabel='HVA layers L',ylabel='Absolute energy error (symlog; CSV values unchanged)',title='Layer-study convergence: best of three required seeds')
    ax.grid(alpha=.25);ax.legend(ncol=2,fontsize=8);fig.savefig(figdir/'layer_study_convergence.png',dpi=170);plt.close(fig)
    # Bell comparison: all four official rows.
    br=readcsv(ROOT/'results/tables/bell.csv')
    labels=[r['pair']+' '+r['condition'] for r in br]
    fig,axs=plt.subplots(1,2,figsize=(12,4.8),constrained_layout=True)
    x=np.arange(len(br));width=.24
    for j,key in enumerate(('XX','YY','ZZ')):axs[0].bar(x+(j-1)*width,[float(r[key]) for r in br],width,label=key)
    axs[0].set_xticks(x,labels,rotation=25,ha='right');axs[0].set_ylim(-1.1,1.1);axs[0].set_ylabel('Correlation');axs[0].legend();axs[0].grid(axis='y',alpha=.2)
    axs[1].bar(x,[float(r['fidelity']) for r in br],color=['#4c78a8' if r['condition']=='ideal' else '#f58518' for r in br])
    axs[1].set_xticks(x,labels,rotation=25,ha='right');axs[1].set_ylim(0,1.05);axs[1].set_ylabel('Bell-state fidelity');axs[1].grid(axis='y',alpha=.2)
    fig.suptitle('Processor D Bell verification (4096 shots per basis)')
    fig.savefig(figdir/'bell_comparison.png',dpi=170);plt.close(fig)
    # Selected D graph, deterministic circular layout.
    D=json.loads((ROOT/'processors/processor_D.json').read_text(encoding='utf-8'))
    n=D['num_qubits'];angles=np.linspace(np.pi/2,np.pi/2+2*np.pi,n,endpoint=False)
    pos={i:(np.cos(a),np.sin(a)) for i,a in enumerate(angles)}
    fig,ax=plt.subplots(figsize=(6,6),constrained_layout=True)
    for a,b in D['edges']:
        ax.plot([pos[a][0],pos[b][0]],[pos[a][1],pos[b][1]],color='#6b7280',lw=2,zorder=1)
    for q,(xx,yy) in pos.items():
        ax.scatter([xx],[yy],s=550,color='#dbeafe',edgecolor='#2563eb',linewidth=2,zorder=2)
        ax.text(xx,yy,str(q),ha='center',va='center',weight='bold',zorder=3)
    ax.set_title(f"Processor D — {D['num_qubits']} qubits, {D['basis_gates'][-1].upper()} native ZZ")
    ax.set_aspect('equal');ax.axis('off');fig.savefig(figdir/'processor_D_topology.png',dpi=170);plt.close(fig)
    # Noisy-vs-ideal energy for the required three g values.
    fig,ax=plt.subplots(figsize=(7,5),constrained_layout=True)
    ns=readcsv(ROOT/'results/tables/s1_noisy.csv')
    for r in ns:
        g=float(r['g']);ideal=winner_details[g]['ideal_energy']
        ax.scatter([g],[ideal],marker='o',s=65,label='Ideal VQE' if g==.5 else None)
        ax.scatter([g],[float(r['energy_noisy'])],marker='s',s=65,label='Noisy D density matrix' if g==.5 else None)
        ax.plot([g,g],[ideal,float(r['energy_noisy'])],color='#777',lw=1)
    ax.set(xlabel='g',ylabel='Energy',title='Selected converged-layer circuits: ideal vs noisy D')
    ax.grid(alpha=.25);ax.legend();fig.savefig(figdir/'noisy_vs_ideal_energy.png',dpi=170);plt.close(fig)
    print('WROTE s1_noisy.csv rows=3; resources.csv rows=6; required figures=5')

if __name__=='__main__':main()
