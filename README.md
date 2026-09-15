# ROM Auto Modder — GitHub Hosted

Bản viết lại chạy trực tiếp trên `ubuntu-latest`, không cần self-hosted runner, Android root hay cài Tool-Tree trên điện thoại.

## Luồng hoạt động

1. Nhận URL Xiaomi Fastboot ROM `.tgz` từ `workflow_dispatch` hoặc Issue `/mod-rom URL`.
2. Dọn dung lượng runner, tải và giải nén ROM.
3. Tự nhận diện `super.img` hoặc các image rời.
4. Unpack EROFS/EXT4, áp dụng profile tính năng, repack image/super.
5. Đóng gói `.tgz`, tạo manifest/SHA-256, chia part và phát hành GitHub Release.

## Chạy

Vào **Actions → Build hosted ROM → Run workflow**, dán URL ROM và bấm **Run workflow**. Không cần cấu hình runner.

Hoặc tạo Issue:

```text
/mod-rom https://example.com/device_images_version.tgz
```

Chỉ OWNER/MEMBER/COLLABORATOR được phép kích hoạt bằng Issue.

## Logic tính năng

Giữ cấu trúc 7 nhóm của Tool-Tree trong `profiles/all.env` và engine rule-based `scripts/patch_engine.py`:

- Framework/property patches.
- CN ROM/property and XML cleanup.
- Keyboard package/overlay hooks.
- Other restrictions and FPS/property patches.
- App patch hook directory.
- Add system apps from `assets/apps/<partition>/`.
- Boot/vendor_boot hook.

### Giới hạn trung thực

`patch-rom` gốc là ELF Android ARM64 đóng/strip, không có mã nguồn quy tắc smali và không thể chạy nguyên bản trên Ubuntu x86. Bản hosted giữ **pipeline, feature flags và các rule công khai có thể tái tạo**, nhưng không giả vờ sao chép byte-for-byte các vá APK/JAR kín. Các rule không thể tái tạo được ghi `unsupported` trong `patch-report.json`; bạn có thể thêm rule hoặc APK vào thư mục plugin mà không đổi workflow.

## ROM lớn

ROM mẫu khoảng 9,62 GB. Workflow dùng `maximize-build-space`, xử lý có kiểm soát dung lượng và chia Release thành part 1.9 GB. GitHub-hosted runner vẫn có thể hết dung lượng với ROM sau giải nén quá lớn; khi đó dùng runner dung lượng lớn của GitHub hoặc giảm `TARGET_PARTITIONS`.

## Thêm ứng dụng

Đặt APK theo cấu trúc:

```text
assets/apps/product/YourApp/YourApp.apk
assets/apps/system_ext/AnotherApp/AnotherApp.apk
```

Engine sẽ chép vào `app/` của phân vùng tương ứng và ghi báo cáo.

## An toàn

ROM mod không còn chữ ký OTA chính thức. Kiểm tra manifest và SHA-256; thử trên thiết bị phụ. Vá image sai có thể bootloop hoặc mất dữ liệu.
