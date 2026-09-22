# contaix.util

General utilities for contaix

This module provides core utility functions used throughout the contaix package, including:

- File path handling (fullpath)
- URL detection and content retrieval (is_url, url_to_contents)
- File saving utilities (save_to_file_and_return_file)
- Basic helper functions (identity)

### Functions

| [`fullpath`](#contaix.util.fullpath)(path)                                    | Returns the full path of the given path.                                                                                                                                                           |
|----------------------------------------------------------------------------------------------------|----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| [`identity`](#contaix.util.identity)(x)                                       | Returns the input unchanged.                                                                                                                                                                       |
| [`is_url`](#contaix.util.is_url)(path)                                      | Check if the given path is a URL.                                                                                                                                                                  |
| [`remove_improperly_double_newlines`](#contaix.util.remove_improperly_double_newlines)(string, \*)     | Remove improperly double newlines from a string.                                                                                                                                                   |
| [`save_to_file_and_return_file`](#contaix.util.save_to_file_and_return_file)([obj, encoder, key]) | Save `encoder(obj)` to a file using a random name in `rootdir` (or a temp directory if not provided).                                                                                              |
| [`source_first_arg_from_clipboard_if_none`](#contaix.util.source_first_arg_from_clipboard_if_none)(func)     | Decorator that sources a `string` argument from the clipboard when it's None and copies the function's return value back to the clipboard when the keyword argument `copy_to_clipboard` is truthy. |
| [`url_to_contents`](#contaix.util.url_to_contents)(url, \*[, kind, timeout])         | Fetch the content from a URL.                                                                                                                                                                      |

### contaix.util.fullpath(path)

Returns the full path of the given path.

* **Parameters:**
  **path** ([`str`](https://docs.python.org/3/builtins/stdtypes.html#str)) – The path to convert to a full path.
* **Returns:**
  The full path.
* **Return type:**
  [`str`](https://docs.python.org/3/builtins/stdtypes.html#str)

### Example

```pycon
>>> fullpath('~/Downloads')
'/home/user/Downloads'
```

```pycon
>>> fullpath('.')
'/home/user/python_projects/aix/aix'
```

### contaix.util.identity(x)

Returns the input unchanged.

* **Parameters:**
  **x** – Any input
* **Returns:**
  The input unchanged

### contaix.util.is_url(path)

Check if the given path is a URL.

* **Parameters:**
  **path** ([`str`](https://docs.python.org/3/builtins/stdtypes.html#str)) – Path to check
* **Returns:**
  True if the path is a URL, False otherwise
* **Return type:**
  [`bool`](https://docs.python.org/3/builtins/functions.html#bool)

### contaix.util.remove_improperly_double_newlines(string, , copy_to_clipboard=True)

Remove improperly double newlines from a string.

Delegates to `dn.repair.remove_improperly_double_newlines` for the pure
transform, adding clipboard integration via the decorator.

* **Parameters:**
  **string** ([`str`](https://docs.python.org/3/builtins/stdtypes.html#str) | [`None`](https://docs.python.org/3/builtins/constants.html#None)) – The input string.
* **Returns:**
  The string with improperly double newlines removed.
* **Return type:**
  [`str`](https://docs.python.org/3/builtins/stdtypes.html#str)

### Example

```pycon
>>> text = "This is a test.\n\nThis should be one newline.\n  \nThis too."
>>> result = remove_improperly_double_newlines(text, copy_to_clipboard=False)
>>> assert result == 'This is a test.\n\nThis should be one newline.\nThis too.'
```

### contaix.util.save_to_file_and_return_file(obj=None, \*, encoder=<function identity>, key=None)

Save `encoder(obj)` to a file using a random name in `rootdir` (or a temp directory if not provided).
Returns the full path to the saved file.
If `obj` is None, returns a partial function with preconfigured `encoder` and
`rootdir`.

* **Parameters:**
  * **obj** – The object to save. If None, return a partial function.
  * **encoder** – A function to encode the object into text or bytes. Defaults to identity.
  * **key** ([`str`](https://docs.python.org/3/builtins/stdtypes.html#str) | [`Callable`](https://docs.python.org/3/library/collections.abc.html#collections.abc.Callable)) – The key (by default, filepath) to write to.
    If None, a temporary file is created.
    If a string starting with ‘\*’, the ‘\*’ is replaced with a unique temporary filename.
    If a string that has a ‘\*’ somewhere in the middle, what’s on the left of if is used as a directory
    and the ‘\*’ is replaced with a unique temporary filename. For example
    ‘/tmp/\*_file.ext’ would be replaced with ‘/tmp/oiu8fj9873_file.ext’.
    If a callable, it will be called with obj as input to get the key. One use case
    is to use a function that generates a key based on the object.
* **Returns:**
  Full path to the saved file, or a partial function if `obj` is None.
* **Return type:**
  [*str*](https://docs.python.org/3/builtins/stdtypes.html#str)

### Examples

```pycon
>>> from pathlib import Path
>>> filepath = save_to_file_and_return_file("hello world")
>>> import os
>>> Path(filepath).read_text()
'hello world'
```

The default encoder is identity, so you can save binary data as well:

```pycon
>>> filepath = save_to_file_and_return_file(b"binary data", encoder=lambda x: x)
>>> Path(filepath).read_bytes()
b'binary data'
```

### contaix.util.source_first_arg_from_clipboard_if_none(func)

Decorator that sources a `string` argument from the clipboard when it’s
None and copies the function’s return value back to the clipboard when the
keyword argument `copy_to_clipboard` is truthy.

The wrapped function must accept a parameter named `string`. It may also
accept a keyword-only parameter named `copy_to_clipboard` (default True).

### contaix.util.url_to_contents(url, , kind='binary', timeout=10)

Fetch the content from a URL.

* **Parameters:**
  * **url** ([`str`](https://docs.python.org/3/builtins/stdtypes.html#str)) – The URL to fetch.
  * **kind** ([*str*](https://docs.python.org/3/builtins/stdtypes.html#str)) – The kind of content to fetch (‘text’, ‘binary’, or ‘response’). Defaults to ‘binary’.
  * **timeout** ([`int`](https://docs.python.org/3/builtins/functions.html#int)) – Timeout for the request in seconds. Default is 10 seconds.
* **Returns:**
  The content of the URL if successful, None otherwise.
* **Return type:**
  [`Optional`](https://docs.python.org/3/library/typing.html#typing.Optional)[[`bytes`](https://docs.python.org/3/builtins/stdtypes.html#bytes)]
