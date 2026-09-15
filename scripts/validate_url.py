#!/usr/bin/env python3
import argparse, ipaddress, socket, urllib.parse

DEFAULT_SUFFIXES=(
    '.aliyuncs.com','bigota.d.miui.com','hugeota.d.miui.com',
    'cdn-ota.azureedge.net','github.com','githubusercontent.com'
)

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('url'); ap.add_argument('--allow-host',action='append',default=[])
    a=ap.parse_args(); u=urllib.parse.urlparse(a.url)
    if u.scheme!='https' or not u.hostname or u.username or u.password:
        raise SystemExit('URL phải là HTTPS và không chứa thông tin đăng nhập')
    host=u.hostname.rstrip('.').lower()
    allow=tuple(x.lower() for x in (a.allow_host or DEFAULT_SUFFIXES))
    if not any(host==x.lstrip('.') or host.endswith(x if x.startswith('.') else '.'+x) for x in allow):
        raise SystemExit(f'Host không nằm trong allowlist: {host}')
    for item in socket.getaddrinfo(host,443,type=socket.SOCK_STREAM):
        ip=ipaddress.ip_address(item[4][0])
        if not ip.is_global:
            raise SystemExit(f'Từ chối địa chỉ không công khai: {ip}')
    print(host)
if __name__=='__main__': main()
