# `site_speed_check.py` cheat sheet

## Imports and constants

| Name | Purpose |
| --- | --- |
| `argparse` | Optional website argument and help |
| `time.perf_counter` | Monotonic elapsed-time measurement |
| `HTTPException` | Handles malformed or incomplete HTTP transfers |
| `HTTPError`, `URLError` | HTTP error responses and connection failures |
| `urlsplit`, `urlunsplit` | URL validation and normalization |
| `Request`, `urlopen` | GET request and standard redirect/TLS handling |
| `MAX_BYTES` | 10 MiB response-body cap, with one extra detection byte |

## Functions

| Function | Behavior |
| --- | --- |
| `parse_website(value)` | Trims input, defaults to HTTPS, validates scheme/host/credentials/port/whitespace, handles IDNA and IPv6, preserves path/query, removes fragment. |
| `check_speed(url, timeout=10, max_bytes=MAX_BYTES)` | Fetches a document, times headers and body reading, bounds downloads, returns measurements, closes the response. |
| `main()` | Reads input, prints timings/status/size/rate, labels partial results, handles failures, and selects an exit code. |
| Main guard | Runs the CLI only for direct execution and exposes its exit code. |

## Timing and reading

- `started` is captured immediately before opening the request.
- `headers_at` is captured when urlopen returns the final response or HTTPError.
- Each body chunk is at most 64 KiB; chunks are discarded after counting.
- Reading stops on EOF or after 10 MiB plus one byte. The extra byte distinguishes a body exactly equal to the cap from a larger body.
- `finished` is captured after reading. Header time plus body time equals total time.
- Rate is bytes / 1,024 / body seconds, with a guard for zero elapsed time.
- `HTTPError` is treated as a response so error pages have visible status and timing.
- A `with response` block closes the connection even if body reading raises.
- Exit 0 requires status 200-399 and a complete body. Other statuses, partial results, and handled failures use 1; CLI syntax errors use 2.

## Commands

```powershell
python site_speed_check.py
python site_speed_check.py https://example.com
python site_speed_check.py --help
```

Without `--browser`, the script uses only Python's standard library and needs no additional installation once Python is available. This default mode excludes rendering and linked resources and does not isolate exact time to first byte.

## Browser mode

`--browser` requires both the Playwright Python package and the Chromium browser download. Installing the package alone is insufficient. Use the same Python environment for installation and execution. Use `python -m playwright` to avoid a missing standalone `playwright` command on PATH. If a Playwright update reports a missing browser, rerun the Chromium installation command.

| Function or switch | Purpose |
| --- | --- |
| `--browser` | Selects Chromium instead of the document fetch. Works with a URL argument or interactive input. |
| `check_browser_speed(url)` | Imports Playwright only on demand; launches headless Chromium, creates a fresh context, observes request failures and HTTP errors, waits for load plus two seconds, and reads navigation/paint/resource entries. Closes the browser in a finally block. |
| `print_browser_result(url, result)` | Displays first-byte, DOMContentLoaded, load-event, first-contentful-paint, resource-count, error-count, and observation-window measurements. |

Browser timestamps use the page's performance clock and exclude browser startup. The fixed observation window avoids waiting for indefinite network idle. It does not imply all dynamic rendering is complete. Resource timing counts cover the main frame and use a 10,000-entry buffer. Browser mode does not use the document-mode download cap. Exit 0 requires a 200-399 main response and no observed HTTP errors or failed requests. RuntimeError carries dependency, launch, and navigation failures to the CLI.

```powershell
python -m pip install playwright
python -m playwright install chromium
python site_speed_check.py example.com --browser
```
