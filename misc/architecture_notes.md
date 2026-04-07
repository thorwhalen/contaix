# contaix Architecture Notes

## Module Overview

### contaix/web.py (NEW - April 2026)

Website-to-markdown pipeline. Key design decisions:

**Navigation extraction**: Parses Next.js RSC inline payloads to get the full
navigation structure (tabs, groups, ordered pages). Falls back to HTML link
extraction for non-Next.js sites. This is critical because:
- Documentation sites have a logical reading order
- The navigation structure defines what "belongs" to the documentation
- Without it, we'd follow every link including external references

**RSC flight endpoint**: Next.js App Router sites serve React Server Component
payloads via `RSC: 1` header. This returns structured content without requiring
JavaScript rendering. The approach:
1. Fetch page with `RSC: 1` header -> get `text/x-component` response
2. Parse RSC flight format (line-oriented: `key:json_payload`)
3. Build a registry mapping keys to parsed data
4. Resolve `$L` references between RSC nodes
5. Convert the React tree to markdown recursively

**Limitations of RSC approach**:
- Code examples are often in lazy-loaded components not present in the RSC stream
- T-chunks (text chunks, prefix `T`) contain HTML code blocks but may not be
  linked to the right `$L` reference
- Works only for Next.js App Router sites (a large portion of modern doc sites)

**Key bugs fixed (April 2026)**:
- `bool` subclasses `int` in Python, so `False` was rendered as `"False"` by the
  `isinstance(node, (int, float))` check. Fix: check `isinstance(node, bool)` first.
- `$L` components with `id` prop (model ID displays) rendered as empty. Fix: use
  `id` as display text when no children present.
- `$L` components with `href` prop (links) were passed through as children.
  Fix: detect `href` and render as `[text](url)`.
- Mojibake from UTF-8 multi-byte chars decoded as latin-1. Fix: replacement map
  in `_clean_rsc_markdown`.

**Caching**: Disk-based caching via `cache_dir` parameter. Each page is cached
by its URL-derived key. This is essential for iteration:
- First pass: fetch all pages (slow, network-bound)
- Subsequent passes: read from cache (fast, CPU-only)
- Uses URL-to-filename conversion (slashes -> double underscores)

### contaix/urls.py

URL extraction and article downloading. Notable patterns:
- `extract_urls` has methods attached as attributes (`.markdown_links()`,
  `.only_urls()`, etc.)
- Clipboard integration via pyperclip decorator
- URL verification with custom user-agent headers

### contaix/code.py

Code aggregation from directories, packages, and GitHub repos.
- `resolve_code_source()` handles path/URL/package name resolution
- Uses `dol.TextFiles` for file access
- `dol.store_aggregate` for combining files
- Supports GitHub via `hubcap.ensure_repo_folder()`

### contaix/aggregation.py

Generic store aggregation with deduplication (via `hg` package) and
chunking (via `lkj.chunk_iterable`).

### contaix/markdown.py

Thin wrapper around `dn.src` for file format conversion.

## Dependency Architecture

```
contaix
  ├── scraped (web scraping via Scrapy)
  │     ├── scrapy
  │     ├── html2text
  │     └── graze (URL/path utilities)
  ├── dol (storage abstractions)
  ├── dn (document conversion)
  │     ├── pypdf
  │     ├── mammoth
  │     └── pandas
  ├── hubcap (GitHub API)
  │     └── PyGithub
  └── lkj (utilities)
```

## Improvement Opportunities

### web.py
- **Code block extraction**: Resolve CodeGroup components by matching
  T-chunk keys to `$L` references via position heuristics
- **Parallel fetching**: Use asyncio or ThreadPoolExecutor for page fetching
- **Playwright fallback**: Add optional playwright-based fetcher for
  non-Next.js JS-rendered sites
- **Sitemap.xml support**: Parse standard sitemaps as another nav source
- **robots.txt respect**: Check robots.txt before crawling
- **Rate limiting**: Add configurable delays between requests

### scraped
- **Caching layer**: The existing `download_site()` always re-downloads.
  Could use `dol` store abstraction for transparent caching.
- **Content extraction**: Currently converts all HTML to markdown.
  Could benefit from content-area detection (article/main selectors).

### General
- **CLI interface**: contaix has no CLI. Could use argh or click.
- **Progress reporting**: Use callbacks or yield-based progress for long operations.
- **Error recovery**: Continue on individual page failures, report at end.
