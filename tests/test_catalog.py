import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def test_targets_have_known_features():
    t=json.loads((ROOT/'config/targets.json').read_text())
    m=json.loads((ROOT/'config/mods.json').read_text())['features']
    for group in t.values():
        for item in group.values():
            for f in item['features']: assert f in m

def test_boot_features_absent():
    m=json.loads((ROOT/'config/mods.json').read_text())['features']
    forbidden=('vendor_boot','boot_patch','selinux_boot','fake_locked_bootloader')
    for k in m: assert not any(x in k for x in forbidden)

def test_exact_core_targets():
    t=json.loads((ROOT/'config/targets.json').read_text())
    assert 'miui_systemui' in t['apk']
    assert 'framework' in t['jar'] and 'services' in t['jar']
