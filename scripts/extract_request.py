#!/usr/bin/env python3
import json
import os
import re
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


def validate(url: str, *, optional: bool = False) -> str:
    url = url.strip()
    if optional and not url:
        return ""
    if "\r" in url or "\n" in url:
        raise SystemExit("URL contains a newline")
    parsed = urllib.parse.urlparse(url)
    host = (parsed.hostname or "").rstrip(".").lower()
    if parsed.scheme != "https" or parsed.username or parsed.password or parsed.port not in (None, 443):
        raise SystemExit("Only HTTPS URLs on port 443 are accepted")
    if not any(host == suffix or host.endswith("." + suffix) for suffix in ALLOWED):
        raise SystemExit(f"Host not allowed: {host}")
    if not parsed.path.lower().endswith((".zip", ".tgz", ".tar.gz", ".bin")):
        raise SystemExit("ROM must be .zip, .tgz, .tar.gz, or payload .bin")
    return url


def main() -> int:
    stock = os.getenv("INPUT_STOCK_URL", "").strip()
    port = os.getenv("INPUT_PORT_URL", "").strip()
    event_path = os.getenv("GITHUB_EVENT_PATH", "")
    body = ""
    if event_path and os.path.isfile(event_path):
        with open(event_path, encoding="utf-8") as handle:
            event = json.load(handle)
        body = ((event.get("comment") or event.get("issue") or {}).get("body") or "")
    if not stock:
        match = re.search(r"(?im)^\s*/mod-rom\s+(https://\S+)", body)
        stock = match.group(1).rstrip(".,;)]") if match else ""
    if not port:
        match = re.search(r"(?i)\bport=(https://\S+)", body)
        port = match.group(1).rstrip(".,;)]") if match else ""
    stock = validate(stock)
    port = validate(port, optional=True)
    output = os.getenv("GITHUB_OUTPUT")
    text = f"stock_url={stock}\nport_url={port}\n"
    if output:
        with open(output, "a", encoding="utf-8") as handle:
            handle.write(text)
    else:
        print(text, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
