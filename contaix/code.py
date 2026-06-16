"""Tools to make AI contexts from code bases"""

from typing import Mapping
import os
import importlib
from typing import Any, Union, Callable, Optional, Iterable
from types import ModuleType

from dol import store_aggregate, TextFiles, filt_iter, cached_keys
from contaix.util import fullpath, identity

DirectoryPathString = str
GithubUrl = str
RegexString = str
CodeSource = Union[DirectoryPathString, GithubUrl, Mapping]


def is_local_pkg_name(name: str) -> bool:
    """Returns True if and only if name is the name of a local package."""
    try:
        importlib.import_module(name)
        return True
    except ImportError:
        return False


def resolve_code_source_dir_path(code_src: CodeSource) -> DirectoryPathString:
    """
    Resolves code_src to a directory path string.
    If the input is a package object or name, it will return the local path where
    the package is located.
    If the input is a github URL, this repository will be DOWNLOAD to a local
    temporary directory and the path of that directory will be returned.

    Args:
        code_src (Any): The source of the code. Can be
            a directory path string,
            a GitHub URL,
            or an imported package (must contain a __path__ atribute)

    Returns:
        The resolved directory path.

    Raises:
        AssertionError: If the resolved path is not a valid directory.
    """
    if isinstance(code_src, str):
        # If it's a string, check if it's a directory
        if os.path.isdir(code_src):
            return os.path.abspath(code_src)  # Return absolute path if it's a directory
        elif "\n" not in code_src and "github" in code_src:
            from hubcap import ensure_repo_folder  # pip install hubcap

            # If it's a GitHub URL, download the repository
            repo_url = code_src
            repo_path = ensure_repo_folder(repo_url)
            return repo_path
        elif is_local_pkg_name(code_src):
            code_src = importlib.import_module(code_src)  # import the package
        else:
            raise ValueError(f"Unsupported string format or non-directory: {code_src}")
    # If it's not a string, check for __path__ attribute
    if hasattr(code_src, "__path__"):
        path_list = list(code_src.__path__)
        assert len(path_list) == 1, (
            f"The __path__ attribute should contain exactly one path, "
            f"but found: {path_list}"
        )
        return os.path.abspath(path_list[0])

    # If no valid resolution was found
    raise ValueError(
        f"Unable to resolve code_src to a valid directory path: {code_src}"
    )


def resolve_code_source(
    code_src: CodeSource,
    keys_filt: Callable = lambda x: x.endswith(".py"),
    *,
    keys_exclude=None,
) -> Mapping:
    """
    Will resolve code_src to a Mapping whose values are the code strings

    Args:
        code_src: The source of the code. Can be an explicit `Mapping`,
            a directory path string,
            a GitHub URL,
            or an imported package (must contain a __path__ atribute)
        keys_filt (Union[Callable, str]): A function or regex string to filter the keys of the code store.
                                        If a string, it will be compiled to a regex pattern.
        keys_filt (Callable): A function to filter the keys. Defaults to lambda x: x.endswith('.py').
        keys_exclude: Optional regex string, iterable of regex strings, or ``path->bool``
            predicate identifying keys to *exclude* (e.g. vendored deps, build outputs).
            Applied on top of (after) ``keys_filt``. Pass
            ``DFLT_AGGREGATE_EXCLUDE_PATTERNS`` to skip the usual bloat.

    """
    if keys_filt:
        if isinstance(keys_filt, str):
            import re

            key_pattern = re.compile(keys_filt)
            keys_filt = key_pattern.search
        elif not callable(keys_filt):
            raise ValueError(f"keys_filt should be callable or string. Was {keys_filt}")
    else:
        keys_filt = lambda x: True

    if keys_exclude is not None:
        should_drop = _exclude_predicate(keys_exclude)
        _include = keys_filt
        keys_filt = lambda x: _include(x) and not should_drop(x)

    # handle a ModuleType that is a single .py file
    if isinstance(code_src, ModuleType):
        if hasattr(code_src, "__file__") and not hasattr(code_src, "__path__"):
            path = os.path.abspath(code_src.__file__)
            with open(path, "r") as f:
                return {os.path.basename(path): f.read()}

    # handle a string that points to a single-file module
    if isinstance(code_src, str):
        try:
            mod = importlib.import_module(code_src)
        except ImportError:
            pass
        else:
            if hasattr(mod, "__file__") and not hasattr(mod, "__path__"):
                path = os.path.abspath(mod.__file__)
                with open(path, "r") as f:
                    return {os.path.basename(path): f.read()}
            # if it's a package, fall through with the module object
            code_src = mod

    if isinstance(code_src, Mapping):
        return code_src
    else:
        code_src_rootdir = resolve_code_source_dir_path(code_src)
        return cached_keys(
            filt_iter(TextFiles(code_src_rootdir), filt=keys_filt), keys_cache=sorted
        )


Filepath = str


# --------------------------------------------------------------------------------------
# Pruning bloat from code aggregates
#
# Aggregates produced by ``code_aggregate`` (or any tool that walks a repo and dumps
# every file into one markdown) often sweep in content that is worthless as AI context
# and enormous in size: vendored dependencies (``node_modules/``), build/cache outputs
# (``dist/``, ``.next/``, ``__pycache__/``), lockfiles, and minified bundles/sourcemaps.
# A single ``node_modules`` tree can turn a few MB of real source into a multi-GB file.
#
# ``prune_code_aggregate`` strips those sections back out *after the fact*, operating as
# a line stream so it handles multi-gigabyte aggregates without loading them in memory.
# ``code_aggregate``/``resolve_code_source`` also accept a ``keys_exclude`` argument now,
# so freshly generated aggregates can avoid the bloat in the first place.

import re

#: Default regex patterns matching section paths that are (almost) never useful as AI
#: context: vendored deps, VCS internals, build/cache outputs, lockfiles, and minified
#: bundles/sourcemaps. Patterns are matched (``re.search``) against each section's path.
DFLT_AGGREGATE_EXCLUDE_PATTERNS = (
    r"(^|/)node_modules/",
    r"(^|/)\.git/",
    r"(^|/)bower_components/",
    r"(^|/)(dist|build|out|target|\.next|\.nuxt|\.turbo|\.cache|\.parcel-cache|"
    r"coverage|__pycache__|\.pytest_cache|\.mypy_cache|\.tox|\.venv|venv|"
    r"site-packages|vendor)/",
    r"(^|/)(package-lock\.json|yarn\.lock|pnpm-lock\.yaml|npm-shrinkwrap\.json|"
    r"poetry\.lock|Pipfile\.lock|Cargo\.lock|composer\.lock|Gemfile\.lock|go\.sum)$",
    r"\.min\.(js|mjs|cjs|css)$",
    r"\.(js|mjs|cjs|css)\.map$",
    r"\.map$",
)

#: Extension-less filenames that should still be recognized as real section headers
#: (so they are not mistaken for in-content markdown headings).
_KNOWN_EXTENSIONLESS_FILES = frozenset(
    {
        "Makefile",
        "Dockerfile",
        "LICENSE",
        "README",
        "CHANGELOG",
        "Procfile",
        "Gemfile",
        "Rakefile",
    }
)


def _exclude_predicate(exclude) -> Callable[[str], bool]:
    """Compile ``exclude`` into a ``path -> bool`` predicate (True == drop the section).

    ``exclude`` may be an iterable of regex strings, a single regex string, a callable
    predicate, or None (drop nothing).
    """
    if exclude is None:
        return lambda path: False
    if callable(exclude):
        return exclude
    if isinstance(exclude, str):
        exclude = (exclude,)
    patterns = [re.compile(p) for p in exclude]
    return lambda path: any(p.search(path) for p in patterns)


def _looks_like_section_path(path: str) -> bool:
    """Heuristic: does ``path`` look like a file path (a real section header) rather
    than an in-content markdown heading like ``## Overview``?"""
    if "/" in path:
        return True
    last = path.rsplit("/", 1)[-1]
    if last in _KNOWN_EXTENSIONLESS_FILES:
        return True
    # a short, space-free extension on the last segment, e.g. ``foo.py`` / ``a.min.js``
    return bool(re.search(r"^[^\s]+\.[A-Za-z0-9_]{1,12}$", last))


def iter_pruned_aggregate_lines(
    lines: Iterable[str],
    *,
    exclude=DFLT_AGGREGATE_EXCLUDE_PATTERNS,
    header_prefix: str = "## ",
    fence: str = "```",
    on_drop: Optional[Callable[[str], Any]] = None,
) -> Iterable[str]:
    """Stream ``lines`` of an aggregated-code markdown, yielding only the lines that
    belong to sections whose header path does *not* match ``exclude``.

    A section header is detected *structurally*: a ``header_prefix`` line whose remainder
    looks like a file path **and** whose next non-blank line opens a code fence. This is
    deliberately not a simple "toggle on every fence" scheme -- file *content* in these
    aggregates routinely contains stray ``` lines (vendored ``.md``/``.ts``/``.json``),
    which corrupts fence-toggle state and lets bloat slip through. Requiring the
    header-then-fence signature makes section boundaries robust to that.

    Because it consumes and produces a line iterable, it works equally on a small
    in-memory string (via ``str.splitlines(keepends=True)``) and on a multi-gigabyte
    file (by iterating the open file object), never holding more than a handful of lines.

    Args:
        lines: Iterable of lines. Whatever line endings are present are preserved.
        exclude: Regex string, iterable of regex strings, or ``path->bool`` predicate
            selecting sections to drop. Defaults to ``DFLT_AGGREGATE_EXCLUDE_PATTERNS``.
        header_prefix: Prefix marking a section header; the remainder is the path.
        fence: Code-fence marker that opens a section's content block.
        on_drop: Optional callback invoked with each dropped section's path (useful for
            logging/counting what was removed).

    Yields:
        The lines to keep, in original order.

    Example:

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
    """
    should_drop = _exclude_predicate(exclude)
    it = iter(lines)
    dropping = False
    for line in it:
        stripped = line.rstrip("\n")
        if stripped.startswith(header_prefix) and _looks_like_section_path(
            stripped[len(header_prefix) :].strip()
        ):
            # Candidate header: confirm by peeking for a fence opener past blank lines.
            path = stripped[len(header_prefix) :].strip()
            buffered = []
            confirmed = False
            for nxt in it:
                buffered.append(nxt)
                ns = nxt.rstrip("\n")
                if ns == "":
                    continue
                confirmed = ns.lstrip().startswith(fence)
                break
            if confirmed:
                dropping = should_drop(path)
                if dropping and on_drop is not None:
                    on_drop(path)
            # Whether or not confirmed, `line` + `buffered` belong to the current
            # section (a new one if confirmed, the ongoing one otherwise).
            if not dropping:
                yield line
                yield from buffered
            continue
        if not dropping:
            yield line


def prune_code_aggregate(
    src: Union[str, Iterable[str]],
    *,
    exclude=DFLT_AGGREGATE_EXCLUDE_PATTERNS,
    egress: Union[Callable, Filepath] = identity,
    header_prefix: str = "## ",
    fence: str = "```",
    on_drop: Optional[Callable[[str], Any]] = None,
) -> Any:
    """Remove bloated sections (vendored deps, build output, lockfiles, minified
    bundles, ...) from an aggregated-code markdown.

    This is the post-hoc complement to ``code_aggregate``'s ``keys_exclude``: use it to
    slim down an aggregate that was already generated (e.g. one that accidentally
    included a ``node_modules/`` tree). It streams, so it handles arbitrarily large
    files.

    Args:
        src: The aggregate as a markdown string, a path to a markdown file, or any
            iterable of lines.
        exclude: Sections to drop (see ``iter_pruned_aggregate_lines``).
        egress: What to do with the result. The default (``identity``) returns the
            pruned markdown as a string. Pass a filepath string to stream the result to
            that file (memory-safe for huge inputs) and return the filepath.
        header_prefix, fence: Aggregate format markers (see ``iter_pruned_aggregate_lines``).
        on_drop: Optional callback invoked with each dropped section's path.

    Returns:
        The pruned markdown string, or the output filepath when ``egress`` is a path.

    Example:

    >>> md = "## keep.py\\n\\n```python\\nok\\n```\\n## dist/bundle.js\\n\\n```python\\nx\\n```\\n"
    >>> "dist/bundle.js" in prune_code_aggregate(md)
    False
    """
    lines = _resolve_lines(src)
    pruned = iter_pruned_aggregate_lines(
        lines,
        exclude=exclude,
        header_prefix=header_prefix,
        fence=fence,
        on_drop=on_drop,
    )
    if isinstance(egress, str):
        out_path = fullpath(egress)
        with open(out_path, "w") as f:
            f.writelines(pruned)
        return out_path
    return egress("".join(pruned))


def _resolve_lines(src: Union[str, Iterable[str]]) -> Iterable[str]:
    """Resolve ``src`` to an iterable of lines (with line endings preserved).

    A string that names an existing file is opened and iterated lazily; any other
    string is treated as the markdown content itself; anything else is assumed to
    already be an iterable of lines.
    """
    if isinstance(src, str):
        if "\n" not in src and os.path.isfile(fullpath(src)):
            return _iter_file_lines(fullpath(src))
        return src.splitlines(keepends=True)
    return src


def _iter_file_lines(path: str) -> Iterable[str]:
    """Lazily yield the lines of a file, closing it when exhausted."""
    with open(path, "r") as f:
        yield from f


def _readme_from_parent_dir(code_store: Mapping) -> Optional[str]:
    """
    Attempts to read a README file from the parent directory of the code store.
    If a README file is found, it returns its content; otherwise, it returns None.
    """
    if (rootdir := getattr(code_store, "rootdir", None)) is not None:
        parent_dir = os.path.dirname(os.path.normpath(rootdir))
        readme_path = os.path.join(parent_dir, "README.md")
        if os.path.exists(readme_path):
            with open(readme_path, "r") as f:
                return f.read()
    return None


def _readme_first_chainmap(code_store: Mapping, readme_content: str) -> Mapping:
    """Create a ChainMap with README first, handling Python 3.11+ iteration changes.

    >>> cm = _readme_first_chainmap({'a.py': 'code'}, 'readme text')
    >>> list(cm.keys())
    ['README.md', 'a.py']
    """
    from collections import ChainMap

    class ReadmeFirstChainMap(ChainMap):
        def keys(self):
            """Ensure README.md appears first, then code store keys."""
            readme_key = "README.md"
            yield readme_key
            yield from (k for k in self.maps[1] if k != readme_key)

    return ReadmeFirstChainMap({"README.md": readme_content}, code_store)


def code_aggregate(
    code_src: CodeSource,
    *,
    egress: Union[Callable, Filepath] = identity,
    kv_to_item=lambda k, v: f"## {k}\n\n```python\n{v.strip()}\n```",
    keys_filt: Union[Callable, str] = r"\.py$",
    keys_exclude=None,
    include_readme: Callable = _readme_from_parent_dir,
    **store_aggregate_kwargs,
) -> Any:
    """
    Aggregates all code segments from the given code source (folder, github url, store).

    This is useful when you want to use AI to search and respond to questions about a
    specific code base.

    Args:
        code_src (dict): A dictionary where keys are references to the code (e.g., paths)
                         and values are code snippets or content.
        egress (Union[Callable, str]): A function to apply to the aggregate before returning.
                                       If a string, the aggregate will be saved to the file.
        kv_to_item (Callable): A function that converts a key-value pairs to the
                               items that should be aggregated.
        keys_filt (Union[Callable, str]): A function or regex string to filter the keys of the code store.
                                        If a string, it will be compiled to a regex pattern.
        keys_exclude: Optional regex string, iterable of regex strings, or ``path->bool``
                      predicate identifying keys to *exclude* from the aggregate (applied
                      after ``keys_filt``). Use ``DFLT_AGGREGATE_EXCLUDE_PATTERNS`` to
                      skip vendored deps, build outputs, lockfiles and minified bundles.
        include_readme (Callable): A function that takes the code_store as input and returns
                                   the content of a README file to include in the aggregate.
                                   If None, no README will be included.
        **store_aggregate_kwargs: Additional keyword arguments to pass to store_aggregate.

    See dol.store_aggregate for more details.

    Returns:
        Any: The aggregated code content, or the result of the egress function.

    Example:

    >>> code_src = {
    ...     'module1.py': 'def foo(): pass',
    ...     'module2.py': 'def bar(): pass',
    ...     'module3.py': 'class Baz: pass',
    ... }
    >>> print(code_aggregate(code_src))
    ## module1.py
    <BLANKLINE>
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

    Here, let's input an imported (third party) package, and have the function save the
    result to a temporary file

    >>> from tempfile import NamedTemporaryFile
    >>> temp_file_name = NamedTemporaryFile().name
    >>> import aix  # doctest: +SKIP
    >>> _  = code_aggregate(aix, egress=temp_file_name)  # doctest: +SKIP
    >>> print(open(temp_file_name).read(15))  # doctest: +SKIP
    ## __init__.py
    <BLANKLINE>

    Tip: You can also import directly from the name (string) of the package by doing
    `code_aggregate(__import__('aix'))` or more robustly,
    `importlib.import_module('aix')`.

    If you have hubcap installed, you can even get an aggregate of code from a GitHub
    repository.

    >>> string = code_aggregate('https://github.com/thorwhalen/aix')  # doctest: +SKIP


    """
    from dol.trans import warn_and_ignore_if_error

    code_store = resolve_code_source(
        code_src, keys_filt=keys_filt, keys_exclude=keys_exclude
    )
    code_store = warn_and_ignore_if_error(code_store)

    if include_readme:
        readme_content = include_readme(code_store)
        if readme_content:
            code_store = _readme_first_chainmap(code_store, readme_content)

    return store_aggregate(
        code_store, egress=egress, kv_to_item=kv_to_item, **store_aggregate_kwargs
    )


class PackageCodeContexts:
    """Manages aggregation and saves of the code of local packages"""

    def __init__(self, save_folder="."):
        self.save_folder = fullpath(save_folder)
        self.save_filepath = lambda *parts: os.path.join(self.save_folder, *parts)

    def save_single(self, pkg: Union[str, ModuleType]):
        """
        Aggregates and saves the code of a single local package.

        Example:

        To save a single package's code in a single file, in the current folder:

        >>> PackageCodeContexts().save_single('aix')  # doctest: +SKIP

        or, to save multiple package's code in a single file, in a specific folder.

        >>> PackageCodeContexts('some/folder/path').save_multiple_pkgs_code(['aix', 'dol'])  # doctest: +SKIP

        """
        if isinstance(pkg, str):
            pkg_name = pkg
            pkg = importlib.import_module(pkg_name)
        elif isinstance(pkg, ModuleType):
            pkg_name = pkg.__name__
        else:
            raise ValueError(f"Unsupported type for pkg: {pkg}")

        filepath = self.save_filepath(f"{pkg_name}.py.md")
        code_aggregate(pkg, egress=filepath)

    def multiple_pkgs_code(
        self,
        name: Optional[Union[str, Iterable]] = None,
        pkgs: list = (),
        *,
        pkg_secion_marker="#",
        section_sepator="\n\n\n",
    ):
        """
        Aggregates the code of multiple local packages in separate sections.
        Saves the result to a file if a name is provided.
        """
        if (
            name is not None
            and not isinstance(name, str)
            and isinstance(name, Iterable)
            and not pkgs
        ):
            # if the first argument is an iterable, assume it's the list of packages
            pkgs = name  # the first argument is actually packages
            name = None

        def sections():
            for pkg in pkgs:
                yield f"{pkg_secion_marker} {pkg}\n\n" + code_aggregate(pkg)

        md_string = section_sepator.join(sections())

        if name is None:
            return md_string
        else:
            assert isinstance(name, str), f"The first argument must a string: {name}"
            # if not extension, add ".py.md" as the extension
            if not os.path.splitext(name)[1]:
                name = f"{name}.py.md"

            with open(self.save_filepath(name), "w") as f:
                f.write(md_string)

    save_multiple_pkgs_code = multiple_pkgs_code  # backwards compatibility alias


from functools import partial
from types import SimpleNamespace


# Lazy re-export of hubcap.github_repo_markdown_of as ``get_github``.
# hubcap raises OSError at import time when GITHUB_TOKEN is unset; resolving
# this lazily lets ``import contaix.code`` succeed without a token, with the
# error deferred until ``get_github`` is actually called.
def __getattr__(name):
    if name == "get_github":
        from hubcap import github_repo_markdown_of

        return github_repo_markdown_of
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
