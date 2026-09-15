#!/usr/bin/env python3
import argparse,json,os,re,shutil,time
from pathlib import Path

def envbool(n): return os.getenv(n,'0')=='1'
def setprop(path,key,value):
 try:s=path.read_text(errors='surrogateescape')
 except Exception:return False
 rx=re.compile(rf'(?m)^[# ]*{re.escape(key)}=.*$')
 ns=rx.sub(f'{key}={value}',s) if rx.search(s) else s.rstrip()+f'\n{key}={value}\n'
 if ns!=s:path.write_text(ns,errors='surrogateescape');return True
 return False

def main():
 a=argparse.ArgumentParser();a.add_argument('--root',required=True);a.add_argument('--apps',required=True);a.add_argument('--report',required=True);x=a.parse_args()
 root=Path(x.root); changes=[]; unsupported=[]
 props=[p for p in root.rglob('*') if p.is_file() and p.name in ('build.prop','default.prop','system.prop')]
 def prop(group,key,val):
  n=sum(setprop(p,key,val) for p in props);changes.append({'group':group,'rule':f'{key}={val}','files':n})
 if envbool('PATCH_FRAMEWORK'):
  prop('framework','ro.control_privapp_permissions',os.getenv('PRIVAPP_MODE','log'))
  unsupported+=['framework: disable APK signature verification requires device-specific smali rule','framework: Kaorios Toolbox patch requires original closed rule']
 if envbool('PATCH_CN_ROM'):
  prop('cn_rom','ro.com.google.clientidbase','android-xiaomi');prop('cn_rom','persist.sys.miui_optimization','false');prop('cn_rom','ro.miui.region','GLOBAL')
  for p in root.rglob('cn.google.services.xml'):
   try:p.rename(p.with_suffix(p.suffix+'.disabled'));changes.append({'group':'cn_rom','rule':'disable cn.google.services.xml','files':1})
   except OSError:pass
 if envbool('PATCH_KEYBOARD'):
  prop('keyboard','ro.com.google.ime.theme_id','5');prop('keyboard','persist.sys.default_ime',os.getenv('KEYBOARD_PACKAGE','com.google.android.inputmethod.latin'))
  unsupported.append('keyboard: MIUI SystemUI/JAR smali patch needs an explicit open rule')
 if envbool('PATCH_OTHERS'):
  prop('other','persist.vendor.dfps.level','0');prop('other','persist.sys.display.refresh_rate','120');prop('other','persist.sys.allow_screenshot','1')
  unsupported.append('other: framework window/FPS method patches vary by HyperOS build')
 if envbool('PATCH_APPS'):
  hooks=Path('plugins/app-patches');count=0
  if hooks.exists():
   for h in sorted(hooks.glob('*.py')): os.system(f'python3 "{h}" "{root}"');count+=1
  changes.append({'group':'app_patches','rule':'external app patch hooks','files':count})
  if not count:unsupported.append('apps: no open per-version APK smali hooks installed')
 if envbool('ADD_APPS'):
  apps=Path(x.apps);count=0
  for part in apps.iterdir() if apps.exists() else []:
   if not part.is_dir():continue
   targets=list(root.rglob(part.name)); target=next((t for t in targets if t.is_dir() and t.name==part.name),None)
   if not target:continue
   for appdir in part.iterdir():
    if appdir.is_dir():shutil.copytree(appdir,target/'app'/appdir.name,dirs_exist_ok=True);count+=1
  changes.append({'group':'add_apps','rule':'copy bundled system apps','files':count})
 if envbool('PATCH_BOOT'):unsupported.append('boot/vendor_boot: native hosted hook is present but disabled until a reproducible Linux boot-image rule is supplied')
 Path(x.report).write_text(json.dumps({'created_at':time.strftime('%FT%TZ',time.gmtime()),'changes':changes,'unsupported':unsupported},ensure_ascii=False,indent=2))
 print(json.dumps({'changes':len(changes),'unsupported':len(unsupported)}))
if __name__=='__main__':main()
