"""
Tools to make contexts (knowledge bases for AI agents)

Examples:

Download all articles from a markdown string and save them as PDF files:

>>> download_articles(md_string)  # doctest: +SKIP

Verify URLs in a markdown string by checking their status codes
(useful when trying to verify if AI hallucinated the urls)
x`
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
    # from scraped:
    markdown_of_site,
    download_site,
    scrape_multiple_sites,
    acquire_content,
)
from contaix.aggregation import aggregate_store
from contaix.code import code_aggregate, PackageCodeContexts
from contaix.urls import (
    extract_urls,
    verify_urls,
    download_articles,
    download_articles_by_section,
)
from contaix.markdown import (
    bytes_to_markdown,
    bytes_store_to_markdown_store,
    dflt_converters,
    add_dflt_converter,
    truncate_text,
    notebook_to_markdown,
)
