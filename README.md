# ROM Auto Modder for Tool-Tree

Dự án GitHub tự nhận liên kết ROM Xiaomi Fastboot (`.tgz`), tải ROM, giải nén các phân vùng cần thiết, gọi **engine Patch ROM của Tool-Tree**, đóng gói lại và phát hành ROM đã mod.

> ROM mẫu đã xác minh: `houji_images_OS3.0.305.0.WNCCNXM_20260727.0000.00_16.0_cn_545a3c8afe.tgz` (~9,62 GB).

## Tính năng

- Tự bắt URL ROM từ **GitHub Issue**, bình luận Issue hoặc `workflow_dispatch`.
- Hỗ trợ tiếp tục tải (`curl -C -`) và kiểm tra URL/host/kích thước/dung lượng trống.
- Unpack: `system`, `system_ext`, `product`, `vendor`, `mi_ext`, `boot`, `vendor_boot` khi tồn tại.
- Áp dụng 7 nhóm vá: framework, ROM CN, bàn phím nâng cao, các bản vá khác, ứng dụng, thêm ứng dụng, `boot/vendor_boot`.
- Repack các image, thay vào cây Fastboot ROM, tạo `.tgz`, SHA-256 và manifest.
- Tự chia ROM thành phần nhỏ hơn 2 GB để tải lên GitHub Release; kèm script ghép lại.
- Có khóa chống SSRF và chỉ cho phép OWNER/MEMBER/COLLABORATOR kích hoạt từ Issue.

## Yêu cầu bắt buộc

Engine `patch-rom` gốc là **ELF Android ARM64** với interpreter `/system/bin/linker64`; vì vậy job vá thật phải chạy trên **self-hosted GitHub Actions runner đặt trên Android ARM64 đã root**, có Tool-Tree được cài/khởi tạo. Không thể chạy engine này trên runner Ubuntu x86_64 của GitHub.

Khuyến nghị:

- Android ARM64 đã root, trống ít nhất **50–80 GB**.
- Tool-Tree 1.6.x đã mở ít nhất một lần.
- Runner có nhãn: `self-hosted`, `android`, `arm64`, `tool-tree`.
- Có `bash`, `curl`, `tar`, `gzip`, `find`, `sha256sum`, `split`, `gh`.
- Biến runner `TOOLTREE_HOME=/data/data/com.tool.tree/files/home` nếu dùng đường dẫn khác.

Xem [docs/SETUP_RUNNER.md](docs/SETUP_RUNNER.md).

## Cách dùng

### GitHub Issue

Tạo Issue hoặc bình luận bằng nội dung:

```text
/mod-rom https://example.com/device_images_xxx.tgz
```

Có thể thêm profile:

```text
/mod-rom https://example.com/device_images_xxx.tgz profile=all
```

### Chạy thủ công

Vào **Actions → Build modded ROM → Run workflow**, nhập `rom_url` và profile `all`.

### Chạy cục bộ trên thiết bị Android

```bash
export ROM_URL='https://example.com/device_images_xxx.tgz'
export PATCH_PROFILE=profiles/all.env
export TOOLTREE_HOME=/data/data/com.tool.tree/files/home
./scripts/rom_pipeline.sh
```

## Cảnh báo

- Sao lưu và kiểm tra ROM trên thiết bị thử nghiệm. Vá framework/boot sai có thể gây bootloop hoặc mất dữ liệu.
- Thiết bị MTK có thể treo khi vá `boot/vendor_boot`.
- ROM đầu ra không mang chữ ký OTA chính thức và thường chỉ phù hợp để flash bằng Fastboot/recovery tùy chỉnh.
- Dự án không tự vượt khóa bootloader, AVB hoặc cơ chế bảo vệ thiết bị.
- Mã Tool-Tree được giữ nguyên giấy phép và nguồn gốc trong `vendor/tool-tree/patch_rom`.
