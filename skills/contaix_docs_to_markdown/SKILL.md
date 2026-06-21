---
name: contaix_docs_to_markdown
description: Convert a documentation website into a single, clean markdown file. Use when the user provides a documentation URL and wants it as markdown, or says "get me the docs", "download documentation", "make a markdown of this site", "aggregate these docs", or gives a URL to a docs site. Also use for converting API reference sites, developer guides, product documentation, or knowledge bases.
argument-hint: <URL of documentation site>
---

# Docs-to-Markdown

Convert any documentation website into a single aggregated markdown file, suitable
for AI consumption, offline reading, or PDF generation.

## Step 0: Determine the URL

If the user gave a URL, use it. If they named a product/service, search for its
documentation URL. If the URL points to a specific page within docs (not the root),
that's fine — the tool will discover the full navigation from any page.

## Step 1: Try the automated pipeline first

```python
from contaix.web import site_to_markdown

result = site_to_markdown(
    '<URL>',
    cache_dir='/tmp/contaix_cache/<site_name>',
    output_file='~/Downloads/<site_name>_docs.md',
    verbose=True,
)
```

`site_to_markdown` now does this in two phases:

1. **Fast path** — probes the site for a publisher-provided single-doc bundle
   at `/llms-full.txt` (Mintlify, Docusaurus, Fern, and many other generators
   ship one). When found, returns it directly. **This is the best case** —
   one HTTP request, clean markdown, no scraping needed.
2. **Scrape path** — if no bundle exists, it falls back to discovering the
   site's navigation, fetching every page (with caching), and aggregating.

You can also call the fast-path helpers directly:

```python
from contaix.web import find_llms_full_url, fetch_llms_full

bundle_url = find_llms_full_url('<URL>')   # str or None
md = fetch_llms_full('<URL>')              # str or None
```

To force the scrape path (e.g. you want only one tab), pass `use_llms_full=False`
or use a `tab_filter`.

**If this works and the user is happy → done.**

## Step 2: If the result needs improvement, diagnose

Run these checks on the output:

```python
content = open(result).read()
import re

# Quick quality check
print(f"Size: {len(content):,} chars")
print(f"Sections: {len(re.findall(r'^# .+', content, re.MULTILINE))}")
print(f"Links: {len(re.findall(r'\\[.+?\\]\\(.+?\\)', content))}")
print(f"Code blocks: {content.count(chr(96)*3) // 2}")

# Artifact check
for pattern, name in [
    (r'\$L[0-9a-f]+', 'unresolved $L refs'),
    ('Loading...', 'Loading placeholders'),
    ('False', 'False artifacts'),
]:
    count = len(re.findall(pattern, content))
    if count > 0:
        print(f"WARNING: {count} {name}")
```

### Common issues and fixes

**Broken links or formatting artifacts** → Run `repair_markdown` on the output.
This is already called automatically inside `site_to_markdown`, but you can
also use it standalone on any markdown from any source:
```python
from contaix.web import repair_markdown

content = open(result).read()
fixed = repair_markdown(content)
# Compare
if fixed != content:
    open(result, 'w').write(fixed)
    print("Repaired markdown artifacts")
```

`repair_markdown` fixes:
- Multi-line links (`[text\nmore text](url)` → `[text](url) — more text`)
- Empty links (`[](url)` → removed)

If you see other markdown issues not covered by `repair_markdown`, add a
new fixer to `contaix.web._fix_*` and wire it into `repair_markdown`.

**Empty content / "Loading..."** → Site uses client-side rendering that
`site_to_markdown` can't handle. Use `contaix_web_aggregate` skill with
WebFetch instead.

**Missing pages** → Check if the site has tabs/sections. Use `tab_filter`:
```python
from contaix.web import list_site_pages
pages = list_site_pages('<URL>')
# See what tabs/groups exist
tabs = set(p['tab'] for p in pages)
groups = set(p['group'] for p in pages)
print(f"Tabs: {tabs}")
print(f"Groups: {groups}")
```

**Navigation not detected** → The site doesn't use Next.js or standard nav
elements. Use `contaix_web_aggregate` skill to manually curate page list.

**Missing code examples** → RSC extraction may miss lazy-loaded code blocks.
For critical pages, supplement with WebFetch:
```
WebFetch the specific page and extract the code examples, then patch them
into the markdown file.
```

## Step 3: Filter pages if needed

```python
# Only include certain tabs
result = site_to_markdown(url, tab_filter='Developer Guide', ...)

# Custom filter function
result = site_to_markdown(url, tab_filter=lambda t: 'API' not in t, ...)
```

## Step 4: For non-standard sites, fall back to manual approach

If `site_to_markdown` doesn't work, use these building blocks:

```python
from contaix.web import (
    extract_site_nav,     # Get navigation structure
    fetch_page,           # Fetch with caching
    fetch_nextjs_rsc,     # Fetch from Next.js RSC endpoint
    html_to_clean_markdown,  # Convert HTML to markdown
    extract_rsc_page_content,  # Extract from RSC flight data
)
```

Or switch to the `contaix_web_aggregate` skill for full manual control.

## API Quick Reference

| Function | Purpose |
|----------|---------|
| `site_to_markdown(url, **kw)` | Full pipeline: llms-full fast path → nav → fetch → convert → aggregate |
| `find_llms_full_url(url)` | Probe for a publisher's `/llms-full.txt` bundle (returns URL or None) |
| `fetch_llms_full(url)` | Fetch the bundle directly (returns markdown or None) |
| `repair_markdown(md)` | Fix broken links, empty links, and other markdown artifacts |
| `extract_site_nav(url)` | Get `{base_url, tabs, pages}` navigation structure |
| `list_site_pages(url)` | Flat list of `{path, title, url, group, tab}` dicts |
| `fetch_page(url, cache_dir=...)` | Fetch HTML with disk caching |
| `fetch_nextjs_rsc(url, cache_dir=...)` | Fetch via Next.js RSC flight endpoint |
| `html_to_clean_markdown(html)` | Convert HTML to markdown via html2text |
| `extract_rsc_page_content(rsc)` | Extract markdown from RSC flight data |
| `is_nextjs_site(html)` | Detect Next.js App Router sites |

## Key `site_to_markdown` parameters

| Parameter | Default | Description |
|-----------|---------|-------------|
| `cache_dir` | `~/.cache/contaix/web` | Cache directory for fetched pages |
| `output_file` | `None` | Save path (returns string if None) |
| `tab_filter` | `None` | Filter by tab label (str or callable). Skips the llms-full fast path. |
| `page_fetcher` | auto | Custom `(url) -> content` function. Skips the llms-full fast path. |
| `content_extractor` | auto | Custom `(content) -> markdown` function |
| `collapse_blank_lines` | `True` | Collapse triple+ newlines to double |
| `use_llms_full` | `True` | Probe for a `/llms-full.txt` publisher bundle first |
| `verbose` | `False` | Print progress |
