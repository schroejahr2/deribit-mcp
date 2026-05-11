#!/usr/bin/env python3
"""Download a local snapshot of the official Deribit API docs."""

from __future__ import annotations

import json
import re
import time
from datetime import datetime, timezone
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import urlparse
from urllib.request import Request, urlopen


BASE_URL = "https://docs.deribit.com"
DOCS_ROOT = Path(__file__).resolve().parents[1] / "docs" / "deribit-api"
PAGES_ROOT = DOCS_ROOT / "pages"
SPECS_ROOT = DOCS_ROOT / "specs"
USER_AGENT = "deribit-mcp-doc-snapshot/1.0"
TIMEOUT_SECONDS = 30


def fetch(url: str) -> bytes:
    request = Request(url, headers={"User-Agent": USER_AGENT})
    with urlopen(request, timeout=TIMEOUT_SECONDS) as response:
        return response.read()


def local_path(root: Path, url: str) -> Path:
    parsed = urlparse(url)
    path = parsed.path.lstrip("/")
    if not path:
        path = "index.md"
    return root / path


def extract_links(llms_text: str) -> list[str]:
    pattern = re.compile(r"\[[^\]]+\]\((https://docs\.deribit\.com/[^)\s]+)\)")
    return sorted(set(pattern.findall(llms_text)))


def write_bytes(path: Path, content: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(content)


def main() -> int:
    DOCS_ROOT.mkdir(parents=True, exist_ok=True)
    PAGES_ROOT.mkdir(parents=True, exist_ok=True)
    SPECS_ROOT.mkdir(parents=True, exist_ok=True)

    started_at = datetime.now(timezone.utc)
    llms_url = f"{BASE_URL}/llms.txt"
    llms_bytes = fetch(llms_url)
    llms_text = llms_bytes.decode("utf-8")
    write_bytes(DOCS_ROOT / "llms.txt", llms_bytes)

    links = extract_links(llms_text)
    markdown_links = [
        url for url in links if urlparse(url).path.endswith(".md")
    ]
    spec_links = [
        url
        for url in links
        if urlparse(url).path.endswith(".json")
        and (
            "/specifications/" in urlparse(url).path
            or urlparse(url).path.endswith("/openapi.json")
        )
    ]

    failures: list[dict[str, str]] = []
    saved_pages: list[str] = []
    saved_specs: list[str] = []

    for url in markdown_links:
        destination = local_path(PAGES_ROOT, url)
        try:
            write_bytes(destination, fetch(url))
            saved_pages.append(str(destination.relative_to(DOCS_ROOT)))
        except (HTTPError, URLError, TimeoutError, OSError) as exc:
            failures.append({"url": url, "error": str(exc)})
        time.sleep(0.05)

    for url in spec_links:
        destination = local_path(SPECS_ROOT, url)
        try:
            write_bytes(destination, fetch(url))
            saved_specs.append(str(destination.relative_to(DOCS_ROOT)))
        except (HTTPError, URLError, TimeoutError, OSError) as exc:
            failures.append({"url": url, "error": str(exc)})
        time.sleep(0.05)

    manifest = {
        "source": llms_url,
        "fetched_at": started_at.isoformat(),
        "markdown_pages": len(saved_pages),
        "spec_files": len(saved_specs),
        "failures": failures,
        "saved_pages": saved_pages,
        "saved_specs": saved_specs,
    }
    (DOCS_ROOT / "manifest.json").write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    readme = f"""# Deribit API Docs Snapshot

Local snapshot of the official Deribit API documentation.

- Source index: `{llms_url}`
- Fetched at: `{started_at.isoformat()}`
- Markdown pages: `{len(saved_pages)}`
- Spec files: `{len(saved_specs)}`
- Failures: `{len(failures)}`

Layout:

- `llms.txt` - official Deribit docs index used for this snapshot
- `pages/` - Markdown pages from the Deribit docs site
- `specs/` - OpenAPI and AsyncAPI JSON specifications
- `manifest.json` - machine-readable inventory and fetch status

Refresh:

```bash
python3 scripts/update_deribit_docs.py
```
"""
    (DOCS_ROOT / "README.md").write_text(readme, encoding="utf-8")

    print(
        "Downloaded "
        f"{len(saved_pages)} markdown pages and {len(saved_specs)} specs "
        f"to {DOCS_ROOT}"
    )
    if failures:
        print(f"{len(failures)} downloads failed; see manifest.json")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
