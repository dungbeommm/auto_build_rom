#!/usr/bin/env bash
set -Eeuo pipefail

: "${TOOLTREE_HOME:=/data/data/com.tool.tree/files/home}"
: "${PROJECT_DIR:?PROJECT_DIR is required}"
: "${PATCH_PROFILE:?PATCH_PROFILE is required}"
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
ENGINE_DIR="$ROOT_DIR/vendor/tool-tree/patch_rom"
ENGINE="$ENGINE_DIR/patch-rom"

[[ "$(uname -m)" == aarch64 || "$(uname -m)" == arm64 ]] || { echo 'Engine yêu cầu Android ARM64' >&2; exit 20; }
[[ -e /system/bin/linker64 ]] || { echo 'Không tìm thấy /system/bin/linker64; cần Android ARM64' >&2; exit 21; }
[[ -x "$ENGINE" ]] || chmod +x "$ENGINE"
[[ -d "$TOOLTREE_HOME" ]] || { echo "Không thấy Tool-Tree home: $TOOLTREE_HOME" >&2; exit 22; }

export HOME="$TOOLTREE_HOME" TERMUX="$HOME/termux" ETC="$HOME/etc" BIN="$HOME/bin"
export LOG="$HOME/usr/log" AON="$HOME/usr/AON" AOK="$HOME/usr/AOK" UDD="$HOME/usr/UDD" UPK="$HOME/usr/UPK"
export TMPDIR="$HOME/tmp" LIB="$HOME/lib" PATH="$BIN:$TERMUX/bin:$TERMUX/py:$PATH"
export SDH="$(dirname "$PROJECT_DIR")" PTSH="$(basename "$PROJECT_DIR")" MPAT="$ENGINE_DIR" ROT=1
mkdir -p "$TMPDIR" "$LOG"
# shellcheck disable=SC1090
source "$PATCH_PROFILE"
export PATCH_FRAMEWORK PATCH_CN_ROM PATCH_KEYBOARD PATCH_OTHERS PATCH_APPS ADD_APPS PATCH_BOOT
export fix_apksign tool_box fix_enforce fix_noti settings_infor settings_show settings_icons sceen_lock dark_show open_app font_fix
export ime_app app_ime ime_color ime_color_dark ime_dimen
export fix_screen fix_fps fix_reset_theme fix_show_error fix_fpscam fix_window app_setup fix_data
export fix_themes fix_appvault fix_thoit fix_joyose fix_mapcn fix_gmscn fix_off_10s
export add_app add_app_2 app_playstore app_restore app_velvet app_auto app_tts app_carrier app_gps app_monet
export fix_fake_lock fix_diselinux

find_named() { local n; for n in "$@"; do find "$PROJECT_DIR" -type f -name "$n" -print0; done; }
run_with_files() {
  local action="$1"; shift
  local -a files=(); while IFS= read -r -d '' f; do files+=("$f"); done < <(find_named "$@")
  if ((${#files[@]})); then echo "[patch] $action (${#files[@]} files)"; "$ENGINE" "$action" "${files[*]}"; else echo "[skip] $action: không thấy file yêu cầu"; fi
}

[[ ${PATCH_FRAMEWORK:-0} == 1 ]] && run_with_files toolbox framework.jar services.jar miui-services.jar
[[ ${PATCH_CN_ROM:-0} == 1 ]] && run_with_files fixnoti miui-framework.jar miui-services.jar PowerKeeper.apk MiuiSystemUI.apk Settings.apk
[[ ${PATCH_KEYBOARD:-0} == 1 ]] && run_with_files fixkey miui-framework.jar miui-services.jar '*FrequentPhrase.apk' MiuiSystemUI.apk Settings.apk
[[ ${PATCH_OTHERS:-0} == 1 ]] && run_with_files fixmultiple services.jar miui-services.jar PowerKeeper.apk miui-framework.jar ExternalStorageProvider.apk
[[ ${PATCH_APPS:-0} == 1 ]] && run_with_files fixapps '*PersonalAssistant*.apk' MIUIWeather.apk Joyose.apk Provision.apk MIUIGallery.apk '*SecurityCenter.apk' '*ThemeManager.apk'
[[ ${ADD_APPS:-0} == 1 ]] && "$ENGINE" online_app
if [[ ${PATCH_BOOT:-0} == 1 ]]; then
  while IFS= read -r -d '' dir; do "$ENGINE" patch_boot "$dir"; done < <(find "$PROJECT_DIR" -maxdepth 1 -type d \( -name boot -o -name vendor_boot \) -print0)
fi
