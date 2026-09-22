# contaix.code

Tools to make AI contexts from code bases

### Module Attributes

| [`DFLT_AGGREGATE_EXCLUDE_PATTERNS`](#contaix.code.DFLT_AGGREGATE_EXCLUDE_PATTERNS)   | Default regex patterns matching section paths that are (almost) never useful as AI context: vendored deps, VCS internals, build/cache outputs, lockfiles, and minified bundles/sourcemaps.   |
|------------------------------------------------------------------------------------|----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|

### Functions

| [`code_aggregate`](#contaix.code.code_aggregate)(code_src, \*[, egress, ...])     | Aggregates all code segments from the given code source (folder, github url, store).                                                         |
|--------------------------------------------------------------------------------------------------|----------------------------------------------------------------------------------------------------------------------------------------------|
| [`is_local_pkg_name`](#contaix.code.is_local_pkg_name)(name)                         | Returns True if and only if name is the name of a local package.                                                                             |
| [`iter_pruned_aggregate_lines`](#contaix.code.iter_pruned_aggregate_lines)(lines, \*[, ...])   | Stream `lines` of an aggregated-code markdown, yielding only the lines that belong to sections whose header path does *not* match `exclude`. |
| [`prune_code_aggregate`](#contaix.code.prune_code_aggregate)(src, \*[, exclude, ...])   | Remove bloated sections (vendored deps, build output, lockfiles, minified bundles, ...) from an aggregated-code markdown.                    |
| [`resolve_code_source`](#contaix.code.resolve_code_source)(code_src[, keys_filt, ...]) | Will resolve code_src to a Mapping whose values are the code strings                                                                         |
| [`resolve_code_source_dir_path`](#contaix.code.resolve_code_source_dir_path)(code_src)          | Resolves code_src to a directory path string.                                                                                                |

### Classes

| [`PackageCodeContexts`](#contaix.code.PackageCodeContexts)([save_folder])   | Manages aggregation and saves of the code of local packages   |
|---------------------------------------------------------------------------------------|---------------------------------------------------------------|

### contaix.code.DFLT_AGGREGATE_EXCLUDE_PATTERNS *= ('(^|/)node_modules/', '(^|/)\\\\.git/', '(^|/)bower_components/', '(^|/)(dist|build|out|target|\\\\.next|\\\\.nuxt|\\\\.turbo|\\\\.cache|\\\\.parcel-cache|coverage|_\_pycache_\_|\\\\.pytest_cache|\\\\.mypy_cache|\\\\.tox|\\\\.venv|venv|site-packages|vendor)/', '(^|/)(package-lock\\\\.json|yarn\\\\.lock|pnpm-lock\\\\.yaml|npm-shrinkwrap\\\\.json|poetry\\\\.lock|Pipfile\\\\.lock|Cargo\\\\.lock|composer\\\\.lock|Gemfile\\\\.lock|go\\\\.sum)$', '\\\\.min\\\\.(js|mjs|cjs|css)$', '\\\\.(js|mjs|cjs|css)\\\\.map$', '\\\\.map$')*

Default regex patterns matching section paths that are (almost) never useful as AI
context: vendored deps, VCS internals, build/cache outputs, lockfiles, and minified
bundles/sourcemaps. Patterns are matched (`re.search`) against each section’s path.

### *class* contaix.code.PackageCodeContexts(save_folder='.')

Bases: [`object`](https://docs.python.org/3/builtins/functions.html#object)

Manages aggregation and saves of the code of local packages

#### multiple_pkgs_code(name=None, pkgs=(), , pkg_secion_marker='#', section_sepator='\\\\n\\\\n\\\\n')

Aggregates the code of multiple local packages in separate sections.
Saves the result to a file if a name is provided.

#### save_multiple_pkgs_code(name=None, pkgs=(), , pkg_secion_marker='#', section_sepator='\\\\n\\\\n\\\\n')

Aggregates the code of multiple local packages in separate sections.
Saves the result to a file if a name is provided.

#### save_single(pkg)

Aggregates and saves the code of a single local package.

### Example

To save a single package’s code in a single file, in the current folder:

```pycon
>>> PackageCodeContexts().save_single('aix')
```

or, to save multiple package’s code in a single file, in a specific folder.

```pycon
>>> PackageCodeContexts('some/folder/path').save_multiple_pkgs_code(['aix', 'dol'])
```

### contaix.code.code_aggregate(code_src, \*, egress=<function identity>, kv_to_item=<function <lambda>>, keys_filt='\\\\\\\\.py$', keys_exclude=None, include_readme=<function \_readme_from_parent_dir>, \*\*store_aggregate_kwargs)

Aggregates all code segments from the given code source (folder, github url, store).

This is useful when you want to use AI to search and respond to questions about a
specific code base.

* **Parameters:**
  * **code_src** (`Union`[[`str`](https://docs.python.org/3/builtins/stdtypes.html#str), [`Mapping`](https://docs.python.org/3/library/typing.html#typing.Mapping)]) – A dictionary where keys are references to the code (e.g., paths)
    and values are code snippets or content.
  * **egress** (`Union`[[`Callable`](https://docs.python.org/3/library/typing.html#typing.Callable), [`str`](https://docs.python.org/3/builtins/stdtypes.html#str)]) – A function to apply to the aggregate before returning.
    If a string, the aggregate will be saved to the file.
  * **kv_to_item** (*Callable*) – A function that converts a key-value pairs to the
    items that should be aggregated.
  * **keys_filt** (`Union`[[`Callable`](https://docs.python.org/3/library/typing.html#typing.Callable), [`str`](https://docs.python.org/3/builtins/stdtypes.html#str)]) – A function or regex string to filter the keys of the code store.
    If a string, it will be compiled to a regex pattern.
  * **keys_exclude** – Optional regex string, iterable of regex strings, or `path->bool`
    predicate identifying keys to *exclude* from the aggregate (applied
    after `keys_filt`). Use `DFLT_AGGREGATE_EXCLUDE_PATTERNS` to
    skip vendored deps, build outputs, lockfiles and minified bundles.
  * **include_readme** ([`Callable`](https://docs.python.org/3/library/typing.html#typing.Callable)) – A function that takes the code_store as input and returns
    the content of a README file to include in the aggregate.
    If None, no README will be included.
  * **\*\*store_aggregate_kwargs** – Additional keyword arguments to pass to store_aggregate.
* **Return type:**
  [*Any*](https://docs.python.org/3/library/typing.html#typing.Any)

See dol.store_aggregate for more details.

* **Returns:**
  The aggregated code content, or the result of the egress function.
* **Return type:**
  [`Any`](https://docs.python.org/3/library/typing.html#typing.Any)

### Example

```pycon
>>> code_src = {
...     'module1.py': 'def foo(): pass',
...     'module2.py': 'def bar(): pass',
...     'module3.py': 'class Baz: pass',
... }
>>> print(code_aggregate(code_src))
## module1.py
```

```python
def foo(): pass
```

<BLANKLINE>
## module2.py
<BLANKLINE>

```python
def bar(): pass
```

<BLANKLINE>
## module3.py
<BLANKLINE>

```python
class Baz: pass
```

Here, let’s input an imported (third party) package, and have the function save the
result to a temporary file

```pycon
>>> from tempfile import NamedTemporaryFile
>>> temp_file_name = NamedTemporaryFile().name
>>> import aix
>>> _  = code_aggregate(aix, egress=temp_file_name)
>>> print(open(temp_file_name).read(15))
## __init__.py
```

#### TIP
You can also import directly from the name (string) of the package by doing
`code_aggregate(__import__('aix'))` or more robustly,
`importlib.import_module('aix')`.

If you have hubcap installed, you can even get an aggregate of code from a GitHub
repository.

```pycon
>>> string = code_aggregate('https://github.com/thorwhalen/aix')
```

### contaix.code.is_local_pkg_name(name)

Returns True if and only if name is the name of a local package.

* **Return type:**
  [`bool`](https://docs.python.org/3/builtins/functions.html#bool)

### contaix.code.iter_pruned_aggregate_lines(lines, , exclude=('(^|/)node_modules/', '(^|/)\\\\\\\\.git/', '(^|/)bower_components/', '(^|/)(dist|build|out|target|\\\\\\\\.next|\\\\\\\\.nuxt|\\\\\\\\.turbo|\\\\\\\\.cache|\\\\\\\\.parcel-cache|coverage|_\_pycache_\_|\\\\\\\\.pytest_cache|\\\\\\\\.mypy_cache|\\\\\\\\.tox|\\\\\\\\.venv|venv|site-packages|vendor)/', '(^|/)(package-lock\\\\\\\\.json|yarn\\\\\\\\.lock|pnpm-lock\\\\\\\\.yaml|npm-shrinkwrap\\\\\\\\.json|poetry\\\\\\\\.lock|Pipfile\\\\\\\\.lock|Cargo\\\\\\\\.lock|composer\\\\\\\\.lock|Gemfile\\\\\\\\.lock|go\\\\\\\\.sum)$', '\\\\\\\\.min\\\\\\\\.(js|mjs|cjs|css)$', '\\\\\\\\.(js|mjs|cjs|css)\\\\\\\\.map$', '\\\\\\\\.map$'), header_prefix='## ', fence='\`\`\`', on_drop=None)

Stream `lines` of an aggregated-code markdown, yielding only the lines that
belong to sections whose header path does *not* match `exclude`.

A section header is detected *structurally*: a `header_prefix` line whose remainder
looks like a file path **and** whose next non-blank line opens a code fence. This is
deliberately not a simple “toggle on every fence” scheme – file *content* in these
aggregates routinely contains stray `` lines (vendored ``.md`/`.ts`/`.json`),
which corrupts fence-toggle state and lets bloat slip through. Requiring the
header-then-fence signature makes section boundaries robust to that.

Because it consumes and produces a line iterable, it works equally on a small
in-memory string (via `str.splitlines(keepends=True)`) and on a multi-gigabyte
file (by iterating the open file object), never holding more than a handful of lines.

* **Parameters:**
  * **lines** ([`Iterable`](https://docs.python.org/3/library/typing.html#typing.Iterable)[[`str`](https://docs.python.org/3/builtins/stdtypes.html#str)]) – Iterable of lines. Whatever line endings are present are preserved.
  * **exclude** – Regex string, iterable of regex strings, or `path->bool` predicate
    selecting sections to drop. Defaults to `DFLT_AGGREGATE_EXCLUDE_PATTERNS`.
  * **header_prefix** ([`str`](https://docs.python.org/3/builtins/stdtypes.html#str)) – Prefix marking a section header; the remainder is the path.
  * **fence** ([`str`](https://docs.python.org/3/builtins/stdtypes.html#str)) – Code-fence marker that opens a section’s content block.
  * **on_drop** ([`Optional`](https://docs.python.org/3/library/typing.html#typing.Optional)[[`Callable`](https://docs.python.org/3/library/typing.html#typing.Callable)[[[`str`](https://docs.python.org/3/builtins/stdtypes.html#str)], [`Any`](https://docs.python.org/3/library/typing.html#typing.Any)]]) – Optional callback invoked with each dropped section’s path (useful for
    logging/counting what was removed).
* **Yields:**
  The lines to keep, in original order.
* **Return type:**
  [`Iterable`](https://docs.python.org/3/library/typing.html#typing.Iterable)[[`str`](https://docs.python.org/3/builtins/stdtypes.html#str)]

### Example

```pycon
>>> md = '''## a.py
...
... ```python
... x = 1  # a heading-looking line: ## not a header
... ```
...
... ## node_modules/dep/index.js
...
... ```python
... huge minified bundle
... ```
... '''
>>> kept = ''.join(iter_pruned_aggregate_lines(md.splitlines(keepends=True)))
>>> '## a.py' in kept and 'x = 1' in kept
True
>>> 'node_modules' in kept
False
```

### contaix.code.prune_code_aggregate(src, \*, exclude=('(^|/)node_modules/', '(^|/)\\\\\\\\.git/', '(^|/)bower_components/', '(^|/)(dist|build|out|target|\\\\\\\\.next|\\\\\\\\.nuxt|\\\\\\\\.turbo|\\\\\\\\.cache|\\\\\\\\.parcel-cache|coverage|_\_pycache_\_|\\\\\\\\.pytest_cache|\\\\\\\\.mypy_cache|\\\\\\\\.tox|\\\\\\\\.venv|venv|site-packages|vendor)/', '(^|/)(package-lock\\\\\\\\.json|yarn\\\\\\\\.lock|pnpm-lock\\\\\\\\.yaml|npm-shrinkwrap\\\\\\\\.json|poetry\\\\\\\\.lock|Pipfile\\\\\\\\.lock|Cargo\\\\\\\\.lock|composer\\\\\\\\.lock|Gemfile\\\\\\\\.lock|go\\\\\\\\.sum)$', '\\\\\\\\.min\\\\\\\\.(js|mjs|cjs|css)$', '\\\\\\\\.(js|mjs|cjs|css)\\\\\\\\.map$', '\\\\\\\\.map$'), egress=<function identity>, header_prefix='## ', fence='\`\`\`', on_drop=None)

Remove bloated sections (vendored deps, build output, lockfiles, minified
bundles, …) from an aggregated-code markdown.

This is the post-hoc complement to `code_aggregate`’s `keys_exclude`: use it to
slim down an aggregate that was already generated (e.g. one that accidentally
included a `node_modules/` tree). It streams, so it handles arbitrarily large
files.

* **Parameters:**
  * **src** (`Union`[[`str`](https://docs.python.org/3/builtins/stdtypes.html#str), [`Iterable`](https://docs.python.org/3/library/typing.html#typing.Iterable)[[`str`](https://docs.python.org/3/builtins/stdtypes.html#str)]]) – The aggregate as a markdown string, a path to a markdown file, or any
    iterable of lines.
  * **exclude** – Sections to drop (see `iter_pruned_aggregate_lines`).
  * **egress** (`Union`[[`Callable`](https://docs.python.org/3/library/typing.html#typing.Callable), [`str`](https://docs.python.org/3/builtins/stdtypes.html#str)]) – What to do with the result. The default (`identity`) returns the
    pruned markdown as a string. Pass a filepath string to stream the result to
    that file (memory-safe for huge inputs) and return the filepath.
  * **header_prefix** ([`str`](https://docs.python.org/3/builtins/stdtypes.html#str)) – Aggregate format markers (see `iter_pruned_aggregate_lines`).
  * **fence** ([`str`](https://docs.python.org/3/builtins/stdtypes.html#str)) – Aggregate format markers (see `iter_pruned_aggregate_lines`).
  * **on_drop** ([`Optional`](https://docs.python.org/3/library/typing.html#typing.Optional)[[`Callable`](https://docs.python.org/3/library/typing.html#typing.Callable)[[[`str`](https://docs.python.org/3/builtins/stdtypes.html#str)], [`Any`](https://docs.python.org/3/library/typing.html#typing.Any)]]) – Optional callback invoked with each dropped section’s path.
* **Return type:**
  [`Any`](https://docs.python.org/3/library/typing.html#typing.Any)
* **Returns:**
  The pruned markdown string, or the output filepath when `egress` is a path.

### Example

```pycon
>>> md = "## keep.py\n\n```python\nok\n```\n## dist/bundle.js\n\n```python\nx\n```\n"
>>> "dist/bundle.js" in prune_code_aggregate(md)
False
```

### contaix.code.resolve_code_source(code_src, keys_filt=<function <lambda>>, \*, keys_exclude=None)

Will resolve code_src to a Mapping whose values are the code strings

* **Parameters:**
  * **code_src** (`Union`[[`str`](https://docs.python.org/3/builtins/stdtypes.html#str), [`Mapping`](https://docs.python.org/3/library/typing.html#typing.Mapping)]) – The source of the code. Can be an explicit `Mapping`,
    a directory path string,
    a GitHub URL,
    or an imported package (must contain a \_\_path_\_ atribute)
  * **keys_filt** (*Callable*) – A function or regex string to filter the keys of the code store.
    If a string, it will be compiled to a regex pattern.
  * **keys_filt** – A function to filter the keys. Defaults to lambda x: x.endswith(‘.py’).
  * **keys_exclude** – Optional regex string, iterable of regex strings, or `path->bool`
    predicate identifying keys to *exclude* (e.g. vendored deps, build outputs).
    Applied on top of (after) `keys_filt`. Pass
    `DFLT_AGGREGATE_EXCLUDE_PATTERNS` to skip the usual bloat.
* **Return type:**
  [`Mapping`](https://docs.python.org/3/library/typing.html#typing.Mapping)

### contaix.code.resolve_code_source_dir_path(code_src)

Resolves code_src to a directory path string.
If the input is a package object or name, it will return the local path where
the package is located.
If the input is a github URL, this repository will be DOWNLOAD to a local
temporary directory and the path of that directory will be returned.

* **Parameters:**
  **code_src** (`Union`[[`str`](https://docs.python.org/3/builtins/stdtypes.html#str), [`Mapping`](https://docs.python.org/3/library/typing.html#typing.Mapping)]) – The source of the code. Can be
  a directory path string,
  a GitHub URL,
  or an imported package (must contain a \_\_path_\_ atribute)
* **Return type:**
  [`str`](https://docs.python.org/3/builtins/stdtypes.html#str)
* **Returns:**
  The resolved directory path.
* **Raises:**
  [**AssertionError**](https://docs.python.org/3/builtins/exceptions.html#AssertionError) – If the resolved path is not a valid directory.
