"""Measure website speed with a document fetch or optional Chromium browser."""

import argparse
import time
from http.client import HTTPException
from urllib.error import HTTPError, URLError
from urllib.parse import urlsplit, urlunsplit
from urllib.request import Request, urlopen

MAX_BYTES = 10 * 1024 * 1024


def parse_website(value):
    """Normalize a hostname or HTTP/HTTPS URL, defaulting to HTTPS."""
    value = value.strip()
    if not value:
        raise ValueError("Enter a hostname or HTTP/HTTPS URL.")
    url = value if "://" in value else "https://" + value
    if any(character.isspace() or ord(character) < 32 for character in url):
        raise ValueError("URLs must not contain spaces or control characters.")
    parsed = urlsplit(url)
    if parsed.scheme.lower() not in ("http", "https"):
        raise ValueError("Only HTTP and HTTPS URLs are supported.")
    if not parsed.hostname or parsed.username is not None or parsed.password is not None:
        raise ValueError("Enter a valid website without embedded credentials.")
    port = parsed.port
    if port is not None and not 1 <= port <= 65535:
        raise ValueError("The port must be between 1 and 65535.")
    hostname = parsed.hostname.encode("idna").decode("ascii")
    authority = f"[{hostname}]" if ":" in hostname else hostname
    if port is not None:
        authority += f":{port}"
    return urlunsplit((parsed.scheme.lower(), authority, parsed.path or "/", parsed.query, ""))


def check_speed(url, timeout=10, max_bytes=MAX_BYTES):
    """Fetch one document, recording headers and body timing with bounded reading."""
    if max_bytes < 1:
        raise ValueError("The download limit must be positive.")
    request = Request(url, headers={
        "User-Agent": "Site-Speed-Check/1.0",
        "Accept-Encoding": "identity",
    })
    started = time.perf_counter()
    try:
        response = urlopen(request, timeout=timeout)
    except HTTPError as error:
        response = error
    with response:
        headers_at = time.perf_counter()
        downloaded = 0
        complete = False
        # Read one extra byte to distinguish a complete body from a capped sample.
        while downloaded <= max_bytes:
            chunk = response.read(min(64 * 1024, max_bytes + 1 - downloaded))
            if not chunk:
                complete = True
                break
            downloaded += len(chunk)
        finished = time.perf_counter()
        body_seconds = finished - headers_at
        return {
            "url": response.geturl(),
            "status": response.code,
            "reason": str(response.reason),
            "headers_ms": (headers_at - started) * 1000,
            "download_ms": body_seconds * 1000,
            "total_ms": (finished - started) * 1000,
            "bytes": downloaded,
            "complete": complete,
            "kib_per_second": downloaded / 1024 / body_seconds if body_seconds > 0 else None,
        }


def check_browser_speed(url):
    """Measure browser navigation and paint milestones in a fresh context."""
    try:
        from playwright.sync_api import Error, sync_playwright
    except ImportError as error:
        raise RuntimeError(
            "Browser mode requires Playwright. Run: python -m pip install playwright "
            "and then: python -m playwright install chromium"
        ) from error
    try:
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(headless=True)
            try:
                context = browser.new_context(viewport={"width": 1365, "height": 768})
                page = context.new_page()
                failures = []
                http_errors = []
                page.on("requestfailed", lambda request: failures.append(request.url))
                page.on("response", lambda response: http_errors.append(response.url)
                        if response.status >= 400 else None)
                page.add_init_script("""(() => {
                    performance.setResourceTimingBufferSize(10000);
                })();""")
                response = page.goto(url, wait_until="load", timeout=30000)
                # A fixed window includes paints and some post-load activity without
                # waiting indefinitely for pages that keep network connections open.
                page.wait_for_timeout(2000)
                result = page.evaluate("""() => {
                    const n = performance.getEntriesByType('navigation')[0];
                    const paints = performance.getEntriesByType('paint');
                    const resources = performance.getEntriesByType('resource');
                    return {
                        headers_ms: n.responseStart,
                        dom_ms: n.domContentLoadedEventEnd,
                        load_ms: n.loadEventEnd,
                        fcp_ms: paints.find(p => p.name === 'first-contentful-paint')?.startTime ?? null,
                        resources: resources.length,
                        observed_ms: performance.now()
                    };
                }""")
                result.update(url=page.url, status=response.status if response else None,
                              failed_requests=len(failures), http_errors=len(http_errors))
                return result
            finally:
                browser.close()
    except Error as error:
        raise RuntimeError(
            f"Browser measurement failed: {error}\n"
            "If Chromium is missing, run: python -m playwright install chromium"
        ) from error


def print_browser_result(url, result):
    print(f"Requested URL: {url}")
    print(f"Final URL: {result['url']}")
    print(f"HTTP status: {result['status']}")
    print(f"Time to first response byte: {result['headers_ms']:.1f} ms")
    print(f"DOM content loaded: {result['dom_ms']:.1f} ms")
    print(f"Page load event: {result['load_ms']:.1f} ms")
    fcp = result["fcp_ms"]
    print(f"First contentful paint: {fcp:.1f} ms" if fcp is not None
          else "First contentful paint: not reported")
    print(f"Completed resource timing entries (main frame): {result['resources']}")
    print(f"Failed network requests: {result['failed_requests']}")
    print(f"HTTP error responses (including assets): {result['http_errors']}")
    print(f"Observation window: {result['observed_ms']:.1f} ms since navigation")
    print("Chromium loads scripts, styles, and images; observed for 2 seconds after load.")
    print("Lazy-loaded assets and later activity may be excluded; this is not a full rendering completion time.")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("website", nargs="?", help="Hostname or HTTP/HTTPS URL")
    parser.add_argument("--browser", action="store_true",
                        help="Use Chromium to include linked assets and browser paint timing")
    args = parser.parse_args()
    try:
        value = args.website if args.website is not None else input("Website: ")
        url = parse_website(value)
        if args.browser:
            result = check_browser_speed(url)
            print_browser_result(url, result)
            return 0 if (result["status"] is not None and 200 <= result["status"] < 400
                         and not result["failed_requests"] and not result["http_errors"]) else 1
        result = check_speed(url)
        print(f"Requested URL: {url}")
        print(f"Final URL: {result['url']}")
        print(f"HTTP status: {result['status']} {result['reason']}")
        print(f"Time to response headers: {result['headers_ms']:.1f} ms")
        print(f"Body download time: {result['download_ms']:.1f} ms")
        print(f"Total fetch time: {result['total_ms']:.1f} ms")
        print(f"Downloaded: {result['bytes']:,} bytes")
        rate = result["kib_per_second"]
        print(f"Average body transfer rate: {rate:.1f} KiB/s" if rate is not None
              else "Average body transfer rate: unavailable")
        if not result["complete"]:
            print("Download limit reached (10 MiB plus one probe byte); timings cover a partial body.")
        print("Measures the main document only; excludes browser rendering and linked assets.")
        return 0 if 200 <= result["status"] < 400 and result["complete"] else 1
    except (ValueError, UnicodeError) as error:
        print(f"Invalid input: {error}")
    except (URLError, OSError, HTTPException) as error:
        print(f"Unable to measure website: {error}")
    except RuntimeError as error:
        print(error)
    except (EOFError, KeyboardInterrupt):
        print("\nCancelled.")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
