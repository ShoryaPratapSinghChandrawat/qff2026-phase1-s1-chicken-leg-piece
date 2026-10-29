#!/usr/bin/env python3
"""Stage-C exact finite-size diagnostics and hypothetical p2-only sensitivity."""
from __future__ import annotations
import csv,json,sys
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from qiskit import transpile
from qiskit.quantum_info import SparsePauliOp,Statevector,partial_trace,state_fidelity,DensityMatrix
from qiskit_aer import AerSimulator
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
import qff_sim as sim

def readcsv(p):
    with p.open(newline='',encoding='utf-8') as f:return list(csv.DictReader(f))
def writecsv(p,cols,rows):
    p.parent.mkdir(parents=True,exist_ok=True)
    with p.open('w',newline='',encoding='utf-8') as f:
        w=csv.DictWriter(f,fieldnames=cols,lineterminator='\n');w.writeheader();w.writerows(rows)
def load_instance(n,g):
    p=ROOT/'data/s1'/f'tfim_open_N{n}_g{g:.2f}.json'
    obj=json.loads(p.read_text(encoding='utf-8'))
    H=SparsePauliOp.from_list([(lab,float(c)) for lab,c in obj['operator']])
    return obj,H

def main():
    # Exact gap + half-chain entropy for supplied N=4 and N=6 operators.
    crit=[]
    for n in (4,6):
        for g in (0.25,0.50,0.75,1.00,1.25,1.50,2.00):
            obj,H=load_instance(n,g)
            vals,states=sim.exact_spectrum(H,2)
            m0=abs(float(vals[0])-float(obj['meta']['E0_exact']))
            m1=abs(float(vals[1])-float(obj['meta']['E1_exact']))
            if m0>1e-9 or m1>1e-9: raise RuntimeError(f'exact N={n} g={g} metadata mismatch E0={m0} E1={m1}')
            traced=list(range(n//2,n))
            reduced=partial_trace(states[0],traced)
            eig=np.linalg.eigvalsh(np.asarray(reduced.data,dtype=complex)).real
            eig=np.clip(eig,0.0,None)
            eig=eig[eig>1e-12]
            entropy=float(-np.sum(eig*np.log2(eig)))
            crit.append({'N':n,'g':g,'E0_exact':float(vals[0]),'E1_exact':float(vals[1]),
                'gap':float(vals[1]-vals[0]),'half_chain_entropy_bits':entropy,
                'E0_metadata_abs_diff':m0,'E1_metadata_abs_diff':m1})
    crit_cols=list(crit[0])
    writecsv(ROOT/'results/additional/criticality.csv',crit_cols,crit)
    fig,axs=plt.subplots(1,2,figsize=(10,4.7),constrained_layout=True)
    for n in (4,6):
        rr=sorted((r for r in crit if r['N']==n),key=lambda r:r['g'])
        axs[0].plot([r['g'] for r in rr],[r['gap'] for r in rr],marker='o',label=f'N={n}')
        axs[1].plot([r['g'] for r in rr],[r['half_chain_entropy_bits'] for r in rr],marker='s',label=f'N={n}')
    axs[0].set(xlabel='g',ylabel='Finite-size gap E1 - E0',title='Exact spectral gap')
    axs[1].set(xlabel='g',ylabel='Half-chain von Neumann entropy (bits)',title='Exact ground-state entanglement')
    for ax in axs:ax.grid(alpha=.25);ax.legend()
    fig.suptitle('Finite-size PS-S1 diagnostics (exact supplied instances)')
    fig.savefig(ROOT/'results/figures/criticality_gap_entropy.png',dpi=170);plt.close(fig)
    print(f'CRITICALITY rows={len(crit)}; N=4,N=6 exact spectra and half-chain entropies saved')

    # p2-only synthetic sensitivity. Explicit custom density-matrix helper; official helpers untouched.
    p=sim.load_processor(str(ROOT/'processors/processor_D.json'))
    raw=readcsv(ROOT/'results/raw/s1_seed_runs.csv')
    official=readcsv(ROOT/'results/tables/s1_noisy.csv')
    selections=json.loads((ROOT/'results/raw/s1_noisy_selection.json').read_text(encoding='utf-8'))
    alphas=[1.0,1.25,1.5,2.0]
    sens=[]
    for g in (0.5,1.0,2.0):
        sel=selections[str(g)] if str(g) in selections else selections.get(str(float(g)))
        if sel is None:
            # JSON float keys are strings like "0.5".
            sel=selections[f'{g:.1f}']
        L=int(sel['layers']);seed=int(sel['seed']);theta=np.asarray(sel['theta'],dtype=float)
        obj,H=load_instance(4,g)
        qc,params=sim.hva_ansatz(4,L,zz_mode='rzz')
        circuit=qc.assign_parameters(dict(zip(params,theta)))
        baseline_off=next(r for r in official if abs(float(r['g'])-g)<1e-9)
        metrics=sim.circuit_metrics(circuit,p)
        for alpha in alphas:
            tqc=sim.transpile_for(circuit,p)
            _,final=sim._layout_maps(tqc,circuit.num_qubits)
            run=tqc.copy();run.save_density_matrix(qubits=final,label='rho')
            nm=sim.official_noise_model(p1=0.001,p2=0.005*alpha,p_ro=0.01)
            aer=AerSimulator(method='density_matrix',noise_model=nm)
            rho=DensityMatrix(aer.run(run).result().data()['rho'])
            energy=float(np.real(rho.expectation_value(H)))
            fid=float(state_fidelity(sim.exact_spectrum(H,2)[1][0],rho))
            row={'g':g,'layers':L,'seed':seed,'alpha_p2':alpha,'p1':0.001,'p2':0.005*alpha,'p_readout':0.01,
                'energy_noisy':energy,'energy_error_noisy':energy-float(obj['meta']['E0_exact']),
                'fidelity_noisy_dm':fid,'two_q_on_D':metrics['cx'],'depth_on_D':metrics['depth'],
                'swaps_on_D':metrics['swaps'],'routing_overhead_2q':metrics['cx_overhead'],
                'synthetic_model':'hypothetical two-qubit error-rate sensitivity; not measured crosstalk'}
            sens.append(row)
            if alpha==1.0:
                de=abs(energy-float(baseline_off['energy_noisy']))
                df=abs(fid-float(baseline_off['fidelity_noisy_dm']))
                if de>1e-10 or df>1e-10: raise RuntimeError(f'alpha=1 baseline mismatch g={g}: dE={de} dF={df}')
                print(f'P2 alpha=1 validation g={g:g}: |dE|={de:.3e} |dF|={df:.3e}')
    sens_cols=list(sens[0])
    writecsv(ROOT/'results/additional/p2_sensitivity.csv',sens_cols,sens)
    fig,axs=plt.subplots(1,2,figsize=(10,4.8),constrained_layout=True)
    for g in (0.5,1.0,2.0):
        rr=sorted((r for r in sens if r['g']==g),key=lambda r:r['alpha_p2'])
        axs[0].plot([r['alpha_p2'] for r in rr],[r['energy_error_noisy'] for r in rr],marker='o',label=f'g={g:g}')
        axs[1].plot([r['alpha_p2'] for r in rr],[r['fidelity_noisy_dm'] for r in rr],marker='s',label=f'g={g:g}')
    axs[0].set(xlabel='p2 multiplier alpha (p1/readout fixed)',ylabel='Noisy energy error',title='Hypothetical p2-only sensitivity')
    axs[1].set(xlabel='p2 multiplier alpha (p1/readout fixed)',ylabel='Noisy density-matrix fidelity',title='Gate-noise sensitivity')
    for ax in axs:ax.grid(alpha=.25);ax.legend()
    fig.suptitle('Synthetic noise sweep only — not hardware calibration or measured crosstalk')
    fig.savefig(ROOT/'results/figures/p2_sensitivity.png',dpi=170);plt.close(fig)
    print(f'P2 sensitivity rows={len(sens)}; alpha=1 validated against official baseline for all three g values')

if __name__=='__main__':main()
