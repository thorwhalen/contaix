# contaix.web

Web content extraction and aggregation tools.

Functions for extracting structured content from websites and converting to markdown,
with support for navigation discovery, caching, and content aggregation.

Main entry points:

> site_to_markdown(url)  # Full pipeline: discover nav, fetch pages, aggregate
> extract_site_nav(url)  # Get ordered navigation structure from a doc site
> fetch_page(url)        # Fetch a single page’s HTML with optional caching

Example:

```default
>>> md = site_to_markdown(
...     'https://platform.claude.com/docs/en/home',
...     cache_dir='/tmp/claude_docs_cache',
...     output_file='~/Downloads/claude_docs.md',
... )
```

### Functions

| [`extract_rsc_page_content`](#contaix.web.extract_rsc_page_content)(rsc_text)                 | Extract page content from RSC flight data.                              |
|-----------------------------------------------------------------------------------------------------|-------------------------------------------------------------------------|
| [`extract_site_nav`](#contaix.web.extract_site_nav)(url, \*[, html])                  | Extract navigation structure from a documentation site.                 |
| [`fetch_llms_full`](#contaix.web.fetch_llms_full)(url, \*[, timeout])                | Fetch a publisher-provided single-doc bundle if available.              |
| [`fetch_nextjs_rsc`](#contaix.web.fetch_nextjs_rsc)(url, \*[, cache_dir, force, ...]) | Fetch page content via Next.js RSC flight endpoint.                     |
| [`fetch_page`](#contaix.web.fetch_page)(url, \*[, cache_dir, force, timeout])   | Fetch a page's HTML content, with optional disk caching.                |
| [`fetch_pages`](#contaix.web.fetch_pages)(urls, \*[, cache_dir, force, verbose]) | Fetch multiple pages with caching.                                      |
| [`find_llms_full_url`](#contaix.web.find_llms_full_url)(url, \*[, timeout])             | Probe for a publisher-provided single-doc bundle.                       |
| [`html_to_clean_markdown`](#contaix.web.html_to_clean_markdown)(html, \*[, ...])            | Convert HTML to clean markdown using html2text.                         |
| [`is_nextjs_site`](#contaix.web.is_nextjs_site)(html)                               | Detect if a page is served by Next.js (App Router).                     |
| [`list_site_pages`](#contaix.web.list_site_pages)(url)                               | List all pages found in a documentation site's navigation.              |
| [`parse_rsc_flight`](#contaix.web.parse_rsc_flight)(rsc_text)                         | Parse RSC flight data into a dict mapping keys to parsed JSON data.     |
| [`rsc_tree_to_markdown`](#contaix.web.rsc_tree_to_markdown)(node, \*[, \_registry, ...])  | Recursively extract markdown from a React Server Component tree node.   |
| [`site_to_markdown`](#contaix.web.site_to_markdown)(url, \*[, cache_dir, ...])        | Download a documentation site and produce a single aggregated markdown. |
| [`url_to_cache_key`](#contaix.web.url_to_cache_key)(url)                              | Convert a URL to a filesystem-safe cache key.                           |

### contaix.web.extract_rsc_page_content(rsc_text)

Extract page content from RSC flight data.

Works on both:

- RSC flight endpoint responses (`text/x-component`)
- Inline RSC payloads extracted from HTML

Returns markdown text if content was found, None otherwise.

* **Return type:**
  [`str`](https://docs.python.org/3/builtins/stdtypes.html#str) | [`None`](https://docs.python.org/3/builtins/constants.html#None)

### contaix.web.extract_site_nav(url, , html=None)

Extract navigation structure from a documentation site.

Returns a dict with keys:

> - `base_url`: The base URL of the site
> - `tabs`: List of tab dicts, each with `label` and `groups`
> - `pages`: Flat ordered list of `{path, title}` dicts (all tabs)

Tries, in order:

> 1. Next.js RSC payload (embedded in SSR HTML)
> 2. HTML `<a>` link extraction with path-based grouping
* **Parameters:**
  * **url** ([`str`](https://docs.python.org/3/builtins/stdtypes.html#str)) – The documentation site URL (e.g. a homepage or any page on the site).
  * **html** ([`str`](https://docs.python.org/3/builtins/stdtypes.html#str)) – Pre-fetched HTML. If None, fetches from `url`.
* **Return type:**
  [`dict`](https://docs.python.org/3/builtins/stdtypes.html#dict)

### contaix.web.fetch_llms_full(url, , timeout=30)

Fetch a publisher-provided single-doc bundle if available.

See [`find_llms_full_url()`](#contaix.web.find_llms_full_url) for how the URL is discovered.

Returns the markdown text, or `None` if no bundle was found.

* **Return type:**
  [`str`](https://docs.python.org/3/builtins/stdtypes.html#str) | [`None`](https://docs.python.org/3/builtins/constants.html#None)

### contaix.web.fetch_nextjs_rsc(url, , cache_dir=None, force=False, timeout=30)

Fetch page content via Next.js RSC flight endpoint.

Next.js App Router sites serve React Server Component payloads when the
`RSC: 1` header is present. These contain the full page content that
would otherwise require JavaScript rendering.

* **Parameters:**
  * **url** ([`str`](https://docs.python.org/3/builtins/stdtypes.html#str)) – The page URL.
  * **cache_dir** ([`str`](https://docs.python.org/3/builtins/stdtypes.html#str)) – Directory to cache RSC responses.
  * **force** ([`bool`](https://docs.python.org/3/builtins/functions.html#bool)) – Re-fetch even if cached.
  * **timeout** ([`int`](https://docs.python.org/3/builtins/functions.html#int)) – Request timeout.
* **Returns:**
  The RSC flight data as text.
* **Return type:**
  [`str`](https://docs.python.org/3/builtins/stdtypes.html#str)

### contaix.web.fetch_page(url, , cache_dir=None, force=False, timeout=30)

Fetch a page’s HTML content, with optional disk caching.

* **Parameters:**
  * **url** ([`str`](https://docs.python.org/3/builtins/stdtypes.html#str)) – The URL to fetch.
  * **cache_dir** ([`str`](https://docs.python.org/3/builtins/stdtypes.html#str)) – Directory to cache HTML files. If None, no caching.
  * **force** ([`bool`](https://docs.python.org/3/builtins/functions.html#bool)) – If True, re-fetch even if cached.
  * **timeout** ([`int`](https://docs.python.org/3/builtins/functions.html#int)) – Request timeout in seconds.
* **Returns:**
  The page’s HTML content.
* **Return type:**
  [`str`](https://docs.python.org/3/builtins/stdtypes.html#str)

### contaix.web.fetch_pages(urls, , cache_dir=None, force=False, verbose=False)

Fetch multiple pages with caching.

Returns a dict mapping URL -> HTML content.
Pages that fail to fetch are skipped with a warning.

* **Return type:**
  [`dict`](https://docs.python.org/3/builtins/stdtypes.html#dict)[[`str`](https://docs.python.org/3/builtins/stdtypes.html#str), [`str`](https://docs.python.org/3/builtins/stdtypes.html#str)]

### contaix.web.find_llms_full_url(url, , timeout=30)

Probe for a publisher-provided single-doc bundle.

Many documentation generators (Mintlify, Docusaurus, Fern, etc.) expose
the entire docs as a single markdown file at `/llms-full.txt` (or
`/llms.txt` for an index). When present, this is far better than
scraping page-by-page.

Tries, in order:

1. Same path as the input URL with the doc-root replaced (e.g.
   `https://site.com/docs/foo` -> `https://site.com/docs/llms-full.txt`).
2. Site root (e.g. `https://site.com/llms-full.txt`).

* **Parameters:**
  * **url** ([`str`](https://docs.python.org/3/builtins/stdtypes.html#str)) – Any URL on the documentation site.
  * **timeout** ([`int`](https://docs.python.org/3/builtins/functions.html#int)) – HEAD request timeout.
* **Returns:**
  The first URL that returns HTTP 200 with non-trivial content, or
  `None` if none of the candidates exist.
* **Return type:**
  [`str`](https://docs.python.org/3/builtins/stdtypes.html#str) | [`None`](https://docs.python.org/3/builtins/constants.html#None)

### contaix.web.html_to_clean_markdown(html, , body_width=0, ignore_images=True, include_links=True, \*\*html2text_options)

Convert HTML to clean markdown using html2text.

* **Parameters:**
  * **html** ([`str`](https://docs.python.org/3/builtins/stdtypes.html#str)) – Raw HTML content.
  * **body_width** ([`int`](https://docs.python.org/3/builtins/functions.html#int)) – Line width for wrapping. 0 = no wrapping.
  * **ignore_images** ([`bool`](https://docs.python.org/3/builtins/functions.html#bool)) – Whether to skip image tags.
  * **include_links** ([`bool`](https://docs.python.org/3/builtins/functions.html#bool)) – Whether to include hyperlinks in output.
* **Return type:**
  [`str`](https://docs.python.org/3/builtins/stdtypes.html#str)

### contaix.web.is_nextjs_site(html)

Detect if a page is served by Next.js (App Router).

Looks for `self.__next_f.push` in the HTML, which is the RSC
streaming payload signature.

* **Return type:**
  [`bool`](https://docs.python.org/3/builtins/functions.html#bool)

### contaix.web.list_site_pages(url)

List all pages found in a documentation site’s navigation.

Returns a list of dicts with keys: path, title, url, group, tab.

* **Return type:**
  [`list`](https://docs.python.org/3/builtins/stdtypes.html#list)[[`dict`](https://docs.python.org/3/builtins/stdtypes.html#dict)]

```pycon
>>> pages = list_site_pages('https://platform.claude.com/docs/en/home')
>>> len(pages)
89
```

### contaix.web.parse_rsc_flight(rsc_text)

Parse RSC flight data into a dict mapping keys to parsed JSON data.

Each RSC record starts with `<hex_key>:<payload>`. Records come in three
flavors:

- `I[...]`: module import descriptors (skipped here).
- `T<hex_size>,<bytes>`: a raw text chunk whose payload occupies exactly
  `hex_size` bytes (often markdown, code, or compiled MDX). The payload
  may contain newlines, so we read by byte count rather than splitting on
  `\n`.
- Anything else: a JSON value terminated by the next record header
  (`\n<hex>:`) or end-of-text.

* **Parameters:**
  **rsc_text** ([`str`](https://docs.python.org/3/builtins/stdtypes.html#str)) – Raw RSC flight response text (`text/x-component`).
* **Returns:**
  Mapping of hex keys to their parsed payloads.
* **Return type:**
  [`dict`](https://docs.python.org/3/builtins/stdtypes.html#dict)

### contaix.web.rsc_tree_to_markdown(node, , \_registry=None, \_depth=0)

Recursively extract markdown from a React Server Component tree node.

The RSC tree uses the format:

```default
["$", "tagName", key, {"children": ..., "className": ...}]
```

or plain strings for text nodes. Component references like `"$L2a"`
are resolved via `_registry` (from [`parse_rsc_flight()`](#contaix.web.parse_rsc_flight)).

* **Return type:**
  [`str`](https://docs.python.org/3/builtins/stdtypes.html#str)

### contaix.web.site_to_markdown(url, , cache_dir=None, output_file=None, tab_filter=None, page_fetcher=None, content_extractor=None, section_separator='\\\\n\\\\n---\\\\n\\\\n', collapse_blank_lines=True, use_llms_full=True, verbose=False)

Download a documentation site and produce a single aggregated markdown.

* **Parameters:**
  * **url** ([`str`](https://docs.python.org/3/builtins/stdtypes.html#str)) – The documentation site’s root URL.
  * **cache_dir** ([`str`](https://docs.python.org/3/builtins/stdtypes.html#str)) – Directory for caching fetched HTML. Defaults to `~/.cache/contaix/web`.
  * **output_file** ([`str`](https://docs.python.org/3/builtins/stdtypes.html#str)) – Path to save the markdown file. If None, returns the string.
  * **tab_filter** ([`str`](https://docs.python.org/3/builtins/stdtypes.html#str) | [`Callable`](https://docs.python.org/3/library/collections.abc.html#collections.abc.Callable)) – If a string, only include pages from tabs whose label contains this
    string (case-insensitive). If a callable, `tab_filter(tab_label) -> bool`.
  * **page_fetcher** ([`Callable`](https://docs.python.org/3/library/collections.abc.html#collections.abc.Callable)) – Custom `(url) -> html` function. Defaults to `fetch_page`.
  * **content_extractor** ([`Callable`](https://docs.python.org/3/library/collections.abc.html#collections.abc.Callable)) – Custom `(html) -> markdown` function. Defaults to auto-detection.
  * **section_separator** ([`str`](https://docs.python.org/3/builtins/stdtypes.html#str)) – Separator between page sections in the output.
  * **use_llms_full** ([`bool`](https://docs.python.org/3/builtins/functions.html#bool)) – If True (default), first try to find a publisher-provided
    `/llms-full.txt` bundle (Mintlify, Docusaurus, etc. ship these).
    When found, returns it directly instead of scraping page-by-page.
    Disable to force the scraping pipeline. Skipped automatically when
    `page_fetcher` or `tab_filter` is set, since those imply the
    caller wants the scraping path.
  * **verbose** ([`bool`](https://docs.python.org/3/builtins/functions.html#bool)) – Print progress information.
* **Returns:**
  If `output_file` is None, returns the markdown string.
  Otherwise, returns the output file path.
* **Return type:**
  [`str`](https://docs.python.org/3/builtins/stdtypes.html#str)

### contaix.web.url_to_cache_key(url)

Convert a URL to a filesystem-safe cache key.

* **Return type:**
  [`str`](https://docs.python.org/3/builtins/stdtypes.html#str)

```pycon
>>> url_to_cache_key('https://example.com/docs/en/foo')
'example.com__docs__en__foo.html'
```
