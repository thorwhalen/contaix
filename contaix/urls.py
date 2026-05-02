"""
Work with urls
"""

# --------------------------------------------------------------------------------------
# Download articles from a markdown string and save them as PDF files

# TODO: Make download_articles more general:
#       - Allowed file types should be handled by plugin dependency injection
#       - There should be a separate title/url extractor that can be passed in
#       - When title is missing, some url_to_filenae should be used (see graze)?
#       - download_articles_by_section should be merged with download_articles

import os
import re
from typing import Tuple, Optional
from collections.abc import Callable, Iterator
from re import Pattern
import requests

DFLT_SAVE_DIR = os.path.expanduser("~/Downloads")


def _strip_trailing_url_punctuation(url: str) -> str:
    """Strip common trailing punctuation from a URL.

    This is useful when URLs appear in prose like "see https://example.com).".

    >>> _strip_trailing_url_punctuation('https://example.com).')
    'https://example.com'
    >>> _strip_trailing_url_punctuation('https://example.com/path?a=1&b=2')
    'https://example.com/path?a=1&b=2'
    """

    return url.rstrip(')].,;:!?*"\'"')


# Default URL matching:
# - Markdown links: [context](https://example.com/...)
# - Bare URLs in prose: https://example.com/...
DFLT_BARE_URL_PATTERN = (
    r"https?://(?:[-\w.]|(?:%[\da-fA-F]{2}))+(?::\d+)?" r"(?:/[^\s()<>\[\]{}\",\']*)?"
)

DFLT_URL_EXTRACTION_PATTERN = re.compile(
    rf"\[([^\]]+)\]\(({DFLT_BARE_URL_PATTERN})\)|({DFLT_BARE_URL_PATTERN})"
)


def _get_head_with_headers(
    url: str, *, timeout: int = 10, headers: dict | None = None
) -> requests.Response:
    """
    Make a HEAD request with proper headers to avoid 403 blocks.

    Args:
        url: The URL to request
        timeout: Request timeout in seconds
        headers: Optional additional headers to merge in

    Returns:
        Response object
    """
    default_headers = {
        "User-Agent": "Mozilla/5.0 (compatible; URLVerifier/1.0; +https://github.com/thorwhalen/contaix)"
    }
    if headers:
        default_headers.update(headers)

    return requests.head(
        url, allow_redirects=True, timeout=timeout, headers=default_headers
    )


def get_from_clipboard():
    import pyperclip  # pip install pyperclip

    return pyperclip.paste()


def extract_urls(
    markdown: str | None = None,
    pattern: Pattern | None = None,
    extractor: Callable[[re.Match], tuple[str, str]] | None = None,
) -> Iterator[tuple[str, str]]:
    """
    Extract URLs and their context from a markdown string.

    Args:
        markdown: The markdown string to process
        pattern: A compiled regex pattern to match URLs and their context.
            Defaults to matching both markdown hyperlinks ``[context](url)``
            and bare ``http(s)://...`` URLs.
        extractor: A function that extracts ``(context, url)`` from a match.
            Defaults to:
            - ``(context, url)`` for markdown hyperlinks
            - ``(url, url)`` for bare URLs

    Returns:
        Iterator of (context, url) pairs

    >>> text = "[Google](https://google.com) and https://github.com"
    >>> list(extract_urls(text))
    [('Google', 'https://google.com'), ('https://github.com', 'https://github.com')]
    """
    markdown = markdown or get_from_clipboard()

    if pattern is None:
        pattern = DFLT_URL_EXTRACTION_PATTERN

    if extractor is None:
        # Default extractor for markdown hyperlinks OR bare urls
        def extractor(match: re.Match) -> tuple[str, str]:
            md_context = match.group(1)
            md_url = match.group(2)
            bare_url = match.group(3)

            url = md_url or bare_url or ""
            url = _strip_trailing_url_punctuation(url)

            if md_context is not None and md_url is not None:
                return md_context, url

            # For bare URLs, use the URL as the context/name
            return url, url

    for match in pattern.finditer(markdown):
        yield extractor(match)


# Example alternative patterns and extractors


def extract_markdown_links(
    markdown: str | None = None, pattern: Pattern | None = None
) -> Iterator[tuple[str, str]]:
    """
    Extract markdown links from a string.

    Note: By default this also extracts bare ``http(s)://...`` URLs found in the
    text. For those, the returned context/name is the URL itself.

    Args:
        markdown: The markdown string to process
        pattern: A compiled regex pattern to match markdown links

    Returns:
        Iterator of (context, url) pairs

    >>> text = "[Google](https://google.com) and https://github.com"
    >>> list(extract_markdown_links(text))
    [('Google', 'https://google.com'), ('https://github.com', 'https://github.com')]
    """
    markdown = markdown or get_from_clipboard()
    pattern = pattern or DFLT_URL_EXTRACTION_PATTERN
    return extract_urls(markdown, pattern=pattern)


def extract_with_surrounding_context(
    markdown: str | None = None, context_chars: int = 30
) -> Iterator[tuple[str, str]]:
    """
    Extract URLs with surrounding text as context.

    Args:
        markdown: The markdown string to process
        context_chars: Number of characters to include before and after URL

    Returns:
        Iterator of (context, url) pairs

    >>> text = "Check this link: [Google](https://google.com) and [GitHub](https://github.com)"
    >>> list(extract_with_surrounding_context(text, context_chars=5))
    [('gle](https://google.com) and', 'https://google.com)'), ('Hub](https://github.com)', 'https://github.com)')]

    """
    markdown = markdown or get_from_clipboard()
    # Pattern to match URLs with a simple validation
    pattern = re.compile(r"https?://[^\s]+")

    def surrounding_context_extractor(match: re.Match) -> tuple[str, str]:
        url = match.group(0)
        start = max(0, match.start() - context_chars)
        end = min(len(markdown), match.end() + context_chars)
        context = markdown[start:end].strip()
        return context, url

    return extract_urls(markdown, pattern, surrounding_context_extractor)


def extract_urls_only(markdown: str | None = None) -> Iterator[tuple[str, str]]:
    """
    Extract URLs with empty context.

    Args:
        markdown: String containing markdown text

    Returns:
        Iterator of tuples with empty string and extracted URLs

    >>> list(extract_urls_only("Check [this link](https://example.com) and https://github.com/user/repo)"))
    [('', 'https://example.com'), ('', 'https://github.com/user/repo')]
    """
    markdown = markdown or get_from_clipboard()
    # Improved URL pattern that stops at common ending characters
    pattern = re.compile(DFLT_BARE_URL_PATTERN)

    def url_only_extractor(match: re.Match) -> tuple[str, str]:
        url = match.group(0)
        url = _strip_trailing_url_punctuation(url)
        return "", url

    return extract_urls(markdown, pattern, url_only_extractor)


def extract_html_links(markdown: str | None = None) -> Iterator[tuple[str, str]]:
    """
    Extract URLs from HTML anchor tags.

    Args:
        markdown: The markdown or HTML string to process

    Returns:
        Iterator of (anchor_text, url) pairs
    """
    markdown = markdown or get_from_clipboard()
    # Simple pattern for HTML anchor tags
    pattern = re.compile(r'<a\s+(?:[^>]*?\s+)?href="([^"]*)"[^>]*>(.*?)</a>')

    def html_link_extractor(match: re.Match) -> tuple[str, str]:
        # Note the order is reversed in HTML: href first, then text
        return match.group(2), match.group(1)

    return extract_urls(markdown, pattern, html_link_extractor)


extract_urls.markdown_links = extract_markdown_links
extract_urls.with_surrounding_context = extract_with_surrounding_context
extract_urls.only_urls = extract_urls_only
extract_urls.html_links = extract_html_links

DFLT_SAVE_DIR = os.path.expanduser("~/Downloads")


def download_articles(
    md_string: str | None = None,
    save_dir: str = DFLT_SAVE_DIR,
    *,
    save_non_pdf: bool = False,
    verbose: bool = True,
):
    """Download PDF articles from markdown text. Wrapper around ``pdfdol.download``.

    If ``md_string`` is None, reads from clipboard (requires pyperclip).
    See ``pdfdol.download.download_articles`` for full documentation.
    """
    md_string = md_string or get_from_clipboard()
    try:
        from pdfdol.download import download_articles as _download_articles
    except ImportError:
        raise ImportError(
            "pdfdol is required for download_articles. "
            "Install it with: pip install pdfdol"
        )
    return _download_articles(
        md_string, save_dir, save_non_pdf=save_non_pdf, verbose=verbose
    )


def download_articles_by_section(
    md_string: str | None = None,
    rootdir=None,
    save_non_pdf: bool = False,
    *,
    section_marker: str = r"###",
):
    """Download articles by markdown section. Wrapper around ``pdfdol.download``.

    If ``md_string`` is None, reads from clipboard (requires pyperclip).
    See ``pdfdol.download.download_articles_by_section`` for full documentation.
    """
    md_string = md_string or get_from_clipboard()
    try:
        from pdfdol.download import (
            download_articles_by_section as _download_by_section,
        )
    except ImportError:
        raise ImportError(
            "pdfdol is required for download_articles_by_section. "
            "Install it with: pip install pdfdol"
        )
    return _download_by_section(
        md_string, rootdir, save_non_pdf, section_marker=section_marker
    )


def verify_urls(src: str | list | None = None) -> dict[str, int | str]:
    """
    Verifies URLs in a markdown string by checking their status codes.

    Args:
        src (str | list): The markdown string or list containing URLs.
            If a string starting with ``[``, parsed as a JSON list of URLs.
            Otherwise, URLs are extracted from the markdown text.

    Returns:
        dict: A dictionary with URLs as keys and their status codes as values.

    >>> verify_urls(['https://example.com'])  # doctest: +SKIP
    {'https://example.com': 200}
    """
    import json

    src = src or get_from_clipboard()

    if isinstance(src, list):
        urls = src
    elif src.lstrip().startswith("["):
        # Parse a JSON list of URLs (safer than eval).
        urls = json.loads(src)
    else:
        # Extract URLs from markdown / prose using the standard extractor.
        urls = [url for _, url in extract_urls(src)]

    url_status_codes = {}
    for url in urls:
        try:
            response = _get_head_with_headers(url)
            url_status_codes[url] = response.status_code
        except Exception as e:
            url_status_codes[url] = str(e)

    return url_status_codes


def remove_hyperlink_crap(string=None, copy_to_clipboard=True):
    r"""Remove unwanted hyperlinks and citations from a string.

    Typically used to clean up text copied from ChatGPT or Claude.
    Delegates to ``dn.repair.remove_hyperlink_crap`` for the pure transform,
    adding clipboard integration on top.

    If no string is specified, reads from clipboard (requires pyperclip).
    """
    from dn.repair import remove_hyperlink_crap as _remove_hyperlink_crap

    if isinstance(string, bool):
        copy_to_clipboard = string
        string = None

    string = string or get_from_clipboard()
    string = _remove_hyperlink_crap(string)

    if copy_to_clipboard:
        try:
            import pyperclip

            pyperclip.copy(string)
        except ImportError:
            print(
                "pyperclip module not found (pip install pyperclip) so can't copy to clipboard"
            )
    return string
