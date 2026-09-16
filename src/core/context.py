from __future__ import annotations

import concurrent.futures
import logging
import subprocess
from pathlib import Path
from typing import Any, Dict, List, Optional, Union, cast, TYPE_CHECKING

from src.core.rom import RomPackage
from src.core.rom_metadata import populate_rom_metadata
from src.core.tooling import resolve_tooling
from src.core.workspace import build_partition_layout, copy_firmware_images, install_partition, prepare_target_directories
from src.utils.shell import ShellRunner
from src.utils.sync_engine import ROMSyncEngine

if TYPE_CHECKING:
    from src.core.cache_manager import RomCacheManager

class RomContext:
    """Runtime context for modifying one ROM package and rebuilding it."""
    def __init__(self, rom: RomPackage, target_work_dir: Union[str, Path]) -> None:
        self.rom=rom
        self.project_root=Path('.').resolve()
        self.bin_root=self.project_root/'bin'
        self.target_dir=Path(target_work_dir).resolve()
        self.target_config_dir=self.target_dir/'config'
        self.repack_images_dir=self.target_dir/'repack_images'
        self.rom_dir=self.rom.extracted_dir
        self.target_rom_dir=self.target_dir
        self.logger=logging.getLogger('Context')
        self._init_tools()
        self.syncer=ROMSyncEngine(self,logging.getLogger('SyncEngine'))
        self.shell=ShellRunner()
        self.enable_ksu=False
        self.enable_custom_avb_chain=False
        self.avb_key_path: Optional[Path]=None
        self.cache_manager: RomCacheManager|None=None
        self.device_config: dict[str,Any]={}
        self.eu_bundle: str|None=None
        self.android_version='0'; self.android_sdk='0'
        self.target_rom_version=''
        self.rom_code='unknown'
        self.is_ab_device=False
        self.security_patch='Unknown'
        self.is_eu_rom=False
        self.is_global_rom=False
        self.global_region=''
        self.region=''

    def _init_tools(self)->None:
        resolved=resolve_tooling(self.project_root,self.logger)
        self.platform_bin_dir=resolved.platform_bin_dir; self.tools=resolved.tools

    def initialize_target(self, *, clean_existing: bool=False)->None:
        self.logger.info('Initializing target workspace at %s',self.target_dir)
        prepare_target_directories(self,clean_existing=clean_existing)
        layout=build_partition_layout(self)
        with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
            futures=[executor.submit(self._install_partition,n,s) for n,s in layout.items()]
            for future in concurrent.futures.as_completed(futures):
                future.result()
        self._copy_firmware_images(list(layout))
        self.get_rom_info()
        self.logger.info('Target workspace initialized.')

    def _install_partition(self,part_name,source_rom): install_partition(self,part_name,source_rom)
    def _copy_firmware_images(self,exclude_list): copy_firmware_images(self,exclude_list)
    def get_rom_info(self): populate_rom_metadata(self)

    def get_target_prop_file(self,part_name:str)->Optional[Path]:
        part_dir=self.target_dir/part_name
        if not part_dir.exists(): return None
        for p in (part_dir/'build.prop',part_dir/'system'/'build.prop',part_dir/'etc'/'build.prop'):
            if p.exists(): return p
        try: return next(part_dir.rglob('build.prop'))
        except StopIteration: return None

    def build_apk_caches(self,force:bool=False)->Dict[str,int]:
        rom_cache=self.syncer._get_rom_cache(self.target_dir)
        if force or not rom_cache: self.syncer.find_apk_by_name('dummy.apk',self.target_dir)
        package_cache=self.syncer._get_package_cache(self.target_dir)
        if force or not package_cache: self.syncer.find_apk_by_package('dummy.package',self.target_dir)
        return cast(dict[str,int],self.syncer.get_apk_cache_stats())

    def _get_apk_package_name(self,apk_path:Path)->Optional[str]:
        if not apk_path.exists() or not self.tools.aapt2.exists(): return None
        try:
            r=subprocess.run([str(self.tools.aapt2),'dump','packagename',str(apk_path)],capture_output=True,text=True,check=True,timeout=5)
            return r.stdout.strip()
        except (subprocess.CalledProcessError,subprocess.TimeoutExpired): return None

    def find_apk_by_name(self,apk_name): return cast(Optional[Path],self.syncer.find_apk_by_name(apk_name,self.target_dir))
    def find_apk_by_package(self,package_name): return cast(Optional[Path],self.syncer.find_apk_by_package(package_name,self.target_dir))
    def clear_apk_caches(self)->None:
        self.syncer._rom_caches.clear(); self.syncer._package_caches.clear()
