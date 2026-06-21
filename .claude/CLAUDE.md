# contaix - Tools to make contexts for AI

contaix creates knowledge bases (contexts) from diverse sources -- code repos,
documentation sites, file collections -- for consumption by AI agents.

## Package Structure

```
contaix/
  __init__.py      # Public API exports
  web.py           # Website-to-markdown: site_to_markdown, extract_site_nav
  urls.py          # URL extraction, verification (PDF download delegates to pdfdol)
  code.py          # Code aggregation: code_aggregate, PackageCodeContexts
  aggregation.py   # Store aggregation with deduplication
  markdown.py      # File format conversion (delegates to dn.src)
  util.py          # Utilities (markdown cleanup delegates to dn.repair)
  skills.py        # Skill discovery across OTHER ecosystem packages
```

contaix's own skills now live at the repo root `skills/` (gh-distributed via
`gh skill install`), symlinked into `.claude/skills/`. (`contaix/data/skills/`
was retired in favor of gh distribution; `skills.py` still discovers other
packages' `data/skills/` — a follow-up may retire/repoint it.)

## Dependencies

**Required:** dol, dn[html], lkj, scraped, html2text, hubcap
**Optional:** pdfdol (for PDF article downloading), dn[all] (for all format converters)

Markdown repair functions live in **dn.repair** (contaix re-exports them).
PDF download functions live in **pdfdol.download** (contaix wraps with clipboard).

## Skill Ecosystem

Skills from contaix and its dependencies are discoverable via:
```python
from contaix.skills import discover_skills, install_skills
discover_skills()   # Find skills in contaix, dn, pdfdol
install_skills()    # Symlink them into ~/.claude/skills/
# Or: python -m contaix.skills
```

Available skills:
- `contaix_docs_to_markdown` - Convert a documentation website to markdown
- `contaix_web_aggregate` - General web content aggregation
- `dn-repair` - Markdown repair and cleanup
- `pdfdol-read` - Read and process PDFs
- `pdfdol-convert` - Convert formats to PDF

## Architecture Principles

- Functions are the primary interface (not classes)
- `dol` store abstractions for file/data access
- Smart defaults with keyword-only configurability
- Pure transforms in domain packages (dn, pdfdol); UX wrappers (clipboard) in contaix
- Own skills in repo-root `skills/` (gh-distributed via `gh skill install`), symlinked into `.claude/skills/`
