# ToolTree HyperOS AutoBuilder

Bản viết lại dùng kiến trúc Python của **HyperOS-Port-Python**, thay cho chuỗi shell phụ thuộc Android runner. Dự án chạy trực tiếp trên GitHub-hosted `ubuntu-24.04`.

## Các nhóm tính năng

- Tải ROM bằng aria2: tiếp tục file dở, nhiều kết nối, cache tên file.
- Đọc Xiaomi Fastboot `.tgz`/`.tar.gz`/`.zip`, OTA `payload.bin`, ZIP chứa payload và thư mục ROM đã giải nén.
- Giải `super.img`, sparse/split sparse, EROFS/EXT4; nhận phân vùng `_a`.
- Vá `framework.jar`, `services.jar`, `miui-services.jar` bằng smali; bỏ kiểm tra chữ ký/hạ cấp theo engine có sẵn.
- Vá ứng dụng theo plugin: Settings, SecurityCenter, Installer, PowerKeeper, Joyose, HTMLViewer, overlay thiết bị.
- Mở khóa feature XML/build.prop, CN/global/EU localization, file replacement và thêm app qua cấu hình.
- Xử lý firmware, `boot.img`, `vendor_boot.img`, AVB, repack `super` hoặc `payload`.
- Preflight, snapshot/cache/diff report và release manifest SHA-256.

> Một ROM đã sửa có thể không boot nếu cấu hình thiết bị, kích thước super hoặc AVB không phù hợp. Luôn mở khóa bootloader và giữ ROM gốc để khôi phục.

## Cách dùng trên GitHub

1. Tạo repository mới và tải toàn bộ nội dung dự án này lên **đúng thư mục gốc**.
2. Mở **Actions → Build modified HyperOS ROM → Run workflow**.
3. Dán `stock_url`. Để trống `port_url` nếu chỉ muốn sửa ROM chính thức.
4. Chọn `super` (gói hybrid flash) hoặc `payload`.
5. Tải các part trong Release, đặt cùng thư mục và chạy `python JOIN.py`.

Cũng có thể bình luận trong Issue:

```text
/mod-rom https://.../rom.tgz
```

Port hai ROM:

```text
/mod-rom https://.../stock.tgz port=https://.../port.zip
```

## Chạy cục bộ

Yêu cầu Linux x86_64, Python 3.11+, Java, khoảng 40–80 GiB trống.

```bash
python -m pip install -r requirements.txt
chmod +x bin/linux/x86_64/* bin/flash/zstd
export PATH="$PWD/bin/linux/x86_64:$PWD/bin/flash:$PATH"
python main.py --stock 'https://.../rom.tgz' --pack-type super --fs-type erofs --clean \
  --enable-diff-report --diff-report build/diff-report.json
```

## Cấu hình

- `devices/common/features.json`: feature XML và build.prop.
- `devices/common/replacements.json`: thay thế/copy ứng dụng và tài nguyên.
- `devices/common/config.json`: kiểu pack, filesystem và các override chung.
- `devices/<codename>/`: ghi đè riêng cho thiết bị.
- `src/core/modifiers/plugins/`: plugin hệ thống/APK.

Dự án giữ giấy phép gốc tại `LICENSE` và bổ sung thay đổi tương thích TGZ/GitHub Actions.
