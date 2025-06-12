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
    code_src: CodeSource, keys_filt: Callable = lambda x: x.endswith(".py")
) -> Mapping:
    """
    Will resolve code_src to a Mapping whose values are the code strings

    Args:
        code_src: The source of the code. Can be an explicit `Mapping`,
            a directory path string,
            a GitHub URL,
            or an imported package (must contain a __path__ atribute)
        keys_filt (Callable): A function to filter the keys. Defaults to lambda x: x.endswith('.py').

    """
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


def code_aggregate(
    code_src: CodeSource,
    *,
    egress: Union[Callable, Filepath] = identity,
    kv_to_item=lambda k, v: f"## {k}\n\n```python\n{v.strip()}\n```",
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
    >>> import aix  # doctest: +ELLIPSIS
    ...
    >>> _  = code_aggregate(aix, egress=temp_file_name)
    >>> print(open(temp_file_name).read(15))
    ## __init__.py
    <BLANKLINE>

    Tip: You can also import directly from the name (string) of the package by doing
    `code_aggregate(__import__('aix'))` or more robustly,
    `importlib.import_module('aix')`.

    If you have hubcap installed, you can even get an aggregate of code from a GitHub
    repository.

    >>> string = code_aggregate('https://github.com/thorwhalen/aix')  # doctest: +SKIP


    """
    code_store = resolve_code_source(code_src)
    if include_readme:
        readme_content = include_readme(code_store)
        if readme_content:
            from collections import ChainMap

            # Note: ChainMap's keys iteration starts with second store, so we put the
            # readme content as the second store to have it appear first in the output.
            code_store = ChainMap(code_store, {"README.md": readme_content})
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
from hubcap import github_repo_markdown_of

get_github = github_repo_markdown_of
