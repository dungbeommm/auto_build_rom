#!/usr/bin/env python3
import ipaddress,socket,sys,urllib.parse
u=urllib.parse.urlparse(sys.argv[1]); h=(u.hostname or '').lower()
allow=('.aliyuncs.com','bigota.d.miui.com','hugeota.d.miui.com','cdn-ota.azureedge.net','.githubusercontent.com','github.com')
if u.scheme!='https' or u.username or u.password or not any(h==x.lstrip('.') or h.endswith(x) for x in allow): sys.exit('URL/host không được phép')
for x in socket.getaddrinfo(h,443,type=socket.SOCK_STREAM):
 if not ipaddress.ip_address(x[4][0]).is_global: sys.exit('Từ chối IP không công khai')
print(h)
