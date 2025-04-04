"""
General utilities for contaix

This module provides core utility functions used throughout the contaix package, including:
- File path handling (fullpath)
- URL detection and content retrieval (is_url, url_to_contents)
- File saving utilities (save_to_file_and_return_file)
- Basic helper functions (identity)
"""

import os
from typing import Union, Callable, Optional
import requests
from dol import written_key


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


def url_to_contents(url: str):
    """
    Fetch the content of a URL.

    Args:
        url (str): URL to fetch

    Returns:
        bytes: Content of the URL

    Raises:
        HTTPError: If the request fails
    """
    response = requests.get(url)
    response.raise_for_status()
    return response.content


def save_to_file_and_return_file(
    obj=None, *, encoder=identity, key: Union[str, Callable] = None
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
