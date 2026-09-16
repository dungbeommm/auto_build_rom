from __future__ import annotations
import shutil
from pathlib import Path
from ..exec import run, require, ToolError

class ImageManager:
    """Read-only extraction of logical partition filesystem images."""
    def __init__(self, logger, root: Path | None = None):
        self.log = logger
        self.root = Path(root) if root else None

    def _read(self, image: Path, offset: int, size: int = 4096) -> bytes:
        with image.open("rb") as f:
            f.seek(offset)
            return f.read(size)

    def fstype(self, image: Path) -> str:
        sb = self._read(image, 0x438, 2)
        if sb == b"\x53\xef":
            return "ext4"
        for off in (0, 1024):
            head = self._read(image, off, 4)
            if head in (b"\xe2\xe1\xf5\xe0", b"EROFS"):
                return "erofs"
        return "unknown"

    def extract(self, image: Path, out: Path) -> Path:
        out.mkdir(parents=True, exist_ok=True)
        fs = self.fstype(image)
        self.log.info("Extracting %s (filesystem=%s) -> %s", image, fs, out)
        if fs == "ext4":
            debugfs = require("debugfs", "debugfs")
            run([debugfs, "-R", f"rdump / {out}", str(image)], logger=self.log)
            return out
        if fs == "erofs":
            # dump.erofs is an inspector only; it does not accept an output
            # directory. Use fsck.erofs with --extract=<directory> for
            # actual filesystem extraction. Modern erofs-utils exposes this
            # form (Ubuntu 24.04 ships erofs-utils 1.7.1).
            fsck = shutil.which("fsck.erofs")
            if not fsck:
                raise ToolError("EROFS image detected but fsck.erofs is missing; install erofs-utils")
            run([fsck, f"--extract={out}", str(image)], logger=self.log)
            return out
        raise ToolError(f"Unsupported filesystem in {image}")

    def extract_partitions(self, partition_dir: Path, out_root: Path) -> list[Path]:
        roots=[]
        out_root.mkdir(parents=True, exist_ok=True)
        for image in sorted(partition_dir.glob("*.img")):
            name=image.stem
            out=out_root/name
            marker=out/".rombuilder_extracted"
            if marker.exists():
                self.log.info("Reuse extracted partition: %s", out)
                roots.append(out); continue
            self.extract(image,out)
            marker.write_text(str(image),encoding="utf-8")
            roots.append(out)
        return roots
