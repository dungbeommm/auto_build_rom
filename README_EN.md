# HyperOS ROM Modifier

Tool này giữ pipeline xử lý ROM của dự án gốc nhưng chỉ làm việc với **một ROM đầu vào**. Toàn bộ luồng Port ROM/cross-ROM đã được loại bỏ.

## Pipeline

1. Nhận ROM ZIP/payload/thư mục hoặc URL.
2. Preflight kiểm tra định dạng và môi trường.
3. Download ROM nếu là URL.
4. Unpack payload/super và giải nén các phân vùng Android cần chỉnh sửa.
5. Tạo workspace `build/rom`, `build/target`.
6. Tạo/đọc cấu hình thiết bị.
7. Chạy các modifier system/APK/framework/firmware.
8. Áp dụng override và patch theo device/Android version.
9. Repack các image.
10. Tạo `super.img` hoặc OTA payload.
11. Sinh snapshot, diff report và checkpoint để resume.

## Chạy

```bash
python3 main.py --rom /path/to/rom.zip
python3 main.py --rom /path/to/rom.zip --pack-type super
python3 main.py --rom /path/to/rom.zip --phases system apk framework firmware repack
```

## Cấu trúc runtime

```text
build/
├── rom/             # dữ liệu đã unpack từ ROM duy nhất
├── target/          # workspace chỉnh sửa
├── snapshots/
├── preflight-report.json
├── diff-report.json
├── repack-context.json
└── rom_debug.prop
```

Không còn tham số `--port`, không tạo `portrom`, không có chế độ Port ROM và không thực hiện sao chép thành phần từ một ROM thứ hai.
