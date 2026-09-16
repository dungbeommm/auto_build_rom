# ROM Auto Builder

Linux/Ubuntu-first ROM image processing pipeline. This project intentionally **does not port ROMs and does not patch `boot.img` or `vendor_boot.img`**.

## Pipeline

`ROM URL -> archive extraction -> super.img detection -> sparse conversion -> lpunpack -> dependency-aware partition extraction -> APK/JAR decode -> exact recipe -> repack -> filesystem image -> lpmake -> ROM ZIP -> verification`

## Important safety rule

Bytecode modifications are **fail-closed**. A feature is not allowed to modify a class merely because a class/file has a similar name. `config/recipes.json` must contain an exact, version-appropriate recipe. If no recipe exists, the build stops instead of guessing.

The original Tool-Tree reference contains a native Android `patch-rom` binary. It is kept only as reference material; it is not silently executed as if it were a Linux x86_64 binary.

## Excluded

- boot image patching
- vendor_boot patching
- fake locked bootloader
- SELinux boot patching
- ROM porting
- Wi-Fi hacking

## Commands

```bash
bash scripts/run.sh list-mods
bash scripts/run.sh doctor
bash scripts/run.sh plan /path/to/rom.zip --feature reboot_menu
bash scripts/run.sh patch /path/to/rom.zip --feature reboot_menu
bash scripts/run.sh build /path/to/rom.zip --feature reboot_menu
```

`build` rebuilds the modified filesystem(s), rebuilds `super.img` with the original LP metadata/group layout, and creates `workspace/release/rom-modified.zip`.

## GitHub Actions

The workflow bootstraps Linux LP tools and Java APK/JAR tools, accepts raw URLs or Markdown links, handles `.zip` and `.tgz/.tar.gz`, validates the checked-out source, and uploads the resulting ROM artifact. A GitHub Release can optionally be created from the workflow input.

## APK signing

Modified APKs normally require a platform-compatible signing key. The builder deliberately does not invent or substitute a key. Provide an appropriate signing stage/key for the target ROM before distributing a modified ROM.
