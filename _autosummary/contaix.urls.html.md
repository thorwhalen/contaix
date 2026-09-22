# contaix.urls

Work with urls

### Functions

| [`download_articles`](#contaix.urls.download_articles)([md_string, save_dir, ...])     | Download PDF articles from markdown text.                          |
|----------------------------------------------------------------------------------------------------|--------------------------------------------------------------------|
| [`download_articles_by_section`](#contaix.urls.download_articles_by_section)([md_string, ...])    | Download articles by markdown section.                             |
| [`extract_html_links`](#contaix.urls.extract_html_links)([markdown])                    | Extract URLs from HTML anchor tags.                                |
| [`extract_markdown_links`](#contaix.urls.extract_markdown_links)([markdown, pattern])       | Extract markdown links from a string.                              |
| [`extract_urls`](#contaix.urls.extract_urls)([markdown, pattern, extractor])      | Extract URLs and their context from a markdown string.             |
| [`extract_urls_only`](#contaix.urls.extract_urls_only)([markdown])                     | Extract URLs with empty context.                                   |
| [`extract_with_surrounding_context`](#contaix.urls.extract_with_surrounding_context)([markdown, ...]) | Extract URLs with surrounding text as context.                     |
| `get_from_clipboard`()                                                                             |                                                                    |
| [`remove_hyperlink_crap`](#contaix.urls.remove_hyperlink_crap)([string, ...])              | Remove unwanted hyperlinks and citations from a string.            |
| [`verify_urls`](#contaix.urls.verify_urls)([src])                                | Verifies URLs in a markdown string by checking their status codes. |

### contaix.urls.download_articles(md_string=None, save_dir='/home/runner/Downloads', , save_non_pdf=False, verbose=True)

Download PDF articles from markdown text. Wrapper around `pdfdol.download`.

If `md_string` is None, reads from clipboard (requires pyperclip).
See `pdfdol.download.download_articles` for full documentation.

### contaix.urls.download_articles_by_section(md_string=None, rootdir=None, save_non_pdf=False, , section_marker='###')

Download articles by markdown section. Wrapper around `pdfdol.download`.

If `md_string` is None, reads from clipboard (requires pyperclip).
See `pdfdol.download.download_articles_by_section` for full documentation.

### contaix.urls.extract_html_links(markdown=None)

Extract URLs from HTML anchor tags.

* **Parameters:**
  **markdown** ([`str`](https://docs.python.org/3/builtins/stdtypes.html#str) | [`None`](https://docs.python.org/3/builtins/constants.html#None)) – The markdown or HTML string to process
* **Return type:**
  [`Iterator`](https://docs.python.org/3/library/collections.abc.html#collections.abc.Iterator)[[`tuple`](https://docs.python.org/3/builtins/stdtypes.html#tuple)[[`str`](https://docs.python.org/3/builtins/stdtypes.html#str), [`str`](https://docs.python.org/3/builtins/stdtypes.html#str)]]
* **Returns:**
  Iterator of (anchor_text, url) pairs

### contaix.urls.extract_markdown_links(markdown=None, pattern=None)

Extract markdown links from a string.

#### NOTE
By default this also extracts bare `http(s)://...` URLs found in the
text. For those, the returned context/name is the URL itself.

* **Parameters:**
  * **markdown** ([`str`](https://docs.python.org/3/builtins/stdtypes.html#str) | [`None`](https://docs.python.org/3/builtins/constants.html#None)) – The markdown string to process
  * **pattern** ([`Pattern`](https://docs.python.org/3/library/re.html#re.Pattern) | [`None`](https://docs.python.org/3/builtins/constants.html#None)) – A compiled regex pattern to match markdown links
* **Return type:**
  [`Iterator`](https://docs.python.org/3/library/collections.abc.html#collections.abc.Iterator)[[`tuple`](https://docs.python.org/3/builtins/stdtypes.html#tuple)[[`str`](https://docs.python.org/3/builtins/stdtypes.html#str), [`str`](https://docs.python.org/3/builtins/stdtypes.html#str)]]
* **Returns:**
  Iterator of (context, url) pairs

```pycon
>>> text = "[Google](https://google.com) and https://github.com"
>>> list(extract_markdown_links(text))
[('Google', 'https://google.com'), ('https://github.com', 'https://github.com')]
```

### contaix.urls.extract_urls(markdown=None, pattern=None, extractor=None)

Extract URLs and their context from a markdown string.

* **Parameters:**
  * **markdown** ([`str`](https://docs.python.org/3/builtins/stdtypes.html#str) | [`None`](https://docs.python.org/3/builtins/constants.html#None)) – The markdown string to process
  * **pattern** ([`Pattern`](https://docs.python.org/3/library/re.html#re.Pattern) | [`None`](https://docs.python.org/3/builtins/constants.html#None)) – A compiled regex pattern to match URLs and their context.
    Defaults to matching both markdown hyperlinks `[context](url)`
    and bare `http(s)://...` URLs.
  * **extractor** ([`Callable`](https://docs.python.org/3/library/collections.abc.html#collections.abc.Callable)[[[`Match`](https://docs.python.org/3/library/re.html#re.Match)], [`tuple`](https://docs.python.org/3/builtins/stdtypes.html#tuple)[[`str`](https://docs.python.org/3/builtins/stdtypes.html#str), [`str`](https://docs.python.org/3/builtins/stdtypes.html#str)]] | [`None`](https://docs.python.org/3/builtins/constants.html#None)) – 

    A function that extracts `(context, url)` from a match.
    Defaults to:
    - `(context, url)` for markdown hyperlinks
    - `(url, url)` for bare URLs
* **Return type:**
  [`Iterator`](https://docs.python.org/3/library/collections.abc.html#collections.abc.Iterator)[[`tuple`](https://docs.python.org/3/builtins/stdtypes.html#tuple)[[`str`](https://docs.python.org/3/builtins/stdtypes.html#str), [`str`](https://docs.python.org/3/builtins/stdtypes.html#str)]]
* **Returns:**
  Iterator of (context, url) pairs

```pycon
>>> text = "[Google](https://google.com) and https://github.com"
>>> list(extract_urls(text))
[('Google', 'https://google.com'), ('https://github.com', 'https://github.com')]
```

### contaix.urls.extract_urls_only(markdown=None)

Extract URLs with empty context.

* **Parameters:**
  **markdown** ([`str`](https://docs.python.org/3/builtins/stdtypes.html#str) | [`None`](https://docs.python.org/3/builtins/constants.html#None)) – String containing markdown text
* **Return type:**
  [`Iterator`](https://docs.python.org/3/library/collections.abc.html#collections.abc.Iterator)[[`tuple`](https://docs.python.org/3/builtins/stdtypes.html#tuple)[[`str`](https://docs.python.org/3/builtins/stdtypes.html#str), [`str`](https://docs.python.org/3/builtins/stdtypes.html#str)]]
* **Returns:**
  Iterator of tuples with empty string and extracted URLs

```pycon
>>> list(extract_urls_only("Check [this link](https://example.com) and https://github.com/user/repo)"))
[('', 'https://example.com'), ('', 'https://github.com/user/repo')]
```

### contaix.urls.extract_with_surrounding_context(markdown=None, context_chars=30)

Extract URLs with surrounding text as context.

* **Parameters:**
  * **markdown** ([`str`](https://docs.python.org/3/builtins/stdtypes.html#str) | [`None`](https://docs.python.org/3/builtins/constants.html#None)) – The markdown string to process
  * **context_chars** ([`int`](https://docs.python.org/3/builtins/functions.html#int)) – Number of characters to include before and after URL
* **Return type:**
  [`Iterator`](https://docs.python.org/3/library/collections.abc.html#collections.abc.Iterator)[[`tuple`](https://docs.python.org/3/builtins/stdtypes.html#tuple)[[`str`](https://docs.python.org/3/builtins/stdtypes.html#str), [`str`](https://docs.python.org/3/builtins/stdtypes.html#str)]]
* **Returns:**
  Iterator of (context, url) pairs

```pycon
>>> text = "Check this link: [Google](https://google.com) and [GitHub](https://github.com)"
>>> list(extract_with_surrounding_context(text, context_chars=5))
[('gle](https://google.com) and', 'https://google.com)'), ('Hub](https://github.com)', 'https://github.com)')]
```

### contaix.urls.remove_hyperlink_crap(string=None, copy_to_clipboard=True)

Remove unwanted hyperlinks and citations from a string.

Typically used to clean up text copied from ChatGPT or Claude.
Delegates to `dn.repair.remove_hyperlink_crap` for the pure transform,
adding clipboard integration on top.

If no string is specified, reads from clipboard (requires pyperclip).

### contaix.urls.verify_urls(src=None)

Verifies URLs in a markdown string by checking their status codes.

* **Parameters:**
  **src** ([`str`](https://docs.python.org/3/builtins/stdtypes.html#str) | [`list`](https://docs.python.org/3/builtins/stdtypes.html#list) | [`None`](https://docs.python.org/3/builtins/constants.html#None)) – The markdown string or list containing URLs.
  If a string starting with `[`, parsed as a JSON list of URLs.
  Otherwise, URLs are extracted from the markdown text.
* **Returns:**
  A dictionary with URLs as keys and their status codes as values.
* **Return type:**
  [`dict`](https://docs.python.org/3/builtins/stdtypes.html#dict)[[`str`](https://docs.python.org/3/builtins/stdtypes.html#str), [`int`](https://docs.python.org/3/builtins/functions.html#int) | [`str`](https://docs.python.org/3/builtins/stdtypes.html#str)]

```pycon
>>> verify_urls(['https://example.com'])
{'https://example.com': 200}
```
