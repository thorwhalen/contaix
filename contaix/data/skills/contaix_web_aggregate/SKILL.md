---
name: contaix_web_aggregate
description: Aggregate web content from multiple pages into structured markdown. Use when the user wants to aggregate a non-documentation website (company info, product pages), when contaix_docs_to_markdown doesn't work for a specific site, when the user wants manual control over which pages to include, or when dealing with JavaScript-rendered sites that need WebFetch.
argument-hint: <URL or description of site to aggregate>
---

# Web Content Aggregation

Aggregate content from arbitrary websites into structured markdown.
Use this when `contaix_docs_to_markdown` doesn't handle the site,
or when you need fine-grained control.

## Step 0: Understand what the user wants

Ask if unclear:
- **Which pages?** All pages under a URL? A curated list? Just the landing page?
- **What content?** Full page content? Just text? Include code/tables?
- **What format?** Single markdown file? Separate files per page?

## Step 1: Analyze the site structure

Fetch the landing page and study it:

```python
from contaix.web import fetch_page, html_to_clean_markdown

html = fetch_page('<URL>', cache_dir='/tmp/contaix_cache')
```

Then use WebFetch to understand the page visually:
```
WebFetch <URL> with prompt: "List all navigation links and main content
sections on this page. What kind of site is this?"
```

### Decision: Is this a documentation site?

If yes → try `contaix_docs_to_markdown` skill first.
If no → continue with manual aggregation below.

### Decision: Is content JavaScript-rendered?

Check by looking at the fetched HTML:
```python
from contaix.web import is_nextjs_site
if is_nextjs_site(html):
    print("Next.js site — use RSC endpoint or site_to_markdown")
elif 'Loading' in html and len(html) > 100000:
    print("Likely JS-rendered — use WebFetch for each page")
else:
    print("Server-rendered — html_to_clean_markdown works")
```

## Step 2: Build the page list

### Option A: Extract from navigation
```python
from contaix.web import extract_site_nav
nav = extract_site_nav('<URL>')
pages = nav['pages']  # [{path, title, url, group, tab}, ...]
```

### Option B: Manual curation
Study the site and build the list:
```python
pages = [
    {'title': 'Overview', 'url': 'https://example.com'},
    {'title': 'Features', 'url': 'https://example.com/features'},
    {'title': 'Pricing', 'url': 'https://example.com/pricing'},
]
```

### Option C: Sitemap
```python
import requests
from xml.etree import ElementTree

r = requests.get('https://example.com/sitemap.xml', timeout=15)
if r.status_code == 200:
    root = ElementTree.fromstring(r.content)
    ns = {'ns': 'http://www.sitemaps.org/schemas/sitemap/0.9'}
    urls = [loc.text for loc in root.findall('.//ns:loc', ns)]
```

## Step 3: Fetch and convert each page

### For server-rendered sites
```python
from contaix.web import fetch_page, html_to_clean_markdown

sections = []
for page in pages:
    html = fetch_page(page['url'], cache_dir='/tmp/contaix_cache')
    md = html_to_clean_markdown(html)
    sections.append(f"# {page['title']}\n\n{md}")
```

### For JS-rendered sites (use WebFetch)
For each page, call WebFetch with an extraction prompt:
```
WebFetch <page_url> with prompt:
"Return the COMPLETE main content of this page as clean markdown.
Include all headings, paragraphs, code examples, tables.
Exclude navigation, sidebars, footers, cookie banners."
```
Collect the results into sections.

### For Next.js sites
```python
from contaix.web import fetch_nextjs_rsc, extract_rsc_page_content

sections = []
for page in pages:
    rsc = fetch_nextjs_rsc(page['url'], cache_dir='/tmp/contaix_cache')
    md = extract_rsc_page_content(rsc)
    if md:
        sections.append(f"# {page['title']}\n\n{md}")
```

## Step 4: Clean, repair, and aggregate

```python
result = '\n\n---\n\n'.join(sections)

# Repair markdown artifacts (broken links, empty links, etc.)
from contaix.web import repair_markdown
result = repair_markdown(result)

# Optional: remove duplicate blocks (nav/footer that leaked through)
from scraped.util import deduplicate_lines
result, removed = deduplicate_lines(result, min_block_size=5)

# Save
from pathlib import Path
output = Path('~/Downloads/<site_name>.md').expanduser()
output.write_text(result)
print(f"Saved to {output} ({len(result):,} chars)")
```

## Step 5: Quality check

Review the output. Look for:
- Noise from navigation/headers/footers repeated across pages
- Missing content (sections that should be there)
- Broken formatting (tables, code blocks, multi-line links)
- Duplicate content between pages

Quick diagnostic:
```python
import re
content = output.read_text()
broken_links = re.findall(r'\[[^\]]*\n[^\]]*\]\([^)]+\)', content)
if broken_links:
    print(f"{len(broken_links)} multi-line links — run repair_markdown()")
```

Fix issues by adjusting the extraction approach per-page if needed.

## Combining with other contaix tools

### Add code from a GitHub repo
```python
from contaix import code_aggregate
code_md = code_aggregate('https://github.com/org/repo')
full = f"{website_md}\n\n---\n\n# Source Code\n\n{code_md}"
```

### Convert final markdown to PDF
```bash
pandoc output.md -o output.pdf --pdf-engine=xelatex
```
