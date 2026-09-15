# Thiết lập self-hosted runner Android ARM64

## 1. Chuẩn bị thiết bị

1. Dùng thiết bị Android ARM64 đã root, dung lượng trống tối thiểu 50–80 GB.
2. Cài Tool-Tree, mở ứng dụng một lần và cho phép root/bộ nhớ.
3. Xác nhận tồn tại:
   - `/data/data/com.tool.tree/files/home/bin/unpack_img`
   - `/data/data/com.tool.tree/files/home/bin/repack_img`
   - `/system/bin/linker64`
4. Cài Termux và các lệnh: `bash curl tar gzip python git gh coreutils findutils`.

## 2. Cài GitHub Actions runner

Trong repository: **Settings → Actions → Runners → New self-hosted runner**. Chọn Linux/ARM64 và chạy các lệnh GitHub cung cấp trong Termux hoặc môi trường root phù hợp.

Thêm nhãn khi cấu hình:

```text
android,arm64,tool-tree
```

Runner phải chạy dưới tài khoản có thể đọc thư mục dữ liệu Tool-Tree và ghi vào bộ nhớ dùng cho job.

## 3. Dung lượng và đường dẫn

Mặc định pipeline dùng `${RUNNER_TEMP}` hoặc `/sdcard/TREE/auto-rom`. Có thể cấu hình biến môi trường runner:

```bash
export TOOLTREE_HOME=/data/data/com.tool.tree/files/home
export WORK_ROOT=/sdcard/TREE/auto-rom
export MAX_ROM_BYTES=15000000000
```

ROM mẫu gần 9,62 GB; pipeline cần xấp xỉ bốn lần kích thước ROM trong lúc tải, giải nén, dựng image và đóng gói.

## 4. Bảo mật

- Chỉ OWNER/MEMBER/COLLABORATOR được kích hoạt bằng Issue.
- `scripts/validate_url.py` chỉ nhận HTTPS, host trong allowlist và IP công khai.
- Muốn thêm CDN, chỉnh allowlist trong mã hoặc truyền đúng `EXTRA_ALLOWED_HOST` trên runner.
- Không chạy pull request không tin cậy trên runner Android có root.
