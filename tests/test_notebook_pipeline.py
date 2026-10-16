from pathlib import Path
import nbformat
ROOT=Path(__file__).resolve().parents[1]

def test_default_notebook_runs_only_the_canonical_stage1_pipeline():
    notebook=nbformat.read(ROOT/'main.ipynb',as_version=4)
    code='\n'.join(c.source for c in notebook.cells if c.cell_type=='code')
    assert 'scripts/reproduce.py' in code
    assert 'scripts/run_e4_ansatz_patterns.py' not in code
    assert 'make_manifest.py' not in code
    assert 'run_vqe_baseline_legacy.py' not in code
    assert 'run_custom_D_comparison.py' not in code and 'run_ring_stress.py' not in code
    assert 'run_density_fidelity.py' not in code

def test_notebook_is_standard_kernel_executed_and_error_free():
    notebook=nbformat.read(ROOT/'main.ipynb',as_version=4)
    assert notebook.metadata.kernelspec.name=='python3'
    assert notebook.metadata.kernelspec.language=='python'
    cells=[c for c in notebook.cells if c.cell_type=='code']
    assert cells and all(c.execution_count is not None for c in cells)
    assert not any(o.output_type=='error' for c in cells for o in c.outputs)
    markdown='\n'.join(c.source for c in notebook.cells if c.cell_type=='markdown').lower()
    assert 'magnetization axis and normalization remain undefined' in markdown
    assert 'no hardware was run' in markdown
    assert ('processor' + ' ' + chr(100)) not in markdown
