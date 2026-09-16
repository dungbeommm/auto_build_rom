# Single-ROM Processing Workflow

## 1. Input
`main.py --rom <ROM>` accepts a local ZIP/payload/directory or a remote HTTP(S) URL.

## 2. Preflight
The tool validates the input path, detects ZIP/payload/super/Brotli markers, prepares the working directory, and writes a JSON report.

## 3. Download
Remote ROM URLs are downloaded before extraction. Optional EU localization bundles follow the same path.

## 4. Extraction
`RomPackage.extract_images()` detects the package type and converts the source into image files. Logical Android partitions are unpacked into the ROM workspace.

Runtime layout:
```text
build/
├── rom/
│   ├── images/
│   ├── extracted/
│   └── extracted/config/
└── target/
```

## 5. Target initialization
`RomContext.initialize_target()` creates the editable target tree. Every selected partition is populated from the same input ROM; there is no second ROM source.

The default partition set is:
- vendor
- odm
- vendor_dlkm
- odm_dlkm
- system_dlkm
- system
- system_ext
- product
- mi_ext
- product_dlkm

Firmware images not represented by the target partition tree are copied into `target/repack_images` for final rebuilding.

## 6. Metadata and device configuration
The tool reads Android version, SDK, incremental build, security patch, region and device codename from the input ROM. Existing `devices/<codename>` configuration is reused; missing payload metadata can create the configuration automatically.

## 7. Modification phases
The phase order is deterministic:
1. `system` — system-level plugin rules.
2. `apk` — APK modifier plugins and APK lookup caches.
3. `framework` — framework/JAR/smali changes.
4. `firmware` — firmware and vbmeta-related changes.
5. `RomModifier` — bloat cleanup and physical override application.

Each phase operates only on `build/target`.

## 8. Repack
Images are rebuilt with EROFS or EXT4 according to configuration/CLI options. The tool can then generate:
- a Super image (`--pack-type super`), or
- an OTA payload (`--pack-type payload`).

Custom AVB handling, signing keys, partition sizing and metadata generation remain in the packer.

## 9. Reliability features
Existing reliability features remain available:
- cache manager for APK/JAR and optional partition data,
- workflow snapshots,
- rollback to a named snapshot,
- diff reports,
- repack checkpoint/resume,
- preflight reports,
- structured logging.

## 10. Removed architecture
The executable workflow no longer contains a Stock/Port split, Port ROM input, cross-device ROM source selection, Port-only partition sourcing, or Port-vs-Stock metadata replacement logic.
