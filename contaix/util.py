"""
General utilities for contaix

This module provides core utility functions used throughout the contaix package, including:
- File path handling (fullpath)
- URL detection and content retrieval (is_url, url_to_contents)
- File saving utilities (save_to_file_and_return_file)
- Basic helper functions (identity)
"""

# TODO: A lot of these were for contaix.markdown, which has moved to dn.src. Get rid of unnecessary definitions

import os
import functools
import inspect
from typing import Union, Optional
from collections.abc import Callable
import requests
from dol import written_key

# imports just to have these functions available in the contaix namespace
from scraped import (  # noqa: F401
    markdown_of_site,
    download_site,
    scrape_multiple_sites,
    acquire_content,
)


def identity(x):
    """
    Returns the input unchanged.

    Args:
        x: Any input

    Returns:
        The input unchanged
    """
    return x


def fullpath(path: str) -> str:
    """
    Returns the full path of the given path.

    Args:
        path (str): The path to convert to a full path.

    Returns:
        str: The full path.

    Example:

    >>> fullpath('~/Downloads')  # doctest: +SKIP
    '/home/user/Downloads'

    >>> fullpath('.')  # doctest: +SKIP
    '/home/user/python_projects/aix/aix'

    """
    return os.path.abspath(os.path.expanduser(path))


def is_url(path: str) -> bool:
    """
    Check if the given path is a URL.

    Args:
        path (str): Path to check

    Returns:
        bool: True if the path is a URL, False otherwise
    """
    return isinstance(path, str) and path.startswith(("http://", "https://"))


DFLT_URL_TO_CONTENTS_KIND = 'binary'
DFLT_URL_TO_CONTENTS_TIMEOUT = 10  # seconds


def url_to_contents(
    url: str,
    *,
    kind=DFLT_URL_TO_CONTENTS_KIND,
    timeout: int = DFLT_URL_TO_CONTENTS_TIMEOUT
) -> Optional[bytes]:
    """
    Fetch the content from a URL.

    Args:
        url (str): The URL to fetch.
        kind (str): The kind of content to fetch ('text' or 'binary' or 'response'). Defaults to 'text'.
        timeout (int): Timeout for the request in seconds. Default is 10 seconds.

    Returns:
        Optional[bytes]: The content of the URL if successful, None otherwise.
    """
    response = requests.get(url, timeout=timeout)
    response.raise_for_status()  # Raise an error for bad responses
    if kind in {'text', 'str'}:
        return response.text
    elif kind in {'binary', 'bytes'}:
        return response.content
    elif kind == 'response':
        return response
    else:
        raise ValueError("Invalid kind. Use 'text', 'binary', or 'response'.")
        raise ValueError("Invalid kind. Use 'text', 'binary', or 'response'.")


def save_to_file_and_return_file(
    obj=None, *, encoder=identity, key: str | Callable = None
):
    """
    Save `encoder(obj)` to a file using a random name in `rootdir` (or a temp directory if not provided).
    Returns the full path to the saved file.
    If `obj` is None, returns a partial function with preconfigured `encoder` and
    `rootdir`.

    Args:
        obj: The object to save. If None, return a partial function.
        encoder: A function to encode the object into text or bytes. Defaults to identity.
        key: The key (by default, filepath) to write to.
            If None, a temporary file is created.
            If a string starting with '*', the '*' is replaced with a unique temporary filename.
            If a string that has a '*' somewhere in the middle, what's on the left of if is used as a directory
            and the '*' is replaced with a unique temporary filename. For example
            '/tmp/*_file.ext' would be replaced with '/tmp/oiu8fj9873_file.ext'.
            If a callable, it will be called with obj as input to get the key. One use case
            is to use a function that generates a key based on the object.

    Returns:
        str: Full path to the saved file, or a partial function if `obj` is None.

    Examples:

    >>> from pathlib import Path
    >>> filepath = save_to_file_and_return_file("hello world")
    >>> import os
    >>> Path(filepath).read_text()
    'hello world'

    The default encoder is identity, so you can save binary data as well:

    >>> filepath = save_to_file_and_return_file(b"binary data", encoder=lambda x: x)
    >>> Path(filepath).read_bytes()
    b'binary data'
    """
    # Note: Yes, it's just written_key from dol, but with a context-sensitive name
    return written_key(obj, encoder=encoder, key=key)


def source_first_arg_from_clipboard_if_none(func):
    """Decorator that sources a `string` argument from the clipboard when it's
    None and copies the function's return value back to the clipboard when the
    keyword argument `copy_to_clipboard` is truthy.

    The wrapped function must accept a parameter named `string`. It may also
    accept a keyword-only parameter named `copy_to_clipboard` (default True).
    """

    sig = inspect.signature(func)

    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        bound = sig.bind_partial(*args, **kwargs)

        # If the function declares a `string` parameter and it is None,
        # attempt to paste from the clipboard. Let ImportError propagate for
        # the paste operation to match previous behavior.
        if 'string' in sig.parameters:
            if bound.arguments.get('string') is None:
                import pyperclip

                bound.arguments['string'] = pyperclip.paste()

        # Call the original function with the bound arguments
        result = func(**bound.arguments)

        # Determine whether to copy result to clipboard. Prefer the provided
        # argument, else fall back to the function's default if available.
        if 'copy_to_clipboard' in sig.parameters:
            copy = bound.arguments.get(
                'copy_to_clipboard', sig.parameters['copy_to_clipboard'].default
            )
        else:
            copy = True

        if copy:
            try:
                import pyperclip

                pyperclip.copy(result)
            except ImportError:
                print(
                    "pyperclip module not found (pip install pyperclip) so can't copy to clipboard"
                )

        return result

    return wrapper


@source_first_arg_from_clipboard_if_none
def remove_improperly_double_newlines(
    string: str | None,
    *,
    copy_to_clipboard=True  # Note: Yes, it's used, but obfuscated by the decorator
) -> str:
    r"""
    Remove improperly double newlines from a string.

    Args:
        string (str): The input string.

    Returns:
        str: The string with improperly double newlines removed.

    Example:

    >>> text = "This is a test.\n\nThis should be one newline.\n  \nThis too."
    >>> assert remove_improperly_double_newlines(text) == 'This is a test.\n\nThis should be one newline.\nThis too.'

    """
    import re

    double_newlines = re.compile(r'\n\ +\n')
    new_string = double_newlines.sub(
        '\n', string.replace('\n\r', '\n').replace('\r\n', '\n')
    )

    return new_string
