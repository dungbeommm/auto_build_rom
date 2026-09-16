from src.core.conditions import BuildContext, ConditionEvaluator

def test_build_context_single_rom_fields():
    ctx=BuildContext(); ctx.android_version=16; ctx.is_eu_rom=True; ctx.is_global_rom=False; ctx.rom_version='OS3.0.105'
    assert ctx.is_eu_rom is True
    assert ctx.is_global_rom is False
    assert ctx.rom_version=='OS3.0.105'

def test_conditions_use_rom_fields():
    ctx=BuildContext(); ctx.android_version=16; ctx.rom_version='OS3.0.105'; ev=ConditionEvaluator()
    assert ev.evaluate({'condition':{'android_version':{'min':15}}},ctx)
    assert ev.evaluate({'condition':{'rom_version':{'contains':'3.0.105'}}},ctx)
