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
        pattern: A compiled regex pattern to match URLs and their context
                 Defaults to matching markdown hyperlinks [context](url)
        extractor: A function that extracts (context, url) from a match
                  Defaults to extracting from markdown hyperlinks

    Returns:
        Iterator of (context, url) pairs

    >>> text = "[Google](https://google.com) and [GitHub](https://github.com)"
    >>> list(extract_urls(text))
    [('Google', 'https://google.com'), ('GitHub', 'https://github.com')]
    """
    markdown = markdown or get_from_clipboard()

    if pattern is None:
        # Default pattern matches markdown hyperlinks: [context](url)
        pattern = re.compile(r"\[([^\]]+)\]\(([^)]+)\)")

    if extractor is None:
        # Default extractor for markdown hyperlinks
        def extractor(match: re.Match) -> tuple[str, str]:
            return match.group(1), match.group(2)

    for match in pattern.finditer(markdown):
        yield extractor(match)


# Example alternative patterns and extractors


def extract_markdown_links(
    markdown: str | None = None, pattern: Pattern | None = None
) -> Iterator[tuple[str, str]]:
    """
    Extract markdown links from a string.

    Args:
        markdown: The markdown string to process
        pattern: A compiled regex pattern to match markdown links

    Returns:
        Iterator of (context, url) pairs

    >>> text = "[Google](https://google.com) and [GitHub](https://github.com)"
    >>> list(extract_markdown_links(text))
    [('Google', 'https://google.com'), ('GitHub', 'https://github.com')]
    """
    markdown = markdown or get_from_clipboard()
    pattern = pattern or re.compile(r"\[([^\]]+)\]\(([^)]+)\)")
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
    pattern = re.compile(
        r'https?://(?:[-\w.]|(?:%[\da-fA-F]{2}))+(?:/[^\s()<>[\]{},"\']*)?'
    )

    def url_only_extractor(match: re.Match) -> tuple[str, str]:
        url = match.group(0)
        # Strip trailing punctuation that might have been incorrectly included
        url = url.rstrip(')].,;:!?*"\'')
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
    """
    Downloads articles from the given markdown string and saves them as PDF files.

    Args:
        md_string (str): The markdown-style string containing titles and URLs.
        save_dir (str): The root directory to save the downloaded PDFs. Defaults to '~/Downloads'.
        save_non_pdf (bool): Whether to save non-PDF content. Defaults to False.
        verbose (bool): Whether to print detailed messages. Defaults to True.

    Returns:
        list: A list of URLs that failed to download or were invalid PDFs.

    Example:

    >>> md_string = '''
    ... - **[Valid PDF](https://example.com/file.pdf)**: A valid PDF file.
    ... - **[Invalid PDF](https://example.com/file.html)**: An HTML page, not a PDF.
    ... '''  # doctest: +SKIP
    >>> download_articles(md_string, save_non_pdf=True)  # doctest: +SKIP
    Downloaded: Valid PDF -> ~/Downloads/Valid_PDF.pdf
    Skipped (HTML or non-PDF): Invalid PDF from https://example.com/file.html
    Non-PDF content saved to: ~/Downloads/Invalid_PDF_non_pdf.html

    Tips:

    - When you knowledge base will have a lot of files, some AI systems have a hard time
        processing the large number of files. In such cases, it might be better to
        aggregate many files into a single file. See pdfdol.concat_pdfs to do this.


    """
    md_string = md_string or get_from_clipboard()
    save_dir = os.path.expanduser(save_dir)
    # Assert the save_dir exists
    assert os.path.exists(save_dir), f"Directory not found: {save_dir}"

    def clog(msg):
        if verbose:
            print(msg)

    # Regex to extract titles and URLs from the markdown string
    pattern = r"- \*\*\[(.*?)\]\((.*?)\)\*\*"
    matches = re.findall(pattern, md_string)

    failed_urls = []

    for title, url in matches:
        # Sanitize title to create a valid filename
        sanitized_title = re.sub(r"[^\w\-_\. ]", "_", title)
        filename = f"{sanitized_title}.pdf"
        filepath = os.path.join(save_dir, filename)

        try:
            response = requests.get(url, stream=True)
            response.raise_for_status()

            # Check Content-Type header
            content_type = response.headers.get("Content-Type", "")
            if "application/pdf" not in content_type:
                clog(
                    f"Skipped (HTML or non-PDF): {title} from {url} (Content-Type: {content_type})"
                )
                if save_non_pdf:
                    # Save non-PDF content with a different extension
                    non_pdf_path = os.path.join(
                        save_dir, f"{sanitized_title}_non_pdf.html"
                    )
                    with open(non_pdf_path, "wb") as f:
                        for chunk in response.iter_content(chunk_size=8192):
                            f.write(chunk)
                    clog(f"Non-PDF content saved to: {non_pdf_path}")
                failed_urls.append(url)
                continue

            # Verify PDF content by checking the first few bytes
            first_chunk = next(response.iter_content(chunk_size=8192))
            if not first_chunk.startswith(b"%PDF"):
                clog(f"Invalid PDF content: {title} from {url}")
                if save_non_pdf:
                    # Save invalid PDF content with a different extension
                    invalid_pdf_path = os.path.join(
                        save_dir, f"{sanitized_title}_invalid.pdf"
                    )
                    with open(invalid_pdf_path, "wb") as f:
                        f.write(first_chunk)
                        for chunk in response.iter_content(chunk_size=8192):
                            f.write(chunk)
                    clog(f"Invalid PDF content saved to: {invalid_pdf_path}")
                failed_urls.append(url)
                continue

            # Save the content as a PDF file
            with open(filepath, "wb") as f:
                f.write(first_chunk)  # Write the first chunk already read
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)

            clog(f"Downloaded: {title} -> {filepath}")
        except Exception as e:
            clog(f"Failed to download {title} from {url}: {e}")
            failed_urls.append(url)

    return failed_urls


def download_articles_by_section(
    md_string: str | None = None,
    rootdir=None,
    save_non_pdf: bool = False,
    *,
    section_marker: str = r"###",
):
    """
    Downloads articles from a markdown string organized by sections into subdirectories.

    This is useful, for example, when you have a large knowledge base and you want to
    organize of aggregate the articles by sections.

    Args:
        md_string (str): The markdown string with sections and articles.
        rootdir (str): The root directory where subdirectories for sections will be created.
                       Defaults to '~/Downloads'.
        save_non_pdf (bool): Whether to save non-PDF content. Defaults to False.

    Returns:
        dict: A dictionary with section names as keys and lists of failed URLs as values.
    """
    md_string = md_string or get_from_clipboard()

    if rootdir is None:
        rootdir = os.path.expanduser("~/Downloads")

    # Ensure the root directory exists
    os.makedirs(rootdir, exist_ok=True)

    # Parse sections and their content
    section_pattern = section_marker + r" (.*?)\n(.*?)(?=\n" + section_marker + r"|\Z)"
    sections = re.findall(section_pattern, md_string, re.DOTALL)

    failed_urls_by_section = {}

    for section_title, section_content in sections:
        # Create a snake-case directory name for the section
        sanitized_section_title = (
            re.sub(r"[^\w\s]", "", section_title).strip().replace(" ", "_").lower()
        )
        section_dir = os.path.join(rootdir, sanitized_section_title)
        os.makedirs(section_dir, exist_ok=True)

        print(f"\nProcessing section: {section_title} (Directory: {section_dir})")

        # Download articles for this section
        failed_urls = download_articles(
            section_content, save_dir=section_dir, save_non_pdf=save_non_pdf
        )
        failed_urls_by_section[section_title] = failed_urls

    return failed_urls_by_section


def verify_urls(md_string: str | None = None) -> dict[str, int | str]:
    """
    Verifies URLs in a markdown string by checking their status codes.

    Args:
        md_string (str): The markdown string containing URLs.

    Returns:
        dict: A dictionary with URLs as keys and their status codes as values.
    """
    md_string = md_string or get_from_clipboard()
    # Regex to extract URLs from the markdown string
    pattern = r"\[(.*?)\]\((.*?)\)"
    matches = re.findall(pattern, md_string)

    url_status_codes = {}

    for title, url in matches:
        try:
            response = requests.head(url, allow_redirects=True)
            url_status_codes[url] = response.status_code
        except Exception as e:
            url_status_codes[url] = str(e)

    return url_status_codes


def remove_hyperlink_crap(string=None, copy_to_clipboard=True):
    r"""
    Remove unwanted hyperlinks and citations from a string.
    Typically used to clean up text copied from ChatGPT (only case supported, for now).

    If no string is specified,

    remove:
        "?utm_source=chatgpt.com"
        "&utm_source=chatgpt.com"
        "oai_citation:\d*‡"

    """
    import re

    if isinstance(string, bool):
        # assume the user mistakingly was trying to control copy_to_clipboard
        copy_to_clipboard = string  # that's what they meant
        string = None  # because no string was actually given

    string = (
        string or get_from_clipboard()
    )  # if no string is given, take it from the clipboard

    string = string.replace("?utm_source=chatgpt.com", "")
    string = string.replace("&utm_source=chatgpt.com", "")
    string = re.sub(r"oai_citation:\d*‡", "", string)

    # Remove double hyperlinks of the form [[X](Y)](Y) -> [X](Y)
    # (Happens sometimes when copying from Claude)
    pattern = r'\[\[([^\]]+)\]\(([^)]+)\)\]\(\2\)'
    # Replacement string: [\1](\2) uses Group 1 (X) and Group 2 (Y)
    replacement = r'[\1](\2)'
    string = re.sub(pattern, replacement, string)

    if copy_to_clipboard:
        try:
            import pyperclip

            pyperclip.copy(string)
        except ImportError:
            print(
                "pyperclip module not found (pip install pyperclip) so can't copy to clipboard"
            )
    return string
