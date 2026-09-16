# Reference-derived feature matrix

Source: supplied `Tool-Tree-main/.github/addon/patch_rom/index.bash`.

| Feature | Exact target(s) declared by reference |
|---|---|
| Disable OTA | filesystem/config (no APK/JAR target declaration in patch panel) |
| Patch `cn.google.services.xml` | filesystem/config |
| Disable overlay fstab | filesystem/config |
| Move Pangu items | filesystem/config |
| Move `mi_ext` items | filesystem/config |
| Add resetprop | filesystem/payload |
| Disable APK signature verification | `framework.jar`, `services.jar`, `miui-services.jar` |
| Kaorios Toolbox 2.0.4 | `framework.jar`, `services.jar` |
| Remove `enforceVersionPolicy` | `miui-services.jar` |
| Fix delayed notifications | `miui-framework.jar`, `miui-services.jar`, `PowerKeeper.apk`, `MiuiSystemUI.apk` |
| Device information | `Settings.apk` |
| Google/location/privacy/KidSpace | `Settings.apk` |
| Notification icons | `Settings.apk` |
| Reboot menu | `MiuiSystemUI.apk` |
| Dark app list | `miui-services.jar` |
| Remove open-app notification | `miui-services.jar` |
| Font fix / hide app-opening dialog | `miui-framework.jar` |
| Advanced keyboard | `miui-framework.jar`, `miui-services.jar`, `FrequentPhrase.apk`, `MiuiSystemUI.apk`, `Settings.apk` |
| Screenshot restrictions | `services.jar`, `miui-services.jar` |
| FPS limits | `PowerKeeper.apk` |
| Theme reset | `miui-framework.jar` |
| Lock-screen error dialog | `services.jar` |
| Camera 60Hz | `miui-services.jar` |
| Window restrictions | `miui-framework.jar`, `miui-services.jar` |
| Android/data/obb | `ExternalStorageProvider.apk` |
| SetupWizard | `miui-services.jar` |
| Theme Store purchases | `ThemeManager.apk` |
| App Vault purchases | `PersonalAssistant.apk` |
| AQI Weather CN | `MIUIWeather.apk` / `*Weather.apk` |
| Joyose Mod | `Joyose.apk` |
| Hide China Gallery map | `MIUIGallery.apk` / `*Gallery.apk` |
| Provision enable GMS | `Provision.apk` |
| Remove 10s/show data/disable system apps | `*SecurityCenter.apk` |
