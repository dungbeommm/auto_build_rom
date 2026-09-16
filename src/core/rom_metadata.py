"""Metadata extraction for the input ROM."""
from __future__ import annotations
from pathlib import Path
from typing import TYPE_CHECKING, cast
if TYPE_CHECKING:
    from src.core.context import RomContext

def populate_rom_metadata(ctx:"RomContext")->None:
    r=ctx.rom; ctx.logger.info('Fetching ROM build props...')
    ctx.android_version=r.get_prop('ro.system.build.version.release') or r.get_prop('ro.build.version.release') or '0'
    ctx.android_sdk=r.get_prop('ro.vendor.build.version.sdk') or r.get_prop('ro.build.version.sdk') or '0'
    version=r.get_prop('ro.mi.os.version.incremental') or r.get_prop('ro.build.version.incremental','') or ''
    ctx.target_rom_version=version
    ctx.rom_code=_detect_rom_code(ctx)
    ctx.is_ab_device=(r.get_prop('ro.build.ab_update','').lower()=='true')
    ctx.security_patch=r.get_prop('ro.build.version.security_patch') or 'Unknown'
    mod=(r.get_prop('ro.product.mod_device','') or '').lower()
    host=(r.get_prop('ro.build.host','') or '').lower()
    ctx.region=_detect_region(mod,r.get_prop('ro.miui.build.region',''),r.get_prop('ro.product.locale',''))
    ctx.is_eu_rom=('xiaomi.eu' in r.path.name.lower() or 'xiaomi.eu' in host or 'xiaomi.eu' in mod)
    ctx.is_global_rom=('_global' in mod and not ctx.is_eu_rom)
    ctx.global_region=_detect_global_region(mod,ctx.is_eu_rom)
    ctx.logger.info('Android=%s SDK=%s ROM=%s Device=%s SecurityPatch=%s',ctx.android_version,ctx.android_sdk,version,ctx.rom_code,ctx.security_patch)

def _detect_rom_code(ctx:"RomContext")->str:
    try:
        d=ctx.rom.extracted_dir/'product/etc/device_features'; xml=cast(Path,next(d.glob('*.xml'))); return xml.stem
    except StopIteration: return ctx.rom.get_prop('ro.product.vendor.device') or 'unknown'
    except Exception as exc: ctx.logger.warning('Device code detection failed: %s',exc); return 'unknown'

def _detect_region(mod:str,build_region:str,locale:str)->str:
    value=(mod or build_region or locale or '').lower()
    for token,region in (('_eea','eea'),('_ru','ru'),('_id','id'),('_tr','tr'),('_tw','tw'),('_in','in'),('_global','global'),('cn','cn')):
        if token in value: return region
    return ''

def _detect_global_region(mod:str,is_eu:bool)->str:
    if is_eu or not mod: return ''
    for suffix,region in (('_lm_cr_global','lm_cr'),('_eea_global','eea'),('_ru_global','ru'),('_id_global','id'),('_tr_global','tr'),('_tw_global','tw'),('_in_global','in'),('_global','global')):
        if mod.endswith(suffix): return region
    return ''
