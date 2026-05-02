"""
Tools to make contexts (knowledge bases for AI agents)

Examples:

Download all articles from a markdown string and save them as PDF files:

>>> download_articles(md_string)  # doctest: +SKIP

Verify URLs in a markdown string by checking their status codes
(useful when trying to verify if AI hallucinated the urls)

>>> verify_urls(md_string)  # doctest: +SKIP

Make an md file with all the code in a directory:

>>> md_string = code_aggregate(package_or_folder_or_github_url)  # doctest: +SKIP

"""

# --------------------------------------------------------------------------------------
# General utilities

from contaix.util import (
    identity,
    fullpath,
    url_to_contents,
    save_to_file_and_return_file,
    remove_improperly_double_newlines,
)
from contaix.aggregation import aggregate_store
from contaix.code import (
    code_aggregate,  # get markdown aggregate of code from a directory, package, or GitHub URL
    PackageCodeContexts,
)


# Lazy re-exports for names whose underlying packages (scraped, hubcap)
# raise at import time when GITHUB_TOKEN is unset. Resolving these via
# ``__getattr__`` lets ``import contaix`` succeed without a token; the
# error surfaces only if a caller actually uses one of these names.
_LAZY_FROM_UTIL = (
    'markdown_of_site',
    'download_site',
    'scrape_multiple_sites',
    'acquire_content',
)
_LAZY_FROM_CODE = ('get_github',)


def __getattr__(name):
    if name in _LAZY_FROM_UTIL:
        from contaix import util
        return getattr(util, name)
    if name in _LAZY_FROM_CODE:
        from contaix import code
        return getattr(code, name)
    raise AttributeError(f'module {__name__!r} has no attribute {name!r}')
from contaix.urls import (
    get_from_clipboard,
    extract_urls,
    verify_urls,
    download_articles,
    download_articles_by_section,
    remove_hyperlink_crap,
)
from contaix.markdown import (
    bytes_to_markdown,
    bytes_store_to_markdown_store,
    dflt_converters,
    add_dflt_converter,
    truncate_text,
    notebook_to_markdown,
)
from contaix.web import (
    site_to_markdown,
    extract_site_nav,
    list_site_pages,
    fetch_page,
    fetch_pages,
    fetch_nextjs_rsc,
    fetch_llms_full,
    find_llms_full_url,
    is_nextjs_site,
    html_to_clean_markdown,
    extract_rsc_page_content,
    repair_markdown,
)
