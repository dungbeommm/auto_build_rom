from __future__ import annotations

import os
import shutil
import sys
import tarfile
import zipfile
from pathlib import Path
from typing import TYPE_CHECKING, List, Optional

from src.utils.payload_dumper import PayloadDumperOutput, PayloadDumperRunner

if TYPE_CHECKING:
    from .package import RomPackage


def extract_payload(
    package: RomPackage,
    partitions: Optional[List[str]],
    extract_metadata: bool = False,
) -> Optional[PayloadDumperOutput]:
    """Extract payload.bin from ROM package.

    Args:
        package: The RomPackage instance.
        partitions: List of partitions to extract (None = all).
        extract_metadata: Whether to extract metadata using --json and --metadata.

    Returns:
        PayloadDumperOutput if extract_metadata=True, None otherwise.
    """
    cmd = ["payload-dumper", "--out", str(package.images_dir)]

    if partitions:
        package.logger.info(f"[{package.label}] Extracting specific images: {partitions} ...")
        cmd.extend(["--partitions", ",".join(partitions)])
    else:
        package.logger.info(f"[{package.label}] Extracting ALL images (Firmware + Logical) ...")

    cmd.append(str(package.path))
    package.shell.run(cmd)

    # Extract metadata if requested
    if extract_metadata:
        package.logger.info(f"[{package.label}] Extracting payload metadata...")
        try:
            runner = PayloadDumperRunner(package.path)
            payload_info = runner.get_full_info()
            package.logger.info(
                f"[{package.label}] Detected device: {payload_info.device_code}, "
                f"Partitions: {len(payload_info.partition_names)}"
            )
            return payload_info
        except Exception as e:
            package.logger.warning(f"[{package.label}] Failed to extract metadata: {e}")
            return None

    return None


def extract_brotli(
    package: RomPackage,
    partitions: Optional[List[str]],
) -> None:
    """Extract and convert brotli-compressed images from ROM package.

    Args:
        package: The RomPackage instance.
        partitions: List of partitions to extract (None = all).
    """
    # 1. Extract zip content
    with zipfile.ZipFile(package.path, "r") as z:
        for f in z.namelist():
            should_extract = False

            # .img handling
            if f.endswith(".img"):
                part_name = Path(f).stem
                if not partitions or part_name in partitions:
                    should_extract = True

            # .br handling
            elif f.endswith(".new.dat.br") or f.endswith(".transfer.list"):
                # Extract partition name from file name (e.g. system.new.dat.br -> system)
                part_name = Path(f).name.split(".")[0]
                if not partitions or part_name in partitions:
                    should_extract = True

            if should_extract:
                package.logger.info(f"Extracting {f}...")
                z.extract(f, package.images_dir)

    # 2. Process .br files
    for br_file in package.images_dir.glob("*.new.dat.br"):
        prefix = br_file.name.replace(".new.dat.br", "")

        new_dat = package.images_dir / f"{prefix}.new.dat"
        transfer_list = package.images_dir / f"{prefix}.transfer.list"
        output_img = package.images_dir / f"{prefix}.img"

        if output_img.exists():
            package.logger.info(f"[{package.label}] Image {output_img.name} already exists.")
            continue

        if not transfer_list.exists():
            package.logger.warning(f"Transfer list for {prefix} not found, skipping conversion.")
            continue

        # 3. Brotli Decompress
        package.logger.info(f"[{package.label}] Decompressing {br_file.name}...")
        try:
            cmd = ["brotli", "-d", "-f", str(br_file), "-o", str(new_dat)]
            package.shell.run(cmd)
        except Exception as e:
            package.logger.error(f"Brotli decompression failed for {prefix}: {e}")
            continue

        # 4. sdat2img
        package.logger.info(f"[{package.label}] Converting {prefix} to raw image...")
        try:
            from src.utils.sdat2img import run_sdat2img

            success = run_sdat2img(str(transfer_list), str(new_dat), str(output_img))

            if not success:
                package.logger.error(f"sdat2img failed for {prefix}")
            else:
                package.logger.info(f"[{package.label}] Generated {output_img.name}")
                if new_dat.exists():
                    os.remove(new_dat)
                if br_file.exists():
                    os.remove(br_file)
                if transfer_list.exists():
                    os.remove(transfer_list)

        except Exception as e:
            package.logger.error(f"sdat2img execution failed: {e}")


def extract_fastboot(
    package: RomPackage,
    partitions: Optional[List[str]],
) -> None:
    """Extract Fastboot ZIP/TGZ images and unpack ``super.img``.

    Archives are streamed member-by-member into ``images_dir``. Only regular
    image members are accepted and their directory components are discarded,
    preventing path traversal while avoiding a second full archive copy.
    """

    def selected(member_name: str) -> bool:
        name = Path(member_name).name
        is_super = name == "super.img" or name.startswith("super.img.") or name.startswith("super.img_sparsechunk.")
        if not (name.endswith(".img") or is_super):
            return False
        part_name = name[:-4] if name.endswith(".img") else name
        part_name = part_name.removesuffix("_a").removesuffix("_b")
        return not partitions or is_super or part_name in partitions

    def write_stream(name: str, source) -> None:
        target = package.images_dir / Path(name).name
        package.logger.info("Extracting %s...", name)
        with target.open("wb") as output:
            shutil.copyfileobj(source, output, length=8 * 1024 * 1024)

    if zipfile.is_zipfile(package.path):
        with zipfile.ZipFile(package.path, "r") as archive:
            for info in archive.infolist():
                if info.is_dir() or not selected(info.filename):
                    continue
                with archive.open(info, "r") as source:
                    write_stream(info.filename, source)
    elif tarfile.is_tarfile(package.path):
        with tarfile.open(package.path, "r:*") as archive:
            for member in archive:
                if not member.isfile() or not selected(member.name):
                    continue
                source = archive.extractfile(member)
                if source is None:
                    continue
                with source:
                    write_stream(member.name, source)
    else:
        raise ValueError(f"Unsupported Fastboot archive: {package.path}")

    from .utils import process_sparse_images

    process_sparse_images(package.images_dir, package.logger, package.shell)
    super_img = package.images_dir / "super.img"
    if not super_img.exists():
        return

    package.logger.info("[%s] Unpacking logical partitions from super.img...", package.label)
    try:
        if partitions:
            for part in partitions:
                extracted = False
                for candidate in (part, f"{part}_a"):
                    try:
                        package.shell.run([
                            sys.executable,
                            "src/utils/lpunpack.py",
                            "-p",
                            candidate,
                            str(super_img),
                            str(package.images_dir),
                        ])
                        extracted = True
                        break
                    except Exception:
                        continue
                if not extracted:
                    package.logger.warning("[%s] Partition not found in super: %s", package.label, part)
        else:
            package.shell.run([
                sys.executable,
                "src/utils/lpunpack.py",
                str(super_img),
                str(package.images_dir),
            ])
    finally:
        super_img.unlink(missing_ok=True)

    for suffix in ("_a.img", "_b.img"):
        for image in package.images_dir.glob(f"*{suffix}"):
            if image.stat().st_size == 0:
                image.unlink()
                continue
            target = image.with_name(image.name.removesuffix(suffix) + ".img")
            if target.exists():
                image.unlink()
            else:
                image.rename(target)
                package.logger.info("[%s] Normalized %s -> %s", package.label, image.name, target.name)


def extract_local(
    package: RomPackage,
    partitions: Optional[List[str]],
) -> None:
    """Handle local directory mode (pre-extracted).

    Args:
        package: The RomPackage instance.
        partitions: List of partitions to process.
    """
    package.logger.info(f"[{package.label}] Local dir mode, skipping payload extraction.")


class ImageExtractor:
    """Handles ROM image extraction logic."""

    def __init__(self, package: RomPackage) -> None:
        self.package = package

    def extract_images(
        self,
        partitions: Optional[List[str]] = None,
        source_changed: bool = False,
        current_source_hash: str = "",
        source_hash_path: Path = None,  # type: ignore[assignment]
    ) -> None:
        """Execute ROM image extraction based on type.

        Args:
            partitions: List of partitions to extract (None = all logical partitions).
            source_changed: Whether the source file has changed.
            current_source_hash: Current hash of the source file.
            source_hash_path: Path to store the source hash.
        """
        from .constants import RomType

        try:
            if self.package.rom_type == RomType.PAYLOAD:
                extract_payload(self.package, partitions)
            elif self.package.rom_type == RomType.BROTLI:
                extract_brotli(self.package, partitions)
            elif self.package.rom_type == RomType.FASTBOOT:
                extract_fastboot(self.package, partitions)

        except Exception as e:
            self.package.logger.error(f"Image extraction failed: {e}")
            raise

        # Save hash after successful extraction if source changed
        if source_changed and source_hash_path is not None:
            try:
                with open(source_hash_path, "w") as f:
                    f.write(current_source_hash)
                self.package.logger.info(
                    f"[{self.package.label}] Saved source file hash for future change detection."
                )
            except Exception as e:
                self.package.logger.warning(
                    f"[{self.package.label}] Could not save source hash file: {e}"
                )
