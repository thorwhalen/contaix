# contaix

Tools to make contexts (knowledge bases) for AI.

contaix turns diverse sources — code repos, documentation sites, file
collections — into clean markdown contexts for AI agents to consume.

```bash
pip install contaix
```

## Claude Code Skills

contaix ships with [Claude Code](https://claude.com/claude-code) skills so an
AI agent can use it directly. After installing, run:

```bash
python -m contaix.skills
```

This symlinks each skill into `~/.claude/skills/`, where Claude Code discovers
them automatically.

| Skill | When the agent uses it |
|-------|------------------------|
| `contaix_docs_to_markdown` | "Get me the docs", "download documentation", "make a markdown of this docs site" |
| `contaix_web_aggregate` | "Aggregate these pages into markdown" — falls back to manual curation when sites need it |
| `dn-repair` (from [dn](https://github.com/thorwhalen/dn)) | "Clean up this markdown", "fix broken links" |
| `pdfdol-read` (from [pdfdol](https://github.com/thorwhalen/pdfdol)) | "Extract text from these PDFs" |
| `pdfdol-convert` (from [pdfdol](https://github.com/thorwhalen/pdfdol)) | "Convert this to PDF" |

`python -m contaix.skills` also picks up skills shipped by the related
packages (`dn`, `pdfdol`) when those are installed — one command wires up
the whole ecosystem.

## Quick Start

### Documentation site → single markdown file

```python
from contaix.web import site_to_markdown

site_to_markdown(
    'https://fal.ai/docs/documentation',
    output_file='~/Downloads/fal_ai_docs.md',
    verbose=True,
)
```

`site_to_markdown` first probes the site for a publisher-provided
`/llms-full.txt` bundle (Mintlify, Docusaurus, Fern, and others ship one).
If found, it returns that directly — one HTTP request, clean markdown, no
scraping. Otherwise it falls back to discovering navigation, fetching every
page (with caching), and aggregating.

To bypass the fast path or grab the bundle yourself:

```python
from contaix.web import find_llms_full_url, fetch_llms_full

bundle_url = find_llms_full_url('https://fal.ai/docs')   # str or None
markdown   = fetch_llms_full('https://fal.ai/docs')      # str or None
```

### Code base → single markdown file

```python
from contaix import code_aggregate

# A local package
md = code_aggregate('contaix')

# A directory
md = code_aggregate('/path/to/project')

# A GitHub repo (downloaded via hubcap)
md = code_aggregate('https://github.com/thorwhalen/contaix')

# Save instead of return
code_aggregate('contaix', egress='/tmp/contaix_code.md')
```

### Files → markdown

```python
from contaix import bytes_to_markdown, bytes_store_to_markdown_store
from dol import Files

# Single file (auto-detects format)
md = bytes_to_markdown(open('report.pdf', 'rb').read(), input_format='pdf')

# A whole folder
src = Files('/path/to/documents')
target = {}
bytes_store_to_markdown_store(src, target)
```

Markdown conversion is delegated to [`dn.src`](https://github.com/thorwhalen/dn)
and supports PDF, DOCX, XLSX, PPTX, HTML, IPYNB, and more.

### Cleanup of messy markdown (e.g. ChatGPT exports)

```python
from contaix import remove_hyperlink_crap, remove_improperly_double_newlines

# Reads from clipboard if no arg, copies result back
clean = remove_hyperlink_crap()
```

Pure transforms live in [`dn.repair`](https://github.com/thorwhalen/dn);
the contaix wrappers add clipboard integration.

### URLs in prose → article PDFs

```python
from contaix import extract_urls, download_articles, verify_urls

# Inspect what URLs are in a string
list(extract_urls("[OpenAI](https://openai.com) and https://anthropic.com"))
# -> [('OpenAI', 'https://openai.com'), ('https://anthropic.com', 'https://anthropic.com')]

# Verify they resolve
verify_urls(['https://openai.com', 'https://anthropic.com'])
# -> {'https://openai.com': 200, 'https://anthropic.com': 200}

# Download as PDFs (delegates to pdfdol)
download_articles(some_md_string, save_dir='~/Downloads/articles')
```

## Package Map

```
contaix/
  web.py           # site_to_markdown, find_llms_full_url, RSC extraction
  code.py          # code_aggregate, PackageCodeContexts, GitHub fetch
  markdown.py      # bytes_to_markdown (delegates to dn.src)
  urls.py          # extract_urls, verify_urls, download_articles
  aggregation.py   # aggregate_store with deduplication and chunking
  util.py          # markdown_of_site, scrape utilities, clipboard helpers
  skills.py        # discover and install ecosystem skills
  data/skills/     # ships SKILL.md files for AI agents
```

## Architecture

- Functions are the primary interface; classes are reserved for stateful
  workflows (e.g. `PackageCodeContexts`).
- `dol` store abstractions for file/data access throughout.
- Smart defaults with keyword-only configurability — out of the box for
  common cases, fully parameterizable when needed.
- Pure transforms live in domain packages (`dn`, `pdfdol`); contaix is the
  orchestration and UX layer.

## Optional dependencies

- `pdfdol` — for `download_articles` and PDF round-trips
  (`pip install contaix[pdf]`)
- `dn[all]` — for the full set of file-format converters
  (`pip install contaix[all]`)

## Related packages

- [`dn`](https://github.com/thorwhalen/dn) — pure markdown conversion and repair
- [`pdfdol`](https://github.com/thorwhalen/pdfdol) — PDF reading, writing, and
  format conversion
- [`dol`](https://github.com/i2mint/dol) — store abstractions used everywhere
- [`scraped`](https://github.com/thorwhalen/scraped) — scraping primitives
- [`hubcap`](https://github.com/thorwhalen/hubcap) — GitHub repo access
