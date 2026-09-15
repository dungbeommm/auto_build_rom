# ToolTree rewrite notes

This distribution is based on the supplied HyperOS-Port-Python source and keeps its Python/plugin architecture.

## Changes made

- Fixed Xiaomi Fastboot `.tgz` and `.tar.gz` handling (the upstream detector classified TGZ as Fastboot but opened it as ZIP).
- Added streamed, regular-file-only archive extraction with basename isolation; TAR links and traversal paths are never materialized.
- Added support for `super.img_sparsechunk.*` alongside `super.img.*`.
- Added fallback from unsuffixed logical partition names to `_a`, and normalized `_a`/`_b` output names.
- Enabled common framework/APK/feature modifications in official-mod mode.
- Defaulted the common profile to EROFS + hybrid `super` output.
- Added a GitHub-hosted Ubuntu workflow, Issue `/mod-rom` parser, strict HTTPS host validation, 40 GiB disk guard, diagnostics, release splitting, SHA-256 manifest and cross-platform join script.
- No Android/self-hosted runner and no APT dependency installation are required.

## Deliberate limitations

- Device-specific framework methods can change between HyperOS releases; every patch is reported but a matching smali method is not guaranteed.
- Boot/vendor_boot changes depend on the existing firmware plugins and device profile; the project does not inject an unknown proprietary Tool-Tree binary.
- ROM output must be tested on the exact device with an unlocked bootloader and a recovery path.
