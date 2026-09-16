from pathlib import Path
from types import SimpleNamespace
from src.core.context import RomContext

def test_context_initialization(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    rom=SimpleNamespace(extracted_dir=tmp_path/'rom/extracted',path=tmp_path/'rom.zip')
    ctx=RomContext(rom,tmp_path/'target')
    assert ctx.rom is rom
    assert ctx.target_dir==Path(tmp_path/'target').resolve()
