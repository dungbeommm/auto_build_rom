#!/usr/bin/env python3
import json
import os
import re
import sys
import urllib.parse


def event_body() -> str:
    event_path = os.getenv("GITHUB_EVENT_PATH", "")
    if not event_path or not os.path.isfile(event_path):
        return ""
    with open(event_path, encoding="utf-8") as handle:
        event = json.load(handle)
    source = event.get("comment") or event.get("issue") or {}
    return source.get("body", "") or ""


def main() -> int:
    url = os.getenv("INPUT_ROM_URL", "").strip()
    if not url:
        match = re.search(r"(?im)^\s*/mod-rom\s+(https://\S+)", event_body())
        url = match.group(1).rstrip(".,;)]") if match else ""
    if "\n" in url or "\r" in url:
        raise SystemExit("URL không được chứa ký tự xuống dòng")
    parsed = urllib.parse.urlparse(url)
    if parsed.scheme != "https" or not parsed.hostname:
        raise SystemExit("Cần URL HTTPS hợp lệ")
    if not re.search(r"\.(?:tgz|tar\.gz)$", parsed.path, re.IGNORECASE):
        raise SystemExit("URL phải trỏ tới tệp .tgz hoặc .tar.gz")
    output = os.getenv("GITHUB_OUTPUT")
    if output:
        with open(output, "a", encoding="utf-8") as handle:
            handle.write(f"rom_url={url}\n")
    else:
        print(url)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
