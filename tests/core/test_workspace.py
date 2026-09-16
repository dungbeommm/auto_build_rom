from types import SimpleNamespace
from src.core.workspace import build_partition_layout

def test_partition_layout_uses_one_rom():
    rom=object(); ctx=SimpleNamespace(rom=rom)
    layout=build_partition_layout(ctx)
    assert set(layout)=={'vendor','odm','vendor_dlkm','odm_dlkm','system_dlkm','system','system_ext','product','mi_ext','product_dlkm'}
    assert all(value is rom for value in layout.values())
