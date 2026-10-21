# Site Speed Check

`site_speed_check.py` measures how quickly a website returns response headers and downloads its main document. Add `--browser` to include Chromium page loading, linked assets, and paint timing. Default mode uses only Python's standard library.

## What the script does

1. Accepts a hostname or HTTP/HTTPS URL, defaulting bare hostnames to HTTPS.
2. Sends a GET request and follows Python urllib's supported redirects.
3. Measures elapsed time to headers, body download time, and total fetch time.
4. Reports downloaded bytes, average body transfer rate, HTTP status, and final URL.
5. Stops body reading at 10 MiB plus one probe byte and labels larger downloads as partial.

## Requirements

- Python 3.9 or later
- Network access to the website
- A working Python certificate trust store for HTTPS

### Without `--browser`: no additional installation

Once Python is installed, default mode is ready to run. It uses only Python's standard library: no Playwright package or browser installation is needed.

```powershell
python -m site_speed_check example.com
```

### With `--browser`: install Playwright and Chromium

Browser mode requires **two separate installation steps**. Run both commands using the same Python environment you use for the script:

```powershell
# 1. Install the Playwright Python package.
python -m pip install playwright

# 2. Download the Chromium browser used by Playwright.
python -m playwright install chromium
```

Installing the Python package alone does not install Chromium. Having Chrome or Edge already installed does not replace this step for this script. Both downloads require internet access. After updating Playwright, rerun the Chromium installation command if it reports a missing browser executable.

Then run with browser measurements enabled:

```powershell
python -m site_speed_check example.com --browser
```

To enter the website interactively, omit `example.com`. Both `python -m site_speed_check` and `python site_speed_check.py` work when run from this project folder.

## Run

Open a terminal in this folder:

```powershell
python site_speed_check.py
```

Enter a website at `Website:` or run:

```powershell
python site_speed_check.py example.com
python site_speed_check.py http://example.com
python site_speed_check.py "https://example.com/path?name=value"
python site_speed_check.py --help
```

Use `python3` if that is your installed Python command, or use your executable's full path. Custom ports and international domain names are supported. Embedded credentials, other schemes, and raw spaces/control characters are rejected. Fragments are removed. Percent-encode spaces and non-ASCII path/query characters.

## Output

The following output describes default document mode.

Illustrative values, not a live result:

```text
Requested URL: https://example.com/
Final URL: https://example.com/
HTTP status: 200 OK
Time to response headers: 150.0 ms
Body download time: 50.0 ms
Total fetch time: 200.0 ms
Downloaded: 10,240 bytes
Average body transfer rate: 200.0 KiB/s
Measures the main document only; excludes browser rendering and linked assets.
```

| Measurement | Meaning |
| --- | --- |
| Time to response headers | Time until the final response headers arrive, including DNS, connection setup, TLS when applicable, redirects, and server response |
| Body download time | Time spent reading the final response body after headers |
| Total fetch time | Headers time plus body download time |
| Downloaded | Body bytes returned by urllib, excluding headers and earlier redirect bodies |
| Average body transfer rate | Downloaded KiB divided by body reading seconds; 1 KiB = 1,024 bytes |

The header measurement is not an isolated DNS, TLS, server-processing, or exact first-byte measurement. Body reading may include data already buffered by the HTTP client. Small documents can produce noisy transfer-rate estimates.

## Limits and behavior

- Default mode is a single main-document fetch. It does not load images, CSS, JavaScript, or render the page. Browser mode is described below.
- Socket operations use a 10-second timeout. DNS, redirects, and a slowly streaming response can make total runtime longer; there is no fixed total deadline.
- The body is read in chunks without retaining it. A 10 MiB limit plus one probe byte prevents unlimited downloads. If exceeded, the script labels the measurements partial and exits with 1. Timings are not a full download result in that case.
- Requests ask for identity encoding. A server may choose a different encoding; byte counts reflect the body delivered by urllib, not guaranteed uncompressed page size.
- HTTPS verification stays enabled. System proxy settings may apply. Redirects can lead from HTTPS to HTTP.
- HTTP errors such as 404 are measured and displayed as error-page responses. A successful response does not establish that the site functions correctly.
- Network conditions, geography, caching, server load, and proxies affect results. There is no universal fast/slow score here.
- No output files, monitoring, or scheduled requests are created.

Exit code 0 means a complete response with status 200-399. Exit code 1 means another status, a partial download, handled input/network errors, or cancellation. Argparse uses 2 for invalid command-line syntax.

## Common issues

- **Python not found**: install Python with PATH enabled or use an existing executable's full path.
- **Playwright package missing**: browser mode requires `python -m pip install playwright`, followed by `python -m playwright install chromium`. Default mode needs neither.
- **Browser executable does not exist**: the package is installed, but its matching Chromium browser is missing. Run `python -m playwright install chromium` with the same Python environment.
- **`playwright` is not recognized**: use `python -m playwright install chromium` rather than the standalone `playwright install` command. This invokes the installed Python module without requiring its command launcher on PATH.
- **Certificate verification failed**: check the site's certificate, computer clock, and Python trust store.
- **Unable to measure website**: check the hostname, network access, firewall, and HTTPS/HTTP port. Broken or incomplete transfers may also cause this error.
- **403 or 429**: the server may block automated clients or limit requests. The reported timings then describe that error response.

## Project files

```text
Site-Speed-Check/
|-- site_speed_check.py
|-- README.md
|-- CHEAT.md
|-- PROMPT.md
`-- .gitignore
```

[CHEAT.md](CHEAT.md) explains the code. [PROMPT.md](PROMPT.md) contains recreation prompts.

## Browser mode: rendering and linked assets

This mode requires both the Playwright Python package and its Chromium browser. Complete both setup steps above, using the same Python executable you use to run the script:

```powershell
python -m pip install playwright
python -m playwright install chromium
```

Then run:

```powershell
python site_speed_check.py example.com --browser
python site_speed_check.py --browser
```

The second command asks for the website. Chromium runs headlessly in a fresh browser context with a 1365 by 768 viewport and normal HTTPS verification. It loads scripts, styles, images, and other resources requested by the page. Navigation waits up to 30 seconds for the load event, then observes two more seconds so paint measurements and some post-load activity can be recorded. Browser startup time is excluded from the browser's navigation timestamps. The document-mode size limit does not apply to browser mode.

| Browser measurement | Meaning |
| --- | --- |
| Time to first response byte | Navigation `responseStart`, measured from the current document's navigation start |
| DOM content loaded | End of the DOMContentLoaded event |
| Page load event | End of the load event, including resources that delay that event |
| First contentful paint | First text/image/content paint reported by Chromium; unavailable is shown when absent |
| Completed resource timing entries | Main-frame resource entries available at collection, excluding the navigation entry; capped by a 10,000-entry buffer |
| Failed network requests | Observed request failures, such as DNS or connection errors |
| HTTP error responses | Observed status codes 400 or above, including the main page and assets |
| Observation window | Browser time elapsed from navigation start to collection |

There is no universal moment when all rendering is finished. These are specific load and paint milestones, not a full Core Web Vitals audit. The script does not scroll or interact: lazy-loaded content, ongoing animations, late fetches, and activity after the observation window may be excluded. Resource counts do not include every resource loaded within subframes. HTTP failures or missing assets may affect the rendering measurements; they are reported separately.

Browser mode exits with 0 when the main response is 200-399 and no observed request failures or HTTP errors occur; otherwise it exits with 1. Missing Playwright/Chromium and navigation failures produce an actionable error message. No results are uploaded or saved.

Implementation references: [Playwright Page API](https://playwright.dev/python/docs/api/class-page) and [MDN navigation timing](https://developer.mozilla.org/en-US/docs/Web/API/PerformanceNavigationTiming).
