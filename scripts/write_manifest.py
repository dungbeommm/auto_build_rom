#!/usr/bin/env python3
import argparse, hashlib, json, os, time

def digest(path):
    h=hashlib.sha256()
    with open(path,'rb') as f:
        for b in iter(lambda:f.read(8*1024*1024),b''): h.update(b)
    return h.hexdigest()
a=argparse.ArgumentParser()
a.add_argument('--url',required=True); a.add_argument('--input',required=True); a.add_argument('--output',required=True); a.add_argument('--profile',required=True)
x=a.parse_args()
print(json.dumps({'schema':1,'created_at':time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime()),'source_url':x.url,'source':{'name':os.path.basename(x.input),'size':os.path.getsize(x.input),'sha256':digest(x.input)},'output':{'name':os.path.basename(x.output),'size':os.path.getsize(x.output),'sha256':digest(x.output)},'profile':os.path.basename(x.profile)},ensure_ascii=False,indent=2))
