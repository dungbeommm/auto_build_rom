"""End-to-end single-ROM modification workflow."""
from __future__ import annotations
import json, logging
from pathlib import Path
from types import SimpleNamespace
from src.app.bootstrap import clean_work_dir, initialize_cache_manager
from src.app.diff_report import collect_artifact_state, generate_diff_report, save_diff_report
from src.app.preflight import run_preflight, save_preflight_report
from src.app.snapshots import StageSnapshotManager
from src.core.config_loader import load_device_config
from src.core.context import RomContext
from src.core.device_auto_config import get_or_create_device_config
from src.core.modifiers import FirmwareModifier, FrameworkModifier, RomModifier, UnifiedModifier
from src.core.packer import Repacker
from src.core.rom import RomPackage
from src.utils.downloader import RomDownloader
from src.utils.otatools_manager import OtaToolsManager
DEFAULT_PHASES=['system','apk','framework','firmware','repack']
REPACK_CHECKPOINT_NAME='repack-context.json'

def resolve_work_paths(work_dir):
    root=Path(work_dir).resolve(); return root,root/'rom',root/'target'

def resolve_remote_input(args,logger):
    if str(args.rom).startswith(('http://','https://')):
        logger.info('Downloading ROM...'); args.rom=str(RomDownloader().download(args.rom))
    if args.eu_bundle and str(args.eu_bundle).startswith(('http://','https://')):
        logger.info('Downloading EU bundle...'); args.eu_bundle=str(RomDownloader().download(args.eu_bundle))

def log_run_configuration(logger,args,cache_enabled):
    logger.info('='*70); logger.info('HyperOS ROM Modifier'); logger.info('='*70); logger.info('ROM: %s',args.rom); logger.info('KSU: %s',args.ksu); logger.info('Work Dir: %s',args.work_dir); logger.info('Phases: %s',', '.join(args.phases) if args.phases else 'all'); logger.info('Cache: %s','Enabled' if cache_enabled else 'Disabled'); logger.info('='*70)

def determine_pack_settings(args,ctx,logger):
    ctx.enable_ksu=bool(args.ksu or ctx.device_config.get('ksu',{}).get('enable',False))
    pack_cfg=ctx.device_config.get('pack',{}) if isinstance(ctx.device_config.get('pack',{}),dict) else {}
    ctx.enable_custom_avb_chain=bool(args.custom_avb_chain or pack_cfg.get('custom_avb_chain',False))
    if args.avb_key: ctx.avb_key_path=Path(args.avb_key).resolve()
    pack_type=args.pack_type or pack_cfg.get('type','payload'); fs_type=args.fs_type or pack_cfg.get('fs_type','erofs')
    logger.info('Pack Type=%s Filesystem=%s',pack_type,fs_type); logger.info('Detected ROM Type=%s',getattr(ctx.rom.rom_type,'name','unknown')); return pack_type,fs_type

def run_modification_phases(ctx,phases,logger):
    logger.info('>>> Phase 3: Modifications')
    if 'system' in phases or 'apk' in phases:
        mod=UnifiedModifier(ctx,enable_apk_mods=('apk' in phases)); mod.run(phases=[p for p in ('system','apk') if p in phases])
    if 'framework' in phases: FrameworkModifier(ctx).run()
    if 'firmware' in phases: FirmwareModifier(ctx).run()
    RomModifier(ctx).run_all_modifications()

def run_repacking(ctx,phases,pack_type,fs_type,target_dir,logger):
    if 'repack' not in phases and phases!=DEFAULT_PHASES: return
    logger.info('>>> Phase 4: Repacking'); packer=Repacker(ctx); packer.pack_all(pack_type=fs_type.upper(),is_rw=(fs_type=='ext4'))
    if pack_type=='super': packer.pack_super_image()
    else: packer.pack_ota_payload()

def save_repack_checkpoint(ctx,work_dir):
    data={'rom_code':ctx.rom_code,'target_rom_version':ctx.target_rom_version,'security_patch':ctx.security_patch,'is_ab_device':ctx.is_ab_device,'android_version':ctx.android_version,'is_eu_rom':ctx.is_eu_rom,'is_global_rom':ctx.is_global_rom,'global_region':ctx.global_region,'device_config':ctx.device_config}
    path=Path(work_dir)/REPACK_CHECKPOINT_NAME; path.write_text(json.dumps(data,ensure_ascii=False,indent=2),encoding='utf-8'); return path

def load_repack_checkpoint(work_dir,target_dir,logger):
    path=Path(work_dir)/REPACK_CHECKPOINT_NAME
    if not path.exists(): raise FileNotFoundError(path)
    d=json.loads(path.read_text(encoding='utf-8'))
    return SimpleNamespace(rom_code=d.get('rom_code','unknown'),target_rom_version=d.get('target_rom_version',''),security_patch=d.get('security_patch','Unknown'),is_ab_device=bool(d.get('is_ab_device',False)),android_version=d.get('android_version','0'),is_eu_rom=bool(d.get('is_eu_rom',False)),is_global_rom=bool(d.get('is_global_rom',False)),global_region=d.get('global_region',''),target_dir=target_dir,target_config_dir=target_dir/'config',repack_images_dir=target_dir/'repack_images',device_config=d.get('device_config',{}),enable_ksu=False,enable_custom_avb_chain=False,avb_key_path=None)

def execute_rom_modification(args,logger):
    cache_bootstrap=initialize_cache_manager(args,logger)
    if cache_bootstrap.exit_code is not None: return cache_bootstrap.exit_code
    cache_manager=cache_bootstrap.cache_manager; log_run_configuration(logger,args,cache_manager is not None)
    if not OtaToolsManager().ensure_otatools(): logger.error('Failed to locate or download otatools.'); return 1
    resolve_remote_input(args,logger)
    work_dir,rom_work_dir,target_dir=resolve_work_paths(args.work_dir)
    if args.resume_from_packer:
        ctx=load_repack_checkpoint(work_dir,target_dir,logger); pack_type,fs_type=determine_pack_settings(args,ctx,logger); run_repacking(ctx,['repack'],pack_type,fs_type,target_dir,logger); return 0
    snapshots=StageSnapshotManager(args.snapshot_dir or work_dir/'snapshots',logger) if (args.enable_snapshots or args.rollback_to_snapshot) else None
    if args.rollback_to_snapshot:
        if not snapshots: return 1
        snapshots.restore(args.rollback_to_snapshot,target_dir); return 0
    if not args.skip_preflight:
        report=run_preflight(args,logger); save_preflight_report(report,args.preflight_report)
        if report.has_failures(args.preflight_strict): return 2
        if args.preflight_only: return 0
    if args.clean: clean_work_dir(work_dir,logger)
    logger.info('>>> Phase 1: Extraction')
    rom=RomPackage(args.rom,rom_work_dir,label='ROM',cache_manager=cache_manager); rom.extract_images()
    logger.info('>>> Phase 2: Initialization')
    ctx=RomContext(rom,target_dir); ctx.cache_manager=cache_manager; ctx.eu_bundle=args.eu_bundle; ctx.initialize_target(clean_existing=True)
    if snapshots: snapshots.capture('phase2_initialized',target_dir)
    device_code=rom.get_prop('ro.product.name_for_attestation') or rom.get_prop('ro.product.vendor.device') or 'unknown'
    try: ctx.device_config=get_or_create_device_config(device_code=device_code,payload_path=Path(args.rom) if rom.rom_type.name=='PAYLOAD' else None,rom_props=rom.props,logger=logger,payload_info=rom.payload_info)
    except TypeError:
        ctx.device_config=get_or_create_device_config(device_code=device_code,payload_path=Path(args.rom) if rom.rom_type.name=='PAYLOAD' else None,stock_props=rom.props,logger=logger,payload_info=rom.payload_info)
    except Exception:
        ctx.device_config=load_device_config(device_code,logger)
    if cache_manager and ctx.device_config.get('cache',{}).get('partitions',False): cache_manager.cache_partitions=True
    pack_type,fs_type=determine_pack_settings(args,ctx,logger); save_repack_checkpoint(ctx,work_dir)
    work_dir.mkdir(parents=True,exist_ok=True); rom.export_props(work_dir/'rom_debug.prop')
    logger.info('Device: %s',rom.get_prop('ro.product.name_for_attestation'))
    phases=args.phases or DEFAULT_PHASES
    baseline=collect_artifact_state(target_dir,logger) if args.enable_diff_report else None
    run_modification_phases(ctx,phases,logger)
    if snapshots: snapshots.capture('phase3_modified',target_dir)
    run_repacking(ctx,phases,pack_type,fs_type,target_dir,logger)
    if snapshots and ('repack' in phases or phases==DEFAULT_PHASES): snapshots.capture('phase4_repacked',target_dir)
    if args.enable_diff_report and baseline is not None:
        final=collect_artifact_state(target_dir,logger); report=generate_diff_report(baseline,final); save_diff_report(report,args.diff_report)
    logger.info('='*70); logger.info('ROM modification completed successfully!'); logger.info('='*70); return 0
