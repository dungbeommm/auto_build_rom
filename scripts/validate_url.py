#!/usr/bin/env python3
import ipaddress
import socket
import sys
import urllib.parse

ALLOWED = (
    "aliyuncs.com",
    "bigota.d.miui.com",
    "hugeota.d.miui.com",
    "cdn-ota.azureedge.net",
    "github.com",
    "githubusercontent.com",
)


def allowed_host(host: str) -> bool:
    return any(host == suffix or host.endswith("." + suffix) for suffix in ALLOWED)


def main() -> int:
    if len(sys.argv) != 2:
        raise SystemExit("Usage: validate_url.py URL")
    parsed = urllib.parse.urlparse(sys.argv[1])
    host = (parsed.hostname or "").rstrip(".").lower()
    if parsed.scheme != "https" or not host or parsed.username or parsed.password:
        raise SystemExit("Chỉ chấp nhận URL HTTPS không chứa thông tin đăng nhập")
    if parsed.port not in (None, 443):
        raise SystemExit("Chỉ chấp nhận cổng HTTPS 443")
    if not allowed_host(host):
        raise SystemExit(f"Host không nằm trong allowlist: {host}")
    if not parsed.path.lower().endswith((".tgz", ".tar.gz")):
        raise SystemExit("Tệp ROM phải có đuôi .tgz hoặc .tar.gz")
    addresses = {item[4][0] for item in socket.getaddrinfo(host, 443, type=socket.SOCK_STREAM)}
    if not addresses:
        raise SystemExit("Không phân giải được host")
    for value in addresses:
        if not ipaddress.ip_address(value).is_global:
            raise SystemExit(f"Từ chối địa chỉ không công khai: {value}")
    print(host)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
