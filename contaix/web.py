"""Web content extraction and aggregation tools.

Functions for extracting structured content from websites and converting to markdown,
with support for navigation discovery, caching, and content aggregation.

Main entry points:

    site_to_markdown(url)  # Full pipeline: discover nav, fetch pages, aggregate
    extract_site_nav(url)  # Get ordered navigation structure from a doc site
    fetch_page(url)        # Fetch a single page's HTML with optional caching

Example::

    >>> md = site_to_markdown(
    ...     'https://platform.claude.com/docs/en/home',
    ...     cache_dir='/tmp/claude_docs_cache',
    ...     output_file='~/Downloads/claude_docs.md',
    ... )  # doctest: +SKIP

"""

import os
import re
import json
import hashlib
from pathlib import Path
from collections.abc import Callable, Mapping, Iterable
from functools import partial
from urllib.parse import urlparse, urljoin
from typing import Iterator

import requests
import html2text


# ---------------------------------------------------------------------------
# Defaults
# ---------------------------------------------------------------------------

DFLT_CACHE_DIR = os.path.join(
    os.path.expanduser('~'), '.cache', 'contaix', 'web'
)

DFLT_REQUEST_TIMEOUT = 30  # seconds

DFLT_USER_AGENT = (
    'Mozilla/5.0 (compatible; contaix/0.1; '
    '+https://github.com/thorwhalen/contaix)'
)


# ---------------------------------------------------------------------------
# Navigation extraction
# ---------------------------------------------------------------------------


def extract_site_nav(url: str, *, html: str = None) -> dict:
    """Extract navigation structure from a documentation site.

    Returns a dict with keys:
        - ``base_url``: The base URL of the site
        - ``tabs``: List of tab dicts, each with ``label`` and ``groups``
        - ``pages``: Flat ordered list of ``{path, title}`` dicts (all tabs)

    Tries, in order:
        1. Next.js RSC payload (embedded in SSR HTML)
        2. HTML ``<a>`` link extraction with path-based grouping

    Parameters
    ----------
    url : str
        The documentation site URL (e.g. a homepage or any page on the site).
    html : str, optional
        Pre-fetched HTML. If None, fetches from ``url``.
    """
    parsed = urlparse(url)
    base_url = f'{parsed.scheme}://{parsed.netloc}'

    if html is None:
        html = _fetch_html(url)

    # Strategy 1: Next.js RSC payload
    nav = _extract_nextjs_nav(html, base_url=base_url)
    if nav is not None:
        return nav

    # Strategy 2: Generic HTML link extraction
    return _extract_html_nav(html, base_url=base_url, start_url=url)


def _extract_nextjs_nav(html: str, *, base_url: str) -> dict | None:
    """Extract navigation from Next.js RSC inline payload.

    Looks for ``self.__next_f.push([1, "..."])`` chunks containing
    ``navigationData``.
    """
    chunks = re.findall(
        r'self\.__next_f\.push\(\[1,"(.*?)"\]\)', html, re.DOTALL
    )
    for chunk in chunks:
        if 'navigationData' not in chunk:
            continue
        try:
            unescaped = chunk.encode().decode('unicode_escape')
        except Exception:
            continue

        # Find the JSON object containing navigationData
        start = unescaped.find('{"navigationData"')
        if start == -1:
            continue

        # Find matching closing brace
        depth = 0
        end = start
        for j, c in enumerate(unescaped[start:], start):
            if c == '{':
                depth += 1
            elif c == '}':
                depth -= 1
            if depth == 0:
                end = j + 1
                break

        try:
            obj = json.loads(unescaped[start:end])
        except json.JSONDecodeError:
            continue

        nav_data = obj.get('navigationData', {})
        tabs = nav_data.get('tabs', [])

        # Build flat ordered page list
        pages = []
        for tab in tabs:
            for group in tab.get('groups', []):
                for page in group.get('pages', []):
                    path = page.get('path', '')
                    title = page.get('pageTitle') or page.get('sidebarTitle', '')
                    if path:
                        pages.append({
                            'path': path,
                            'title': title,
                            'url': base_url + path if path.startswith('/') else path,
                            'group': group.get('label', ''),
                            'tab': tab.get('label', ''),
                        })

        return {
            'base_url': base_url,
            'tabs': tabs,
            'pages': pages,
        }

    return None


def _extract_html_nav(
    html: str, *, base_url: str, start_url: str
) -> dict:
    """Extract navigation from HTML links as a fallback.

    Finds all internal ``<a>`` links that share a common path prefix with
    ``start_url`` and orders them by first occurrence.
    """
    from bs4 import BeautifulSoup

    parsed_start = urlparse(start_url)
    # Determine the "doc root" path prefix from the start URL
    # e.g. /docs/en/home -> /docs/en/
    path_parts = parsed_start.path.rstrip('/').rsplit('/', 1)
    doc_prefix = path_parts[0] + '/' if len(path_parts) > 1 else '/'

    soup = BeautifulSoup(html, 'html.parser')
    seen = set()
    pages = []

    for a in soup.find_all('a', href=True):
        href = a['href']
        # Normalize relative URLs
        if href.startswith('/'):
            full_url = base_url + href
        elif href.startswith('http'):
            full_url = href
        else:
            continue

        # Only include links under the doc prefix on the same domain
        parsed_href = urlparse(full_url)
        if parsed_href.netloc != parsed_start.netloc:
            continue
        if not parsed_href.path.startswith(doc_prefix):
            continue

        path = parsed_href.path
        if path in seen:
            continue
        seen.add(path)

        title = a.get_text(strip=True)
        if not title or len(title) > 200:
            continue

        pages.append({
            'path': path,
            'title': title,
            'url': full_url,
            'group': _infer_group_from_path(path, doc_prefix),
            'tab': '',
        })

    return {
        'base_url': base_url,
        'tabs': [],
        'pages': pages,
    }


def _infer_group_from_path(path: str, prefix: str) -> str:
    """Infer a group name from a URL path segment."""
    relative = path[len(prefix):]
    parts = relative.strip('/').split('/')
    if len(parts) >= 2:
        return parts[0].replace('-', ' ').title()
    return ''


# ---------------------------------------------------------------------------
# Page fetching with caching
# ---------------------------------------------------------------------------


def url_to_cache_key(url: str) -> str:
    """Convert a URL to a filesystem-safe cache key.

    >>> url_to_cache_key('https://example.com/docs/en/foo')
    'example.com__docs__en__foo.html'
    """
    parsed = urlparse(url)
    path = parsed.netloc + parsed.path.rstrip('/')
    safe = path.replace('/', '__').replace(':', '_')
    return safe + '.html'


def fetch_page(
    url: str,
    *,
    cache_dir: str = None,
    force: bool = False,
    timeout: int = DFLT_REQUEST_TIMEOUT,
) -> str:
    """Fetch a page's HTML content, with optional disk caching.

    Parameters
    ----------
    url : str
        The URL to fetch.
    cache_dir : str, optional
        Directory to cache HTML files. If None, no caching.
    force : bool
        If True, re-fetch even if cached.
    timeout : int
        Request timeout in seconds.

    Returns
    -------
    str
        The page's HTML content.
    """
    if cache_dir and not force:
        cache_path = os.path.join(cache_dir, url_to_cache_key(url))
        if os.path.isfile(cache_path):
            return Path(cache_path).read_text(encoding='utf-8')

    html = _fetch_html(url, timeout=timeout)

    if cache_dir:
        os.makedirs(cache_dir, exist_ok=True)
        cache_path = os.path.join(cache_dir, url_to_cache_key(url))
        Path(cache_path).write_text(html, encoding='utf-8')

    return html


def fetch_pages(
    urls: Iterable[str],
    *,
    cache_dir: str = None,
    force: bool = False,
    verbose: bool = False,
) -> dict[str, str]:
    """Fetch multiple pages with caching.

    Returns a dict mapping URL -> HTML content.
    Pages that fail to fetch are skipped with a warning.
    """
    results = {}
    urls = list(urls)
    for i, url in enumerate(urls):
        if verbose:
            print(f'  [{i + 1}/{len(urls)}] Fetching {url}')
        try:
            results[url] = fetch_page(url, cache_dir=cache_dir, force=force)
        except Exception as e:
            if verbose:
                print(f'    WARNING: Failed to fetch {url}: {e}')
    return results


def _fetch_html(url: str, *, timeout: int = DFLT_REQUEST_TIMEOUT) -> str:
    """Fetch HTML from a URL with standard headers."""
    headers = {'User-Agent': DFLT_USER_AGENT}
    response = requests.get(url, headers=headers, timeout=timeout)
    response.raise_for_status()
    return response.text


def fetch_nextjs_rsc(
    url: str,
    *,
    cache_dir: str = None,
    force: bool = False,
    timeout: int = DFLT_REQUEST_TIMEOUT,
) -> str:
    """Fetch page content via Next.js RSC flight endpoint.

    Next.js App Router sites serve React Server Component payloads when the
    ``RSC: 1`` header is present. These contain the full page content that
    would otherwise require JavaScript rendering.

    Parameters
    ----------
    url : str
        The page URL.
    cache_dir : str, optional
        Directory to cache RSC responses.
    force : bool
        Re-fetch even if cached.
    timeout : int
        Request timeout.

    Returns
    -------
    str
        The RSC flight data as text.
    """
    cache_key = url_to_cache_key(url).replace('.html', '.rsc')

    if cache_dir and not force:
        cache_path = os.path.join(cache_dir, cache_key)
        if os.path.isfile(cache_path):
            return Path(cache_path).read_text(encoding='utf-8')

    parsed = urlparse(url)
    headers = {
        'User-Agent': DFLT_USER_AGENT,
        'RSC': '1',
        'Next-Url': parsed.path,
    }
    response = requests.get(url, headers=headers, timeout=timeout)
    response.raise_for_status()
    text = response.text

    if cache_dir:
        os.makedirs(cache_dir, exist_ok=True)
        cache_path = os.path.join(cache_dir, cache_key)
        Path(cache_path).write_text(text, encoding='utf-8')

    return text


def is_nextjs_site(html: str) -> bool:
    """Detect if a page is served by Next.js (App Router).

    Looks for ``self.__next_f.push`` in the HTML, which is the RSC
    streaming payload signature.
    """
    return 'self.__next_f.push' in html


# ---------------------------------------------------------------------------
# Content extraction: HTML -> Markdown
# ---------------------------------------------------------------------------


def html_to_clean_markdown(
    html: str,
    *,
    body_width: int = 0,
    ignore_images: bool = True,
    include_links: bool = True,
    **html2text_options,
) -> str:
    """Convert HTML to clean markdown using html2text.

    Parameters
    ----------
    html : str
        Raw HTML content.
    body_width : int
        Line width for wrapping. 0 = no wrapping.
    ignore_images : bool
        Whether to skip image tags.
    include_links : bool
        Whether to include hyperlinks in output.
    """
    converter = html2text.HTML2Text()
    converter.body_width = body_width
    converter.ignore_images = ignore_images
    converter.ignore_links = not include_links
    converter.protect_links = True
    converter.wrap_links = False
    for key, value in html2text_options.items():
        setattr(converter, key, value)
    return converter.handle(html).strip()


# ---------------------------------------------------------------------------
# Content extraction: RSC payload -> Markdown
# ---------------------------------------------------------------------------


_RSC_RECORD_HEAD = re.compile(r'(?:^|\n)([0-9a-f]{1,4}):', re.MULTILINE)


def parse_rsc_flight(rsc_text: str) -> dict:
    """Parse RSC flight data into a dict mapping keys to parsed JSON data.

    Each RSC record starts with ``<hex_key>:<payload>``. Records come in three
    flavors:

    - ``I[...]``: module import descriptors (skipped here).
    - ``T<hex_size>,<bytes>``: a raw text chunk whose payload occupies exactly
      ``hex_size`` bytes (often markdown, code, or compiled MDX). The payload
      may contain newlines, so we read by byte count rather than splitting on
      ``\\n``.
    - Anything else: a JSON value terminated by the next record header
      (``\\n<hex>:``) or end-of-text.

    Parameters
    ----------
    rsc_text : str
        Raw RSC flight response text (``text/x-component``).

    Returns
    -------
    dict
        Mapping of hex keys to their parsed payloads.
    """
    registry = {}
    # Find every record header (key:) position; we'll slice payloads between them.
    headers = list(_RSC_RECORD_HEAD.finditer(rsc_text))
    for i, m in enumerate(headers):
        key = m.group(1)
        payload_start = m.end()
        next_start = headers[i + 1].start() if i + 1 < len(headers) else len(rsc_text)
        payload = rsc_text[payload_start:next_start]

        # Skip module imports
        if payload.startswith('I['):
            continue

        # T-chunks: payload begins with "T<hex>,<bytes...>" where <hex> is the
        # byte-length of the chunk. Read exactly that many bytes; the rest of
        # ``payload`` may be trailing whitespace before the next header.
        if payload.startswith('T'):
            t_match = re.match(r'T([0-9a-f]+),', payload)
            if t_match:
                size = int(t_match.group(1), 16)
                start = t_match.end()
                raw = payload[start:start + size]
                if '<pre' in raw and '<code' in raw:
                    code_text = _html_code_block_to_text(raw)
                    if code_text:
                        registry[key] = code_text
                elif raw.strip():
                    registry[key] = raw
                continue

        # JSON payload: it may span multiple lines, but stops at the next
        # record header. Strip any trailing whitespace that came along.
        payload = payload.rstrip()
        if not payload:
            continue
        try:
            registry[key] = json.loads(payload)
        except (json.JSONDecodeError, ValueError):
            pass
    return registry


def _html_code_block_to_text(html: str) -> str:
    """Extract plain text from an HTML <pre><code> block."""
    # Remove all HTML tags
    text = re.sub(r'<[^>]+>', '', html)
    # Decode HTML entities
    text = text.replace('&lt;', '<').replace('&gt;', '>')
    text = text.replace('&amp;', '&').replace('&quot;', '"')
    text = text.replace('&#39;', "'").replace('&nbsp;', ' ')
    return text.strip()


def rsc_tree_to_markdown(node, *, _registry: dict = None, _depth: int = 0) -> str:
    """Recursively extract markdown from a React Server Component tree node.

    The RSC tree uses the format::

        ["$", "tagName", key, {"children": ..., "className": ...}]

    or plain strings for text nodes. Component references like ``"$L2a"``
    are resolved via ``_registry`` (from :func:`parse_rsc_flight`).
    """
    if _registry is None:
        _registry = {}

    # Order matters: bool check MUST come before int/float because
    # bool is a subclass of int in Python (False == 0, True == 1)
    if node is None or isinstance(node, bool):
        return ''
    if node == '$undefined':
        return ''
    if isinstance(node, str):
        # Resolve $L references
        if node.startswith('$L') and len(node) > 2:
            ref_key = node[2:]  # strip "$L"
            if ref_key in _registry:
                resolved = _registry[ref_key]
                # If it resolved to a plain string (e.g. from T-chunk),
                # wrap it as a code block if it looks like code
                if isinstance(resolved, str):
                    if '\n' in resolved and len(resolved) > 50:
                        return f'\n\n```\n{resolved}\n```\n\n'
                    return resolved
                return rsc_tree_to_markdown(
                    resolved, _registry=_registry, _depth=_depth
                )
        return node
    if isinstance(node, (int, float)):
        return str(node)
    if isinstance(node, list):
        # Check if this is a React element: ["$", tag, key, props]
        if (
            len(node) >= 4
            and node[0] == '$'
            and isinstance(node[1], str)
        ):
            return _rsc_element_to_markdown(
                tag=node[1],
                props=node[3] if isinstance(node[3], dict) else {},
                registry=_registry,
                depth=_depth,
            )
        # Otherwise it's an array of children
        parts = []
        for child in node:
            text = rsc_tree_to_markdown(
                child, _registry=_registry, _depth=_depth
            )
            if text:
                parts.append(text)
        return ''.join(parts)
    if isinstance(node, dict):
        children = node.get('children')
        if children is not None:
            return rsc_tree_to_markdown(
                children, _registry=_registry, _depth=_depth
            )
    return ''


def _rsc_element_to_markdown(
    tag: str, props: dict, *, registry: dict, depth: int
) -> str:
    """Convert a single RSC element to markdown."""
    children_md = rsc_tree_to_markdown(
        props.get('children', ''), _registry=registry, _depth=depth + 1
    )

    # Handle $L components (React component references)
    if tag.startswith('$L'):
        # Check if this is a link component (has href prop)
        href = props.get('href', '')
        if href:
            text = children_md.strip()
            if not text:
                return ''
            # If children span multiple lines (card-style link),
            # use the first line as link text and append the rest
            lines = [l.strip() for l in text.split('\n') if l.strip()]
            if len(lines) > 1:
                title = lines[0]
                desc = ' '.join(lines[1:])
                return f'[{title}]({href}) — {desc}'
            return f'[{text}]({href})'
        # Check if this is a model-ID / code-copy component (has id prop as text)
        id_val = props.get('id', '')
        if id_val and not children_md.strip():
            return f'`{id_val}`'
        # Check if this is a code block component
        if 'language' in props or 'code' in props:
            lang = props.get('language', '')
            code = props.get('code', children_md)
            return f'\n\n```{lang}\n{code.strip()}\n```\n\n'
        # Otherwise, pass through children
        return children_md

    # Heading tags
    if tag in ('h1', 'h2', 'h3', 'h4', 'h5', 'h6'):
        level = int(tag[1])
        return f'\n\n{"#" * level} {children_md.strip()}\n\n'

    # Paragraph
    if tag == 'p':
        text = children_md.strip()
        if text:
            return f'\n\n{text}\n\n'
        return ''

    # Lists
    if tag in ('ul', 'ol'):
        return f'\n{children_md}\n'
    if tag == 'li':
        text = children_md.strip()
        if text:
            return f'- {text}\n'
        return ''

    # Code blocks
    if tag == 'pre':
        return f'\n\n```\n{children_md.strip()}\n```\n\n'
    if tag == 'code':
        text = children_md.strip()
        if '\n' in text:
            return text  # Already in a pre block
        return f'`{text}`'

    # Inline elements
    if tag in ('strong', 'b'):
        return f'**{children_md}**'
    if tag in ('em', 'i'):
        return f'*{children_md}*'
    if tag == 'a':
        href = props.get('href', '')
        text = children_md.strip()
        if href and text:
            return f'[{text}]({href})'
        return text

    # Block-level elements
    if tag == 'hr':
        return '\n\n---\n\n'
    if tag == 'br':
        return '\n'
    if tag in ('div', 'section', 'article', 'main', 'nav', 'aside'):
        # For block-level containers, check if className suggests a grid/card layout
        # and add newlines between children if so
        cls = props.get('className', '')
        if 'grid' in cls or 'flex' in cls or 'gap' in cls:
            # Re-render children with newlines between them
            children = props.get('children', [])
            if isinstance(children, list) and not (
                len(children) >= 4
                and children[0] == '$'
                and isinstance(children[1], str)
            ):
                parts = []
                for child in children:
                    text = rsc_tree_to_markdown(
                        child, _registry=registry, _depth=depth + 1
                    )
                    if text and text.strip():
                        parts.append(text.strip())
                return '\n\n'.join(parts)
        return children_md
    if tag == 'span':
        return children_md

    # Table elements
    if tag == 'table':
        return _rsc_table_to_markdown(props, registry=registry, depth=depth)
    if tag in ('thead', 'tbody'):
        return children_md
    if tag == 'tr':
        return children_md
    if tag in ('th', 'td'):
        return children_md.strip()

    # Blockquote
    if tag == 'blockquote':
        lines = children_md.strip().split('\n')
        return '\n' + '\n'.join(f'> {line}' for line in lines) + '\n'

    # Default: just return children
    return children_md


def _rsc_table_to_markdown(
    props: dict, *, registry: dict, depth: int
) -> str:
    """Convert an RSC table element to markdown table format."""
    children = props.get('children', [])

    # Collect rows by walking the tree
    rows = _collect_table_rows(children, registry=registry)
    if not rows:
        return rsc_tree_to_markdown(
            children, _registry=registry, _depth=depth
        )

    lines = []
    for i, row in enumerate(rows):
        line = '| ' + ' | '.join(cell.strip() for cell in row) + ' |'
        lines.append(line)
        # Add header separator after first row
        if i == 0:
            sep = '| ' + ' | '.join('---' for _ in row) + ' |'
            lines.append(sep)

    return '\n\n' + '\n'.join(lines) + '\n\n'


def _collect_table_rows(
    node, *, registry: dict
) -> list[list[str]]:
    """Walk an RSC tree and collect table rows as lists of cell strings."""
    rows = []

    if isinstance(node, str):
        if node.startswith('$L') and len(node) > 2:
            ref_key = node[2:]
            if ref_key in registry:
                return _collect_table_rows(registry[ref_key], registry=registry)
        return rows
    if not isinstance(node, (list, tuple)):
        return rows

    # Is this a React element?
    if len(node) >= 4 and node[0] == '$' and isinstance(node[1], str):
        tag = node[1]
        props = node[3] if isinstance(node[3], dict) else {}
        children = props.get('children', [])

        if tag.startswith('$L'):
            # Wrapper component - recurse into children
            rows.extend(_collect_table_rows(children, registry=registry))
            return rows

        if tag == 'tr':
            # Collect cells from this row
            cells = _collect_table_cells(children, registry=registry)
            if cells:
                rows.append(cells)
            return rows

        if tag in ('table', 'thead', 'tbody', 'div', 'section'):
            return _collect_table_rows(children, registry=registry)

        return rows

    # Array of children
    for child in node:
        rows.extend(_collect_table_rows(child, registry=registry))

    return rows


def _collect_table_cells(
    node, *, registry: dict
) -> list[str]:
    """Collect cell text from a table row's children."""
    cells = []

    if isinstance(node, str):
        if node.startswith('$L') and len(node) > 2:
            ref_key = node[2:]
            if ref_key in registry:
                return _collect_table_cells(
                    registry[ref_key], registry=registry
                )
        return cells
    if not isinstance(node, (list, tuple)):
        return cells

    if len(node) >= 4 and node[0] == '$' and isinstance(node[1], str):
        tag = node[1]
        props = node[3] if isinstance(node[3], dict) else {}
        children = props.get('children', [])

        if tag.startswith('$L'):
            return _collect_table_cells(children, registry=registry)

        if tag in ('td', 'th'):
            text = rsc_tree_to_markdown(
                children, _registry=registry, _depth=0
            )
            cells.append(text.strip())
            return cells

        return _collect_table_cells(children, registry=registry)

    for child in node:
        cells.extend(_collect_table_cells(child, registry=registry))

    return cells


def extract_rsc_page_content(rsc_text: str) -> str | None:
    """Extract page content from RSC flight data.

    Works on both:
    - RSC flight endpoint responses (``text/x-component``)
    - Inline RSC payloads extracted from HTML

    Returns markdown text if content was found, None otherwise.
    """
    # If this looks like HTML with inline RSC, extract the chunks first
    if rsc_text.strip().startswith('<!DOCTYPE') or '<html' in rsc_text[:200]:
        chunks = re.findall(
            r'self\.__next_f\.push\(\[1,"(.*?)"\]\)', rsc_text, re.DOTALL
        )
        rsc_lines = []
        for chunk in chunks:
            try:
                rsc_lines.append(chunk.encode().decode('unicode_escape'))
            except Exception:
                continue
        rsc_text = '\n'.join(rsc_lines)

    if not rsc_text:
        return None

    # Parse all RSC data into a registry for reference resolution
    registry = parse_rsc_flight(rsc_text)

    # Find the content node: look for lists that contain content elements
    content_parts = []
    for key, data in registry.items():
        if isinstance(data, list) and _looks_like_page_content(data):
            md = rsc_tree_to_markdown(data, _registry=registry)
            if md and len(md.strip()) > 100:
                content_parts.append(md)

    if content_parts:
        # Return the longest content part (likely the page body)
        result = max(content_parts, key=len)
        return _clean_rsc_markdown(result)

    # Fallback: no list-tree content found. Some sites (e.g. Mintlify) keep the
    # prose content in T-chunk strings rather than RSC component trees. Pick the
    # T-chunk that looks most like markdown prose (skipping CSS/JS/JSX).
    prose_chunks = [
        v for v in registry.values()
        if isinstance(v, str) and _looks_like_markdown_prose(v)
    ]
    if prose_chunks:
        result = max(prose_chunks, key=len)
        return _clean_rsc_markdown(result)
    return None


def _clean_rsc_markdown(md: str) -> str:
    """Post-process markdown from RSC extraction to fix common artifacts."""
    # Remove unresolved $L references (component placeholders)
    md = re.sub(r'\$L[0-9a-f]+', '', md)
    # Fix double-dollar (RSC escaping for literal $)
    md = re.sub(r'\$\$', '$', md)
    # Remove $undefined artifacts
    md = re.sub(r'\$undefined', '', md)
    # Fix mojibake: common UTF-8 misinterpretation patterns
    # These occur when UTF-8 multi-byte chars are decoded as latin-1/cp1252
    _mojibake_map = {
        '\u00e2\u0080\u0094': '\u2014',  # — (em dash)
        '\u00e2\u0080\u0093': '\u2013',  # – (en dash)
        '\u00e2\u0080\u0099': '\u2019',  # ' (right single quote)
        '\u00e2\u0080\u009c': '\u201c',  # " (left double quote)
        '\u00e2\u0080\u009d': '\u201d',  # " (right double quote)
        '\u00e2\u0080\u0098': '\u2018',  # ' (left single quote)
        '\u00c2\u00a0': ' ',             # non-breaking space
        '\u00e2\u0080\u00a6': '\u2026',  # … (ellipsis)
        '\u00c3\u00a9': '\u00e9',        # é
        '\u00e2\u0080\u008b': '',        # zero-width space
        '\u00e2\u00a0\u00af\u00ef\u00b8\u008f': '\u26a0\ufe0f',  # ⚠️
    }
    for bad, good in _mojibake_map.items():
        md = md.replace(bad, good)
    # Collapse double blank lines to single (keeps markdown valid)
    md = re.sub(r'\n{3,}', '\n\n', md)
    # Clean up lines that are just whitespace
    md = re.sub(r'\n[ \t]+\n', '\n\n', md)
    return md.strip()


def _looks_like_page_content(data) -> bool:
    """Heuristic: does this RSC node look like page content?

    Checks if the data contains HTML content elements (h1-h6, p, ul, etc.).
    Uses Python repr which uses single quotes.
    """
    text = repr(data)[:8000]
    content_indicators = ("'h1'", "'h2'", "'h3'", "'p'", "'ul'", "'ol'", "'pre'")
    return any(ind in text for ind in content_indicators)


# T-chunks that are obviously CSS/JS/MDX-compiled JSX rather than prose.
_CODE_CHUNK_INDICATORS = (
    'use strict', '_provideComponents', 'arguments[0]',
    '@font-face', 'function ', '() => {', 'window.', 'document.',
    'addEventListener', 'querySelector',
)
# Markdown-prose markers (cheap signal vs the heavy code markers above).
_PROSE_CHUNK_INDICATORS = ('# ', '## ', '**', '- ', '`', 'http')


def _looks_like_markdown_prose(text: str) -> bool:
    """Heuristic: is this T-chunk markdown prose rather than CSS/JS/JSX?

    Used as a fallback for sites that ship page content as raw markdown in
    T-chunks instead of as RSC component trees.
    """
    if len(text) < 100:
        return False
    head = text[:600]
    if any(marker in head for marker in _CODE_CHUNK_INDICATORS):
        return False
    return any(marker in text for marker in _PROSE_CHUNK_INDICATORS)


# ---------------------------------------------------------------------------
# llms.txt / llms-full.txt fast path
# ---------------------------------------------------------------------------

# Common locations where doc-site generators (Mintlify, Docusaurus, etc.)
# publish a single-document version of their docs for LLM consumption.
LLMS_FULL_CANDIDATES = ('/llms-full.txt', '/llms.txt')


def find_llms_full_url(
    url: str, *, timeout: int = DFLT_REQUEST_TIMEOUT
) -> str | None:
    """Probe for a publisher-provided single-doc bundle.

    Many documentation generators (Mintlify, Docusaurus, Fern, etc.) expose
    the entire docs as a single markdown file at ``/llms-full.txt`` (or
    ``/llms.txt`` for an index). When present, this is far better than
    scraping page-by-page.

    Tries, in order:

    1. Same path as the input URL with the doc-root replaced (e.g.
       ``https://site.com/docs/foo`` -> ``https://site.com/docs/llms-full.txt``).
    2. Site root (e.g. ``https://site.com/llms-full.txt``).

    Parameters
    ----------
    url : str
        Any URL on the documentation site.
    timeout : int
        HEAD request timeout.

    Returns
    -------
    str or None
        The first URL that returns HTTP 200 with non-trivial content, or
        ``None`` if none of the candidates exist.
    """
    parsed = urlparse(url)
    base = f'{parsed.scheme}://{parsed.netloc}'
    # Build candidate prefix list: longest path prefix first, then root.
    prefixes = []
    path = parsed.path.rstrip('/')
    while path:
        prefixes.append(path)
        if '/' not in path.lstrip('/'):
            break
        path = path.rsplit('/', 1)[0]
    prefixes.append('')  # site root

    headers = {'User-Agent': DFLT_USER_AGENT}
    seen = set()
    for prefix in prefixes:
        for candidate in LLMS_FULL_CANDIDATES:
            probe = base + prefix + candidate
            if probe in seen:
                continue
            seen.add(probe)
            try:
                r = requests.head(
                    probe, headers=headers, allow_redirects=True, timeout=timeout
                )
            except requests.RequestException:
                continue
            if r.status_code != 200:
                continue
            ctype = r.headers.get('content-type', '')
            # Reject HTML 200 responses (some sites return their 404 page as 200).
            if 'html' in ctype.lower():
                continue
            try:
                size = int(r.headers.get('content-length', '0'))
            except ValueError:
                size = 0
            # Anything under 500 bytes is almost certainly not a real bundle.
            if size and size < 500:
                continue
            return r.url  # follow redirects to canonical URL
    return None


def fetch_llms_full(
    url: str, *, timeout: int = DFLT_REQUEST_TIMEOUT
) -> str | None:
    """Fetch a publisher-provided single-doc bundle if available.

    See :func:`find_llms_full_url` for how the URL is discovered.

    Returns the markdown text, or ``None`` if no bundle was found.
    """
    bundle_url = find_llms_full_url(url, timeout=timeout)
    if not bundle_url:
        return None
    headers = {'User-Agent': DFLT_USER_AGENT}
    r = requests.get(bundle_url, headers=headers, timeout=timeout)
    r.raise_for_status()
    return r.text


# ---------------------------------------------------------------------------
# High-level pipeline
# ---------------------------------------------------------------------------


def site_to_markdown(
    url: str,
    *,
    cache_dir: str = None,
    output_file: str = None,
    tab_filter: str | Callable = None,
    page_fetcher: Callable = None,
    content_extractor: Callable = None,
    section_separator: str = '\n\n---\n\n',
    collapse_blank_lines: bool = True,
    use_llms_full: bool = True,
    verbose: bool = False,
) -> str:
    """Download a documentation site and produce a single aggregated markdown.

    Parameters
    ----------
    url : str
        The documentation site's root URL.
    cache_dir : str, optional
        Directory for caching fetched HTML. Defaults to ``~/.cache/contaix/web``.
    output_file : str, optional
        Path to save the markdown file. If None, returns the string.
    tab_filter : str or callable, optional
        If a string, only include pages from tabs whose label contains this
        string (case-insensitive). If a callable, ``tab_filter(tab_label) -> bool``.
    page_fetcher : callable, optional
        Custom ``(url) -> html`` function. Defaults to ``fetch_page``.
    content_extractor : callable, optional
        Custom ``(html) -> markdown`` function. Defaults to auto-detection.
    section_separator : str
        Separator between page sections in the output.
    use_llms_full : bool
        If True (default), first try to find a publisher-provided
        ``/llms-full.txt`` bundle (Mintlify, Docusaurus, etc. ship these).
        When found, returns it directly instead of scraping page-by-page.
        Disable to force the scraping pipeline. Skipped automatically when
        ``page_fetcher`` or ``tab_filter`` is set, since those imply the
        caller wants the scraping path.
    verbose : bool
        Print progress information.

    Returns
    -------
    str
        If ``output_file`` is None, returns the markdown string.
        Otherwise, returns the output file path.
    """
    if cache_dir is None:
        cache_dir = DFLT_CACHE_DIR

    # Fast path: many doc generators expose the whole site as a single markdown
    # bundle at /llms-full.txt. When available, prefer it over scraping.
    if use_llms_full and page_fetcher is None and tab_filter is None:
        if verbose:
            print(f'Probing {url} for llms-full.txt bundle...')
        try:
            bundle = fetch_llms_full(url)
        except requests.RequestException as e:
            if verbose:
                print(f'  llms-full probe failed ({e}); falling back to scrape')
            bundle = None
        if bundle:
            if verbose:
                print(
                    f'  Found publisher bundle ({len(bundle):,} chars) — '
                    'skipping per-page scrape'
                )
            if output_file:
                output_file = os.path.expanduser(output_file)
                os.makedirs(os.path.dirname(output_file) or '.', exist_ok=True)
                Path(output_file).write_text(bundle, encoding='utf-8')
                if verbose:
                    print(f'Saved to {output_file} ({len(bundle)} chars)')
                return output_file
            return bundle
        elif verbose:
            print('  No bundle found, falling back to page-by-page scrape')

    if verbose:
        print(f'Extracting navigation from {url}...')

    nav = extract_site_nav(url)
    pages = nav['pages']

    if verbose:
        print(f'Found {len(pages)} pages')

    # Apply tab filter
    if tab_filter is not None:
        if isinstance(tab_filter, str):
            filter_str = tab_filter.lower()
            pages = [p for p in pages if filter_str in p.get('tab', '').lower()]
        else:
            pages = [p for p in pages if tab_filter(p.get('tab', ''))]
        if verbose:
            print(f'After tab filter: {len(pages)} pages')

    if not pages:
        if verbose:
            print('No pages found!')
        return ''

    # Detect if this is a Next.js site (check the first page's HTML)
    _is_nextjs = False
    if page_fetcher is None:
        test_html = fetch_page(pages[0]['url'], cache_dir=cache_dir)
        _is_nextjs = is_nextjs_site(test_html)
        if verbose and _is_nextjs:
            print('Detected Next.js site - using RSC flight endpoint')

    # Set up fetcher and extractor based on site type
    if page_fetcher is not None:
        _fetcher = page_fetcher
        _extractor = content_extractor or _auto_extract_content
    elif _is_nextjs:
        _fetcher = partial(fetch_nextjs_rsc, cache_dir=cache_dir)
        _extractor = content_extractor or extract_rsc_page_content
    else:
        _fetcher = partial(fetch_page, cache_dir=cache_dir)
        _extractor = content_extractor or _auto_extract_content

    # Fetch and convert all pages
    sections = []
    current_group = None
    for i, page in enumerate(pages):
        page_url = page['url']
        title = page.get('title', '')
        group = page.get('group', '')

        if verbose:
            print(f'  [{i + 1}/{len(pages)}] {title or page_url}')

        try:
            raw = _fetcher(page_url)
            content = _extractor(raw)

            if content and content.strip():
                # Add group header when group changes
                header_parts = []
                if group and group != current_group:
                    current_group = group
                    header_parts.append(f'<!-- group: {group} -->')
                header_parts.append(f'# {title}' if title else f'# {page_url}')
                header = '\n'.join(header_parts)

                # Remove any leading h1 from content if it duplicates the title
                content = _strip_duplicate_title(content, title)

                sections.append(f'{header}\n\n{content.strip()}')
        except Exception as e:
            if verbose:
                print(f'    WARNING: Failed: {e}')

    # Aggregate
    markdown = section_separator.join(sections)

    # Clean up whitespace and repair markdown artifacts
    if collapse_blank_lines:
        markdown = re.sub(r'\n{3,}', '\n\n', markdown)
    else:
        markdown = re.sub(r'\n{4,}', '\n\n\n', markdown)
    markdown = repair_markdown(markdown)

    if output_file:
        output_file = os.path.expanduser(output_file)
        os.makedirs(os.path.dirname(output_file) or '.', exist_ok=True)
        Path(output_file).write_text(markdown, encoding='utf-8')
        if verbose:
            print(f'Saved to {output_file} ({len(markdown)} chars)')
        return output_file

    return markdown


def _auto_extract_content(html: str) -> str:
    """Automatically choose the best content extraction method.

    1. Try RSC payload extraction (for Next.js sites)
    2. Fall back to html2text on the full HTML
    """
    rsc_content = extract_rsc_page_content(html)
    if rsc_content and len(rsc_content.strip()) > 100:
        return rsc_content

    # Fallback: html2text on full HTML, trying to extract main content
    return _extract_main_content_html(html)


def _extract_main_content_html(html: str) -> str:
    """Extract main content area from HTML and convert to markdown.

    Tries to find ``<article>``, ``<main>``, or ``[role=main]`` elements
    before falling back to the full HTML.
    """
    try:
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(html, 'html.parser')

        # Try progressively broader selectors
        for selector in ['article', 'main', '[role="main"]', '.content', '#content']:
            element = soup.select_one(selector)
            if element:
                text = element.get_text(strip=True)
                if len(text) > 100:
                    return html_to_clean_markdown(str(element))

    except ImportError:
        pass

    # Full HTML fallback
    return html_to_clean_markdown(html)


def _strip_duplicate_title(content: str, title: str) -> str:
    """Remove a leading H1 from content if it duplicates the page title."""
    if not title:
        return content
    # Match a leading # Title line
    match = re.match(r'^#\s+(.+?)(?:\n|$)', content.strip())
    if match:
        h1_text = match.group(1).strip()
        if h1_text.lower() == title.lower():
            return content.strip()[match.end():].strip()
    return content


# ---------------------------------------------------------------------------
# Markdown repair utilities
# ---------------------------------------------------------------------------


# Markdown repair utilities are now in dn.repair; re-exported here for
# backward compatibility and convenience.
from dn.repair import repair_markdown  # noqa: F401
from dn.repair import fix_multiline_links  # noqa: F401
from dn.repair import fix_empty_links  # noqa: F401


# ---------------------------------------------------------------------------
# Convenience functions
# ---------------------------------------------------------------------------


def list_site_pages(url: str) -> list[dict]:
    """List all pages found in a documentation site's navigation.

    Returns a list of dicts with keys: path, title, url, group, tab.

    >>> pages = list_site_pages('https://platform.claude.com/docs/en/home')  # doctest: +SKIP
    >>> len(pages)  # doctest: +SKIP
    89
    """
    return extract_site_nav(url)['pages']
