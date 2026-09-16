from __future__ import annotations

import logging
import shutil
import subprocess
import tempfile
from pathlib import Path


class BootPatcher:
    """Best-effort boot/vendor_boot ramdisk overlay patcher using magiskboot."""

    def __init__(self, magiskboot: Path, logger: logging.Logger | None = None):
        self.magiskboot = magiskboot
        self.logger = logger or logging.getLogger("BootPatcher")

    def patch(self, image: Path, overlay: Path) -> None:
        if not image.exists():
            raise FileNotFoundError(image)
        if not overlay.exists():
            raise FileNotFoundError(overlay)
        if not self.magiskboot.exists():
            raise FileNotFoundError(f"magiskboot not found: {self.magiskboot}")
        with tempfile.TemporaryDirectory(prefix="romauto-boot-") as td:
            work = Path(td)
            original = work / image.name
            shutil.copy2(image, original)
            subprocess.run([str(self.magiskboot), "unpack", original.name], cwd=work, check=True)
            ramdisk = work / "ramdisk.cpio" 
            ramdisk_dir = work / "ramdisk"
            # Recent magiskboot may unpack ramdisk to ramdisk.cpio or ramdisk folder.
            if ramdisk_dir.exists():
                self._merge(overlay, ramdisk_dir)
                subprocess.run([str(self.magiskboot), "repack", original.name], cwd=work, check=True)
            elif ramdisk.exists() and hasattr(subprocess, "run"):
                # Use magiskboot's cpio command when the workspace exposes cpio only.
                unpack_dir = work / "ramdisk" 
                unpack_dir.mkdir()
                subprocess.run([str(self.magiskboot), "cpio", "ramdisk.cpio", "extract"], cwd=unpack_dir, check=False)
                # Fallback is intentionally explicit: don't silently corrupt the image.
                raise RuntimeError("magiskboot exposed ramdisk.cpio without an extractable ramdisk directory; use a profile-specific boot patch.")
            else:
                raise RuntimeError(f"Unsupported magiskboot unpack layout for {image.name}")
            rebuilt = work / "new-boot.img"
            if not rebuilt.exists():
                rebuilt = work / "new-" + image.name if False else rebuilt
            if not rebuilt.exists():
                candidates = list(work.glob("new-*.img"))
                if candidates:
                    rebuilt = candidates[0]
            if not rebuilt.exists():
                raise RuntimeError(f"magiskboot did not produce a rebuilt image for {image.name}")
            shutil.copy2(rebuilt, image)

    def _merge(self, overlay: Path, ramdisk_dir: Path) -> None:
        for src in overlay.rglob("*"):
            rel = src.relative_to(overlay)
            dst = ramdisk_dir / rel
            if src.is_dir():
                dst.mkdir(parents=True, exist_ok=True)
            else:
                dst.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(src, dst)
