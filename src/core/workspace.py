"""Workspace preparation for single-ROM modification."""
from __future__ import annotations
import shutil
from typing import TYPE_CHECKING
from src.core.rom import RomPackage
if TYPE_CHECKING:
    from src.core.context import RomContext

def prepare_target_directories(ctx:"RomContext",*,clean_existing:bool)->None:
    if ctx.target_dir.exists() and clean_existing: shutil.rmtree(ctx.target_dir)
    ctx.target_dir.mkdir(parents=True,exist_ok=True); ctx.target_config_dir.mkdir(parents=True,exist_ok=True); ctx.repack_images_dir.mkdir(parents=True,exist_ok=True)

def build_partition_layout(ctx:"RomContext")->dict[str,RomPackage]:
    return {name:ctx.rom for name in ("vendor","odm","vendor_dlkm","odm_dlkm","system_dlkm","system","system_ext","product","mi_ext","product_dlkm")}

def install_partition(ctx:"RomContext",part_name:str,source_rom:RomPackage)->None:
    src_dir=source_rom.extract_partition_to_file(part_name)
    if not src_dir or not src_dir.exists(): ctx.logger.warning('Partition %s missing, skipping.',part_name); return
    dest=ctx.target_dir/part_name
    if dest.exists(): shutil.rmtree(dest)
    try: ctx.shell.run(['cp','-a','--reflink=auto',str(src_dir),str(dest)])
    except Exception: shutil.copytree(src_dir,dest,symlinks=True,dirs_exist_ok=True)
    src_fs,src_fc=source_rom.get_config_files(part_name)
    if src_fs.exists(): shutil.copy2(src_fs,ctx.target_config_dir/f'{part_name}_fs_config')
    if src_fc.exists(): shutil.copy2(src_fc,ctx.target_config_dir/f'{part_name}_file_contexts')

def copy_firmware_images(ctx:"RomContext",exclude_list:list[str])->None:
    if not ctx.rom.images_dir.exists(): return
    copied=0
    for img in ctx.rom.images_dir.glob('*.img'):
        name=img.stem.replace('_a','').replace('_b','')
        if name in exclude_list: continue
        shutil.copy2(img,ctx.repack_images_dir/img.name); copied+=1
    ctx.logger.info('Copied %s firmware images.',copied)
