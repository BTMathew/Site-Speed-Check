# AI prompt guide: building `site_speed_check.py`

## 1. Create the project

```text
Create a Python 3.9+ project named Site-Speed-Check containing site_speed_check.py, README.md, CHEAT.md, PROMPT.md, and .gitignore. Use only the standard library and keep all work local until asked to publish.
```

## 2. Validate website input

```text
Implement parse_website(value) with urlsplit/urlunsplit. Accept hostnames and HTTP/HTTPS URLs; default bare hostnames to HTTPS. Trim input and reject blanks, raw whitespace/control characters, unsupported schemes, missing hostnames, embedded credentials, and ports outside 1-65535. Normalize international hostnames through IDNA, preserve IPv6 brackets, paths and queries, default empty paths to /, and remove fragments.
```

## 3. Measure a bounded document fetch

```text
Implement check_speed(url, timeout=10, max_bytes=10*1024*1024). Use Request/urlopen with User-Agent Site-Speed-Check/1.0 and Accept-Encoding identity, normal TLS verification, and default urllib redirects. Use perf_counter immediately before opening, after headers, and after body reading. Treat HTTPError as a usable response. Read body chunks up to 64 KiB without retaining them. Stop at EOF or max_bytes plus one probe byte. Return final URL, status, reason, headers/download/total milliseconds, bytes, completeness, and KiB/s (guard zero elapsed time). Close responses with a context manager. Propagate network and incomplete-transfer errors to the CLI.
```

## 4. Add a CLI

```text
Use argparse for an optional website argument or ask Website:. Print requested/final URLs, HTTP status/reason, time to response headers, body download time, total fetch time, bytes, and average KiB/s. Label capped downloads as partial. Explain that only the main document is measured. Return 0 only for a complete response with status 200-399, otherwise 1. Handle invalid inputs, URLError/OSError/HTTPException, EOF, and Ctrl+C. Preserve argparse help and syntax-error behavior. Use a guarded SystemExit(main()) entry point.
```

## 5. Verify and document

```text
Use a local HTTP server to verify complete responses, redirects, error pages, empty bodies, delayed bodies, and capped downloads. Test input parsing and CLI output/exit codes without requiring external network access. Document timing definitions, the 10 MiB plus one byte cap, per-socket timeout rather than a total deadline, proxies, normal HTTPS verification, encoding caveats, and that the results exclude browser rendering/linked assets and are not Core Web Vitals. Add a code cheat sheet and recreation prompts. Ignore caches and virtual environments.
```

## Single all-in-one prompt

```text
Build a standard-library Python website speed checker in Site-Speed-Check/site_speed_check.py with interactive or argument input. Normalize hostnames/HTTP/HTTPS URLs, defaulting to HTTPS, with credential/scheme/port/whitespace validation and IDNA support. Send GET using urllib with verified HTTPS, default redirects, User-Agent Site-Speed-Check/1.0, identity encoding, and a 10-second socket timeout. Measure time to response headers, body download time, total fetch time, downloaded bytes, and average KiB/s using perf_counter. Read/discard chunks and stop at 10 MiB plus one probe byte; label larger bodies partial. Show HTTP error statuses as measured responses. Exit 0 only for complete 200-399 responses and 1 for partial/error/handled failures. Add README.md, CHEAT.md, PROMPT.md, and .gitignore in the same style as the HTTP Test project. Verify locally with a test HTTP server and keep the project local until publishing is requested.
```

## Optional browser mode extension

Documentation must distinguish the two setup paths: without `--browser`, Python alone is sufficient and no additional installation is needed. With `--browser`, users must install both the Playwright Python package and its Chromium browser, in the same Python environment:

```powershell
python -m pip install playwright
python -m playwright install chromium
python -m site_speed_check example.com --browser
```

Explain that installing the package alone does not download Chromium. Use module commands so the instructions work even when `playwright` is not on PATH. If an update produces a missing-browser error, rerun the Chromium installation command.

```text
Extend site_speed_check.py with --browser, retaining the default document mode. Import Playwright lazily so default mode has no dependency. Use headless Chromium in a fresh context with a 1365x768 viewport and normal TLS verification. Navigate with wait_until=load and a 30-second timeout, then observe two additional seconds. Collect PerformanceNavigationTiming responseStart, domContentLoadedEventEnd, loadEventEnd, first-contentful-paint if reported, performance.now, and main-frame resource timing entry count with a 10,000-entry buffer. Count failed requests and HTTP responses >=400. Display the final URL and main status alongside metrics and error counts. Close Chromium in finally. Handle missing packages/browser and navigation errors clearly. Exit 0 only for a 200-399 main response and no observed request/HTTP failures. Explain that timestamps exclude startup, post-load observation is bounded, lazy loading and later activity may be excluded, no scrolling occurs, and this is not a full rendering completion or Core Web Vitals test. Document python -m pip install playwright and python -m playwright install chromium. Verify using a local page with linked CSS, JavaScript, images, and error assets. Keep work local.
```
