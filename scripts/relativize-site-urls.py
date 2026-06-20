#!/usr/bin/env python3
"""Make generated Zola links portable across GitHub Pages and a custom domain."""

from __future__ import annotations

import argparse
import os
import re
from pathlib import Path
from urllib.parse import urlsplit, urlunsplit


HTML_URL_ATTR_RE = re.compile(
    r"(?P<prefix>\b(?:href|src|srcset)=)(?P<quote>[\"'])(?P<value>[^\"']*)(?P=quote)"
)
CSS_URL_RE = re.compile(
    r"url\((?P<quote>[\"']?)(?P<value>(?:https?://[^)\"']+|/[^)\"']*))(?P=quote)\)"
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("output_dir", type=Path)
    parser.add_argument("base_url")
    return parser.parse_args()


def normalized_base_url(base_url: str) -> str:
    return base_url.rstrip("/")


def site_url_path(value: str, base_url: str) -> str | None:
    if value.startswith(base_url + "/"):
        return value[len(base_url) :]
    if value == base_url:
        return "/"
    if value.startswith("/") and not value.startswith("//"):
        return value
    return None


def relpath_posix(path: Path, start: Path) -> str:
    return Path(os.path.relpath(path, start)).as_posix()


def relative_site_url(value: str, current_file: Path, output_dir: Path, base_url: str) -> str:
    path_value = site_url_path(value, base_url)
    if path_value is None:
        return value

    parsed = urlsplit(path_value)
    if not parsed.path.startswith("/"):
        return value

    current_dir = current_file.parent
    root = output_dir.resolve()
    target_path = parsed.path.lstrip("/")

    if parsed.path in ("", "/"):
        relative_path = relpath_posix(root, current_dir)
        if relative_path == ".":
            relative_path = "./"
        elif not relative_path.endswith("/"):
            relative_path += "/"
    else:
        target = root / target_path
        relative_path = relpath_posix(target, current_dir)
        if parsed.path.endswith("/") and not relative_path.endswith("/"):
            relative_path += "/"

    return urlunsplit(("", "", relative_path, parsed.query, parsed.fragment))


def relative_srcset(value: str, current_file: Path, output_dir: Path, base_url: str) -> str:
    candidates = []
    for candidate in value.split(","):
        leading = candidate[: len(candidate) - len(candidate.lstrip())]
        parts = candidate.strip().split(None, 1)
        if not parts:
            candidates.append(candidate)
            continue

        url = relative_site_url(parts[0], current_file, output_dir, base_url)
        descriptor = f" {parts[1]}" if len(parts) > 1 else ""
        candidates.append(f"{leading}{url}{descriptor}")
    return ",".join(candidates)


def rewrite_html(path: Path, output_dir: Path, base_url: str) -> None:
    original = path.read_text()

    def replace(match: re.Match[str]) -> str:
        tag_start = original.rfind("<", 0, match.start())
        tag_end = original.find(">", match.end())
        tag = original[tag_start : tag_end + 1] if tag_start != -1 and tag_end != -1 else ""
        if re.search(r"\brel=[\"']canonical[\"']", tag):
            return match.group(0)

        value = match.group("value")
        if match.group("prefix").lower().startswith("srcset"):
            value = relative_srcset(value, path, output_dir, base_url)
        else:
            value = relative_site_url(value, path, output_dir, base_url)
        return f"{match.group('prefix')}{match.group('quote')}{value}{match.group('quote')}"

    rewritten = HTML_URL_ATTR_RE.sub(replace, original)
    if rewritten != original:
        path.write_text(rewritten)


def rewrite_css(path: Path, output_dir: Path, base_url: str) -> None:
    original = path.read_text()

    def replace(match: re.Match[str]) -> str:
        value = relative_site_url(match.group("value"), path, output_dir, base_url)
        quote = match.group("quote")
        return f"url({quote}{value}{quote})"

    rewritten = CSS_URL_RE.sub(replace, original)
    if rewritten != original:
        path.write_text(rewritten)


def main() -> None:
    args = parse_args()
    output_dir = args.output_dir.resolve()
    base_url = normalized_base_url(args.base_url)

    for path in output_dir.rglob("*.html"):
        rewrite_html(path, output_dir, base_url)

    for path in output_dir.rglob("*.css"):
        rewrite_css(path, output_dir, base_url)


if __name__ == "__main__":
    main()
