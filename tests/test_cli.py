from src.app.cli import parse_args

def test_cli_accepts_single_rom(tmp_path):
    rom=tmp_path/'rom.zip'; rom.write_bytes(b'not-a-real-zip')
    args=parse_args(['--rom',str(rom),'--phases','system,apk','framework'])
    assert args.rom == str(rom)
    assert args.phases == ['system','apk','framework']
