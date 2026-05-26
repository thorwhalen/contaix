---
name: contaix-acquire-docs
description: Acquire a tool's documentation as a single agent-ready markdown bundle, plus any machine-readable specs (OpenAPI, MCP, AsyncAPI, GraphQL). Use whenever the user provides one or more URLs (or a tool/product name) and wants the docs / manual / API reference as a context bundle for an AI agent. Triggers on "acquire the docs", "get me the docs", "bundle this manual", "make a context for tool X", "download the API reference", "give me everything as one md", "fetch the OpenAPI spec", "grab the MCP spec", or any URL pointing at a documentation / developer / API / manual site. Tries cheapest paths first — GitHub source, llms.txt, raw-markdown variants of doc URLs — and only falls back to HTML scraping (via contaix_docs_to_markdown / contaix_web_aggregate) when nothing better is available.
argument-hint: <one or more docs URLs, or a tool/product name>
---

# contaix-acquire-docs — agent-ready doc bundles

Produce a single aggregated markdown file (plus side-car JSON/YAML specs when the
tool has an API or MCP) suitable to feed an AI agent as context. **The whole point
of this skill is to avoid the expensive HTML-scrape-then-clean path when a cleaner
source exists.** Climb the ladder cheapest-rung-first; stop as soon as a rung
gives a clean, complete artifact.

## Inputs to extract from the request

- **URL(s)** of the documentation site(s). If the user named a tool instead of a
  URL, search for the docs site first (try `<tool>.com/docs`, `docs.<tool>.com`,
  `<tool>.dev`, vendor's GitHub README, then a web search as last resort).
- **Pages of interest** — sometimes the user names specific sections ("Intro,
  API reference, MCP server"). Honor the ordering; don't reshuffle.
- **Output folder** — defaults to `./docs/`. Create if missing.
- **Tool kind hints** — does it have an HTTP API? an MCP server? a CLI? These
  determine which side-car specs to hunt for (step B).

If anything material is ambiguous after a quick site probe, ask one short
question before downloading hundreds of pages.

## A. The acquisition ladder — try in order, stop when one succeeds

### Rung 1 — find the docs' source repository

The cleanest possible source is **markdown checked into git** by the vendor. It's
the same file the rendered site is built from — no scraping needed.

Hunt order:

1. **"Edit this page" / "Edit on GitHub" link.** Almost every modern doc generator
   adds one. Fetch the docs landing page and grep for `github.com/.*/edit/`,
   `github.com/.*/blob/`, or `github.com/.*/tree/`. The URL points directly at
   the source file.
   ```bash
   curl -sSL "<DOCS_URL>" | grep -oE 'github\.com/[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+(/(blob|tree|edit)/[^"'"'"' ]+)?' | sort -u | head -20
   ```
2. **`<meta>` / `<link>` tags** — some generators put a `repository` or
   `source-url` meta tag. Same `curl | grep` pattern, look for `<meta` and
   `<link` lines.
3. **`robots.txt` / `humans.txt` / page footer** — sometimes credits the source.
4. **GitHub repo search** for the vendor's org + likely names:
   ```bash
   gh search repos --owner <vendor-org> docs --limit 10
   gh search repos "<product> docs" --limit 10
   gh search code "site_name: <product>" --limit 10   # Jekyll / Hugo configs
   ```
   Common repo names: `<product>-docs`, `docs`, `<product>.dev`, `website`, `site`.
5. **For Mintlify sites specifically** — the source repo is usually owned by the
   vendor, not Mintlify. Check the vendor org. Mintlify repos contain a
   `docs.json` or `mint.json` at the root.

If you find a source repo:
- Clone it shallow: `git clone --depth=1 <repo-url> /tmp/<name>-src`.
- Inspect the structure (`docs/`, `pages/`, `src/content/docs/`, `content/`,
  `book/`, etc.). The `.md` / `.mdx` files **are** what gets rendered.
- Concatenate / select the ones the user asked for. **Stop here.**

### Rung 2 — pre-aggregated LLM bundles (`llms.txt` / `llms-full.txt`)

The [llms.txt convention](https://llmstxt.org) is now widely adopted (Mintlify,
Cursor, Vercel, Anthropic, Stripe, Pinecone, etc.). When present, it's the
fastest path — sometimes a single GET is the whole job.

```bash
for path in llms.txt llms-full.txt; do
  for base in "<DOCS_URL_NO_TRAILING_SLASH>" "<SITE_ROOT>"; do
    code=$(curl -sSL -o /dev/null -w "%{http_code}" "$base/$path")
    echo "$code  $base/$path"
  done
done
```

- `llms.txt` = a tiny **index** of all doc pages, each as `[Title](url): summary`.
  Useful when you only want a subset.
- `llms-full.txt` = the **full text** of every doc page, concatenated with
  `# Title\nSource: <url>\n\n<body>` headers. Often Mintlify-MDX, not pure
  markdown — components like `<Tip>`, `<ParamField>`, `<Tabs>` are kept. That's
  fine; agents read them perfectly.

When `llms-full.txt` exists:
- Parse it once by `^# .+\nSource: .+$` headings into pages.
- **Re-order** per the user's request (the file is usually alphabetical, which is
  rarely what the user wants).
- Build a TOC, group by section, add a top note pointing at sources and any
  side-car spec files. **Stop here.**

### Rung 3 — raw-markdown variants of doc URLs

Many generators expose the source markdown at a predictable URL. **Probe one
known page** before fetching the whole site.

| Generator       | Try                                                    |
|-----------------|--------------------------------------------------------|
| Mintlify        | `<page-url>.md` (works site-wide)                      |
| Docusaurus 3+   | `<page-url>.md`                                        |
| GitBook         | `<page-url>.md` or `?format=markdown`                  |
| MkDocs Material | `<page-url>raw.md` (rare; usually no)                  |
| Nextra          | Source on GitHub; raw URL on the site is uncommon      |
| Fumadocs        | `<page-url>.mdx` (sometimes)                           |
| Starlight       | Source on GitHub (Astro Starlight); not on the site    |
| Sphinx/RTD      | `<page-url>.txt` (reST source) or `_sources/<path>.txt`|
| ReadMe.com      | No; use API                                            |

```bash
# Probe one page
curl -sSL -o /dev/null -w "%{http_code} %{size_download}\n" "<DOC_PAGE>.md"
```

If `200` and the body looks like markdown (`#`, `_`, ` ``` `) — not HTML —
sweep the rest of the pages by iterating the URL list from rung 4.

### Rung 4 — enumerate the page list

Three sources of page lists, cheap → expensive:

1. **`llms.txt` parsing** (rung 2 fallback): even if `llms-full.txt` is missing,
   `llms.txt` is often present and gives you the full URL list.
2. **`sitemap.xml`**:
   ```bash
   curl -sSL "<SITE_ROOT>/sitemap.xml" | grep -oE '<loc>[^<]+</loc>' \
     | sed 's/<\/\?loc>//g' | grep '/docs/' | sort -u
   ```
   Some sites have `sitemap-docs.xml` or a `sitemap_index.xml`.
3. **Navigation extraction** via `contaix.web.extract_site_nav` (works on
   Next.js / Mintlify / Docusaurus).

With the URL list in hand, repeat the rung 3 probe (`<url>.md`) per page,
fetching everything that returns markdown.

### Rung 5 — HTML scrape and clean (last resort)

Only if rungs 1–4 fail. **Delegate to the existing skills:**

- **`contaix_docs_to_markdown`** — for well-structured documentation sites.
  One-call API (`site_to_markdown`), handles Next.js RSC, runs `repair_markdown`
  on the output.
- **`contaix_web_aggregate`** — for non-doc sites or JS-rendered pages that
  need WebFetch per page.

Always invoke this rung **explicitly noting** that the cheaper rungs were tried
and why each failed — that's the audit trail.

## B. Side-car spec hunt (run in parallel with A)

If the tool has an API, MCP server, or events surface, agents consuming the
bundle will get **much** better results from a machine-readable spec than from
prose. Hunt for these whenever the docs mention an API endpoint, an MCP
endpoint, webhooks, or a SDK.

### OpenAPI / Swagger

```bash
for path in openapi.json openapi.yaml openapi.yml swagger.json swagger.yaml \
            api/openapi.json v1/openapi.json docs/openapi.json \
            api-docs api-docs.json .well-known/openapi; do
  code=$(curl -sSL -o /dev/null -w "%{http_code}" "<SITE_ROOT>/$path")
  echo "$code  $path"
done
```

Also grep the docs HTML for `swagger-ui`, `redoc`, `rapidoc`, `stoplight` — these
embed an OpenAPI URL in the page source (`spec-url`, `specUrl`, `url:` props).

Save as `<tool>_openapi.json` (or `.yaml`). Validate it:
```bash
python3 -c "import json; d=json.load(open('<file>')); \
  print(d.get('openapi'), '·', d['info']['title'], d['info']['version'], \
        '·', len(d.get('paths', {})), 'paths,', \
        len(d.get('components', {}).get('schemas', {})), 'schemas')"
```

### MCP server

There is **no universal static manifest** — MCP servers expose their tool
catalog over the protocol (`tools/list` JSON-RPC). But check anyway:

```bash
for path in .well-known/mcp.json mcp.json mcp-server.json \
            mcp/manifest.json mcp/tools.json mcp-server/openapi.json; do
  code=$(curl -sSL -o /dev/null -w "%{http_code}" "<SITE_ROOT>/$path")
  echo "$code  $path"
done
```

If absent (the common case), the MCP server URL itself can be introspected:
```bash
# JSON-RPC: list tools
curl -sSL -X POST "<MCP_SERVER_URL>" \
  -H 'Content-Type: application/json' \
  -d '{"jsonrpc":"2.0","id":1,"method":"tools/list","params":{}}' | jq .
```
Requires whatever auth the server demands (usually `Authorization: Bearer ...`).
If this works, save the response as `<tool>_mcp_tools.json`.

If neither static nor live introspection works, the docs page that catalogs the
MCP tools (often `mcp-server/tools.md` or similar) is already in the bundle from
section A — note this in the top-of-file summary so agents know where to look.

### AsyncAPI (events / webhooks)

```bash
for path in asyncapi.json asyncapi.yaml events.json; do
  code=$(curl -sSL -o /dev/null -w "%{http_code}" "<SITE_ROOT>/$path")
  echo "$code  $path"
done
```

### GraphQL schema

If the docs mention GraphQL, try introspection on the API endpoint:
```bash
curl -sSL -X POST "<GRAPHQL_URL>" -H 'Content-Type: application/json' \
  -d '{"query":"{__schema{types{name kind}}}"}' | jq .
```
Save as `<tool>_graphql_schema.json`.

### Postman / Insomnia collections

Grep the docs site for `postman.com/`, `getpostman.com/run-button`,
`insomnia.rest/run/` links — those export full request collections.

## C. Assembly

1. Group pages by the section structure the user asked for (or by the section
   prefix in the URL path: `introduction/`, `api-reference/`, `mcp-server/`).
2. Demote each page's `# Title` heading down to `### Title` and wrap each section
   in `## Section`. Keep a `_Source: <url>_` line under each page heading so the
   agent can chase originals if needed.
3. Top of file: title, generation date, list of side-car files, a one-paragraph
   note explaining any preserved MDX components, and a TOC.
4. **Don't strip MDX components** (`<Tip>`, `<ParamField>`, `<ResponseField>`,
   `<Tabs>`, `<Accordion>`). They render as plain prose, carry real semantic
   structure (param types, defaults, response shapes), and stripping them loses
   info. Note their presence in the top-of-file paragraph.

A minimal stitching script is reproducible without new contaix functions —
just parse `llms-full.txt` (or the per-page `.md` files) by heading, regroup,
and rewrite. Keep the script short; don't over-abstract for one bundle.

## D. Quality checklist before declaring done

Run these against the final markdown:

```python
import re
md = open('<file>.md').read()
print(f"  size: {len(md):,} chars")
print(f"  ##  sections: {len(re.findall(r'^## ', md, re.M))}")
print(f"  ### pages:    {len(re.findall(r'^### ', md, re.M))}")
print(f"  code blocks:  {md.count(chr(96)*3) // 2}")
print(f"  external links: {len(re.findall(r'\\]\\(https?://', md))}")
# Junk that means HTML-clean went sideways
for pat, name in [(r'\\$L[0-9a-f]+', '$L refs'),
                  ('Loading\\.\\.\\.', 'Loading…'),
                  (r'^\\s*\\*?\\s*Copyright \\d{4}', 'footer leakage'),
                  ('cookie', 'cookie-banner leak')]:
    n = len(re.findall(pat, md, re.I | re.M))
    if n: print(f"  WARN {n}× {name}")
```

If the junk counters are nonzero, the markdown came from rung 5; run
`contaix.web.repair_markdown` on it and re-check.

## E. Output layout convention

In the chosen output folder:

```
docs/
├── <tool>.md                    ← the bundle
├── <tool>_openapi.json          ← when present
├── <tool>_mcp_tools.json        ← when present (live introspection)
├── <tool>_asyncapi.json         ← when present
└── <tool>_graphql_schema.json   ← when present
```

The bundle's top-of-file note should list whichever side-car files exist so
downstream agents discover them.

## F. Generator fingerprint cheatsheet

When the user gives only a URL, fingerprinting the generator narrows the
shortcuts. One `curl` of the landing page exposes most:

| Fingerprint in landing-page HTML            | Generator       | Best shortcut                          |
|---------------------------------------------|-----------------|----------------------------------------|
| `mintlify`, `mint.json`, `/_next/static/`   | Mintlify        | `llms-full.txt`, then `<url>.md`        |
| `__docusaurus`, `docusaurus`                | Docusaurus      | source repo, `sitemap.xml`, `<url>.md`  |
| `_gitbook`, `gitbook`                       | GitBook         | `?format=markdown`, source repo         |
| `<meta name="generator" content="MkDocs"`   | MkDocs          | source repo (`docs/` folder)            |
| `__VP_HASH_MAP__`, `vitepress`              | VitePress       | source repo                             |
| `data-nextra-`, `nextra`                    | Nextra          | source repo                             |
| `astro-island`, `starlight-`                | Starlight       | source repo (`src/content/docs/`)       |
| `fumadocs`                                  | Fumadocs        | source repo, sometimes `<url>.mdx`      |
| `_static/`, `sphinx`, `pydata-sphinx-theme` | Sphinx          | `<url>.txt`, source repo                |
| `<meta name="generator" content="Hugo"`     | Hugo            | source repo                             |
| `<meta name="generator" content="Jekyll"`   | Jekyll          | source repo                             |
| `readme.io`, `readme.com`                   | ReadMe.com      | their `/v1/docs` API + OpenAPI export   |

Quick probe:
```bash
curl -sSL "<DOCS_URL>" | grep -iE 'generator|mintlify|docusaurus|gitbook|nextra|vitepress|starlight|fumadocs|sphinx|hugo|jekyll|readme\.(io|com)' | head -20
```

## G. When to fall back to the older skills

Concretely: if rungs 1–4 are exhausted with no usable artifact, **hand off** to:

- `contaix_docs_to_markdown` — for the structured-docs HTML→md pipeline (its
  `site_to_markdown` already handles Next.js RSC, then `repair_markdown` cleans
  the result).
- `contaix_web_aggregate` — for sites that need per-page WebFetch curation.

This skill complements them; it doesn't replace them. The whole point is to
avoid invoking them when something cheaper works.
