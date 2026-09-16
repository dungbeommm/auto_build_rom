# ROM-Auto-Builder

Linux-first ROM modification orchestrator based on the target/dependency declarations from the supplied `Tool-Tree-main` reference.

## Scope

Included:
- ROM ZIP / `super.img` / extracted directory discovery
- `super.img` partition extraction through `lpunpack`
- Dependency-aware target selection
- Exact target registry for APK/JAR files used by the reference patch UI
- APK decode/build through Apktool
- JAR DEX decode/build through Baksmali/Smali
- Fail-closed recipe engine: no guessed bytecode edits
- Checkpoint state and logs
- GitHub Actions workflow
- Verification of rebuilt APK/JAR/ZIP archives

Excluded by design:
- ROM porting
- `boot.img` patching
- `vendor_boot.img` patching
- fake locked bootloader
- boot SELinux patching
- Wi-Fi hacking addon

## Important accuracy rule

The supplied reference exposes the exact target/dependency list in `patch_rom/index.bash`, but the actual patch implementation is compiled into the Android AArch64 binary `patch-rom`. The new engine therefore refuses to invent bytecode patterns. Exact bytecode changes must be supplied as tested recipes under `config/recipes.json` for the target Android/HyperOS version.

The original AArch64 reference binary is retained under `bin/android-aarch64/reference-patch-rom` for compatibility/reference work; it is not used as an x86_64 GitHub Actions implementation.

## Quick start

```bash
export PYTHONPATH="$PWD/src"
python3 main.py list-mods
python3 main.py doctor
python3 main.py plan workspace/input/rom.zip --feature reboot_menu
python3 main.py patch workspace/input/rom.zip --feature reboot_menu
```

Install the external tools listed in `config/pipeline.json`. For GitHub Actions, the workflow installs Java, Build Tools, e2fsprogs and erofs-utils; `lpunpack/lpmake/lpdump` must be provided in `bin/linux-x86_64/` or installed on the runner.

## Feature selection

Feature IDs are defined in `config/mods.json`. The resolver maps each feature to only the APK/JAR targets declared by the reference tool. For example:

`reboot_menu` -> `MiuiSystemUI.apk`

`fix_delayed_notifications` -> `MiuiSystemUI.apk`, `PowerKeeper.apk`, `miui-framework.jar`, `miui-services.jar`

`advanced_keyboard` -> `miui-framework.jar`, `miui-services.jar`, `FrequentPhrase.apk`, `MiuiSystemUI.apk`, `Settings.apk`

## Resume

The pipeline writes `workspace/state/pipeline.json`. It is safe to inspect with:

```bash
python3 main.py resume
```
