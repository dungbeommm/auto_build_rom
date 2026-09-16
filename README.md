# ROM Auto Builder — HyperOS / Xiaomi ROM GitHub Actions

Tool tự động hóa ROM theo pipeline:

`URL ROM -> download -> preflight -> unpack -> port/sync -> framework/APK patch -> boot/vendor_boot patch -> rebuild EROFS/ext4 -> super.img hoặc payload -> report + artifact`

Engine này lấy phần porting/unpack/repack từ bộ HyperOS-Port-Python bạn cung cấp và thêm một lớp Python `romauto` để điều phối profile, patch và GitHub Actions. Tool-Tree được lấy từ upstream theo tag để có các binary unpack/repack cần thiết thay vì nhúng binary khổng lồ vào repository.

## GitHub Actions

Vào **Actions → Build ROM → Run workflow** rồi nhập:

- `stock_url`: URL trực tiếp tới ROM stock.
- `port_url`: URL trực tiếp tới ROM port; bỏ trống để chạy official-modification mode.
- `profile`: file JSON profile, ví dụ `config/profiles/default.json`.
- `pack_type`: `super` hoặc `payload`.
- `fs_type`: `erofs` hoặc `ext4`.
- `device`: mã máy nếu muốn khóa profile thiết bị.

### URL ROM

Khuyến nghị URL trả trực tiếp file ZIP/Payload và có thể tải không cần cookie đăng nhập. Engine tải file theo HTTP và giữ cache trong workspace.

## Feature model

Các chức năng tương ứng menu Tool-Tree được map thành feature Python:

| Feature | Vai trò |
|---|---|
| `cn_global_patch` | patch property/rule để thích nghi CN/Global |
| `keyboard_unlock` | patch property/resource theo profile |
| `framework_patch_rules` | patch file/rule cho framework |
| `app_patches` | sửa/copy/delete thành phần APK |
| `add_apps` | thêm APK vào partition |
| `boot_patch` | overlay ramdisk cho `boot.img` |
| `vendor_boot_patch` | overlay ramdisk cho `vendor_boot.img` |
| `delete_apps` | loại bỏ app theo glob |
| `other_patches` | rule tổng quát |

Không có một patch “CN/Global” hay “advanced keyboard” duy nhất chạy đúng cho mọi HyperOS/Android version. Vì vậy các thay đổi có tính phụ thuộc ROM nằm trong JSON rule/profile; engine chỉ thực hiện đúng rule đã khai báo.

## Tool-Tree

Mặc định workflow pin `TOOL_TREE_REF=V1.6.0`. Có thể đổi qua environment variable hoặc repository variable. Binary được lấy từ `.github/module/bin` của Tool-Tree và dùng cho `magiskboot`, `lpmake`, `lpunpack`, `mkfs.erofs`, `extract.erofs`, `avbtool` và các utility liên quan.

## Super image

Dynamic partitions Android dùng `super` để chứa các partition động như `system`, `vendor`, `product`, `system_ext`, `odm`. Khi build `super.img`, profile thiết bị phải có kích thước/layout phù hợp. Tool kiểm tra `super_size` và ghi cảnh báo nếu `devices/<codename>/partition_info.json` không khớp.

## Boot / AVB

`boot.img`, `vendor_boot.img` và `vbmeta` có quan hệ với Android Verified Boot. Pipeline không tự ký bằng khóa OEM. Nếu build cần re-sign AVB, đưa khóa riêng vào workflow/repository secret và profile hóa phần ký. Không nên nhúng private key vào Git.

## Local

```bash
python -m pip install -r requirements.txt
python -m romauto.run \\
  --config config/profiles/default.json \\
  --stock "https://example.com/stock.zip" \\
  --port "https://example.com/port.zip" \\
  --pack-type super \\
  --fs-type erofs \\
  --tool-tree
```

## Cấu trúc

- `src/`: engine HyperOS-Port-Python nền.
- `romauto/`: orchestration layer mới.
- `config/profiles/`: profile ROM.
- `patches/`: rule patch.
- `assets/apps/`: APK bổ sung do người dùng cung cấp.
- `.github/workflows/`: CI và build ROM tự động.

## Giới hạn quan trọng

ROM Android vendor-specific không thể đảm bảo một bộ byte patch dùng chung cho mọi thiết bị. Tự động hóa đáng tin cậy cần profile theo codename, Android/HyperOS version, file system, partition layout và phiên bản framework. Pipeline vì thế ưu tiên **fail rõ ràng + report** thay vì âm thầm tạo image có nguy cơ bootloop.
