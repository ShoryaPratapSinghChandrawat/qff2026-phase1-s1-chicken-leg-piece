import hashlib,json,shutil,subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def test_manifest_is_byte_reproducible():
    subprocess.run([sys.executable,str(ROOT/'make_manifest.py')],cwd=ROOT,check=True,capture_output=True)
    first=(ROOT/'results/experiment_manifest.json').read_bytes()
    subprocess.run([sys.executable,str(ROOT/'make_manifest.py')],cwd=ROOT,check=True,capture_output=True)
    assert first==(ROOT/'results/experiment_manifest.json').read_bytes()
def test_manifest_paths_and_hashes_are_valid():
    m=json.loads((ROOT/'results/experiment_manifest.json').read_text())
    assert m['schema_version']==1 and 'PS-S1' in m['status']
    assert m['problem']['fields_g']==[.5,1.,1.5]
    assert m['problem']['energy_tolerance']==1e-6
    assert m['primary_architectures']['A_branch']['qubits']==5
    assert m['primary_architectures']['B_ref12']['qubits']==9
    assert m['input_files'] and m['generated_artifacts']
    assert 'legacy_artifacts' not in m
    for item in m['input_files']+m['generated_artifacts']:
        path=Path(item['path'])
        assert not path.is_absolute() and '..' not in path.parts
        target=ROOT/path
        if item['path']=='main.ipynb':
            import nbformat
            nb=nbformat.read(target,as_version=4)
            stable={'metadata':nb.metadata,'cells':[{'cell_type':c.cell_type,'metadata':{k:v for k,v in c.metadata.items() if k!='execution'},'source':c.source} for c in nb.cells]}
            actual=hashlib.sha256(json.dumps(stable,sort_keys=True,ensure_ascii=False).encode()).hexdigest()
            assert actual==item['sha256']
        else:
            assert target.is_file() and sha(target)==item['sha256']
    paths=[x['path'] for x in m['input_files']+m['generated_artifacts']]
    assert not any('uploads' in p or 'website' in p or 'extras/legacy' in p for p in paths)
def test_manifest_regenerates_in_a_clean_filesystem_copy(tmp_path):
    copy=tmp_path/'project-copy';shutil.copytree(ROOT,copy,ignore=shutil.ignore_patterns('.venv','__pycache__','.pytest_cache','*.pyc'))
    subprocess.run([sys.executable,str(copy/'make_manifest.py')],cwd=copy,check=True,capture_output=True,text=True)
    assert (copy/'results/experiment_manifest.json').read_bytes()==(ROOT/'results/experiment_manifest.json').read_bytes()
