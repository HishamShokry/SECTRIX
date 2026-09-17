#!/usr/bin/env python3
"""Add rate limiting to an existing (certbot-managed) nginx vhost.

The zones are declared in deploy/nginx-security-headers.conf; they do nothing
until a `limit_req` references them from inside a location block. Certbot owns
the vhost, so this patches it in place rather than replacing it.

What it does:
  * adds `limit_req zone=general` to the existing `location /`
  * adds dedicated `location /contact/` and `location /admin/` blocks, copying
    the proxy settings from `location /` so the upstream is whatever the file
    already uses -- never a hardcoded address
  * leaves every certbot-managed line untouched

Safe to re-run: it detects its own markers and exits if already applied.
The caller is responsible for `nginx -t` and the reload.

    sudo python3 deploy/add-vhost-ratelimit.py /etc/nginx/sites-enabled/example.com
"""
import re
import sys
from pathlib import Path

MARKER = "# sectrex: rate limiting"

TUNING = {"contact": ("contact", 3), "admin": ("admin", 5)}


def find_location_root(text):
    """Return (start, end, body) for the `location / { ... }` block."""
    # [ \t]* not \s*: \s matches newlines, so a blank line before the block
    # would be captured as part of the indent and re-emitted on every line.
    match = re.search(r"\n([ \t]*)location[ \t]+/[ \t]*\{", text)
    if not match:
        return None
    indent = match.group(1)
    start = match.start() + 1
    depth = 0
    i = text.index("{", match.start())
    while i < len(text):
        if text[i] == "{":
            depth += 1
        elif text[i] == "}":
            depth -= 1
            if depth == 0:
                return start, i + 1, text[start:i + 1], indent
        i += 1
    return None


def main():
    if len(sys.argv) != 2:
        sys.exit(f"usage: {sys.argv[0]} /etc/nginx/sites-enabled/<vhost>")

    path = Path(sys.argv[1])
    if not path.is_file():
        sys.exit(f"not a file: {path}")

    text = path.read_text()

    if MARKER in text:
        print("already applied; nothing to do")
        return 0

    found = find_location_root(text)
    if not found:
        sys.exit("could not find a `location / { ... }` block to work from")
    start, end, body, indent = found

    # Reuse the proxy directives already in the file, so we inherit the
    # correct upstream instead of guessing it.
    proxy_lines = [
        line.strip()
        for line in body.splitlines()
        if line.strip().startswith(("proxy_pass", "proxy_set_header", "proxy_redirect"))
    ]
    if not any(line.startswith("proxy_pass") for line in proxy_lines):
        sys.exit("`location /` has no proxy_pass; is this the right vhost?")

    # 1. Dedicated blocks for the two sensitive paths, inserted BEFORE
    #    `location /` (nginx prefers the longest prefix match regardless of
    #    order, but keeping them first reads better).
    new_blocks = [f"{indent}{MARKER} -- zones are declared in /etc/nginx/conf.d/00-security.conf"]
    for path_name, (zone, burst) in TUNING.items():
        new_blocks.append(f"{indent}location /{path_name}/ {{")
        new_blocks.append(f"{indent}    limit_req zone={zone} burst={burst} nodelay;")
        for line in proxy_lines:
            new_blocks.append(f"{indent}    {line}")
        new_blocks.append(f"{indent}}}")
        new_blocks.append("")

    # 2. A general ceiling inside the existing `location /`.
    brace = body.index("{") + 1
    patched_root = (
        body[:brace]
        + f"\n{indent}    limit_req zone=general burst=40 nodelay;"
        + body[brace:]
    )

    text = text[:start] + "\n".join(new_blocks) + "\n" + patched_root + text[end:]
    path.write_text(text)
    print(f"patched {path}")
    print("  + location /contact/  (zone=contact, 5r/m)")
    print("  + location /admin/    (zone=admin,  20r/m)")
    print("  + limit_req zone=general in location /")
    return 0


if __name__ == "__main__":
    sys.exit(main())
