#!/usr/bin/env python3
import os
import sys
import tarfile


def main() -> int:
    if len(sys.argv) != 2:
        raise SystemExit("Usage: safe_tar.py ARCHIVE")
    with tarfile.open(sys.argv[1], "r:gz") as archive:
        for member in archive.getmembers():
            normalized = os.path.normpath(member.name)
            if normalized.startswith("/") or normalized == ".." or normalized.startswith("../"):
                raise SystemExit(f"Unsafe archive path: {member.name}")
            if member.issym() or member.islnk():
                target = os.path.normpath(os.path.join(os.path.dirname(normalized), member.linkname))
                if target.startswith("/") or target == ".." or target.startswith("../"):
                    raise SystemExit(f"Unsafe archive link: {member.name} -> {member.linkname}")
    print("Archive paths OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
