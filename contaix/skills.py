"""Skill discovery and installation for the contaix ecosystem.

Claude Code skills are stored in ``~/.claude/skills/`` as folders containing
``SKILL.md`` files. When packages are pip-installed, their skills live in
``<package>/data/skills/`` and need to be symlinked into the global directory.

This module discovers skills from installed packages and creates those symlinks.

Usage::

    # From the command line:
    python -m contaix.skills

    # From Python:
    from contaix.skills import install_skills
    install_skills()

    # List available skills without installing:
    from contaix.skills import discover_skills
    for name, path in discover_skills().items():
        print(f"  {name}: {path}")
"""

import importlib
import os
from pathlib import Path

# Packages in the contaix ecosystem that may ship skills.
# Add new packages here as the ecosystem grows.
ECOSYSTEM_PACKAGES = ("contaix", "dn", "pdfdol")

GLOBAL_SKILLS_DIR = Path.home() / ".claude" / "skills"


def discover_skills(packages=ECOSYSTEM_PACKAGES) -> dict[str, Path]:
    """Discover skills from installed ecosystem packages.

    Scans each package's ``data/skills/`` directory for folders containing
    a ``SKILL.md`` file.

    Parameters
    ----------
    packages : tuple of str
        Package names to scan.

    Returns
    -------
    dict
        Mapping of skill name to its ``Path`` in the installed package.
    """
    found = {}
    for pkg_name in packages:
        try:
            pkg = importlib.import_module(pkg_name)
        except ImportError:
            continue
        pkg_dir = Path(pkg.__file__).parent
        skills_dir = pkg_dir / "data" / "skills"
        if not skills_dir.is_dir():
            continue
        for skill_dir in sorted(skills_dir.iterdir()):
            if skill_dir.is_dir() and (skill_dir / "SKILL.md").exists():
                found[skill_dir.name] = skill_dir
    return found


def install_skills(
    packages=ECOSYSTEM_PACKAGES,
    *,
    force: bool = False,
    verbose: bool = True,
):
    """Create symlinks in ``~/.claude/skills/`` for discovered skills.

    Parameters
    ----------
    packages : tuple of str
        Package names to scan for skills.
    force : bool
        If True, replace existing symlinks (but not regular directories).
    verbose : bool
        Print progress.
    """
    GLOBAL_SKILLS_DIR.mkdir(parents=True, exist_ok=True)
    skills = discover_skills(packages)

    if not skills:
        if verbose:
            print("No skills found in installed packages.")
        return

    if verbose:
        print(f"Found {len(skills)} skill(s) in {len(packages)} package(s):")

    for name, source_dir in skills.items():
        target = GLOBAL_SKILLS_DIR / name
        if target.is_symlink():
            if not force:
                if verbose:
                    print(f"  skip {name} (symlink exists)")
                continue
            target.unlink()
        elif target.exists():
            if verbose:
                print(
                    f"  skip {name} (directory exists — "
                    f"remove manually if you want to replace it)"
                )
            continue

        os.symlink(source_dir, target)
        if verbose:
            print(f"  link {name} -> {source_dir}")


def uninstall_skills(
    packages=ECOSYSTEM_PACKAGES,
    *,
    verbose: bool = True,
):
    """Remove symlinks created by :func:`install_skills`.

    Only removes symlinks (not regular directories) to avoid data loss.

    Parameters
    ----------
    packages : tuple of str
        Package names whose skills should be removed.
    verbose : bool
        Print progress.
    """
    skills = discover_skills(packages)
    for name in skills:
        target = GLOBAL_SKILLS_DIR / name
        if target.is_symlink():
            target.unlink()
            if verbose:
                print(f"  removed {name}")
        elif verbose and target.exists():
            print(f"  skip {name} (not a symlink)")


def main():
    """CLI entry point: discover and install skills."""
    import sys

    if "--uninstall" in sys.argv:
        print("Removing contaix ecosystem skills...")
        uninstall_skills()
    else:
        print("Installing contaix ecosystem skills...")
        install_skills(force="--force" in sys.argv)
        print()
        print(f"Skills directory: {GLOBAL_SKILLS_DIR}")


if __name__ == "__main__":
    main()
