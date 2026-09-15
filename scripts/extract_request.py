#!/usr/bin/env python3
import json,os,re,sys,urllib.parse
body=''; ep=os.getenv('GITHUB_EVENT_PATH','')
if ep and os.path.exists(ep):
 e=json.load(open(ep,encoding='utf-8')); body=(e.get('comment') or e.get('issue') or {}).get('body','') or ''
url=os.getenv('INPUT_ROM_URL','').strip()
if not url:
 m=re.search(r'(?im)^\s*/mod-rom\s+(https://\S+)',body); url=m.group(1).rstrip('.,;)]') if m else ''
u=urllib.parse.urlparse(url)
if u.scheme!='https' or not u.hostname or not re.search(r'\.(?:tgz|tar\.gz)(?:$|\?)',url,re.I): sys.exit('Cần URL HTTPS .tgz/.tar.gz')
out=os.getenv('GITHUB_OUTPUT')
line=f'rom_url={url}\n'
open(out,'a').write(line) if out else print(line,end='')
