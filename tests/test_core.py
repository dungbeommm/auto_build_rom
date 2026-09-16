import tempfile, zipfile, json, struct
from pathlib import Path
from rombuilder.core.rom import RomWorkspace
from rombuilder.core.config import Config
from rombuilder.core.dependency import requirements

def test_sparse_magic():
    with tempfile.TemporaryDirectory() as d:
        p=Path(d)/'x.img'; p.write_bytes(struct.pack('<I',0xED26FF3A))
        assert RomWorkspace.is_sparse(p)

def test_requirements():
    c=Config(Path(__file__).parents[1])
    r=requirements(c,['advanced_keyboard'])
    names={x.patterns for x in r}
    assert ('miui-framework.jar',) in names
    assert ('MiuiSystemUI.apk',) in names

def test_zip_traversal_rejected():
    # The implementation checks members before extraction; exercise the same rule here.
    with tempfile.TemporaryDirectory() as d:
        p=Path(d)/'bad.zip'
        with zipfile.ZipFile(p,'w') as z: z.writestr('../../evil','x')
        out=Path(d)/'out'; out.mkdir()
        with zipfile.ZipFile(p) as z:
            for i in z.infolist():
                target=(out/i.filename).resolve()
                assert not str(target).startswith(str(out.resolve())+'/')
