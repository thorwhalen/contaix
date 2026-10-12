"""Tests for ``contaix.web.html_to_clean_markdown`` and the html2text-free dependency set."""

import subprocess
import sys
from pathlib import Path

import pytest

from contaix.web import _extract_main_content_html, html_to_clean_markdown

ROOT = Path(__file__).resolve().parent.parent


def test_core_dependencies_exclude_copyleft_html2text():
    tomllib = pytest.importorskip("tomllib")  # py>=3.11
    deps = tomllib.loads((ROOT / "pyproject.toml").read_text())["project"][
        "dependencies"
    ]
    assert not any(d.lower().startswith("html2text") for d in deps)
    assert any(d.startswith("markdownify") for d in deps)


def test_importing_contaix_web_does_not_import_html2text():
    code = "import sys, contaix.web; sys.exit('html2text' in sys.modules)"
    assert subprocess.run([sys.executable, "-I", "-c", code]).returncode == 0


def test_basic_structure():
    html = (
        "<h1>Title</h1><p>Some <b>bold</b>, <i>it</i> and <code>code</code>.</p>"
        "<ul><li>one</li><li>two</li></ul><p>Snake_case_name and a*b*c</p>"
    )
    md = html_to_clean_markdown(html)
    assert md.startswith("# Title\n\n")
    assert "**bold**" in md and "`code`" in md
    assert "* one" in md and "* two" in md
    assert "Snake_case_name" in md and "a*b*c" in md  # no escaping noise


def test_links_and_images_options():
    html = '<p><a href="http://x.org/a">link</a> <img src="i.png" alt="pic"></p>'
    assert html_to_clean_markdown(html) == "[link](http://x.org/a)"
    assert html_to_clean_markdown(html, include_links=False) == "link"
    assert "![pic](i.png)" in html_to_clean_markdown(html, ignore_images=False)


def test_non_content_tags_are_dropped():
    html = (
        "<html><head><title>T</title><style>p{}</style></head>"
        "<body><script>alert(1)</script><noscript>x</noscript><p>body</p></body></html>"
    )
    assert html_to_clean_markdown(html) == "body"


def test_blank_lines_inside_code_blocks_are_preserved():
    html = "<p>a</p><br><br><br><p>b</p><pre><code>def f():\n    pass\n\n\ndef g():\n    pass\n</code></pre>"
    md = html_to_clean_markdown(html)
    assert "\n\n\n" not in md.split("```")[0]  # collapsed outside code
    assert "pass\n\n\ndef g" in md  # PEP 8 spacing kept inside code


def test_tables_survive():
    md = html_to_clean_markdown(
        "<table><tr><th>k</th><th>v</th></tr><tr><td>a</td><td>1</td></tr></table>"
    )
    assert "| k | v |" in md and "| a | 1 |" in md


def test_entities_are_kept_as_characters():
    assert html_to_clean_markdown("<p>&copy; a&nbsp;b</p>") == "© a b"


def test_empty_input():
    assert html_to_clean_markdown("") == ""
    assert html_to_clean_markdown("   ") == ""


def test_unknown_options_raise_instead_of_being_ignored():
    with pytest.raises(TypeError, match="ignore_links"):
        html_to_clean_markdown("<p>x</p>", ignore_links=True)
    with pytest.raises(TypeError, match="unicode_snob"):
        html_to_clean_markdown("<p>x</p>", unicode_snob=True)


def test_markdownify_options_pass_through():
    assert html_to_clean_markdown("<h1>T</h1>", heading_style="UNDERLINED").startswith(
        "T\n="
    )
    assert html_to_clean_markdown("<ul><li>a</li></ul>", bullets="-") == "- a"


def test_strip_option_composes_with_flags():
    html = '<p><b>b</b> <a href="u">l</a> <img src="i.png"></p>'
    assert html_to_clean_markdown(html, strip=["b"]) == "b [l](u)"


def test_body_width_nonzero_is_rejected_zero_accepted():
    assert html_to_clean_markdown("<p>x</p>", body_width=0) == "x"
    with pytest.raises(ValueError, match="body_width"):
        html_to_clean_markdown("<p>x</p>", body_width=80)


def test_extract_main_content_prefers_article():
    filler = "word " * 40
    html = f"<nav>menu</nav><article><h1>Hi</h1><p>{filler}</p></article><footer>f</footer>"
    md = _extract_main_content_html(html)
    assert md.startswith("# Hi") and "menu" not in md and "footer" not in md
