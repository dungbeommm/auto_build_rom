from src.app import workflow

def test_resolve_work_paths(tmp_path):
    root, rom, target = workflow.resolve_work_paths(tmp_path/'build')
    assert root.name=='build'
    assert rom.name=='rom'
    assert target.name=='target'
