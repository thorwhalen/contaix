# Changelog

All notable changes to this project are documented in this file.

The format is inspired by [Keep a Changelog](https://keepachangelog.com/);
each section corresponds to a git version tag (which is also the release
published to PyPI). Entries are commit subjects and PR titles, verbatim.

## [0.0.17] - 2026-06-16

- Add prune_code_aggregate: strip vendored/build bloat from code aggregates

## [0.0.16] - 2026-05-27

- ci: switch to wads reusable workflow stub
- Add contaix-acquire-docs skill ([#4](https://github.com/thorwhalen/contaix/pull/4))

## [0.0.15] - 2026-05-14

- chore(ci): bump action pins to checkout@v6, setup-uv@v7

## [0.0.14] - 2026-05-02

### Fixed

- fix(ci): pass exclude-paths to Windows Run Tests step (matches Linux job)

## [0.0.13] - 2026-05-02

- chore: require dn>=0.0.9, drop fallback, re-enable Windows tests

### Fixed

- fix: pass copy_to_clipboard=False in doctest to avoid pyperclip fallback noise

## [0.0.12] - 2026-05-02

- chore: migrate to pyproject.toml + uv-based CI (modern wads format)
- Update ci.yml
- Comment out extras_require section in setup.cfg for clarity
- Refactor markdown tests to improve clarity and consistency; add scraped dependency
- 0.0.2

### Added

- feat: llms-full.txt fast path + RSC parser fix + bug fixes
- feat: add skill discovery system for pip-installed packages
- feat: add web.py for website-to-markdown conversion with skills and docs
- feat: add _strip_trailing_url_punctuation function and update URL extraction to handle bare URLs
- feat: update remove_hyperlink_crap to handle trailing slashes in double hyperlinks
- feat: add _get_head_with_headers function to handle HEAD requests with custom headers
- feat: integrate warn_and_ignore_if_error in code_aggregate to handle errors gracefully
- feat: add regex to remove duplicate hyperlinks in remove_hyperlink_crap function
- feat: enhance url_to_contents function to support content type and timeout parameters
- feat: import pyperclip in get_from_clipboard and update download_articles_by_section signature
- feat: enhance URL extraction functions to use clipboard content when markdown input is None
- feat: set default value for keys_filt parameter in code_aggregate to filter Python files
- feat: add _readme_first_chainmap function to prioritize README in ChainMap and update code_aggregate to use it
- feat: add _safe_chainmap function to safely handle key-value pairs and update code_aggregate to use it for README inclusion
- feat: update code_aggregate and resolve_code_source to support keys_filt parameter for key filtering
- feat: add key_filt parameter to code_aggregate for filtering keys in code store
- feat: add decorator to source string from clipboard and enhance remove_improperly_double_newlines function
- feat: add remove_improperly_double_newlines function to clean up double newlines in strings
- feat: add remove_hyperlink_crap function to clean up unwanted hyperlinks and citations from a string
- feat: add _readme_from_parent_dir function to read README from parent directory and include it in code_aggregate output
- feat: enhance resolve_code_source function to handle single-file modules

### Changed

- refactor: delegate markdown repair to dn and PDF downloads to pdfdol
- refactor: move scraped functions to util.py to try to solve CI problem

### Fixed

- fix(ci): skip doctests that require unpublished/private deps; disable Windows
- fix(ci): exclude docsrc and misc from pytest --doctest-modules collection
- fix: graceful fallback when dn.repair is unavailable
- fix: lazy-load scraped/hubcap re-exports so import works without GITHUB_TOKEN
- fix: handle boolean input in remove_hyperlink_crap function to improve usability
- fix: add get_github function and improve resolve_code_source_dir_path documentation
- fix: remove unnecessary definitions in util module and update setup.cfg to include dn dependency
- fix: add JSON handling for notebook input in notebook_to_markdown function
- fix: add notes for vendoring and synchronization in markdown module
- fix: improve store handling in aggregate_store function
- fix: add doctest ellipsis for aix import in code_aggregate function
- fix: add aix to install_requires in setup.cfg
- fix: add tabulate to install_requires in setup.cfg
- fix: update import statements to include installation instructions; correct pptx package name
