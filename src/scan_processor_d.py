#!/usr/bin/env python3
"""Stage-A compile/resource scan for the 12 predeclared Processor-D variants."""
from __future__ import annotations
import csv
import json
from collections import deque
from pathlib import Path
import sys

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from qiskit import transpile
import qff_sim as sim

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "results/tables/d_candidates.csv"
NAMES = {
    "ring": [(0,1),(0,5),(1,2),(2,3),(3,4),(4,5)],
    "path": [(0,1),(1,2),(2,3),(3,4),(4,5)],
    "grid_2x3": [(0,1),(0,3),(1,2),(1,4),(2,5),(3,4),(4,5)],
    "chorded_ring": [(0,1),(0,3),(0,5),(1,2),(2,3),(3,4),(4,5)],
}
BASES = {
    "CX": ["rz","sx","x","cx"],
    "CZ": ["rz","sx","x","cz"],
    "RZZ": ["rz","sx","x","rzz"],
}


def all_pairs_dist(n, edges):
    adj={i:set() for i in range(n)}
    for a,b in edges: adj[a].add(b); adj[b].add(a)
    ds={}
    for s in range(n):
        d={s:0}; q=deque([s])
        while q:
            u=q.popleft()
            for v in sorted(adj[u]):
                if v not in d: d[v]=d[u]+1; q.append(v)
        if len(d)!=n: return adj, ds, False
        for t,dist in d.items():
            if s<t: ds[(s,t)]=dist
    return adj, ds, True


def pair_info(n, edges):
    _,ds,connected=all_pairs_dist(n,edges)
    if not connected: return None,None,None,None
    adj=tuple(sorted(tuple(sorted(e)) for e in edges))
    adjacent=adj[0]
    far=max(ds.values())
    far_pair=min(pair for pair,dist in ds.items() if dist==far)
    return adjacent,ds[adjacent],far_pair,far


def twoq_metrics(qc):
    ops=qc.count_ops()
    twoq=sum(int(ops.get(g,0)) for g in ("cx","cz","rzz"))
    skip={"measure","barrier","reset"}
    depth=qc.depth(filter_function=lambda inst: inst.operation.name not in skip)
    two_depth=qc.depth(filter_function=lambda inst: inst.operation.num_qubits==2 and inst.operation.name not in skip)
    return twoq,depth,two_depth


METRIC_OUTPUTS = {
    "logical_2q": "logical_cx",
    "two_q": "cx",
    "depth": "depth",
    "two_q_depth": "two_q_depth",
    "swaps": "swaps",
    "overhead": "cx_overhead",
}


def compile_metric_record(qc, processor, size_label, metrics_fn=None):
    """Return metrics only for successful, executable circuit transpilation.

    Transpiler failures and explicit non-executable results are recorded as a
    false executable flag plus a diagnostic; they can never look feasible.
    `metrics_fn` is injectable for a lightweight regression test.
    """
    if metrics_fn is None:
        metrics_fn = sim.circuit_metrics
    try:
        metrics = metrics_fn(qc, processor)
        if not metrics.get("executable", False):
            reason = metrics.get("reason") or "circuit_metrics reported executable=False"
            return {f"{size_label}_executable": False,
                    **{f"{size_label}_{key}": "NA" for key in METRIC_OUTPUTS},
                    f"{size_label}_error": str(reason)}
        missing = [source for source in METRIC_OUTPUTS.values()
                   if source not in metrics or metrics[source] is None]
        if missing:
            raise ValueError(f"successful metrics missing required fields: {', '.join(missing)}")
        for source in METRIC_OUTPUTS.values():
            try:
                value = float(metrics[source])
            except (TypeError, ValueError) as exc:
                raise ValueError(f"successful metrics field {source} is not numeric: {metrics[source]!r}") from exc
            if not np.isfinite(value):
                raise ValueError(f"successful metrics field {source} is non-finite: {metrics[source]!r}")
        return {f"{size_label}_executable": True,
                **{f"{size_label}_{key}": metrics[source]
                   for key, source in METRIC_OUTPUTS.items()},
                f"{size_label}_error": ""}
    except Exception as exc:
        diagnostic = f"{type(exc).__name__}: {exc}"
        return {f"{size_label}_executable": False,
                **{f"{size_label}_{key}": "NA" for key in METRIC_OUTPUTS},
                f"{size_label}_error": diagnostic}


def _is_true(value):
    return value is True or str(value).strip().lower() in {"true", "1"}


def candidate_selectable(candidate):
    """Only candidates passing every required resource and Bell compile check qualify."""
    if not _is_true(candidate.get("valid")) or not _is_true(candidate.get("bell_all_compiled")):
        return False
    for label in ("n4", "n6"):
        if not _is_true(candidate.get(f"{label}_executable")):
            return False
        for field in ("two_q", "depth", "swaps"):
            try:
                value = float(candidate[f"{label}_{field}"])
            except (KeyError, TypeError, ValueError):
                return False
            if not np.isfinite(value):
                return False
    return True


def selection_key(candidate):
    """Preserved deterministic objective and tie-break ordering."""
    tie={"CX":0,"CZ":1,"RZZ":2}
    return (float(candidate["n4_two_q"]),float(candidate["n4_depth"]),
            float(candidate["far_bell_mean_two_q"]),float(candidate["graph_diameter"]),
            tie[candidate["basis"]],candidate["topology"])


def select_candidate(candidates):
    feasible=[candidate for candidate in candidates if candidate_selectable(candidate)]
    return min(feasible,key=selection_key) if feasible else None


def main():
    rows=[]
    candidates=[]
    # Measure A/B reference bottlenecks with the official helper, same N=4,L=2 HVA.
    hva4,_=sim.hva_ansatz(4,2,zz_mode="cx")
    A=sim.PROCESSOR_A
    B=sim.PROCESSOR_B
    ab={}
    for name,p in (("A",A),("B",B)):
        m=sim.circuit_metrics(hva4,p)
        ab[name]=m
    for topology,edges0 in NAMES.items():
      edges=[tuple(e) for e in edges0]
      adjacent,adj_dist,far_pair,diameter=pair_info(6,edges)
      for basis_name,basis in BASES.items():
        proc={"name":"Processor D candidate","team":"Chicken Leg Piece","problem_statement":"PS-S1",
              "num_qubits":6,"edges":edges,"basis_gates":basis,
              "error_rates":{"p1":0.001,"p2":0.005,"p_readout":0.01},
              "justification":"Predeclared topology and native-gate candidate for Stage A screening. This is a temporary test record, not a final proposal or performance claim. The graph and basis will be evaluated with the official validator, HVA resource metrics, and compile-only Bell circuits before a deterministic metrics-based selection is made."}
        valid_errors=sim.validate_processor_d(proc,4)
        candidate={"topology":topology,"basis":basis_name,"processor":proc,"valid":not valid_errors,
                   "validation_errors":"; ".join(valid_errors),"adjacent_pair":adjacent,
                   "adjacent_distance":adj_dist,"farthest_pair":far_pair,"graph_diameter":diameter}
        # HVA resource metrics for N=4 and N=6, L=2. A failed/partial
        # transpilation is recorded as non-executable and blocks selection.
        for n,label in ((4,"n4"),(6,"n6")):
            qc,_=sim.hva_ansatz(n,2,zz_mode="rzz" if basis_name=="RZZ" else "cx")
            candidate.update(compile_metric_record(qc,proc,label))
        # Forced-layout compile-only check of XX/YY/ZZ for adjacent and farthest pairs.
        compile_status=[]; bell_counts={}
        cm=sim.coupling_map_from_edges(edges,6)
        for pair_label,pair in (("adj",adjacent),("far",far_pair)):
            for basis_label in ("XX","YY","ZZ"):
                try:
                    tqc=transpile(sim.bell_circuit(basis_label),basis_gates=basis,
                        coupling_map=cm,initial_layout=list(pair),optimization_level=1,seed_transpiler=42)
                    count,depth,two_depth=twoq_metrics(tqc)
                    bell_counts[f"{pair_label}_{basis_label}_two_q"]=count
                    bell_counts[f"{pair_label}_{basis_label}_depth"]=depth
                    bell_counts[f"{pair_label}_{basis_label}_two_q_depth"]=two_depth
                    compile_status.append(f"{pair_label}_{basis_label}:OK")
                except Exception as exc:
                    compile_status.append(
                        f"{pair_label}_{basis_label}:FAIL:{type(exc).__name__}: {exc}"
                    )
        candidate["bell_compile_status"]="; ".join(compile_status)
        candidate["bell_all_compiled"]=all(x.endswith(":OK") for x in compile_status)
        candidate.update(bell_counts)
        candidate.update({
            "A_n4_hva_two_q":ab["A"].get("cx"),"A_n4_hva_depth":ab["A"].get("depth"),"A_n4_hva_swaps":ab["A"].get("swaps"),
            "B_n4_hva_two_q":ab["B"].get("cx"),"B_n4_hva_depth":ab["B"].get("depth"),"B_n4_hva_swaps":ab["B"].get("swaps")})
        candidates.append(candidate)
    # Bell-pair count is the mean generic 2-qubit count over XX/YY/ZZ compile checks.
    for c in candidates:
        for pair_label in ("adj","far"):
            vals=[c.get(f"{pair_label}_{b}_two_q") for b in ("XX","YY","ZZ")]
            c[f"{pair_label}_bell_mean_two_q"]=(sum(vals)/3 if all(isinstance(v,int) for v in vals) else float("inf"))
    feasible=[c for c in candidates if candidate_selectable(c)]
    dims=["n4_two_q","n4_depth","n4_swaps","adj_bell_mean_two_q","far_bell_mean_two_q","graph_diameter"]
    def dominates(a,b):
        av=[float(a[k]) for k in dims]; bv=[float(b[k]) for k in dims]
        return all(x<=y for x,y in zip(av,bv)) and any(x<y for x,y in zip(av,bv))
    pareto=[c for c in feasible if not any(dominates(o,c) for o in feasible if o is not c)]
    for c in candidates:
        c["pareto"]=c in pareto
    # Deterministic selection key: (n4_two_q, n4_depth, far_bell_mean_two_q,
    # graph_diameter, basis rank CX<CZ<RZZ, topology label ascending lexical).
    # That final name-order tie-break resolves otherwise identical candidates reproducibly.
    shortlist=sorted(pareto,key=selection_key)[:3]
    # At most three predeclared Pareto candidates get shot-based diagnostics.
    bell_results=[]
    for c in shortlist:
        p=c["processor"]
        for pair_label,pair in (("adjacent",c["adjacent_pair"]),("farthest",c["farthest_pair"])):
            for condition,noisy in (("ideal",False),("noisy",True)):
                result=sim.bell_experiment(p,pair,noisy,shots=4096)
                bell_results.append({"topology":c["topology"],"basis":c["basis"],"pair_label":pair_label,
                    "condition":condition,"pair":"-".join(map(str,pair)),"pair_distance":result["pair_distance"],
                    "two_qubit_gates":result["cx"],"XX":result["XX"],"XX_se":result["XX_se"],
                    "YY":result["YY"],"YY_se":result["YY_se"],"ZZ":result["ZZ"],"ZZ_se":result["ZZ_se"],
                    "fidelity":result["fidelity"],"fidelity_se":result["fidelity_se"]})
    chosen=select_candidate(pareto)
    if chosen is not None:
        chosen["processor"]["name"]="Processor D"
        a=ab["A"]; b=ab["B"]
        chosen["processor"]["justification"]=(
          f"Measured Stage A N=4, L=2 HVA resource counts were {a['cx']} two-qubit gates, depth {a['depth']}, and {a['swaps']} routing SWAPs on Processor A, versus {b['cx']} gates, depth {b['depth']}, and {b['swaps']} SWAPs on Processor B. "
          f"The selected {chosen['topology']} with {chosen['basis']} basis measured {chosen['n4_two_q']} two-qubit gates, depth {chosen['n4_depth']}, {chosen['n4_swaps']} SWAPs, and a graph diameter of {chosen['graph_diameter']}; it was selected by the predeclared Pareto and deterministic tie-break rule, not sampled fidelity. "
          "The assumed rates equal the official minimum and are synthetic benchmark inputs, not calibrated device data. The model does not represent device-specific gate variation, crosstalk, drift, leakage, or readout correlations. The design trades off the measured connectivity/resource profile against an idealized equal two-qubit error model."
        )
        (ROOT/"processors/processor_D.json").write_text(json.dumps(chosen["processor"],indent=2)+"\n",encoding="utf-8")
    # Candidate table, with all twelve variants and measured A/B reference columns.
    fields=[]
    for c in candidates:
        for k in c:
            if k not in ("processor",):
                if k not in fields: fields.append(k)
    OUT.parent.mkdir(parents=True,exist_ok=True)
    with OUT.open("w",newline="",encoding="utf-8") as f:
        w=csv.DictWriter(f,fieldnames=fields,extrasaction="ignore",lineterminator="\n"); w.writeheader();
        for c in candidates: w.writerow(c)
    if bell_results:
        pth=ROOT/"results/tables/d_shortlist_bell_diagnostics.csv"
        with pth.open("w",newline="",encoding="utf-8") as f:
            w=csv.DictWriter(f,fieldnames=list(bell_results[0]),lineterminator="\n"); w.writeheader(); w.writerows(bell_results)
    print(f"candidate rows={len(candidates)} feasible={len(feasible)} pareto={len(pareto)} shot-diagnostic candidates={len(shortlist)}")
    for c in sorted(candidates,key=lambda x:(x['topology'],x['basis'])):
        print(c['topology'],c['basis'],"valid",c['valid'],"Bell",c['bell_all_compiled'],
              "N4",c.get('n4_two_q'),c.get('n4_depth'),c.get('n4_swaps'),"diam",c['graph_diameter'],"Pareto",c['pareto'])
    if chosen:
        print("SELECTED",chosen['topology'],chosen['basis'],"justification words",len(chosen['processor']['justification'].split()))
    else:
        print("NO feasible Pareto candidate")

if __name__=="__main__": main()
