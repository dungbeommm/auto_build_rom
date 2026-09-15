#!/usr/bin/env python3
import json, os, re, sys, urllib.parse

URL_RE = re.compile(r'https://[^\s<>()\]"\']+?\.(?:tgz|tar\.gz)(?:\?[^\s<>()\]"\']*)?', re.I)

def main():
    event_path=os.environ.get('GITHUB_EVENT_PATH')
    explicit=os.environ.get('INPUT_ROM_URL','').strip()
    profile=os.environ.get('INPUT_PROFILE','all').strip() or 'all'
    body=''
    if event_path and os.path.exists(event_path):
        event=json.load(open(event_path, encoding='utf-8'))
        body=(event.get('comment') or event.get('issue') or {}).get('body','') or ''
    url=explicit
    if not url:
        command=re.search(r'(?im)^\s*/mod-rom\s+(https://\S+)', body)
        if command: url=command.group(1).rstrip('.,;)]')
        else:
            found=URL_RE.search(body)
            if found: url=found.group(0)
        m=re.search(r'\bprofile=([A-Za-z0-9_-]+)', body)
        if m: profile=m.group(1)
    if not url:
        print('Không tìm thấy URL ROM HTTPS .tgz/.tar.gz', file=sys.stderr); return 2
    parsed=urllib.parse.urlparse(url)
    if parsed.scheme!='https' or not parsed.hostname:
        print('Chỉ chấp nhận URL HTTPS hợp lệ', file=sys.stderr); return 2
    out=os.environ.get('GITHUB_OUTPUT')
    lines=f'rom_url={url}\nprofile={profile}\n'
    if out: open(out,'a',encoding='utf-8').write(lines)
    else: print(lines,end='')
    return 0
if __name__=='__main__': raise SystemExit(main())
