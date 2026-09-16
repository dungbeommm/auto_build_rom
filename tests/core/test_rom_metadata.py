from pathlib import Path
from types import SimpleNamespace
from src.core.rom_metadata import populate_rom_metadata

def test_metadata_comes_from_single_rom(tmp_path):
    feat=tmp_path/'extracted/product/etc/device_features'; feat.mkdir(parents=True)
    (feat/'fuxi.xml').write_text('<xml/>')
    rom=SimpleNamespace(
        path=tmp_path/'rom.zip', extracted_dir=tmp_path/'extracted',
        get_prop=lambda key, default='': {
            'ro.system.build.version.release':'16', 'ro.vendor.build.version.sdk':'36',
            'ro.mi.os.version.incremental':'OS3.0.1', 'ro.build.ab_update':'true',
            'ro.build.version.security_patch':'2026-09-01', 'ro.product.mod_device':'fuxi_global',
            'ro.product.vendor.device':'fuxi', 'ro.product.name_for_attestation':'fuxi'
        }.get(key, default))
    ctx=SimpleNamespace(rom=rom,logger=__import__('logging').getLogger('test'))
    populate_rom_metadata(ctx)
    assert ctx.rom_code=='fuxi'
    assert ctx.android_version=='16'
    assert ctx.android_sdk=='36'
    assert ctx.target_rom_version=='OS3.0.1'
    assert ctx.is_ab_device is True
