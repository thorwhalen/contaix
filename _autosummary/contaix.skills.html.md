# contaix.skills

Skill discovery and installation for the contaix ecosystem.

Claude Code skills are stored in `~/.claude/skills/` as folders containing
`SKILL.md` files. When packages are pip-installed, their skills live in
`<package>/data/skills/` and need to be symlinked into the global directory.

This module discovers skills from installed packages and creates those symlinks.

Usage:

```default
# From the command line:
python -m contaix.skills

# From Python:
from contaix.skills import install_skills
install_skills()

# List available skills without installing:
from contaix.skills import discover_skills
for name, path in discover_skills().items():
    print(f"  {name}: {path}")
```

### Functions

| [`discover_skills`](#contaix.skills.discover_skills)([packages])                | Discover skills from installed ecosystem packages.                                            |
|---------------------------------------------------------------------------------------------|-----------------------------------------------------------------------------------------------|
| [`install_skills`](#contaix.skills.install_skills)([packages, force, verbose]) | Create symlinks in `~/.claude/skills/` for discovered skills.                                 |
| [`main`](#contaix.skills.main)()                                     | CLI entry point: discover and install skills.                                                 |
| [`uninstall_skills`](#contaix.skills.uninstall_skills)([packages, verbose])      | Remove symlinks created by [`install_skills()`](#contaix.skills.install_skills). |

### contaix.skills.discover_skills(packages=('contaix', 'dn', 'pdfdol'))

Discover skills from installed ecosystem packages.

Scans each package’s `data/skills/` directory for folders containing
a `SKILL.md` file.

* **Parameters:**
  **packages** ([*tuple*](https://docs.python.org/3/builtins/stdtypes.html#tuple) *of* [*str*](https://docs.python.org/3/builtins/stdtypes.html#str)) – Package names to scan.
* **Returns:**
  Mapping of skill name to its `Path` in the installed package.
* **Return type:**
  [`dict`](https://docs.python.org/3/builtins/stdtypes.html#dict)[[`str`](https://docs.python.org/3/builtins/stdtypes.html#str), [`Path`](https://docs.python.org/3/library/pathlib.html#pathlib.Path)]

### contaix.skills.install_skills(packages=('contaix', 'dn', 'pdfdol'), , force=False, verbose=True)

Create symlinks in `~/.claude/skills/` for discovered skills.

* **Parameters:**
  * **packages** ([*tuple*](https://docs.python.org/3/builtins/stdtypes.html#tuple) *of* [*str*](https://docs.python.org/3/builtins/stdtypes.html#str)) – Package names to scan for skills.
  * **force** ([`bool`](https://docs.python.org/3/builtins/functions.html#bool)) – If True, replace existing symlinks (but not regular directories).
  * **verbose** ([`bool`](https://docs.python.org/3/builtins/functions.html#bool)) – Print progress.

### contaix.skills.main()

CLI entry point: discover and install skills.

### contaix.skills.uninstall_skills(packages=('contaix', 'dn', 'pdfdol'), , verbose=True)

Remove symlinks created by [`install_skills()`](#contaix.skills.install_skills).

Only removes symlinks (not regular directories) to avoid data loss.

* **Parameters:**
  * **packages** ([*tuple*](https://docs.python.org/3/builtins/stdtypes.html#tuple) *of* [*str*](https://docs.python.org/3/builtins/stdtypes.html#str)) – Package names whose skills should be removed.
  * **verbose** ([`bool`](https://docs.python.org/3/builtins/functions.html#bool)) – Print progress.
